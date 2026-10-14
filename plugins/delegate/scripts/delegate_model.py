#!/usr/bin/env python3
"""Shared model checks for public and compatibility executor entries."""
import re
import sys


def model_error(backend, model):
    if not model:
        return None
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,199}(?:\[1m\])?', model):
        return 'invalid --model'
    normalized = model.lower().removesuffix('[1m]')
    # Recognize known families through provider namespaces without rewriting
    # the caller's slug or guessing the ownership of private model names.
    components = [re.sub(r'^(?:anthropic|openai)\.', '', part)
                  for part in re.split(r'[/@:]', normalized)]
    claude = any(part in ('sonnet', 'opus', 'haiku', 'fable', 'best', 'opusplan')
                 or part.startswith('claude-') for part in components)
    codex = any(part.startswith(('gpt-', 'codex', 'o1', 'o3', 'o4')) for part in components)
    if (backend == 'codex' and claude) or (backend == 'claude-code' and codex):
        return '--model belongs to the other backend'
    if backend == 'claude-code' and 'opusplan' in components:
        return 'claude-code review does not support automatic model-switching modes'
    return None


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('codex', 'claude-code'):
        sys.exit(64)
    error = model_error(sys.argv[1], sys.argv[2])
    if error:
        print('delegate: ' + error, file=sys.stderr)
        sys.exit(64)
