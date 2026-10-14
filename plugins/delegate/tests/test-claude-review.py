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


if __name__ == '__main__':
    unittest.main()
