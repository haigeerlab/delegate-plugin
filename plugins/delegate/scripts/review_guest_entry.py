#!/usr/bin/env python3
"""Dedicated Linux guest controller; installed/configured by the operator.

No VM creation, CLI installation, credential import or login. The host pins
these source files before loading this entry. Control remains outside srt.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import stat
from types import SimpleNamespace

from claude_review import execute, unique_object
from review_guest import GuestLease, unpack_snapshot
from review_isolation import build_linux_policy
from review_service import ReviewService

ROOT = Path('/tmp/delegate-review-control')
DOMAINS = {'api.anthropic.com', 'claude.ai', 'platform.claude.com'}


def private_directory(path):
    path = Path(path)
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = path.lstat()
    if (not path.is_absolute() or path.resolve(strict=True) != path or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700):
        raise ValueError('private_guest_directory_untrusted')
    return path


def validate_runtime(configuration):
    fields = {'schema_version', 'claude', 'srt', 'node_bin', 'readable_paths', 'allowed_domains'}
    if (not isinstance(configuration, dict) or set(configuration) != fields
            or type(configuration['schema_version']) is not int or configuration['schema_version'] != 1):
        raise ValueError('guest_runtime_invalid')
    for key in ('claude', 'srt', 'node_bin'):
        value = configuration[key]
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError('guest_runtime_path_invalid')
        path = Path(value).resolve(strict=True)
        if (key == 'node_bin' and not path.is_dir()) or (key != 'node_bin' and (not path.is_file() or not os.access(path, os.X_OK))):
            raise ValueError('guest_runtime_path_invalid')
        configuration[key] = str(path)
    readable = configuration['readable_paths']
    if (not isinstance(readable, list) or len(readable) > 32
            or any(not isinstance(path, str) or not Path(path).is_absolute()
                   or path in ('/', '/tmp', '/home', '/run', '/sys', '/etc') for path in readable)):
        raise ValueError('guest_runtime_reads_invalid')
    domains = configuration['allowed_domains']
    if not isinstance(domains, list) or not domains or not set(domains) <= DOMAINS or len(domains) != len(set(domains)):
        raise ValueError('guest_provider_network_unverified')
    configuration['allowed_domains'] = [domain + ':443' for domain in domains]
    return configuration


def _read_regular(path, limit):
    path = Path(path)
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('guest_file_path_untrusted')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as source:
        metadata = os.fstat(source.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError('guest_file_untrusted')
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError('guest_file_limit')
    return data


def cancel_request(request, *, action='cancel', root=ROOT):
    if (action != 'cancel' or not isinstance(request, dict) or set(request) != {'run_id'}
            or not isinstance(request['run_id'], str) or not re.fullmatch(r'[0-9a-f]{32}', request['run_id'])):
        raise ValueError('guest_cancel_request_invalid')
    root = private_directory(root)
    run = root / ('run-' + request['run_id'])
    if not run.exists():
        return {'execution_status': 'cancelled', 'cleanup': 'unverified', 'diagnostics': ['guest_run_not_observed']}
    control = private_directory(run / 'control')
    marker = control / 'cancel'
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(fd)
    except FileExistsError:
        _read_regular(marker, 0)
    try:
        unit = _read_regular(control / 'active.unit', 100).decode('ascii')
    except (OSError, ValueError, UnicodeError):
        return {'execution_status': 'cancelled', 'cleanup': 'unverified', 'diagnostics': ['guest_unit_not_observed']}
    if not re.fullmatch(r'delegate-review-[0-9a-f]{32}\.service', unit):
        raise ValueError('guest_unit_identity_invalid')
    boundary = ReviewService(manager='/usr/bin/systemctl')
    boundary.unit = unit
    boundary.control = control
    return boundary.finish(exit_code=None, reason='cancelled')


def run_request(request):
    if platform.system() != 'Linux' or platform.machine() != 'aarch64':
        raise ValueError('guest_platform_unsupported')
    fields = {'schema_version', 'run_id', 'context', 'snapshot', 'arguments', 'timeout',
              'runtime_config', 'runtime_sha256', 'code_sha256'}
    if (not isinstance(request, dict) or set(request) != fields
            or type(request['schema_version']) is not int or request['schema_version'] != 1
            or not isinstance(request['run_id'], str) or not re.fullmatch(r'[0-9a-f]{32}', request['run_id'])
            or type(request['timeout']) is not int or not 1 <= request['timeout'] <= 540):
        raise ValueError('guest_review_request_invalid')
    raw = _read_regular(request['runtime_config'], 65536)
    if hashlib.sha256(raw).hexdigest() != request['runtime_sha256']:
        raise ValueError('guest_runtime_digest_changed')
    configuration = validate_runtime(json.loads(raw, object_pairs_hook=unique_object))
    for path in (Path('/etc/claude-code/managed-settings.json'), Path('/etc/claude-code/managed-settings.d')):
        if path.exists():
            raise ValueError('guest_managed_configuration_unverified')
    arguments = request['arguments']
    if (not isinstance(arguments, dict) or set(arguments) != {'model', 'max_turns', 'max_budget_usd', 'task'}
            or type(arguments['max_turns']) is not int or arguments['max_turns'] < 1
            or not isinstance(arguments['task'], str) or len(arguments['task']) > 65536):
        raise ValueError('guest_arguments_invalid')
    context = request['context']
    if (not isinstance(context, dict) or 'files' in context
            or not isinstance(context.get('allowed_tools'), list) or not context['allowed_tools']
            or any(tool not in ('Read', 'Glob', 'Grep') for tool in context['allowed_tools'])):
        raise ValueError('guest_context_invalid')
    root = private_directory(ROOT)
    run = root / ('run-' + request['run_id'])
    with GuestLease(root, 'review'):
        run.mkdir(mode=0o700)
        for name in ('snapshot', 'control', 'writable'):
            (run / name).mkdir(mode=0o700)
        data = run / 'snapshot/data'; data.mkdir(mode=0o700)
        context = dict(context)
        records = request['snapshot']
        paths = unpack_snapshot(json.dumps(records).encode(), data)
        context['files'] = {name: (data / name).read_bytes() for name in paths}
        if context['file_sha256'] != {name: hashlib.sha256(content).hexdigest() for name, content in context['files'].items()}:
            raise ValueError('guest_snapshot_manifest_mismatch')
        home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve(strict=True)
        environment = {'HOME': str(home), 'PATH': configuration['node_bin'] + ':/usr/bin:/bin',
            'SHELL': '/bin/bash', 'TMPDIR': str(run / 'writable'), 'CLAUDE_CODE_TMPDIR': str(run / 'writable'),
            'PYTHONDONTWRITEBYTECODE': '1', 'DELEGATE_REVIEW_DEPTH': '1', 'DISABLE_AUTOUPDATER': '1',
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1', 'DISABLE_TELEMETRY': '1',
            'DISABLE_ERROR_REPORTING': '1', 'ENABLE_CLAUDEAI_MCP_SERVERS': 'false',
            'CLAUDE_CODE_DISABLE_ARTIFACT': '1', 'CLAUDE_CODE_SKIP_PROMPT_HISTORY': '1'}
        os.environ.clear()
        os.environ.update(HOME=str(home), PATH='/usr/bin:/bin', USER=pwd.getpwuid(os.getuid()).pw_name,
            XDG_RUNTIME_DIR='/run/user/%s' % os.getuid(),
            DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/%s/bus' % os.getuid())
        control = run / 'control'
        readable = [Path(value).resolve(strict=True) for value in configuration['readable_paths']]
        readable += [Path('/usr'), Path(configuration['claude']), Path(__file__).with_name('review_network.py')]
        for path in (Path('/etc/ld.so.cache'), Path('/etc/hosts'), Path('/etc/nsswitch.conf'),
                     Path('/etc/resolv.conf'), Path('/etc/ssl/certs'), home / '.claude', home / '.claude.json'):
            if path.exists():
                readable.append(path.resolve(strict=True))
        policy = build_linux_policy(snapshot=run / 'snapshot', writable=run / 'writable', home=home,
            protected=[control, Path(request['runtime_config']).resolve(strict=True)],
            readable=readable, allowed_domains=configuration['allowed_domains'])
        policy_path = control / 'policy.json'; policy_path.write_text(json.dumps(policy)); policy_path.chmod(0o600)
        def invoke(argv, *, deadline, stdin=None):
            boundary = ReviewService(manager='/usr/bin/systemctl')
            active = control / 'active.unit'
            temporary = control / 'active.unit.tmp'
            with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'w') as output:
                output.write(boundary.unit)
            os.replace(temporary, active)
            if (control / 'cancel').exists():
                return {'execution_status': 'cancelled', 'cleanup': 'confirmed', 'stdout': b'', 'diagnostics': []}
            wrapped = [configuration['srt'], '--settings', str(policy_path), '--', '/usr/bin/python3', '-B',
                str(Path(__file__).with_name('review_network.py')), '--', *argv]
            return boundary.run('/usr/bin/systemd-run', wrapped, deadline=deadline,
                environment=environment, cwd=run / 'snapshot', control=control, stdin=stdin,
                expected_tools=context['allowed_tools'] if '-p' in argv else None,
                cancel_marker=control / 'cancel')
        report = None
        for command in ([configuration['srt'], '--version'],
                        [str(Path(configuration['node_bin']) / 'node'), '--version']):
            probe = invoke(command, deadline=5)
            output = probe['stdout'].strip()
            node_match = re.fullmatch(rb'v([0-9]+)\.([0-9]+)\.([0-9]+)', output)
            supported = (output == b'0.0.79' if command[0] == configuration['srt'] else
                         bool(node_match and tuple(int(part) for part in node_match.groups()) >= (22, 12, 0)))
            if probe['execution_status'] != 'completed' or probe['cleanup'] != 'confirmed' or not supported:
                from review_result import base_report
                state = probe['execution_status'] if probe['execution_status'] in ('cancelled', 'timed_out') else 'conditions_missing'
                report = base_report('claude-code', {'execution_status': state, 'backend_started': False,
                    'cleanup': probe['cleanup'], 'diagnostics': ['sandbox_runtime_version_unverified']}, context, arguments['model'])
                break
        if report is None:
            report = execute(configuration['claude'], SimpleNamespace(**arguments), context, invoke, timeout=request['timeout'])
        report['execution_environment'] = {'kind': 'dedicated_linux_guest', 'os': platform.system(), 'arch': platform.machine()}
        # Unknown cleanup must preserve owned control evidence for diagnosis.
        if report['cleanup'] == 'confirmed':
            shutil.rmtree(run)
        return report
