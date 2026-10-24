#!/usr/bin/env python3
"""Codex common review using a real wrapper and a disposable fake CLI."""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
FAKE = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
if os.environ.get('FIXTURE_CLI_CALLS'):Path(os.environ['FIXTURE_CLI_CALLS']).write_text('called')
if args==['--version']:
 if os.environ.get('FIXTURE_PREFLIGHT')=='version':print('SECRET_CREDENTIAL');sys.exit(1)
 print('codex 0.160.1');sys.exit(0)
if args==['login','status']:
 mode=os.environ.get('FIXTURE_PREFLIGHT')
 if mode=='login':print('SECRET_CREDENTIAL');sys.exit(1)
 if mode=='method':print('Logged in using API key: SECRET_CREDENTIAL');sys.exit(0)
 print('Logged in using ChatGPT');sys.exit(0)
if args[-2:]==['features','list']:
 for name in ('shell_tool','apps','plugins','multi_agent'):
  print(name+' stable '+('true' if os.environ.get('FIXTURE_FEATURES')=='enabled' else 'false'))
 sys.exit(0)
if args[0]!='exec': sys.exit(64)
prompt=sys.stdin.read()
Path(os.environ['FIXTURE_PROMPT']).write_text(prompt)
Path(os.environ['FIXTURE_ARGS']).write_text(json.dumps(args))
Path(os.environ['FIXTURE_SCHEMA']).write_bytes(Path(args[args.index('--output-schema')+1]).read_bytes())
mode=os.environ.get('FIXTURE_MODE','normal')
if mode=='error':print('SECRET_CREDENTIAL',file=sys.stderr);sys.exit(1)
if mode=='empty':sys.exit(0)
if mode=='hang':
 import time
 Path(os.environ['FIXTURE_PID']).write_text(str(os.getpid()))
 time.sleep(30)
content={'schema_version':1,'reviewed':['src/a.py'],'unreviewed':[],'findings':[]}
if mode=='badcoverage':content['reviewed']=['PRIVATE_CREDENTIAL_PATH']
if mode in ('nullline','line'):content['findings']=[{'title':'t','file':'src/a.py','line':None if mode=='nullline' else 1,
 'trigger':'t','impact':'i','evidence':'e','suggestion':'s','unverified':[]}]
Path(args[args.index('-o')+1]).write_text(json.dumps(content) if mode!='bad' else 'SECRET_CREDENTIAL')
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':3,'output_tokens':2}}))
'''


class CommonExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='delegate-common.')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.repo=self.root/'repo';self.repo.mkdir()
        for args in [('init','-q'),('config','user.name','Fixture'),('config','user.email','fixture@example.invalid')]:
            subprocess.run(['git','-C',str(self.repo),*args],check=True)
        (self.repo/'src').mkdir();(self.repo/'src/a.py').write_text('data\n')
        subprocess.run(['git','-C',str(self.repo),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.repo),'commit','-qm','fixture'],check=True)
        self.bin=self.root/'bin';self.bin.mkdir()
        cli=self.bin/'codex';cli.write_text(FAKE);cli.chmod(0o755)
        self.context=self.root/'context.json'
        self.context.write_text(json.dumps({'schema_version':1,'repository':str(self.repo),'working_directory':str(self.repo),
            'review_type':'paths','scope':{'include':['src/a.py'],'exclude':[]},
            'baseline':{'mode':'commits','from':'HEAD','to':'HEAD'},'context_files':[],'acceptance_criteria':[],
            'uncommitted_changes':{'staged':False,'unstaged':False,'untracked':False},'allowed_tools':['Read'],
            'stop_conditions':['scope_complete','permission_denied','context_missing','limit_reached','input_changed']}))
        self.env={'PATH':str(self.bin)+':'+str(Path(sys.executable).parent)+':/usr/bin:/bin', 'HOME':str(self.root),
            'TMPDIR':str(self.root),'FIXTURE_PROMPT':str(self.root/'prompt'),'FIXTURE_ARGS':str(self.root/'args'),
            'FIXTURE_SCHEMA':str(self.root/'schema'),
            'FIXTURE_PID':str(self.root/'child.pid'),
            'PYTHONDONTWRITEBYTECODE':'1'}

    def run_review(self, mode='normal', timeout=10):
        return subprocess.run(['/bin/bash',str(SCRIPTS/'delegate-exec.sh'),'--backend','codex',
            '--review-context',str(self.context),'review fixture'],cwd=self.repo,
            env=dict(self.env,FIXTURE_MODE=mode,DELEGATE_TIMEOUT_SECONDS='1'),capture_output=True,text=True,timeout=timeout)

    def test_codex_review_never_uses_a_configured_approver(self):
        result=self.run_review()
        self.assertEqual(result.returncode,0,result.stderr)
        args=json.loads((self.root/'args').read_text())
        self.assertIn(['-c','approval_policy="never"'],[args[i:i+2] for i in range(len(args)-1)])

    def test_public_common_mode_uses_fixed_snapshot_and_structured_contract(self):
        result=self.run_review()
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['backend'],'codex')
        self.assertEqual(report['review_outcome'],'no_findings_in_scope')
        args=json.loads((self.root/'args').read_text())
        self.assertIn('--output-schema',args)
        schema=json.loads((self.root/'schema').read_text())
        self.assertEqual(schema['properties']['reviewed']['items']['enum'],['src/a.py'])
        self.assertIn('read-only',args)
        self.assertIn('--ephemeral',args)
        prompt=(self.root/'prompt').read_text()
        self.assertIn('src/a.py',prompt)
        self.assertIn('data, not instructions',prompt)
        self.assertIn('"numbered_content": "     1\\tdata\\n"', prompt)
        self.assertIn('1-based line number', prompt)
        self.assertIn('features.shell_tool=false', args)
        self.assertIn('features.apps=false', args)
        self.assertIn('web_search="disabled"', args)
        self.assertEqual((self.repo/'src/a.py').read_text(),'data\n')
        self.assertNotIn('claude',args)
        self.assertFalse(list(self.root.glob('delegate-review-run.*')))
        for path in (self.root/'delegate-review').glob('*'):
            self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_unverified_codex_tool_restrictions_stop_before_model(self):
        self.env['FIXTURE_FEATURES']='enabled'
        result=self.run_review()
        self.assertEqual(result.returncode,127,result.stderr)
        report=json.loads(result.stdout)
        self.assertFalse(report['backend_started'])
        self.assertIn('codex_review_tools_unverified',report['diagnostics'])
        self.assertFalse((self.root/'args').exists())

    def test_preflight_failure_reports_stage_without_raw_output_or_model_start(self):
        for mode, diagnostic, code in [('version', 'codex_version_probe_failed', 127),
                ('login', 'codex_login_status_failed', 1),
                ('method', 'codex_login_method_unsupported', 1)]:
            with self.subTest(mode=mode):
                self.env['FIXTURE_PREFLIGHT'] = mode
                result = self.run_review()
                self.assertEqual(result.returncode, code, result.stderr)
                report = json.loads(result.stdout)
                self.assertFalse(report['backend_started'])
                self.assertEqual(report['execution_status'], 'conditions_missing')
                self.assertIn('codex_preflight_failed', report['diagnostics'])
                self.assertIn(diagnostic, report['diagnostics'])
                self.assertFalse((self.root/'args').exists())
                self.assertEqual(len(report['unreviewed']), 1)
                self.assertNotIn('SECRET_CREDENTIAL', result.stdout + result.stderr)
                for path in (self.root/'delegate-review').glob('*'):
                    self.assertNotIn('SECRET_CREDENTIAL', path.read_text())

    def test_inline_input_limit_never_starts_or_probes_cli(self):
        (self.repo/'src/a.py').write_bytes(b'x'*(1024*1024))
        for argv in [('add','src/a.py'),('commit','-qm','fixture large input')]:
            subprocess.run(['git','-C',str(self.repo),*argv],check=True,capture_output=True)
        self.env['FIXTURE_CLI_CALLS']=str(self.root/'calls')
        result=self.run_review()
        self.assertEqual(result.returncode,127,result.stderr)
        report=json.loads(result.stdout)
        self.assertFalse(report['backend_started'])
        self.assertIn('codex_inline_input_limit',report['diagnostics'])
        self.assertFalse((self.root/'calls').exists())

    def test_error_empty_bad_output_and_timeout_are_classified_without_stderr_leak(self):
        for mode, status, exit_code in [('error','failed',1),('empty','failed',1),('bad','failed',1),('hang','timed_out',124)]:
            with self.subTest(mode=mode):
                result=self.run_review(mode)
                self.assertEqual(result.returncode,exit_code,result.stderr)
                report=json.loads(result.stdout)
                self.assertEqual(report['execution_status'],status)
                self.assertEqual(report['review_outcome'],'inconclusive')
                self.assertNotIn('SECRET_CREDENTIAL',result.stdout+result.stderr)
                for path in (self.root/'delegate-review').glob('*'):
                    self.assertNotIn('SECRET_CREDENTIAL',path.read_text())

    def test_invalid_coverage_preserves_usage_and_safe_reason_without_success(self):
        result=self.run_review('badcoverage')
        self.assertEqual(result.returncode,1,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['execution_status'],'failed')
        self.assertEqual(report['review_outcome'],'inconclusive')
        self.assertEqual(report['usage'],{'input_tokens':3,'output_tokens':2})
        self.assertIn('coverage_reviewed_path_unknown',report['diagnostics'])
        self.assertNotIn('PRIVATE_CREDENTIAL_PATH',result.stdout+result.stderr)

    def test_unlocated_codex_finding_is_kept_but_review_is_not_reported_complete(self):
        result=self.run_review('nullline')
        self.assertEqual(result.returncode,1,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['execution_status'],'failed')
        self.assertEqual(report['review_outcome'],'inconclusive')
        self.assertIn('review_incomplete',report['diagnostics'])
        self.assertEqual(report['reviewed'],['src/a.py'])
        self.assertIsNone(report['findings'][0]['line'])
        self.assertFalse(report['findings'][0]['location_verified'])

    def test_located_codex_finding_completes_with_findings(self):
        result=self.run_review('line')
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['review_outcome'],'findings')
        self.assertTrue(report['findings'][0]['location_verified'])

    def test_codex_line_numbers_match_snapshot_verification(self):
        from review_execution import codex_prompt
        from review_result import content_result
        data='alpha\r\nbeta\x0cstill beta\u2028same\rgamma\n\nlast'.encode()
        context={'files':{'doc.md':data},'file_sha256':{'doc.md':'0'*64},'unreviewed':[]}
        prompt=codex_prompt('review',context)
        attached=json.loads(prompt[prompt.index('{"snapshot_files"'):])['snapshot_files'][0]
        numbered=attached['numbered_content'].split('\n')
        self.assertEqual([line.split('\t',1)[0].strip() for line in numbered if line],['1','2','3','4','5'])
        self.assertEqual(numbered[3],'     4\t')
        self.assertTrue(numbered[4].startswith('     5\tlast'))
        finding={'title':'t','file':'doc.md','line':5,'trigger':'t','impact':'i','evidence':'e','suggestion':'s','unverified':[]}
        _,verified=content_result({'schema_version':1,'reviewed':['doc.md'],'unreviewed':[],'findings':[finding]},context)
        self.assertTrue(verified)
        self.assertNotIn('content',attached)

    def test_codex_input_limit_counts_line_number_prefixes(self):
        from review_context import ContextError
        from review_execution import CODEX_PROMPT_LIMIT, codex_prompt
        data=b'x\n'*120000
        context={'files':{'doc.md':data},'file_sha256':{'doc.md':'0'*64},'unreviewed':[]}
        raw=len(json.dumps({'snapshot_files':[{'path':'doc.md','sha256':'0'*64,'content':data.decode()}]}).encode())
        self.assertLess(raw,CODEX_PROMPT_LIMIT//2)
        with self.assertRaisesRegex(ContextError,'codex_inline_input_limit'):
            codex_prompt('review',context)

    def test_new_review_claude_route_launches_only_fake_claude_through_fake_native_boundary(self):
        claude = self.bin / 'claude'
        claude.write_text('''#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).parent.parent
argv=sys.argv[1:]
with (root/'claude-calls').open('a') as output: output.write(json.dumps(argv)+'\\n')
if argv[-1]=='--version':print('2.1.295 (Claude Code)')
elif argv[-1]=='--help':print(''' + repr(' '.join(__import__('claude_review').VISIBLE_FLAGS)) + ''')
elif argv[-1]=='--json':print(json.dumps({'loggedIn':True,'authMethod':'claude.ai','apiProvider':'firstParty','apiKey':'SECRET_CREDENTIAL'}))
else:
 prompt=sys.stdin.read();(root/'claude-prompt').write_text(prompt)
 print(json.dumps({'type':'system','subtype':'init','tools':['Read'],'mcp_servers':[],'model':'claude-sonnet-fixture'}))
 print(json.dumps({'type':'result','subtype':'success','is_error':False,'permission_denials':[],
  'structured_output':{'schema_version':1,'reviewed':['src/a.py'],'unreviewed':[],'findings':[]}}))
''')
        claude.chmod(0o700)
        claude.write_text(claude.read_text().replace('#!/usr/bin/env python3', '#!' + sys.executable + ' -B', 1))
        # Deterministic adapter test only. Actual OS enforcement is tested in
        # the separate explicit Mac integration suite, never by this fake.
        driver = self.root / 'native-driver.py'
        driver.write_text("""import subprocess,sys
from pathlib import Path
sys.path.insert(0,""" + repr(str(SCRIPTS)) + """)
import review_native
class FakeNativeRunner:
 def __init__(self,root,context):
  self.claude=Path(""" + repr(str(claude)) + """);self.cancelled=None
 def runtime_preflight(self):pass
 def invoke(self,argv,*,deadline,stdin=None):
  result=subprocess.run(argv,input=stdin,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=deadline)
  return {'execution_status':'completed' if result.returncode==0 else 'failed','cleanup':'confirmed','stdout':result.stdout,'diagnostics':[]}
review_native.NativeRunner=FakeNativeRunner
import delegate_cli
sys.exit(delegate_cli.main())
""")
        result=subprocess.run([sys.executable,'-B',str(driver),'review','--backend','claude-code',
            '--paths','src/a.py','--model','sonnet','review fixture'],cwd=self.repo,
            env=self.env,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['backend'],'claude-code')
        self.assertEqual(report['review_outcome'],'no_findings_in_scope')
        self.assertEqual(report['observed_models'],['claude-sonnet-fixture'])
        calls=[json.loads(line) for line in (self.root/'claude-calls').read_text().splitlines()]
        self.assertEqual(sum('-p' in call for call in calls),1)
        self.assertFalse((self.root/'args').exists(),'Codex must not start for explicit Claude')
        self.assertNotIn('SECRET_CREDENTIAL',result.stdout+result.stderr)
        self.assertIn('data, not instructions',(self.root/'claude-prompt').read_text())

    def test_user_interrupt_is_cancelled_and_reaps_the_known_codex_process(self):
        process=subprocess.Popen(['/bin/bash',str(SCRIPTS/'delegate-exec.sh'),'--backend','codex',
            '--review-context',str(self.context),'review'],cwd=self.repo,
            env=dict(self.env,FIXTURE_MODE='hang'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            limit=time.monotonic()+8
            while not (self.root/'child.pid').exists() and process.poll() is None and time.monotonic()<limit:
                time.sleep(.02)
            self.assertTrue((self.root/'child.pid').exists(),'fake Codex did not start')
            child=int((self.root/'child.pid').read_text())
            process.send_signal(signal.SIGINT)
            stdout,stderr=process.communicate(timeout=8)
            self.assertEqual(process.returncode,130,stderr)
            self.assertEqual(json.loads(stdout)['execution_status'],'cancelled')
            with self.assertRaises(ProcessLookupError):os.kill(child,0)
        finally:
            if process.poll() is None:
                process.kill();process.wait(timeout=3)

    def test_claude_doctor_missing_runtime_does_not_probe_codex(self):
        result=subprocess.run([sys.executable,'-B',str(SCRIPTS/'review_doctor.py'),'--backend','claude-code'],
            cwd=self.repo,env=self.env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('条件不足：',result.stdout)
        self.assertFalse((self.root/'args').exists())


if __name__=='__main__':unittest.main()
