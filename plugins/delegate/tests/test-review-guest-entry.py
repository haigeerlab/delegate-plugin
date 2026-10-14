#!/usr/bin/env python3
"""Guest controller validation only; no Linux or authentication claims."""
import json
import copy
import base64
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import review_guest_entry


class GuestEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='delegate-guest-entry.')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        for name in ('claude','srt'):
            (self.root/name).write_text('fixture');(self.root/name).chmod(0o700)
        self.runtime={'schema_version':1,'claude':str(self.root/'claude'),'srt':str(self.root/'srt'),
                      'node_bin':str(self.root),'readable_paths':['/usr'],'allowed_domains':['api.anthropic.com']}

    def test_runtime_is_explicit_and_rejects_arbitrary_provider_or_commands(self):
        self.assertEqual(review_guest_entry.validate_runtime(copy.deepcopy(self.runtime))['claude'],str(self.root/'claude'))
        for change in [{'environment':{'ANTHROPIC_API_KEY':'SECRET'}},{'allowed_domains':['*.anthropic.com']},
                {'allowed_domains':['attacker.invalid']},{'claude':'claude --write'}, {'readable_paths':['/']},
                {'schema_version':True}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                review_guest_entry.validate_runtime(dict(self.runtime,**change))

    def test_private_control_directory_cannot_alias_other_paths(self):
        safe=self.root/'control';review_guest_entry.private_directory(safe)
        self.assertEqual(safe.stat().st_mode&0o777,0o700)
        alias=self.root/'alias';alias.symlink_to(safe)
        with self.assertRaises(ValueError):review_guest_entry.private_directory(alias)
        safe.chmod(0o755)
        with self.assertRaises(ValueError):review_guest_entry.private_directory(safe)

    def test_unknown_action_bad_identifier_and_extra_fields_are_rejected(self):
        for action, run_id in [('other','a'*32),('cancel','../outside'),('cancel','a'*31)]:
            with self.subTest(action=action),self.assertRaises(ValueError):
                review_guest_entry.cancel_request({'run_id':run_id},action=action,root=self.root)
        with self.assertRaises(ValueError):
            review_guest_entry.cancel_request({'run_id':'a'*32,'unexpected':'command'},action='cancel',root=self.root)

    def test_cancel_without_known_owned_unit_does_not_claim_cleanup(self):
        report=review_guest_entry.cancel_request({'run_id':'a'*32},action='cancel',root=self.root)
        self.assertEqual(report['cleanup'],'unverified')
        self.assertEqual(report['execution_status'],'cancelled')
        self.assertFalse((self.root/('run-'+'a'*32)).exists())

    def test_cancel_during_runtime_probe_does_not_start_another_probe_or_model(self):
        configuration=self.root/'runtime.json'; configuration.write_text(json.dumps(self.runtime))
        file_digest=hashlib.sha256(b'scope\n').hexdigest()
        request={'schema_version':1,'run_id':'a'*32,'timeout':30,
            'runtime_config':str(configuration),'runtime_sha256':hashlib.sha256(configuration.read_bytes()).hexdigest(),
            'code_sha256':{},'arguments':{'model':None,'max_turns':12,'max_budget_usd':None,'task':'review'},
            'snapshot':{'schema_version':1,'files':[{'path':'a.py','sha256':file_digest,
                       'data':base64.b64encode(b'scope\n').decode()}]},
            'context':{'allowed_tools':['Read'],'scope':{},'baseline':{},'diff_sha256':'b'*64,
                       'file_sha256':{'a.py':file_digest},'unreviewed':[]}}
        with patch.object(review_guest_entry.platform,'system',return_value='Linux'), \
                patch.object(review_guest_entry.platform,'machine',return_value='aarch64'), \
                patch.object(review_guest_entry,'ROOT',self.root/'control-root'), \
                patch.object(review_guest_entry,'build_linux_policy',return_value={}), \
                patch.object(review_guest_entry,'ReviewService') as boundary, \
                patch.object(review_guest_entry,'execute') as execute, patch.dict(os.environ):
            boundary.return_value.unit='delegate-review-'+'c'*32+'.service'
            boundary.return_value.run.return_value={'execution_status':'cancelled','cleanup':'confirmed',
                                                     'stdout':b'','diagnostics':[]}
            report=review_guest_entry.run_request(request)
        self.assertEqual(report['execution_status'],'cancelled')
        self.assertEqual(report['cleanup'],'confirmed')
        self.assertEqual(boundary.return_value.run.call_count,1)
        execute.assert_not_called()


if __name__=='__main__':unittest.main()
