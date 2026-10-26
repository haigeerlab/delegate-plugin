#!/usr/bin/env python3
"""Temporary Codex project trust for write runs; the user's Codex configuration is only read."""
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))
SCRIPT = PLUGIN / 'scripts' / 'codex_trust.py'

ROOT = '/work/repo'
KEYS = [ROOT + '/sub', ROOT]


def git(cwd, *args):
    subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True)


def make_repo(path):
    path.mkdir()
    git(path, 'init', '-q')
    (path / 'f').write_text('x\n', encoding='utf-8')
    git(path, 'add', 'f')
    git(path, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'init')


class TrustUnitTests(unittest.TestCase):
    def setUp(self):
        self.trust = importlib.import_module('codex_trust')

    def decide(self, config, keys=KEYS, root=ROOT):
        return self.trust.decide(config, keys, root)

    def test_override_value(self):
        self.assertEqual(self.trust.override(ROOT), 'projects={"/work/repo"={trust_level="trusted"}}')

    def test_missing_config_gets_override(self):
        self.assertEqual(self.decide(None), (self.trust.override(ROOT), None))

    def test_unrelated_config_gets_override(self):
        config = ('model = "gpt"\n[projects."/work/repo-sub"]\ntrust_level = "untrusted"\n'
                  '[projects."/work/repo/sub/deeper"]\ntrust_level = "untrusted"\n').encode()
        self.assertEqual(self.decide(config), (self.trust.override(ROOT), None))

    def test_existing_entry_in_any_form_blocks_override(self):
        forms = [
            '[projects."/work/repo"]\ntrust_level = "trusted"\n',
            '[projects."/work/repo"]\ntrust_level = "untrusted"\n',
            'projects."/work/repo".trust_level = "untrusted"\n',
            'projects = { "/work/repo" = { trust_level = "untrusted" } }\n',
            "[projects.'/work/repo']\ntrust_level = 'untrusted'\n",
            '[projects."/work/repo/sub"]\ntrust_level = "untrusted"\n',
        ]
        for text in forms:
            self.assertEqual(self.decide(text.encode()), (None, None), text)

    def test_unknown_root(self):
        self.assertEqual(self.decide(None, root=None), (None, self.trust.REASON_ROOT))

    def test_unsafe_path(self):
        for bad in ('/work/re"po', '/work/re\\po', '/work/re\npo', '/work/re\x7fpo'):
            self.assertEqual(self.decide(None, keys=[bad, ROOT]), (None, self.trust.REASON_PATH), repr(bad))
            self.assertEqual(self.decide(None, keys=[bad], root=bad), (None, self.trust.REASON_PATH), repr(bad))

    def test_not_utf8(self):
        self.assertEqual(self.decide(b'model = "\xff"\n'), (None, self.trust.REASON_ENCODING))

    def test_trust_root(self):
        self.assertEqual(self.trust.trust_root('/work/repo/.git'), '/work/repo')
        self.assertEqual(self.trust.trust_root('/work/repo/.git/'), '/work/repo')
        self.assertIsNone(self.trust.trust_root('/work/repo/.git/modules/sub'))
        self.assertIsNone(self.trust.trust_root('/work/bare.git'))
        self.assertIsNone(self.trust.trust_root(''))

    def test_candidate_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            real = Path(temp).resolve() / 'real'
            real.mkdir()
            link = Path(temp).resolve() / 'link'
            link.symlink_to(real)
            keys = self.trust.candidate_keys(str(real), str(link), str(real))
            self.assertEqual(keys, [str(real), str(link)])
            self.assertEqual(self.trust.candidate_keys(str(real), '/elsewhere', '/root'),
                             [str(real), '/root'])

    def test_unreadable_config(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'config.toml'
            self.assertEqual(self.trust.read_config(str(path)), (None, None))
            path.write_bytes(b'model = "x"\n')
            self.assertEqual(self.trust.read_config(str(path)), (b'model = "x"\n', None))
            path.chmod(0)
            try:
                if os.access(str(path), os.R_OK):
                    self.skipTest('running with privileges that ignore file modes')
                self.assertEqual(self.trust.read_config(str(path)), (None, self.trust.REASON_UNREADABLE))
            finally:
                path.chmod(0o600)

    def test_notice(self):
        self.assertEqual(self.trust.notice(self.trust.REASON_ROOT, '/h/.codex/config.toml'),
                         'delegate: 未能确认 Codex 用户配置里有没有本仓库的信任条目（无法确定 Git 信任根），'
                         '本次不加临时信任；Codex 可能会往 /h/.codex/config.toml 写入一条信任记录。')


class RepositoryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-write-trust-')
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'codex-home'
        self.home.mkdir()
        self.config = self.home / 'config.toml'
        self.main = self.base / 'main'
        make_repo(self.main)
        (self.main / 'sub').mkdir()
        self.worktree = self.base / 'main-wt'
        git(self.main, 'worktree', 'add', '-q', str(self.worktree))
        (self.worktree / 'sub').mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def expected(self, root):
        return 'projects={"%s"={trust_level="trusted"}}\n' % root


class TrustCommandTests(RepositoryFixture):
    def run_trust(self, cwd, **env):
        merged = dict(os.environ, CODEX_HOME=str(self.home), PWD=str(cwd), **env)
        return subprocess.run([sys.executable, '-B', str(SCRIPT)], cwd=str(cwd), env=merged,
                              capture_output=True, text=True, check=False)

    def test_override_key_is_main_repository(self):
        for cwd in (self.main, self.main / 'sub', self.worktree, self.worktree / 'sub'):
            result = self.run_trust(cwd)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, self.expected(self.main), ''), cwd)

    def test_existing_entries_block_override(self):
        for key in (self.main, self.worktree):
            self.config.write_text('[projects."%s"]\ntrust_level = "untrusted"\n' % key, encoding='utf-8')
            result = self.run_trust(self.worktree)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''), key)

    def test_uncertain_prints_notice_only(self):
        self.config.write_bytes(b'\xff\n')
        result = self.run_trust(self.main)
        self.assertEqual((result.returncode, result.stdout), (0, ''))
        self.assertIn('配置文件不是 UTF-8', result.stderr)
        self.assertIn(str(self.config), result.stderr)

    def test_default_codex_home(self):
        env = {k: v for k, v in os.environ.items() if k != 'CODEX_HOME'}
        env.update(HOME=str(self.base), PWD=str(self.main))
        result = subprocess.run([sys.executable, '-B', str(SCRIPT)], cwd=str(self.main), env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout), (0, self.expected(self.main)))
        (self.base / '.codex').mkdir()
        (self.base / '.codex' / 'config.toml').write_text('[projects."%s"]\n' % self.main, encoding='utf-8')
        result = subprocess.run([sys.executable, '-B', str(SCRIPT)], cwd=str(self.main), env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout), (0, ''))

    def test_config_is_never_written(self):
        self.config.write_text('model = "x"\n', encoding='utf-8')
        before = (self.config.read_bytes(), self.config.stat().st_mtime_ns, sorted(os.listdir(self.home)))
        self.run_trust(self.worktree / 'sub')
        after = (self.config.read_bytes(), self.config.stat().st_mtime_ns, sorted(os.listdir(self.home)))
        self.assertEqual(before, after)


FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
if args == ["--version"]:
    print("codex stub 1.0")
    raise SystemExit(0)
if args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT")
    raise SystemExit(0)
with open(os.environ["STUB_CALL_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args, ensure_ascii=False) + "\n")
print("OpenAI Codex v0.162.1\n--------\nsession id: 01a15f3b-0f2c-7d82-b5cc-7a1f711c11d2\n--------")
for index, arg in enumerate(args[:-1]):
    if arg == "-o":
        with open(args[index + 1], "w", encoding="utf-8") as answer:
            answer.write(os.environ.get("STUB_ANSWER", "fake answer\n"))
'''
APPROVAL = 'approval_policy="never"'


class WriteRunTests(RepositoryFixture):
    def setUp(self):
        super().setUp()
        (self.base / 'bin').mkdir()
        fake = self.base / 'bin' / 'codex'
        fake.write_text(FAKE_CODEX, encoding='utf-8')
        fake.chmod(0o755)
        (self.base / 'tmp').mkdir()
        self.calls = self.base / 'calls.log'
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'DELEGATE_REVIEW_DEPTH')}
        self.env.update(PATH='%s:%s:/usr/bin:/bin' % (self.base / 'bin', Path(sys.executable).parent),
                        TMPDIR=str(self.base / 'tmp'), STUB_CALL_LOG=str(self.calls),
                        CODEX_HOME=str(self.home), DELEGATE_TIMEOUT_SECONDS='20')

    def run_delegate(self, *args, cwd=None, **env):
        cwd = cwd or self.main
        merged = dict(self.env, PWD=str(cwd), **env)
        return subprocess.run(['/bin/bash', str(PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run', *args],
                              cwd=str(cwd), env=merged, capture_output=True, text=True, timeout=60)

    def last_call(self):
        import json
        return json.loads(self.calls.read_text(encoding='utf-8').splitlines()[-1])

    def trust_args(self, call):
        return [call[index + 1] for index, arg in enumerate(call[:-1])
                if arg == '-c' and call[index + 1].startswith('projects=')]

    def assert_override(self, call):
        position = call.index(APPROVAL)
        self.assertEqual(call[position + 1:position + 3], ['-c', self.expected(self.main).rstrip('\n')], call)
        self.assertEqual(len(self.trust_args(call)), 1, call)

    def run_id(self, output):
        self.assertEqual(output.returncode, 0, output.stderr)
        return output.stdout.rstrip('\n').splitlines()[-1].split()[1].split('=')[1]

    def test_write_run_overrides_with_main_repository(self):
        for cwd in (self.main, self.main / 'sub', self.worktree, self.worktree / 'sub'):
            output = self.run_delegate('--write', '--', '任务', cwd=cwd)
            self.assertEqual(output.returncode, 0, output.stderr)
            self.assertNotIn('信任条目', output.stderr)
            self.assert_override(self.last_call())

    def test_read_only_run_has_no_override(self):
        output = self.run_delegate('--', '任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(self.trust_args(self.last_call()), [])

    def test_existing_entry_keeps_arguments(self):
        self.config.write_text('[projects."%s"]\ntrust_level = "untrusted"\n' % self.main, encoding='utf-8')
        output = self.run_delegate('--write', '--', '任务', cwd=self.worktree / 'sub')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(self.trust_args(self.last_call()), [])

    def test_uncertain_config_warns_and_runs_unchanged(self):
        self.config.write_bytes(b'\xff\n')
        output = self.run_delegate('--write', '--', '任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertIn('delegate: 未能确认 Codex 用户配置里有没有本仓库的信任条目（配置文件不是 UTF-8）', output.stderr)
        self.assertEqual(self.trust_args(self.last_call()), [])

    def test_resumable_and_resume_follow_write_mode(self):
        ask = {'STUB_ANSWER': 'NEED_USER: 选 A？\n'}
        first = self.run_id(self.run_delegate('--resumable', '--write', '--', '任务', **ask))
        self.assert_override(self.last_call())
        self.run_id(self.run_delegate('--resume', first, '--write', '--', '选 A'))
        call = self.last_call()
        self.assertEqual(call[:2], ['exec', 'resume'])
        self.assert_override(call)
        reading = self.run_id(self.run_delegate('--resumable', '--', '任务', **ask))
        self.assertEqual(self.trust_args(self.last_call()), [])
        self.run_id(self.run_delegate('--resume', reading, '--', '选 A'))
        self.assertEqual(self.last_call()[:2], ['exec', 'resume'])
        self.assertEqual(self.trust_args(self.last_call()), [])

    def test_config_is_never_written(self):
        self.config.write_text('model = "x"\n', encoding='utf-8')
        before = (self.config.read_bytes(), self.config.stat().st_mtime_ns, sorted(os.listdir(self.home)))
        self.assertEqual(self.run_delegate('--write', '--', '任务').returncode, 0)
        after = (self.config.read_bytes(), self.config.stat().st_mtime_ns, sorted(os.listdir(self.home)))
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
