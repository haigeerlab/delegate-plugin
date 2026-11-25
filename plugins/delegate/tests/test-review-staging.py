#!/usr/bin/env python3
"""Check staged supervisor and guest imports without source-tree fallback."""
import ast
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import review_macos
import review_transport

# Include the deferred review_init import in review_macos.anchor().
ANCHOR_IMPORTS = ('review_macos', 'review_init')
GUEST_IMPORTS = ('review_guest_entry', 'review_service', 'review_result', 'reviewer_select')
# claude_review.execute() runs only in the controller, from the full plugin
# directory; the staged anchor never calls it.
ANCHOR_CONTROLLER_ONLY = {('claude_review.py', 'review_context'), ('claude_review.py', 'review_result')}
# reviewer_select.codex_check()/claude_check() probe the host before a review;
# the guest only calls describe() through review_result.reviewer_default().
GUEST_HOST_ONLY = {('reviewer_select.py', 'backend'), ('reviewer_select.py', 'review_macos'),
                   ('reviewer_select.py', 'review_native')}


class StagingTests(unittest.TestCase):
    def assert_staged_imports(self, files, modules):
        with tempfile.TemporaryDirectory(prefix='delegate-staging.') as temporary:
            staged = Path(temporary)
            for name in files:
                shutil.copy2(SCRIPTS / name, staged / name)
            code = 'import sys\nsys.path.insert(0, %r)\n' % str(staged)
            code += '\n'.join('import %s' % module for module in modules)
            result = subprocess.run([sys.executable, '-I', '-B', '-c', code],
                cwd=staged, capture_output=True, text=True, timeout=10)
            stderr = result.stderr.splitlines()
            self.assertEqual(result.returncode, 0, stderr[-1] if stderr else '')

    def assert_static_imports_staged(self, files, exempt=frozenset()):
        # Lazy imports inside functions only fail at run time, so scan every
        # import statement and require each local script module to be staged.
        local = {path.stem for path in SCRIPTS.glob('*.py')}
        staged = {Path(name).stem for name in files}
        missing = set()
        for name in files:
            for node in ast.walk(ast.parse((SCRIPTS / name).read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    modules = [alias.name.split('.')[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    modules = [node.module.split('.')[0]]
                else:
                    continue
                missing.update(module for module in modules if module in local and module not in staged
                               and (name, module) not in exempt)
        self.assertEqual(sorted(missing), [])

    def test_anchor_static_imports_are_staged(self):
        self.assert_static_imports_staged(review_macos.ANCHOR_FILES, ANCHOR_CONTROLLER_ONLY)

    def test_guest_static_imports_are_staged(self):
        self.assert_static_imports_staged(review_transport.GUEST_FILES, GUEST_HOST_ONLY)

    def test_anchor_staged_imports(self):
        self.assert_staged_imports(review_macos.ANCHOR_FILES, ANCHOR_IMPORTS)

    def test_guest_staged_imports(self):
        self.assert_staged_imports(review_transport.GUEST_FILES, GUEST_IMPORTS)


if __name__ == '__main__':
    unittest.main()
