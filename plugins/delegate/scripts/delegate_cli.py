#!/usr/bin/env python3
"""Purpose-based commands, retaining the original no-subcommand CLI."""
import os
import json
from pathlib import Path
import re
import sys

import delegate_backend as backend
from delegate_capabilities import BACKENDS, describe
from review_context import ContextError, STOPS, capture, capture_document, git, names, selected

HELP = '''用法：delegate-exec.sh review|run [选项] [--] [任务]
review：两个后端的只读审查，--backend 默认为 codex。
run：既有 Codex 通用委托；写入须明确 --write。
高级审查输入：review --context <JSON>；旧 CLI --review-context 保留。
review 范围：--paths <仓库相对路径>（可重复），--module <名称>（需 paths）；
             --base <提交> [--head <提交，默认 HEAD>] 或 --changes staged|unstaged|working-tree。
             --exclude / --spec / --plan / --criterion 可重复；--repo <仓库>；
             --include-untracked 仅用于 working-tree；--dry-run 只预览，不调用模型。
paths/module 默认读取 HEAD，工作区版本须显式 --changes；context 与快捷范围选项互斥。
Codex review 直接附带已校验文件内容，序列化输入上限 1 MiB；超限不启动模型。
能力（下方 --review-context 是旧 CLI 名称；review 使用 --context 或范围快捷参数）：
''' + describe() + '\n'


def review_arguments(options):
    bounded = options[:options.index('--')] if '--' in options else options
    for flag in ('--backend', '--model', '--effort', '--max-turns', '--max-budget-usd',
                 '--context', '--repo', '--base', '--head', '--changes', '--module', '--dry-run', '--include-untracked'):
        if sum(value == flag or value.startswith(flag + '=') for value in bounded) > 1:
            raise backend.ArgumentError('duplicate option: ' + flag)
    parser = backend.Parser(add_help=False, allow_abbrev=False)
    parser.add_argument('--backend', choices=tuple(BACKENDS), default='codex')
    for flag in ('--model', '--effort', '--max-turns', '--max-budget-usd', '--context',
                 '--repo', '--base', '--head', '--changes', '--module'):
        parser.add_argument(flag)
    for flag in ('--paths', '--exclude', '--spec', '--plan', '--criterion'):
        parser.add_argument(flag, action='append', default=[])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--include-untracked', action='store_true')
    parser.add_argument('task', nargs='?', default='只读审查指定范围，报告有证据的问题、未审范围及未验证内容。')
    args = parser.parse_args(options)
    if any(getattr(args, name) == '' for name in ('model', 'effort', 'max_turns', 'max_budget_usd',
                                                 'context', 'repo', 'base', 'head', 'changes', 'module')):
        raise backend.ArgumentError('option values must not be empty')
    if args.context and any((args.repo is not None, args.paths, args.exclude, args.spec, args.plan,
                             args.criterion, args.base is not None, args.head is not None,
                             args.changes is not None, args.module is not None, args.include_untracked)):
        raise backend.ArgumentError('--context cannot be combined with scope shortcuts')
    if not args.context:
        if args.head is not None and args.base is None:
            raise backend.ArgumentError('--head requires --base')
        if args.base is not None and args.changes is not None:
            raise backend.ArgumentError('--base and --changes are mutually exclusive')
        if args.changes is not None and args.changes not in ('staged', 'unstaged', 'working-tree'):
            raise backend.ArgumentError('unsupported --changes')
        if args.module is not None and (not args.paths or args.base is not None):
            raise backend.ArgumentError('--module requires --paths and cannot use commit diff')
        if args.include_untracked and args.changes != 'working-tree':
            raise backend.ArgumentError('--include-untracked requires --changes working-tree')
        if not args.paths and args.base is None and args.changes is None:
            raise backend.ArgumentError('review requires --paths, --base, --changes or --context')
    forwarded = ['--backend', args.backend, '--review-context', args.context or '(scope shortcuts)']
    for flag in ('--model', '--effort', '--max-turns', '--max-budget-usd'):
        value = getattr(args, flag[2:].replace('-', '_'))
        if value is not None:
            forwarded.extend((flag, value))
    forwarded.extend(('--', args.task))
    checked = backend.parse(forwarded)  # Validate executor-specific options before reading the repository.
    args.max_turns = checked.max_turns
    return args, forwarded


def scope_document(args):
    working = Path(args.repo or Path.cwd()).resolve(strict=True)
    root = git(working, 'rev-parse', '--show-toplevel').decode().strip()
    changes = args.changes
    flags = {'staged': changes in ('staged', 'working-tree'),
             'unstaged': changes in ('unstaged', 'working-tree'), 'untracked': args.include_untracked}
    diff_options = ['diff', '--no-ext-diff', '--no-textconv', '--no-renames']
    if changes:
        baseline = {'mode': changes}
        diff_options += ['--cached'] if changes == 'staged' else ['HEAD'] if changes == 'working-tree' else []
    else:
        refs = [args.base or 'HEAD', args.head or 'HEAD']
        if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/~^+-]{0,199}', ref) for ref in refs):
            raise ContextError('baseline_ref_invalid')
        resolved = [git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip() for ref in refs]
        baseline = {'mode': 'commits', 'from': resolved[0], 'to': resolved[1]}
        diff_options += resolved
    include = args.paths
    if not include:
        include = names(git(root, *diff_options, '--name-only', '-z', '--'))
        if args.include_untracked:
            include = sorted(set(include + names(git(root, 'ls-files', '--others', '--exclude-standard', '-z', '--'))))
        if not include:
            raise ContextError('diff_has_no_changes')
    kind = 'diff' if args.base is not None or not args.paths else 'module' if args.module else 'paths'
    scope = {'include': include, 'exclude': args.exclude}
    if kind == 'module':
        scope['module'] = args.module
    return {'schema_version': 1, 'repository': root, 'working_directory': str(working),
            'review_type': kind, 'scope': scope, 'baseline': baseline,
            'context_files': args.spec + args.plan, 'acceptance_criteria': args.criterion,
            'uncommitted_changes': flags, 'allowed_tools': ['Read'], 'stop_conditions': sorted(STOPS)}


def review(options):
    args, forwarded = review_arguments(options)
    context = None
    try:
        context = capture(args.context) if args.context else capture_document(scope_document(args))
        if args.dry_run:
            from review_execution import CODEX_PROMPT_LIMIT, codex_prompt, deadline
            preview = {key: context[key] for key in ('repository', 'working_directory', 'review_type',
                'scope', 'baseline', 'context_files', 'acceptance_criteria', 'uncommitted_changes',
                'allowed_tools', 'stop_conditions', 'head', 'diff_sha256', 'file_sha256', 'unreviewed',
                'dirty', 'repository_dirty')}
            preview.update(kind='review_preview', backend=args.backend, backend_started=False,
                           host='unknown', requested_model=args.model, observed_models=[],
                           capabilities=BACKENDS[args.backend], permission='read-only',
                           timeout_seconds=deadline(), backend_preflight='not_performed')
            preview['requested_effort'] = args.effort
            preview['requested_limits'] = ({'max_turns': args.max_turns, 'max_budget_usd': args.max_budget_usd}
                                           if args.backend == 'claude-code' else {})
            preview['input_transport'] = 'inline_files' if args.backend == 'codex' else 'snapshot_read_tools'
            if args.backend == 'codex':
                preview['prompt_bytes'] = len(codex_prompt(args.task, context).encode('utf-8'))
                preview['max_prompt_bytes'] = CODEX_PROMPT_LIMIT
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        if not any(selected(name, context['scope']) for name in context['files']):
            raise ContextError('scope_has_no_reviewable_files')
    except (ContextError, ValueError, OSError, RuntimeError) as error:
        reason = str(error) if isinstance(error, ContextError) else 'review_environment_unavailable'
        return backend.context_failure(args.backend, args.model, reason, context)
    return backend.main(forwarded, review_context=context)


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if os.environ.get('DELEGATE_REVIEW_DEPTH', '0') != '0':
        print('delegate: recursive delegation is not supported.', file=sys.stderr)
        return 64
    if arguments in (['--help'], ['-h']):
        print(HELP + '\n' + backend.HELP, end='')
        return 0
    if not arguments or arguments[0] not in ('review', 'run'):
        return backend.main(arguments)
    command, options = arguments[0], arguments[1:]
    if options in (['--help'], ['-h']):
        print(HELP, end='')
        return 0
    try:
        if command == 'run':
            args = backend.parse(options)
            if not BACKENDS[args.backend]['run']:
                raise backend.ArgumentError(args.backend + ' does not support run; use review')
            if args.review_context is not None:
                raise backend.ArgumentError('run does not accept --review-context; use review --context')
            return backend.main(options)
        return review(options)
    except backend.ArgumentError as error:
        print(backend.argument_message(error), file=sys.stderr)
        return 64


if __name__ == '__main__':
    sys.exit(main())
