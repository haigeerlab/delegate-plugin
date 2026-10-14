#!/usr/bin/env python3
"""Explicit Lima transport for the Claude review backend; never starts a VM."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import tempfile
import time
import uuid

from claude_review import unique_object
from review_guest import GuestLease, validate_configuration
from review_result import base_report

SCRIPTS = Path(__file__).resolve().parent
GUEST_FILES = ('review_guest.py', 'review_isolation.py', 'review_network.py', 'review_service.py',
               'review_context.py', 'review_result.py', 'claude_review.py', 'review_guest_entry.py')
PROFILE_FIELDS = {'schema_version', 'limactl', 'lima_home', 'guest', 'guest_scripts',
                  'guest_runtime_config', 'guest_runtime_sha256'}
BOOTSTRAP = '''import hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
request=json.loads(sys.stdin.buffer.read(16777217))
try:
 directory=Path(request.pop('scripts'))
 action=request.pop('action')
 expected=request['code_sha256'] if action=='run' else request.pop('code_sha256')
 if not directory.is_absolute() or directory.resolve(strict=True)!=directory: raise ValueError()
 if directory.stat().st_mode & 0o022: raise ValueError()
 for name,digest in expected.items():
  path=directory/name
  if path.resolve(strict=True)!=path or path.stat().st_mode & 0o022 or path.stat().st_nlink!=1: raise ValueError()
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError()
 sys.path.insert(0,str(directory))
 import review_guest_entry as entry
 result=entry.run_request(request) if action=='run' else entry.cancel_request(request,action=action)
 print(json.dumps(result))
except (ValueError,OSError,KeyError,TypeError,ImportError):
 print(json.dumps({'schema_version':1,'execution_status':'conditions_missing','cleanup':'unverified','diagnostics':['guest_preflight_unavailable']}))
 sys.exit(127)
'''


class TransportError(Exception):
    """Fixed codes only; no remote stderr or config contents."""


def validate_profile(profile):
    if (not isinstance(profile, dict) or set(profile) != PROFILE_FIELDS
            or type(profile['schema_version']) is not int or profile['schema_version'] != 1):
        raise TransportError('guest_profile_invalid')
    for key in ('limactl', 'lima_home'):
        value = profile[key]
        try:
            path = Path(value)
            if not isinstance(value, str) or not path.is_absolute() or path.resolve(strict=True) != path:
                raise TransportError('guest_profile_path_invalid')
            if (key == 'limactl' and (not path.is_file() or not os.access(path, os.X_OK))) or (key == 'lima_home' and not path.is_dir()):
                raise TransportError('guest_profile_path_invalid')
        except (OSError, RuntimeError, TypeError):
            raise TransportError('guest_profile_path_invalid') from None
    if not isinstance(profile['guest'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', profile['guest']):
        raise TransportError('guest_name_invalid')
    for key in ('guest_scripts', 'guest_runtime_config'):
        if (not isinstance(profile[key], str) or not re.fullmatch(r'/[A-Za-z0-9_./-]+', profile[key])
                or any(part in ('', '.', '..') for part in profile[key].split('/')[1:])):
            raise TransportError('guest_profile_remote_path_invalid')
    if not isinstance(profile['guest_runtime_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', profile['guest_runtime_sha256']):
        raise TransportError('guest_runtime_digest_invalid')
    return profile


def validate_instance(instance, profile):
    if (not isinstance(instance, dict) or instance.get('name') != profile['guest']
            or instance.get('status') != 'Running' or instance.get('arch') != 'aarch64'
            or instance.get('vmType') != 'vz' or instance.get('errors', []) != []
            or instance.get('dir') != str(Path(profile['lima_home']) / profile['guest'])):
        raise TransportError('dedicated_guest_not_ready')
    configuration = instance.get('config')
    if not isinstance(configuration, dict):
        raise TransportError('guest_configuration_unverified')
    # Lima v2.2.1 serializes [] with omitempty. This normalization is only for
    # its verified effective Config export, never an arbitrary declaration.
    configuration = dict(configuration)
    for key in ('mounts', 'portForwards', 'provision'):
        configuration.setdefault(key, [])
    try:
        validate_configuration(configuration)
    except ValueError:
        raise TransportError('guest_configuration_unsafe') from None
    for flag in ('forwardX11', 'forwardX11Trusted', 'loadDotSSHPubKeys'):
        if configuration['ssh'].get(flag) is not False:
            raise TransportError('guest_ssh_configuration_unverified')
    return {'guest': instance['name'], 'arch': instance['arch'], 'vm_type': instance['vmType']}


def code_digests():
    return {name: hashlib.sha256((SCRIPTS / name).read_bytes()).hexdigest() for name in GUEST_FILES}


def request_payload(context, arguments, run_id, profile, timeout):
    metadata = {key: value for key, value in context.items() if key != 'files'}
    snapshot = {'schema_version': 1, 'files': [{'path': name, 'sha256': context['file_sha256'][name],
        'data': base64.b64encode(data).decode('ascii')} for name, data in context['files'].items()]}
    request = {'schema_version': 1, 'run_id': run_id, 'context': metadata, 'snapshot': snapshot,
        'arguments': arguments, 'timeout': timeout, 'runtime_config': profile['guest_runtime_config'],
        'runtime_sha256': profile['guest_runtime_sha256'], 'code_sha256': code_digests()}
    return json.dumps(request, ensure_ascii=False).encode('utf-8')


class GuestTransport:
    def __init__(self, profile, private):
        self.profile = validate_profile(profile)
        self.private = Path(private)
        self.run_id = uuid.uuid4().hex
        home = self.private / 'host-control-home'
        home.mkdir(mode=0o700, exist_ok=True)
        self.environment = {'HOME': str(home), 'TMPDIR': str(self.private),
            'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LIMA_HOME': profile['lima_home']}
        self.cancelled = None

    def command(self, action):
        if action not in ('run', 'cancel'):
            raise TransportError('guest_action_invalid')
        return [self.profile['limactl'], 'shell', '--start=false', '--preserve-env=false',
                '--reconnect=false', '--shell=/bin/sh', '--workdir=/tmp', self.profile['guest'],
                '/usr/bin/python3', '-B', '-c', BOOTSTRAP]

    def invoke(self, command, *, payload=b'', timeout=5, cancellable=False):
        if len(payload) > 16 * 1024 * 1024:
            raise TransportError('guest_payload_limit')
        process = None
        try:
            with tempfile.TemporaryFile() as input_file, tempfile.TemporaryFile() as output:
                input_file.write(payload); input_file.seek(0)
                process = subprocess.Popen(command, env=self.environment, stdin=input_file,
                    stdout=output, stderr=subprocess.DEVNULL, start_new_session=True)
                expires = time.monotonic() + timeout
                while process.poll() is None:
                    if cancellable and self.cancelled:
                        raise TransportError('transport_cancelled')
                    if time.monotonic() >= expires:
                        raise TransportError('transport_timed_out')
                    if os.fstat(output.fileno()).st_size > 1024 * 1024:
                        raise TransportError('transport_output_limit')
                    time.sleep(.02)
                if os.fstat(output.fileno()).st_size > 1024 * 1024:
                    raise TransportError('transport_output_limit')
                output.seek(0)
                data = output.read(1024 * 1024 + 1)
                if process.returncode not in (0, 127):
                    raise TransportError('transport_failed')
                return data
        except OSError:
            raise TransportError('transport_unavailable') from None
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)

    def preflight(self):
        version = self.invoke([self.profile['limactl'], '--version']).strip()
        if version != b'limactl version 2.2.1':
            raise TransportError('lima_version_unsupported')
        raw = self.invoke([self.profile['limactl'], 'list', '--json', '--all-fields', self.profile['guest']])
        try:
            instance = json.loads(raw, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError):
            raise TransportError('guest_state_invalid') from None
        return validate_instance(instance, self.profile)

    def cancel(self):
        request = {'run_id': self.run_id, 'action': 'cancel', 'scripts': self.profile['guest_scripts'], 'code_sha256': code_digests()}
        try:
            raw = self.invoke(self.command('cancel'), payload=json.dumps(request).encode(), timeout=8)
            result = json.loads(raw, object_pairs_hook=unique_object)
            return result.get('cleanup') == 'confirmed'
        except (TransportError, ValueError, UnicodeError, AttributeError):
            return False

    def review(self, args, context, timeout):
        facts = self.preflight()
        request = json.loads(request_payload(context, {'model': args.model, 'max_turns': args.max_turns,
            'max_budget_usd': args.max_budget_usd, 'task': args.task}, self.run_id, self.profile, timeout))
        request.update(action='run', scripts=self.profile['guest_scripts'])
        saved = {}
        def stopped(signum, frame):
            self.cancelled = signum
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            saved[signum] = signal.signal(signum, stopped)
        try:
            with GuestLease(self.private, self.profile['guest']):
                try:
                    # Version/help/auth each have their own guest 5s boundary.
                    raw = self.invoke(self.command('run'), payload=json.dumps(request).encode(),
                                      timeout=min(timeout + 35, 585), cancellable=True)
                    report = json.loads(raw, object_pairs_hook=unique_object)
                    if not isinstance(report, dict) or report.get('schema_version') != 1:
                        raise TransportError('guest_result_invalid')
                    if 'review_outcome' not in report:
                        if report.get('execution_status') == 'conditions_missing':
                            confirmed = self.cancel()
                            return base_report('claude-code', {'execution_status': 'conditions_missing',
                                'backend_started': False, 'cleanup': 'confirmed' if confirmed else 'unverified',
                                'diagnostics': ['guest_preflight_unavailable']}, context, args.model)
                        raise TransportError('guest_result_invalid')
                    if report.get('backend') != 'claude-code':
                        raise TransportError('guest_backend_identity_invalid')
                    report['execution_environment']['guest'] = facts['guest']
                    return report
                except (TransportError, ValueError, UnicodeError, TypeError, KeyError) as error:
                    confirmed = self.cancel()
                    code = str(error) if isinstance(error, TransportError) else 'guest_result_invalid'
                    state = 'cancelled' if self.cancelled else 'timed_out' if code == 'transport_timed_out' else 'failed'
                    return base_report('claude-code', {'execution_status': state, 'backend_started': True,
                        'cleanup': 'confirmed' if confirmed else 'unverified', 'diagnostics': [code],
                        'execution_environment': {'kind': 'dedicated_linux_guest', 'guest': facts['guest']}}, context, args.model)
        finally:
            for signum, handler in saved.items():
                signal.signal(signum, handler)
