#!/usr/bin/env python3
"""CLAUDE.md and AGENTS.md must carry identical shared sections (standard G2).

A shared section sits between `<!-- shared:begin -->` and `<!-- shared:end -->`;
everything outside the markers is host-specific and may differ.
"""
from pathlib import Path
import re
import sys

BLOCK = re.compile(r'<!-- shared:begin -->\n(.*?)<!-- shared:end -->', re.S)
FILES = ('CLAUDE.md', 'AGENTS.md')


def main(root):
    blocks = {}
    for name in FILES:
        text = Path(root, name).read_text(encoding='utf-8')
        if text.count('<!-- shared:begin -->') != text.count('<!-- shared:end -->'):
            print('shared-sections: %s has unbalanced markers' % name)
            return 1
        blocks[name] = BLOCK.findall(text)
    if not blocks[FILES[0]]:
        print('shared-sections: %s has no shared section' % FILES[0])
        return 1
    if blocks[FILES[0]] != blocks[FILES[1]]:
        print('shared-sections: %s and %s differ inside the shared markers' % FILES)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
