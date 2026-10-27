#!/usr/bin/env python3
"""Run one Codex process group with a deadline and interrupt cleanup."""
import os
import signal
import subprocess
import sys
import time

# Abort cleanup bounds; REAP_SECONDS keeps a stuck child from hanging the host.
GRACE_SECONDS = 2
REAP_SECONDS = 5
UNREAPED_STATUS = 125


class Interrupted(Exception):
    def __init__(self, signum):
        self.signum = signum


def interrupt(signum, frame):
    raise Interrupted(signum)


def process_table():
    """Map pid -> (ppid, pgid, is_zombie) for every visible process."""
    table = {}
    if os.path.exists('/proc/self/stat'):
        for name in os.listdir('/proc'):
            if not name.isdigit():
                continue
            try:
                with open('/proc/%s/stat' % name) as stat:
                    data = stat.read()
            except OSError:
                continue
            # Fields after "(comm)": state ppid pgrp ...
            fields = data[data.rfind(')') + 2:].split()
            table[int(name)] = (int(fields[1]), int(fields[2]), fields[0] == 'Z')
        return table
    try:
        rows = subprocess.run(['ps', '-A', '-o', 'pid=', '-o', 'ppid=', '-o', 'pgid=', '-o', 'stat='],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              universal_newlines=True, timeout=5).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return table
    for row in rows:
        parts = row.split()
        if len(parts) == 4:
            table[int(parts[0])] = (int(parts[1]), int(parts[2]), parts[3].startswith('Z'))
    return table


def descendants(root, table):
    """Return {pid: pgid} for every process below root along ppid links."""
    children = {}
    for pid, (ppid, _, _) in table.items():
        children.setdefault(ppid, []).append(pid)
    found = {}
    pending = [root]
    while pending:
        for child in children.get(pending.pop(), []):
            if child not in found:
                found[child] = table[child][1]
                pending.append(child)
    return found


def signal_group(pgid, signum):
    try:
        os.killpg(pgid, signum)
    except (ProcessLookupError, PermissionError):
        # macOS reports EPERM when only zombies remain in the group.
        pass


def living(pids):
    if not pids:
        return []
    table = process_table()
    return sorted(pid for pid in pids if pid in table and not table[pid][2])


def wait_gone(pids, seconds):
    deadline = time.monotonic() + seconds
    remaining = living(pids)
    while remaining and time.monotonic() < deadline:
        time.sleep(.05)
        remaining = living(pids)
    return remaining


def term_descendants(process, report):
    """Freeze Codex only while its descendants are listed and sent TERM."""
    signal_group(process.pid, signal.SIGSTOP)
    found = descendants(process.pid, process_table())
    excluded = (process.pid, os.getpgrp())
    groups = sorted(set(pgid for pgid in found.values() if pgid > 1 and pgid not in excluded))
    for pgid in groups:
        signal_group(pgid, signal.SIGTERM)
    signal_group(process.pid, signal.SIGTERM)
    # A stopped process only acts on TERM once continued.
    signal_group(process.pid, signal.SIGCONT)
    listed = ' '.join('%d(%d)' % (pid, found[pid]) for pid in sorted(found)) or '无'
    report('delegate: 清理：中止前 Codex 的后代进程 %d 个：%s' % (len(found), listed))
    return found, groups


def stop_group(process, aborted=False, report=None):
    """Stop the Codex group; return False if the direct child could not be reaped."""
    if report is None:
        def report(line):
            print(line, file=sys.stderr)
    found, groups = {}, []
    if aborted:
        found, groups = term_descendants(process, report)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
    deadline = time.monotonic() + GRACE_SECONDS
    try:
        process.wait(timeout=GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass
    members = [pid for pid, pgid in found.items() if pgid in groups]
    if wait_gone(members, max(0, deadline - time.monotonic())):
        for pgid in groups:
            signal_group(pgid, signal.SIGKILL)
    # The parent may have exited while a descendant still holds this group.
    signal_group(process.pid, signal.SIGKILL)
    reaped = True
    try:
        process.wait(timeout=REAP_SECONDS)
    except subprocess.TimeoutExpired:
        reaped = False
    if aborted:
        left = wait_gone(found, 1)
        if left:
            report('delegate: 清理：中止后仍有残留，PID=%s' % ' '.join(str(pid) for pid in left))
        else:
            report('delegate: 清理：中止后无残留')
    if not reaped:
        report('delegate: 执行进程未能回收，PID=%d' % process.pid)
    return reaped


def reporter(path):
    def report(line):
        print(line, file=sys.stderr)
        if path:
            try:
                with open(path, 'a') as handle:
                    handle.write(line + '\n')
            except OSError:
                pass
    return report


def main():
    args = sys.argv[1:]
    report_path = None
    if args[:1] == ['--report']:
        report_path, args = args[1], args[2:]
    process = None
    aborted = False
    status = 0
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupt)
    try:
        # Do not lose the child's PID if an interrupt arrives during Popen.
        signals = {signal.SIGTERM, signal.SIGINT, signal.SIGHUP}
        previous = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
        try:
            process = subprocess.Popen(args[1:], start_new_session=True,
                                       restore_signals=True, preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, previous))
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        status = process.wait(timeout=int(args[0]))
        status = status if status >= 0 else 128 - status
    except subprocess.TimeoutExpired:
        aborted = True
        status = 124
    except Interrupted as exc:
        aborted = True
        status = 128 + exc.signum
    except OSError as exc:
        print('delegate: 无法启动 Codex：%s' % exc, file=sys.stderr)
        status = 127
    finally:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        if process is not None and not stop_group(process, aborted, reporter(report_path)):
            status = UNREAPED_STATUS
    return status


if __name__ == '__main__':
    sys.exit(main())
