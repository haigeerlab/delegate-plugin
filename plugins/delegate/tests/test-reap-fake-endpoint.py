#!/usr/bin/env python3
"""Abort-reaping regressions for run_codex.py with the real Codex CLI.

Run with: python3 -B plugins/delegate/tests/test-reap-fake-endpoint.py
Codex talks only to a fake Responses endpoint on 127.0.0.1 that sends no model
output, only tool calls running `sleep`. No credentials are sent or read and
CODEX_HOME is a temporary directory, so the user's Codex configuration is untouched.
Skipped when `codex` is not on PATH.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

_root_parser = argparse.ArgumentParser(add_help=False)
_root_parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]), help="delegate-plugin checkout root")
_root_args, _unittest_args = _root_parser.parse_known_args()
PLUGIN_ROOT = Path(_root_args.root).resolve()
sys.argv = [sys.argv[0], *_unittest_args]

RUNNER = PLUGIN_ROOT / "plugins/delegate/scripts/run_codex.py"
SLEEP_SECONDS = 40
COMMAND = "sleep %d && echo slept" % SLEEP_SECONDS


class FakeResponses(BaseHTTPRequestHandler):
    """Every request is answered with one exec_command tool call."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def _event(self, obj):
        self.wfile.write(("event: %s\ndata: %s\n\n" % (obj["type"], json.dumps(obj))).encode())
        self.wfile.flush()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("content-length", 0)))
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        self._event({"type": "response.created", "response": {"id": "resp_fake"}})
        self._event({"type": "response.output_item.done", "item": {
            "type": "function_call", "id": "fc_fake", "call_id": "call_fake", "name": "exec_command",
            "arguments": json.dumps({"cmd": COMMAND, "yield_time_ms": 30000})}})
        self._event({"type": "response.completed", "response": {"id": "resp_fake", "usage": {
            "input_tokens": 1, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 1,
            "output_tokens_details": {"reasoning_tokens": 0}, "total_tokens": 2}}})


def process_table():
    rows = subprocess.run(["ps", "-A", "-o", "pid=", "-o", "ppid=", "-o", "stat=", "-o", "command="],
                          text=True, capture_output=True, check=True).stdout.splitlines()
    table = {}
    for row in rows:
        parts = row.split(None, 3)
        if len(parts) == 4:
            table[int(parts[0])] = (int(parts[1]), parts[2], parts[3])
    return table


def descendants(root):
    table = process_table()
    found = {}
    for pid, (ppid, _, command) in table.items():
        parent = ppid
        while parent > 1:
            if parent == root:
                found[pid] = command
                break
            parent = table.get(parent, (0,))[0]
    return found


def living(pids):
    table = process_table()
    return sorted(pid for pid in pids if pid in table and not table[pid][1].startswith("Z"))


@unittest.skipUnless(shutil.which("codex"), "codex CLI not on PATH")
class RealCodexAbortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeResponses)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delegate-reap-fake-endpoint-")
        self.base = Path(self.temp.name)
        (self.base / "home").mkdir()
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.seen = {}
        self.to_kill = set()

    def tearDown(self):
        for pid in self.to_kill:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self.temp.cleanup()

    def start(self, seconds):
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("CODEX_API_KEY", None)
        env["CODEX_HOME"] = str(self.base / "home")
        port = self.server.server_address[1]
        provider = 'model_providers.fk={name="fk",base_url="http://127.0.0.1:%d/v1",wire_api="responses"}' % port
        command = [sys.executable, "-B", str(RUNNER), str(seconds), "codex", "exec", "--ephemeral",
                   "--skip-git-repo-check", "-c", provider, "-c", 'model_provider="fk"', "-m", "fake-model",
                   "-c", 'approval_policy="never"', "--sandbox", "read-only", "--color", "never",
                   "-o", str(self.base / "answer"), "--", "go"]
        # A file, not a pipe: a surviving command could otherwise keep the read open.
        self.log = self.base / "runner.log"
        with open(self.log, "wb") as log:
            return subprocess.Popen(command, cwd=self.repo, env=env, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)

    def wait_for_sleep(self, runner):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            found = descendants(runner.pid)
            if any(command.strip() == "sleep %d" % SLEEP_SECONDS for command in found.values()):
                self.seen = found
                self.to_kill.update(found)
                return
            if runner.poll() is not None:
                break
            time.sleep(.2)
        self.fail("Codex never ran the fake sleep command: %r" % self.log.read_text("utf-8", "replace")[-1500:])

    def assert_no_survivors(self, runner, status, expected, started, bound):
        output = self.log.read_text("utf-8", "replace")
        elapsed = time.monotonic() - started
        self.assertEqual(status, expected, output[-1500:])
        self.assertLess(elapsed, bound, output[-1500:])
        deadline = time.monotonic() + 1
        while living(self.seen) and time.monotonic() < deadline:
            time.sleep(.1)
        survivors = {pid: self.seen[pid] for pid in living(self.seen)}
        self.assertEqual(survivors, {}, "processes survived the abort:\n%s" % output[-1500:])

    def test_deadline_reaps_running_command(self):
        runner = self.start(15)
        self.wait_for_sleep(runner)
        started = time.monotonic()
        try:
            status = runner.wait(timeout=40)
        except subprocess.TimeoutExpired:
            os.killpg(runner.pid, signal.SIGKILL)
            self.fail("run_codex.py did not stop at its deadline")
        self.assert_no_survivors(runner, status, 124, started, 30)

    def test_signals_reap_running_command(self):
        for signum, expected in ((signal.SIGTERM, 143), (signal.SIGINT, 130), (signal.SIGHUP, 129)):
            with self.subTest(signal=signum.name):
                runner = self.start(300)
                self.wait_for_sleep(runner)
                started = time.monotonic()
                os.kill(runner.pid, signum)
                try:
                    status = runner.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(runner.pid, signal.SIGKILL)
                    self.fail("run_codex.py did not exit after %s" % signum.name)
                self.assert_no_survivors(runner, status, expected, started, 15)


if __name__ == "__main__":
    unittest.main()
