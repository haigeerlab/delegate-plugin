#!/usr/bin/env python3
"""Validate model claims separately from trusted execution facts."""
import json
import math
import re

from claude_review import unique_object
from review_context import criteria_name, selected
from review_init import ResultError, init_error, init_valid, read_init
from review_recheck import STATUSES as RECHECK_STATUSES

CLAUDE_LOGIN_REFRESH_HINT = ('delegate: Claude 登录令牌可能已过期：请在沙箱外的终端运行一次 `claude`'
    '（例如 claude -p "ok"）刷新登录后重试；仍失败时运行 claude /login 重新登录。')

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
    # spec/review-snapshot-recheck.md S10: a context file outside this round's scope is reference material
    # (S6 tells the reviewer not to report on it), so leaving it unreported is not missing coverage.
    reference_only = {name for name in context.get('context_files', ()) if not selected(name, context['scope'])}
    for name in context['files']:
        if (name not in reviewed and name not in reference_only
                and not any(entry['path'] == name for entry in omitted)):
            omitted.append({'path': name, 'reason': 'coverage_not_reported'})
    validated, verified = [], True
    design = context.get('profile') == 'design'
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
            verified = verified and design
        if design:
            downgrade(value, location, context, previous)
        validated.append(value)
    result = {'reviewed': reviewed, 'unreviewed': omitted, 'findings': validated}
    if previous:
        result['recheck'] = dict(context['recheck_source'], items=recheck_items(content['previous'], previous))
    return result, verified


def downgrade(value, location, context, previous):
    """design-v1 (spec/design-review-criteria.md): only reference-file evidence keeps a finding blocking.

    The model's text is kept; only severity changes and the reason is recorded.
    """
    if value['severity'] != 'blocking':
        return
    if previous:
        reason = 'second_round'
    elif not (location and not selected(value['file'], context['scope'])):
        reason = 'no_code_evidence'
    else:
        return
    value['severity'] = 'suggestion'
    value['downgraded'] = reason


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


def reviewer_default(backend):
    """Before any selection: the requested backend counts as explicit (spec/reviewer-selection.md E3)."""
    from reviewer_select import VENDORS, describe
    return describe(backend, None, 'explicit') if backend in VENDORS else describe(None, None, 'none')


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
        'host': 'unknown', 'backend': backend, 'criteria': criteria_name(context),
        'reviewer': context.get('reviewer') or reviewer_default(backend), 'backend_started': execution.get('backend_started', True),
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
                    if error == 'authentication_failed' and 'claude_login_refresh_required' not in report['diagnostics']:
                        report['diagnostics'].append('claude_login_refresh_required')
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
