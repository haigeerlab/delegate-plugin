#!/usr/bin/env python3
"""Actual Linux/srt/service gate. Requires a dedicated disposable guest.

No model, credentials, host shares or real repository. Missing prerequisites
fail the suite; successful fake-manager tests cannot replace this gate.
"""
import argparse
import importlib.util
import json
import http.server
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--srt', required=True)
args, rest = parser.parse_known_args()
sys.argv = [sys.argv[0]] + rest
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


isolation = load('review_isolation')
service = load('review_service')


class LinuxGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-linux.')
        self.base = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        self.snapshot, self.run, self.home, self.source, self.control = [
            self.base / name for name in ('snapshot', 'run', 'home', 'source', 'control')]
        for path in (self.snapshot, self.run, self.home, self.source, self.control):
            path.mkdir(mode=0o700)
        self.env = {'HOME': str(self.home), 'PATH': os.environ['PATH'], 'SHELL': '/bin/bash',
                    'TMPDIR': str(self.run), 'CLAUDE_CODE_TMPDIR': str(self.run),
                    'PYTHONDONTWRITEBYTECODE': '1'}
        self.policy = self.control / 'policy.json'
        self.policy.write_text(json.dumps(isolation.build_linux_policy(
            snapshot=self.snapshot, writable=self.run, home=self.home,
            protected=[self.source, self.control], allowed_domains=[],
            readable=[Path('/usr'), Path('/etc/ld.so.cache'), Path('/etc/hosts'),
                      Path('/etc/nsswitch.conf'), Path('/etc/resolv.conf').resolve(),
                      Path('/tmp/delegate-tools/review_network.py'),
                      Path(args.srt).resolve().parents[4]])))
        self.policy.chmod(0o600)

    def invoke(self, code, deadline=5):
        boundary = service.ReviewService(manager='/usr/bin/systemctl')
        result = boundary.run('/usr/bin/systemd-run', [args.srt, '--settings',
            str(self.policy), '--', '/usr/bin/python3', '-B',
            '/tmp/delegate-tools/review_network.py', '--', '/usr/bin/python3', '-B', '-c', code],
            deadline=deadline, environment=self.env, cwd=self.snapshot,
            control=self.control)
        self.assertEqual(result['cleanup'], 'confirmed', result)
        return result

    def test_normal_result_and_empty_cgroup(self):
        result = self.invoke("print('review fixture')")
        self.assertEqual(result['execution_status'], 'completed', result)
        self.assertEqual(result['stdout'].strip(), b'review fixture')

    def test_source_git_config_snapshot_and_escape_writes_denied(self):
        (self.source / '.git').mkdir()
        (self.home / '.claude').mkdir()
        targets = [self.source / 'code.py', self.source / '.git/index',
                   self.home / '.claude/settings.json', self.snapshot / 'scope.py',
                   self.control / 'result.json']
        for target in targets:
            target.write_text('baseline')
        (self.run / 'escape').symlink_to(self.source, target_is_directory=True)
        names = [str(path) for path in targets] + [str(self.run / 'escape/code.py')]
        result = self.invoke("from pathlib import Path\nfor name in %r:\n"
            " try: Path(name).write_text('unauthorized')\n"
            " except OSError: pass\n else: raise AssertionError('write permitted')\n"
            "print('writes denied')" % names)
        self.assertEqual(result['execution_status'], 'completed', result)
        self.assertTrue(all(path.read_text() == 'baseline' for path in targets))

    def test_scope_reads_temp_writes_and_other_reads_denied(self):
        (self.snapshot / 'scope').write_text('input')
        (self.source / 'secret').write_text('fixture secret')
        (self.run / 'escape').symlink_to(self.source / 'secret')
        code = "from pathlib import Path\nassert Path(%r).read_text() == 'input'\n" % str(self.snapshot / 'scope')
        code += "Path(%r).write_text('allowed')\n" % str(self.run / 'allowed')
        code += "for name in %r:\n try: Path(name).read_bytes()\n except OSError as exc: print('read denied',name,exc.errno)\n else: print('read permitted',name);raise AssertionError('read permitted')" % [str(self.source / 'secret'), str(self.run / 'escape'), '/sys/fs/cgroup/cgroup.procs', '/run/user/%s/bus' % os.getuid()]
        result = self.invoke(code)
        self.assertEqual(result['execution_status'], 'completed', result)
        self.assertEqual((self.run / 'allowed').read_text(), 'allowed')

    def test_delete_rename_hardlink_denied(self):
        target = self.snapshot / 'scope'; target.write_text('baseline')
        code = "import os\nfor action in (lambda: os.unlink(%r), lambda: os.rename(%r,%r), lambda: os.link(%r,%r)):\n try: action()\n except OSError: pass\n else: raise AssertionError('mutation permitted')" % (str(target), str(target), str(self.run / 'renamed'), str(target), str(self.run / 'link'))
        self.assertEqual(self.invoke(code)['execution_status'], 'completed')
        self.assertEqual(target.read_text(), 'baseline')
        self.assertFalse((self.run / 'link').exists())

    def test_runtime_default_extra_write_paths_remain_denied(self):
        shared = Path('/tmp/claude'); created = not shared.exists()
        if created:
            shared.mkdir(mode=0o700)
        targets = []
        for directory in (self.home / '.npm/_logs', self.home / '.claude/debug'):
            directory.mkdir(parents=True); targets.append(directory / self.base.name)
        targets.append(shared / self.base.name)
        try:
            code = "from pathlib import Path\nfor name in %r:\n try:Path(name).write_text('unauthorized')\n except OSError:pass\n else:raise AssertionError('default write permitted')" % [str(path) for path in targets]
            self.assertEqual(self.invoke(code)['execution_status'], 'completed')
            self.assertTrue(all(not path.exists() for path in targets))
        finally:
            targets[-1].unlink(missing_ok=True)
            if created:
                shared.rmdir()

    def test_direct_network_binding_and_unix_socket_denied(self):
        code = "import socket\nfor family,action in ((socket.AF_INET,'connect'),(socket.AF_INET,'bind'),(socket.AF_UNIX,'unix')):\n try:\n  s=socket.socket(family);s.settimeout(1)\n  if action=='connect':s.connect(('1.1.1.1',443))\n  elif action=='bind':s.bind(('127.0.0.1',0))\n  else:s.connect('/run/user/%s/bus')\n except OSError as exc:print('network denied',action,exc.errno)\n else:print('network permitted',action);raise AssertionError('network permitted')" % os.getuid()
        result = self.invoke(code)
        self.assertEqual(result['execution_status'], 'completed', result)

    def helper(self, parent_exits=False):
        # The marker proves the double-fork helper actually started. Kernel
        # cgroup emptiness, including outer proxies, establishes final cleanup.
        marker = str(self.run / 'ready')
        return ("import os,time,signal\nfrom pathlib import Path\n"
                "pid=os.fork()\nif pid==0:\n os.setsid()\n pid=os.fork()\n"
                " if pid:os._exit(0)\n signal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
                " Path(%r).write_text('started');time.sleep(30);os._exit(0)\n"
                "while not Path(%r).exists():time.sleep(.01)\n" % (marker, marker)
                + ("print('parent exited')\n" if parent_exits else
                   "signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)\n"))

    def test_timeout_reaps_double_fork_and_outer_helpers(self):
        result = self.invoke(self.helper(), deadline=2)
        self.assertTrue((self.run / 'ready').exists(), result)
        self.assertEqual(result['execution_status'], 'timed_out', result)

    def test_parent_first_exit_reaps_double_fork(self):
        result = self.invoke(self.helper(parent_exits=True), deadline=2)
        self.assertTrue((self.run / 'ready').exists(), result)
        # bwrap may wait for namespace descendants; the deadline remains real.
        self.assertIn(result['execution_status'], ('completed', 'timed_out'), result)

    def test_rapid_double_fork_burst_has_no_surviving_cgroup(self):
        code = "import os,signal,time\nfrom pathlib import Path\nroot=Path(%r)\nfor i in range(8):\n if os.fork()==0:\n  os.setsid()\n  if os.fork():os._exit(0)\n  signal.signal(signal.SIGTERM,signal.SIG_IGN)\n  (root/('ready'+str(i))).write_text('started');time.sleep(30);os._exit(0)\nwhile len(list(root.glob('ready*')))<8:time.sleep(.01)\nos._exit(0)" % str(self.run)
        result = self.invoke(code, deadline=2)
        self.assertEqual(len(list(self.run.glob('ready*'))), 8, result)
        self.assertIn(result['execution_status'], ('completed', 'timed_out'), result)

    def test_nonzero_is_failed(self):
        self.assertEqual(self.invoke('raise SystemExit(7)')['execution_status'], 'failed')

    def test_oversize_output_fails_without_unbounded_return(self):
        result = self.invoke("import sys;sys.stdout.write('x'*(2*1024*1024))")
        self.assertEqual(result['execution_status'], 'failed', result['diagnostics'])
        self.assertIn('output_limit', result['diagnostics'])
        self.assertLessEqual(len(result['stdout']), 1024 * 1024)

    def test_unrelated_session_survives(self):
        sentinel = subprocess.Popen(['/usr/bin/sleep', '30'], start_new_session=True)
        try:
            self.assertEqual(self.invoke(self.helper(), deadline=2)['execution_status'], 'timed_out')
            self.assertIsNone(sentinel.poll())
        finally:
            sentinel.kill(); sentinel.wait(timeout=2)

    def test_cancel_reaps_double_fork_and_preserves_cause(self):
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signum=signum):
                marker = self.run / 'ready'; marker.unlink(missing_ok=True)
                done = threading.Event()

                def interrupt():
                    expires = time.monotonic() + 5
                    while not done.is_set() and not marker.exists() and time.monotonic() < expires:
                        time.sleep(.01)
                    if not done.is_set() and marker.exists():
                        os.kill(os.getpid(), signum)

                sender = threading.Thread(target=interrupt, daemon=True)
                sender.start()
                try:
                    result = self.invoke(self.helper(), deadline=8)
                finally:
                    done.set(); sender.join(timeout=2)
                self.assertTrue(marker.exists(), result)
                self.assertEqual(result['execution_status'], 'cancelled', result)

    def test_client_death_still_has_guest_deadline(self):
        boundary = service.ReviewService(manager='/usr/bin/systemctl')
        command = boundary.command('/usr/bin/systemd-run', ['/usr/bin/env', '-i'] + [
            key + '=' + value for key, value in self.env.items()] + [args.srt,
            '--settings', str(self.policy), '--', '/usr/bin/python3', '-B',
            '/tmp/delegate-tools/review_network.py', '--', '/usr/bin/python3', '-B',
            '-c', self.helper()], 2)
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
        group = None
        try:
            expires = time.monotonic() + 5
            while not (self.run / 'ready').exists() and time.monotonic() < expires:
                time.sleep(.01)
            self.assertTrue((self.run / 'ready').exists(), 'client fixture did not start')
            group = boundary.observe()['ControlGroup']
            self.assertTrue(group)
            process.kill(); process.wait(timeout=2)
            expires = time.monotonic() + 5
            while not boundary._empty(group) and time.monotonic() < expires:
                time.sleep(.02)
            self.assertTrue(boundary._empty(group), 'guest unit survived client death/deadline')
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=2)
            if group and not boundary._empty(group):
                boundary._manager(['stop', boundary.unit])

    def test_proxy_denies_unlisted_and_allows_only_exact_fixture_port(self):
        hits = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                self.send_response(200); self.end_headers(); self.wfile.write(b'fixture')

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        other = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        other_worker = threading.Thread(target=other.serve_forever, daemon=True); other_worker.start()
        port = server.server_port
        # Fixture-only: use the proxy even for loopback. This does not establish
        # an original Claude CLI's DNS/TLS/provider compatibility.
        code = "import os,urllib.request,urllib.error\nos.environ.pop('NO_PROXY',None);os.environ.pop('no_proxy',None)\nproxy=os.environ['HTTP_PROXY'].replace('localhost:','127.0.0.1:')\nopener=urllib.request.build_opener(urllib.request.ProxyHandler({'http':proxy}))\ntry:\n r=opener.open('http://127.0.0.1:%s/probe',timeout=2);print(r.status,r.read().decode())\nexcept urllib.error.HTTPError as exc:print(exc.code)" % port
        try:
            policy = json.loads(self.policy.read_text())
            policy['network']['allowedDomains'] = ['127.0.0.1:%s' % port]
            self.policy.write_text(json.dumps(policy))
            denied = self.invoke(code.replace(':%s/probe' % port, ':%s/probe' % other.server_port))
            self.assertEqual(denied['execution_status'], 'completed', denied)
            self.assertEqual(denied['stdout'].strip(), b'403'); self.assertEqual(hits, [])
            allowed = self.invoke(code)
            self.assertEqual(allowed['execution_status'], 'completed', allowed)
            self.assertEqual(allowed['stdout'].strip(), b'200 fixture')
            self.assertEqual(hits, ['/probe'])
        finally:
            server.shutdown(); server.server_close(); worker.join(timeout=2)
            other.shutdown(); other.server_close(); other_worker.join(timeout=2)


if __name__ == '__main__':
    if sys.platform != 'linux' or not Path(args.srt).is_absolute():
        parser.error('dedicated Linux guest and absolute srt required')
    unittest.main(verbosity=2)
