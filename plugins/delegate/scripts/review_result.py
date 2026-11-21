#!/usr/bin/env python3
"""Validate model claims separately from trusted execution facts."""
import json
import math
import re

from claude_review import unique_object
from review_recheck import STATUSES as RECHECK_STATUSES

CONTENT_FIELDS = {'schema_version', 'reviewed', 'unreviewed', 'findings'}
FINDING_FIELDS = {'title', 'file', 'line', 'trigger', 'impact', 'evidence', 'suggestion', 'unverified', 'severity'}
SEVERITY_VALUES = ['blocking', 'suggestion']
CONTENT_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'properties': {'schema_version': {'type': 'integer', 'const': 1}, 'reviewed': {'type': 'array', 'items': {'type': 'string'}},
        'unreviewed': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'properties': {'path': {'type': 'string'}, 'reason': {'type': 'string'}}, 'required': ['path', 'reason']}},
        'findings': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'properties': {**{name: {'type': 'string'} for name in FINDING_FIELDS - {'line', 'unverified', 'severity'}},
                'line': {'type': ['integer', 'null']}, 'unverified': {'type': 'array', 'items': {'type': 'string'}},
                'severity': {'type': 'string', 'enum': SEVERITY_VALUES}},
            'required': sorted(FINDING_FIELDS)}}}, 'required': sorted(CONTENT_FIELDS)}


TLS_UNTRUSTED_MARKERS = ('SELF_SIGNED_CERT_IN_CHAIN', 'DEPTH_ZERO_SELF_SIGNED_CERT',
    'UNABLE_TO_GET_ISSUER_CERT', 'UNABLE_TO_VERIFY_LEAF_SIGNATURE')


class ResultError(Exception):
    pass


def schema_for_context(context):
    schema = json.loads(json.dumps(CONTENT_SCHEMA))
    paths = sorted(context['files'])
    if paths:
        properties = schema['properties']
        properties['reviewed']['items']['enum'] = paths
        properties['unreviewed']['items']['properties']['path']['enum'] = paths
        properties['findings']['items']['properties']['file']['enum'] = paths
    previous = context.get('previous_findings')
    if previous:
        schema['properties']['previous'] = {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'properties': {'index': {'type': 'integer', 'enum': [item['index'] for item in previous]},
                'status': {'type': 'string', 'enum': RECHECK_STATUSES}, 'evidence': {'type': 'string'}},
            'required': ['evidence', 'index', 'status']}}
        schema['required'] = sorted(CONTENT_FIELDS | {'previous'})
    return schema


def init_error(event, tools):
    # Fixed codes only: startup events can contain paths, credentials or data.
    if not isinstance(event, dict) or event.get('type') != 'system' or event.get('subtype') != 'init':
        return 'initial_event_not_init'
    actual = event.get('tools')
    if (not isinstance(actual, list) or not all(isinstance(tool, str) for tool in actual)
            or len(actual) != len(set(actual))):
        return 'initial_tools_invalid'
    # --tools cannot remove EndConversation. It only ends the session, while
    # StructuredOutput supplies the requested schema; neither grants IO access.
    if set(actual) - {'StructuredOutput', 'EndConversation'} != set(tools):
        return 'initial_tools_mismatch'
    if event.get('mcp_servers') != []:
        return 'initial_mcp_unverified'
    return None


def init_valid(event, tools):
    return init_error(event, tools) is None


def read_init(stream, tools, *, complete=False):
    """Bound startup metadata without trusting arbitrary pre-init events."""
    consumed, redraws = 0, 0
    for line in stream[:65537].splitlines(keepends=True):
        consumed += len(line)
        if consumed > 65536:
            raise ResultError('initial_output_oversized')
        if not line.endswith(b'\n') and not complete:
            return None
        try:
            event = json.loads(line, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError):
            raise ResultError('initial_output_invalid') from None
        if isinstance(event, dict) and event.get('type') == 'system' and event.get('subtype') == 'init':
            error = init_error(event, tools)
            if error:
                raise ResultError(error)
            return event
        # Original 2.1.296 emits this passive repaint before init. No hook,
        # plugin, model, control request or unknown payload gets this exception.
        if (not isinstance(event, dict) or event.get('type') != 'system'
                or event.get('subtype') != 'ui_invalidate' or event.get('event') != 'ui.render'
                or set(event) - {'type', 'subtype', 'event', 'uuid', 'session_id'}
                or any(not isinstance(event[key], str) or not re.fullmatch(
                    r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', event[key])
                    for key in ('uuid', 'session_id') if key in event)):
            raise ResultError('initial_event_not_init')
        redraws += 1
        if redraws > 8:
            raise ResultError('initial_prefix_limit')
    if complete:
        raise ResultError('initial_event_not_init' if redraws else 'initial_output_empty')
    return None


def content_result(content, context):
    previous = context.get('previous_findings') or []
    if (not isinstance(content, dict) or set(content) != (CONTENT_FIELDS | {'previous'} if previous else CONTENT_FIELDS)
            or type(content['schema_version']) is not int or content['schema_version'] != 1):
        raise ResultError('structured_result_invalid')
    reviewed, unreviewed, findings = content['reviewed'], content['unreviewed'], content['findings']
    if (not isinstance(reviewed, list) or len(reviewed) > 256
            or any(not isinstance(path, str) for path in reviewed)
            or not isinstance(unreviewed, list) or len(unreviewed) > 256
            or not isinstance(findings, list) or len(findings) > 100):
        raise ResultError('coverage_collections_invalid')
    if any(path not in context['files'] for path in reviewed):
        raise ResultError('coverage_reviewed_path_unknown')
    if len(set(reviewed)) != len(reviewed):
        raise ResultError('coverage_reviewed_duplicate')
    omitted = list(context['unreviewed'])
    for item in unreviewed:
        if (not isinstance(item, dict) or set(item) != {'path', 'reason'}
                or not isinstance(item['path'], str)
                or not isinstance(item['reason'], str) or not 1 <= len(item['reason']) <= 1000):
            raise ResultError('coverage_unreviewed_item_invalid')
        if item['path'] not in context['files']:
            raise ResultError('coverage_unreviewed_path_unknown')
        if item['path'] in reviewed:
            raise ResultError('coverage_overlap')
        if any(entry['path'] == item['path'] for entry in omitted):
            raise ResultError('coverage_unreviewed_duplicate')
        omitted.append(dict(item))
    for name in context['files']:
        if name not in reviewed and not any(entry['path'] == name for entry in omitted):
            omitted.append({'path': name, 'reason': 'coverage_not_reported'})
    validated, verified = [], True
    for item in findings:
        if not isinstance(item, dict) or set(item) != FINDING_FIELDS:
            raise ResultError('finding_invalid')
        if item['severity'] not in SEVERITY_VALUES:
            raise ResultError('finding_invalid')
        for key in FINDING_FIELDS - {'line', 'unverified', 'severity'}:
            if not isinstance(item[key], str) or not 1 <= len(item[key]) <= 4000:
                raise ResultError('finding_invalid')
        if (not isinstance(item['unverified'], list) or len(item['unverified']) > 20
                or any(not isinstance(value, str) or len(value) > 2000 for value in item['unverified'])
                or (item['line'] is not None and type(item['line']) is not int)):
            raise ResultError('finding_invalid')
        data = context['files'].get(item['file'])
        line = item['line']
        location = data is not None and type(line) is int and 1 <= line <= len(data.splitlines())
        value = dict(item, location_verified=location)
        value['unverified'] = list(item['unverified'])
        if not location:
            value['line'] = None
            value['unverified'].append('location_not_verified_in_snapshot')
            verified = False
        validated.append(value)
    result = {'reviewed': reviewed, 'unreviewed': omitted, 'findings': validated}
    if previous:
        result['recheck'] = dict(context['recheck_source'], items=recheck_items(content['previous'], previous))
    return result, verified


def recheck_items(answers, previous):
    by_index = {item['index']: item for item in previous}
    if not isinstance(answers, list) or len(answers) != len(by_index):
        raise ResultError('recheck_invalid')
    seen = {}
    for answer in answers:
        if (not isinstance(answer, dict) or set(answer) != {'index', 'status', 'evidence'}
                or type(answer['index']) is not int or answer['index'] not in by_index or answer['index'] in seen
                or answer['status'] not in RECHECK_STATUSES
                or not isinstance(answer['evidence'], str) or not 1 <= len(answer['evidence']) <= 4000):
            raise ResultError('recheck_invalid')
        seen[answer['index']] = answer
    return [{'index': index, 'status': seen[index]['status'], 'evidence': seen[index]['evidence'],
             'finding': {key: value for key, value in by_index[index].items() if key != 'index'}}
            for index in sorted(by_index)]


def clear_recheck_items(report):
    """A review without a conclusion keeps the previous report's sha and fingerprint but no verdicts."""
    if report['execution_status'] != 'completed' and report.get('recheck'):
        report['recheck']['items'] = []


def conclude(report, verified):
    """Shared outcome rule for both backends (spec/review-recheck.md A12)."""
    if report['execution_status'] != 'completed':
        clear_recheck_items(report)
        return
    if not verified or report['unreviewed']:
        report['execution_status'] = 'failed'
        report['diagnostics'].append('review_incomplete')
        clear_recheck_items(report)
        return
    unresolved = any(item['status'] == 'unresolved' for item in (report.get('recheck') or {}).get('items', []))
    report['review_outcome'] = 'findings' if report['findings'] or unresolved else 'no_findings_in_scope'


def base_report(backend, execution, context, requested_model):
    state = execution.get('execution_status', 'failed')
    cleanup = execution.get('cleanup', 'unverified')
    if state not in ('completed', 'conditions_missing', 'failed', 'timed_out', 'cancelled'):
        state = 'failed'
    if state == 'completed' and cleanup != 'confirmed':
        state = 'failed'
    # Control-plane diagnostics are fixed identifiers, never raw stderr.
    diagnostics = [item for item in execution.get('diagnostics', [])
                   if isinstance(item, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', item)]
    return {'schema_version': 1, 'execution_status': state, 'review_outcome': 'inconclusive',
        'host': 'unknown', 'backend': backend, 'backend_started': execution.get('backend_started', True),
        'execution_environment': execution.get('execution_environment', 'unknown'),
        'cleanup': cleanup, 'requested_model': requested_model, 'observed_models': [],
        'scope': {'paths': context['scope'], 'baseline': context['baseline'],
                  'diff_sha256': context['diff_sha256'], 'fingerprint': context.get('fingerprint'),
                  'files': context['file_sha256']},
        'reviewed': [], 'unreviewed': list(context['unreviewed']) + [
            {'path': name, 'reason': 'review_not_completed'} for name in context['files']],
        'findings': [], 'diagnostics': diagnostics,
        'recheck': dict(context['recheck_source'], items=[]) if context.get('recheck_source') else None,
        'limitations': ['Structured format and verified locations do not prove findings true. Review does not authorize merge or delivery.']}


def claude_report(stream, execution, context, *, requested_model=None):
    report = base_report('claude-code', execution, context, requested_model)
    try:
        if not isinstance(stream, bytes) or not stream.strip() or len(stream) > 1024 * 1024:
            raise ResultError('stream_empty_or_oversized')
        events = [json.loads(line, object_pairs_hook=unique_object) for line in stream.splitlines() if line.strip()]
        if not events or any(not isinstance(event, dict) for event in events):
            raise ResultError('stream_invalid')
        inits = [event for event in events if event.get('type') == 'system' and event.get('subtype') == 'init']
        try:
            init = read_init(stream, context['allowed_tools'], complete=True)
        except ResultError as error:
            if str(error) not in report['diagnostics']:
                report['diagnostics'].append(str(error))
            raise ResultError('tool_boundary_unverified') from None
        if len(inits) != 1 or init != inits[0]:
            raise ResultError('tool_boundary_unverified')
        terminals = [event for event in events if event.get('type') == 'result']
        if len(terminals) != 1 or events[-1] is not terminals[0]:
            raise ResultError('terminal_result_missing_or_duplicate')
        terminal = terminals[0]
        # Execution metadata remains useful even when the answer is invalid.
        models = []
        model = inits[0].get('model')
        if isinstance(model, str) and re.fullmatch(r'[A-Za-z0-9._:/@+-]{1,200}', model):
            models.append(model)
        model_usage = terminal.get('modelUsage')
        if isinstance(model_usage, dict):
            models += [name for name in model_usage if isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9._:/@+-]{1,200}', name)]
        report['observed_models'] = sorted(set(models))
        usage = {}
        cost = terminal.get('total_cost_usd')
        if type(cost) in (int, float) and math.isfinite(cost) and cost >= 0:
            usage['estimated_cost_usd'] = cost
        tokens = terminal.get('usage')
        if isinstance(tokens, dict):
            for key in ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'):
                value = tokens.get(key)
                if type(value) is int and value >= 0:
                    usage[key] = value
        if usage:
            report['usage'] = usage
        if len(report['observed_models']) > 1:
            raise ResultError('model_switch_detected')
        if requested_model and requested_model.startswith('claude-') and models and any(model != requested_model.removesuffix('[1m]') for model in models):
            raise ResultError('requested_model_not_observed')
        denials = terminal.get('permission_denials')
        if isinstance(denials, list) and denials and 'permission_denied' not in report['diagnostics']:
            report['diagnostics'].append('permission_denied')
        if terminal.get('is_error') is not False or terminal.get('subtype') != 'success':
            # Preserve only closed protocol enums, never errors/message text
            # or denial tool inputs. Error results can also contain denials.
            subtype = terminal.get('subtype')
            if subtype in ('error_during_execution', 'error_max_turns',
                    'error_max_budget_usd', 'error_max_structured_output_retries'):
                report['diagnostics'].append('claude_' + subtype)
            for event in events:
                error = event.get('error')
                if event.get('type') == 'assistant' and error in (
                        'authentication_failed', 'oauth_org_not_allowed', 'billing_error',
                        'rate_limit', 'overloaded', 'invalid_request', 'model_not_found',
                        'server_error', 'unknown', 'max_output_tokens'):
                    code = 'claude_api_' + error
                    if code not in report['diagnostics']:
                        report['diagnostics'].append(code)
                    # Node TLS codes only map to a fixed code; the text stays out.
                    if (any(marker in json.dumps(event) for marker in TLS_UNTRUSTED_MARKERS)
                            and 'claude_api_tls_untrusted' not in report['diagnostics']):
                        report['diagnostics'].append('claude_api_tls_untrusted')
            raise ResultError('backend_result_error')
        if not isinstance(denials, list):
            raise ResultError('permission_status_unverified')
        content, verified = content_result(terminal.get('structured_output'), context)
        report.update(content)
        if denials:
            raise ResultError('permission_denied')
        conclude(report, verified)
    except (ValueError, UnicodeError, ResultError) as error:
        code = str(error) if isinstance(error, ResultError) else 'stream_invalid'
        if code.startswith('coverage_') and 'coverage_invalid' not in report['diagnostics']:
            report['diagnostics'].append('coverage_invalid')
        if code not in report['diagnostics']:
            report['diagnostics'].append(code)
        if report['execution_status'] == 'completed':
            report['execution_status'] = 'failed'
    clear_recheck_items(report)
    return report


def render(report):
    return json.dumps(report, ensure_ascii=False, indent=2) + '\n'
