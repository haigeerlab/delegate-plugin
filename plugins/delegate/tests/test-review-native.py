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


AUTHENTICATION_VARIABLES = ('CLAUDE_CONFIG_DIR', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN',
    'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX',
    'CLAUDE_CODE_USE_FOUNDRY', 'ANTHROPIC_BASE_URL', 'DELEGATE_CLAUDE_GUEST_CONFIG')


class DesktopBaseUrl(unittest.TestCase):
    """Claude Desktop injects the official endpoint into every Code session."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.context = {'repository': str(self.root), 'files': {'src/a.py': b'fixture\n'},
            'allowed_tools': ['Read'], 'scope': {}, 'baseline': {}, 'diff_sha256': None,
            'file_sha256': {}, 'unreviewed': []}
        self.args = SimpleNamespace(model='sonnet', task='fixture', max_turns=12, max_budget_usd=None)

    def environment(self, base_url, extra=None):
        values = {name: '' for name in AUTHENTICATION_VARIABLES}
        values.update({'ANTHROPIC_BASE_URL': base_url, 'CLAUDE_CODE_ENTRYPOINT': 'claude-desktop',
                       'DELEGATE_REVIEW_DEPTH': '0'}, **(extra or {}))
        return patch.dict('os.environ', values)

    def review(self, base_url, extra=None):
        # The CLI lookup is the first step after the authentication check; a
        # sentinel there proves which side of the check was reached.
        with self.environment(base_url, extra), patch('sys.platform', 'darwin'), \
                patch.object(review_native, 'executable', side_effect=BoundaryError('claude_cli_missing')):
            report, _ = review_native.native_review(self.args, self.context)
        return report['diagnostics']

    def doctor(self, base_url):
        import contextlib, io, os, review_doctor
        output = io.StringIO()
        previous = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        with self.environment(base_url), patch('sys.platform', 'darwin'), \
                patch('sys.argv', ['review_doctor.py', '--backend', 'claude-code']), \
                patch.object(review_native, 'executable', side_effect=BoundaryError('claude_cli_missing')), \
                contextlib.redirect_stdout(output):
            review_doctor.main()
        return output.getvalue()

    def test_desktop_official_base_url_passes_review_authentication_check(self):
        self.assertEqual(self.review('https://api.anthropic.com'), ['claude_cli_missing'])

    def test_desktop_official_base_url_passes_doctor_authentication_check(self):
        output = self.doctor('https://api.anthropic.com')
        self.assertIn('条件不足：claude_cli_missing', output)
        self.assertNotIn('native_authentication_environment_unverified', output)

    def test_official_base_url_variants_pass(self):
        for value in ('https://api.anthropic.com', 'https://api.anthropic.com/',
                      'HTTPS://API.Anthropic.COM', 'https://api.anthropic.com:443/'):
            with self.subTest(value=value):
                self.assertEqual(self.review(value), ['claude_cli_missing'])

    def test_other_base_urls_stay_refused(self):
        for value in ('https://proxy.example.com', 'http://api.anthropic.com',
                      'https://api.anthropic.com.evil.example', 'https://evil.api.anthropic.com',
                      'https://api.anthropic.com./', 'https://api.anthropic.com/v1',
                      'https://api.anthropic.com//', 'https://api.anthropic.com:8443',
                      'https://api.anthropic.com:abc', 'https://user@api.anthropic.com',
                      'https://api.anthropic.com@evil.example', 'https://api.anthropic.com?',
                      'https://api.anthropic.com/?x=1', 'https://api.anthropic.com#',
                      ' https://api.anthropic.com', 'https://api.anthropic.com\n',
                      'api.anthropic.com', 'https://api.anthropic.com\\@evil.example'):
            with self.subTest(value=value):
                self.assertEqual(self.review(value), ['native_authentication_environment_unverified'])
                self.assertIn('条件不足：native_authentication_environment_unverified',
                              self.doctor(value))

    def test_other_authentication_variables_still_refused_with_official_base_url(self):
        for name in AUTHENTICATION_VARIABLES[:7]:
            with self.subTest(name=name):
                self.assertEqual(self.review('https://api.anthropic.com', {name: 'x'}),
                                 ['native_authentication_environment_unverified'])


if __name__ == '__main__':
    unittest.main()
