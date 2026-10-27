#!/usr/bin/env python3
"""The published interface.json and report contract match source facts."""
import ast
import json
from pathlib import Path
import re
import sys
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))
import delegate_capabilities
import review_result

EXECUTION_STATUS = {'completed', 'conditions_missing', 'failed', 'timed_out', 'cancelled'}
REVIEW_OUTCOME = {'findings', 'no_findings_in_scope', 'inconclusive'}
STABLE_FIELDS = {'schema_version', 'execution_status', 'review_outcome', 'backend', 'scope',
                 'reviewed', 'unreviewed', 'findings', 'limitations'}
SCOPE_FIELDS = {'paths', 'baseline', 'diff_sha256', 'files'}
FINDING_FIELDS = {'title', 'file', 'line', 'trigger', 'impact', 'evidence', 'suggestion', 'unverified'}


def constants(node):
    """String values a node can produce, or None when not statically known."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.IfExp):
        body, orelse = constants(node.body), constants(node.orelse)
        return None if body is None or orelse is None else body | orelse
    return None


def assigned_values(key):
    """Every value the scripts assign to report[key] or put under key in a dict literal."""
    values, unknown = set(), []
    for path in sorted((PLUGIN / 'scripts').glob('*.py')):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'), filename=str(path))):
            pairs = []
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)
                            and target.slice.value == key):
                        pairs.append(node.value)
            elif isinstance(node, ast.Dict):
                pairs.extend(value for name, value in zip(node.keys, node.values)
                             if isinstance(name, ast.Constant) and name.value == key)
            for value in pairs:
                found = constants(value)
                if found is None:
                    unknown.append('%s:%d' % (path.name, value.lineno))
                else:
                    values |= found
    return values, unknown


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        path = PLUGIN / 'interface.json'
        self.assertTrue(path.is_file(), 'missing plugins/delegate/interface.json')
        self.interface = json.loads(path.read_text(encoding='utf-8'))
        context = {'files': {'a.py': b''}, 'unreviewed': [], 'scope': {'include': ['a.py'], 'exclude': []},
                   'baseline': {'mode': 'commits', 'from': 'a', 'to': 'b'},
                   'diff_sha256': 'f' * 64, 'file_sha256': {'a.py': 'e' * 64}}
        self.report = review_result.base_report('codex', {'execution_status': 'completed', 'cleanup': 'confirmed'},
                                                context, None)

    def test_interface_version(self):
        self.assertRegex(self.interface['interface'], r'^[0-9]+\.[0-9]+$')

    def test_backends_match_capabilities(self):
        backends = delegate_capabilities.BACKENDS
        self.assertEqual(self.interface['review']['backends'],
                         [name for name, value in backends.items() if value['review']])
        self.assertEqual(self.interface['run']['backends'],
                         [name for name, value in backends.items() if value['run']])
        self.assertIs(self.interface['review']['readOnly'], True)

    def test_resume_is_an_additive_minor_version(self):
        self.assertEqual(self.interface['interface'], '1.3')
        # spec-guard reads these two fields; they must never change within major version 1.
        self.assertEqual(self.interface['review']['command'], '/delegate:review')
        self.assertEqual(self.interface['doctor']['command'], '/delegate:doctor')
        self.assertEqual(self.interface['run']['resume'], {
            'optIn': '--resumable', 'option': '--resume',
            'backends': [name for name, value in delegate_capabilities.BACKENDS.items() if value['resume']],
            'statuses': ['done', 'needs-input', 'timeout']})

    def test_timeout_is_an_additive_minor_version(self):
        # run-timeout: the timeout status always exits 124; statuses is an open set.
        self.assertEqual(self.interface['run']['timeout'], {'status': 'timeout', 'exitCode': 124})
        self.assertIn(self.interface['run']['timeout']['status'], self.interface['run']['resume']['statuses'])

    def test_result_and_usage_are_additive(self):
        # run-result (interface 1.3): result file, --strict and usage; statuses is an open set.
        self.assertEqual(self.interface['run']['result'], {
            'schemaVersion': 1, 'line': 'delegate: result=<path>', 'strict': '--strict',
            'statuses': ['done', 'needs-input', 'timeout', 'unmarked', 'failed', 'interrupted', 'unreaped', 'empty']})
        self.assertEqual(self.interface['run']['usage'], {'in': 'result.usage', 'cumulative': 'session', 'perRun': 'run'})
        self.assertLessEqual(set(self.interface['run']['resume']['statuses']), set(self.interface['run']['result']['statuses']))
        self.assertEqual(self.interface['run']['write'], 'explicit')
        self.assertTrue(delegate_capabilities.BACKENDS['codex']['result'])
        self.assertFalse(delegate_capabilities.BACKENDS['claude-code']['result'])

    def test_continue_is_additive(self):
        # run-continue (interface 1.3): only done rounds of a --resumable chain; accepts is an open set.
        self.assertEqual(self.interface['run']['continue'], {
            'option': '--continue', 'backends': [name for name, value in delegate_capabilities.BACKENDS.items()
                                                 if value['continue']],
            'accepts': ['done'], 'chain': '--resumable', 'stateRetentionDays': 14})
        import run_state
        self.assertEqual(self.interface['run']['continue']['stateRetentionDays'], run_state.STATE_RETENTION_DAYS)

    def test_long_run_is_additive(self):
        # run-longrun (interface 1.3): --timeout only widens the default; the caller runs it in the background.
        self.assertEqual(self.interface['run']['longRun'], {'option': '--timeout', 'minSeconds': 541, 'maxSeconds': 7200,
                                                            'defaultSeconds': 540, 'background': 'caller'})
        self.assertTrue(delegate_capabilities.BACKENDS['codex']['longRun'])

    def test_check_and_write_authorization_are_additive(self):
        # run-check (interface 1.3): --check never uses a shell; run.write stays "explicit".
        import run_check
        self.assertEqual(self.interface['run']['check'], {
            'option': '--check', 'shell': False, 'when': 'done', 'timeoutSeconds': run_check.CHECK_TIMEOUT_SECONDS,
            'operators': list(run_check.SHELL_OPS), 'match': 'token-prefix-or-suffix'})
        self.assertEqual(self.interface['run']['writeAuthorization'], {
            'option': '--authorized-by', 'requires': '--write', 'recorded': 'result.authorization',
            'verifies': ['file-sha256-across-chain', 'repository']})
        self.assertEqual(self.interface['run']['write'], 'explicit')
        self.assertTrue(delegate_capabilities.BACKENDS['codex']['check'])
        self.assertTrue(delegate_capabilities.BACKENDS['codex']['writeAuthorization'])

    def test_report_schema_version(self):
        self.assertEqual(self.interface['review']['report']['schemaVersion'], self.report['schema_version'])

    def test_stable_fields_present(self):
        self.assertLessEqual(STABLE_FIELDS, set(self.report))
        self.assertLessEqual(SCOPE_FIELDS, set(self.report['scope']))
        self.assertEqual(FINDING_FIELDS, review_result.FINDING_FIELDS)

    def test_execution_status_values(self):
        empty = {'files': {}, 'unreviewed': [], 'scope': {}, 'baseline': {}, 'diff_sha256': '', 'file_sha256': {}}
        for state in EXECUTION_STATUS - {'completed'}:
            self.assertEqual(review_result.base_report('codex', {'execution_status': state}, empty, None)['execution_status'], state)
        self.assertEqual(review_result.base_report('codex', {'execution_status': 'unexpected'}, empty, None)['execution_status'], 'failed')
        values, _ = assigned_values('execution_status')
        self.assertLessEqual(values, EXECUTION_STATUS)

    def test_review_outcome_values(self):
        values, unknown = assigned_values('review_outcome')
        self.assertEqual(unknown, [], 'review_outcome assigned a non-constant value; check the contract by hand')
        self.assertEqual(values, REVIEW_OUTCOME)

    def test_backend_values(self):
        values = set(re.findall(r"base_report\('([a-z-]+)'",
                                ''.join(path.read_text(encoding='utf-8') for path in (PLUGIN / 'scripts').glob('*.py'))))
        self.assertEqual(values, set(delegate_capabilities.BACKENDS))


if __name__ == '__main__':
    unittest.main()
