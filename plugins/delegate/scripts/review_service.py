"""Linux unit boundary used by the optional Claude guest controller.

Fake-manager tests verify wrapper decisions, not cgroup enforcement. The
launcher still needs actual guest validation before any Claude execution.
"""
import os
import json
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

PROPERTIES = ('Id', 'LoadState', 'ActiveState', 'SubState', 'ControlGroup',
              'Result', 'ExecMainCode', 'ExecMainStatus')


class ManagerError(Exception):
    """Carries a fixed diagnostic code, never raw CLI output."""


class ReviewService:
    def __init__(self, *, manager, cgroup_root=Path('/sys/fs/cgroup')):
        self.manager = Path(manager)
        self.cgroup_root = Path(cgroup_root)
        if not self.manager.is_absolute() or not self.cgroup_root.is_absolute():
            raise ValueError('manager and cgroup root must be absolute')
        self.unit = 'delegate-review-' + uuid.uuid4().hex + '.service'
        self.probe_timeout = 5
        self.control = None

    def command(self, launcher, argv, deadline):
        """Build trusted launcher argv; task input is never an executable."""
        if (type(deadline) is not int or not 1 <= deadline <= 540
                or not Path(launcher).is_absolute() or not isinstance(argv, (list, tuple)) or not argv
                or not all(isinstance(arg, str) and '\0' not in arg for arg in argv)
                or not Path(argv[0]).is_absolute()):
            raise ValueError('invalid trusted service command or deadline')
        return [str(launcher), '--user', '--wait', '--pipe', '--quiet', '--description=delegate-review',
                '--service-type=exec', '--unit=' + self.unit,
                '--expand-environment=no', '--property=Restart=no',
                '--property=Delegate=no', '--property=RemainAfterExit=no',
                '--property=RuntimeMaxSec=%ss' % deadline,
                '--property=KillMode=control-group', '--property=SendSIGKILL=yes',
                '--property=TimeoutStopSec=2s', '--'] + list(argv)

    def _manager(self, operation):
        # A manager probe is trusted control-plane code, outside the reviewer.
        # It still gets a deadline, output limit and process-group cleanup.
        env = {name: os.environ[name] for name in
               ('PATH', 'HOME', 'USER', 'LOGNAME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS')
               if name in os.environ}
        process = None
        try:
            with tempfile.TemporaryFile() as output:
                process = subprocess.Popen([str(self.manager), '--user'] + operation,
                    env=env, stdin=subprocess.DEVNULL, stdout=output,
                    stderr=subprocess.DEVNULL, start_new_session=True)
                try:
                    status = process.wait(timeout=self.probe_timeout)
                except subprocess.TimeoutExpired:
                    raise ManagerError('manager_timeout') from None
                if status != 0:
                    raise ManagerError('manager_rejected')
                if output.tell() > 16384:
                    raise ManagerError('manager_output_limit')
                output.seek(0)
                try:
                    return output.read(16385).decode('utf-8', errors='strict')
                except UnicodeError:
                    raise ManagerError('manager_invalid_output') from None
        except OSError:
            raise ManagerError('manager_unavailable') from None
        finally:
            if process is not None:
                # Manager children must not keep the probe alive after it exits.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    raise ManagerError('manager_cleanup_unverified') from None

    def observe(self):
        text = self._manager(['show', '--property=' + ','.join(PROPERTIES), self.unit])
        values = {}
        for line in text.splitlines():
            key, separator, value = line.partition('=')
            if not separator or key not in PROPERTIES or key in values:
                raise ManagerError('manager_invalid_output')
            values[key] = value
        if set(values) != set(PROPERTIES) or values['Id'] != self.unit:
            raise ManagerError('manager_identity_unverified')
        group = values['ControlGroup']
        if group:
            components = group.split('/')[1:]
            if (not group.startswith('/') or not components or components[-1] != self.unit
                    or any(not re.fullmatch(r'[A-Za-z0-9_.@:-]+', item)
                           or item in ('.', '..') for item in components)):
                raise ManagerError('cgroup_identity_unverified')
        for key in ('ExecMainCode', 'ExecMainStatus'):
            if not re.fullmatch(r'[0-9]{1,3}', values[key]):
                raise ManagerError('manager_invalid_output')
        return values

    def _empty(self, group):
        if not group:
            return False
        path = self.cgroup_root / group.lstrip('/')
        try:
            # A previously observed cgroup may disappear after unit teardown.
            # Do not accept an alias or symlink as evidence of that disappearance.
            if path.resolve() != path or self.cgroup_root.resolve(strict=True) != self.cgroup_root:
                return False
            if not path.exists():
                return True
            event_file = path / 'cgroup.events'
            if event_file.resolve(strict=True) != event_file:
                return False
            with event_file.open('rb') as events:
                data = events.read(4097)
            if len(data) > 4096:
                return False
            populated = [line.split() for line in data.splitlines()
                         if line.split()[:1] == [b'populated']]
            return populated == [[b'populated', b'0']]
        except (OSError, RuntimeError):
            return False

    def finish(self, *, exit_code, reason=None):
        """Stop only this unit once, preserving cancellation/deadline causes.

        Missing/collected unit metadata is inconclusive, never a fabricated
        successful run. A later launcher must retain authoritative unit facts.
        """
        if reason not in (None, 'timeout', 'cancelled'):
            raise ValueError('unknown wrapper termination reason')
        diagnostics = []
        before = after = None
        try:
            before = self.observe()
            if not before['ControlGroup']:
                before = self._recorded_state() or before
        except ManagerError as exc:
            before = self._recorded_state()
            if before is None:
                diagnostics.append(str(exc))
        if not (before and before['ActiveState'] in ('inactive', 'failed')
                and self._empty(before['ControlGroup'])):
            try:
                self._manager(['stop', self.unit])
            except ManagerError as exc:
                diagnostics.append(str(exc))
        try:
            after = self.observe()
        except ManagerError as exc:
            after = self._recorded_state()
            if after is None:
                diagnostics.append(str(exc))
        group = before['ControlGroup'] if before else ''
        confirmed = bool(before and after and group
                         and after['ActiveState'] in ('inactive', 'failed')
                         and after['ControlGroup'] in ('', group) and self._empty(group))
        status = 'failed'
        if reason == 'cancelled':
            status = 'cancelled'
        elif reason == 'timeout' or (before and before['Result'] == 'timeout'):
            status = 'timed_out'
        elif (before and exit_code == 0 and before['Result'] == 'success'
              and before['ActiveState'] == 'inactive' and before['SubState'] == 'dead'
              and before['ExecMainCode'] == '1' and before['ExecMainStatus'] == '0'
              and confirmed and not diagnostics):
            status = 'completed'
        if not confirmed:
            diagnostics.append('cleanup_unverified')
        return {'execution_status': status, 'cleanup': 'confirmed' if confirmed else 'unverified',
                'diagnostics': sorted(set(diagnostics))}

    def _recorded_state(self):
        # Only the trusted ExecStopPost recorder may write this control root.
        if self.control is None:
            return None
        path = self.control / (self.unit + '.end.json')
        try:
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as source:
                metadata = os.fstat(source.fileno())
                if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid()
                        or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1):
                    return None
                data = source.read(4097)
            value = json.loads(data)
            if (len(data) > 4096 or not isinstance(value, dict)
                    or set(value) != {'unit', 'group', 'result', 'exit_code', 'exit_status'}
                    or value['unit'] != self.unit
                    or not re.fullmatch(r'/[A-Za-z0-9_.@:/-]+', value['group'])
                    or any(part in ('', '.', '..') for part in value['group'].split('/')[1:])
                    or value['group'].split('/')[-1] != self.unit):
                return None
            result, code, status = value['result'], value['exit_code'], value['exit_status']
            if (result not in ('success', 'exit-code', 'signal', 'core-dump', 'timeout',
                               'resources', 'start-limit-hit', 'oom-kill', 'protocol')
                    or code not in ('exited', 'killed', 'dumped', '')
                    or not isinstance(status, str) or len(status) > 16):
                return None
            return {'Id': self.unit, 'LoadState': 'loaded', 'ActiveState': 'inactive',
                    'SubState': 'dead', 'ControlGroup': value['group'], 'Result': result,
                    'ExecMainCode': '1' if code == 'exited' else '2',
                    'ExecMainStatus': status}
        except (OSError, ValueError, TypeError):
            return None

    def run(self, launcher, argv, *, deadline, environment, cwd, control,
            stdin=None, expected_tools=None, cancel_marker=None):
        """Bound one trusted guest invocation, with retained end facts.

        Original CLI integration and authentication remain separate. Raw stderr
        stays in an ephemeral bounded file, never diagnostic fields or logs.
        """
        cwd, control = Path(cwd), Path(control)
        recorder = Path(__file__).resolve()
        if (not control.is_absolute() or control.resolve(strict=True) != control
                or not control.is_dir() or stat.S_IMODE(control.stat().st_mode) != 0o700
                or not cwd.is_absolute() or cwd.resolve(strict=True) != cwd
                or not all(re.fullmatch(r'[A-Za-z0-9_./-]+', str(path))
                           for path in (control, recorder))):
            raise ValueError('invalid private service control directory')
        if (not isinstance(environment, dict) or not environment
                or any(not re.fullmatch(r'[A-Z][A-Z0-9_]*', key)
                       or not isinstance(value, str) or '\0' in value
                       for key, value in environment.items())):
            raise ValueError('invalid trusted guest environment')
        if stdin is not None and (not isinstance(stdin, bytes) or len(stdin) > 2 * 1024 * 1024):
            raise ValueError('invalid bounded review input')
        if expected_tools is not None and (not isinstance(expected_tools, list) or not expected_tools
                or any(tool not in ('Read', 'Glob', 'Grep') for tool in expected_tools)):
            raise ValueError('invalid expected review tools')
        if cancel_marker is not None:
            cancel_marker = Path(cancel_marker)
            if cancel_marker.parent != control or cancel_marker.name != 'cancel':
                raise ValueError('invalid private cancel marker')
        self.control = control
        command = self.command(launcher, argv, deadline)
        index = command.index('--')
        command[index + 1:] = ['/usr/bin/env', '-i'] + [
            key + '=' + value for key, value in sorted(environment.items())] + list(argv)
        record = '/usr/bin/python3 -B %s --record %s %s' % (
            recorder, control / (self.unit + '.end.json'), self.unit)
        command[index:index] = ['--property=ExecStopPost=' + record,
                               '--property=WorkingDirectory=' + str(cwd)]
        reason = None
        saved = {}

        def cancelled(signum, frame):
            nonlocal reason
            reason = 'cancelled'

        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            saved[signum] = signal.signal(signum, cancelled)
        process = None
        result = None
        try:
            with tempfile.TemporaryFile() as input_file, tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
                if stdin is not None:
                    input_file.write(stdin)
                    input_file.seek(0)
                process = subprocess.Popen(command, stdin=input_file if stdin is not None else subprocess.DEVNULL,
                    stdout=output, stderr=errors, start_new_session=True)
                expires = time.monotonic() + deadline + 3
                overflow = False
                guard_failed = False
                guard_checked = expected_tools is None
                def check_init():
                    from review_result import init_valid
                    data = os.pread(output.fileno(), 65537, 0)
                    first, separator, _ = data.partition(b'\n')
                    if not separator and len(data) <= 65536 and process.poll() is None:
                        return None
                    try:
                        event = json.loads(first)
                        return isinstance(event, dict) and init_valid(event, expected_tools)
                    except (ValueError, UnicodeError):
                        return False
                while process.poll() is None:
                    overflow = max(os.fstat(output.fileno()).st_size,
                                   os.fstat(errors.fileno()).st_size) > 1024 * 1024
                    if cancel_marker is not None and cancel_marker.exists():
                        reason = 'cancelled'
                    if not guard_checked:
                        valid = check_init()
                        if valid is not None:
                            guard_checked = True
                            guard_failed = not valid
                    if reason or overflow or guard_failed or time.monotonic() >= expires:
                        if reason is None and not overflow and not guard_failed:
                            reason = 'timeout'
                        break
                    time.sleep(.02)
                result = self.finish(exit_code=process.poll(), reason=reason)
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
                if not guard_checked:
                    guard_failed = check_init() is not True
                overflow = overflow or max(os.fstat(output.fileno()).st_size,
                                           os.fstat(errors.fileno()).st_size) > 1024 * 1024
                # --wait can return after a unit has already been collected.
                # Re-read only trusted retained facts after stop completes.
                if result['cleanup'] == 'confirmed' and not reason and not overflow and not guard_failed:
                    facts = self._recorded_state()
                    if facts and facts['Result'] == 'timeout':
                        result['execution_status'] = 'timed_out'
                    elif (not result['diagnostics'] and facts and facts['Result'] == 'success' and facts['ExecMainCode'] == '1'
                          and facts['ExecMainStatus'] == '0' and process.returncode == 0):
                        result['execution_status'] = 'completed'
                if overflow:
                    if result['execution_status'] not in ('cancelled', 'timed_out'):
                        result['execution_status'] = 'failed'
                    result['diagnostics'].append('output_limit')
                if guard_failed:
                    if result['execution_status'] not in ('cancelled', 'timed_out'):
                        result['execution_status'] = 'failed'
                    result['diagnostics'].append('tool_boundary_unverified')
                output.seek(0)
                result['stdout'] = output.read(1024 * 1024)
                return result
        finally:
            if process is not None and process.poll() is None:
                try:
                    self._manager(['stop', self.unit])
                finally:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=2)
            for signum, handler in saved.items():
                signal.signal(signum, handler)


def record_end(path, unit):
    """systemd invokes this outside srt after killing service descendants."""
    if not re.fullmatch(r'delegate-review-[0-9a-f]{32}\.service', unit):
        raise ValueError('invalid recorder unit')
    groups = [line.removeprefix('0::') for line in Path('/proc/self/cgroup').read_text().splitlines()
              if line.startswith('0::')]
    if len(groups) != 1 or groups[0].split('/')[-1] != unit:
        raise ValueError('recorder cgroup identity unverified')
    value = {'unit': unit, 'group': groups[0], 'result': os.environ.get('SERVICE_RESULT', ''),
             'exit_code': os.environ.get('EXIT_CODE', ''),
             'exit_status': os.environ.get('EXIT_STATUS', '')}
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'w') as out:
        json.dump(value, out)


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] != '--record':
        raise SystemExit('trusted service recorder only')
    record_end(sys.argv[2], sys.argv[3])
