#!/usr/bin/env python3
"""Mac process boundary, currently exercised only by model-free fixtures.

A temporary launchd job supplies a distinct kernel resource coalition. The
trusted anchor gates startup, stops every reviewer member before killing, and
compares enumeration with the kernel task count. Signals bind to PID generation.
This private Darwin ABI requires explicit capability checks; never fall back to
process names, parent polling or group-only cleanup.
"""
import ctypes
import errno
import json
import os
from pathlib import Path
import plistlib
import signal
import stat
import subprocess
import sys
import time
import uuid

LIMIT = 1024 * 1024


class BoundaryError(Exception):
    """Fixed diagnostic only, no subprocess output."""


class CoalInfo(ctypes.Structure):
    _fields_ = [('identity', ctypes.c_uint64), ('kind', ctypes.c_uint32),
                ('tasks', ctypes.c_uint32)]


class Kernel:
    def __init__(self):
        if sys.platform != 'darwin':
            raise BoundaryError('macos_required')
        try:
            self.lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
            self.lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                ctypes.c_void_p, ctypes.c_int]
            self.lib.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
            self.lib.proc_listcoalitions.argtypes = [ctypes.c_int, ctypes.c_int,
                ctypes.c_void_p, ctypes.c_int]
            self.lib.proc_signal_with_audittoken.argtypes = [ctypes.c_void_p, ctypes.c_int]
        except (OSError, AttributeError):
            raise BoundaryError('macos_process_api_unavailable') from None
        if not self.identity(os.getpid()) or not self.coalition(os.getpid()):
            raise BoundaryError('macos_process_api_unverified')

    def identity(self, pid):
        # PROC_PIDT_BSDINFOWITHUNIQID: 136-byte public BSD info + 56-byte
        # unique identifier. Both describe the same process in one kernel read.
        data = ctypes.create_string_buffer(192)
        ctypes.set_errno(0)
        size = self.lib.proc_pidinfo(pid, 18, 0, data, 192)
        if size != 192:
            if size == 0 and ctypes.get_errno() == errno.ESRCH:
                return None
            raise BoundaryError('process_identity_unverified')
        raw = data.raw
        value = lambda offset, size=4: int.from_bytes(raw[offset:offset + size], 'little')
        if value(12) != pid:
            raise BoundaryError('process_identity_unverified')
        return {'pid': pid, 'uid': value(20), 'state': value(4),
                'unique': value(152, 8), 'generation': value(168)}

    def coalition(self, pid):
        data = (ctypes.c_uint64 * 5)()
        ctypes.set_errno(0)
        size = self.lib.proc_pidinfo(pid, 20, 0, data, 40)
        if size != 40:
            if size == 0 and ctypes.get_errno() == errno.ESRCH:
                return None
            raise BoundaryError('process_coalition_unverified')
        return int(data[0])

    def count(self, coalition):
        if not isinstance(coalition, int) or coalition <= 0:
            raise BoundaryError('coalition_identity_unverified')
        rows = (CoalInfo * 16384)()
        size = self.lib.proc_listcoalitions(1, 0, rows, ctypes.sizeof(rows))
        if size <= 0 or size >= ctypes.sizeof(rows) or size % 16:
            raise BoundaryError('coalition_count_unverified')
        matches = [row.tasks for row in rows[:size // 16]
                   if row.identity == coalition and row.kind == 0]
        if len(matches) > 1:
            raise BoundaryError('coalition_count_unverified')
        return matches[0] if matches else 0

    def members(self, coalition):
        pids = (ctypes.c_int * 65536)()
        count = self.lib.proc_listallpids(pids, ctypes.sizeof(pids))
        if not 0 < count < len(pids):
            raise BoundaryError('process_enumeration_unverified')
        members = []
        for pid in pids[:count]:
            if pid <= 0:
                continue
            try:
                before = self.identity(pid)
                if before is None or self.coalition(pid) != coalition:
                    continue
                after = self.identity(pid)
            except BoundaryError:
                # Other users' protected processes may be unreadable. A count
                # equality check below must still prove full owned membership.
                continue
            if after is not None and before['unique'] == after['unique']:
                if after['uid'] != os.getuid():
                    raise BoundaryError('coalition_owner_unverified')
                if after['state'] != 5:
                    members.append(after)
        return members

    def signal(self, pid, generation, signum):
        token = (ctypes.c_uint32 * 8)()
        token[5], token[7] = pid, generation
        return self.lib.proc_signal_with_audittoken(token, signum)

    def clean(self, coalition, anchor=None):
        """Bounded stop barrier prevents a fork race during final enumeration."""
        expires = time.monotonic() + 3
        while time.monotonic() < expires:
            members = self.members(coalition)
            for member in members:
                if member['pid'] != anchor:
                    result = self.signal(member['pid'], member['generation'], signal.SIGSTOP)
                    if result not in (0, errno.ESRCH):
                        raise BoundaryError('process_stop_rejected')
            stopped = self.members(coalition)
            if (self.count(coalition) == len(stopped)
                    and all(item['pid'] == anchor or item['state'] == 4 for item in stopped)):
                for member in stopped:
                    if member['pid'] != anchor:
                        result = self.signal(member['pid'], member['generation'], signal.SIGKILL)
                        if result not in (0, errno.ESRCH):
                            raise BoundaryError('process_kill_rejected')
                while time.monotonic() < expires:
                    if self.count(coalition) == (1 if anchor is not None else 0):
                        return
                    time.sleep(.02)
                break
            time.sleep(.02)
        raise BoundaryError('cleanup_unverified')


def private_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp.' + uuid.uuid4().hex)
    try:
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'w') as output:
            json.dump(value, output)
        # Publish complete control facts atomically, without replacing an
        # existing gate/terminal file. exists() must never expose partial JSON.
        os.link(temporary, path, follow_symlinks=False)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    with path.open('rb') as source:
        raw = source.read(2 * LIMIT + 1)
    if len(raw) > 2 * LIMIT:
        raise BoundaryError('control_output_limit')
    return json.loads(raw)


class MacBoundary:
    def __init__(self, control):
        self.control = Path(control)
        metadata = self.control.lstat()
        if (not self.control.is_absolute() or self.control.resolve(strict=True) != self.control
                or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700):
            raise BoundaryError('private_control_required')
        self.kernel = Kernel()
        self.label = 'com.delegate.review.' + uuid.uuid4().hex
        self.target = 'gui/%s/%s' % (os.getuid(), self.label)
        self.coalition = None

    def launchctl(self, *arguments):
        try:
            return subprocess.run(['/bin/launchctl', *arguments], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode
        except (OSError, subprocess.TimeoutExpired):
            raise BoundaryError('launchd_control_unavailable') from None

    def service_loaded(self):
        code = self.launchctl('print', self.target)
        if code not in (0, 113):
            raise BoundaryError('launchd_observation_unverified')
        return code == 0

    def run(self, argv, *, cwd, environment, deadline, stdin=None, cancelled=lambda: None,
            expected_tools=None):
        if (not isinstance(argv, list) or not argv or not Path(argv[0]).is_absolute()
                or not all(isinstance(value, str) and '\0' not in value for value in argv)
                or type(deadline) is not int or not 1 <= deadline <= 540
                or not Path(cwd).is_absolute() or Path(cwd).resolve(strict=True) != Path(cwd)
                or not isinstance(environment, dict) or
                any(not isinstance(k, str) or not isinstance(v, str) or '\0' in k + v
                    for k, v in environment.items())
                or stdin is not None and (not isinstance(stdin, bytes) or len(stdin) > 2 * LIMIT)):
            raise ValueError('invalid trusted Mac command')
        if expected_tools is not None and (not isinstance(expected_tools, list)
                or not expected_tools or len(expected_tools) != len(set(expected_tools))
                or any(tool not in ('Read', 'Glob', 'Grep') for tool in expected_tools)):
            raise ValueError('invalid expected review tools')
        root = self.control
        (root / 'stdin').write_bytes(stdin or b''); (root / 'stdin').chmod(0o600)
        private_json(root / 'request', {'argv': argv, 'cwd': str(cwd), 'environment': environment,
            'deadline': deadline, 'target': self.target, 'expected_tools': expected_tools})
        # launchd's interpreter may not be allowed to reopen an installation
        # under Documents. Stage only trusted supervisor/parser code in the
        # existing private control tree, which remains denied to the reviewer.
        anchor_code = root / 'anchor-code'
        anchor_code.mkdir(mode=0o700)
        for name in ('review_macos.py', 'review_result.py', 'claude_review.py'):
            staged = anchor_code / name
            staged.write_bytes((Path(__file__).resolve().parent / name).read_bytes())
            staged.chmod(0o600)
        plist = root / 'job.plist'
        plist.write_bytes(plistlib.dumps({'Label': self.label, 'RunAtLoad': True,
            'KeepAlive': False, 'AbandonProcessGroup': False,
            'ProgramArguments': [str(Path(sys.executable).resolve()), '-B',
                str(anchor_code / 'review_macos.py'), '--anchor', str(root)],
            'StandardOutPath': '/dev/null', 'StandardErrorPath': '/dev/null'}))
        plist.chmod(0o600)
        result = {'execution_status': 'failed', 'cleanup': 'unverified', 'stdout': b'',
                  'execution_environment': 'native', 'cleanup_scope': 'kernel_coalition',
                  'backend_started': False, 'diagnostics': []}
        cause = None
        received = None
        saved = {}
        def stop(signum, frame):
            nonlocal received
            received = received or signum
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            saved[signum] = signal.signal(signum, stop)
        try:
            if self.launchctl('bootstrap', self.target.rsplit('/', 1)[0], str(plist)):
                raise BoundaryError('launchd_start_failed')
            expires = time.monotonic() + 4
            while not (root / 'ready').exists():
                cause = received or cancelled()
                if cause:
                    raise BoundaryError('cancelled_before_start')
                if time.monotonic() >= expires:
                    raise BoundaryError('anchor_start_unverified')
                time.sleep(.02)
            ready = read_json(root / 'ready')
            pid = ready['pid']
            identity = self.kernel.identity(pid)
            coalition = self.kernel.coalition(pid)
            if (identity is None or identity['generation'] != ready['generation']
                    or not coalition or coalition == self.kernel.coalition(os.getpid())
                    or self.kernel.count(coalition) != 1
                    or [item['pid'] for item in self.kernel.members(coalition)] != [pid]):
                raise BoundaryError('job_coalition_unverified')
            self.coalition = coalition
            cause = received or cancelled()
            if cause:
                raise BoundaryError('cancelled_before_start')
            private_json(root / 'start', {'coalition': coalition})
            expires = time.monotonic() + deadline + 8
            while not (root / 'end').exists():
                cause = cause or received or cancelled()
                if cause and not (root / 'cancel').exists():
                    private_json(root / 'cancel', {'signal': cause})
                if time.monotonic() >= expires:
                    raise BoundaryError('anchor_end_unverified')
                time.sleep(.02)
            result.update(read_json(root / 'end'))
            if result['diagnostics'] and result['execution_status'] == 'completed':
                result['execution_status'] = 'failed'
            if cause:
                result['execution_status'] = 'cancelled'
        except (BoundaryError, OSError, ValueError, KeyError, TypeError) as error:
            if cause:
                result['execution_status'] = 'cancelled'
            result['diagnostics'].append(str(error) if isinstance(error, BoundaryError) else 'macos_control_failed')
        finally:
            # Even an unknown bootstrap outcome is removed by this exact nonce
            # service identity, never a broad launchd domain or process name.
            try:
                if self.coalition is not None:
                    self.kernel.clean(self.coalition)
                self.launchctl('bootout', self.target)
                if self.service_loaded() or self.coalition is not None and self.kernel.count(self.coalition) != 0:
                    raise BoundaryError('cleanup_unverified')
                result['cleanup'] = 'confirmed'
            except BoundaryError as error:
                result['cleanup'] = 'unverified'
                result['diagnostics'].append(str(error))
            if result['cleanup'] != 'confirmed' and result['execution_status'] == 'completed':
                result['execution_status'] = 'failed'
            cause = cause or received
            if cause:
                result['execution_status'] = 'cancelled'
                result['cancel_signal'] = cause
            for signum, handler in saved.items():
                signal.signal(signum, handler)
        output = root / 'stdout'
        if output.exists():
            with output.open('rb') as source:
                result['stdout'] = source.read(LIMIT + 1)
        return result


def anchor(root):
    """Trusted supervisor; reviewer never receives this control path as a tool."""
    kernel = Kernel()
    pid = os.getpid()
    coalition = kernel.coalition(pid)
    identity = kernel.identity(pid)
    private_json(root / 'ready', {'pid': pid, 'generation': identity['generation']})
    request = read_json(root / 'request')
    end = {'execution_status': 'failed', 'backend_started': False, 'diagnostics': []}
    process = None
    try:
        expires = time.monotonic() + 5
        while not (root / 'start').exists():
            if time.monotonic() >= expires:
                raise BoundaryError('anchor_gate_timeout')
            time.sleep(.02)
        if read_json(root / 'start')['coalition'] != coalition:
            raise BoundaryError('anchor_identity_mismatch')
        with (root / 'stdin').open('rb') as input_file, (root / 'stdout').open('w+b') as output, (root / 'stderr').open('wb') as errors:
            os.chmod(root / 'stdout', 0o600); os.chmod(root / 'stderr', 0o600)
            process = subprocess.Popen(request['argv'], cwd=request['cwd'], env=request['environment'],
                stdin=input_file, stdout=output, stderr=errors, start_new_session=True)
            end['backend_started'] = True
            expires = time.monotonic() + request['deadline']
            checked = request['expected_tools'] is None
            def check_init():
                from review_result import read_init, ResultError
                data = os.pread(output.fileno(), 65537, 0)
                try:
                    event = read_init(data, request['expected_tools'], complete=process.poll() is not None)
                    return (True, None) if event is not None else None
                except ResultError as error:
                    return False, str(error)
            while process.poll() is None:
                if (root / 'cancel').exists():
                    end['execution_status'] = 'cancelled'; break
                if not checked:
                    valid = check_init()
                    if valid is not None:
                        checked = True
                        if not valid[0]:
                            end['diagnostics'].extend(['tool_boundary_unverified', valid[1]]); break
                if any(os.fstat(stream.fileno()).st_size > LIMIT for stream in (output, errors)):
                    end['diagnostics'].append('output_limit'); break
                if time.monotonic() >= expires:
                    end['execution_status'] = 'timed_out'; break
                time.sleep(.02)
            else:
                end['execution_status'] = 'completed' if process.returncode == 0 else 'failed'
            if not checked:
                valid = check_init()
                if valid is None or not valid[0]:
                    end['diagnostics'].extend(['tool_boundary_unverified',
                        valid[1] if valid is not None else 'initial_output_empty'])
                    if end['execution_status'] not in ('cancelled', 'timed_out'):
                        end['execution_status'] = 'failed'
            if any(os.fstat(stream.fileno()).st_size > LIMIT for stream in (output, errors)):
                end['execution_status'] = 'failed'; end['diagnostics'].append('output_limit')
    except (BoundaryError, OSError, ValueError, KeyError, TypeError) as error:
        end['diagnostics'].append(str(error) if isinstance(error, BoundaryError) else 'macos_execution_failed')
    finally:
        try:
            kernel.clean(coalition, anchor=pid)
            if process is not None:
                process.wait(timeout=1)
                end['launcher_exit_code'] = process.returncode
            end['cleanup'] = 'confirmed'
        except (BoundaryError, subprocess.TimeoutExpired) as error:
            end['cleanup'] = 'unverified'
            end['diagnostics'].append(str(error) if isinstance(error, BoundaryError) else 'cleanup_unverified')
        try:
            private_json(root / 'end', end)
            # Keep the anchor alive for the controller's empty-membership proof.
            time.sleep(4)
        finally:
            subprocess.run(['/bin/launchctl', 'bootout', request['target']],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--anchor':
        raise SystemExit('trusted Mac anchor entry only')
    anchor(Path(sys.argv[2]))
