#!/usr/bin/env python3
"""Offline native routing/error contracts; no Darwin jobs or real executors."""
import errno
import json
import plistlib
import signal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import delegate_backend
import review_native
from review_macos import BoundaryError, Kernel, MacBoundary, private_json


class NativeContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.context = {'repository': str(self.root), 'files': {'src/a.py': b'fixture\n'},
            'allowed_tools': ['Read'], 'scope': {}, 'baseline': {}, 'diff_sha256': None,
            'file_sha256': {}, 'unreviewed': []}
        self.args = SimpleNamespace(model='sonnet', task='fixture', max_turns=12, max_budget_usd=None)

    def test_launchd_anchor_does_not_require_installation_directory_access(self):
        control = self.root / 'control'; control.mkdir(mode=0o700)
        with patch('review_macos.Kernel'), \
                patch.object(MacBoundary, 'launchctl', return_value=1), \
                patch.object(MacBoundary, 'service_loaded', return_value=False):
            result = MacBoundary(control).run(['/usr/bin/true'], cwd=self.root,
                environment={'PATH': '/usr/bin:/bin'}, deadline=1)
        self.assertFalse(result['backend_started'])
        job = plistlib.loads((control / 'job.plist').read_bytes())
        anchor = Path(job['ProgramArguments'][2])
        self.assertEqual(anchor.parent.parent, control,
            'launchd must not reopen the plugin installation in Documents')
        self.assertEqual(anchor.parent.stat().st_mode & 0o777, 0o700)
        for name in ('review_macos.py', 'review_result.py', 'claude_review.py'):
            staged = anchor.parent / name
            self.assertEqual(staged.read_bytes(), (SCRIPTS / name).read_bytes())
            self.assertEqual(staged.stat().st_mode & 0o777, 0o600)

    def test_public_claude_branch_selects_native_without_loading_guest(self):
        expected = ({'execution_status': 'failed', 'backend': 'claude-code', 'diagnostics': [],
                     'backend_started': True, 'reviewed': [],
                     'unreviewed': [{'path': 'src/a.py', 'reason': 'fixture_failed'}]}, 1)
        with patch('review_context.capture', return_value=self.context), \
                patch('review_native.native_review', return_value=expected) as native, \
                patch('review_execution.save_artifacts', return_value={'report': 'fixture'}), \
                patch('review_result.render', return_value='fixture\n'):
            code = delegate_backend.main(['--backend', 'claude-code', '--review-context',
                'fixture.json', 'fixture'])
        self.assertEqual(code, 1)
        native.assert_called_once()

    def test_missing_native_runtime_never_executes_or_switches_backend(self):
        with patch.object(review_native, 'NativeRunner', side_effect=BoundaryError('sandbox_runtime_missing')):
            report, code = review_native.native_review(self.args, self.context)
        self.assertEqual(code, 127)
        self.assertEqual(report['backend'], 'claude-code')
        self.assertFalse(report['backend_started'])
        self.assertEqual(report['execution_status'], 'conditions_missing')
        self.assertEqual(report['diagnostics'], ['sandbox_runtime_missing'])

    def test_runtime_cancellation_is_not_authentication_or_empty_success(self):
        with patch.object(review_native, 'NativeRunner', side_effect=BoundaryError('runtime_cancelled')):
            report, code = review_native.native_review(self.args, self.context)
        self.assertEqual((code, report['execution_status'], report['review_outcome']),
                         (130, 'cancelled', 'inconclusive'))

    def test_runtime_cleanup_unknown_is_preserved(self):
        with patch.object(review_native, 'NativeRunner', side_effect=BoundaryError('runtime_cleanup_unverified')):
            report, code = review_native.native_review(self.args, self.context)
        self.assertEqual(report['cleanup'], 'unverified')
        self.assertNotEqual(code, 0)
        retained = Path(report['retained_control'])
        self.assertTrue(retained.is_dir())
        import shutil
        self.addCleanup(shutil.rmtree, retained)

    def test_control_json_is_invisible_until_fully_written(self):
        destination = self.root / 'ready'
        dump = json.dump
        def before_flush(value, stream):
            self.assertFalse(destination.exists(), 'partial gate was published')
            dump(value, stream)
        with patch('review_macos.json.dump', side_effect=before_flush):
            private_json(destination, {'pid': 123})
        self.assertEqual(json.loads(destination.read_text()), {'pid': 123})

    def test_duplicate_control_fact_cannot_overwrite_first(self):
        destination = self.root / 'end'
        private_json(destination, {'first': True})
        with self.assertRaises(FileExistsError):
            private_json(destination, {'first': False})
        self.assertEqual(json.loads(destination.read_text()), {'first': True})
        self.assertEqual(list(self.root.glob('*.tmp.*')), [])

    def test_incomplete_membership_never_crosses_kill_barrier(self):
        kernel = Kernel.__new__(Kernel)
        kernel.members = Mock(return_value=[{'pid': 123, 'generation': 10, 'state': 4}])
        kernel.count = Mock(return_value=2)
        kernel.signal = Mock(return_value=0)
        with patch('review_macos.time.monotonic', side_effect=[0, 0, 4]), \
                patch('review_macos.time.sleep'), self.assertRaisesRegex(BoundaryError, 'cleanup_unverified'):
            kernel.clean(77)
        self.assertEqual([call.args[2] for call in kernel.signal.call_args_list], [signal.SIGSTOP])

    def test_signal_denial_stops_cleanup_without_claiming_success(self):
        kernel = Kernel.__new__(Kernel)
        kernel.members = Mock(return_value=[{'pid': 123, 'generation': 10, 'state': 2}])
        kernel.signal = Mock(return_value=errno.EPERM)
        with self.assertRaisesRegex(BoundaryError, 'process_stop_rejected'):
            kernel.clean(77)
        self.assertEqual(kernel.signal.call_count, 1)


if __name__ == '__main__':
    unittest.main()
