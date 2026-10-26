#!/usr/bin/env python3
"""Explicit executor selection, independent of the parent session host."""
import argparse
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import sys
from delegate_capabilities import BACKENDS
from delegate_model import model_error

SCRIPTS = Path(__file__).resolve().parent
HELP = '''用法：delegate-exec.sh [--backend codex|claude-code] [选项] [--] <任务>
默认后端：codex；主会话宿主无法核实时显示 unknown。
共同选项：--model <slug> --review-context <JSON 文件>
Codex：--write --effort none|minimal|low|medium|high|xhigh
      --resumable（可续跑）；--resume <runId> 带用户答复续跑
Claude Code：必须提供 --review-context；--max-turns <正整数>（默认 12）
             --max-budget-usd <正数>；不支持 --write 或 --effort。
Claude 审查目前仅支持 Mac 本机 CLI + srt 0.0.79；条件不足不会切换后端。
'''


class ArgumentError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(message)


def parse(arguments):
    # Duplicate selectors are errors rather than a silent last-option override.
    options = arguments[:arguments.index('--')] if '--' in arguments else arguments
    for flag in ('--backend', '--model', '--effort', '--review-context', '--max-turns', '--max-budget-usd', '--resume'):
        if sum(a == flag or a.startswith(flag + '=') for a in options) > 1:
            raise ArgumentError('duplicate option: ' + flag)
    parser = Parser(add_help=False, allow_abbrev=False)
    parser.add_argument('--backend', choices=tuple(BACKENDS), default='codex')
    parser.add_argument('--model')
    parser.add_argument('--effort', choices=('none', 'minimal', 'low', 'medium', 'high', 'xhigh'))
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--resumable', action='store_true')
    parser.add_argument('--resume')
    parser.add_argument('--review-context')
    parser.add_argument('--max-turns')
    parser.add_argument('--max-budget-usd')
    parser.add_argument('task')
    result = parser.parse_args(arguments)
    if not result.task.strip() or len(result.task) > 65536 or '\0' in result.task:
        raise ArgumentError('empty or oversized task')
    for flag in ('--effort', '--max-turns', '--max-budget-usd'):
        if getattr(result, flag[2:].replace('-', '_')) is not None and flag not in BACKENDS[result.backend]['options']:
            raise ArgumentError(result.backend + ' does not support ' + flag)
    if result.write and not BACKENDS[result.backend]['write']:
        raise ArgumentError(result.backend + ' does not support --write')
    if (result.resumable or result.resume is not None) and not BACKENDS[result.backend]['resume']:
        raise ArgumentError(result.backend + ' does not support --resumable or --resume')
    if result.resume is not None and (result.resumable or result.model is not None or result.effort is not None
                                      or result.review_context is not None):
        raise ArgumentError('--resume cannot be combined with --resumable, --model, --effort or --review-context')
    if result.resumable and result.review_context is not None:
        raise ArgumentError('--resumable cannot be combined with --review-context')
    error = model_error(result.backend, result.model)
    if error:
        raise ArgumentError(error)
    if result.backend == 'claude-code':
        if not result.review_context:
            raise ArgumentError('claude-code requires --review-context')
        turns = result.max_turns or '12'
        if not turns.isascii() or not turns.isdecimal() or not 1 <= int(turns) <= 2147483647:
            raise ArgumentError('--max-turns must be a positive integer')
        result.max_turns = int(turns)
        if result.max_budget_usd is not None:
            try:
                budget = Decimal(result.max_budget_usd)
            except InvalidOperation:
                raise ArgumentError('--max-budget-usd must be a positive finite number') from None
            if not budget.is_finite() or budget <= 0:
                raise ArgumentError('--max-budget-usd must be a positive finite number')
    if result.write and result.review_context:
        raise ArgumentError('--review-context is read-only and cannot use --write')
    return result


def context_failure(backend, model, diagnostic, context=None):
    from review_result import base_report, render
    if context is None:
        context = {'scope': {'state': 'unknown'}, 'baseline': {}, 'diff_sha256': None,
                   'files': {}, 'file_sha256': {}, 'unreviewed': [{'path': 'unknown', 'reason': diagnostic}]}
    report = base_report(backend, {'execution_status': 'conditions_missing',
        'backend_started': False, 'cleanup': 'confirmed', 'diagnostics': [diagnostic]}, context, model)
    print(render(report), end='')
    return 127


def main(arguments=None, *, review_context=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if os.environ.get('DELEGATE_REVIEW_DEPTH', '0') != '0':
        print('delegate: recursive delegation is not supported.', file=sys.stderr)
        return 64
    if arguments in (['--help'], ['-h']):
        print(HELP, end='')
        return 0
    try:
        args = parse(arguments)
    except ArgumentError as error:
        print('delegate: ' + str(error), file=sys.stderr)
        return 64
    print('delegate: host=unknown backend=' + args.backend + ' model=unknown', file=sys.stderr)
    if args.backend == 'codex' and args.review_context is None:
        forwarded = []
        if args.write:
            forwarded.append('--write')
        if args.resumable:
            forwarded.append('--resumable')
        if args.resume is not None:
            forwarded.extend(('--resume', args.resume))
        for flag, value in (('--model', args.model), ('--effort', args.effort)):
            if value is not None:
                forwarded.extend((flag, value))
        os.execv('/bin/bash', ['/bin/bash', str(SCRIPTS / 'codex-exec.sh'), *forwarded, '--', args.task])
    if args.review_context is not None:
        from review_context import ContextError, capture
        from review_execution import codex_review, save_artifacts
        from review_result import base_report, render
        try:
            context = capture(args.review_context) if review_context is None else review_context
        except (ContextError, ValueError, OSError) as error:
            diagnostic = str(error) if isinstance(error, ContextError) else 'review_environment_unavailable'
            return context_failure(args.backend, args.model, diagnostic)
        try:
            if args.backend == 'codex':
                report, status = codex_review(args, context)
            else:
                from review_native import native_review
                report, status = native_review(args, context)
        except (ContextError, ValueError, OSError) as error:
            diagnostic = str(error) if isinstance(error, ContextError) else 'review_environment_unavailable'
            report = base_report(args.backend, {'execution_status': 'conditions_missing',
                'backend_started': False, 'cleanup': 'confirmed', 'diagnostics': [diagnostic]}, context, args.model)
            status = 127
        try:
            artifacts = save_artifacts(report, context)
            print('delegate: artifacts=' + artifacts['report'], file=sys.stderr)
        except (ValueError, OSError):
            report['diagnostics'].append('artifact_write_failed')
            if report['execution_status'] == 'completed':
                report['execution_status'] = 'failed'
                report['review_outcome'] = 'inconclusive'
                status = 1
        print('delegate: status=' + report['execution_status'] + ' backend=' + args.backend
              + ' started=' + str(report.get('backend_started', False)).lower()
              + ' reviewed=' + str(len(report['reviewed'])) + '/' + str(len(context['files']))
              + ' unreviewed=' + str(len(report['unreviewed']))
              + ' usage=' + ('reported' if 'usage' in report else 'unknown'), file=sys.stderr)
        print(render(report), end='')
        return status
    return 64


if __name__ == '__main__':
    sys.exit(main())
