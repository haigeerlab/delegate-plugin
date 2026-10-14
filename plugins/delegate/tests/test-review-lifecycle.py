#!/usr/bin/env python3
"""Model-free feasibility tests for the existing group runner around srt.

These tests deliberately challenge detached helpers; they are not a new
production supervisor. Test teardown kills only recorded fixture children.
"""
import argparse
import importlib.util
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
arguments, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]] + remaining
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('review_isolation', SCRIPTS / 'review_isolation.py')
isolation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(isolation)


def alive(pid):
    state = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'stat='],
                           capture_output=True, text=True, timeout=2).stdout.strip()
    return bool(state) and not state.startswith('Z')


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='delegate-lifecycle.', dir='/private/tmp')
        self.base = Path(self.temporary.name).resolve()
        self.snapshot, self.run, self.home = [self.base / name for name in ('snapshot', 'run', 'home')]
        for directory in (self.snapshot, self.run, self.home):
            directory.mkdir(mode=0o700)
        self.python = Path(sys.executable).resolve()
        policy = isolation.build_policy(snapshot=self.snapshot, writable=self.run,
            home=self.home, protected=[], allowed_domains=[],
            readable=[Path('/System'), Path('/usr'), Path('/bin').resolve(),
                      Path('/sbin').resolve(), Path('/dev'), self.python.parents[1]])
        self.config = self.base / 'policy.json'
        self.config.write_text(json.dumps(policy))
        self.env = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'HOME': str(self.home),
                    'SHELL': '/bin/bash', 'TMPDIR': str(self.run),
                    'CLAUDE_CODE_TMPDIR': str(self.run), 'PYTHONDONTWRITEBYTECODE': '1'}
        self.child_file = self.run / 'child.pid'
        self.group_file = self.run / 'group.pid'

    def tearDown(self):
        if self.child_file.exists():
            pid = int(self.child_file.read_text())
            if alive(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                deadline = time.monotonic() + 2
                while alive(pid) and time.monotonic() < deadline:
                    time.sleep(.025)
                self.assertFalse(alive(pid), 'test teardown failed to stop its fixture helper')
        if self.group_file.exists():
            try:
                os.killpg(int(self.group_file.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.temporary.cleanup()

    def command(self, code, deadline=2):
        return [str(self.python), '-B', str(SCRIPTS / 'run_codex.py'), str(deadline),
                arguments.srt, '--settings', str(self.config), '--',
                str(self.python), '-B', '-c', code]

    def child_code(self, detached=False, parent_exits=False):
        helper = 'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)'
        code = "import os,subprocess,signal,time; from pathlib import Path; "
        code += "Path(%r).write_text(str(os.getpgrp())); " % str(self.group_file)
        code += "child=subprocess.Popen(%r, start_new_session=%r); " % (
            [str(self.python), '-B', '-c', helper], detached)
        code += "Path(%r).write_text(str(child.pid)); " % str(self.child_file)
        if not parent_exits:
            code += 'signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)'
        return code

    def invoke(self, code, deadline=2):
        # A file avoids hanging the test harness on a deliberately surviving
        # helper's inherited pipe. Pipe handling is a separate lifecycle case.
        with (self.base / 'output.log').open('w') as output:
            return subprocess.run(self.command(code, deadline), env=self.env,
                cwd=self.snapshot, stdin=subprocess.DEVNULL, stdout=output,
                stderr=output, timeout=8).returncode

    def test_normal_exit_is_preserved(self):
        self.assertEqual(self.invoke("print('fixture completed')"), 0)

    def test_deadline_reaps_same_group_helper(self):
        self.assertEqual(self.invoke(self.child_code()), 124)
        self.assertTrue(self.child_file.exists(), 'helper did not start')
        self.assertFalse(alive(int(self.child_file.read_text())), 'same-group helper survived')

    def test_deadline_reaps_detached_helper(self):
        self.assertEqual(self.invoke(self.child_code(detached=True)), 124)
        self.assertTrue(self.child_file.exists(), 'detached helper did not start')
        self.assertFalse(alive(int(self.child_file.read_text())), 'detached helper survived')

    def test_parent_first_exit_reaps_same_group_helper_holding_pipe(self):
        process = subprocess.Popen(self.command(self.child_code(parent_exits=True)),
            env=self.env, cwd=self.snapshot, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            process.communicate(timeout=8)
            self.assertEqual(process.returncode, 0)
            self.assertTrue(self.child_file.exists(), 'helper did not start')
            self.assertFalse(alive(int(self.child_file.read_text())), 'pipe-holding helper survived')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=2)

    def test_parent_first_exit_reaps_detached_helper(self):
        self.assertEqual(self.invoke(self.child_code(detached=True, parent_exits=True)), 0)
        self.assertTrue(self.child_file.exists(), 'detached helper did not start')
        self.assertFalse(alive(int(self.child_file.read_text())), 'detached helper survived normal exit')

    def cancel_run(self, detached, signum):
        with (self.base / 'output.log').open('w') as output:
            process = subprocess.Popen(self.command(self.child_code(detached=detached), deadline=10),
                env=self.env, cwd=self.snapshot, stdin=subprocess.DEVNULL,
                stdout=output, stderr=output, start_new_session=True)
            try:
                deadline = time.monotonic() + 5
                while not self.child_file.exists() and time.monotonic() < deadline:
                    time.sleep(.025)
                self.assertTrue(self.child_file.exists(), 'helper did not start')
                process.send_signal(signum)
                self.assertEqual(process.wait(timeout=5), 128 + signum)
                self.assertFalse(alive(int(self.child_file.read_text())), 'helper survived cancellation')
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=2)

    def test_cancel_reaps_same_group_helper_and_preserves_wrapper_cause(self):
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signum=signum):
                self.child_file.unlink(missing_ok=True)
                self.cancel_run(False, signum)

    def test_cancel_reaps_detached_helper(self):
        self.cancel_run(True, signal.SIGTERM)

    def test_cleanup_does_not_kill_an_unrelated_session(self):
        sentinel = subprocess.Popen([str(self.python), '-B', '-c', 'import time; time.sleep(30)'],
                                    start_new_session=True)
        try:
            self.assertEqual(self.invoke(self.child_code()), 124)
            self.assertIsNone(sentinel.poll(), 'unrelated fixture session was killed')
        finally:
            sentinel.kill()
            sentinel.wait(timeout=2)


if __name__ == '__main__':
    if (sys.platform != 'darwin' or not Path(arguments.srt).is_absolute()
            or not Path(arguments.srt).is_file()):
        parser.error('requires macOS and an existing srt executable; no model calls')
    unittest.main(verbosity=2)
