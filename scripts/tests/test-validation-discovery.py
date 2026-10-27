#!/usr/bin/env python3
"""Exercise real file checks with isolated no-op suite dependencies."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[2]


class DiscoveryTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix='delegate-validation.', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ('scripts/validate.sh', 'scripts/check-manifests.py',
                '.claude-plugin/marketplace.json', 'plugins/delegate/.claude-plugin/plugin.json'):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / name, target)
        # Test file discovery, not the product suites: no CLI/model dependency
        # or recursive invocation of this test is allowed in the fixture.
        for name in ('evals/_preflight.sh', 'evals/propose-not-auto.sh', 'evals/routing-fitness.sh',
                'plugins/delegate/tests/test-channel.sh', 'plugins/delegate/tests/test-detection.sh',
                'plugins/delegate/tests/test-routing.sh'):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('#!/bin/bash\nexit 0\n')
            target.chmod(0o755)
        suites = ('backend', 'channel-regressions', 'command-migration', 'review-backends',
            'review-cli', 'claude-review', 'review-context', 'review-result', 'review-execution',
            'review-native', 'review-transport', 'review-guest-entry', 'review-artifacts',
            'review-service', 'review-guest', 'interface', 'run-resume', 'run-timeout', 'write-trust', 'reap-fake-endpoint',
            'run-result', 'run-continue', 'run-longrun', 'run-check', 'run-rules', 'claude-isolation')
        for suite in suites:
            (root / ('plugins/delegate/tests/test-%s.py' % suite)).write_text('# fixture suite\n')
        target = root / 'scripts/tests/test-validation-discovery.py'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('# prevent recursive fixture validation\n')
        return root

    def validate(self, root):
        environment = {'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin',
            'HOME': str(root), 'TMPDIR': str(root), 'PYTHONDONTWRITEBYTECODE': '1'}
        return subprocess.run(['/bin/bash', str(root / 'scripts/validate.sh')], cwd=root,
            env=environment, capture_output=True, timeout=30)

    def test_private_acceptance_and_git_are_excluded_from_all_file_checks(self):
        root = self.fixture()
        for directory in ('.agent/acceptance/backup', '.git/objects'):
            folder = root / directory
            folder.mkdir(parents=True)
            (folder / 'bad.json').write_text('{')
            (folder / 'bad.py').write_text('if:\n')
            (folder / 'private.sh').write_text('#!/bin/bash\nif\n')
            (folder / 'private.sh').chmod(0o600)
        result = self.validate(root)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertIn(b'validate: ok', result.stdout)
        self.assertEqual((root / '.agent/acceptance/backup/private.sh').stat().st_mode & 0o777, 0o600)

    def test_invalid_product_json_python_and_shell_still_fail(self):
        for name, content, reason in (('bad.json', '{', b'invalid JSON'),
                ('bad.py', 'if:\n', 'Python 语法校验未通过'.encode()),
                ('bad.sh', '#!/bin/bash\nif\n', b'bash syntax error')):
            with self.subTest(name=name):
                root = self.fixture()
                target = root / 'plugins/delegate' / name
                target.write_text(content)
                target.chmod(0o755)
                result = self.validate(root)
                self.assertEqual(result.returncode, 1)
                self.assertIn(reason, result.stderr)

    def test_nonexecutable_product_shell_still_fails(self):
        root = self.fixture()
        target = root / 'plugins/delegate/not-executable.sh'
        target.write_text('#!/bin/bash\nexit 0\n')
        target.chmod(0o600)
        result = self.validate(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'not executable: plugins/delegate/not-executable.sh', result.stderr)

    def test_other_agent_paths_and_similar_names_are_not_excluded(self):
        for name in ('.agent/state.json', '.agent/acceptance-adjacent/bad.json'):
            with self.subTest(name=name):
                root = self.fixture()
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('{')
                result = self.validate(root)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b'invalid JSON: ' + name.encode(), result.stderr)


if __name__ == '__main__':
    unittest.main()
