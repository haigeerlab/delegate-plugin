#!/usr/bin/env python3
"""Prepare a delegate release up to one local commit (spec/release-prepare.md).

Unattended: never reads stdin, never pushes, tags, merges or touches the local
installation. Stdout carries exactly one JSON document; errors are fixed codes.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'delegate.release-prepare/v1'
CHECK_NAMES = ('validate', 'plugin-validate-marketplace', 'plugin-validate-plugin', 'diff-check', 'verify-artifacts')
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')
PLUGIN_JSON = 'plugins/delegate/.claude-plugin/plugin.json'
INTERFACE_JSON = 'plugins/delegate/interface.json'
NOTES = {'zh': 'docs/releases/unreleased.md', 'en': 'docs/en/releases/unreleased.md'}
HISTORY = {'zh': '历史验收记录', 'en': 'Historical acceptance records'}
REQUIRED = {'zh': ('## 影响面', '## 验证与已知限制'), 'en': ('## Impact', '## Validation and known limitations')}
TITLE = re.compile(r'^<!-- release-title: (.+?) -->$', re.M)
PLACEHOLDER = '@@RELEASE_PREPARE_PYTHON_TESTS@@'


class Stop(Exception):
    def __init__(self, reason, exit_code=1):
        super().__init__(reason)
        self.reason, self.exit_code = reason, exit_code


def git(repo, *args, check=True):
    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0', LANG='C', LC_ALL='C')
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True,
                            stdin=subprocess.DEVNULL, env=environment)
    if check and result.returncode != 0:
        raise Stop('check_failed')
    return result.stdout.strip() if check else result


def key(version):
    return tuple(int(part) for part in version.split('.'))


def parse_arguments(argv):
    positional = [value for value in argv if value != '--check']
    if len(argv) > 2 or len(positional) != 1 or argv.count('--check') > 1 or positional[0].startswith('-'):
        raise Stop('usage_invalid', 64)
    return positional[0], '--check' in argv


def notes_parts(text, language):
    """Split unreleased notes into (history head, title, body); body excludes the title line."""
    marker = HISTORY[language]
    if marker not in text:
        raise Stop('release_notes_incomplete')
    end = text.index('\n', text.index(marker)) + 1 if '\n' in text[text.index(marker):] else len(text)
    head, rest = text[:end], text[end:]
    match = TITLE.search(rest)
    headings = re.findall(r'^## .+$', rest, re.M)
    impact, validation = REQUIRED[language]
    if (not match or not match.group(1).strip() or impact not in headings or validation not in headings
            or not [line for line in headings if line not in (impact, validation)]):
        raise Stop('release_notes_incomplete')
    body = (rest[:match.start()] + rest[match.end():]).strip('\n') + '\n'
    return head, match.group(1).strip(), body


def anchors(old):
    v = re.escape('v' + old)
    return {
        'README.md': [r'当前发行：\[%s\]\(https://github\.com/haigeerlab/delegate-plugin/releases/tag/%s\)' % (v, v),
                      r'发行源码由 `%s` 标签固定' % v, r'发行变化见 \[%s\]\(docs/releases/%s\.md\)、' % (v, v),
                      r'、(\d+) 个循环注册的 Python 回归套', r'%s 发布验证为 (\d+) 项 Python' % v],
        'README.en.md': [r'Current release: \[%s\]\(https://github\.com/haigeerlab/delegate-plugin/releases/tag/%s\)' % (v, v),
                         r'The `%s` tag fixes' % v, r'Release changes are in \[%s\]\(docs/en/releases/%s\.md\), ' % (v, v),
                         r'(\d+) loop-registered Python regression suites', r'%s release validation passed (\d+) Python' % v],
        'docs/README.md': [r'读 \[%s 版本说明\]\(releases/%s\.md\)' % (v, v),
                           r'\| 当前发行 \| \[%s\]\(releases/%s\.md\) \| \[%s\]\(en/releases/%s\.md\) \|' % (v, v, v, v),
                           r'^\| 旧版发行记录 \| (.+) \| (.+) \|$'],
        'docs/en/README.md': [r'read \[%s release notes\]\(releases/%s\.md\)' % (v, v),
                              r'\| Current release \| \[%s\]\(\.\./releases/%s\.md\) \| \[%s\]\(releases/%s\.md\) \|' % (v, v, v, v),
                              r'^\| Previous release records \| (.+) \| (.+) \|$'],
        'CONTRIBUTING.md': [r'%s 发布验证为 (\d+) 项 Python、(\d+) 项 shell 和 (\d+) 项 eval（' % v,
                            r'总入口包含 (\d+) 个循环注册'],
        'CONTRIBUTING.en.md': [r'%s release validation passed (\d+) Python, (\d+) shell and (\d+) eval cases \(' % v,
                               r'The aggregate includes (\d+) loop-registered'],
        NOTES['zh']: [r'%s 之后(?:暂无未发布变更|的未发布变更见下)。' % v],
        NOTES['en']: [r'(?:No unreleased changes after %s\.|Unreleased changes after %s follow\.)' % (v, v)],
    }


def check_anchors(texts, old):
    for name, patterns in anchors(old).items():
        for pattern in patterns:
            if len(re.findall(pattern, texts[name], re.M)) != 1:
                raise Stop('release_docs_anchor_missing')


def read_texts(repo):
    names = set(anchors('0.0.0')) | {PLUGIN_JSON, INTERFACE_JSON}
    texts = {}
    for name in names:
        try:
            texts[name] = (Path(repo) / name).read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            raise Stop('release_docs_anchor_missing') from None
    return texts


def preconditions(repo, version, texts):
    if not VERSION.fullmatch(version):
        raise Stop('version_invalid')
    current = json.loads(texts[PLUGIN_JSON])['version']
    if key(version) <= key(current):
        raise Stop('version_not_newer')
    if git(repo, 'rev-parse', '--verify', '--quiet', 'refs/tags/v' + version, check=False).returncode == 0:
        raise Stop('tag_exists')
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise Stop('worktree_dirty')
    base = git(repo, 'rev-parse', 'HEAD')
    main_ref = git(repo, 'rev-parse', '--verify', '--quiet', 'refs/remotes/origin/main', check=False)
    if main_ref.returncode != 0 or main_ref.stdout.strip() != base:
        raise Stop('base_not_main')
    for language in ('zh', 'en'):
        notes_parts(texts[NOTES[language]], language)
    check_anchors(texts, current)
    return current, base


UPDATE = {
    'zh': ('## 更新\n\n'
           '- Claude Code：运行 `claude plugin update delegate@delegate-marketplace`，然后打开新会话或执行 `/reload-plugins`。\n'
           '- Codex：把 `~/.codex/config.toml` 里 `[marketplaces.delegate-marketplace]` 的 `ref` 改成 `"v{new}"`，再运行 '
           '`codex plugin marketplace upgrade delegate-marketplace` 和 `codex plugin add delegate@delegate-marketplace`，然后重开会话。\n'),
    'en': ('## Update\n\n'
           '- Claude Code: run `claude plugin update delegate@delegate-marketplace`, then open a new session or run `/reload-plugins`.\n'
           '- Codex: change `ref` in `[marketplaces.delegate-marketplace]` of `~/.codex/config.toml` to `"v{new}"`, run '
           '`codex plugin marketplace upgrade delegate-marketplace` and `codex plugin add delegate@delegate-marketplace`, then reopen the session.\n'),
}
MEASURED = {'zh': '本次发版准备实测：免费总验证 {python} 项 Python，循环注册的 Python 回归套 {suites} 个。',
            'en': 'Release preparation measured: free validation {python} Python tests, {suites} loop-registered Python regression suites.'}
HEADER = {'zh': '# v{new}：{title}\n\n简体中文 | [English](../en/releases/v{new}.md)\n\n',
          'en': '# v{new}: {title}\n\n[简体中文](../../releases/v{new}.md) | English\n\n'}
FOLD = {'zh': 'v{old} 之后的{title}已归入 [v{new} 版本说明](v{new}.md)。v{new} 之后暂无未发布变更。',
        'en': '{title} after v{old} is recorded in [v{new} release notes](v{new}.md). No unreleased changes after v{new}.'}


def sub_once(pattern, replacement, text):
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if count != 1:
        raise Stop('release_docs_anchor_missing')
    return result


def release_notes(text, language, old, new, python, suites):
    head, title, body = notes_parts(text, language)
    validation = REQUIRED[language][1]
    start = body.index(validation + '\n')
    following = re.search(r'^## ', body[start + len(validation):], re.M)
    end = start + len(validation) + following.start() if following else len(body)
    section = body[start:end].rstrip('\n') + '\n\n' + MEASURED[language].format(python=python, suites=suites) + '\n'
    body = body[:start] + section + ('\n' + body[end:] if end < len(body) else '')
    notes = HEADER[language].format(new=new, title=title) + body.rstrip('\n') + '\n\n' + UPDATE[language].format(new=new)
    folded = sub_once(anchors(old)[NOTES[language]][0], lambda _: FOLD[language].format(old=old, new=new, title=title), head)
    return notes, folded.rstrip('\n') + '\n', title


def render(texts, old, new, python, suites):
    """Return every rewritten or new file; raises Stop when an anchor is missing."""
    out, titles = {}, {}
    for language, path in (('zh', 'docs/releases/v{}.md'), ('en', 'docs/en/releases/v{}.md')):
        notes, folded, titles[language] = release_notes(texts[NOTES[language]], language, old, new, python, suites)
        out[path.format(new)] = notes
        out[NOTES[language]] = folded
    o, n = 'v' + old, 'v' + new
    out[PLUGIN_JSON] = sub_once(r'"version": "%s"' % re.escape(old), '"version": "%s"' % new, texts[PLUGIN_JSON])
    patterns = anchors(old)
    readme = texts['README.md']
    readme = sub_once(patterns['README.md'][0], lambda m: m.group(0).replace(o, n), readme)
    readme = sub_once(patterns['README.md'][1], '发行源码由 `%s` 标签固定' % n, readme)
    readme = sub_once(patterns['README.md'][2], lambda m: '发行变化见 [%s](docs/releases/%s.md)、[%s](docs/releases/%s.md)、' % (n, n, o, o), readme)
    readme = sub_once(patterns['README.md'][3], '、%s 个循环注册的 Python 回归套' % suites, readme)
    out['README.md'] = sub_once(patterns['README.md'][4], '%s 发布验证为 %s 项 Python' % (n, python), readme)
    readme = texts['README.en.md']
    readme = sub_once(patterns['README.en.md'][0], lambda m: m.group(0).replace(o, n), readme)
    readme = sub_once(patterns['README.en.md'][1], 'The `%s` tag fixes' % n, readme)
    readme = sub_once(patterns['README.en.md'][2], lambda m: 'Release changes are in [%s](docs/en/releases/%s.md), [%s](docs/en/releases/%s.md), ' % (n, n, o, o), readme)
    readme = sub_once(patterns['README.en.md'][3], '%s loop-registered Python regression suites' % suites, readme)
    out['README.en.md'] = sub_once(patterns['README.en.md'][4], '%s release validation passed %s Python' % (n, python), readme)
    index = texts['docs/README.md']
    index = sub_once(patterns['docs/README.md'][0], lambda m: m.group(0).replace(o, n), index)
    index = sub_once(patterns['docs/README.md'][1], lambda m: m.group(0).replace(o, n), index)
    out['docs/README.md'] = sub_once(patterns['docs/README.md'][2], lambda m: '| 旧版发行记录 | [%s](releases/%s.md)、%s | [%s](en/releases/%s.md), %s |' % (o, o, m.group(1), o, o, m.group(2)), index)
    index = texts['docs/en/README.md']
    index = sub_once(patterns['docs/en/README.md'][0], lambda m: m.group(0).replace(o, n), index)
    index = sub_once(patterns['docs/en/README.md'][1], lambda m: m.group(0).replace(o, n), index)
    out['docs/en/README.md'] = sub_once(patterns['docs/en/README.md'][2], lambda m: '| Previous release records | [%s](../releases/%s.md)、%s | [%s](releases/%s.md), %s |' % (o, o, m.group(1), o, o, m.group(2)), index)
    guide = texts['CONTRIBUTING.md']
    guide = sub_once(patterns['CONTRIBUTING.md'][0], lambda m: '%s 发布验证为 %s 项 Python、%s 项 shell 和 %s 项 eval（%s 为 %s 项，' % (n, python, m.group(2), m.group(3), o, m.group(1)), guide)
    out['CONTRIBUTING.md'] = sub_once(patterns['CONTRIBUTING.md'][1], '总入口包含 %s 个循环注册' % suites, guide)
    guide = texts['CONTRIBUTING.en.md']
    guide = sub_once(patterns['CONTRIBUTING.en.md'][0], lambda m: '%s release validation passed %s Python, %s shell and %s eval cases (%s: %s Python; ' % (n, python, m.group(2), m.group(3), o, m.group(1)), guide)
    out['CONTRIBUTING.en.md'] = sub_once(patterns['CONTRIBUTING.en.md'][1], 'The aggregate includes %s loop-registered' % suites, guide)
    return out, titles


def default_checks(repo, *, installed=None):
    import shutil
    installed = Path(installed or Path.home() / '.claude/plugins/installed_plugins.json')
    verify = None
    try:
        plugins = json.loads(installed.read_text(encoding='utf-8')).get('plugins', {})
        for name, entries in plugins.items():
            if name.startswith('spec-guard@') and entries and entries[0].get('installPath'):
                verify = ['/bin/bash', str(Path(entries[0]['installPath']) / 'hooks/verify-artifacts.sh')]
    except (OSError, ValueError, AttributeError, TypeError):
        verify = None
    claude = shutil.which('claude') or 'claude'
    return [('validate', ['/bin/bash', 'scripts/validate.sh']),
            ('plugin-validate-marketplace', [claude, 'plugin', 'validate', '.']),
            ('plugin-validate-plugin', [claude, 'plugin', 'validate', './plugins/delegate']),
            ('diff-check', ['git', 'diff', '--cached', '--check']),
            ('verify-artifacts', verify)]


def run_checks(repo, checks, records, after_validate=None):
    """Run checks in order; append {name, command, exit_code}; return the Python test count."""
    python = None
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
    for name, argv in checks:
        record = {'name': name, 'command': list(argv) if argv else None, 'exit_code': None}
        records.append(record)
        if not argv:
            raise Stop('check_unavailable')
        try:
            result = subprocess.run(argv, cwd=str(repo), capture_output=True, text=True,
                                    stdin=subprocess.DEVNULL, env=environment)
        except OSError:
            raise Stop('check_unavailable') from None
        record['exit_code'] = result.returncode
        sys.stderr.write('release-prepare: %s exit=%d\n' % (name, result.returncode))
        if result.returncode != 0:
            raise Stop('check_failed')
        if name == 'validate':
            counts = [int(value) for value in re.findall(r'^Ran (\d+) tests? in ', result.stdout + result.stderr, re.M)]
            if not counts:
                raise Stop('check_failed')
            python = sum(counts)
            if after_validate:
                after_validate(python)
    return python


def loop_suites(repo):
    try:
        text = (Path(repo) / 'scripts/validate.sh').read_text(encoding='utf-8')
    except OSError:
        raise Stop('release_docs_anchor_missing') from None
    # The Python regression loop is the one whose body runs test-${SUITE}.py (the shell loop runs .sh).
    loops = [match.group(1) for match in re.finditer(r'^for SUITE in (.+?); do\n(.*?)^done$', text, re.M | re.S)
             if 'test-${SUITE}.py' in match.group(2)]
    if len(loops) != 1:
        raise Stop('release_docs_anchor_missing')
    return len(loops[0].split())


def interface_versions(repo, texts):
    now = json.loads(texts[INTERFACE_JSON])['interface']
    tags = git(repo, 'tag', '--list', 'v*', '--sort=-v:refname').split()
    last = None
    if tags:
        shown = git(repo, 'show', '%s:%s' % (tags[0], INTERFACE_JSON), check=False)
        if shown.returncode == 0:
            try:
                last = json.loads(shown.stdout)['interface']
            except (ValueError, KeyError, TypeError):
                last = None
    return {'last_release': last, 'now': now}


def human_steps(new):
    n = 'v' + new
    return [
        {'command': 'git push -u origin release/%s && gh pr create --base main --head release/%s' % (n, n),
         'why': '远端写入：delegate 是流水线自用插件，推送与开 PR 由 autopilot 编排或人取得授权后做，脚本只到本地。'},
        {'command': 'gh pr merge <PR 编号> --merge',
         'why': '流水线自用插件发布最高只到 prepare，合并进主干要用户点头。'},
        {'command': 'git tag -a %s <合并提交> -m "%s" && git push origin %s' % (n, n, n),
         'why': '打标签即固定发行源码，市场按标签安装，属于发布动作，要用户点头。'},
        {'command': 'gh release create %s --verify-tag --title "%s" --notes-file docs/releases/%s.md' % (n, n, n),
         'why': '对外发布，撤回会影响已经看到或安装的人，要用户点头。'},
        {'command': 'claude plugin marketplace update delegate-marketplace && claude plugin update delegate@delegate-marketplace',
         'why': '本机升级影响所有正在运行的会话，需要用户同意并安排先后。'},
        {'command': '把 ~/.codex/config.toml 里 [marketplaces.delegate-marketplace] 的 ref 改成 "%s"，再运行 codex plugin marketplace upgrade delegate-marketplace 和 codex plugin add delegate@delegate-marketplace' % n,
         'why': '改用户的全局配置，并影响所有 Codex 会话，需要用户同意。'},
        {'command': '在打开中的 Claude Code 会话执行 /reload-plugins 或新开会话；⌘Q 退出并重开 ChatGPT',
         'why': '桌面动作，只能用户本人在界面上做；⌘Q 会断开所有 Codex 线程，要等各方到安全点。'},
    ]


def read_texts_at(repo, commit):
    names = set(anchors('0.0.0')) | {PLUGIN_JSON, INTERFACE_JSON}
    return {name: git(repo, 'show', '%s:%s' % (commit, name)) + '\n' for name in names}


def write_files(repo, files):
    for name, text in files.items():
        path = Path(repo) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def prepare(repo, version, base, rendered, checks, result):
    branch = 'release/v' + version
    original = git(repo, 'symbolic-ref', '--short', '-q', 'HEAD', check=False).stdout.strip() or base
    trailer = 'Release-Prepare: v' + version
    if git(repo, 'rev-parse', '--verify', '--quiet', 'refs/heads/' + branch, check=False).returncode == 0:
        tip = git(repo, 'rev-parse', 'refs/heads/' + branch)
        parent = git(repo, 'rev-parse', '--verify', '--quiet', tip + '^', check=False).stdout.strip()
        if parent != base or trailer not in git(repo, 'log', '-1', '--format=%B', tip).splitlines():
            raise Stop('release_branch_conflict')
        result['release'].update(sha=tip, reused=True)
        git(repo, 'checkout', '-q', branch)
        try:
            return run_checks(repo, checks, result['checks'])
        except Stop:
            git(repo, 'checkout', '-q', original, check=False)
            raise
    created = [name for name in rendered if not (Path(repo) / name).exists()]
    git(repo, 'checkout', '-q', '-b', branch)

    def fill(python):
        measured = {name: text.replace(PLACEHOLDER, str(python)) for name, text in rendered.items()}
        write_files(repo, measured)
        git(repo, 'add', '--', *sorted(measured))

    try:
        write_files(repo, rendered)
        python = run_checks(repo, checks, result['checks'], after_validate=fill)
        git(repo, 'commit', '-q', '-m', 'chore: 准备 v%s 发行' % version,
            '-m', '由 scripts/release-prepare.sh 生成：版本号、中英文发行说明、待发行说明收回、当前发行链接与发布验证数字。',
            '-m', trailer)
    except Stop:
        git(repo, 'reset', '-q', '--hard', base, check=False)
        for name in created:
            try:
                (Path(repo) / name).unlink()
            except OSError:
                pass
        git(repo, 'checkout', '-q', original, check=False)
        git(repo, 'branch', '-D', branch, check=False)
        raise
    result['release']['sha'] = git(repo, 'rev-parse', 'HEAD')
    return python


def report(mode):
    return {'schema': SCHEMA, 'mode': mode, 'status': 'stopped', 'reason': None,
            'version': {'before': None, 'after': None}, 'interface': {'last_release': None, 'now': None},
            'base': {'ref': 'origin/main', 'sha': None},
            'release': {'branch': None, 'sha': None, 'reused': False},
            'notes': {'title': None, 'zh': None, 'en': None},
            'tests': {'python': None, 'loop_suites': None}, 'checks': [], 'human_steps': []}


def main(argv, *, repo=None, checks=None, stdout=None):
    stdout = stdout or sys.stdout
    repo = Path(repo or Path(__file__).resolve().parents[1])
    result = report('check' if '--check' in argv else 'prepare')
    exit_code = 0
    try:
        version, check_only = parse_arguments(argv)
        texts = read_texts(repo)
        old, base = preconditions(repo, version, texts)
        suites = loop_suites(repo)
        rendered, titles = render(texts, old, version, PLACEHOLDER, suites)
        result['version'] = {'before': old, 'after': version}
        result['base']['sha'] = base
        result['interface'] = interface_versions(repo, texts)
        result['release']['branch'] = 'release/v' + version
        result['notes'] = {'title': titles['zh'], 'zh': 'docs/releases/v%s.md' % version,
                           'en': 'docs/en/releases/v%s.md' % version}
        result['tests']['loop_suites'] = suites
        checks = checks if checks is not None else default_checks(repo)
        if check_only:
            result['tests']['python'] = run_checks(repo, checks, result['checks'])
        else:
            result['tests']['python'] = prepare(repo, version, base, rendered, checks, result)
        result['human_steps'] = human_steps(version)
        result['status'] = 'ready'
    except Stop as stop:
        result['status'], result['reason'] = 'stopped', stop.reason
        exit_code = stop.exit_code
    stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return exit_code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
