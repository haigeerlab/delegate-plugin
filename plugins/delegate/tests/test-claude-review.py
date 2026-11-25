#!/usr/bin/env python3
"""Claude preflight faults using an isolated-invocation fake; no host auth."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import claude_review


class FakeBoundary:
    def __init__(self, version=b'2.1.295 (Claude Code)', help_text=None, auth=None):
        self.calls = []
        self.version = version
        self.help_text = help_text if help_text is not None else ' '.join(claude_review.VISIBLE_FLAGS).encode()
        self.auth = auth if auth is not None else json.dumps({'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty', 'email': 'SECRET_EMAIL', 'apiKey': 'SECRET_KEY'}).encode()
        self.fault = None

    def __call__(self, argv, *, deadline):
        self.calls.append((argv, deadline))
        if self.fault:
            return self.fault
        suffix = argv[-1:]
        data = self.version if suffix == ['--version'] else self.help_text if suffix == ['--help'] else self.auth
        return {'execution_status': 'completed', 'cleanup': 'confirmed', 'stdout': data, 'diagnostics': []}


class ClaudePreflightTests(unittest.TestCase):
    def run_probe(self, boundary):
        return claude_review.preflight('/opt/claude', boundary)

    def test_only_safe_auth_fields_are_returned(self):
        boundary = FakeBoundary()
        result = self.run_probe(boundary)
        self.assertEqual(result, {'version': '2.1.295', 'auth_method': 'claude.ai', 'provider': 'firstParty'})
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual([call[0][-1] for call in boundary.calls], ['--version', '--help', '--json'])
        self.assertTrue(all(call[1] == 5 for call in boundary.calls))
        self.assertTrue(all('--safe-mode' in call[0] and '--restricted' in call[0] for call in boundary.calls))
        self.assertTrue(all('-p' not in call[0] for call in boundary.calls))

    def test_old_unknown_and_invalid_utf8_versions_fail_closed(self):
        for version in (b'2.1.294', b'unknown SECRET_KEY', b'2.1.295-preview', b'\xff'):
            with self.subTest(version=version), self.assertRaisesRegex(claude_review.PreflightError, 'cli_version_unsupported'):
                self.run_probe(FakeBoundary(version=version))

    def test_visible_required_capability_missing_is_conditions_missing(self):
        with self.assertRaisesRegex(claude_review.PreflightError, 'cli_capability_missing'):
            self.run_probe(FakeBoundary(help_text=b'--print --tools'))

    def test_bad_empty_duplicate_and_wrong_type_auth_are_not_authenticated(self):
        values = [b'', b'not JSON SECRET_KEY', b'{}', b'{"loggedIn":true,"loggedIn":false}',
                  b'{"loggedIn":"true","authMethod":"claude.ai","apiProvider":"firstParty"}',
                  b'{"loggedIn":true,"authMethod":"none","apiProvider":"firstParty"}']
        for auth in values:
            with self.subTest(auth=auth), self.assertRaises(claude_review.PreflightError) as caught:
                self.run_probe(FakeBoundary(auth=auth))
            self.assertNotIn('SECRET', str(caught.exception))

    def test_logged_out_and_unknown_provider_are_separate_conditions(self):
        for data, code in [({'loggedIn': False}, 'authentication_missing'),
                           ({'loggedIn': True, 'authMethod': 'third_party', 'apiProvider': 'bedrock'}, 'provider_unverified'),
                           ({'loggedIn': True, 'authMethod': 'api_key_helper', 'apiProvider': 'firstParty'}, 'authentication_method_unverified')]:
            with self.subTest(code=code), self.assertRaisesRegex(claude_review.PreflightError, code):
                self.run_probe(FakeBoundary(auth=json.dumps(data).encode()))

    def test_timeout_cancel_error_overflow_and_unknown_cleanup_are_not_success(self):
        for state, cleanup, output, code in [('timed_out', 'confirmed', b'', 'probe_timed_out'),
                ('cancelled', 'confirmed', b'', 'probe_cancelled'),
                ('failed', 'confirmed', b'SECRET_KEY', 'probe_failed'),
                ('completed', 'unverified', b'2.1.295', 'probe_cleanup_unverified'),
                ('completed', 'confirmed', b'a' * 65537, 'probe_output_invalid')]:
            boundary = FakeBoundary()
            boundary.fault = {'execution_status': state, 'cleanup': cleanup, 'stdout': output, 'diagnostics': ['SECRET_KEY']}
            with self.subTest(code=code), self.assertRaisesRegex(claude_review.PreflightError, code):
                self.run_probe(boundary)

    def test_probe_failure_reports_append_stage_without_changing_execution(self):
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        context = {'files': {}, 'scope': {}, 'baseline': {}, 'diff_sha256': '',
                   'file_sha256': {}, 'unreviewed': []}
        stages = [('--version', 'probe_stage_version'), ('--help', 'probe_stage_help'),
                  ('--json', 'probe_stage_auth')]
        faults = [('timed_out', 'confirmed', 'probe_timed_out', 'timed_out'),
                  ('failed', 'confirmed', 'probe_failed', 'conditions_missing'),
                  ('cancelled', 'confirmed', 'probe_cancelled', 'cancelled'),
                  ('completed', 'unverified', 'probe_cleanup_unverified', 'conditions_missing'),
                  ('unavailable', 'unverified', 'probe_unavailable', 'conditions_missing')]
        for index, (suffix, stage) in enumerate(stages):
            for state, cleanup, code, expected_state in faults:
                with self.subTest(stage=stage, code=code):
                    boundary = FakeBoundary()
                    def invoke(argv, *, deadline):
                        if argv[-1] == suffix:
                            boundary.calls.append((argv, deadline))
                            if state == 'unavailable':
                                raise OSError('SECRET_KEY')
                            return {'execution_status': state, 'cleanup': cleanup, 'stdout': b''}
                        return boundary(argv, deadline=deadline)
                    report = claude_review.execute('/opt/claude', args, context, invoke, timeout=30)
                    self.assertEqual(report['diagnostics'], [code, stage])
                    self.assertEqual(report['execution_status'], expected_state)
                    self.assertFalse(report['backend_started'])
                    self.assertEqual(report['cleanup'], cleanup)
                    self.assertEqual([argv[-1] for argv, _ in boundary.calls],
                                     [item[0] for item in stages[:index + 1]])
                    self.assertTrue(all('-p' not in argv for argv, _ in boundary.calls))

    def test_oversized_probe_output_reports_stage(self):
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        context = {'files': {}, 'scope': {}, 'baseline': {}, 'diff_sha256': '',
                   'file_sha256': {}, 'unreviewed': []}
        cases = [(FakeBoundary(version=b'a' * 65537), 'probe_stage_version'),
                 (FakeBoundary(help_text=b'a' * 65537), 'probe_stage_help'),
                 (FakeBoundary(auth=b'a' * 65537), 'probe_stage_auth')]
        for boundary, stage in cases:
            with self.subTest(stage=stage):
                report = claude_review.execute('/opt/claude', args, context, boundary, timeout=30)
                self.assertEqual(report['diagnostics'], ['probe_output_invalid', stage])
                self.assertEqual(report['execution_status'], 'conditions_missing')
                self.assertFalse(report['backend_started'])

    def test_non_probe_failure_reports_do_not_include_stage(self):
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        context = {'files': {}, 'scope': {}, 'baseline': {}, 'diff_sha256': '',
                   'file_sha256': {}, 'unreviewed': []}
        cases = [(FakeBoundary(version=b'2.1.294'), 'cli_version_unsupported'),
                 (FakeBoundary(help_text=b'--tools'), 'cli_capability_missing'),
                 (FakeBoundary(auth=b'not JSON'), 'authentication_output_invalid'),
                 (FakeBoundary(auth=b'{"loggedIn":false}'), 'authentication_missing'),
                 (FakeBoundary(auth=b'{"loggedIn":true,"authMethod":"none","apiProvider":"firstParty"}'),
                  'authentication_method_unverified'),
                 (FakeBoundary(auth=b'{"loggedIn":true,"authMethod":"third_party","apiProvider":"bedrock"}'),
                  'provider_unverified')]
        for boundary, code in cases:
            with self.subTest(code=code):
                report = claude_review.execute('/opt/claude', args, context, boundary, timeout=30)
                self.assertEqual(report['diagnostics'], [code])
                self.assertFalse(any(item.startswith('probe_stage_') for item in report['diagnostics']))
                self.assertEqual(report['execution_status'], 'conditions_missing')
                self.assertFalse(report['backend_started'])
                self.assertEqual(report['cleanup'], 'confirmed')

    def test_executable_must_be_trusted_absolute_and_no_raw_error_escapes(self):
        for name in ('claude', '/opt/../claude', '/opt/claude\0'):
            with self.subTest(name=name), self.assertRaises(claude_review.PreflightError):
                claude_review.preflight(name, FakeBoundary())
        def unavailable(*_, **__):
            raise OSError('SECRET_KEY')
        with self.assertRaisesRegex(claude_review.PreflightError, '^probe_unavailable$'):
            claude_review.preflight('/opt/claude', unavailable)
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        context = {'files': {}, 'scope': {}, 'baseline': {}, 'diff_sha256': '',
                   'file_sha256': {}, 'unreviewed': []}
        report = claude_review.execute('/opt/claude', args, context, unavailable, timeout=30)
        self.assertEqual(report['cleanup'], 'unverified')
        self.assertFalse(report['backend_started'])

    def launch_prompt(self, context):
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='TASK-MARKER')
        boundary, prompts = FakeBoundary(), []
        def invoke(argv, *, deadline, stdin=None):
            if '-p' not in argv:
                return boundary(argv, deadline=deadline)
            prompts.append(stdin.decode('utf-8'))
            return {'execution_status': 'failed', 'cleanup': 'confirmed', 'diagnostics': [], 'stdout': b''}
        claude_review.execute('/opt/claude', args, context, invoke, timeout=30)
        return prompts[0]

    def test_claude_prompt_explains_context_files_before_task(self):
        from review_context import CONTEXT_FILES_INSTRUCTION
        context = {'files': {'src/a.py': b'first\n'}, 'unreviewed': [], 'scope': {'include': ['src/a.py'], 'exclude': []},
                   'baseline': {'mode': 'commits'}, 'diff_sha256': 'a' * 64, 'file_sha256': {'src/a.py': 'b' * 64},
                   'allowed_tools': ['Read']}
        prompt = self.launch_prompt(dict(context, context_files=['src/a.py']))
        self.assertLess(prompt.index(CONTEXT_FILES_INSTRUCTION), prompt.index('Task: TASK-MARKER'))
        self.assertNotIn(CONTEXT_FILES_INSTRUCTION, self.launch_prompt(dict(context, context_files=[])))

    def test_claude_prompt_uses_design_criteria_for_design_profile(self):
        from review_context import DESIGN_CRITERIA, SEVERITY_CRITERIA
        context = {'files': {'src/a.py': b'first\n'}, 'unreviewed': [], 'scope': {'include': ['src/a.py'], 'exclude': []},
                   'baseline': {'mode': 'commits'}, 'diff_sha256': 'a' * 64, 'file_sha256': {'src/a.py': 'b' * 64},
                   'allowed_tools': ['Read'], 'profile': 'design'}
        prompt = self.launch_prompt(context)
        self.assertLess(prompt.index(DESIGN_CRITERIA), prompt.index('Task: TASK-MARKER'))
        self.assertNotIn(SEVERITY_CRITERIA, prompt)

    def test_review_launch_uses_claude_restrictions_and_common_task_data(self):
        from review_result import schema_for_context
        context = {'files': {'src/a.py': b'first\n'}, 'unreviewed': [],
            'scope': {'include': ['src/a.py'], 'exclude': []}, 'baseline': {'mode': 'commits'},
            'diff_sha256': 'a' * 64, 'file_sha256': {'src/a.py': 'b' * 64}, 'allowed_tools': ['Read']}
        args = SimpleNamespace(model='sonnet', max_turns=12, max_budget_usd='1.50', task='review fixture')
        boundary = FakeBoundary()
        launches = []
        def invoke(argv, *, deadline, stdin=None):
            if '-p' not in argv:
                return boundary(argv, deadline=deadline)
            launches.append((argv, deadline, stdin))
            events = [{'type': 'system', 'subtype': 'init', 'tools': ['Read'], 'mcp_servers': [], 'model': 'claude-sonnet-fixture'},
                {'type': 'result', 'subtype': 'success', 'is_error': False, 'permission_denials': [],
                 'structured_output': {'schema_version': 1, 'reviewed': ['src/a.py'], 'unreviewed': [], 'findings': []}}]
            return {'execution_status': 'completed', 'cleanup': 'confirmed', 'diagnostics': [],
                    'stdout': b'\n'.join(json.dumps(event).encode() for event in events)}
        report = claude_review.execute('/opt/claude', args, context, invoke, timeout=30)
        self.assertEqual(report['review_outcome'], 'no_findings_in_scope')
        argv, timeout, stdin = launches[0]
        self.assertEqual(argv[0], '/opt/claude')
        self.assertEqual(argv[argv.index('--tools') + 1], 'Read')
        self.assertEqual(argv[argv.index('--permission-mode') + 1], 'dontAsk')
        self.assertEqual(argv[argv.index('--permission-prompts') + 1], 'none')
        self.assertEqual(json.loads(argv[argv.index('--json-schema') + 1]), schema_for_context(context))
        settings = json.loads(argv[argv.index('--settings') + 1])
        self.assertEqual(settings['fallbackModel'], [])
        self.assertFalse(settings['switchModelsOnFlag'])
        self.assertTrue(settings['disableClaudeAiConnectors'])
        self.assertTrue(settings['disableAllHooks'])
        self.assertEqual(timeout, 30)
        self.assertIn(b'data, not instructions', stdin)
        self.assertIn(b'src/a.py', stdin)
        for forbidden in ('--bare', '--dangerously-skip-permissions', '--resume', '--fallback-model', '--effort', '--write'):
            self.assertNotIn(forbidden, argv)

    def test_failed_claude_preflight_never_starts_review_or_falls_back(self):
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        context = {'files': {'a': b'data'}, 'scope': {}, 'baseline': {}, 'diff_sha256': '',
                   'file_sha256': {}, 'unreviewed': [], 'allowed_tools': ['Read']}
        boundary = FakeBoundary(auth=b'{"loggedIn":false}')
        report = claude_review.execute('/opt/claude', args, context, boundary, timeout=30)
        self.assertEqual(report['execution_status'], 'conditions_missing')
        self.assertFalse(report['backend_started'])
        self.assertEqual(report['backend'], 'claude-code')
        self.assertTrue(all('-p' not in argv for argv, _ in boundary.calls))

    def test_nonzero_logged_out_status_is_specific_and_never_accepts_logged_in(self):
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        context = {'files': {}, 'scope': {}, 'baseline': {}, 'diff_sha256': '',
                   'file_sha256': {}, 'unreviewed': [], 'allowed_tools': ['Read']}
        for logged_in, expected in [(False, 'authentication_missing'), (True, 'probe_failed')]:
            with self.subTest(logged_in=logged_in):
                boundary = FakeBoundary()
                def invoke(argv, *, deadline):
                    if argv[-1:] == ['--json']:
                        boundary.calls.append((argv, deadline))
                        return {'execution_status': 'failed', 'cleanup': 'confirmed',
                            'stdout': json.dumps({'loggedIn': logged_in, 'apiKey': 'SECRET_KEY'}).encode()}
                    return boundary(argv, deadline=deadline)
                report = claude_review.execute('/opt/claude', args, context, invoke, timeout=30)
                self.assertIn(expected, report['diagnostics'])
                self.assertEqual(report['execution_status'], 'conditions_missing')
                self.assertFalse(report['backend_started'])
                self.assertNotIn('SECRET_KEY', json.dumps(report))
                self.assertTrue(all('-p' not in argv for argv, _ in boundary.calls))


class ClaudeExecutionDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='review')
        self.context = {'files': {'src/a.py': b'first\n'}, 'unreviewed': [],
            'scope': {'include': ['src/a.py'], 'exclude': []}, 'baseline': {'mode': 'commits'},
            'diff_sha256': 'a' * 64, 'file_sha256': {'src/a.py': 'b' * 64}, 'allowed_tools': ['Read']}
        events = [{'type': 'system', 'subtype': 'init', 'tools': ['Read'], 'mcp_servers': [],
                   'model': 'claude-sonnet-fixture'},
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'permission_denials': [],
             'structured_output': {'schema_version': 1, 'reviewed': ['src/a.py'],
                                   'unreviewed': [], 'findings': []}}]
        self.stream = b'\n'.join(json.dumps(event).encode() for event in events)

    def run_execution(self, execution):
        boundary = FakeBoundary()
        def invoke(argv, *, deadline, stdin=None):
            if '-p' not in argv:
                return boundary(argv, deadline=deadline)
            if isinstance(execution, OSError):
                raise execution
            return execution
        report = claude_review.execute('/opt/claude', self.args, self.context, invoke, timeout=30)
        serialized = json.dumps(report)
        for field in ('stdout_bytes', 'stderr_bytes', 'launcher_exit_code', 'stdout_check'):
            self.assertNotIn('"' + field + '"', serialized)
        self.assertNotIn('SECRET_STDERR', serialized)
        for value in ('13579', '24680'):
            self.assertNotIn(value, serialized)
        return report

    def test_stdout_checks_append_specific_codes_and_preserve_empty_stream_diagnostic(self):
        for check, code in [('missing', 'stream_file_missing'), ('short', 'stream_read_short'),
                            ('ok', None), (None, None)]:
            with self.subTest(check=check):
                execution = {'execution_status': 'failed', 'cleanup': 'confirmed', 'stdout': b''}
                if check is not None:
                    execution['stdout_check'] = check
                report = self.run_execution(execution)
                expected = ['stream_empty_or_oversized'] + ([code] if code else [])
                self.assertEqual(report['diagnostics'], expected)
                self.assertEqual(report['execution_status'], 'failed')
                self.assertEqual(report['review_outcome'], 'inconclusive')

    def test_incomplete_reviews_append_backend_exit_and_stderr_codes(self):
        # A stopped (timed out or cancelled) backend exits nonzero because we
        # reaped it, so only a failed review reports backend_exit_nonzero.
        expected = {'failed': ['stream_empty_or_oversized', 'backend_exit_nonzero', 'backend_stderr_nonempty'],
                    'timed_out': ['stream_empty_or_oversized', 'backend_stderr_nonempty'],
                    'cancelled': ['stream_empty_or_oversized', 'backend_stderr_nonempty']}
        for state in ('failed', 'timed_out', 'cancelled'):
            with self.subTest(state=state):
                report = self.run_execution({'execution_status': state, 'cleanup': 'confirmed',
                    'stdout': b'', 'stdout_bytes': 13579, 'stderr_bytes': 24680,
                    'launcher_exit_code': -7, 'stderr': b'SECRET_STDERR'})
                self.assertEqual(report['diagnostics'], expected[state])
                self.assertEqual(report['execution_status'], state)
                self.assertEqual(report['review_outcome'], 'inconclusive')

    def test_zero_missing_and_noninteger_metadata_add_no_backend_codes(self):
        values = [{}, {'launcher_exit_code': 0, 'stderr_bytes': 0},
                  {'launcher_exit_code': True, 'stderr_bytes': True},
                  {'launcher_exit_code': '7', 'stderr_bytes': '9'},
                  {'launcher_exit_code': 7.0, 'stderr_bytes': 9.0},
                  {'launcher_exit_code': None, 'stderr_bytes': -1}]
        for metadata in values:
            with self.subTest(metadata=metadata):
                report = self.run_execution(dict(metadata, execution_status='failed',
                    cleanup='confirmed', stdout=b''))
                self.assertEqual(report['diagnostics'], ['stream_empty_or_oversized'])

    def test_completed_review_with_stderr_keeps_success_without_backend_codes(self):
        report = self.run_execution({'execution_status': 'completed', 'cleanup': 'confirmed',
            'stdout': self.stream, 'stdout_check': 'ok', 'stdout_bytes': len(self.stream),
            'stderr_bytes': 24680, 'launcher_exit_code': 7, 'stderr': b'SECRET_STDERR'})
        self.assertEqual(report['diagnostics'], [])
        self.assertEqual(report['execution_status'], 'completed')
        self.assertEqual(report['review_outcome'], 'no_findings_in_scope')

    def test_failed_report_after_completed_execution_gets_backend_codes(self):
        report = self.run_execution({'execution_status': 'completed', 'cleanup': 'confirmed',
            'stdout': b'', 'stderr_bytes': 9, 'launcher_exit_code': 7})
        self.assertEqual(report['execution_status'], 'failed')
        self.assertEqual(report['diagnostics'], ['stream_empty_or_oversized',
            'backend_exit_nonzero', 'backend_stderr_nonempty'])

    def test_existing_execution_diagnostic_codes_are_not_duplicated(self):
        for check, code in [('missing', 'stream_file_missing'), ('short', 'stream_read_short')]:
            with self.subTest(check=check):
                codes = [code, 'backend_exit_nonzero', 'backend_stderr_nonempty']
                report = self.run_execution({'execution_status': 'failed', 'cleanup': 'confirmed',
                    'stdout': b'', 'stdout_check': check, 'launcher_exit_code': 7,
                    'stderr_bytes': 9, 'diagnostics': codes})
                self.assertEqual(report['diagnostics'], codes + ['stream_empty_or_oversized'])

    def test_execution_oserror_preserves_existing_failure_diagnostics(self):
        report = self.run_execution(OSError('SECRET_STDERR'))
        self.assertEqual(report['diagnostics'], ['claude_execution_unavailable',
                                                'stream_empty_or_oversized'])
        self.assertEqual(report['execution_status'], 'failed')
        self.assertEqual(report['review_outcome'], 'inconclusive')
        self.assertEqual(report['cleanup'], 'unverified')


if __name__ == '__main__':
    unittest.main()
