#!/usr/bin/env python3
"""check-local-paths.sh rejects machine-specific home paths in tracked and new files."""
from pathlib import Path
import subprocess
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT / 'scripts' / 'check-local-paths.sh'
# Built at runtime so this file itself never contains a real-looking home path.
REAL = '/' + 'Users' + '/someone/project/run.py'


class LocalPathTests(unittest.TestCase):
    def repo(self):
        temporary = tempfile.TemporaryDirectory(prefix='delegate-local-paths.')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        (root / '.gitignore').write_text('ignored/\n')
        (root / 'clean.md').write_text('nothing here\n')
        subprocess.run(['git', '-C', str(root), 'add', '-A'], check=True)
        return root

    def check(self, root):
        return subprocess.run(['/bin/bash', str(SCRIPT), str(root)], capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=30)

    def test_clean_repository_passes(self):
        result = self.check(self.repo())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_tracked_file_with_real_home_path_fails_with_location(self):
        root = self.repo()
        (root / 'docs').mkdir()
        (root / 'docs' / 'note.md').write_text('line one\nsee %s\n' % REAL)
        subprocess.run(['git', '-C', str(root), 'add', '-A'], check=True)
        result = self.check(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn('docs/note.md:2', result.stderr)

    def test_untracked_new_file_is_checked(self):
        root = self.repo()
        (root / 'new.txt').write_text(REAL + '\n')
        result = self.check(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn('new.txt:1', result.stderr)

    def test_ignored_file_is_not_checked(self):
        root = self.repo()
        (root / 'ignored').mkdir()
        (root / 'ignored' / 'log.txt').write_text(REAL + '\n')
        result = self.check(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_placeholders_pass(self):
        root = self.repo()
        (root / 'ok.md').write_text('/' + 'Users/<用户名>/x\n~/x\n$HOME/x\n<repo>/x\n/' + 'Users/\n')
        subprocess.run(['git', '-C', str(root), 'add', '-A'], check=True)
        result = self.check(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_repository_itself_is_clean(self):
        result = self.check(PROJECT)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
