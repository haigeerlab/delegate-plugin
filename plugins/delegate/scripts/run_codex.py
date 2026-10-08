#!/usr/bin/env python3
"""Run one Codex process group with a deadline and interrupt cleanup."""
import os
import signal
import subprocess
import sys


class Interrupted(Exception):
    def __init__(self, signum):
        self.signum = signum


def interrupt(signum, frame):
    raise Interrupted(signum)


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    # The parent may have exited while a descendant still holds this group.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def main():
    process = None
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupt)
    try:
        # Do not lose the child's PID if an interrupt arrives during Popen.
        signals = {signal.SIGTERM, signal.SIGINT, signal.SIGHUP}
        previous = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
        try:
            process = subprocess.Popen(sys.argv[2:], start_new_session=True,
                                       restore_signals=True, preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, previous))
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        status = process.wait(timeout=int(sys.argv[1]))
        return status if status >= 0 else 128 - status
    except subprocess.TimeoutExpired:
        return 124
    except Interrupted as exc:
        return 128 + exc.signum
    except OSError as exc:
        print('delegate: 无法启动 Codex：%s' % exc, file=sys.stderr)
        return 127
    finally:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        if process is not None:
            stop_group(process)


if __name__ == '__main__':
    sys.exit(main())
