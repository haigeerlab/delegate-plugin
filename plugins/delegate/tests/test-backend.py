#!/usr/bin/env python3
"""Regression coverage for authentication, cache identity and hook integration."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--root', default=str(Path(__file__).resolve().parents[3]))
arguments, remaining = parser.parse_known_args()
ROOT = Path(arguments.root).resolve()
sys.argv = [sys.argv[0]] + remaining

FAKE_CODEX = '''#!/usr/bin/env python3
import json, os, signal, subprocess, sys, time
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['STUB_CALL_LOG'], 'a') as output:
    output.write(json.dumps(args) + '\\n')
if args == ['--version']:
    print('codex test')
    sys.exit(int(os.environ.get('STUB_VERSION_EXIT', '0')))
if args == ['login', 'status']:
    if os.environ.get('STUB_LOGIN_HANG'):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(8); open(%r, "w").write("late")' % os.environ['STUB_CHILD_MARKER']])
        Path(os.environ['STUB_CHILD_PID']).write_text(str(child.pid))
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        while True: time.sleep(.1)
    print(os.environ.get('STUB_LOGIN_TEXT', 'Logged in using ChatGPT'))
    sys.exit(int(os.environ.get('STUB_LOGIN_EXIT', '0')))
if args and args[0] == 'exec':
    Path(args[args.index('-o') + 1]).write_text('answer')
    sys.exit(0)
sys.exit(64)
'''


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='delegate-backend-test.')
        self.base = Path(self.temporary.name)
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        fake = self.bin / 'codex'
        fake.write_text(FAKE_CODEX)
        fake.chmod(0o755)
        self.home = self.base / 'home'
        (self.home / '.codex').mkdir(parents=True)
        (self.home / '.codex/auth.json').write_text('{}')
        self.codex_home = self.base / 'custom-codex-home'
        self.codex_home.mkdir()
        self.calls = self.base / 'calls.jsonl'
        self.env = dict(os.environ, HOME=str(self.home), CODEX_HOME=str(self.codex_home),
                        PATH=str(self.bin) + ':' + str(Path(sys.executable).parent) + ':/usr/bin:/bin',
                        TMPDIR=str(self.base / 'tmp'), STUB_CALL_LOG=str(self.calls),
                        PYTHONDONTWRITEBYTECODE='1')
        for name in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'CODEX_AUTH_FILE', 'CODEX_AGENTS_FILE'):
            self.env.pop(name, None)
        self.repo = self.base / 'project'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.detect = ROOT / 'plugins/delegate/hooks/detect.sh'
        self.wrapper = ROOT / 'plugins/delegate/scripts/codex-exec.sh'

    def tearDown(self):
        self.temporary.cleanup()

    def run_script(self, path, *args, env=None):
        return subprocess.run(['/bin/bash', str(path)] + list(args), env=env or self.env,
                              cwd=self.repo, capture_output=True, text=True, timeout=10)

    def test_chatgpt_login_does_not_require_auth_json(self):
        # The fake CLI represents a successful keyring or custom-home login.
        (self.home / '.codex/auth.json').unlink()
        output = self.run_script(self.detect, '--print')
        self.assertEqual(output.stdout.strip(), '可用')
        self.assertIn(['login', 'status'], [json.loads(line) for line in self.calls.read_text().splitlines()])

    def test_login_timeout_kills_group_with_inherited_output(self):
        pid_file = self.base / 'probe-child.pid'
        marker = self.base / 'probe-child.marker'
        env = dict(self.env, STUB_LOGIN_HANG='1', STUB_CHILD_PID=str(pid_file), STUB_CHILD_MARKER=str(marker))
        result = subprocess.run([str(self.detect), '--print'], env=env, capture_output=True,
                                text=True, timeout=15)
        self.assertIn('不可用', result.stdout)
        self.assertTrue(pid_file.exists(), 'login probe child did not start')
        time.sleep(3)
        self.assertFalse(marker.exists(), 'login probe descendant survived deadline')

    def test_live_harness_accepts_cli_auth_without_auth_json_and_short_logs(self):
        (self.home / '.codex/auth.json').unlink()
        (self.base / 'tmp').mkdir()
        result = subprocess.run(['/bin/bash', str(ROOT / 'plugins/delegate/tests/test-channel.sh'), '--live'],
                                cwd=self.base, env=self.env, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-1000:])
        self.assertIn('LIVE：真实只读委托答复非空', result.stdout)

    def test_api_key_and_unknown_login_are_rejected_without_echoing_credentials(self):
        for text in ('Logged in using an API key - TEST_API_SECRET', 'Unrecognized login method'):
            with self.subTest(text=text):
                self.calls.write_text('')
                env = dict(self.env, STUB_LOGIN_TEXT=text)
                output = self.run_script(self.wrapper, 'readonly check', env=env)
                self.assertNotEqual(output.returncode, 0)
                self.assertIn('ChatGPT', output.stderr)
                self.assertNotIn('TEST_API_SECRET', output.stdout + output.stderr)
                calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
                self.assertFalse(any(call and call[0] == 'exec' for call in calls))

    def test_exec_enforces_chatgpt_and_openai_provider(self):
        output = self.run_script(self.wrapper, 'readonly check')
        self.assertEqual(output.returncode, 0, output.stderr)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        call = next(call for call in calls if call[0] == 'exec')
        self.assertIn('forced_login_method="chatgpt"', call)
        self.assertIn('model_provider="openai"', call)

    def test_failed_login_is_not_reported_as_available(self):
        output = self.run_script(self.detect, '--print', env=dict(self.env, STUB_LOGIN_EXIT='1'))
        self.assertIn('不可用', output.stdout)
        self.assertEqual(output.returncode, 0)

    def test_doctor_refreshes_a_previously_unavailable_cache(self):
        self.run_script(self.detect, '--session-start', env=dict(self.env, STUB_VERSION_EXIT='1'))
        output = self.run_script(ROOT / 'plugins/delegate/hooks/doctor.sh')
        self.assertIn('\n可用\n', output.stdout)
        self.assertNotIn('发现 1 个问题', output.stdout)

    def test_cache_from_other_codex_home_is_not_reused(self):
        self.run_script(self.detect, '--session-start')
        self.calls.write_text('')
        output = self.run_script(self.detect, env=dict(self.env, CODEX_HOME=str(self.base / 'other-home'), STUB_LOGIN_EXIT='1'))
        self.assertEqual(output.stdout, '')
        self.assertTrue(self.calls.read_text(), 'authentication home change must trigger a fresh check')

    def test_future_cache_timestamp_triggers_a_fresh_check(self):
        self.run_script(self.detect, '--session-start')
        cache = self.base / 'tmp/delegate/detection.json'
        data = json.loads(cache.read_text())
        data['checkedAt'] = time.time() + 3600
        cache.write_text(json.dumps(data))
        self.calls.write_text('')
        self.run_script(self.detect)
        self.assertTrue(self.calls.read_text(), 'future timestamps must not extend cache freshness')

    def test_prompt_cold_cache_injects_one_confirmation_pointer(self):
        output = self.run_script(ROOT / 'plugins/delegate/hooks/prompt.sh')
        self.assertEqual(output.returncode, 0)
        self.assertEqual(len(output.stdout.splitlines()), 1)
        context = json.loads(output.stdout)['hookSpecificOutput']['additionalContext']
        self.assertIn('等用户确认', context)
        hooks = json.loads((ROOT / 'plugins/delegate/hooks/hooks.json').read_text())
        handlers = hooks['hooks']['UserPromptSubmit'][0]['hooks']
        self.assertEqual(len(handlers), 1)
        self.assertIn('/hooks/prompt.sh', handlers[0]['command'])


if __name__ == '__main__':
    unittest.main()
