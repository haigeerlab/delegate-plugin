#!/usr/bin/env python3
"""Private state for resumable Codex runs; Codex session files are never read or removed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

import run_events

RUN_ID = re.compile(r'[0-9]{14}\.[0-9]+')
SESSION_LINE = re.compile(r'session id: ([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})')
MARKER = 'NEED_USER:'
TIME_UP = 'TIME_UP:'
DONE = 'DONE:'
CLEANUP_LEFTOVER = re.compile(r'delegate: 清理：中止后仍有残留，PID=([0-9 ]+)$')
CLEANUP_UNREAPED = re.compile(r'delegate: 执行进程未能回收，PID=([0-9]+)$')
CLEANUP_FORCED = 'delegate: 执行进程超时未退出，已强制结束'
# Deadline split for one delegated run: T total seconds -> wrap-up W, main run M, "no new step" threshold S.
WRAPUP_CAP = 45
WRAPUP_DIVISOR = 6
THRESHOLD_MARGIN = 90
THRESHOLD_DIVISOR = 2
# Retention: process logs keep the latest LOG_GROUPS runs; chain state outlives them by age (run-continue).
LOG_GROUPS = 50
LOG_SUFFIXES = ('.answer', '.wrapup', '.wrapup.answer', '.baseline', '.cleanup', '.events.jsonl',
                '.wrapup.events.jsonl', '.check.log', '.check.cleanup', '.check.json')
STATE_SUFFIXES = ('.state.json', '.resumed', '.result.json')
STATE_RETENTION_DAYS = 14
AUTHORIZATION_MAX_BYTES = 64 * 1024


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


def deadlines(total):
    wrapup = min(WRAPUP_CAP, total // WRAPUP_DIVISOR)
    main = total - wrapup
    return wrapup, main, max(main - THRESHOLD_MARGIN, main // THRESHOLD_DIVISOR)


def classify(answer, resumable=True, strict=False):
    text = answer.lstrip().lstrip('﻿').lstrip()
    if text.startswith(TIME_UP):
        return 'timeout', text[len(TIME_UP):].strip()
    if resumable and text.startswith(MARKER):
        return 'needs-input', text[len(MARKER):].strip()
    if not strict:
        return 'done', None
    if text.startswith(DONE):
        return 'done', text[len(DONE):].split('\n', 1)[0].strip()
    return 'unmarked', None


def run_usage(session, parent_total, has_parent):
    """(usage of this run, note): Codex reports usage cumulatively, so a continued run takes the difference."""
    if session is None:
        return None, '本次没有完成的轮次'
    if not has_parent:
        return session, None
    if not isinstance(parent_total, dict) or any(not isinstance(parent_total.get(key), int) or value is None
                                                 for key, value in session.items()):
        return None, '父轮用量未知'
    return {key: value - parent_total[key] for key, value in session.items()}, None


def session_usage(events, wrapup=None):
    """The latest cumulative usage of the session: the wrap-up round runs later in the same session."""
    later = run_events.usage(wrapup) if wrapup else None
    return later if later is not None else (run_events.usage(events) if events else None)


def usage_line(directory, events, wrapup, parent):
    session = session_usage(events, wrapup)
    origin = read_state(directory, parent) if parent else None
    run, note = run_usage(session, (origin or {}).get('usageTotal'), bool(parent))
    if run is None:
        return '用量：未知（%s）' % note
    return '用量：本次输入 {:,}（缓存 {:,}）/ 输出 {:,}；整个会话输入 {:,}'.format(
        run['inputTokens'], run['cachedInputTokens'], run['outputTokens'], session['inputTokens'])


def _iso(seconds):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(seconds))


def _read_lines(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as handle:
            return [line.rstrip('\n') for line in handle if line.strip()]
    except (OSError, TypeError):
        return []


def build_result(options):
    """The result document for one run; see spec/run-result.md."""
    directory, run_id, parent = options.directory, options.run_id, options.parent or None
    state = read_state(directory, run_id) if options.resumable else None
    origin = read_state(directory, parent) if parent else None
    session = session_usage(options.events, options.wrapup_events)
    run, note = run_usage(session, (origin or {}).get('usageTotal'), bool(parent))
    commands, truncated = run_events.commands(options.events)
    try:
        with open(options.answer, encoding='utf-8', errors='replace') as handle:
            answer = handle.read()
    except OSError:
        answer = ''
    markers = {'needUser': None, 'timeUp': None, 'done': None}
    if options.status in ('done', 'needs-input', 'timeout', 'unmarked'):
        status, text = classify(answer, bool(options.resumable_mode), options.strict)
        key = {'needs-input': 'needUser', 'timeout': 'timeUp', 'done': 'done'}.get(status)
        if key and text is not None:
            markers[key] = text
    changed = None
    if options.write:
        try:
            with open(options.baseline, encoding='utf-8', errors='replace') as handle:
                baseline = handle.read().splitlines()
            current = subprocess.run(['git', 'status', '--porcelain'], cwd=options.repository, check=True,
                                     stdout=subprocess.PIPE, universal_newlines=True).stdout.splitlines()
            changed = changed_files(baseline, current)
        except (OSError, TypeError, subprocess.CalledProcessError):
            changed = None
    ended = time.time()
    try:
        answer_bytes = os.path.getsize(options.answer)
    except OSError:
        answer_bytes = None
    wrapup = {'mode': options.wrapup_mode, 'reason': options.wrapup_reason or None} if options.wrapup_mode else None
    return {
        'schema': 1, 'runId': run_id, 'kind': options.kind, 'parent': parent,
        'chainRoot': (state or {}).get('chainRoot') or (origin or {}).get('chainRoot') or parent or run_id,
        'backend': 'codex', 'repository': os.path.realpath(options.repository), 'write': options.write,
        'strict': options.strict, 'model': options.model or None, 'effort': options.effort or None,
        'status': options.status, 'exitCode': options.exit_code, 'resumable': options.resumable,
        'startedAt': _iso(options.started), 'endedAt': _iso(ended),
        'durationSeconds': round(max(0.0, ended - options.started), 1),
        'sessionId': run_events.session_id(options.events),
        'answer': {'path': options.answer, 'bytes': answer_bytes}, 'markers': markers, 'wrapUp': wrapup,
        'commands': commands, 'commandsTruncated': truncated, 'changedFiles': changed,
        'usage': {'run': run, 'session': session, 'note': note},
        'cleanup': parse_cleanup(_read_lines(options.cleanup)),
        'logs': {'events': options.events, 'stderr': options.log},
        'timeoutSeconds': options.timeout_seconds,
    }


def result_main(arguments):
    parser = argparse.ArgumentParser(prog='run_state.py result', add_help=False)
    for name in ('directory', 'run_id', 'kind', 'repository', 'status', 'answer', 'events', 'log'):
        parser.add_argument('--' + name.replace('_', '-'), dest=name, required=True)
    for name in ('parent', 'model', 'effort', 'wrapup_events', 'wrapup_mode', 'wrapup_reason', 'baseline', 'cleanup'):
        parser.add_argument('--' + name.replace('_', '-'), dest=name, default='')
    parser.add_argument('--exit-code', dest='exit_code', type=int, required=True)
    parser.add_argument('--started', type=float, required=True)
    parser.add_argument('--timeout-seconds', dest='timeout_seconds', type=int, default=None)
    parser.add_argument('--check-command', dest='check_command', default=None)
    parser.add_argument('--authorization-file', dest='authorization_file', default='')
    for name in ('write', 'strict', 'resumable', 'resumable_mode'):
        parser.add_argument('--' + name.replace('_', '-'), dest=name, type=lambda value: value == '1', default=False)
    options = parser.parse_args(arguments)
    result = build_result(options)
    result['authorization'] = authorization_entry(options.authorization_file, options.write)
    if options.check_command is not None:
        import run_check
        result['check'] = run_check.recorded(options.directory, options.run_id, options.check_command)
    print(write_result(options.directory, result))
    return 0


def parse_cleanup(lines):
    """Structured view of the abort-cleanup report lines written by run_codex.py and the wrapper."""
    if not lines:
        return None
    leftover, unreaped = [], None
    for line in lines:
        match = CLEANUP_LEFTOVER.match(line)
        if match:
            leftover.extend(int(pid) for pid in match.group(1).split())
        match = CLEANUP_UNREAPED.match(line)
        if match:
            unreaped = int(match.group(1))
    return {'lines': list(lines), 'leftoverPids': leftover, 'unreapedPid': unreaped,
            'wrapperForced': any(line.startswith(CLEANUP_FORCED) for line in lines)}


def changed_files(baseline, current):
    """Porcelain lines that are new or different from the pre-run snapshot."""
    known = set(baseline)
    return [line for line in current if line not in known]


def _path(directory, run_id, suffix):
    return Path(directory) / (run_id + suffix)


def write_state(directory, state):
    _write_private(directory, state['runId'], '.state.json', state)


def _authorization_state(path):
    granted = authorization_file(path)[0] if path else None
    return {'path': granted['path'], 'sha256': granted['sha256']} if granted else None


def authorization_entry(path, write):
    """The result file's record of where write authorization came from (run-check)."""
    if not write:
        return None
    granted = authorization_file(path)[0] if path else None
    return dict(source='file', **granted) if granted else {'source': 'in-turn'}


def write_result(directory, result):
    return _write_private(directory, result['runId'], '.result.json', result)


def _write_private(directory, run_id, suffix, document):
    if os.path.islink(directory):
        raise OSError('state directory must not be a symlink')
    target = _path(directory, run_id, suffix)
    temporary = _path(directory, '.' + run_id, suffix[:-5] + '.%d.tmp' % os.getpid())
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(document, handle, ensure_ascii=False)
        os.replace(temporary, target)
        return target
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


def cleanup(directory, now):
    """Keep the latest LOG_GROUPS process logs and chain state younger than STATE_RETENTION_DAYS."""
    try:
        entries = list(os.scandir(directory))
    except OSError:
        return
    logs = []
    for entry in entries:
        try:
            # Group key: exactly <runId>.log (a .check.log belongs to its run's group, not a group of its own).
            if entry.name.endswith('.log') and not entry.name.endswith('.check.log'):
                logs.append((entry.stat().st_mtime, entry.path))
            elif entry.name.endswith(STATE_SUFFIXES) and entry.stat().st_mtime < now - STATE_RETENTION_DAYS * 86400:
                os.unlink(entry.path)
        except OSError:
            continue
    logs.sort(reverse=True)
    for _, log in logs[LOG_GROUPS:]:
        try:
            os.unlink(log)
        except OSError:
            continue
        for suffix in LOG_SUFFIXES:
            try:
                os.unlink(log[:-4] + suffix)
            except OSError:
                pass


def authorization_file(path):
    """({path, sha256, bytes}, None) for a usable --authorized-by file, else (None, reason). Content is not read for meaning."""
    try:
        info = os.lstat(path)
    except OSError:
        return None, '文件不存在或读不了'
    if stat.S_ISLNK(info.st_mode):
        return None, '是软链接'
    if not stat.S_ISREG(info.st_mode):
        return None, '不是普通文件'
    if info.st_size == 0 or info.st_size > AUTHORIZATION_MAX_BYTES:
        return None, '为空或超过 64 KiB'
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'rb') as handle:
            data = handle.read(AUTHORIZATION_MAX_BYTES + 1)
    except OSError:
        return None, '读不了'
    if not data or len(data) > AUTHORIZATION_MAX_BYTES:
        return None, '为空或超过 64 KiB'
    return {'path': os.path.realpath(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}, None


def check_resume(directory, run_id, repository, write, mode='resume', authorization=None):
    if not valid_run_id(run_id):
        return 'invalid run id', None
    state = read_state(directory, run_id)
    if state is None:
        return 'run not found', None
    if not state.get('sessionId'):
        return 'run not resumable', None
    if mode == 'continue' and state.get('status') != 'done':
        return 'run not done', None
    if mode != 'continue' and state.get('status') not in ('needs-input', 'timeout'):
        return 'run not waiting for input', None
    if os.path.lexists(_path(directory, run_id, '.resumed')):
        return 'run already resumed', None
    if os.path.realpath(repository) != os.path.realpath(state.get('repository', '')):
        return 'repository mismatch', None
    if bool(write) != bool(state.get('write')):
        return 'write mode mismatch', None
    recorded = state.get('authorization')
    if isinstance(recorded, dict) and recorded.get('sha256') != (authorization or None):
        return 'authorization mismatch', None
    return None, state


def record(directory, run_id, log, answer, repository, write, model, effort, parent, resumable, forced=None,
           events=None, strict=False, wrapup_events=None, kind='run', authorization=None):
    with open(answer, encoding='utf-8', errors='replace') as handle:
        status = forced or classify(handle.read(), resumable, strict)[0]
    if resumable:
        session = run_events.session_id(events) if events else session_id_from_log(log)
        origin = read_state(directory, parent) if parent else None
        chain_root = (origin or {}).get('chainRoot') or parent or run_id
        if session is None:
            print('delegate: 过程日志里没有会话 ID，本次运行不能续跑。', file=sys.stderr)
        try:
            write_state(directory, {'schema': 1, 'runId': run_id, 'sessionId': session,
                                    'repository': os.path.realpath(repository), 'write': write,
                                    'model': model, 'effort': effort, 'status': status, 'parent': parent or None,
                                    'chainRoot': chain_root, 'strict': bool(strict), 'kind': kind,
                                    'authorization': _authorization_state(authorization),
                                    'usageTotal': session_usage(events, wrapup_events)})
        except OSError:
            print('delegate: 续跑状态写入失败，本次运行不能续跑。', file=sys.stderr)
            session = None
        resumable = session is not None
    return 'delegate: run_id=%s status=%s resumable=%s' % (run_id, status, 'true' if resumable else 'false')


def main(arguments):
    command = arguments[0] if arguments else ''
    options = {}
    if command == 'result':
        return result_main(arguments[1:])
    if command == 'usage-line' and len(arguments) == 5:
        print(usage_line(arguments[1], arguments[2] or None, arguments[3] or None, arguments[4] or None))
        return 0
    if command == 'authorization' and len(arguments) == 2:
        granted, reason = authorization_file(arguments[1])
        if granted is None:
            print('delegate: authorization file not usable\n' + reason, file=sys.stderr)
            return 64
        print('\n'.join((granted['path'], granted['sha256'], str(granted['bytes']))))
        return 0
    while len(arguments) >= 2 and arguments[-2] in ('--events', '--strict', '--wrapup-events', '--kind',
                                                    '--authorization-file'):
        options[arguments[-2][2:]] = arguments[-1]
        arguments = arguments[:-2]
    if command == 'record' and len(arguments) in (11, 12):
        directory, run_id, log, answer, repository, write, model, effort, parent, resumable = arguments[1:11]
        forced = arguments[11] if len(arguments) == 12 else None
        print(record(directory, run_id, log, answer, repository, write == '1', model, effort, parent, resumable == '1',
                     forced or None, events=options.get('events') or None, strict=options.get('strict') == '1',
                     wrapup_events=options.get('wrapup-events') or None, kind=options.get('kind') or 'run',
                     authorization=options.get('authorization-file') or None))
        return 0
    if command == 'session' and len(arguments) == 2:
        print(session_id_from_log(arguments[1]) or '')
        return 0
    if command == 'deadlines' and len(arguments) == 2 and arguments[1].isdigit():
        print('\n'.join(str(value) for value in deadlines(int(arguments[1]))))
        return 0
    if command == 'changes' and len(arguments) == 2:
        try:
            with open(arguments[1], encoding='utf-8', errors='replace') as handle:
                baseline = handle.read().splitlines()
            current = subprocess.run(['git', 'status', '--porcelain'], check=True, stdout=subprocess.PIPE,
                                     universal_newlines=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            return 1
        print('\n'.join(changed_files(baseline, current)))
        return 0
    if command == 'cleanup' and len(arguments) == 2:
        cleanup(arguments[1], time.time())
        return 0
    if command == 'check' and len(arguments) in (5, 6, 7):
        mode = arguments[5] if len(arguments) >= 6 else 'resume'
        authorization = arguments[6] if len(arguments) == 7 else None
        reason, state = check_resume(arguments[1], arguments[2], arguments[3], arguments[4] == '1', mode, authorization)
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
