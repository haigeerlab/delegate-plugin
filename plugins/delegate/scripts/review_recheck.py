#!/usr/bin/env python3
"""Read a previous delegate review report and take its blocking findings (spec/review-recheck.md).

The previous report is untrusted model output handed in as a file: only its
structure is checked and copied; errors are fixed codes, never its text or path.
"""
import hashlib
import json
import os
import re
import subprocess

from claude_review import unique_object
from review_context import ContextError, criteria_name

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


OBJECT_ID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
GIT_TIMEOUT = 30


def is_snapshot(baseline):
    return baseline.get('from') == baseline.get('to')


def git_succeeds(repository, *args, expect=None):
    # No replace refs and no lazy fetch: decide on the original local history only.
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0')
    try:
        result = subprocess.run(['git', '-C', repository, *args], stdin=subprocess.DEVNULL, capture_output=True,
                                env=env, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and (expect is None or result.stdout.strip() == expect)


def same_history(repository, previous, current):
    """The previous snapshot commit is the current one or an ancestor of it (spec/review-snapshot-recheck.md)."""
    if (not isinstance(previous, str) or not isinstance(current, str) or not OBJECT_ID.match(previous)
            or len(previous) != len(current) or not isinstance(repository, str)):
        return False
    return (git_succeeds(repository, 'cat-file', '-t', '--end-of-options', previous, expect=b'commit')
            and git_succeeds(repository, 'merge-base', '--is-ancestor', '--end-of-options', previous, current))


def check_scope(report, context):
    previous, current = report['scope']['baseline'], context['baseline']
    same = (report['scope']['paths'] == context['scope'] and previous.get('mode') == current.get('mode')
            and report.get('criteria', 'severity-v1') == criteria_name(context))
    if same and current.get('mode') == 'commits':
        if is_snapshot(previous) != is_snapshot(current):
            same = False
        elif is_snapshot(current):
            same = same_history(context.get('repository'), previous.get('to'), current.get('to'))
        else:
            same = previous.get('from') == current.get('from')
    if not same:
        raise ContextError('previous_report_scope_mismatch')


def source(report, sha256):
    return {'previous_report_sha256': sha256, 'previous_fingerprint': report['scope'].get('fingerprint')}
