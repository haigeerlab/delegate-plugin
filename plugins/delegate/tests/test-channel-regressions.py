#!/usr/bin/env python3
"""Regression tests for plugins/delegate/scripts/codex-exec.sh.

Run with: python3 plugins/delegate/tests/test-channel-regressions.py
All Codex calls resolve to a temporary fake executable; no credentials or network are used.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

_root_parser = argparse.ArgumentParser(add_help=False)
_root_parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]), help="delegate-plugin checkout root")
_root_args, _unittest_args = _root_parser.parse_known_args()
PLUGIN_ROOT = Path(_root_args.root).resolve()
sys.argv = [sys.argv[0], *_unittest_args]

FAKE_CODEX = r'''#!/usr/bin/env python3
import os, signal, subprocess, sys, time
args = sys.argv[1:]
if os.environ.get("STUB_VERSION_START"): open(os.environ["STUB_VERSION_START"], "w").close()
if args == ["--version"]:
    print("codex stub 1.0")
    raise SystemExit(0)
if args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT")
    raise SystemExit(0)
if not args or args[0] != "exec":
    raise SystemExit(64)
start_marker = os.environ.get("STUB_EXEC_START")
if start_marker: open(start_marker, "w").close()
log = os.environ.get("STUB_CALL_LOG")
if log:
    with open(log, "a", encoding="utf-8") as f: f.write("exec\n")
answer = None
for i, arg in enumerate(args[:-1]):
    if arg == "-o": answer = args[i + 1]
mode = os.environ.get("STUB_MODE", "success")
tracked = os.environ.get("STUB_TRACKED_FILE")
if tracked:
    with open(tracked, "w", encoding="utf-8") as f: f.write("modified by fake codex\n")
if mode == "hang_ignore":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
if mode in ("timeout_child", "signal_child"):
    marker = os.environ["STUB_MARKER"]
    code = "import time; time.sleep(3); open(%r, 'w').write('late')" % marker
    child = subprocess.Popen([sys.executable, "-c", code], start_new_session=False)
    with open(os.environ["STUB_CHILD_PID"], "w") as f: f.write(str(child.pid))
if mode in ("hang_ignore", "timeout_child", "signal_child"):
    while True: time.sleep(.1)
if answer and mode != "empty":
    with open(answer, "w", encoding="utf-8") as f: f.write("fake answer\n")
if mode == "biglog":
    sys.stdout.write("x" * 100_000)
    sys.stdout.flush()
if mode in ("fail", "biglog"): raise SystemExit(3)
'''

class ChannelRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = PLUGIN_ROOT
        cls.script = cls.root / "plugins/delegate/scripts/codex-exec.sh"
        if not cls.script.is_file():
            raise RuntimeError(f"wrapper not found: {cls.script}")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delegate-channel-regression-")
        self.base = Path(self.temp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.fake = self.bin / "codex"
        self.fake.write_text(FAKE_CODEX, encoding="utf-8")
        self.fake.chmod(0o755)
        self.tmpdir = self.base / "tmp"
        self.tmpdir.mkdir()
        self.env = os.environ.copy()
        self.env.pop("OPENAI_API_KEY", None)
        self.env.pop("CODEX_API_KEY", None)
        self.env.update({
            "PATH": f"{self.bin}:{Path(sys.executable).parent}:/usr/bin:/bin",
            "TMPDIR": str(self.tmpdir),
            "DELEGATE_TIMEOUT_SECONDS": "1",
            "STUB_CALL_LOG": str(self.base / "calls.log"),
            "STUB_MODE": "success",
        })

        self.repo, self.tracked = self.make_git_repo("default")

    def tearDown(self):
        self.temp.cleanup()

    def run_wrapper(self, *args, env=None, timeout=6, cwd=None):
        """Every wrapper invocation gets an outer timeout and process-group cleanup."""
        run_env = self.env.copy()
        if env:
            run_env.update({k: str(v) for k, v in env.items()})
        proc = subprocess.Popen(
            [str(self.script), *args], cwd=cwd or self.repo, env=run_env,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            out, err = proc.communicate(timeout=timeout)
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            self._kill_group(proc.pid)
            out, err = proc.communicate(timeout=2)
            self.fail(f"outer timeout ({timeout}s); wrapper stdout={out[-500:]!r}, stderr={err[-500:]!r}")

    @staticmethod
    def _kill_group(pgid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def make_git_repo(self, name):
        repo = self.base / f"repo-{name}"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Regression Test"], cwd=repo, check=True)
        tracked = repo / "tracked.txt"
        tracked.write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repo, check=True)
        return repo, tracked

    def wait_for_path(self, path, timeout=2):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if Path(path).exists(): return True
            time.sleep(.025)
        return Path(path).exists()

    def test_timeout_ignoring_sigterm_is_bounded_and_returns_124(self):
        status, _, stderr = self.run_wrapper("hang", env={"STUB_MODE": "hang_ignore"}, timeout=8)
        self.assertEqual(status, 124, stderr.decode("utf-8", "replace"))

    def test_timeout_kills_descendant_before_it_can_write_marker(self):
        marker = self.base / "late-marker"
        child_pid = self.base / "child.pid"
        status, _, stderr = self.run_wrapper("child", env={
            "STUB_MODE": "timeout_child", "STUB_MARKER": marker, "STUB_CHILD_PID": child_pid,
        }, timeout=8)
        self.assertEqual(status, 124, stderr.decode("utf-8", "replace"))
        self.assertTrue(self.wait_for_path(child_pid), "fake codex did not record its child")
        time.sleep(3.2)
        self.assertFalse(marker.exists(), "descendant wrote after timeout termination")

    def test_wrapper_sigterm_reaps_codex_and_descendant(self):
        marker = self.base / "signal-marker"
        child_pid_file = self.base / "signal-child.pid"
        env = self.env.copy()
        env["DELEGATE_TIMEOUT_SECONDS"] = "20"
        env["STUB_VERSION_START"] = str(self.base / "version-start")
        env.update({"STUB_MODE": "signal_child", "STUB_MARKER": str(marker), "STUB_CHILD_PID": str(child_pid_file), "STUB_EXEC_START": str(self.base / "exec-start")})
        env = {str(k): str(v) for k, v in env.items()}
        proc = subprocess.Popen([str(self.script), "signal"], cwd=self.repo, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        try:
            if not self.wait_for_path(child_pid_file, timeout=8):
                self.fail("fake codex child did not start")
            os.kill(proc.pid, signal.SIGTERM)
            try:
                _, stderr = proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                self.fail("wrapper did not exit after SIGTERM")
            self.assertNotEqual(proc.returncode, 0, stderr.decode("utf-8", "replace"))
            time.sleep(3.2)
            self.assertFalse(marker.exists(), "child survived wrapper SIGTERM and wrote marker")
        finally:
            self._kill_group(proc.pid)
            if proc.poll() is None:
                proc.wait(timeout=2)
            if proc.stdout and not proc.stdout.closed:
                proc.stdout.close()
            if proc.stderr and not proc.stderr.closed:
                proc.stderr.close()

    def test_write_failures_report_git_acceptance_and_keep_changes(self):
        cases = (("fail", 3), ("empty", None), ("timeout_child", 124))
        for mode, expected_status in cases:
            with self.subTest(mode=mode):
                repo, tracked = self.make_git_repo(mode)
                env = {"STUB_MODE": mode, "STUB_TRACKED_FILE": tracked}
                if mode == "timeout_child":
                    env.update({"STUB_MARKER": self.base / f"write-{time.monotonic_ns()}.marker",
                                "STUB_CHILD_PID": self.base / f"write-{time.monotonic_ns()}.pid"})
                status, _, stderr = self.run_wrapper("--write", "mutate", env=env, cwd=repo, timeout=8)
                if expected_status is not None:
                    self.assertEqual(status, expected_status, stderr.decode("utf-8", "replace"))
                else:
                    self.assertNotEqual(status, 0, "empty answer unexpectedly succeeded")
                self.assertEqual(tracked.read_text(encoding="utf-8"), "modified by fake codex\n")
                changed = subprocess.run(["git", "status", "--short"], cwd=repo, text=True,
                                         capture_output=True, check=True).stdout
                self.assertIn("tracked.txt", changed)
                diagnostic = stderr.decode("utf-8", "replace")
                self.assertIn("git 验收", diagnostic, diagnostic[-1200:])
                self.assertIn("tracked.txt", diagnostic, diagnostic[-1200:])

    def test_large_single_line_failure_log_has_bounded_stderr_and_full_path(self):
        status, _, stderr = self.run_wrapper("large log", env={"STUB_MODE": "biglog"})
        decoded = stderr.decode("utf-8", "replace")
        self.assertEqual(status, 3, decoded[-1000:])
        self.assertLessEqual(len(stderr), 18_000, f"stderr was {len(stderr)} bytes")
        self.assertIn("完整过程日志：", decoded)
        self.assertRegex(decoded, r"完整过程日志：[^\s]+\.log")

    def test_write_mode_rejects_non_git_directory_without_exec(self):
        outside_git = self.base / "plain"
        outside_git.mkdir()
        status, _, stderr = self.run_wrapper("--write", "mutate", cwd=outside_git)
        diagnostic = stderr.decode("utf-8", "replace")
        self.assertNotEqual(status, 0, diagnostic)
        self.assertRegex(diagnostic, r"(?i)(不是 git|git 仓库|git repository)")
        calls = Path(self.env["STUB_CALL_LOG"])
        self.assertFalse(calls.exists() and "exec" in calls.read_text(encoding="utf-8"),
                         "wrapper invoked codex exec outside a Git repository")

    def test_help_works_without_codex_and_lists_supported_options(self):
        env = self.env.copy()
        empty_path = self.base / "empty-path"
        empty_path.mkdir()
        env["PATH"] = str(empty_path)
        proc = subprocess.Popen([str(self.script), "--help"], cwd=self.base, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        try:
            out, err = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            self._kill_group(proc.pid)
            proc.communicate(timeout=2)
            self.fail("--help exceeded outer timeout")
        text = (out + err).decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 0, text)
        for option in ("--model", "--effort", "--write"):
            self.assertIn(option, text)
        self.assertFalse(Path(self.env["STUB_CALL_LOG"]).exists(), "--help invoked codex")

if __name__ == "__main__":
    unittest.main()
