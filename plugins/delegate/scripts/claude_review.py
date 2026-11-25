#!/usr/bin/env python3
"""Claude checks executed only through a caller's enforcing process boundary.

This adapter never discovers a CLI or reads credentials itself.
The 2.1.295 minimum is the inspected compatibility baseline, not a claim about
which release first introduced each flag. Model calls remain a separate gate.
"""
import json
from pathlib import PurePosixPath
import re

MINIMUM_VERSION = (2, 1, 295)
VISIBLE_FLAGS = ('--safe-mode', '--restricted', '--permission-mode', '--permission-prompts',
                 '--tools', '--disable-slash-commands', '--strict-mcp-config', '--mcp-config',
                 '--no-chrome', '--no-session-persistence', '--output-format', '--json-schema',
                 '--max-budget-usd', '--settings')
SAFE_PREFIX = ('--safe-mode', '--restricted', '--strict-mcp-config',
               '--mcp-config', '{"mcpServers":{}}', '--disable-slash-commands', '--no-chrome')
SETTINGS = {'disableAllHooks': True, 'disableClaudeAiConnectors': True, 'enableArtifact': False,
            'disableWorkflows': True, 'disableBundledSkills': True,
            'switchModelsOnFlag': False, 'fallbackModel': []}


# Per-probe deadline (spec/claude-review.md, 2026-11-26): 5 s misjudged occasional slow CLI starts.
PROBE_DEADLINE = 15


class PreflightError(Exception):
    """Fixed diagnostic code only; probe output is never echoed."""

    def __init__(self, code, *, stage=None):
        super().__init__(code)
        self.stage = stage


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def _probe(invoker, argv, *, stage, authentication=False):
    try:
        result = invoker(argv, deadline=PROBE_DEADLINE)
    except OSError:
        raise PreflightError('probe_unavailable', stage=stage) from None
    if not isinstance(result, dict) or result.get('cleanup') != 'confirmed':
        raise PreflightError('probe_cleanup_unverified', stage=stage)
    state = result.get('execution_status')
    if state != 'completed':
        # Original auth status exits nonzero when logged out. Only its bounded,
        # explicit false field gets this diagnosis; no failed probe authorizes
        # a model even if its output claims to be logged in.
        output = result.get('stdout')
        if state == 'failed' and authentication and isinstance(output, bytes) and len(output) <= 65536:
            try:
                value = json.loads(output, object_pairs_hook=unique_object)
                if isinstance(value, dict) and value.get('loggedIn') is False:
                    raise PreflightError('authentication_missing')
            except (ValueError, UnicodeError):
                pass
        code = {'timed_out': 'probe_timed_out', 'cancelled': 'probe_cancelled'}.get(state, 'probe_failed')
        raise PreflightError(code, stage=stage)
    output = result.get('stdout')
    if not isinstance(output, bytes) or len(output) > 65536:
        raise PreflightError('probe_output_invalid', stage=stage)
    return output


def preflight(executable, invoker):
    path = PurePosixPath(executable)
    if (not isinstance(executable, str) or not path.is_absolute()
            or str(path) != executable or '..' in path.parts or '\0' in executable):
        raise PreflightError('cli_path_invalid')
    prefix = [executable, *SAFE_PREFIX]
    version = _probe(invoker, prefix + ['--version'], stage='probe_stage_version')
    match = re.fullmatch(rb'(\d+)\.(\d+)\.(\d+)(?: \(Claude Code\))?\s*', version)
    if not match or tuple(int(part) for part in match.groups()) < MINIMUM_VERSION:
        raise PreflightError('cli_version_unsupported')
    help_text = _probe(invoker, prefix + ['--help'], stage='probe_stage_help')
    flags = set(re.findall(rb'--[a-z][a-z-]*', help_text))
    # Hidden flags (notably --max-turns) use the documented fixed baseline.
    if not all(flag.encode() in flags for flag in VISIBLE_FLAGS):
        raise PreflightError('cli_capability_missing')
    try:
        auth = json.loads(_probe(invoker, prefix + ['auth', 'status', '--json'], stage='probe_stage_auth', authentication=True), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError):
        raise PreflightError('authentication_output_invalid') from None
    if not isinstance(auth, dict) or type(auth.get('loggedIn')) is not bool:
        raise PreflightError('authentication_output_invalid')
    if not auth['loggedIn']:
        raise PreflightError('authentication_missing')
    # Only known first-party fields are accepted. Unknown/third-party methods
    # never widen the network policy or switch authentication automatically.
    if auth.get('authMethod') == 'third_party' or auth.get('apiProvider') != 'firstParty':
        raise PreflightError('provider_unverified')
    if auth.get('authMethod') not in ('claude.ai', 'oauth_token', 'api_key'):
        raise PreflightError('authentication_method_unverified')
    return {'version': '.'.join(part.decode() for part in match.groups()),
            'auth_method': auth['authMethod'], 'provider': auth['apiProvider']}


def execute(executable, args, context, invoker, *, timeout):
    """Invoke the original CLI through the supplied enforcing boundary.

    A fake invoker verifies adapter behavior only. The public entry must supply
    a validated native Mac boundary; no backend fallback is permitted.
    """
    from review_context import task_prompt
    from review_result import schema_for_context, base_report, claude_report
    if type(timeout) is not int or not 1 <= timeout <= 540:
        raise ValueError('invalid review deadline')
    try:
        conditions = preflight(executable, invoker)
    except PreflightError as error:
        state = {'probe_timed_out': 'timed_out', 'probe_cancelled': 'cancelled'}.get(str(error), 'conditions_missing')
        diagnostics = [str(error)]
        if error.stage is not None:
            diagnostics.append(error.stage)
        return base_report('claude-code', {'execution_status': state, 'backend_started': False,
            'cleanup': 'unverified' if str(error) in ('probe_cleanup_unverified', 'probe_unavailable') else 'confirmed',
            'diagnostics': diagnostics}, context, args.model)
    command = [executable, *SAFE_PREFIX, '-p', '--permission-mode', 'dontAsk',
        '--permission-prompts', 'none', '--tools', ','.join(context['allowed_tools']),
        '--disallowedTools', 'Bash,PowerShell,REPL,Edit,Write,NotebookEdit,WebFetch,WebSearch,Agent,Skill,mcp__*',
        '--no-session-persistence', '--output-format', 'stream-json', '--verbose',
        '--max-turns', str(args.max_turns), '--settings', json.dumps(SETTINGS, separators=(',', ':')),
        '--json-schema', json.dumps(schema_for_context(context), separators=(',', ':'))]
    if args.model is not None:
        command += ['--model', args.model]
    if args.max_budget_usd is not None:
        command += ['--max-budget-usd', args.max_budget_usd]
    prompt = task_prompt(args.task, context) + '\nSnapshot files are under data/<original path>. Findings use original paths.'
    try:
        execution = invoker(command, deadline=timeout, stdin=prompt.encode('utf-8'))
    except OSError:
        execution = {'execution_status': 'failed', 'cleanup': 'unverified', 'stdout': b'',
                     'diagnostics': ['claude_execution_unavailable']}
    report = claude_report(execution.get('stdout'), execution, context, requested_model=args.model)
    diagnostics = []
    if execution.get('stdout_check') == 'missing':
        diagnostics.append('stream_file_missing')
    elif execution.get('stdout_check') == 'short':
        diagnostics.append('stream_read_short')
    if report['execution_status'] != 'completed':
        exit_code = execution.get('launcher_exit_code')
        stderr_bytes = execution.get('stderr_bytes')
        # Timed out or cancelled backends were reaped by us; their nonzero
        # exit says nothing about the original CLI.
        if report['execution_status'] == 'failed' and type(exit_code) is int and exit_code != 0:
            diagnostics.append('backend_exit_nonzero')
        if type(stderr_bytes) is int and stderr_bytes > 0:
            diagnostics.append('backend_stderr_nonempty')
    for code in diagnostics:
        if code not in report['diagnostics']:
            report['diagnostics'].append(code)
    report['cli_version'] = conditions['version']
    report['authentication'] = {'method': conditions['auth_method'], 'provider': conditions['provider']}
    return report
