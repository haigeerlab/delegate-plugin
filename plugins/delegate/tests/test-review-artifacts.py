#!/usr/bin/env python3
"""Private artifacts, minimal logs and bounded retention."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import review_execution


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='delegate-artifacts.')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.repo=self.root/'repo';self.repo.mkdir()
        self.context={'repository':str(self.repo)}
        self.report={'backend':'claude-code','backend_started':True,'execution_status':'failed',
            'cleanup':'confirmed','diagnostics':['permission_denied'],'findings':[],
            'reviewed':['sensitive_filename.py'],'unreviewed':[],'task':'DO_NOT_LOG_TASK','thinking':'DO_NOT_LOG_THINKING'}
        self.patch=patch('review_execution.tempfile.gettempdir',return_value=str(self.root))
        self.patch.start();self.addCleanup(self.patch.stop)

    def test_permissions_and_process_log_do_not_retain_task_or_findings(self):
        paths=review_execution.save_artifacts(self.report,self.context)
        log=Path(paths['log'])
        self.assertEqual(log.parent.stat().st_mode&0o777,0o700)
        for path in paths.values():self.assertEqual(Path(path).stat().st_mode&0o777,0o600)
        self.assertNotIn('DO_NOT_LOG',log.read_text())
        self.assertNotIn('sensitive_filename',log.read_text())
        self.assertEqual(json.loads(Path(paths['report']).read_text()),self.report)

    def test_source_overlapping_tmp_or_symlink_log_root_is_refused(self):
        with patch('review_execution.tempfile.gettempdir',return_value=str(self.repo)):
            with self.assertRaises(ValueError):review_execution.save_artifacts(self.report,self.context)
        outside=self.root/'outside';outside.mkdir()
        (self.root/'delegate-review').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):review_execution.save_artifacts(self.report,self.context)
        self.assertEqual(list(outside.iterdir()),[])

    def test_retention_keeps_fifty_groups_and_does_not_delete_unrelated_files(self):
        for _ in range(51):last=review_execution.save_artifacts(self.report,self.context)
        root=self.root/'delegate-review'
        marker=root/'unrelated';marker.write_text('keep')
        review_execution.save_artifacts(self.report,self.context)
        self.assertEqual(len(list(root.glob('*.report.json'))),50)
        self.assertEqual(len(list(root.glob('*.answer'))),50)
        self.assertEqual(len(list(root.glob('*.log'))),50)
        self.assertTrue(Path(last['report']).exists())
        self.assertEqual(marker.read_text(),'keep')


if __name__=='__main__':unittest.main()
