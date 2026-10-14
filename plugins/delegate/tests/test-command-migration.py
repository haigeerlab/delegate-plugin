#!/usr/bin/env python3
"""Guard the rendered UTF-8 size of legacy command migration, without a CLI.

Codex rust-v0.162.1 skips rendered command skills larger than 4,000 bytes:
https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/command_migration/plugin.rs
The wrapper below matches that release's render_command_skill format. Its
output was checked byte-for-byte against three actual native migration results.
This check does not establish installation or host command usability.
"""
import json
from pathlib import Path
import re
import unittest

COMMANDS = Path(__file__).resolve().parents[1] / 'commands'
LIMIT = 4000


def rendered_skill(document, source_name):
    if not document.startswith('---\n'):
        raise ValueError('command frontmatter missing')
    header, body = document[4:].split('\n---\n', 1)
    descriptions = re.findall(r'^description:\s*(.+)$', header, re.MULTILINE)
    if len(descriptions) != 1:
        raise ValueError('command description missing or duplicated')
    value = descriptions[0]
    description = json.loads(value) if value.startswith('"') else value
    if not isinstance(description, str) or not description.strip():
        raise ValueError('command description empty')
    quote = lambda text: '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'
    name = 'source-command-' + source_name
    return ('---\nname: ' + quote(name) + '\ndescription: ' + quote(description.strip())
            + '\n---\n\n# ' + name + '\n\nUse this skill when the user asks to run the migrated '
            + 'source command `' + source_name + '`.\n\n## Command Template\n\n'
            + (body.strip() or 'No command template body was found.') + '\n')


class CommandMigrationTests(unittest.TestCase):
    def test_source_commands_fit_rendered_native_migration_budget(self):
        for path in sorted(COMMANDS.glob('*.md')):
            with self.subTest(command=path.stem):
                size = len(rendered_skill(path.read_text(), path.stem).encode('utf-8'))
                self.assertLessEqual(size, LIMIT,
                    '%s renders to %d UTF-8 bytes; Codex skips skills above %d' %
                    (path.name, size, LIMIT))

    def test_budget_counts_utf8_bytes_and_the_generated_wrapper(self):
        document = '---\ndescription: "帮助"\n---\n\n' + '审' * 1300
        rendered = rendered_skill(document, 'help')
        self.assertLess(len(document.encode('utf-8')), LIMIT)
        self.assertLess(len(rendered), LIMIT)
        self.assertGreater(len(rendered.encode('utf-8')), LIMIT)


if __name__ == '__main__':
    unittest.main()
