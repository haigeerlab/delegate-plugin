#!/usr/bin/env python3
"""Review findings and execution status are independent, with fixed evidence."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_result


class ResultTests(unittest.TestCase):
    def setUp(self):
        self.context = {'files': {'src/a.py': b'first\nsecond\n'}, 'unreviewed': [], 'scope': {'include': ['src/a.py'], 'exclude': []},
                        'allowed_tools': ['Read', 'Glob', 'Grep'], 'baseline': {'mode': 'commits', 'from': 'a', 'to': 'b'},
                        'diff_sha256': 'f' * 64, 'file_sha256': {'src/a.py': 'e' * 64}}
        self.content = {'schema_version': 1, 'reviewed': ['src/a.py'], 'unreviewed': [], 'findings': []}
        self.terminal = {'type': 'result', 'subtype': 'success', 'is_error': False, 'structured_output': self.content,
                         'permission_denials': [], 'modelUsage': {'claude-fixture': {'inputTokens': 4, 'outputTokens': 2}}, 'total_cost_usd': 0.01}
        self.init = {'type': 'system', 'subtype': 'init', 'tools': ['Read', 'Glob', 'Grep'], 'model': 'claude-fixture', 'mcp_servers': []}
        self.execution = {'execution_status': 'completed', 'cleanup': 'confirmed', 'diagnostics': []}

    def stream(self, *events):
        return b'\n'.join(json.dumps(value).encode() for value in events) + b'\n'

    def report(self, stream=None, execution=None):
        return review_result.claude_report(self.stream(self.init, self.terminal) if stream is None else stream,
                execution or self.execution, self.context, requested_model='sonnet')

    def test_complete_scope_without_findings_and_backend_metadata(self):
        result = self.report()
        self.assertEqual(result['execution_status'], 'completed')
        self.assertEqual(result['review_outcome'], 'no_findings_in_scope')
        self.assertEqual(result['backend'], 'claude-code')
        self.assertEqual(result['host'], 'unknown')
        self.assertEqual(result['observed_models'], ['claude-fixture'])
        self.assertEqual(result['requested_model'], 'sonnet')
        self.assertEqual(result['usage']['estimated_cost_usd'], .01)
        self.assertEqual(result['unreviewed'], [])

    def test_finding_is_not_an_execution_failure_or_merge_authorization(self):
        self.content['findings'] = [{'title': 'Regression', 'file': 'src/a.py', 'line': 2, 'trigger': 'specific input',
            'impact': 'wrong output', 'evidence': 'second', 'suggestion': 'validate input', 'unverified': ['runtime not tested']}]
        result = self.report()
        self.assertEqual(result['review_outcome'], 'findings')
        self.assertEqual(result['execution_status'], 'completed')
        self.assertTrue(result['findings'][0]['location_verified'])
        self.assertIn('does not authorize', review_result.render(result))

    def test_wrong_file_or_line_is_marked_unverified_and_inconclusive(self):
        for filename, line in [('src/a.py', 20), ('secret', 1)]:
            self.content['findings'] = [{'title': 'Claim', 'file': filename, 'line': line, 'trigger': 'input',
                'impact': 'effect', 'evidence': 'claim', 'suggestion': 'check', 'unverified': []}]
            result = self.report()
            self.assertEqual(result['review_outcome'], 'inconclusive')
            self.assertFalse(result['findings'][0]['location_verified'])
            self.assertIsNone(result['findings'][0]['line'])

    def test_partial_coverage_permission_denial_and_omitted_snapshot_are_inconclusive(self):
        self.content['reviewed'] = []
        result = self.report()
        self.assertEqual(result['review_outcome'], 'inconclusive')
        self.assertEqual(result['unreviewed'], [{'path': 'src/a.py', 'reason': 'coverage_not_reported'}])
        self.content['reviewed'] = ['src/a.py']
        self.terminal['permission_denials'] = [{'tool_name': 'Read', 'tool_input': {'secret': 'SECRET_KEY'}}]
        result = self.report()
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['review_outcome'], 'inconclusive')
        self.assertIn('permission_denied', result['diagnostics'])
        self.assertNotIn('SECRET_KEY', json.dumps(result))
        self.context['unreviewed'] = [{'path': 'src/b', 'reason': 'binary_or_non_utf8'}]
        result = self.report()
        self.assertIn({'path': 'src/b', 'reason': 'binary_or_non_utf8'}, result['unreviewed'])

    def test_empty_malformed_missing_duplicate_or_error_terminal_never_means_no_findings(self):
        error = dict(self.terminal, subtype='error_max_turns', is_error=True, errors=['SECRET_KEY'])
        for stream in (b'', b'bad SECRET_KEY', self.stream(self.init), self.stream(self.terminal),
                self.stream(self.init, self.terminal, self.terminal), self.stream(self.init, error),
                self.stream(self.init, dict(self.terminal, structured_output={})),
                self.stream(self.init, dict(self.terminal, is_error='false'))):
            with self.subTest(stream=stream[:30]):
                result = self.report(stream)
                self.assertEqual(result['execution_status'], 'failed')
                self.assertEqual(result['review_outcome'], 'inconclusive')
                self.assertNotIn('SECRET_KEY', json.dumps(result))

    def test_tool_or_mcp_expansion_fails_closed(self):
        for init in (dict(self.init, tools=['Read', 'Bash']), dict(self.init, mcp_servers=[{'name': 'other'}]),
                dict(self.init, tools=['Read', 'Glob', 'Grep', 'Agent'])):
            result = self.report(self.stream(init, self.terminal))
            self.assertEqual(result['execution_status'], 'failed')
            self.assertIn('tool_boundary_unverified', result['diagnostics'])

    def test_documented_end_conversation_and_schema_tool_do_not_expand_read_access(self):
        init = dict(self.init, tools=self.init['tools'] + ['EndConversation', 'StructuredOutput'])
        result = self.report(self.stream(init, self.terminal))
        self.assertEqual(result['execution_status'], 'completed')
        self.assertEqual(result['review_outcome'], 'no_findings_in_scope')
        # Ending without the terminal review never means scope was reviewed.
        result = self.report(self.stream(init))
        self.assertEqual(result['review_outcome'], 'inconclusive')
        self.assertIn('terminal_result_missing_or_duplicate', result['diagnostics'])

    def test_initial_boundary_reasons_are_fixed_codes_without_untrusted_content(self):
        cases = [(None, 'initial_event_not_init'),
            (dict(self.init, subtype='PRIVATE_STARTUP_TEXT'), 'initial_event_not_init'),
            (dict(self.init, tools=['Read', 'PRIVATE_TOOL']), 'initial_tools_mismatch'),
            (dict(self.init, tools=['Read', 'Read']), 'initial_tools_invalid'),
            (dict(self.init, tools=[{}]), 'initial_tools_invalid'),
            (dict(self.init, mcp_servers=[{'name': 'PRIVATE_SERVER'}]), 'initial_mcp_unverified')]
        for event, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(review_result.init_error(event, self.context['allowed_tools']), expected)

    def test_boundary_diagnostic_is_not_duplicated_by_final_parser(self):
        execution = dict(self.execution, execution_status='failed',
            diagnostics=['tool_boundary_unverified', 'initial_tools_mismatch'])
        result = self.report(self.stream(dict(self.init, tools=['Bash'])), execution)
        self.assertEqual(result['diagnostics'], ['tool_boundary_unverified', 'initial_tools_mismatch'])

    def test_verified_ui_redraw_before_init_does_not_skip_tool_validation(self):
        redraw = {'type': 'system', 'subtype': 'ui_invalidate', 'event': 'ui.render'}
        stream = self.stream(redraw, self.init, self.terminal)
        self.assertEqual(self.report(stream)['execution_status'], 'completed')
        for tools in (['Read', 'Bash'], ['Read', 'Agent']):
            result = self.report(self.stream(redraw, dict(self.init, tools=tools), self.terminal))
            self.assertEqual(result['execution_status'], 'failed')
            self.assertEqual(result['review_outcome'], 'inconclusive')

    def test_streaming_init_waits_for_complete_line_after_bounded_redraw(self):
        redraw = {'type': 'system', 'subtype': 'ui_invalidate', 'event': 'ui.render'}
        prefix = self.stream(redraw)
        init = json.dumps(self.init).encode()
        self.assertIsNone(review_result.read_init(prefix + init[:20], self.context['allowed_tools']))
        self.assertEqual(review_result.read_init(prefix + init + b'\n', self.context['allowed_tools']), self.init)
        with self.assertRaisesRegex(review_result.ResultError, 'initial_event_not_init'):
            review_result.read_init(prefix, self.context['allowed_tools'], complete=True)

    def test_unknown_hook_install_or_malformed_redraw_prefix_still_fails_closed(self):
        for prefix in ({'type': 'system', 'subtype': 'hook_started'},
                {'type': 'system', 'subtype': 'plugin_install'},
                {'type': 'assistant', 'message': 'PRIVATE_CONTENT'},
                {'type': 'system', 'subtype': 'ui_invalidate', 'event': 'PRIVATE_EVENT'},
                {'type': 'system', 'subtype': 'ui_invalidate', 'event': 'ui.render', 'content': 'PRIVATE_CONTENT'}):
            result = self.report(self.stream(prefix, self.init, self.terminal))
            self.assertEqual(result['execution_status'], 'failed')
            self.assertNotIn('PRIVATE_', json.dumps(result))
        redraw = {'type': 'system', 'subtype': 'ui_invalidate', 'event': 'ui.render'}
        result = self.report(self.stream(*([redraw] * 9), self.init, self.terminal))
        self.assertEqual(result['execution_status'], 'failed')
        with self.assertRaisesRegex(review_result.ResultError, 'initial_output_oversized'):
            review_result.read_init(b'x' * 65537, self.context['allowed_tools'])

    def test_timeout_cancel_nonzero_and_unknown_cleanup_override_valid_model_result(self):
        for state, cleanup in [('timed_out', 'confirmed'), ('cancelled', 'confirmed'),
                               ('failed', 'confirmed'), ('completed', 'unverified')]:
            with self.subTest(state=state, cleanup=cleanup):
                result = self.report(execution={'execution_status': state, 'cleanup': cleanup, 'diagnostics': []})
                self.assertNotEqual(result['execution_status'], 'completed')
                self.assertEqual(result['review_outcome'], 'inconclusive')

    def test_missing_usage_and_model_are_unknown_not_zero_and_raw_process_events_are_not_kept(self):
        self.init.pop('model')
        self.terminal.pop('modelUsage')
        self.terminal.pop('total_cost_usd')
        result = self.report(self.stream(self.init, {'type': 'assistant', 'message': {'content': 'SECRET_THINKING'}}, self.terminal))
        self.assertEqual(result['observed_models'], [])
        self.assertNotIn('usage', result)
        self.assertNotIn('SECRET_THINKING', json.dumps(result))

    def test_observed_model_switch_cannot_be_reported_as_success(self):
        self.terminal['modelUsage']['claude-other-model'] = {'inputTokens': 2}
        result = self.report()
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['review_outcome'], 'inconclusive')
        self.assertIn('model_switch_detected', result['diagnostics'])

    def test_scope_schema_uses_only_snapshot_paths_without_mutating_shared_schema(self):
        before = json.dumps(review_result.CONTENT_SCHEMA, sort_keys=True)
        schema = review_result.schema_for_context(self.context)
        properties = schema['properties']
        self.assertEqual(properties['reviewed']['items']['enum'], ['src/a.py'])
        self.assertEqual(properties['unreviewed']['items']['properties']['path']['enum'], ['src/a.py'])
        self.assertEqual(properties['findings']['items']['properties']['file']['enum'], ['src/a.py'])
        self.assertEqual(json.dumps(review_result.CONTENT_SCHEMA, sort_keys=True), before)

    def test_bad_coverage_preserves_cli_model_usage_and_specific_safe_reason(self):
        for content, detail in (
                (dict(self.content, reviewed=['data/src/a.py']), 'coverage_reviewed_path_unknown'),
                (dict(self.content, reviewed=['src/a.py', 'src/a.py']), 'coverage_reviewed_duplicate'),
                (dict(self.content, reviewed=[{}]), 'coverage_collections_invalid'),
                (dict(self.content, unreviewed=[{'path': 'PRIVATE_CREDENTIAL_PATH', 'reason': 'private'}]), 'coverage_unreviewed_path_unknown'),
                (dict(self.content, unreviewed=[{'path': {}, 'reason': 'private'}]), 'coverage_unreviewed_item_invalid'),
                (dict(self.content, reviewed=[], unreviewed=[{'path': 'src/a.py', 'reason': 'one'},
                    {'path': 'src/a.py', 'reason': 'two'}]), 'coverage_unreviewed_duplicate'),
                (dict(self.content, unreviewed=[{'path': 'src/a.py', 'reason': 'private'}]), 'coverage_overlap')):
            with self.subTest(detail=detail):
                terminal = dict(self.terminal, structured_output=content)
                result = self.report(self.stream(self.init, terminal))
                self.assertEqual(result['execution_status'], 'failed')
                self.assertEqual(result['review_outcome'], 'inconclusive')
                self.assertEqual(result['observed_models'], ['claude-fixture'])
                self.assertEqual(result['usage']['estimated_cost_usd'], .01)
                self.assertIn(detail, result['diagnostics'])
                self.assertNotIn('PRIVATE_CREDENTIAL_PATH', json.dumps(result))

    def test_backend_error_preserves_cli_metadata_without_becoming_success(self):
        terminal = dict(self.terminal, subtype='error_max_turns', is_error=True)
        result = self.report(self.stream(self.init, terminal))
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['observed_models'], ['claude-fixture'])
        self.assertEqual(result['usage']['estimated_cost_usd'], .01)
        self.assertIn('backend_result_error', result['diagnostics'])

    def test_error_terminal_preserves_denial_without_exposing_tool_input(self):
        terminal = dict(self.terminal, subtype='error_during_execution', is_error=True,
            errors=['PRIVATE_ERROR_TEXT'], permission_denials=[
                {'tool_name': 'Read', 'tool_input': {'file_path': 'PRIVATE_CREDENTIAL_PATH'}}])
        terminal.pop('structured_output')
        result = self.report(self.stream(self.init, terminal),
            execution={'execution_status': 'failed', 'cleanup': 'confirmed', 'diagnostics': []})
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['review_outcome'], 'inconclusive')
        self.assertIn('permission_denied', result['diagnostics'])
        self.assertIn('backend_result_error', result['diagnostics'])
        self.assertEqual(result['reviewed'], [])
        self.assertTrue(result['unreviewed'])
        self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_known_error_subtypes_are_fixed_diagnostics(self):
        for subtype in ('error_during_execution', 'error_max_turns',
                'error_max_budget_usd', 'error_max_structured_output_retries'):
            with self.subTest(subtype=subtype):
                terminal = dict(self.terminal, subtype=subtype, is_error=True, errors=['PRIVATE_ERROR_TEXT'])
                result = self.report(self.stream(self.init, terminal))
                self.assertIn('claude_' + subtype, result['diagnostics'])
                self.assertIn('backend_result_error', result['diagnostics'])
                self.assertEqual(result['review_outcome'], 'inconclusive')
                self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_assistant_error_enum_is_retained_without_message_or_unknown_values(self):
        for error in ('authentication_failed', 'oauth_org_not_allowed', 'billing_error',
                'rate_limit', 'overloaded', 'invalid_request', 'model_not_found',
                'server_error', 'unknown', 'max_output_tokens'):
            with self.subTest(error=error):
                terminal = dict(self.terminal, subtype='error_during_execution', is_error=True)
                assistant = {'type': 'assistant', 'error': error, 'message': 'PRIVATE_CREDENTIAL_CONTENT'}
                result = self.report(self.stream(self.init, assistant, terminal))
                self.assertIn('claude_api_' + error, result['diagnostics'])
                self.assertEqual(result['execution_status'], 'failed')
                self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_unknown_or_malformed_error_fields_never_become_diagnostics_or_success(self):
        for value in ('PRIVATE_CREDENTIAL_CONTENT', {}, [], None, True):
            with self.subTest(value=value):
                terminal = dict(self.terminal, subtype=value, is_error=True, permission_denials=value)
                result = self.report(self.stream(self.init,
                    {'type': 'assistant', 'error': value, 'message': 'PRIVATE_CONTENT'}, terminal))
                self.assertEqual(result['execution_status'], 'failed')
                self.assertEqual(result['review_outcome'], 'inconclusive')
                self.assertIn('backend_result_error', result['diagnostics'])
                self.assertNotIn('permission_denied', result['diagnostics'])
                self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_recovered_assistant_error_does_not_override_success_or_duplicate_failure_codes(self):
        assistant = {'type': 'assistant', 'error': 'rate_limit', 'message': 'PRIVATE_CONTENT'}
        result = self.report(self.stream(self.init, assistant, self.terminal))
        self.assertEqual(result['execution_status'], 'completed')
        self.assertEqual(result['review_outcome'], 'no_findings_in_scope')
        self.assertNotIn('claude_api_rate_limit', result['diagnostics'])
        terminal = dict(self.terminal, subtype='error_during_execution', is_error=True)
        result = self.report(self.stream(self.init, assistant, assistant, terminal))
        self.assertEqual(result['diagnostics'].count('claude_api_rate_limit'), 1)
        self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_permission_denial_is_not_hidden_by_invalid_coverage(self):
        terminal = dict(self.terminal, structured_output=dict(self.content, reviewed=['data/src/a.py']),
            permission_denials=[{'tool_name': 'Read', 'tool_input': 'PRIVATE_CREDENTIAL_PATH'}])
        result = self.report(self.stream(self.init, terminal))
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['review_outcome'], 'inconclusive')
        self.assertIn('permission_denied', result['diagnostics'])
        self.assertIn('coverage_reviewed_path_unknown', result['diagnostics'])
        self.assertNotIn('PRIVATE_CREDENTIAL_PATH', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
