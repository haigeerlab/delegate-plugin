#!/usr/bin/env python3
"""Check YAML frontmatter of plugin commands, skills and agents.

Rules follow anthropics/claude-plugins-official validate-frontmatter: every
file needs a parsable frontmatter block with a string `description`; skills and
agents also need a string `name` (a command's name comes from its file name).
Requires PyYAML; CI installs it before running this script.
"""
from pathlib import Path
import sys

import yaml


def kind(path):
    parts = path.parts
    if path.name == 'SKILL.md' and 'skills' in parts:
        return 'skill'
    if path.parent.name == 'commands':
        return 'command'
    if path.parent.name == 'agents':
        return 'agent'
    return None


def frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        raise ValueError('missing frontmatter block')
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            data = yaml.safe_load('\n'.join(lines[1:index]))
            if not isinstance(data, dict):
                raise ValueError('frontmatter is not a mapping')
            return data
    raise ValueError('unterminated frontmatter block')


def problems(path):
    try:
        data = frontmatter(path.read_text(encoding='utf-8'))
    except (ValueError, yaml.YAMLError) as error:
        return ['frontmatter: %s' % str(error).splitlines()[0]]
    required = ['description'] if kind(path) == 'command' else ['name', 'description']
    return ['missing or non-string %r' % field for field in required
            if not isinstance(data.get(field), str) or not data[field].strip()]


def main(root):
    files = [path for path in sorted(Path(root, 'plugins').glob('*/**/*.md')) if kind(path)]
    failed = 0
    for path in files:
        for problem in problems(path):
            print('%s: %s' % (path.relative_to(root), problem))
            failed = 1
    if not files:
        print('no command, skill or agent files found')
        return 1
    if not failed:
        print('frontmatter: ok (%d files)' % len(files))
    return failed


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
