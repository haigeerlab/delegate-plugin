#!/usr/bin/env python3
"""Read a previous delegate review report and take its blocking findings (spec/review-recheck.md).

The previous report is untrusted model output handed in as a file: only its
structure is checked and copied; errors are fixed codes, never its text or path.
"""
import hashlib
import json

from claude_review import unique_object
from review_context import ContextError

LIMIT = 1024 * 1024
MAX_ITEMS = 100
STATUSES = ['resolved', 'unresolved']
TEXT_FIELDS = ('title', 'file', 'trigger', 'impact', 'evidence', 'suggestion')


def load(path):
    try:
        with open(path, 'rb') as source:
            data = source.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError()
        value = json.loads(data.decode('utf-8'), object_pairs_hook=unique_object)
    except (OSError, ValueError, UnicodeError, TypeError):
        raise ContextError('previous_report_unreadable') from None
    if not isinstance(value, dict):
        raise ContextError('previous_report_unreadable')
    return hashlib.sha256(data).hexdigest(), value


def invalid():
    return ContextError('previous_report_invalid')


def finding(item):
    if not isinstance(item, dict):
        raise invalid()
    copied = {}
    for key in TEXT_FIELDS:
        value = item.get(key)
        if not isinstance(value, str) or not 1 <= len(value) <= 4000:
            raise invalid()
        copied[key] = value
    line, unverified = item.get('line', 'missing'), item.get('unverified')
    if line is not None and type(line) is not int:
        raise invalid()
    if (not isinstance(unverified, list) or len(unverified) > 20
            or any(not isinstance(value, str) or len(value) > 2000 for value in unverified)):
        raise invalid()
    copied.update(line=line, unverified=list(unverified), severity='blocking')
    return copied


def blocking_set(report):
    if (report.get('schema_version') != 1 or report.get('execution_status') != 'completed'
            or report.get('review_outcome') not in ('findings', 'no_findings_in_scope')):
        raise invalid()
    scope, findings, recheck = report.get('scope'), report.get('findings'), report.get('recheck')
    if (not isinstance(scope, dict) or not isinstance(scope.get('paths'), dict)
            or not isinstance(scope.get('baseline'), dict) or not isinstance(findings, list)):
        raise invalid()
    chosen = []
    if recheck is not None:
        items = recheck.get('items') if isinstance(recheck, dict) else None
        if not isinstance(items, list):
            raise invalid()
        for item in items:
            if not isinstance(item, dict) or item.get('status') not in STATUSES:
                raise invalid()
            if item['status'] == 'unresolved':
                chosen.append(finding(item.get('finding')))
    for item in findings:
        if not isinstance(item, dict):
            raise invalid()
        copied = finding(item)
        if item.get('severity') != 'suggestion':
            chosen.append(copied)
    if len(chosen) > MAX_ITEMS:
        raise invalid()
    return [dict(item, index=number) for number, item in enumerate(chosen, 1)]


def check_scope(report, context):
    previous, current = report['scope']['baseline'], context['baseline']
    same = report['scope']['paths'] == context['scope'] and previous.get('mode') == current.get('mode')
    if same and current.get('mode') == 'commits':
        same = previous.get('from') == current.get('from')
    if not same:
        raise ContextError('previous_report_scope_mismatch')


def source(report, sha256):
    return {'previous_report_sha256': sha256, 'previous_fingerprint': report['scope'].get('fingerprint')}
