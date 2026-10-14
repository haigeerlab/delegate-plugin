#!/usr/bin/env python3
"""Model-free policy and actual macOS permission probes; no user configuration.

Use --policy-only for unit checks, or --srt /absolute/path/to/srt for OS checks.
Missing isolation prerequisites are an error, never a passing/skipped OS check.
"""
import argparse
import importlib.util
import json
import http.server
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--policy-only', action='store_true')
parser.add_argument('--srt')
arguments, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]] + remaining
script = Path(__file__).resolve().parents[1] / 'scripts/review_isolation.py'
spec = importlib.util.spec_from_file_location('review_isolation', script)
isolation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(isolation)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='delegate-isolation.')
        self.base = Path(self.temporary.name).resolve()
        self.snapshot = self.base / 'snapshot'
        self.writable = self.base / 'run'
        self.home = self.base / 'home'
        self.source = self.base / 'source'
        for path in (self.snapshot, self.writable, self.home, self.source):
            path.mkdir(mode=0o700)

    def tearDown(self):
        self.temporary.cleanup()

    def policy(self, **changes):
        options = dict(snapshot=self.snapshot, writable=self.writable, home=self.home,
                       protected=[self.source], readable=[], allowed_domains=[])
        options.update(changes)
        return isolation.build_policy(**options)

    def test_snapshot_and_source_do_not_receive_write_grants(self):
        policy = self.policy()
        self.assertEqual(policy['filesystem']['allowWrite'],
                         [{'path': str(self.writable), 'literal': True}])
        self.assertIn({'path': '/private/tmp/claude', 'literal': True},
                      policy['filesystem']['denyWrite'])
        self.assertIn({'path': str(self.home), 'literal': True},
                      policy['filesystem']['denyWrite'])

    def test_read_access_requires_explicit_carveouts(self):
        policy = self.policy()
        self.assertEqual(policy['filesystem']['denyRead'], [{'path': '/', 'literal': True}])
        self.assertEqual(policy['network']['allowedDomains'], [])
        self.assertTrue(policy['network']['strictAllowlist'])
        self.assertFalse(policy['network']['allowAllUnixSockets'])

    def test_write_root_inside_protected_or_snapshot_is_rejected(self):
        for root in (self.source, self.snapshot, self.home, self.base):
            with self.subTest(root=root), self.assertRaises(ValueError):
                self.policy(writable=root)

    def test_literal_metacharacters_do_not_become_globs(self):
        special = self.base / 'snapshot[*]'
        special.mkdir()
        policy = self.policy(snapshot=special)
        self.assertIn({'path': str(special), 'literal': True}, policy['filesystem']['allowRead'])

    def test_symlink_roots_and_broad_network_exemptions_are_rejected(self):
        link = self.base / 'link'
        link.symlink_to(self.writable, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.policy(writable=link)
        for domain in ('*', '*.example.com', 'https://example.com', 'example.com/path'):
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                self.policy(allowed_domains=[domain])


class MacOSPermissions(PolicyTests):
    def setUp(self):
        super().setUp()
        self.tmp = self.writable / 'tmp'
        self.tmp.mkdir(mode=0o700)
        self.interpreter = Path(sys.executable).resolve()
        self.env = {
            'PATH': '/opt/homebrew/bin:/usr/bin:/bin',
            'HOME': str(self.home), 'SHELL': '/bin/bash', 'LC_ALL': 'C',
            'TMPDIR': str(self.tmp), 'CLAUDE_CODE_TMPDIR': str(self.tmp),
            'PYTHONDONTWRITEBYTECODE': '1',
        }

    def probe(self, code, domains=()):
        # The policy is outside allowWrite, with no source links or actual .git.
        config = self.base / 'policy.json'
        config.write_text(json.dumps(self.policy(
            readable=[Path('/System'), Path('/usr'), Path('/bin').resolve(),
                      Path('/sbin').resolve(), Path('/dev'), self.interpreter.parents[1]],
            allowed_domains=list(domains))))
        config.chmod(0o600)
        return subprocess.run([arguments.srt, '--settings', str(config), '--',
                               str(self.interpreter), '-B', '-c', code],
                              env=self.env, cwd=self.snapshot, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=15)

    def test_os_blocks_source_git_config_snapshot_and_symlink_writes(self):
        git = self.source / '.git'
        git.mkdir()
        config = self.home / '.claude'
        config.mkdir()
        targets = [self.source / 'code.py', git / 'index', config / 'settings.json',
                   self.snapshot / 'review.py']
        for path in targets:
            path.write_text('baseline')
        link = self.writable / 'escape'
        link.symlink_to(self.source, target_is_directory=True)
        targets.append(link / 'code.py')
        code = '''import errno, json
from pathlib import Path
denied = []
for name in %r:
    try:
        Path(name).write_text('unauthorized')
    except OSError as exc:
        assert exc.errno in (errno.EPERM, errno.EACCES), (name, exc.errno)
        denied.append(name)
    else:
        raise AssertionError('write allowed: ' + name)
print(json.dumps(denied))
''' % [str(path) for path in targets]
        result = self.probe(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [str(path) for path in targets])
        self.assertTrue(all(path.read_text() == 'baseline' for path in targets))

    def test_os_allows_snapshot_read_and_dedicated_temporary_write(self):
        source = self.snapshot / 'scope.py'
        source.write_text('review input')
        marker = self.tmp / 'allowed'
        result = self.probe("from pathlib import Path; assert Path(%r).read_text() == 'review input'; "
                            "Path(%r).write_text('allowed'); print('read/write confirmed')" %
                            (str(source), str(marker)))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(marker.read_text(), 'allowed')
        self.assertEqual(result.stdout.strip(), 'read/write confirmed')

    def test_os_blocks_out_of_scope_reads_including_links(self):
        secret = self.source / 'out-of-scope.txt'
        secret.write_text('fixture only')
        link = self.writable / 'read-escape'
        link.symlink_to(secret)
        code = '''import errno
from pathlib import Path
for name in %r:
    try:
        Path(name).read_text()
    except OSError as exc:
        assert exc.errno in (errno.EPERM, errno.EACCES), (name, exc.errno)
    else:
        raise AssertionError('read allowed: ' + name)
print('reads denied')
''' % [str(secret), str(link)]
        result = self.probe(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'reads denied')

    def test_os_blocks_delete_rename_and_hardlink_escape(self):
        original = self.snapshot / 'protected.py'
        original.write_text('baseline')
        alias = self.writable / 'hardlink'
        renamed = self.writable / 'renamed'
        code = '''import errno, os
from pathlib import Path
source, alias, renamed = %r
for operation in (lambda: os.unlink(source), lambda: os.rename(source, renamed),
                  lambda: os.link(source, alias)):
    try:
        operation()
    except OSError as exc:
        assert exc.errno in (errno.EPERM, errno.EACCES), exc.errno
    else:
        raise AssertionError('mutation allowed')
print('mutations denied')
''' % [str(original), str(alias), str(renamed)]
        result = self.probe(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(original.read_text(), 'baseline')
        self.assertFalse(alias.exists())
        self.assertFalse(renamed.exists())

    def test_os_blocks_srt_default_extra_write_locations(self):
        # No real home contents. Use a unique child under the shared temp root;
        # if that root is absent, prepare/remove only the empty fixture root.
        shared = Path('/private/tmp/claude')
        created = not shared.exists()
        if created:
            shared.mkdir(mode=0o700)
        name = self.base.name
        default_target = shared / name
        defaults = [self.home / '.npm/_logs', self.home / '.claude/debug']
        for path in defaults:
            path.mkdir(parents=True)
        targets = [path / name for path in defaults] + [default_target]
        code = '''import errno
from pathlib import Path
for name in %r:
    try:
        Path(name).write_text('should be denied')
    except OSError as exc:
        assert exc.errno in (errno.EPERM, errno.EACCES), (name, exc.errno)
    else:
        raise AssertionError('srt default write allowed: ' + name)
print('defaults denied')
''' % [str(path) for path in targets]
        try:
            result = self.probe(code)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(all(not path.exists() for path in targets))
        finally:
            default_target.unlink(missing_ok=True)
            if created:
                shared.rmdir()

    def start_server(self):
        hits = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'fixture response')

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server.server_address[1], hits

    def request_code(self, port):
        # Isolate filter behavior from Darwin localhost resolution under the
        # deny-all read policy. This numeric proxy rewrite is a fixture-only
        # adaptation, not proof that an unmodified Claude CLI can use it.
        return '''import os, urllib.request, urllib.error
os.environ.pop('NO_PROXY', None)
os.environ.pop('no_proxy', None)
proxy = os.environ['HTTP_PROXY'].replace('localhost:', '127.0.0.1:')
opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': proxy}))
try:
    with opener.open('http://127.0.0.1:%s/probe', timeout=3) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as exc:
    print('proxy denied', exc.code)
''' % port

    def test_os_network_denies_unlisted_endpoint(self):
        port, hits = self.start_server()
        result = self.probe(self.request_code(port))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'proxy denied 403')
        self.assertEqual(hits, [])

    def test_os_network_permits_only_exact_allowed_port(self):
        port, hits = self.start_server()
        other_port, other_hits = self.start_server()
        domain = '127.0.0.1:%s' % port
        allowed = self.probe(self.request_code(port), domains=[domain])
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(allowed.stdout.strip(), '200 fixture response')
        self.assertEqual(hits, ['/probe'])
        denied = self.probe(self.request_code(other_port), domains=[domain])
        self.assertEqual(denied.returncode, 0, denied.stderr)
        self.assertEqual(denied.stdout.strip(), 'proxy denied 403')
        self.assertEqual(other_hits, [])

    def test_os_network_blocks_direct_socket_and_local_binding(self):
        port, hits = self.start_server()
        code = '''import errno, socket
for action in ('connect', 'bind'):
    with socket.socket() as connection:
        connection.settimeout(2)
        try:
            if action == 'connect': connection.connect(('127.0.0.1', %s))
            else: connection.bind(('127.0.0.1', 0))
        except OSError as exc:
            assert exc.errno in (errno.EPERM, errno.EACCES), (action, exc.errno)
        else:
            raise AssertionError('direct socket allowed: ' + action)
print('direct sockets denied')
''' % port
        result = self.probe(code, domains=['127.0.0.1:%s' % port])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'direct sockets denied')
        self.assertEqual(hits, [])


if __name__ == '__main__':
    if arguments.policy_only:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests)
    else:
        if (sys.platform != 'darwin' or not arguments.srt
                or not Path(arguments.srt).is_absolute() or not Path(arguments.srt).is_file()):
            parser.error('actual OS tests require macOS and --srt /absolute/path/to/srt')
        version = subprocess.run([arguments.srt, '--version'], capture_output=True, text=True, timeout=5)
        if version.returncode != 0 or version.stdout.strip() != '0.0.79':
            parser.error('actual OS tests require the verified srt 0.0.79 baseline')
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(MacOSPermissions)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
