#!/usr/bin/env python3
"""Offline output checks and opt-in, model-free Mac process-boundary tests."""
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
from unittest.mock import patch
import uuid

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--srt')
arguments, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]] + remaining
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import review_macos
from review_macos import MacBoundary, Kernel
from review_isolation import build_policy


class AnchorRecordTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.control = Path(self.temporary.name).resolve()
        (self.control / 'stdin').write_bytes(b'')
        (self.control / 'start').write_text(json.dumps({'coalition': 77}))

    def invoke(self, code):
        (self.control / 'request').write_text(json.dumps({
            'argv': [sys.executable, '-B', '-c', code], 'cwd': str(self.control),
            'environment': {}, 'deadline': 2, 'expected_tools': None,
            'target': 'fixture'}))
        with patch('review_macos.Kernel') as kernel, \
                patch('review_macos.subprocess.run'), patch('review_macos.time.sleep'):
            kernel.return_value.coalition.return_value = 77
            kernel.return_value.identity.return_value = {'generation': 1}
            review_macos.anchor(self.control)
        return json.loads((self.control / 'end').read_text())

    def test_normal_exit_records_stdout_bytes(self):
        end = self.invoke("import os; os.write(1, b'fixture completed\\n')")
        self.assertEqual(end['execution_status'], 'completed')
        self.assertEqual(type(end['stdout_bytes']), int)
        self.assertEqual(end['stdout_bytes'], len(b'fixture completed\n'))
        self.assertEqual(end['stderr_bytes'], 0)

    def test_nonzero_exit_records_stderr_bytes(self):
        end = self.invoke("import os; os.write(2, b'fixture error\\n'); raise SystemExit(7)")
        self.assertEqual(end['execution_status'], 'failed')
        self.assertEqual(type(end['stderr_bytes']), int)
        self.assertGreater(end['stderr_bytes'], 0)
        self.assertNotEqual(end['launcher_exit_code'], 0)

    def test_failure_before_open_has_no_byte_counts(self):
        (self.control / 'start').write_text(json.dumps({'coalition': 78}))
        end = self.invoke('pass')
        self.assertNotIn('stdout_bytes', end)
        self.assertNotIn('stderr_bytes', end)

    def test_unexpected_error_records_fixed_diagnostic_and_cleans(self):
        (self.control / 'request').write_text(json.dumps({
            'argv': ['/usr/bin/true'], 'cwd': str(self.control),
            'environment': {}, 'deadline': 2, 'expected_tools': None,
            'target': 'fixture'}))
        with patch('review_macos.Kernel') as kernel, \
                patch('review_macos.subprocess.Popen') as popen, \
                patch('review_macos.subprocess.run') as run, \
                patch('review_macos.time.sleep'), \
                patch('review_macos.os.fstat', side_effect=RuntimeError('SECRET_TEXT')):
            kernel.return_value.coalition.return_value = 77
            kernel.return_value.identity.return_value = {'generation': 1}
            popen.return_value.poll.return_value = 0
            popen.return_value.returncode = 0
            review_macos.anchor(self.control)
        raw = (self.control / 'end').read_text()
        end = json.loads(raw)
        self.assertTrue(end['backend_started'])
        self.assertIn('anchor_internal_error', end['diagnostics'])
        self.assertEqual(end['execution_status'], 'failed')
        self.assertEqual(end['cleanup'], 'confirmed')
        self.assertNotIn('SECRET_TEXT', raw)
        self.assertNotIn('RuntimeError', raw)
        kernel.return_value.clean.assert_called_once_with(77, anchor=os.getpid())
        popen.return_value.wait.assert_called_once_with(timeout=1)
        self.assertEqual(run.call_args.args[0], ['/bin/launchctl', 'bootout', 'fixture'])


class StdoutCheckTests(unittest.TestCase):
    def test_missing_file(self):
        self.assertEqual(review_macos.stdout_check(4, False, 0), 'missing')
        self.assertEqual(review_macos.stdout_check(0, False, 0), 'missing')

    def test_short_read(self):
        self.assertEqual(review_macos.stdout_check(4, True, 3), 'short')
        self.assertEqual(review_macos.stdout_check(4, True, 0), 'short')

    def test_complete_read(self):
        self.assertEqual(review_macos.stdout_check(4, True, 4), 'ok')
        self.assertEqual(review_macos.stdout_check(4, True, 5), 'ok')

    def test_empty_file(self):
        self.assertEqual(review_macos.stdout_check(0, True, 0), 'ok')

    def test_read_limit(self):
        limit = review_macos.LIMIT
        self.assertEqual(review_macos.stdout_check(limit + 2, True, limit + 1), 'ok')
        self.assertEqual(review_macos.stdout_check(limit + 2, True, limit), 'short')

    def test_missing_record(self):
        self.assertIsNone(review_macos.stdout_check(None, False, 0))
        self.assertIsNone(review_macos.stdout_check(None, True, 4))

    def test_noninteger_record(self):
        for recorded in ('4', 4.0, True):
            with self.subTest(recorded=recorded):
                self.assertIsNone(review_macos.stdout_check(recorded, True, 4))


class ControllerRecordTests(unittest.TestCase):
    def test_stdout_check_from_end_record(self):
        cases = [(4, None, 'missing'), (4, b'abc', 'short'), (4, b'abcd', 'ok'),
                 (0, b'', 'ok'), (None, b'abcd', None)]
        for recorded, output, expected in cases:
            with self.subTest(recorded=recorded, output=output), \
                    tempfile.TemporaryDirectory() as temporary:
                control = Path(temporary).resolve()
                def launchctl(*arguments):
                    if arguments[0] == 'bootstrap':
                        (control / 'ready').write_text(json.dumps({'pid': 123, 'generation': 1}))
                        end = {'execution_status': 'completed', 'diagnostics': []}
                        if recorded is not None:
                            end['stdout_bytes'] = recorded
                        (control / 'end').write_text(json.dumps(end))
                        if output is not None:
                            (control / 'stdout').write_bytes(output)
                    return 0
                with patch('review_macos.Kernel') as kernel, \
                        patch.object(MacBoundary, 'launchctl', side_effect=launchctl), \
                        patch.object(MacBoundary, 'service_loaded', return_value=False):
                    kernel.return_value.identity.return_value = {'generation': 1}
                    kernel.return_value.coalition.side_effect = lambda pid: 77 if pid == 123 else 88
                    kernel.return_value.count.side_effect = [1, 0]
                    kernel.return_value.members.return_value = [{'pid': 123}]
                    result = MacBoundary(control).run(['/usr/bin/true'], cwd=control,
                        environment={}, deadline=1)
                self.assertEqual(result['execution_status'], 'completed')
                self.assertEqual(result['diagnostics'], [])
                if expected is None:
                    self.assertNotIn('stdout_check', result)
                else:
                    self.assertEqual(result['stdout_check'], expected)


@unittest.skipUnless(arguments.srt, 'requires explicit --srt for Mac process fixtures')
class MacBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='delegate-mac-test.', dir='/private/tmp')
        self.root = Path(self.temporary.name).resolve()
        self.snapshot, self.writable, self.home, self.control = [self.root / name for name in
            ('snapshot', 'writable', 'home', 'control')]
        for path in (self.snapshot, self.writable, self.home, self.control):
            path.mkdir(mode=0o700)
        self.python = Path(sys.executable).resolve()
        self.kernel = Kernel()
        self.config = self.root / 'policy.json'
        self.config.write_text(json.dumps(build_policy(snapshot=self.snapshot,
            writable=self.writable, home=self.home, protected=[self.control],
            readable=[Path('/System'), Path('/usr'), Path('/bin').resolve(),
                Path('/sbin').resolve(), Path('/dev'), self.python.parents[1]], allowed_domains=[])))
        self.environment = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'HOME': str(self.home),
            'SHELL': '/bin/bash', 'TMPDIR': str(self.writable),
            'CLAUDE_CODE_TMPDIR': str(self.writable), 'PYTHONDONTWRITEBYTECODE': '1'}
        self.marker = self.writable / 'child.json'
        self.boundary = MacBoundary(self.control)

    def tearDown(self):
        if self.marker.exists():
            for pid, generation in json.loads(self.marker.read_text()):
                self.kernel.signal(pid, generation, signal.SIGKILL)
        self.temporary.cleanup()

    def command(self, code):
        return [arguments.srt, '--settings', str(self.config), '--',
                str(self.python), '-B', '-c', code]

    def invoke(self, code, deadline=2, cancel_after=None):
        started = time.monotonic()
        return self.boundary.run(self.command(code), cwd=self.snapshot,
            environment=self.environment, deadline=deadline,
            cancelled=lambda: signal.SIGTERM if cancel_after and
                time.monotonic() - started >= cancel_after and self.marker.exists() else None)

    def helper(self, parent_exits=False, detached=True, double_fork=False):
        helper = "import os,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        if double_fork:
            helper += "pid=os.fork(); os._exit(0) if pid else None; "
        # Fixture writes the identity supplied by its own kernel, not a label.
        helper += ("import ctypes,json; from pathlib import Path; "
            "lib=ctypes.CDLL('/usr/lib/libproc.dylib'); data=ctypes.create_string_buffer(56); "
            "lib.proc_pidinfo(os.getpid(),17,0,data,56); "
            "version=int.from_bytes(data.raw[32:36],'little',signed=True); "
            "Path(%r).write_text(json.dumps([[os.getpid(),version]])); time.sleep(20)" % str(self.marker))
        code = "import subprocess,signal,time; child=subprocess.Popen(%r,start_new_session=%r); " % (
            [str(self.python), '-B', '-c', helper], detached)
        # Ensure parent-first exit is tested after the helper starts.
        code += "from pathlib import Path; marker=Path(%r); " % str(self.marker)
        code += "exec('while not marker.exists(): time.sleep(.01)'); "
        if not parent_exits:
            code += 'signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(20)'
        return code

    def assert_clean(self, result, state):
        self.assertEqual(result['execution_status'], state, result)
        self.assertEqual(result['cleanup'], 'confirmed', result)
        self.assertFalse(self.boundary.service_loaded())
        self.assertEqual(self.kernel.count(self.boundary.coalition), 0)
        if self.marker.exists():
            for pid, generation in json.loads(self.marker.read_text()):
                identity = self.kernel.identity(pid)
                self.assertTrue(identity is None or identity['generation'] != generation
                    or identity['state'] == 5, 'fixture helper survived')

    def test_normal_exit_and_stdout(self):
        result = self.invoke("print('fixture completed')")
        self.assert_clean(result, 'completed')
        self.assertEqual(result['stdout'], b'fixture completed\n')
        end = json.loads((self.control / 'end').read_text())
        self.assertEqual(type(end['stdout_bytes']), int)
        self.assertEqual(end['stdout_bytes'], len(result['stdout']))
        self.assertEqual(end['stderr_bytes'], 0)
        self.assertEqual(result['stdout_check'], 'ok')
        self.assertEqual(result['diagnostics'], [])

    def test_nonzero_exit(self):
        result = self.invoke("import os; os.write(2, b'fixture error\\n'); raise SystemExit(7)")
        self.assert_clean(result, 'failed')
        end = json.loads((self.control / 'end').read_text())
        self.assertEqual(type(end['stderr_bytes']), int)
        self.assertGreater(end['stderr_bytes'], 0)
        self.assertNotEqual(end['launcher_exit_code'], 0)
        self.assertEqual(result['stdout_check'], 'ok')
        self.assertEqual(result['diagnostics'], [])

    def test_reviewer_cannot_read_staged_supervisor_code(self):
        protected = str(self.control / 'anchor-code' / 'review_macos.py')
        body = ("try: Path(%r).read_bytes()\n"
            "except PermissionError: print('supervisor read denied')\n"
            "else: raise SystemExit(95)") % protected
        code = 'from pathlib import Path; exec(%r)' % body
        result = self.invoke(code)
        self.assert_clean(result, 'completed')
        self.assertEqual(result['stdout'], b'supervisor read denied\n')

    def test_timeout_reaps_detached_helper(self):
        self.assert_clean(self.invoke(self.helper()), 'timed_out')
        self.assertTrue(self.marker.exists())

    def test_parent_first_exit_reaps_detached_helper_holding_pipe(self):
        self.assert_clean(self.invoke(self.helper(parent_exits=True)), 'completed')
        self.assertTrue(self.marker.exists())

    def test_cancel_reaps_detached_helper(self):
        self.assert_clean(self.invoke(self.helper(), deadline=10, cancel_after=.5), 'cancelled')
        self.assertTrue(self.marker.exists())

    def test_real_interrupt_signals_reap_detached_helper(self):
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signum=signum):
                self.marker.unlink(missing_ok=True)
                control = self.control / str(signum); control.mkdir(mode=0o700)
                self.boundary = MacBoundary(control)
                driver = ("import sys,json; from pathlib import Path; sys.path.insert(0,%r); "
                    "from review_macos import MacBoundary; "
                    "result=MacBoundary(Path(%r)).run(%r,cwd=Path(%r),environment=%r,deadline=10); "
                    "result.pop('stdout'); print(json.dumps(result))") % (
                        str(SCRIPTS), str(control), self.command(self.helper()),
                        str(self.snapshot), self.environment)
                process = subprocess.Popen([str(self.python), '-B', '-c', driver],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    expires = time.monotonic() + 5
                    while not self.marker.exists() and process.poll() is None and time.monotonic() < expires:
                        time.sleep(.02)
                    self.assertTrue(self.marker.exists(), 'signal fixture did not start')
                    ready = json.loads((control / 'ready').read_text())
                    self.boundary.coalition = self.kernel.coalition(ready['pid'])
                    process.send_signal(signum)
                    output, errors = process.communicate(timeout=8)
                    self.assertEqual(process.returncode, 0, errors.decode()[:1000])
                    result = json.loads(output)
                    self.assertEqual(result['cancel_signal'], signum)
                    # The external driver has its own nonce service label.
                    self.boundary.target = json.loads((control / 'request').read_text())['target']
                    self.assert_clean(result, 'cancelled')
                finally:
                    if process.poll() is None:
                        process.kill(); process.wait(timeout=2)

    def test_reparented_double_fork_keeps_kernel_membership(self):
        self.assert_clean(self.invoke(self.helper(parent_exits=True, double_fork=True)), 'completed')
        self.assertTrue(self.marker.exists())

    def test_fast_fork_members_are_all_reaped(self):
        code = 'import os,time\nfor index in range(16):\n if os.fork()==0: time.sleep(20); os._exit(0)\n'
        self.assert_clean(self.invoke(code), 'completed')

    def test_output_limit_fails_and_cleans(self):
        result = self.invoke("import os,time; os.write(1,b'x'*(2*1024*1024)); time.sleep(20)")
        self.assert_clean(result, 'failed')
        self.assertIn('output_limit', result['diagnostics'])

    def test_reviewer_cannot_create_another_launchd_job(self):
        label = 'com.delegate.escape-fixture.' + uuid.uuid4().hex
        target = 'gui/%s/%s' % (os.getuid(), label)
        code = "import subprocess; result=subprocess.run(%r,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(result.returncode)" % (
            ['/bin/launchctl', 'submit', '-l', label, '--', '/bin/sleep', '15'],)
        try:
            # A trusted positive control proves syntax/domain availability;
            # otherwise a bad command could masquerade as sandbox enforcement.
            positive = subprocess.run(['/bin/launchctl', 'submit', '-l', label, '--', '/bin/sleep', '15'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
            self.assertEqual(positive.returncode, 0, 'trusted submit unavailable')
            self.assertEqual(subprocess.run(['/bin/launchctl', 'print', target],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode, 0)
            self.assertEqual(subprocess.run(['/bin/launchctl', 'bootout', target],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode, 0)
            result = self.invoke(code)
            self.assert_clean(result, 'completed')
            self.assertNotEqual(int(result['stdout'].strip()), 0, 'reviewer escaped via launchd submit')
            self.assertNotEqual(subprocess.run(['/bin/launchctl', 'print', target],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode, 0)
        finally:
            # If containment fails, remove only this generated, owned label.
            subprocess.run(['/bin/launchctl', 'bootout', target], stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=3)

    def test_stale_generation_does_not_signal_current_fixture(self):
        child = subprocess.Popen([str(self.python), '-B', '-c', 'import time; time.sleep(20)'])
        try:
            identity = self.kernel.identity(child.pid)
            self.assertNotEqual(self.kernel.signal(child.pid, identity['generation'] + 1, signal.SIGKILL), 0)
            self.assertIsNone(child.poll())
        finally:
            child.kill(); child.wait(timeout=2)

    def test_cleanup_leaves_unrelated_session_alive(self):
        sentinel = subprocess.Popen([str(self.python), '-B', '-c', 'import time; time.sleep(20)'], start_new_session=True)
        try:
            self.assert_clean(self.invoke(self.helper()), 'timed_out')
            self.assertIsNone(sentinel.poll())
        finally:
            sentinel.kill(); sentinel.wait(timeout=2)

    def test_source_and_control_writes_are_denied(self):
        source = self.snapshot / 'source.py'; source.write_text('baseline')
        code = "from pathlib import Path\ntargets=%r\ndenied=0\n" % [str(source), str(self.control / 'start')]
        code += 'for path in targets:\n try: Path(path).write_text("changed")\n except PermissionError: denied+=1\nprint(denied)'
        result = self.invoke(code)
        self.assertEqual(result['execution_status'], 'completed',
            (self.control / 'stderr').read_text()[:1000])
        self.assert_clean(result, 'completed')
        self.assertEqual(result['stdout'], b'2\n')
        self.assertEqual(source.read_text(), 'baseline')


if __name__ == '__main__':
    if arguments.srt and (sys.platform != 'darwin' or not Path(arguments.srt).is_absolute()
            or not Path(arguments.srt).is_file()):
        parser.error('requires macOS and an existing srt; never calls a model')
    unittest.main(verbosity=2)
