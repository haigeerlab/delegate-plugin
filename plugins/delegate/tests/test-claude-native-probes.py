#!/usr/bin/env python3
"""Original CLI interface probes in a prepared disposable Linux guest.

Version/help/logout-status/invalid-option only: no -p, tasks, login or model.
Requires a verified native binary SHA-256 and the approved enforcing runtime.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from claude_review import SAFE_PREFIX, VISIBLE_FLAGS, preflight, PreflightError
from review_isolation import build_linux_policy
from review_service import ReviewService

parser = argparse.ArgumentParser()
parser.add_argument('--claude', required=True)
parser.add_argument('--sha256', required=True)
parser.add_argument('--srt', required=True)
options = parser.parse_args()
claude = Path(options.claude)
srt = Path(options.srt).resolve(strict=True)
if (sys.platform!='linux' or str(claude)!='/tmp/delegate-tools/claude-native/package/claude'
        or claude.resolve(strict=True)!=claude or not re.fullmatch(r'[0-9a-f]{64}',options.sha256)):
    parser.error('requires the canonical pinned original CLI in this dedicated guest')


class NativeProbes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        digest=hashlib.sha256()
        with claude.open('rb') as source:
            for block in iter(lambda:source.read(1048576),b''):digest.update(block)
        assert digest.hexdigest()==options.sha256
        cls.temp=tempfile.TemporaryDirectory(prefix='delegate-native-probes.')
        cls.root=Path(cls.temp.name).resolve()
        cls.snapshot=cls.root/'snapshot';cls.writable=cls.root/'writable';cls.control=cls.root/'control'
        for path in (cls.snapshot,cls.writable,cls.control):path.mkdir(mode=0o700)
        cls.home=Path.home().resolve(strict=True)
        assert not (cls.home/'.claude').exists() and not (cls.home/'.claude.json').exists(), 'fresh unauthenticated guest required'
        cls.environment={'HOME':str(cls.home),'PATH':'/tmp/delegate-tools/node-v22.22.0-linux-arm64/bin:/usr/bin:/bin',
            'SHELL':'/bin/bash','TMPDIR':str(cls.writable),'CLAUDE_CODE_TMPDIR':str(cls.writable),
            'PYTHONDONTWRITEBYTECODE':'1','DELEGATE_REVIEW_DEPTH':'1','DISABLE_AUTOUPDATER':'1',
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','DISABLE_TELEMETRY':'1','DISABLE_ERROR_REPORTING':'1',
            'ENABLE_CLAUDEAI_MCP_SERVERS':'false','CLAUDE_CODE_DISABLE_ARTIFACT':'1','CLAUDE_CODE_SKIP_PROMPT_HISTORY':'1'}
        os.environ.update(XDG_RUNTIME_DIR='/run/user/%s'%os.getuid(),DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/%s/bus'%os.getuid())
        readable=[Path('/usr'),claude,srt.parents[3],Path('/tmp/delegate-tools/node-v22.22.0-linux-arm64'),
            Path('/tmp/delegate-tools/review_network.py')]
        for p in (Path('/etc/ld.so.cache'),Path('/etc/hosts'),Path('/etc/nsswitch.conf'),Path('/etc/resolv.conf'),Path('/etc/ssl/certs')):
            if p.exists():readable.append(p.resolve(strict=True))
        cls.policy=cls.control/'policy.json'
        cls.policy.write_text(json.dumps(build_linux_policy(snapshot=cls.snapshot,writable=cls.writable,
            home=cls.home,protected=[cls.control],readable=readable,allowed_domains=['api.anthropic.com:443'])))
        cls.policy.chmod(0o600)
        cls.records=[]

    @classmethod
    def tearDownClass(cls):
        assert not (cls.home/'.claude').exists() and not (cls.home/'.claude.json').exists(), 'guest global state changed'
        Path('/tmp/delegate-runtime/native-probes-summary.json').write_text(json.dumps(cls.records,indent=2))
        cls.temp.cleanup()

    def invoke(self, argv, *, deadline):
        # All trusted call sites are model-free; prohibit prompt/task/session flags.
        self.assertFalse(set(argv)&{'-p','--print','--resume','--continue'})
        boundary=ReviewService(manager='/usr/bin/systemctl')
        wrapped=[str(srt),'--settings',str(self.policy),'--','/usr/bin/python3','-B',
            '/tmp/delegate-tools/review_network.py','--',*argv]
        result=boundary.run('/usr/bin/systemd-run',wrapped,deadline=deadline,
            environment=self.environment,cwd=self.snapshot,control=self.control)
        self.assertEqual(result['cleanup'],'confirmed',result['diagnostics'])
        return result

    def test_version_inside_enforcing_boundary(self):
        result=self.invoke([str(claude),*SAFE_PREFIX,'--version'],deadline=5)
        self.assertEqual(result['execution_status'],'completed',result['diagnostics'])
        self.assertRegex(result['stdout'],rb'^2\.1\.295(?: \(Claude Code\))?\s*$')
        self.records.append({'probe':'version','version':'2.1.295','cleanup':result['cleanup']})

    def test_visible_capabilities_inside_enforcing_boundary(self):
        result=self.invoke([str(claude),*SAFE_PREFIX,'--help'],deadline=5)
        self.assertEqual(result['execution_status'],'completed',result['diagnostics'])
        flags=set(re.findall(rb'--[a-z][a-z-]*',result['stdout']))
        self.assertTrue(all(f.encode() in flags for f in VISIBLE_FLAGS))
        self.records.append({'probe':'help','required_flags_present':True,'cleanup':result['cleanup']})

    def test_logged_out_json_is_not_usable_authentication(self):
        result=self.invoke([str(claude),*SAFE_PREFIX,'auth','status','--json'],deadline=5)
        value=json.loads(result['stdout'])
        self.assertIs(value.get('loggedIn'),False)
        self.assertEqual(result['execution_status'],'failed')
        self.records.append({'probe':'auth_status','logged_in':False,'cleanup':result['cleanup']})

    def test_preflight_refuses_original_unauthenticated_cli(self):
        with self.assertRaises(PreflightError) as caught:
            preflight(str(claude),self.invoke)
        self.assertEqual(str(caught.exception),'authentication_missing')
        self.records.append({'probe':'adapter_preflight','refused':True,'diagnostic':str(caught.exception)})

    def test_unsupported_option_is_rejected_before_session(self):
        command=[str(claude),*SAFE_PREFIX,'--delegate-native-probe-invalid']
        code="import json,subprocess; p=subprocess.run(%r,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=4); print(json.dumps({'exit':p.returncode,'unknown_option':b'unknown option' in p.stderr and b'--delegate-native-probe-invalid' in p.stderr}))"%command
        result=self.invoke(['/usr/bin/python3','-B','-c',code],deadline=5)
        self.assertEqual(result['execution_status'],'completed')
        value=json.loads(result['stdout']);self.assertNotEqual(value['exit'],0);self.assertTrue(value['unknown_option'])
        self.records.append({'probe':'invalid_option','exit':value['exit'],'rejected':True,'cleanup':result['cleanup']})


if __name__=='__main__':unittest.main(argv=[__file__],verbosity=2)
