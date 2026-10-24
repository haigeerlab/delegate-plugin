#!/usr/bin/env python3
"""Private state for resumable Codex runs; Codex session files are never read or removed."""
import json
import os
from pathlib import Path
import re
import sys

RUN_ID = re.compile(r'[0-9]{14}\.[0-9]+')
SESSION_LINE = re.compile(r'session id: ([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})')
MARKER = 'NEED_USER:'


def valid_run_id(value):
    return isinstance(value, str) and RUN_ID.fullmatch(value) is not None


def session_id_from_log(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as log:
            for line in log:
                match = SESSION_LINE.fullmatch(line.strip())
                if match:
                    return match.group(1)
    except OSError:
        return None
    return None


def classify(answer):
    text = answer.lstrip().lstrip('﻿').lstrip()
    if text.startswith(MARKER):
        return 'needs-input', text[len(MARKER):].strip()
    return 'done', None


def _path(directory, run_id, suffix):
    return Path(directory) / (run_id + suffix)


def write_state(directory, state):
    if os.path.islink(directory):
        raise OSError('state directory must not be a symlink')
    target = _path(directory, state['runId'], '.state.json')
    temporary = _path(directory, '.' + state['runId'], '.state.%d.tmp' % os.getpid())
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(state, handle, ensure_ascii=False)
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def read_state(directory, run_id):
    if not valid_run_id(run_id) or os.path.islink(directory):
        return None
    try:
        descriptor = os.open(_path(directory, run_id, '.state.json'), os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, encoding='utf-8') as handle:
            state = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict) or state.get('runId') != run_id:
        return None
    return state


def claim_resume(directory, run_id):
    try:
        os.close(os.open(_path(directory, run_id, '.resumed'), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600))
    except FileExistsError:
        return False
    return True


def check_resume(directory, run_id, repository, write):
    if not valid_run_id(run_id):
        return 'invalid run id', None
    state = read_state(directory, run_id)
    if state is None:
        return 'run not found', None
    if not state.get('sessionId'):
        return 'run not resumable', None
    if state.get('status') != 'needs-input':
        return 'run not waiting for input', None
    if os.path.lexists(_path(directory, run_id, '.resumed')):
        return 'run already resumed', None
    if os.path.realpath(repository) != os.path.realpath(state.get('repository', '')):
        return 'repository mismatch', None
    if bool(write) != bool(state.get('write')):
        return 'write mode mismatch', None
    return None, state


def record(directory, run_id, log, answer, repository, write, model, effort, parent, resumable):
    status = 'done'
    if resumable:
        with open(answer, encoding='utf-8', errors='replace') as handle:
            status = classify(handle.read())[0]
        session = session_id_from_log(log)
        if session is None:
            print('delegate: 过程日志里没有会话 ID，本次运行不能续跑。', file=sys.stderr)
        try:
            write_state(directory, {'schema': 1, 'runId': run_id, 'sessionId': session,
                                    'repository': os.path.realpath(repository), 'write': write,
                                    'model': model, 'effort': effort, 'status': status, 'parent': parent or None})
        except OSError:
            print('delegate: 续跑状态写入失败，本次运行不能续跑。', file=sys.stderr)
            session = None
        resumable = session is not None
    return 'delegate: run_id=%s status=%s resumable=%s' % (run_id, status, 'true' if resumable else 'false')


def main(arguments):
    command = arguments[0] if arguments else ''
    if command == 'record' and len(arguments) == 11:
        directory, run_id, log, answer, repository, write, model, effort, parent, resumable = arguments[1:]
        print(record(directory, run_id, log, answer, repository, write == '1', model, effort, parent, resumable == '1'))
        return 0
    if command == 'check' and len(arguments) == 5:
        reason, state = check_resume(arguments[1], arguments[2], arguments[3], arguments[4] == '1')
        if reason:
            print('delegate: ' + reason, file=sys.stderr)
            return 64
        print('\n'.join((state['sessionId'], state.get('model') or '', state.get('effort') or '')))
        return 0
    if command == 'claim' and len(arguments) == 3:
        if not valid_run_id(arguments[2]) or not claim_resume(arguments[1], arguments[2]):
            print('delegate: run already resumed', file=sys.stderr)
            return 64
        return 0
    print('delegate: run_state usage error', file=sys.stderr)
    return 64


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
