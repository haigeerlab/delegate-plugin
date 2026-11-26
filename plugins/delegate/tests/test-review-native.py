#!/usr/bin/env python3
"""Offline native routing/error contracts; no Darwin jobs or real executors."""
import errno
import hashlib
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
        for name in ('review_macos.py', 'review_init.py', 'claude_review.py'):
            staged = anchor.parent / name
            self.assertEqual(staged.read_bytes(), (SCRIPTS / name).read_bytes())
            self.assertEqual(staged.stat().st_mode & 0o777, 0o600)
        self.assertFalse((anchor.parent / 'review_result.py').exists())

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


class SandboxTrustTests(unittest.TestCase):
    """S88: explicitly trusted certificates are added read-only for the sandboxed CLI."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.bin = self.base / 'bin'; self.bin.mkdir()
        for name in ('claude', 'srt', 'node'):
            (self.bin / name).write_text('#!/bin/sh\n'); (self.bin / name).chmod(0o755)
        self.repository = self.base / 'repository'; self.repository.mkdir()
        self.context = {'repository': str(self.repository), 'files': {'src/a.py': b'fixture\n'},
            'file_sha256': {'src/a.py': hashlib.sha256(b'fixture\n').hexdigest()}, 'allowed_tools': ['Read']}
        self.caller_ca = self.base / 'caller-ca.pem'; self.caller_ca.write_text('PRIVATE_CALLER_CA')

    def runner(self, trust):
        root = self.base / ('run%d' % len(list(self.base.glob('run*')))); root.mkdir(mode=0o700)
        def export(directory, **_):
            if isinstance(trust, Exception):
                raise trust
            directory.mkdir(mode=0o700)
            path = directory / 'trusted.pem'; path.write_text('PRIVATE_PEM'); path.chmod(0o400)
            return {'count': trust, 'path': str(path)} if trust else {'count': 0, 'path': None}
        values = {name: '' for name in AUTHENTICATION_VARIABLES}
        values['NODE_EXTRA_CA_CERTS'] = str(self.caller_ca)
        with patch.dict('os.environ', values), patch('sys.platform', 'darwin'), \
                patch.object(review_native, 'executable', side_effect=lambda name, _: self.bin / name), \
                patch.object(review_native, 'export_trusted', side_effect=export):
            return review_native.NativeRunner(root, self.context)

    def test_exported_file_is_readable_not_writable_and_hidden_from_review_tools(self):
        runner = self.runner(3)
        path = str(runner.root / 'trust' / 'trusted.pem')
        self.assertEqual(runner.environment.get('NODE_EXTRA_CA_CERTS'), path)
        policy = json.loads(runner.policy.read_text())['filesystem']
        self.assertIn(path, json.dumps(policy['allowRead']))
        self.assertNotIn('trust', json.dumps(policy['allowWrite']))
        self.assertIn('Read(/%s)' % path, runner.tool_denials)
        self.assertEqual(runner.trust_diagnostics, [])
        self.assertEqual(runner.trust_count, 3)
        self.assertNotIn(str(self.caller_ca), json.dumps([runner.environment, policy]))

    def test_nothing_trusted_or_failed_export_adds_no_trust_or_caller_file(self):
        for trust, diagnostics in ((0, []), (review_native.TrustExportError('system_trust_export_unavailable'),
                ['system_trust_export_unavailable'])):
            with self.subTest(trust=trust):
                runner = self.runner(trust)
                self.assertNotIn('NODE_EXTRA_CA_CERTS', runner.environment)
                self.assertEqual(runner.trust_diagnostics, diagnostics)
                self.assertNotIn(str(self.caller_ca), runner.policy.read_text())

    def test_failed_export_is_a_non_fatal_report_diagnostic(self):
        runner = SimpleNamespace(claude=Path('/fixture/claude'), invoke=None, cancelled=None,
            runtime_preflight=lambda: None, trust_diagnostics=['system_trust_export_unavailable'])
        expected = {'execution_status': 'completed', 'diagnostics': [], 'cleanup': 'confirmed'}
        context = dict(self.context, scope={}, baseline={}, diff_sha256=None, file_sha256={}, unreviewed=[])
        args = SimpleNamespace(model=None, task='fixture', max_turns=12, max_budget_usd=None)
        with patch.object(review_native, 'NativeRunner', return_value=runner), \
                patch.object(review_native, 'native_temporary', return_value=self.base), \
                patch.object(review_native, 'execute', return_value=expected), \
                patch.object(review_native.shutil, 'rmtree'):
            report, status = review_native.native_review(args, context)
        self.assertEqual(status, 0)
        self.assertEqual(report['execution_status'], 'completed')
        self.assertEqual(report['diagnostics'], ['system_trust_export_unavailable'])

    def test_doctor_reports_only_the_certificate_count(self):
        import contextlib, io, os, review_doctor
        for trust, line in ((3, '系统明确信任的证书：3 张，已加入沙箱'),
                (review_native.TrustExportError('system_trust_export_unavailable'),
                 '系统证书导出：system_trust_export_unavailable（不影响运行，沙箱只用 CLI 自带的公共根证书）')):
            with self.subTest(trust=trust):
                runner = self.runner(trust)
                runner.runtime_preflight = lambda: None
                output = io.StringIO()
                previous = os.getcwd(); os.chdir(self.repository)
                try:
                    with patch('sys.argv', ['review_doctor.py', '--backend', 'claude-code']), \
                            patch.object(review_doctor, 'NativeRunner', return_value=runner), \
                            patch.object(review_doctor, 'preflight', return_value={'version': '2.1.311',
                                'auth_method': 'claude.ai', 'provider': 'firstParty'}), \
                            patch.dict('os.environ', {'DELEGATE_REVIEW_DEPTH': '0'}), \
                            contextlib.redirect_stdout(output):
                        review_doctor.main()
                finally:
                    os.chdir(previous)
                self.assertIn(line, output.getvalue())
                self.assertNotIn('PRIVATE_', output.getvalue())
                self.assertNotIn('trusted.pem', output.getvalue())
                note = ('已登录只说明本机存有凭据，不代表登录令牌仍然有效；审查若报 claude_api_authentication_failed，'
                        '请在沙箱外的终端运行一次 `claude`（例如 claude -p "ok"）刷新登录后重试；'
                        '仍失败时运行 claude /login 重新登录。')
                lines = output.getvalue().splitlines()
                auth_index = lines.index('认证方式：claude.ai；提供者：firstParty')
                self.assertEqual(lines[auth_index + 1], note)
                self.assertEqual(lines.count(note), 1)

    def test_reviewers_text_and_json_do_not_include_login_refresh_note(self):
        import contextlib, io, review_doctor
        expected = {'schema': 'delegate.reviewers/v1', 'reviewers': [
            {'backend': 'codex', 'vendor': 'openai', 'available': True, 'diagnostic': None},
            {'backend': 'claude-code', 'vendor': 'anthropic', 'available': True, 'diagnostic': None}], 'hint': None}
        for json_output in (False, True):
            with self.subTest(json_output=json_output):
                output = io.StringIO()
                args = ['review_doctor.py', '--reviewers'] + (['--json'] if json_output else [])
                with patch('sys.argv', args), \
                        patch('reviewer_select.real_checks', return_value={'codex': lambda: None, 'claude-code': lambda: None}), \
                        patch.dict('os.environ', {'DELEGATE_REVIEW_DEPTH': '0'}), \
                        patch.object(review_doctor, 'preflight') as preflight, \
                        contextlib.redirect_stdout(output):
                    self.assertEqual(review_doctor.main(), 0)
                preflight.assert_not_called()
                self.assertNotIn('已登录只说明', output.getvalue())
                self.assertNotIn('claude_login_refresh_required', output.getvalue())
                self.assertNotIn('claude /login', output.getvalue())
                if json_output:
                    self.assertEqual(json.loads(output.getvalue()), expected)
                else:
                    self.assertEqual(output.getvalue(), 'delegate: 第二审查者（无模型检查，不发请求）\n'
                        'codex（openai）：可用\nclaude-code（anthropic）：可用\n'
                        '不阻止任何操作；模型、额度与真实审查未验证。\n')


if __name__ == '__main__':
    unittest.main()
