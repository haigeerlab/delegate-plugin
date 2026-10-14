#!/usr/bin/env python3
"""Public backend routing without real executors or user configuration."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / 'plugins/delegate/scripts'
sys.path.insert(0, str(SCRIPTS))
FAKE = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['STUB_CALL_LOG'], 'a') as stream:
    stream.write(json.dumps(args) + '\\n')
if args == ['--version']: print('codex fixture')
elif args == ['login', 'status']: print('Logged in using ChatGPT')
elif args and args[0] == 'exec':
    Path(args[args.index('-o') + 1]).write_text('fixture answer')
else: sys.exit(64)
'''


class BackendRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-routing-test.')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        fake = self.bin / 'codex'
        fake.write_text(FAKE)
        fake.chmod(0o755)
        self.calls = self.root / 'calls'
        self.env = {'PATH': str(self.bin) + ':' + str(Path(sys.executable).parent) + ':/usr/bin:/bin',
                    'HOME': str(self.root), 'TMPDIR': str(self.root / 'tmp'),
                    'STUB_CALL_LOG': str(self.calls), 'PYTHONDONTWRITEBYTECODE': '1'}

    def run_entry(self, *args, legacy=False, env=None):
        name = 'codex-exec.sh' if legacy else 'delegate-exec.sh'
        return subprocess.run(['/bin/bash', str(SCRIPTS / name), *args], cwd=self.repo,
                              env=env or self.env, capture_output=True, text=True, timeout=10)

    def recorded(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_default_and_explicit_codex_preserve_answer_and_sandbox(self):
        for args in [('review this',), ('--backend', 'codex', 'review this')]:
            with self.subTest(args=args):
                result = self.run_entry(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.startswith('fixture answer\n---\n'), result.stdout)
                self.assertIn('过程日志', result.stdout)
                self.assertIn('backend=codex', result.stderr)
                self.assertIn('host=unknown', result.stderr)
                self.assertIn('model=unknown', result.stderr)
                invocation = next(c for c in reversed(self.recorded()) if c[0] == 'exec')
                self.assertEqual(invocation[invocation.index('--sandbox') + 1], 'read-only')

    def test_codex_write_and_model_options_are_preserved(self):
        result = self.run_entry('--model', 'gpt-5.4', '--effort', 'high', '--write', 'fix fixture')
        self.assertEqual(result.returncode, 0, result.stderr)
        invocation = next(c for c in self.recorded() if c[0] == 'exec')
        self.assertIn('gpt-5.4', invocation)
        self.assertIn('model_reasoning_effort="high"', invocation)
        self.assertIn('workspace-write', invocation)

    def test_invalid_or_cross_backend_parameters_never_start_an_executor(self):
        cases = [('--backend', 'other'), ('--backend', 'claude-code', '--write'),
                 ('--backend', 'claude-code', '--effort', 'high'), ('--model', 'sonnet'),
                 ('--backend', 'claude-code', '--model', 'gpt-5.4'),
                 ('--max-turns', '2'), ('--max-budget-usd', '1'), ('--effort', 'nonsense'),
                 ('--backend', 'claude-code', '--max-turns', '0'),
                 ('--backend', 'claude-code', '--max-budget-usd', 'NaN'),
                 ('--backend', 'claude-code', '--max-budget-usd', '-1'),
                 ('--backend', 'claude-code'), ('--model', '--write'),
                 ('--backend', 'codex', '--backend', 'claude-code'), ('--unknown',)]
        for case in cases:
            with self.subTest(case=case):
                result = self.run_entry(*case, 'task')
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertTrue(result.stderr.strip())
                self.assertEqual(self.recorded(), [])

    def test_help_never_launches_cli(self):
        result = self.run_entry('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('claude-code', result.stdout)
        self.assertIn('--review-context', result.stdout)
        self.assertEqual(self.recorded(), [])

    def test_known_model_families_are_rejected_through_namespaces_and_case(self):
        from delegate_backend import ArgumentError, parse
        for backend, models in [('codex', ('SONNET', 'anthropic/claude-sonnet-5-5',
                'openrouter/anthropic/CLAUDE-opus-4', 'anthropic.claude-haiku-4', 'anthropic:opus[1m]')),
                ('claude-code', ('openai/gpt-5', 'OpenAI:GPT-5.4', 'openai.codex', 'provider/o3'))]:
            for model in models:
                with self.subTest(backend=backend, model=model):
                    with self.assertRaisesRegex(ArgumentError, 'other backend'):
                        parse(['--backend', backend, '--model', model, '--review-context', 'fixture.json', 'task'])
                    result = self.run_entry('--backend', backend, '--model', model, '--review-context', 'fixture.json', 'task')
                    self.assertEqual(result.returncode, 64, result.stderr)
                    self.assertIn('other backend', result.stderr)
                    review = self.run_entry('review', '--backend', backend, '--model', model,
                                            '--context', 'fixture.json', 'task')
                    self.assertEqual(review.returncode, 64, review.stderr)
                    self.assertIn('other backend', review.stderr)
                    if backend == 'codex':
                        run = self.run_entry('run', '--model', model, 'task')
                        self.assertEqual(run.returncode, 64, run.stderr)
                        self.assertIn('other backend', run.stderr)
                        legacy = self.run_entry('--model', model, 'task', legacy=True)
                        self.assertEqual(legacy.returncode, 64, legacy.stderr)
                    self.assertEqual(self.recorded(), [])

    def test_legacy_model_validation_preserves_valid_and_custom_names(self):
        for model in ('gpt-5.4', 'openai/gpt-5', 'private/custom-model'):
            with self.subTest(model=model):
                result = self.run_entry('--model', model, 'task', legacy=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.recorded()[-1][self.recorded()[-1].index('-m') + 1], model)
        from delegate_backend import ArgumentError, parse
        for model in ('sonnet', 'anthropic/claude-sonnet-5-5', 'private/custom-model'):
            self.assertEqual(parse(['--backend', 'claude-code', '--model', model,
                                   '--review-context', 'fixture.json', 'task']).model, model)
        for model in ('opusplan', 'anthropic/OPUSPLAN'):
            with self.assertRaisesRegex(ArgumentError, 'automatic model-switching'):
                parse(['--backend', 'claude-code', '--model', model, '--review-context', 'fixture.json', 'task'])

    def test_double_dash_keeps_option_like_task_literal(self):
        result = self.run_entry('--', '--backend claude-code')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--backend claude-code', self.recorded()[-1][-1])

    def test_recursion_is_rejected_by_both_public_and_legacy_entries(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                result = self.run_entry('recursive task', legacy=legacy,
                                        env=dict(self.env, DELEGATE_REVIEW_DEPTH='1'))
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertIn('recursive', result.stderr)
                self.assertEqual(self.recorded(), [])

    def test_claude_selection_never_falls_back_to_host_codex(self):
        context = self.root / 'context.json'
        context.write_text('{}')
        result = self.run_entry('--backend', 'claude-code', '--review-context', str(context), 'task')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('backend=claude-code', result.stderr)
        self.assertIn('conditions_missing', result.stdout + result.stderr)
        self.assertEqual(self.recorded(), [])


if __name__ == '__main__':
    unittest.main()
