#!/usr/bin/env python3
"""Guest transport configuration and protocol faults, without a VM."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import review_transport


class GuestTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='delegate-transport.')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.cli=self.root/'limactl';self.cli.write_text('fixture');self.cli.chmod(0o700)
        self.lima=self.root/'lima';self.lima.mkdir()
        self.config={'schema_version':1,'limactl':str(self.cli),'lima_home':str(self.lima),'guest':'delegate-review',
            'guest_scripts':'/opt/delegate/scripts','guest_runtime_config':'/opt/delegate/runtime.json','guest_runtime_sha256':'a'*64}
        self.instance={'name':'delegate-review','status':'Running','arch':'aarch64','vmType':'vz','errors':[],
            'dir':str(self.lima/'delegate-review'),'config':{'plain':True,
                'ssh':{'forwardAgent':False,'forwardX11':False,'forwardX11Trusted':False,'loadDotSSHPubKeys':False},
                'containerd':{'system':False,'user':False},'rosetta':{'enabled':False}}}

    def test_explicit_local_configuration_and_effective_empty_lists(self):
        config=review_transport.validate_profile(self.config)
        result=review_transport.validate_instance(self.instance,config)
        self.assertEqual(result['guest'],'delegate-review')
        self.assertEqual(result['arch'],'aarch64')

    def test_unknown_field_noncanonical_path_and_unsafe_guest_are_rejected(self):
        for updates in [{'unexpected':'secret'},{'guest':'name;command'},{'guest_scripts':'relative'},
                {'guest_runtime_sha256':'bad'},{'lima_home':str(self.root/'missing')}]:
            with self.subTest(updates=updates),self.assertRaises(review_transport.TransportError):
                review_transport.validate_profile(dict(self.config,**updates))

    def test_actual_shares_forwarding_provisioning_or_unknown_switches_are_refused(self):
        variants=[]
        for key in ('mounts','portForwards','provision'):
            value=copy.deepcopy(self.instance);value['config'][key]=[{'fixture':True}];variants.append(value)
        for section,key in [('ssh','forwardAgent'),('ssh','forwardX11'),('containerd','user'),('rosetta','enabled')]:
            value=copy.deepcopy(self.instance);value['config'][section][key]=True;variants.append(value)
            value=copy.deepcopy(self.instance);value['config'][section].pop(key);variants.append(value)
        for value in variants:
            with self.subTest(value=value),self.assertRaises(review_transport.TransportError):
                review_transport.validate_instance(value,self.config)

    def test_wrong_stopped_or_unknown_guest_never_auto_starts(self):
        for updates in [{'name':'other'},{'status':'Stopped'},{'arch':'x86_64'},{'errors':['SECRET_ERROR']},
                        {'dir':'/outside/guest'},{'config':{}}]:
            with self.subTest(updates=updates),self.assertRaises(review_transport.TransportError):
                review_transport.validate_instance(dict(self.instance,**updates),self.config)

    def test_remote_command_is_fixed_and_credentials_are_not_transmitted(self):
        transport=review_transport.GuestTransport(self.config,self.root)
        command=transport.command('run')
        self.assertIn('--start=false',command)
        self.assertIn('--preserve-env=false',command)
        self.assertIn('--reconnect=false',command)
        self.assertNotIn('--sync',command)
        self.assertNotIn('ANTHROPIC_API_KEY',json.dumps(transport.environment))
        self.assertNotIn('OPENAI_API_KEY',json.dumps(transport.environment))
        self.assertNotIn('SSH_AUTH_SOCK',transport.environment)
        with self.assertRaises(review_transport.TransportError):transport.command('other')

    def test_payload_contains_only_fixed_scoped_snapshot_and_trusted_code_digests(self):
        context={'files':{'src/a.py':b'scope\n'},'file_sha256':{'src/a.py':'b'*64},'scope':{'include':['src/a.py'],'exclude':[]}}
        request=review_transport.request_payload(context,{'model':'sonnet','max_turns':12,'max_budget_usd':None,'task':'review'},'c'*32,self.config,30)
        document=json.loads(request)
        self.assertEqual(set(document['snapshot']['files'][0]),{'path','sha256','data'})
        self.assertEqual(document['snapshot']['files'][0]['path'],'src/a.py')
        self.assertNotIn('files',document['context'])
        self.assertEqual(set(document['code_sha256']),set(review_transport.GUEST_FILES))
        self.assertEqual(document['runtime_sha256'],'a'*64)
        self.assertNotIn('lima_home',document)

    def test_unknown_guest_preflight_failure_still_attempts_owned_cancel(self):
        transport=review_transport.GuestTransport(self.config,self.root)
        context={'files':{},'file_sha256':{},'scope':{'include':['src/a.py'],'exclude':[]},
                 'baseline':{},'diff_sha256':'b'*64,'unreviewed':[]}
        args=SimpleNamespace(model=None,max_turns=12,max_budget_usd=None,task='review')
        envelope={'schema_version':1,'execution_status':'conditions_missing','cleanup':'unverified'}
        with patch.object(transport,'preflight',return_value={'guest':'delegate-review'}), \
                patch.object(transport,'invoke',return_value=json.dumps(envelope).encode()), \
                patch.object(transport,'cancel',return_value=True) as cancel:
            report=transport.review(args,context,30)
        cancel.assert_called_once_with()
        self.assertEqual(report['execution_status'],'conditions_missing')
        self.assertEqual(report['cleanup'],'confirmed')
        self.assertEqual(report['review_outcome'],'inconclusive')


if __name__=='__main__':unittest.main()
