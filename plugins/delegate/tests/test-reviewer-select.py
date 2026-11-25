#!/usr/bin/env python3
"""Second-reviewer choice with injected availability checks (spec/reviewer-selection.md)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reviewer_select


class ChooseTests(unittest.TestCase):
    def test_vendor_table(self):
        self.assertEqual(reviewer_select.VENDORS, {'codex': 'openai', 'claude-code': 'anthropic'})

    def test_order_prefers_the_other_vendor(self):
        self.assertEqual(reviewer_select.order('claude-code'), ['codex', 'claude-code'])
        self.assertEqual(reviewer_select.order('codex'), ['claude-code', 'codex'])

    def test_author_claude_code(self):
        cases = [({'codex': True, 'claude-code': True}, 'codex', 'cross_vendor', ['codex']),
                 ({'codex': 'codex_not_logged_in', 'claude-code': True}, 'claude-code', 'same_vendor_fallback',
                  ['codex', 'claude-code']),
                 ({'codex': 'codex_not_logged_in', 'claude-code': 'claude_cli_missing'}, None, 'none',
                  ['codex', 'claude-code'])]
        for available, backend, selection, order in cases:
            with self.subTest(available=available):
                injected, calls = self.fixed(available)
                chosen, how, diagnostics = reviewer_select.choose('claude-code', injected)
                self.assertEqual((chosen, how), (backend, selection))
                self.assertEqual(calls, order, 'only the needed vendors are checked, in order')
                if backend is None:
                    self.assertEqual(diagnostics, ['codex_not_logged_in', 'claude_cli_missing'])

    def test_author_codex_is_symmetric(self):
        cases = [({'codex': True, 'claude-code': True}, 'claude-code', 'cross_vendor'),
                 ({'codex': True, 'claude-code': 'claude_cli_missing'}, 'codex', 'same_vendor_fallback'),
                 ({'codex': 'codex_not_logged_in', 'claude-code': 'claude_cli_missing'}, None, 'none')]
        for available, backend, selection in cases:
            with self.subTest(available=available):
                injected, _ = self.fixed(available)
                self.assertEqual(reviewer_select.choose('codex', injected)[:2], (backend, selection))

    def test_unknown_author_is_rejected(self):
        injected, _ = self.fixed({'codex': True, 'claude-code': True})
        with self.assertRaises(ValueError):
            reviewer_select.choose('other', injected)

    def test_check_codes_and_probe_stage_are_kept_in_order(self):
        # spec/claude-review.md CR-23: a probe failure carries its stage into the "unreviewed" report.
        injected, _ = self.fixed({'codex': 'codex_not_logged_in',
                                  'claude-code': ('probe_timed_out', 'probe_stage_help')})
        self.assertEqual(reviewer_select.choose('claude-code', injected),
                         (None, 'none', ['codex_not_logged_in', 'probe_timed_out', 'probe_stage_help']))

    def fixed(self, available):
        calls = []

        def make(name):
            def check():
                calls.append(name)
                value = available[name]
                return None if value is True else value
            return check
        return {name: make(name) for name in available}, calls


class ClaudeCheckTests(unittest.TestCase):
    """claude_check returns the probe stage after the main code (spec/claude-review.md CR-23)."""

    def check_with(self, error):
        from unittest import mock
        import claude_review
        import review_native

        class Runner:
            claude = '/opt/claude'

            def __init__(self, *args):
                pass

            def runtime_preflight(self):
                pass

            def invoke(self, *args, **kwargs):
                raise AssertionError('preflight is replaced in this test')

        def fail(*args):
            raise error
        with mock.patch.object(review_native, 'NativeRunner', Runner), \
                mock.patch.object(review_native, 'native_temporary', lambda *args: None), \
                mock.patch.object(claude_review, 'preflight', fail):
            return reviewer_select.claude_check()

    def test_probe_failure_returns_code_and_stage(self):
        import claude_review
        for code, stage in [('probe_timed_out', 'probe_stage_version'),
                            ('probe_cleanup_unverified', 'probe_stage_auth')]:
            with self.subTest(code=code):
                self.assertEqual(self.check_with(claude_review.PreflightError(code, stage=stage)), (code, stage))

    def test_judgement_failure_returns_code_only(self):
        import claude_review
        self.assertEqual(self.check_with(claude_review.PreflightError('authentication_missing')),
                         'authentication_missing')


class DescribeTests(unittest.TestCase):
    def test_selected_reviewer(self):
        self.assertEqual(reviewer_select.describe('codex', 'claude-code', 'cross_vendor'),
                         {'vendor': 'openai', 'backend': 'codex', 'same_vendor': False, 'selection': 'cross_vendor'})
        self.assertEqual(reviewer_select.describe('claude-code', 'claude-code', 'same_vendor_fallback'),
                         {'vendor': 'anthropic', 'backend': 'claude-code', 'same_vendor': True,
                          'selection': 'same_vendor_fallback'})

    def test_explicit_backend_with_and_without_author(self):
        self.assertEqual(reviewer_select.describe('codex', 'codex', 'explicit')['same_vendor'], True)
        self.assertEqual(reviewer_select.describe('codex', None, 'explicit'),
                         {'vendor': 'openai', 'backend': 'codex', 'same_vendor': None, 'selection': 'explicit'})

    def test_no_reviewer(self):
        self.assertEqual(reviewer_select.describe(None, 'codex', 'none'),
                         {'vendor': None, 'backend': None, 'same_vendor': None, 'selection': 'none'})



class RealChecksTests(unittest.TestCase):
    def test_fixture_override_only_when_the_variable_is_set(self):
        import os
        saved = os.environ.pop(reviewer_select.FIXTURE, None)
        try:
            real = reviewer_select.real_checks()
            self.assertIs(real['codex'], reviewer_select.codex_check)
            self.assertIs(real['claude-code'], reviewer_select.claude_check)
            os.environ[reviewer_select.FIXTURE] = '{"codex": null}'
            pinned = reviewer_select.real_checks()
            self.assertIsNone(pinned['codex']())
            self.assertEqual(pinned['claude-code'](), 'fixture_unavailable')
        finally:
            os.environ.pop(reviewer_select.FIXTURE, None)
            if saved is not None:
                os.environ[reviewer_select.FIXTURE] = saved


if __name__ == '__main__':
    unittest.main()
