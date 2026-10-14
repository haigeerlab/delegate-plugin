#!/usr/bin/env python3
"""Opt-in actual Mac public path using a fixed synthetic CLI, never a model."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--srt', required=True)
parser.add_argument('--node', required=True)
arguments, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]] + remaining
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from claude_review import VISIBLE_FLAGS

FAKE = '''#!/bin/bash
set -u
case "${@: -1}" in
  --version) printf '2.1.295 (Claude Code)\\n'; exit 0 ;;
  --help) printf '%s\\n' '__FLAGS__'; exit 0 ;;
  --json) printf '%s\\n' '{"loggedIn":true,"authMethod":"claude.ai","apiProvider":"firstParty"}'; exit 0 ;;
esac
case " $* " in *' -p '*) ;; *) exit 64 ;; esac
prompt=$(cat)
case "$prompt" in *fixture-mode=empty*) exit 0 ;; esac
case "$prompt" in *fixture-mode=malformed*) printf 'FIXTURE_SECRET_NOT_A_CREDENTIAL\\n'; exit 0 ;; esac
case "$prompt" in
  *fixture-mode=unsafe*) printf '%s\\n' '{"type":"system","subtype":"init","tools":["Bash"],"mcp_servers":[]}'; sleep 20; exit 1 ;;
esac
printf '%s\\n' '{"type":"system","subtype":"ui_invalidate","event":"ui.render"}'
printf '%s\\n' '{"type":"system","subtype":"init","tools":["Read","EndConversation","StructuredOutput"],"mcp_servers":[],"model":"claude-synthetic-fixture"}'
case "$prompt" in *fixture-mode=hang*) sleep 20 & wait; exit 1 ;; esac
if (printf changed >data/src/a.py) 2>/dev/null; then exit 95; fi
denials='[]'
case "$prompt" in *fixture-mode=denied*) denials='[{"tool_name":"Write","tool_input":{"file_path":"data/src/a.py"}}]' ;; esac
printf '%s\\n' '{"type":"result","subtype":"success","is_error":false,"permission_denials":'"${denials}"',"structured_output":{"schema_version":1,"reviewed":["src/a.py"],"unreviewed":[],"findings":[]}}'
'''.replace('__FLAGS__', ' '.join(VISIBLE_FLAGS))


class NativeIntegration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='delegate-public-mac.', dir='/private/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / 'repo'; self.repo.mkdir(mode=0o700)
        (self.repo / 'src').mkdir(); (self.repo / 'src/a.py').write_text('fixture line\n')
        fake = self.root / 'fake-claude'; fake.write_text(FAKE); fake.chmod(0o700)
        home = self.root / 'home'; home.mkdir(mode=0o700)
        self.env = {'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin', 'HOME': str(home),
            'TMPDIR': str(self.root), 'PYTHONDONTWRITEBYTECODE': '1',
            'DELEGATE_CLAUDE_BIN': str(fake), 'DELEGATE_SRT_BIN': arguments.srt,
            'DELEGATE_NODE_BIN': arguments.node, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1'}
        for args in (['init', '-q'], ['add', 'src/a.py'],
                ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture']):
            subprocess.run(['/usr/bin/git', '-C', str(self.repo), *args], env=self.env, check=True)
        self.context = self.root / 'context.json'
        self.context.write_text(json.dumps({'schema_version': 1, 'repository': str(self.repo),
            'working_directory': str(self.repo), 'review_type': 'paths',
            'scope': {'include': ['src/a.py'], 'exclude': []},
            'baseline': {'mode': 'commits', 'from': 'HEAD', 'to': 'HEAD'},
            'context_files': [], 'acceptance_criteria': ['Synthetic fixture only'],
            'uncommitted_changes': {'staged': False, 'unstaged': False, 'untracked': False},
            'allowed_tools': ['Read'], 'stop_conditions': ['scope_complete', 'permission_denied',
                'context_missing', 'limit_reached', 'input_changed']}))
        self.command = ['/bin/bash', str(SCRIPTS / 'delegate-exec.sh'), 'review', '--backend', 'claude-code',
            '--context', str(self.context), '--model', 'sonnet']

    def verify(self, result, status, code):
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, code, {key: report[key] for key in
            ('execution_status', 'cleanup', 'diagnostics')})
        self.assertEqual(report['backend'], 'claude-code')
        self.assertEqual(report['execution_environment'], 'native')
        self.assertEqual(report['execution_status'], status, report)
        self.assertEqual(report['cleanup'], 'confirmed', report)
        self.assertEqual((self.repo / 'src/a.py').read_text(), 'fixture line\n')
        self.assertEqual(subprocess.check_output(['/usr/bin/git', '-C', str(self.repo), 'status', '--porcelain'], env=self.env), b'')
        for path in (self.root / 'delegate-review').glob('*'):
            self.assertNotIn('FIXTURE_SECRET_NOT_A_CREDENTIAL', path.read_text())
        self.assertNotIn('FIXTURE_SECRET_NOT_A_CREDENTIAL', result.stdout + result.stderr)
        return report

    def invoke(self, mode, timeout=None):
        environment = dict(self.env)
        if timeout:
            environment['DELEGATE_TIMEOUT_SECONDS'] = str(timeout)
        return subprocess.run(self.command + ['fixture-mode=' + mode], env=environment, cwd=self.repo,
            capture_output=True, text=True, timeout=20)

    def test_explicit_claude_starts_native_fixture_and_blocks_snapshot_write(self):
        report = self.verify(self.invoke('normal'), 'completed', 0)
        self.assertEqual(report['review_outcome'], 'no_findings_in_scope')
        self.assertEqual(report['reviewed'], ['src/a.py'])
        self.assertEqual(report['observed_models'], ['claude-synthetic-fixture'])

    def test_long_host_tmpdir_does_not_break_native_startup(self):
        # macOS supplies a long /private/var/folders TMPDIR by default. srt's
        # Unix proxy socket must fit Darwin's pathname limit independently.
        temporary = self.root / ('host-temporary-' + 'x' * 70)
        temporary.mkdir(mode=0o700)
        self.env['TMPDIR'] = str(temporary)
        self.verify(self.invoke('normal'), 'completed', 0)

    def test_empty_malformed_and_denied_are_inconclusive(self):
        for mode in ('empty', 'malformed', 'denied'):
            with self.subTest(mode=mode):
                report = self.verify(self.invoke(mode), 'failed', 1)
                self.assertEqual(report['review_outcome'], 'inconclusive')
                expected = {'empty': 'initial_output_empty', 'malformed': 'initial_output_invalid',
                    'denied': 'permission_denied'}[mode]
                self.assertIn(expected, report['diagnostics'])

    def test_unsafe_init_stops_before_deadline(self):
        report = self.verify(self.invoke('unsafe'), 'failed', 1)
        self.assertIn('tool_boundary_unverified', report['diagnostics'])
        self.assertIn('initial_tools_mismatch', report['diagnostics'])
        self.assertEqual(report['diagnostics'].count('tool_boundary_unverified'), 1)

    def test_timeout_is_not_empty_success(self):
        self.verify(self.invoke('hang', timeout=2), 'timed_out', 124)

    def test_real_cancel_cleans_this_native_job(self):
        existing = set(Path('/private/tmp').glob('delegate-native.*'))
        process = subprocess.Popen(self.command + ['fixture-mode=hang'], env=self.env, cwd=self.repo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            expires = time.monotonic() + 10
            while time.monotonic() < expires:
                outputs = []
                for root in set(Path('/private/tmp').glob('delegate-native.*')) - existing:
                    for request in root.glob('control/*/request'):
                        # Read only trusted startup metadata, and inspect output
                        # only after identifying this unique synthetic CLI.
                        try:
                            argv = json.loads(request.read_bytes())['argv']
                            output = request.parent / 'stdout'
                            if self.env['DELEGATE_CLAUDE_BIN'] in argv and '-p' in argv and output.exists():
                                outputs.append(output)
                        except (FileNotFoundError, ValueError, KeyError):
                            continue
                if any(b'"type":"system"' in path.read_bytes() for path in outputs):
                    break
                self.assertIsNone(process.poll(), 'public fixture exited before model stub')
                time.sleep(.02)
            else:
                self.fail('public model stub did not start')
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=8)
            result = subprocess.CompletedProcess(self.command, process.returncode, stdout, stderr)
            self.verify(result, 'cancelled', 143)
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=2)
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()


if __name__ == '__main__':
    if sys.platform != 'darwin' or not all(Path(path).is_absolute() and Path(path).is_file()
            for path in (arguments.srt, arguments.node)):
        parser.error('requires Mac and existing srt/node; only creates the fixed fake CLI')
    unittest.main(verbosity=2)
