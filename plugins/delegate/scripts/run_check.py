#!/usr/bin/env python3
"""--check: validate a check command without a shell and run it after a done run (spec/run-check.md)."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

# S38, copied from module-crew S30 (module_crew/merge.py:24 and _check_config); change it only via mc-coord.
SHELL_OPS = ("&&", "||", ";", "|", ">", "<", "`", "$(")
SPLIT_REFUSAL = '检查命令拆不开：{error}'
EMPTY_REFUSAL = '检查命令不能为空'
OPERATOR_REFUSAL = ('检查命令里有 shell 运算符（「{token}」）：module-crew 不经 shell 执行检查命令，运算符会被当成普通参数。'
                    "改用两种写法之一：把这些步骤写进项目脚本，检查命令写这个脚本；或写成 /bin/sh -c '<原命令>'")


CHECK_TIMEOUT_SECONDS = 600
TAIL_LINES = 40
TAIL_BYTES = 16384
LABELS = {'passed': '通过', 'timeout': '超时', 'cannot-run': '跑不起来', 'unreaped': '未能回收', 'skipped': '跳过'}


def check_timeout(environ):
    # Like DELEGATE_TIMEOUT_SECONDS, the environment can only shorten the limit.
    try:
        seconds = int(environ.get('DELEGATE_CHECK_TIMEOUT_SECONDS', CHECK_TIMEOUT_SECONDS))
    except ValueError:
        return CHECK_TIMEOUT_SECONDS
    return min(seconds, CHECK_TIMEOUT_SECONDS) if seconds > 0 else CHECK_TIMEOUT_SECONDS


def status_of(code, output):
    """Map run_codex.py's exit code for the check command to a check status."""
    if code == 0:
        return 'passed'
    if code == 124:
        return 'timeout'
    if code == 125:
        return 'unreaped'
    if code in (126, 127):
        return 'cannot-run'
    return 'failed'


def label(check):
    if check['status'] == 'failed':
        return '检查：失败（退出 %s）' % check.get('exitCode')
    return '检查：' + LABELS[check['status']]


def _tail(path):
    try:
        with open(path, 'rb') as handle:
            handle.seek(0, os.SEEK_END)
            handle.seek(max(0, handle.tell() - TAIL_BYTES))
            text = handle.read().decode('utf-8', 'replace')
    except OSError:
        return ''
    return '\n'.join(text.splitlines()[-TAIL_LINES:])


def run(directory, run_id, repository, command):
    """Run the check through run_codex.py (argument list, own session, abort reaping) and record it."""
    argv = validate(command)[0]
    base = Path(directory) / run_id
    runner = Path(__file__).with_name('run_codex.py')
    started = time.time()
    with open(str(base) + '.check.log', 'wb') as output:
        code = subprocess.run([sys.executable, '-B', str(runner), '--report', str(base) + '.check.cleanup',
                               str(check_timeout(os.environ)), *argv], cwd=repository, stdin=subprocess.DEVNULL,
                              stdout=output, stderr=subprocess.STDOUT).returncode
    tail = _tail(str(base) + '.check.log')
    check = {'command': command, 'argv': argv, 'status': status_of(code, tail), 'exitCode': code,
             'durationSeconds': round(time.time() - started, 1), 'tail': tail}
    if check['status'] == 'unreaped':
        try:
            with open(str(base) + '.check.cleanup', encoding='utf-8', errors='replace') as handle:
                check['cleanup'] = [line.rstrip('\n') for line in handle if line.strip()]
        except OSError:
            check['cleanup'] = []
    with open(str(base) + '.check.json', 'w', encoding='utf-8') as handle:
        json.dump(check, handle, ensure_ascii=False)
    return check


def recorded(directory, run_id, command):
    """The check entry for the result file: what ran, or a skip when the run did not end done."""
    try:
        with open(str(Path(directory) / run_id) + '.check.json', encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {'command': command, 'argv': validate(command)[0], 'status': 'skipped'}


def validate(command):
    """(argv, None) when the command may run, else (None, refusal text) — byte for byte as module-crew."""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return None, SPLIT_REFUSAL.format(error=exc)
    if not argv:
        return None, EMPTY_REFUSAL
    bad = next((token for token in argv if token.startswith(SHELL_OPS) or token.endswith(SHELL_OPS)), None)
    if bad is not None:
        return None, OPERATOR_REFUSAL.format(token=bad)
    return argv, None


def main(arguments):
    if len(arguments) == 2 and arguments[0] == 'validate':
        refusal = validate(arguments[1])[1]
        if refusal:
            print(refusal, file=sys.stderr)
            return 64
        return 0
    if len(arguments) == 5 and arguments[0] == 'run':
        print(label(run(*arguments[1:])))
        return 0
    print('delegate: run_check usage error', file=sys.stderr)
    return 64


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
