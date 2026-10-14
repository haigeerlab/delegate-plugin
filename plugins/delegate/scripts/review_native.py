#!/usr/bin/env python3
"""Optional Claude review on the current Mac; no guest or installation fallback."""
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import sys
import tempfile

from claude_review import execute
from review_context import write_snapshot
from review_execution import deadline
from review_isolation import build_policy
from review_macos import BoundaryError, MacBoundary
from review_result import base_report


def executable(name, variable):
    value = os.environ.get(variable) or shutil.which(name)
    if not value:
        raise BoundaryError('sandbox_runtime_missing' if name == 'srt' else name + '_cli_missing')
    path = Path(value)
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise BoundaryError('runtime_path_invalid')
    return path.resolve(strict=True)


def native_temporary(context, prefix):
    # srt binds a Unix proxy socket beneath TMPDIR. Darwin's long default
    # /var/folders path exceeds the socket pathname limit after its suffix.
    root = Path('/private/tmp').resolve(strict=True)
    repository = Path(context['repository']).resolve(strict=True)
    if root == repository or repository in root.parents:
        raise ValueError('temporary_directory_overlaps_repository')
    return Path(tempfile.mkdtemp(prefix=prefix, dir=root))


class NativeRunner:
    def __init__(self, root, context):
        if sys.platform != 'darwin':
            raise BoundaryError('macos_required')
        if os.environ.get('DELEGATE_CLAUDE_GUEST_CONFIG'):
            raise BoundaryError('guest_configuration_no_longer_supported')
        # Never silently ignore explicitly configured alternative authentication.
        if any(os.environ.get(name) for name in ('CLAUDE_CONFIG_DIR', 'ANTHROPIC_API_KEY',
                'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CODE_USE_BEDROCK',
                'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY', 'ANTHROPIC_BASE_URL')):
            raise BoundaryError('native_authentication_environment_unverified')
        self.claude = executable('claude', 'DELEGATE_CLAUDE_BIN')
        self.srt = executable('srt', 'DELEGATE_SRT_BIN')
        self.node = executable('node', 'DELEGATE_NODE_BIN')
        self.root = Path(root)
        self.context = context
        self.cancelled = None
        self.counter = 0
        self.snapshot, self.writable, self.control = [self.root / name for name in
            ('snapshot', 'writable', 'control')]
        for path in (self.snapshot, self.writable, self.control):
            path.mkdir(mode=0o700)
        data = self.snapshot / 'data'; data.mkdir(mode=0o700)
        write_snapshot(context, data)
        account = pwd.getpwuid(os.getuid())
        home = Path(account.pw_dir).resolve(strict=True)
        for path in (Path('/Library/Application Support/ClaudeCode/managed-settings.json'),
                Path('/Library/Application Support/ClaudeCode/managed-settings.d')):
            if path.exists():
                raise BoundaryError('native_managed_configuration_unverified')
        readable = [Path('/System'), Path('/usr'), Path('/bin').resolve(), Path('/sbin').resolve(),
                    Path('/dev'), self.claude]
        for path in (home / '.claude', home / '.claude.json', home / 'Library/Keychains',
                     Path('/private/etc/ssl/cert.pem')):
            if path.exists():
                readable.append(path.resolve(strict=True))
        self.policy = self.control / 'policy.json'
        self.policy.write_text(json.dumps(build_policy(snapshot=self.snapshot,
            writable=self.writable, home=home, protected=[self.control, Path(context['repository'])],
            readable=readable, allowed_domains=['api.anthropic.com:443', 'claude.ai:443', 'platform.claude.com:443'])))
        self.policy.chmod(0o600)
        self.environment = {'HOME': str(home), 'USER': account.pw_name, 'LOGNAME': account.pw_name,
            'PATH': str(self.node.parent) + ':/usr/bin:/bin', 'SHELL': '/bin/bash',
            'TMPDIR': str(self.writable), 'CLAUDE_CODE_TMPDIR': str(self.writable),
            'PYTHONDONTWRITEBYTECODE': '1', 'DELEGATE_REVIEW_DEPTH': '1',
            'DISABLE_AUTOUPDATER': '1', 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
            'DISABLE_TELEMETRY': '1', 'DISABLE_ERROR_REPORTING': '1',
            'ENABLE_CLAUDEAI_MCP_SERVERS': 'false', 'CLAUDE_CODE_DISABLE_ARTIFACT': '1',
            'CLAUDE_CODE_SKIP_PROMPT_HISTORY': '1'}
        # Deny reviewer Read/Glob/Grep access to authentication/runtime paths.
        # OS grants above serve the CLI and native helpers, not review context.
        if any(re.search(r'[()*?\[\]\r\n]', str(path)) for path in readable):
            raise BoundaryError('native_runtime_path_unsupported')
        self.tool_denials = ['Read(//%s%s)' % (str(path).lstrip('/'), suffix)
            for path in readable for suffix in ('', '/**')]

    def invoke(self, argv, *, deadline, stdin=None, runtime_probe=False):
        if self.cancelled:
            return {'execution_status': 'cancelled', 'cleanup': 'confirmed', 'stdout': b'',
                'backend_started': False, 'diagnostics': [], 'execution_environment': 'native'}
        if '-p' in argv:
            from claude_review import SETTINGS
            argv = list(argv)
            settings = dict(SETTINGS, permissions={'deny': self.tool_denials,
                'blockReadsOutsideWorkingDirectories': True})
            argv[argv.index('--settings') + 1] = json.dumps(settings, separators=(',', ':'))
        command = argv if runtime_probe else [str(self.srt), '--settings', str(self.policy), '--', *argv]
        control = self.control / str(self.counter); self.counter += 1
        control.mkdir(mode=0o700)
        boundary = MacBoundary(control)
        result = boundary.run(command, cwd=self.snapshot, environment=self.environment,
            deadline=deadline, stdin=stdin,
            expected_tools=self.context['allowed_tools'] if '-p' in argv else None)
        # Even with unknown cleanup, preserve only control facts, not raw
        # authentication, prompts, model streams or stderr as diagnostic files.
        # A surviving child may hold its unlinked descriptor until termination.
        for name in ('stdin', 'stdout', 'stderr'):
            (control / name).unlink(missing_ok=True)
        self.cancelled = result.get('cancel_signal')
        return result

    def runtime_preflight(self):
        for command in ([str(self.srt), '--version'], [str(self.node), '--version']):
            result = self.invoke(command, deadline=5, runtime_probe=True)
            output = result['stdout'].strip()
            match = re.fullmatch(rb'v([0-9]+)\.([0-9]+)\.([0-9]+)', output)
            supported = (output == b'0.0.79' if command[0] == str(self.srt) else
                bool(match and tuple(int(item) for item in match.groups()) >= (22, 12, 0)))
            if result['cleanup'] != 'confirmed':
                raise BoundaryError('runtime_cleanup_unverified')
            if result['execution_status'] == 'cancelled':
                raise BoundaryError('runtime_cancelled')
            if result['execution_status'] == 'timed_out':
                raise BoundaryError('runtime_timed_out')
            if result['execution_status'] != 'completed':
                diagnostic = next((code for code in result['diagnostics']
                    if re.fullmatch(r'[a-z][a-z0-9_]{0,79}', code)), 'sandbox_runtime_probe_failed')
                raise BoundaryError(diagnostic)
            if not supported:
                raise BoundaryError('sandbox_runtime_version_unverified')


def native_review(args, context):
    runner = None
    root = None
    report = None
    try:
        if not context['files']:
            raise BoundaryError('review_scope_unavailable')
        root = native_temporary(context, 'delegate-native.')
        runner = NativeRunner(root, context)
        runner.runtime_preflight()
        report = execute(str(runner.claude), args, context, runner.invoke, timeout=deadline())
        report['execution_environment'] = 'native'
        report['cleanup_scope'] = 'kernel_coalition'
        state = report['execution_status']
        status = (0 if state == 'completed' else 124 if state == 'timed_out' else
            128 + runner.cancelled if state == 'cancelled' and runner.cancelled else
            130 if state == 'cancelled' else 127 if state == 'conditions_missing' else 1)
        return report, status
    except (BoundaryError, OSError, ValueError) as error:
        code = str(error) if isinstance(error, BoundaryError) else 'native_environment_unavailable'
        state = {'runtime_cancelled': 'cancelled', 'runtime_timed_out': 'timed_out'}.get(code, 'conditions_missing')
        report = base_report('claude-code', {'execution_status': state, 'backend_started': False,
            'execution_environment': 'native',
            'cleanup': 'unverified' if code == 'runtime_cleanup_unverified' else 'confirmed',
            'diagnostics': [code]}, context, args.model)
        return report, 124 if state == 'timed_out' else 130 if state == 'cancelled' else 127
    finally:
        if root is not None:
            if report is not None and report['cleanup'] == 'unverified':
                # Preserve owned private control facts for a failed cleanup.
                # Bounded raw output is never returned as a diagnostic log.
                report['retained_control'] = str(root)
            else:
                shutil.rmtree(root)
