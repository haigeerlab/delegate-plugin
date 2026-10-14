#!/usr/bin/env python3
"""Actual prepared guest plus a pinned fake Claude; never invokes a model.

Requires the separately authorized disposable VM and fake runtime profile.
Not part of the offline suite or real cross-model/host acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
import unittest

FAKE_CLAUDE = r'''#!/usr/bin/python3 -B
import json,os,re,sys,time
from pathlib import Path
sys.path.insert(0,'/tmp/delegate-tests/scripts')
from claude_review import VISIBLE_FLAGS
args=sys.argv[1:]
if args[-1:] == ['--version']:print('2.1.295 (Claude Code)');sys.exit(0)
if args[-1:] == ['--help']:print(' '.join(VISIBLE_FLAGS));sys.exit(0)
if args[-1:] == ['--json']:print(json.dumps({'loggedIn':True,'authMethod':'claude.ai','apiProvider':'firstParty','apiKey':'FIXTURE_SECRET_NOT_A_CREDENTIAL'}));sys.exit(0)
assert '-p' in args and '--safe-mode' in args and '--restricted' in args and '--no-session-persistence' in args
assert args[args.index('--permission-mode')+1]=='dontAsk'
assert args[args.index('--tools')+1]=='Read'
assert all(x not in args for x in ('--bare','--dangerously-skip-permissions','--effort','--resume'))
prompt=sys.stdin.read()
mode=re.search(r'Task: fixture-mode=([a-z_]+)',prompt).group(1)
if mode=='empty':sys.exit(0)
if mode=='malformed':print('FIXTURE_SECRET_NOT_A_CREDENTIAL invalid stream');sys.exit(0)
init={'type':'system','subtype':'init','tools':['Bash'] if mode=='unsafe_tools' else ['Read'],'mcp_servers':[],'model':'claude-sonnet-fixture'}
print(json.dumps(init),flush=True)
if mode=='unsafe_tools':time.sleep(30);sys.exit(1)
if mode=='hang':
 pid=os.fork()
 if pid==0:
  os.setsid();Path(os.environ['TMPDIR'],'started.pid').write_text(str(os.getpid()));time.sleep(60);os._exit(0)
 Path(os.environ['TMPDIR'],'parent.pid').write_text(str(os.getpid()));time.sleep(60);sys.exit(1)
path=Path('data/src/a.py')
assert path.read_text()=='first line\nsecond line\n'
denials=[]
try:path.write_text('unauthorized')
except OSError:
 if mode=='denied':denials=[{'tool_name':'Write','tool_input':{'file_path':'data/src/a.py'}}]
else:raise AssertionError('snapshot write unexpectedly permitted')
assert path.read_text()=='first line\nsecond line\n'
findings=[]
if mode=='findings':findings=[{'title':'Synthetic fixture issue','file':'src/a.py','line':1,'trigger':'Fixed fixture input','impact':'Synthetic demonstration','evidence':'first line','suggestion':'Check the fixture','unverified':['No real bug claim']}]
print(json.dumps({'type':'result','subtype':'success','is_error':False,'permission_denials':denials,
 'structured_output':{'schema_version':1,'reviewed':['src/a.py'],'unreviewed':[],'findings':findings}}),flush=True)
'''

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True)
parser.add_argument('--profile', required=True)
options = parser.parse_args()
root = Path(options.root)
profile_path = Path(options.profile)
if (not root.is_absolute() or root.resolve(strict=True) != root or root.parent != Path('/private/tmp')
        or not root.name.startswith('delegate-review-cli-vm.')
        or profile_path.resolve(strict=True) != profile_path or profile_path.parent != root):
    parser.error("requires this batch's canonical disposable root and profile")
profile = json.loads(profile_path.read_bytes())
if profile.get('guest_runtime_config') != '/tmp/delegate-runtime/fake.json':
    parser.error('only the explicitly prepared fake runtime is supported; no original CLI execution')
ssh = ['/usr/bin/ssh', '-F', str(root / 'lima/delegate-review/ssh.config'),
       '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=5', '-T', 'lima-delegate-review']
control_environment = {'HOME': str(root/'home'), 'TMPDIR': str(root/'tmp'), 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'}
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def guest(code, timeout=10):
    code = "import os;os.environ['XDG_RUNTIME_DIR']='/run/user/%s'%os.getuid();os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus';" + code
    result = subprocess.run(ssh + ['/usr/bin/python3', '-B', '-c', shlex.quote(code)],
        env=control_environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
    if result.returncode:
        # Preserve the failure category without dumping SSH or guest stderr.
        categories = [label for marker, label in (
            (b'Connection closed', 'connection_closed'),
            (b'Connection reset', 'connection_reset'),
            (b'Connection refused', 'connection_refused'),
            (b'Connection timed out', 'connection_timed_out'),
            (b'Traceback', 'guest_python_error'),
            (b'SyntaxError', 'guest_syntax_error'),
        ) if marker in result.stderr]
        raise AssertionError('trusted guest control probe failed: exit=%s categories=%s'
                             % (result.returncode, categories))
    return json.loads(result.stdout)


class GuestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Pin the executable fixture before any public task can be launched.
        proof = guest("import hashlib,json;from pathlib import Path;p=Path('/tmp/delegate-runtime/fake.json');config=json.loads(p.read_bytes());print(json.dumps({'claude':config['claude'],'runtime':hashlib.sha256(p.read_bytes()).hexdigest(),'fixture':hashlib.sha256(Path('/tmp/delegate-tools/fake-claude').read_bytes()).hexdigest()}))")
        assert proof == {'claude': '/tmp/delegate-tools/fake-claude',
            'runtime': profile['guest_runtime_sha256'], 'fixture': hashlib.sha256(FAKE_CLAUDE.encode()).hexdigest()}
        cls.temp = tempfile.TemporaryDirectory(prefix='integration.', dir=root)
        cls.work = Path(cls.temp.name).resolve()
        cls.repo = cls.work/'repo'; cls.repo.mkdir(mode=0o700)
        (cls.repo/'src').mkdir(); (cls.repo/'src/a.py').write_text('first line\nsecond line\n')
        cls.env = dict(control_environment, PATH=str(Path(sys.executable).parent)+':/usr/bin:/bin',
            TMPDIR=str(cls.work), DELEGATE_CLAUDE_GUEST_CONFIG=str(profile_path), PYTHONDONTWRITEBYTECODE='1')
        for args in (['init','-q'], ['add','src/a.py'], ['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','temporary fixture']):
            subprocess.run(['/usr/bin/git','-C',str(cls.repo),*args], env=dict(cls.env,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null'),check=True)
        cls.context = cls.work/'context.json'
        cls.context.write_text(json.dumps({'schema_version':1,'repository':str(cls.repo),'working_directory':str(cls.repo),
            'review_type':'paths','scope':{'include':['src/a.py'],'exclude':[]},'baseline':{'mode':'commits','from':'HEAD','to':'HEAD'},
            'context_files':[],'acceptance_criteria':['Fixed fixture only'],
            'uncommitted_changes':{'staged':False,'unstaged':False,'untracked':False},'allowed_tools':['Read'],
            'stop_conditions':['scope_complete','permission_denied','context_missing','limit_reached','input_changed']}))
        cls.command = ['/bin/bash',str(SCRIPTS/'delegate-exec.sh'),'--backend','claude-code',
            '--review-context',str(cls.context),'--model','sonnet']
        cls.records = []

    @classmethod
    def tearDownClass(cls):
        (root/'logs/public-integration-summary.json').write_text(json.dumps(cls.records,indent=2))
        cls.temp.cleanup()

    def verify(self, result, mode, status, exit_code):
        self.assertEqual(result.returncode,exit_code,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['execution_status'],status,report)
        self.assertEqual(report['backend'],'claude-code')
        self.assertEqual(report['cleanup'],'confirmed',report)
        self.assertNotIn('FIXTURE_SECRET_NOT_A_CREDENTIAL',result.stdout+result.stderr)
        self.assertEqual((self.repo/'src/a.py').read_text(),'first line\nsecond line\n')
        self.assertEqual(subprocess.check_output(['/usr/bin/git','-C',str(self.repo),'status','--porcelain'],env=self.env),b'')
        for path in (self.work/'delegate-review').glob('*'):
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            self.assertNotIn('FIXTURE_SECRET_NOT_A_CREDENTIAL',path.read_text())
        self.records.append({'mode':mode,'execution_status':report['execution_status'],'cleanup':report['cleanup'],
            'review_outcome':report['review_outcome'],'diagnostics':report['diagnostics'],'backend':'claude-code','executor':'pinned_fake_cli_in_actual_guest'})
        return report

    def invoke(self, mode, status='failed', exit_code=1, deadline='5'):
        result=subprocess.run(self.command+['fixture-mode='+mode],env=dict(self.env,DELEGATE_TIMEOUT_SECONDS=deadline),
            cwd=self.repo,capture_output=True,text=True,timeout=45)
        return self.verify(result,mode,status,exit_code)

    def observe_ready(self, process):
        # Poll inside one independent SSH connection, rather than opening a
        # new handshake for every readiness check. Do not retry failed SSH.
        code='''import json,sys,time
from pathlib import Path
sys.path.insert(0,'/tmp/delegate-tests/scripts')
from review_service import ReviewService
root=Path('/tmp/delegate-review-control');expires=time.monotonic()+12;result=None
while time.monotonic()<expires:
 runs=[p for p in root.glob('run-*') if (p/'writable/started.pid').exists()]
 if len(runs)==1:
  b=ReviewService(manager='/usr/bin/systemctl')
  b.unit=(runs[0]/'control/active.unit').read_text();result=b.observe();break
 time.sleep(.05)
print(json.dumps(result))
'''
        facts=guest(code,timeout=18)
        self.assertIsNotNone(facts,'actual cgroup helper readiness not observed')
        self.assertEqual(facts['ActiveState'],'active');self.assertTrue(facts['ControlGroup'].endswith('/'+facts['Id']))
        return facts

    def finish_process(self, process):
        if process.poll() is None:process.terminate()
        try:process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill();process.communicate(timeout=3)

    def verify_group_empty(self, facts):
        code="import json,sys,time;sys.path.insert(0,'/tmp/delegate-tests/scripts');from review_service import ReviewService;b=ReviewService(manager='/usr/bin/systemctl');group=%r;expires=time.monotonic()+5;\nwhile not b._empty(group) and time.monotonic()<expires:time.sleep(.02)\nprint(json.dumps({'empty':b._empty(group)}))"%facts['ControlGroup']
        self.assertEqual(guest(code,timeout=8),{'empty':True})

    def test_normal_read_and_actual_snapshot_write_denial(self):
        report=self.invoke('normal','completed',0)
        self.assertEqual(report['review_outcome'],'no_findings_in_scope')
        self.assertEqual(report['reviewed'],['src/a.py']);self.assertEqual(report['unreviewed'],[])

    def test_synthetic_finding_keeps_original_location(self):
        report=self.invoke('findings','completed',0)
        self.assertEqual(report['review_outcome'],'findings');self.assertEqual(report['findings'][0]['line'],1)
        self.assertTrue(report['findings'][0]['location_verified'])

    def test_actual_write_denial_is_not_a_pass(self):
        report=self.invoke('denied')
        self.assertEqual(report['review_outcome'],'inconclusive');self.assertIn('permission_denied',report['diagnostics'])

    def test_empty_and_malformed_outputs_are_failed_without_raw_output(self):
        for mode in ('empty','malformed'):
            with self.subTest(mode=mode):self.assertEqual(self.invoke(mode)['review_outcome'],'inconclusive')

    def test_unsafe_initial_tools_stop_actual_service(self):
        self.assertIn('tool_boundary_unverified',self.invoke('unsafe_tools')['diagnostics'])

    def test_timeout_reaps_started_detached_helper(self):
        process=subprocess.Popen(self.command+['fixture-mode=hang'],cwd=self.repo,
            env=dict(self.env,DELEGATE_TIMEOUT_SECONDS='4'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            facts=self.observe_ready(process);stdout,stderr=process.communicate(timeout=15)
            self.verify(subprocess.CompletedProcess(process.args,process.returncode,stdout,stderr),'timeout','timed_out',124)
            self.verify_group_empty(facts)
        finally:
            self.finish_process(process)

    def test_interrupt_signals_reap_started_detached_helper(self):
        for signum in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):
            with self.subTest(signum=signum):
                process=subprocess.Popen(self.command+['fixture-mode=hang'],cwd=self.repo,
                    env=dict(self.env,DELEGATE_TIMEOUT_SECONDS='20'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                try:
                    facts=self.observe_ready(process);process.send_signal(signum);stdout,stderr=process.communicate(timeout=15)
                    self.verify(subprocess.CompletedProcess(process.args,process.returncode,stdout,stderr),signum.name,'cancelled',128+signum)
                    self.verify_group_empty(facts)
                finally:
                    self.finish_process(process)


if __name__=='__main__':unittest.main(argv=[__file__],verbosity=2)
