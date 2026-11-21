#!/usr/bin/env python3
"""Release preparation in disposable repositories with fake checks (never runs validate.sh)."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release_prepare as rp

OLD, NEW = '0.10.0', '0.11.0'
FILES = {
    'plugins/delegate/.claude-plugin/plugin.json': '{\n  "name": "delegate",\n  "version": "0.10.0",\n  "license": "MIT"\n}\n',
    'plugins/delegate/interface.json': '{\n  "interface": "1.5"\n}\n',
    'scripts/validate.sh': '#!/bin/bash\nfor SUITE in alpha beta gamma; do\n  python3 -B "plugins/delegate/tests/test-${SUITE}.py"\ndone\n',
    'README.md': (
        '仓库：[haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · 当前发行：[v0.10.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.10.0) · [文档索引](docs/README.md)\n\n'
        '发行源码由 `v0.10.0` 标签固定，`main` 会继续变化。\n\n'
        '发行变化见 [v0.10.0](docs/releases/v0.10.0.md)、[v0.9.0](docs/releases/v0.9.0.md) 与 [v0.5.0](docs/releases/v0.5.0.md)，后续修改见[未发布记录](docs/releases/unreleased.md)。\n\n'
        '总入口包含 3 个 shell 产品套、28 个循环注册的 Python 回归套。v0.10.0 发布验证为 388 项 Python、53 项 shell 和 19 项 eval；实际证据另列。\n'),
    'README.en.md': (
        'Repository: [haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · Current release: [v0.10.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.10.0) · [Documentation index](docs/en/README.md)\n\n'
        'The `v0.10.0` tag fixes release source at one revision, while `main` continues to change.\n\n'
        'Release changes are in [v0.10.0](docs/en/releases/v0.10.0.md), [v0.9.0](docs/en/releases/v0.9.0.md) and [v0.5.0](docs/en/releases/v0.5.0.md).\n\n'
        'The entry point covers three shell product suites, 28 loop-registered Python regression suites. v0.10.0 release validation passed 388 Python, 53 shell and 19 eval cases. Evidence is separate.\n'),
    'docs/README.md': (
        '- 升级：读 [v0.10.0 版本说明](releases/v0.10.0.md)；后续变化看 [未发布记录](releases/unreleased.md)。\n\n'
        '| 当前发行 | [v0.10.0](releases/v0.10.0.md) | [v0.10.0](en/releases/v0.10.0.md) |\n'
        '| 旧版发行记录 | [v0.9.0](releases/v0.9.0.md)、[v0.8.6](releases/v0.8.6.md) | [v0.9.0](en/releases/v0.9.0.md), [v0.8.6](en/releases/v0.8.6.md) |\n'),
    'docs/en/README.md': (
        '- Upgrading: read [v0.10.0 release notes](releases/v0.10.0.md); see Unreleased for later changes.\n\n'
        '| Current release | [v0.10.0](../releases/v0.10.0.md) | [v0.10.0](releases/v0.10.0.md) |\n'
        '| Previous release records | [v0.9.0](../releases/v0.9.0.md)、[v0.8.6](../releases/v0.8.6.md) | [v0.9.0](releases/v0.9.0.md), [v0.8.6](releases/v0.8.6.md) |\n'),
    'CONTRIBUTING.md': '总入口检查语法。v0.10.0 发布验证为 388 项 Python、53 项 shell 和 19 项 eval（v0.9.0 为 354 项，v0.5.0 为 157 项 Python）；总入口包含 28 个循环注册的 Python 回归套。\n',
    'CONTRIBUTING.en.md': 'The entry point checks syntax. v0.10.0 release validation passed 388 Python, 53 shell and 19 eval cases (v0.9.0: 354 Python; v0.5.0: 157 Python). The aggregate includes 28 loop-registered Python regression suites.\n',
}
UNRELEASED_ZH = ('# 未发布变更\n\n简体中文 | [English](../en/releases/unreleased.md)\n\n'
                 '旧版本已归入 [v0.10.0 版本说明](v0.10.0.md)。v0.10.0 之后的未发布变更见下。历史验收记录保留其发生时的版本和状态，不追认历史批准。\n\n'
                 '<!-- release-title: 示例改动 -->\n\n这是示例版本的导语。\n\n## 示例改动\n\n- 做了一件事。\n\n'
                 '## 影响面\n\n接口不变。\n\n## 验证与已知限制\n\n示例测试通过。\n')
UNRELEASED_EN = ('# Unreleased changes\n\n[简体中文](../../releases/unreleased.md) | English\n\n'
                 'Older versions are recorded in [v0.10.0 release notes](v0.10.0.md). Unreleased changes after v0.10.0 follow. Historical acceptance records retain their original version/status without retroactive approval.\n\n'
                 '<!-- release-title: Example change -->\n\nThis is the example introduction.\n\n## Example change\n\n- Did one thing.\n\n'
                 '## Impact\n\nInterface unchanged.\n\n## Validation and known limitations\n\nExample tests pass.\n')


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL).stdout.strip()


TEMPLATE = None


def template():
    """Build the fixture repository once per process; tests copy it."""
    global TEMPLATE
    if TEMPLATE is None:
        holder = tempfile.TemporaryDirectory(prefix='delegate-release-template.')
        repo = Path(holder.name).resolve() / 'repo'
        repo.mkdir()
        git(repo, 'init', '-q', '-b', 'main')
        git(repo, 'config', 'user.name', 'Fixture')
        git(repo, 'config', 'user.email', 'fixture@example.invalid')
        for name, text in FILES.items():
            Fixture.write_to(repo, name, text)
        Fixture.write_to(repo, 'docs/releases/unreleased.md', UNRELEASED_ZH.split('\n<!--')[0].replace('之后的未发布变更见下。', '之后暂无未发布变更。'))
        Fixture.write_to(repo, 'docs/en/releases/unreleased.md', UNRELEASED_EN.split('\n<!--')[0].replace('Unreleased changes after v0.10.0 follow.', 'No unreleased changes after v0.10.0.'))
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', '基准版本')
        git(repo, 'tag', '-a', 'v0.10.0', '-m', '上一版')
        Fixture.write_to(repo, 'docs/releases/unreleased.md', UNRELEASED_ZH)
        Fixture.write_to(repo, 'docs/en/releases/unreleased.md', UNRELEASED_EN)
        git(repo, 'commit', '-qam', '写待发行说明')
        git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        TEMPLATE = (holder, repo)
    return TEMPLATE[1]


class Fixture(unittest.TestCase):
    def setUp(self):
        import shutil
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-release.')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / 'repo'
        shutil.copytree(template(), self.repo, symlinks=True)
        self.base = git(self.repo, 'rev-parse', 'HEAD')

    @staticmethod
    def write_to(repo, name, text):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def write(self, name, text):
        self.write_to(self.repo, name, text)

    def checks(self, fail=None, missing=None, python=400):
        result = []
        for name in rp.CHECK_NAMES:
            if name == missing:
                result.append((name, ['/nonexistent/command-for-test']))
            elif name == 'validate':
                result.append((name, ['/bin/sh', '-c', 'echo "Ran %d tests in 1s"; exit %d' % (python, 1 if fail == name else 0)]))
            else:
                result.append((name, ['/bin/sh', '-c', 'exit %d' % (1 if fail == name else 0)]))
        return result

    def run_main(self, *argv, **options):
        import contextlib
        output = io.StringIO()
        with contextlib.redirect_stderr(io.StringIO()):
            code = rp.main(list(argv), repo=self.repo, checks=options.get('checks') or self.checks(), stdout=output)
        return code, json.loads(output.getvalue())

    def snapshot(self):
        files = {path.relative_to(self.repo).as_posix(): path.read_bytes()
                 for path in self.repo.rglob('*') if path.is_file() and '.git' not in path.relative_to(self.repo).parts}
        refs = git(self.repo, 'for-each-ref', '--format=%(refname) %(objectname)')
        return files, refs, git(self.repo, 'rev-parse', '--abbrev-ref', 'HEAD')


class PreconditionTests(Fixture):
    def stopped(self, reason, *argv, code=1, **options):
        result, report = self.run_main(*argv, **options)
        self.assertEqual(result, code, report)
        self.assertEqual(report['status'], 'stopped')
        self.assertEqual(report['reason'], reason)
        self.assertEqual(report['schema'], 'delegate.release-prepare/v1')
        return report

    def test_usage_errors_exit_64(self):
        for argv in [(), ('0.11.0', '--check', 'x'), ('--bogus',), ('0.11.0', '--force')]:
            self.stopped('usage_invalid', *argv, code=64)

    def test_version_rules(self):
        self.stopped('version_invalid', '0.11')
        self.stopped('version_invalid', 'v0.11.0')
        self.stopped('version_not_newer', '0.10.0')
        self.stopped('version_not_newer', '0.9.9')
        git(self.repo, 'tag', 'v0.11.0')
        self.stopped('tag_exists', '0.11.0')

    def test_dirty_worktree_and_stale_base(self):
        self.write('stray.txt', 'x\n')
        self.stopped('worktree_dirty', '0.11.0')
        (self.repo / 'stray.txt').unlink()
        git(self.repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD~1')
        self.stopped('base_not_main', '0.11.0')

    def test_unreleased_notes_must_have_title_and_sections(self):
        for old in ['<!-- release-title: 示例改动 -->\n', '## 影响面\n', '## 验证与已知限制\n', '## 示例改动\n\n- 做了一件事。\n\n']:
            self.write('docs/releases/unreleased.md', UNRELEASED_ZH.replace(old, ''))
            git(self.repo, 'commit', '-qam', '改待发行说明')
            git(self.repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
            self.stopped('release_notes_incomplete', '0.11.0', '--check')
        self.write('docs/releases/unreleased.md', UNRELEASED_ZH)
        self.write('docs/en/releases/unreleased.md', UNRELEASED_EN.replace('## Impact\n', ''))
        git(self.repo, 'commit', '-qam', '改英文待发行说明')
        git(self.repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.stopped('release_notes_incomplete', '0.11.0', '--check')

    def test_missing_anchor_stops_without_guessing(self):
        self.write('CONTRIBUTING.md', FILES['CONTRIBUTING.md'].replace('发布验证为', '验证结果为'))
        git(self.repo, 'commit', '-qam', '改措辞')
        git(self.repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        report = self.stopped('release_docs_anchor_missing', '0.11.0', '--check')
        self.assertEqual(report['checks'], [])



UPDATE_ZH = ('## 更新\n\n'
             '- Claude Code：运行 `claude plugin update delegate@delegate-marketplace`，然后打开新会话或执行 `/reload-plugins`。\n'
             '- Codex：把 `~/.codex/config.toml` 里 `[marketplaces.delegate-marketplace]` 的 `ref` 改成 `"v0.11.0"`，再运行 '
             '`codex plugin marketplace upgrade delegate-marketplace` 和 `codex plugin add delegate@delegate-marketplace`，然后重开会话。\n')
UPDATE_EN = ('## Update\n\n'
             '- Claude Code: run `claude plugin update delegate@delegate-marketplace`, then open a new session or run `/reload-plugins`.\n'
             '- Codex: change `ref` in `[marketplaces.delegate-marketplace]` of `~/.codex/config.toml` to `"v0.11.0"`, run '
             '`codex plugin marketplace upgrade delegate-marketplace` and `codex plugin add delegate@delegate-marketplace`, then reopen the session.\n')


class RenderTests(Fixture):
    def rendered(self):
        texts = rp.read_texts(self.repo)
        return rp.render(texts, OLD, NEW, 400, 3)[0]

    def test_release_notes_are_generated_from_unreleased(self):
        out = self.rendered()
        self.assertEqual(out['docs/releases/v0.11.0.md'],
            '# v0.11.0：示例改动\n\n简体中文 | [English](../en/releases/v0.11.0.md)\n\n这是示例版本的导语。\n\n'
            '## 示例改动\n\n- 做了一件事。\n\n## 影响面\n\n接口不变。\n\n## 验证与已知限制\n\n示例测试通过。\n\n'
            '本次发版准备实测：免费总验证 400 项 Python，循环注册的 Python 回归套 3 个。\n\n' + UPDATE_ZH)
        self.assertEqual(out['docs/en/releases/v0.11.0.md'],
            '# v0.11.0: Example change\n\n[简体中文](../../releases/v0.11.0.md) | English\n\nThis is the example introduction.\n\n'
            '## Example change\n\n- Did one thing.\n\n## Impact\n\nInterface unchanged.\n\n## Validation and known limitations\n\nExample tests pass.\n\n'
            'Release preparation measured: free validation 400 Python tests, 3 loop-registered Python regression suites.\n\n' + UPDATE_EN)

    def test_unreleased_notes_fold_to_one_paragraph(self):
        out = self.rendered()
        self.assertEqual(out['docs/releases/unreleased.md'],
            '# 未发布变更\n\n简体中文 | [English](../en/releases/unreleased.md)\n\n'
            '旧版本已归入 [v0.10.0 版本说明](v0.10.0.md)。v0.10.0 之后的示例改动已归入 [v0.11.0 版本说明](v0.11.0.md)。'
            'v0.11.0 之后暂无未发布变更。历史验收记录保留其发生时的版本和状态，不追认历史批准。\n')
        self.assertEqual(out['docs/en/releases/unreleased.md'],
            '# Unreleased changes\n\n[简体中文](../../releases/unreleased.md) | English\n\n'
            'Older versions are recorded in [v0.10.0 release notes](v0.10.0.md). Example change after v0.10.0 is recorded in '
            '[v0.11.0 release notes](v0.11.0.md). No unreleased changes after v0.11.0. '
            'Historical acceptance records retain their original version/status without retroactive approval.\n')

    def test_version_links_and_counts(self):
        out = self.rendered()
        self.assertEqual(out['plugins/delegate/.claude-plugin/plugin.json'], FILES['plugins/delegate/.claude-plugin/plugin.json'].replace('0.10.0', '0.11.0'))
        self.assertEqual(out['README.md'], (
            '仓库：[haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · 当前发行：[v0.11.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.11.0) · [文档索引](docs/README.md)\n\n'
            '发行源码由 `v0.11.0` 标签固定，`main` 会继续变化。\n\n'
            '发行变化见 [v0.11.0](docs/releases/v0.11.0.md)、[v0.10.0](docs/releases/v0.10.0.md)、[v0.9.0](docs/releases/v0.9.0.md) 与 [v0.5.0](docs/releases/v0.5.0.md)，后续修改见[未发布记录](docs/releases/unreleased.md)。\n\n'
            '总入口包含 3 个 shell 产品套、3 个循环注册的 Python 回归套。v0.11.0 发布验证为 400 项 Python、53 项 shell 和 19 项 eval；实际证据另列。\n'))
        self.assertEqual(out['README.en.md'], (
            'Repository: [haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · Current release: [v0.11.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.11.0) · [Documentation index](docs/en/README.md)\n\n'
            'The `v0.11.0` tag fixes release source at one revision, while `main` continues to change.\n\n'
            'Release changes are in [v0.11.0](docs/en/releases/v0.11.0.md), [v0.10.0](docs/en/releases/v0.10.0.md), [v0.9.0](docs/en/releases/v0.9.0.md) and [v0.5.0](docs/en/releases/v0.5.0.md).\n\n'
            'The entry point covers three shell product suites, 3 loop-registered Python regression suites. v0.11.0 release validation passed 400 Python, 53 shell and 19 eval cases. Evidence is separate.\n'))
        self.assertEqual(out['docs/README.md'], (
            '- 升级：读 [v0.11.0 版本说明](releases/v0.11.0.md)；后续变化看 [未发布记录](releases/unreleased.md)。\n\n'
            '| 当前发行 | [v0.11.0](releases/v0.11.0.md) | [v0.11.0](en/releases/v0.11.0.md) |\n'
            '| 旧版发行记录 | [v0.10.0](releases/v0.10.0.md)、[v0.9.0](releases/v0.9.0.md)、[v0.8.6](releases/v0.8.6.md) | [v0.10.0](en/releases/v0.10.0.md), [v0.9.0](en/releases/v0.9.0.md), [v0.8.6](en/releases/v0.8.6.md) |\n'))
        self.assertEqual(out['docs/en/README.md'], (
            '- Upgrading: read [v0.11.0 release notes](releases/v0.11.0.md); see Unreleased for later changes.\n\n'
            '| Current release | [v0.11.0](../releases/v0.11.0.md) | [v0.11.0](releases/v0.11.0.md) |\n'
            '| Previous release records | [v0.10.0](../releases/v0.10.0.md)、[v0.9.0](../releases/v0.9.0.md)、[v0.8.6](../releases/v0.8.6.md) | [v0.10.0](releases/v0.10.0.md), [v0.9.0](releases/v0.9.0.md), [v0.8.6](releases/v0.8.6.md) |\n'))
        self.assertEqual(out['CONTRIBUTING.md'], '总入口检查语法。v0.11.0 发布验证为 400 项 Python、53 项 shell 和 19 项 eval（v0.10.0 为 388 项，v0.9.0 为 354 项，v0.5.0 为 157 项 Python）；总入口包含 3 个循环注册的 Python 回归套。\n')
        self.assertEqual(out['CONTRIBUTING.en.md'], 'The entry point checks syntax. v0.11.0 release validation passed 400 Python, 53 shell and 19 eval cases (v0.10.0: 388 Python; v0.9.0: 354 Python; v0.5.0: 157 Python). The aggregate includes 3 loop-registered Python regression suites.\n')

    def test_placeholder_count_is_used_until_measured(self):
        texts = rp.read_texts(self.repo)
        out, titles = rp.render(texts, OLD, NEW, rp.PLACEHOLDER, 3)
        self.assertEqual(titles, {'zh': '示例改动', 'en': 'Example change'})
        self.assertIn(rp.PLACEHOLDER, out['README.md'])
        self.assertIn(rp.PLACEHOLDER, out['docs/releases/v0.11.0.md'])
        self.assertNotIn(rp.PLACEHOLDER, out['docs/releases/unreleased.md'])


class CheckAndReportTests(Fixture):
    def test_check_mode_reports_counts_checks_steps_and_interface(self):
        code, report = self.run_main(NEW, '--check')
        self.assertEqual(code, 0, report)
        self.assertEqual((report['mode'], report['status'], report['reason']), ('check', 'ready', None))
        self.assertEqual(report['version'], {'before': OLD, 'after': NEW})
        self.assertEqual(report['interface'], {'last_release': '1.5', 'now': '1.5'})
        self.assertEqual(report['base'], {'ref': 'origin/main', 'sha': self.base})
        self.assertEqual(report['release'], {'branch': 'release/v0.11.0', 'sha': None, 'reused': False})
        self.assertEqual(report['notes'], {'title': '示例改动', 'zh': 'docs/releases/v0.11.0.md', 'en': 'docs/en/releases/v0.11.0.md'})
        self.assertEqual(report['tests'], {'python': 400, 'loop_suites': 3})
        self.assertEqual([item['name'] for item in report['checks']], list(rp.CHECK_NAMES))
        for item in report['checks']:
            self.assertIsInstance(item['command'], list)
            self.assertEqual(item['exit_code'], 0)
        self.assertEqual(len(report['human_steps']), 7)
        for step in report['human_steps']:
            self.assertTrue(step['command'].strip() and step['why'].strip(), step)
        self.assertIn('v0.11.0', report['human_steps'][2]['command'])

    def test_failed_check_stops_and_lists_checks_run_so_far(self):
        code, report = self.run_main(NEW, '--check', checks=self.checks(fail='plugin-validate-plugin'))
        self.assertEqual((code, report['reason']), (1, 'check_failed'))
        self.assertEqual([(item['name'], item['exit_code']) for item in report['checks']],
                         [('validate', 0), ('plugin-validate-marketplace', 0), ('plugin-validate-plugin', 1)])
        self.assertEqual(report['human_steps'], [])

    def test_missing_command_is_check_unavailable(self):
        code, report = self.run_main(NEW, '--check', checks=self.checks(missing='verify-artifacts'))
        self.assertEqual((code, report['reason']), (1, 'check_unavailable'))
        self.assertIsNone(report['checks'][-1]['exit_code'])
        code, report = self.run_main(NEW, '--check', checks=[(name, None) if name == 'diff-check' else (name, argv)
                                                             for name, argv in self.checks()])
        self.assertEqual(report['reason'], 'check_unavailable')

    def test_validate_without_test_count_is_a_failure(self):
        checks = [(name, ['/bin/sh', '-c', 'echo ok'] if name == 'validate' else argv) for name, argv in self.checks()]
        code, report = self.run_main(NEW, '--check', checks=checks)
        self.assertEqual(report['reason'], 'check_failed')

    def test_loop_suites_counts_the_python_loop_not_the_shell_loop(self):
        self.write('scripts/validate.sh', '#!/bin/bash\nfor SUITE in channel detection routing; do\n'
                   '  /bin/bash "plugins/delegate/tests/test-${SUITE}.sh"\ndone\n'
                   'for SUITE in a b c d e; do\n  python3 -B "plugins/delegate/tests/test-${SUITE}.py"\ndone\n')
        self.assertEqual(rp.loop_suites(self.repo), 5)
        self.assertEqual(rp.loop_suites(ROOT), len(next(line for line in (ROOT / 'scripts/validate.sh').read_text().splitlines()
                                                        if line.startswith('for SUITE in backend ')).split()) - 4)

    def test_default_checks_resolve_spec_guard_from_installed_record(self):
        record = self.repo.parent / 'installed_plugins.json'
        record.write_text(json.dumps({'plugins': {'spec-guard@spec-guard-marketplace': [{'installPath': '/opt/sg/1.0'}]}}))
        checks = dict(rp.default_checks(self.repo, installed=record))
        self.assertEqual(checks['verify-artifacts'], ['/bin/bash', '/opt/sg/1.0/hooks/verify-artifacts.sh'])
        self.assertEqual(checks['validate'], ['/bin/bash', 'scripts/validate.sh'])
        self.assertEqual(checks['plugin-validate-plugin'][-3:], ['plugin', 'validate', './plugins/delegate'])
        record.write_text(json.dumps({'plugins': {}}))
        self.assertIsNone(dict(rp.default_checks(self.repo, installed=record))['verify-artifacts'])


class PrepareTests(Fixture):
    BRANCH = 'release/v0.11.0'

    def branch_exists(self):
        return subprocess.run(['git', '-C', str(self.repo), 'rev-parse', '--verify', '--quiet', 'refs/heads/' + self.BRANCH],
                              capture_output=True, stdin=subprocess.DEVNULL).returncode == 0

    def test_check_mode_writes_nothing(self):
        before = self.snapshot()
        code, report = self.run_main(NEW, '--check')
        self.assertEqual(code, 0, report)
        self.assertEqual(self.snapshot(), before)

    def test_prepare_makes_exactly_one_commit_with_trailer(self):
        code, report = self.run_main(NEW)
        self.assertEqual(code, 0, report)
        self.assertEqual((report['mode'], report['status'], report['release']['reused']), ('prepare', 'ready', False))
        sha = report['release']['sha']
        self.assertRegex(sha, r'^[0-9a-f]{40}$')
        self.assertEqual(git(self.repo, 'rev-parse', '--abbrev-ref', 'HEAD'), self.BRANCH)
        self.assertEqual(git(self.repo, 'rev-parse', 'HEAD'), sha)
        self.assertEqual(git(self.repo, 'rev-parse', sha + '^'), self.base)
        message = git(self.repo, 'log', '-1', '--format=%B', sha)
        self.assertTrue(message.startswith('chore: 准备 v0.11.0 发行'), message)
        self.assertTrue(message.rstrip().endswith('Release-Prepare: v0.11.0'), message)
        self.assertEqual(git(self.repo, 'status', '--porcelain', '--untracked-files=all'), '')
        expected, _ = rp.render({name: text for name, text in rp.read_texts_at(self.repo, self.base).items()}, OLD, NEW, 400, 3)
        for name, text in expected.items():
            self.assertEqual((self.repo / name).read_text(encoding='utf-8'), text, name)
        changed = set(git(self.repo, 'diff', '--name-only', self.base, sha).split())
        self.assertEqual(changed, set(expected))
        self.assertEqual(report['tests'], {'python': 400, 'loop_suites': 3})

    def test_failed_check_leaves_no_commit_no_branch_and_returns(self):
        for fail in ('validate', 'diff-check', 'verify-artifacts'):
            before = self.snapshot()
            code, report = self.run_main(NEW, checks=self.checks(fail=fail))
            self.assertEqual((code, report['reason']), (1, 'check_failed'), fail)
            self.assertIsNone(report['release']['sha'])
            self.assertFalse(self.branch_exists())
            self.assertEqual(self.snapshot(), before, fail)

    def test_rerun_reuses_the_same_commit(self):
        code, first = self.run_main(NEW)
        self.assertEqual(code, 0, first)
        git(self.repo, 'checkout', '-q', 'main')
        code, second = self.run_main(NEW)
        self.assertEqual(code, 0, second)
        self.assertTrue(second['release']['reused'])
        self.assertEqual(second['release']['sha'], first['release']['sha'])
        self.assertEqual(git(self.repo, 'rev-list', '--count', '%s..%s' % (self.base, self.BRANCH)), '1')
        git(self.repo, 'checkout', '-q', 'main')
        code, failed = self.run_main(NEW, checks=self.checks(fail='validate'))
        self.assertEqual((code, failed['reason'], failed['release']['sha']), (1, 'check_failed', first['release']['sha']))
        self.assertTrue(self.branch_exists())
        self.assertEqual(git(self.repo, 'rev-parse', '--abbrev-ref', 'HEAD'), 'main')

    def test_foreign_release_branch_is_refused(self):
        git(self.repo, 'branch', self.BRANCH)
        git(self.repo, 'checkout', '-q', self.BRANCH)
        self.write('extra.txt', 'x\n')
        git(self.repo, 'add', 'extra.txt')
        git(self.repo, 'commit', '-qm', '别人的提交')
        git(self.repo, 'checkout', '-q', 'main')
        before = self.snapshot()
        code, report = self.run_main(NEW)
        self.assertEqual((code, report['reason']), (1, 'release_branch_conflict'))
        self.assertEqual(self.snapshot(), before)

    def test_stdin_is_never_read(self):
        class Forbidden:
            def read(self, *args):
                raise AssertionError('stdin read')
            readline = read
        saved = sys.stdin
        sys.stdin = Forbidden()
        try:
            code, report = self.run_main(NEW)
        finally:
            sys.stdin = saved
        self.assertEqual(code, 0, report)
        self.assertIn('</dev/null', (ROOT / 'scripts/release-prepare.sh').read_text())

if __name__ == '__main__':
    unittest.main()
