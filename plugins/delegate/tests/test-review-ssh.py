#!/usr/bin/env python3
"""Actual SSH-disconnect cleanup probe for an already populated fixture VM.

Never creates a VM or installs tools. Run only with the dedicated temporary
environment documented in the verification record; no models/credentials.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import tempfile
import time
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True)
arguments = parser.parse_args()
root = Path(arguments.root)
if (not root.is_absolute() or root.resolve(strict=True) != root
        or not root.name.startswith(('delegate-review-vm.', 'delegate-review-cli-vm.'))
        or root.parent != Path('/private/tmp')):
    parser.error('requires this run\'s existing dedicated temporary VM root')
environment = {'HOME': str(root / 'home'), 'TMPDIR': str(root / 'tmp'),
               'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'}
ssh = ['/usr/bin/ssh', '-F', str(root / 'lima/delegate-review/ssh.config'),
       '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=5', '-T', 'lima-delegate-review']


def command(code):
    # SSH joins command arguments through the remote shell. This is fixed
    # trusted fixture code, shell-quoted; task/file contents never become code.
    return ssh + ['/usr/bin/python3', '-B', '-c', shlex.quote(code)]


class SSHGate(unittest.TestCase):
    def test_scoped_snapshot_and_invalid_payload_through_real_ssh(self):
        source = Path(__file__).resolve().parents[1] / 'scripts/review_guest.py'
        spec = importlib.util.spec_from_file_location('guest', source)
        guest = importlib.util.module_from_spec(spec); spec.loader.exec_module(guest)
        code = '''import importlib.util,json,sys,tempfile
from pathlib import Path
s=importlib.util.spec_from_file_location('guest','/tmp/delegate-tests/scripts/review_guest.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='delegate-staging.') as directory:
 target=Path(directory).resolve()
 wire=sys.stdin.buffer.read(m.MAX_WIRE_BYTES+1)
 try:
  paths=m.unpack_snapshot(wire,target)
 except ValueError:
  print(json.dumps({'status':'rejected','empty':not any(target.iterdir())}));sys.exit(2)
 print(json.dumps({'status':'staged','files':{name:m.hashlib.sha256((target/name).read_bytes()).hexdigest() for name in paths}}))
'''
        with tempfile.TemporaryDirectory(dir=root) as directory:
            scope = Path(directory).resolve(); (scope / 'module').mkdir()
            (scope / 'module/a.txt').write_text('fixed review input')
            (scope / 'SPEC.md').write_text('acceptance fixture')
            (scope / 'excluded.txt').write_text('must never cross SSH')
            paths = ['module/a.txt', 'SPEC.md']
            wire = guest.pack_snapshot(scope, paths)
            result = subprocess.run(command(code), env=environment, input=wire,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=8)
            self.assertEqual(result.returncode, 0)
            expected = {name: hashlib.sha256((scope / name).read_bytes()).hexdigest() for name in paths}
            self.assertEqual(json.loads(result.stdout), {'status': 'staged', 'files': expected})
            invalid = json.loads(wire); invalid['files'][-1]['path'] = '../escape'
            result = subprocess.run(command(code), env=environment,
                input=json.dumps(invalid).encode(), stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=8)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout), {'status': 'rejected', 'empty': True})

    def test_disconnect_has_bounded_guest_cleanup_and_unknown_terminal_result(self):
        code = '''import importlib.util,json,os,sys,threading,time
os.environ['PATH']='/tmp/delegate-tools/node-v22.22.0-linux-arm64/bin:/usr/bin:/bin'
os.environ['XDG_RUNTIME_DIR']='/run/user/%s'%os.getuid()
os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus'
sys.argv=['fixture','--srt','/tmp/delegate-tools/srt/node_modules/.bin/srt']
s=importlib.util.spec_from_file_location('gate','/tmp/delegate-tests/tests/test-review-linux.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
t=m.LinuxGate();t.setUp()
b=m.service.ReviewService(manager='/usr/bin/systemctl')
def ready():
 expires=time.monotonic()+5
 while not (t.run/'ready').exists() and time.monotonic()<expires:time.sleep(.01)
 if (t.run/'ready').exists():
  facts=b.observe();print(json.dumps({'unit':b.unit,'group':facts['ControlGroup']}),flush=True)
threading.Thread(target=ready,daemon=True).start()
try:
 b.run('/usr/bin/systemd-run',[m.args.srt,'--settings',str(t.policy),'--','/usr/bin/python3','-B','/tmp/delegate-tools/review_network.py','--','/usr/bin/python3','-B','-c',t.helper()],deadline=3,environment=t.env,cwd=t.snapshot,control=t.control)
finally:t.temp.cleanup()
'''
        with tempfile.TemporaryFile(dir=root) as output:
            process = subprocess.Popen(command(code), env=environment, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.DEVNULL, start_new_session=True)
            facts = None
            try:
                expires = time.monotonic() + 8
                while time.monotonic() < expires:
                    output.seek(0); data = output.read(4097)
                    if b'\n' in data:
                        facts = json.loads(data.splitlines()[0]); break
                    if process.poll() is not None:
                        break
                    time.sleep(.02)
                self.assertIsNotNone(facts, 'SSH fixture never supplied owned unit evidence')
                self.assertEqual(set(facts), {'unit', 'group'})
                self.assertRegex(facts['unit'], r'^delegate-review-[0-9a-f]{32}\.service$')
                self.assertRegex(facts['group'], r'^/[A-Za-z0-9_.@:/-]+$')
                self.assertTrue(facts['group'].endswith('/' + facts['unit']))
                self.assertFalse(any(part in ('', '.', '..') for part in facts['group'].split('/')[1:]))
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=2)
                # A new independent SSH channel checks kernel membership after
                # losing the first channel's final result. Never invent success.
                verify = '''import importlib.util,time
s=importlib.util.spec_from_file_location('service','/tmp/delegate-tests/scripts/review_service.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b=m.ReviewService(manager='/usr/bin/systemctl')
group=%r
expires=time.monotonic()+6
while not b._empty(group) and time.monotonic()<expires:time.sleep(.02)
assert b._empty(group),'guest cgroup survived SSH disconnect'
print('cleanup confirmed; terminal result unknown')
''' % facts['group']
                result = subprocess.run(command(verify), env=environment, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=12)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), b'cleanup confirmed; terminal result unknown')
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=2)


if __name__ == '__main__':
    unittest.main(argv=[__file__], verbosity=2)
