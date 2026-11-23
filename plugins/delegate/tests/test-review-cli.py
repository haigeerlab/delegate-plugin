#!/usr/bin/env python3
"""User-facing commands using disposable repositories and fake executors."""
import importlib.util
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('routing_fixture', TESTS / 'test-review-backends.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class ReviewCLITests(unittest.TestCase):
    setUp = fixture.BackendRoutingTests.setUp
    run_entry = fixture.BackendRoutingTests.run_entry
    recorded = fixture.BackendRoutingTests.recorded

    def test_run_preserves_codex_read_only_and_explicit_write(self):
        for options, sandbox in [((), 'read-only'), (('--write',), 'workspace-write')]:
            result = self.run_entry('run', *options, 'fixture task')
            self.assertEqual(result.returncode, 0, result.stderr)
            call = self.recorded()[-1]
            self.assertEqual(call[call.index('--sandbox') + 1], sandbox)
            self.assertIn('fixture answer', result.stdout)

    def test_run_rejects_claude_and_review_context_before_any_executor(self):
        for options in [('--backend', 'claude-code'), ('--review-context', 'private.json')]:
            result = self.run_entry('run', *options, 'fixture task')
            self.assertEqual(result.returncode, 64, result.stderr)
            self.assertEqual(self.recorded(), [])

    def test_command_help_is_model_free_and_describes_capability_difference(self):
        for command in [('run', '--help'), ('review', '--help'), ('--help',)]:
            result = self.run_entry(*command)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('claude-code', result.stdout)
            self.assertEqual(self.recorded(), [])

    def test_capabilities_are_used_for_backend_option_validation(self):
        from delegate_capabilities import BACKENDS
        from delegate_backend import ArgumentError, parse
        self.assertTrue(BACKENDS['codex']['run'])
        self.assertFalse(BACKENDS['claude-code']['run'])
        self.assertEqual(set(BACKENDS), {'codex', 'claude-code'})
        for backend, options in [('codex', ('--max-turns', '2')),
                                 ('claude-code', ('--effort', 'high'))]:
            with self.assertRaises(ArgumentError):
                parse(['--backend', backend, '--review-context', 'context.json', *options, 'task'])

    def prepare_review(self):
        (self.repo / 'src').mkdir()
        for name, content in [('src/a.py', 'before\n'), ('src/excluded.py', 'excluded secret\n'),
                              ('SPEC.md', 'spec fixture\n'), ('PLAN.md', 'plan fixture\n')]:
            (self.repo / name).write_text(content)
        for argv in [('config', 'user.name', 'Fixture'), ('config', 'user.email', 'fixture@example.invalid'),
                     ('add', '.'), ('commit', '-qm', 'fixture baseline')]:
            self.git(*argv)
        self.old = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'src/a.py').write_text('after\n')
        self.git('add', '.'); self.git('commit', '-qm', 'fixture change')
        self.new = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              text=True, capture_output=True).stdout

    def preview(self, *options):
        result = self.run_entry('review', *options, '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.recorded(), [])
        self.assertFalse((self.root / 'tmp').exists())
        value = json.loads(result.stdout)
        self.assertEqual(value['kind'], 'review_preview')
        self.assertFalse(value['backend_started'])
        self.assertNotIn('review_outcome', value)
        self.assertNotIn('after\\n', result.stdout)
        return value

    def test_paths_preview_fixed_head_context_exclusions_and_dirty_state(self):
        self.prepare_review()
        (self.repo / 'src/a.py').write_text('PRIVATE_UNSTAGED_BODY\n')
        before = (self.repo / '.git/index').read_bytes()
        value = self.preview('--backend', 'claude-code', '--paths', 'src', '--exclude', 'src/excluded.py',
                             '--spec', 'SPEC.md', '--plan', 'PLAN.md', '--criterion', 'check contract')
        self.assertEqual(value['backend'], 'claude-code')
        self.assertEqual(value['review_type'], 'paths')
        self.assertEqual(set(value['file_sha256']), {'src/a.py', 'SPEC.md', 'PLAN.md'})
        self.assertEqual(value['file_sha256']['src/a.py'], hashlib.sha256(b'after\n').hexdigest())
        self.assertTrue(value['repository_dirty']['unstaged'])
        self.assertFalse(value['uncommitted_changes']['unstaged'])
        self.assertEqual(value['allowed_tools'], ['Read'])
        self.assertEqual(value['acceptance_criteria'], ['check contract'])
        self.assertEqual(before, (self.repo / '.git/index').read_bytes())

    def test_fixed_diff_without_paths_derives_only_changed_files(self):
        self.prepare_review()
        value = self.preview('--base', self.old, '--head', 'HEAD')
        self.assertEqual(value['review_type'], 'diff')
        self.assertEqual(value['baseline']['to'], self.new)
        self.assertEqual(value['scope']['include'], ['src/a.py'])
        self.assertEqual(set(value['file_sha256']), {'src/a.py'})

    def test_both_backends_preview_ignores_outside_bracket_filenames(self):
        self.prepare_review()
        baseline = self.preview('--paths', 'src/a.py')
        (self.repo / 'outside/[id]').mkdir(parents=True)
        (self.repo / 'outside/[id]/tracked.py').write_text('outside secret\n')
        self.git('add', 'outside'); self.git('commit', '-qm', 'outside scope')
        (self.repo / 'outside/[id]/untracked.py').write_text('outside untracked secret\n')
        for backend in ('codex', 'claude-code'):
            with self.subTest(backend=backend):
                value = self.preview('--backend', backend, '--paths', 'src/a.py')
                self.assertEqual(value['file_sha256'], baseline['file_sha256'])
                self.assertEqual(value['scope'], baseline['scope'])
                self.assertTrue(value['repository_dirty']['untracked'])
                self.assertNotIn('outside', json.dumps(value))

    def test_working_diff_and_module_explicitly_include_uncommitted_versions(self):
        self.prepare_review()
        (self.repo / 'src/a.py').write_text('staged\n'); self.git('add', 'src/a.py')
        (self.repo / 'src/a.py').write_text('unstaged\n')
        (self.repo / 'src/new.py').write_text('untracked\n')
        for mode, expected in [('staged', b'staged\n'), ('unstaged', b'unstaged\n'), ('working-tree', b'unstaged\n')]:
            with self.subTest(mode=mode):
                value = self.preview('--changes', mode)
                self.assertEqual(value['file_sha256']['src/a.py'], hashlib.sha256(expected).hexdigest())
                self.assertNotIn('src/new.py', value['file_sha256'])
        value = self.preview('--paths', 'src', '--module', 'pricing', '--changes', 'working-tree',
                             '--include-untracked', '--exclude', 'src/excluded.py')
        self.assertEqual(value['review_type'], 'module')
        self.assertEqual(value['scope']['module'], 'pricing')
        self.assertIn('src/new.py', value['file_sha256'])

    def test_invalid_scope_combinations_never_start_executor(self):
        self.prepare_review()
        cases = [(), ('--head', 'HEAD'), ('--module', 'pricing'), ('--include-untracked', '--paths', 'src'),
                 ('--base', 'HEAD', '--changes', 'staged'), ('--paths', '.'), ('--paths', '../outside'),
                 ('--context', 'private.json', '--paths', 'src'), ('--paths', 'src', '--write'),
                 ('--paths', 'src', '--backend', 'codex', '--backend', 'claude-code'),
                 ('--base', '--help'), ('--paths', 'src', '--backend', 'claude-code', '--effort', 'high'),
                 ('--base', ''), ('--paths', 'src', '--module', ''), ('--paths', 'src', '--context', ''),
                 ('--paths', 'src', '--model', '')]
        for options in cases:
            with self.subTest(options=options):
                result = self.run_entry('review', *options, '--dry-run')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.recorded(), [])

    def test_empty_diff_reports_conditions_missing_not_review_passed(self):
        self.prepare_review()
        result = self.run_entry('review', '--base', 'HEAD', '--dry-run')
        self.assertEqual(result.returncode, 127, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['execution_status'], 'conditions_missing')
        self.assertEqual(report['review_outcome'], 'inconclusive')
        self.assertFalse(report['backend_started'])
        self.assertEqual(self.recorded(), [])

    def test_advanced_context_preview_uses_same_capture_as_shortcuts(self):
        self.prepare_review()
        import review_context
        context = {'schema_version': 1, 'repository': str(self.repo), 'working_directory': str(self.repo),
                   'review_type': 'paths', 'scope': {'include': ['src/a.py'], 'exclude': []},
                   'baseline': {'mode': 'commits', 'from': 'HEAD', 'to': 'HEAD'}, 'context_files': [],
                   'acceptance_criteria': [], 'uncommitted_changes': {'staged': False, 'unstaged': False, 'untracked': False},
                   'allowed_tools': ['Read'], 'stop_conditions': sorted(review_context.STOPS)}
        path = self.root / 'review.json'; path.write_text(json.dumps(context))
        advanced = self.preview('--context', str(path))
        simple = self.preview('--paths', 'src/a.py')
        for key in ('review_type', 'scope', 'baseline', 'file_sha256', 'uncommitted_changes', 'stop_conditions'):
            self.assertEqual(advanced[key], simple[key])

    def test_shortcuts_reach_real_public_codex_wrapper_with_structured_result(self):
        self.prepare_review()
        common_spec = importlib.util.spec_from_file_location('common_fixture', TESTS / 'test-review-execution.py')
        common = importlib.util.module_from_spec(common_spec); common_spec.loader.exec_module(common)
        (self.bin / 'codex').write_text(common.FAKE)
        env = dict(self.env, FIXTURE_PROMPT=str(self.root/'prompt'), FIXTURE_ARGS=str(self.root/'argv'),
                   FIXTURE_SCHEMA=str(self.root/'schema'), FIXTURE_MODE='normal')
        result = self.run_entry('review', '--paths', 'src/a.py', 'check fixture', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['backend'], 'codex')
        self.assertEqual(report['execution_status'], 'completed')
        self.assertEqual(report['reviewed'], ['src/a.py'])
        argv = json.loads((self.root/'argv').read_text())
        self.assertEqual(argv[argv.index('--sandbox')+1], 'read-only')
        self.assertIn('--ephemeral', argv)

    def test_missing_primary_paths_are_not_hidden_by_present_spec(self):
        self.prepare_review()
        value = self.preview('--paths', 'missing', '--spec', 'SPEC.md')
        self.assertIn({'path': 'missing', 'reason': 'scope_has_no_reviewable_files'}, value['unreviewed'])
        partial = self.preview('--paths', 'src/a.py', '--paths', 'missing')
        self.assertIn({'path': 'missing', 'reason': 'scope_has_no_reviewable_files'}, partial['unreviewed'])
        result = self.run_entry('review', '--paths', 'missing', '--spec', 'SPEC.md')
        self.assertEqual(result.returncode, 127, result.stderr)
        self.assertFalse(json.loads(result.stdout)['backend_started'])
        self.assertEqual(self.recorded(), [])

    def test_repo_subdirectory_paths_are_still_root_relative_and_limits_are_explicit(self):
        self.prepare_review()
        value = self.preview('--repo', str(self.repo/'src'), '--paths', 'src/a.py',
                             '--backend', 'claude-code', '--max-turns', '3', '--max-budget-usd', '0.5')
        self.assertEqual(value['repository'], str(self.repo.resolve()))
        self.assertEqual(value['working_directory'], str((self.repo/'src').resolve()))
        self.assertEqual(set(value['file_sha256']), {'src/a.py'})
        self.assertEqual(value['requested_limits'], {'max_turns': 3, 'max_budget_usd': '0.5'})



class PreviousReportCLITests(unittest.TestCase):
    setUp = fixture.BackendRoutingTests.setUp
    run_entry = fixture.BackendRoutingTests.run_entry
    recorded = fixture.BackendRoutingTests.recorded
    prepare_review = ReviewCLITests.prepare_review
    git = ReviewCLITests.git
    preview = ReviewCLITests.preview

    def previous(self, **values):
        finding = {'title': 'PRIVATE_FINDING_TEXT', 'file': 'src/a.py', 'line': 1, 'trigger': 't', 'impact': 'i',
                   'evidence': 'e', 'suggestion': 's', 'unverified': [], 'severity': 'blocking'}
        report = {'schema_version': 1, 'execution_status': 'completed', 'review_outcome': 'findings',
                  'scope': {'paths': {'include': ['src/a.py'], 'exclude': []},
                            'baseline': {'mode': 'commits', 'from': self.old, 'to': self.new}, 'fingerprint': None},
                  'findings': [finding, dict(finding, severity='suggestion')], 'recheck': None}
        report.update(values)
        path = self.root / ('PRIVATE_PREVIOUS_PATH_%d.json' % len(list(self.root.glob('PRIVATE_PREVIOUS_PATH_*'))))
        path.write_text(json.dumps(report))
        return str(path)

    def test_preview_counts_previous_blocking_findings(self):
        self.prepare_review()
        value = self.preview('--base', self.old, '--previous-report', self.previous())
        self.assertEqual(value['previous_findings_count'], 1)
        self.assertNotIn('previous_findings', value)

    def test_profile_option_preview_and_errors(self):
        self.prepare_review()
        design = self.preview('--paths', 'src/a.py', '--profile', 'design')
        self.assertEqual((design['profile'], design['criteria']), ('design', 'design-v1'))
        plain = self.preview('--paths', 'src/a.py')
        self.assertEqual((plain['profile'], plain['criteria']), ('default', 'severity-v1'))
        for options in [('--profile', 'other'), ('--profile', 'design', '--profile', 'design'), ('--profile', '')]:
            with self.subTest(options=options):
                result = self.run_entry('review', '--paths', 'src/a.py', *options, '--dry-run')
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertEqual(self.recorded(), [])

    def test_preview_without_option_has_no_count(self):
        self.prepare_review()
        self.assertNotIn('previous_findings_count', self.preview('--base', self.old))

    def test_bad_previous_report_never_starts_executor(self):
        self.prepare_review()
        cases = [(str(self.root / 'missing.json'), 'previous_report_unreadable'),
                 (self.previous(execution_status='failed'), 'previous_report_invalid'),
                 (self.previous(scope={'paths': {'include': ['src'], 'exclude': []},
                                       'baseline': {'mode': 'commits', 'from': self.old, 'to': self.old}}),
                  'previous_report_scope_mismatch')]
        for path, code in cases:
            for options in [(), ('--dry-run',)]:
                with self.subTest(code=code, options=options):
                    result = self.run_entry('review', '--base', self.old, '--previous-report', path, *options)
                    self.assertEqual(result.returncode, 127, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report['execution_status'], 'conditions_missing')
                    self.assertFalse(report['backend_started'])
                    self.assertIn(code, report['diagnostics'])
                    self.assertIsNone(report.get('recheck'))
                    self.assertEqual(self.recorded(), [])
                    self.assertNotIn('PRIVATE_', result.stdout + result.stderr)

    def test_previous_report_option_is_single_and_non_empty(self):
        self.prepare_review()
        path = self.previous()
        for options in [('--previous-report', ''), ('--previous-report', path, '--previous-report', path)]:
            with self.subTest(options=options):
                result = self.run_entry('review', '--base', self.old, *options, '--dry-run')
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertEqual(self.recorded(), [])


execution_spec = importlib.util.spec_from_file_location('execution_fixture', TESTS / 'test-review-execution.py')
execution = importlib.util.module_from_spec(execution_spec)
execution_spec.loader.exec_module(execution)


class SnapshotRecheckCLITests(unittest.TestCase):
    """spec/review-snapshot-recheck.md SR-01/SR-02 through the public entry point with a fake Codex."""
    setUp = execution.CommonExecutionTests.setUp

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, text=True,
                              capture_output=True, stdin=subprocess.DEVNULL).stdout.strip()

    def change(self, text, message):
        (self.repo / 'src/a.py').write_text(text)
        self.git('add', '.')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def review(self, *options, mode='normal'):
        prompt = self.root / 'prompt'
        if prompt.exists():
            prompt.unlink()
        return subprocess.run(['/bin/bash', str(SCRIPTS / 'delegate-exec.sh'), 'review', *options, 'snapshot fixture'],
                              cwd=self.repo, env=dict(self.env, FIXTURE_MODE=mode, DELEGATE_TIMEOUT_SECONDS='1'),
                              capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)

    def first_round(self):
        result = self.review('--paths', 'src/a.py', mode='line')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['execution_status'], 'completed')
        baseline = report['scope']['baseline']
        self.assertEqual(baseline['from'], baseline['to'])
        path = self.root / 'PRIVATE_ROUND1.json'
        path.write_text(result.stdout)
        return path, report

    def edited(self, report, **baseline):
        value = json.loads(json.dumps(report))
        value['scope']['baseline'].update(baseline)
        path = self.root / ('PRIVATE_EDITED_%d.json' % len(list(self.root.glob('PRIVATE_EDITED_*'))))
        path.write_text(json.dumps(value))
        return path

    def test_snapshot_recheck_after_rework_runs_and_reports_previous_items(self):
        path, first = self.first_round()
        self.change('reworked\n', 'rework')
        result = self.review('--paths', 'src/a.py', '--previous-report', str(path), mode='recheck')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue((self.root / 'prompt').exists(), 'the executor must start')
        self.assertEqual(report['execution_status'], 'completed')
        self.assertEqual(report['recheck']['previous_report_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual([(item['index'], item['status']) for item in report['recheck']['items']], [(1, 'unresolved')])
        self.assertEqual(report['recheck']['items'][0]['finding']['title'], first['findings'][0]['title'])
        preview = self.review('--paths', 'src/a.py', '--previous-report', str(path), '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)['previous_findings_count'], 1)
        self.assertFalse((self.root / 'prompt').exists(), 'dry run must not start the executor')

    def test_snapshot_recheck_rejections_never_start_the_executor(self):
        path, first = self.first_round()
        start = first['scope']['baseline']['to']
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'tag', '-a', '-m', 'tag', 'v1', start)
        tag_object = self.git('rev-parse', 'refs/tags/v1')
        branch = self.git('symbolic-ref', '--short', 'HEAD')
        self.git('checkout', '-q', '--orphan', 'other')
        other = self.change('other\n', 'other history')
        self.git('checkout', '-q', '-f', branch)
        later = self.change('reworked\n', 'rework')
        cases = {
            'other history': (path, ['--paths', 'src/a.py', '--base', other, '--head', other]),
            'missing commit': (self.edited(first, **{'from': '0' * 40, 'to': '0' * 40}), ['--paths', 'src/a.py']),
            'tag object': (self.edited(first, **{'from': tag_object, 'to': tag_object}), ['--paths', 'src/a.py']),
            'malformed id': (self.edited(first, **{'from': start[:12], 'to': start[:12]}), ['--paths', 'src/a.py']),
            'different paths': (path, ['--paths', 'src']),
            'snapshot then range': (path, ['--paths', 'src/a.py', '--base', start, '--head', later]),
            'range then snapshot': (self.edited(first, to=later), ['--paths', 'src/a.py']),
        }
        for name, (previous, options) in cases.items():
            for extra in [(), ('--dry-run',)]:
                with self.subTest(case=name, options=extra):
                    result = self.review(*options, '--previous-report', str(previous), *extra)
                    self.assertEqual(result.returncode, 127, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report['execution_status'], 'conditions_missing')
                    self.assertFalse(report['backend_started'])
                    self.assertIn('previous_report_scope_mismatch', report['diagnostics'])
                    self.assertFalse((self.root / 'prompt').exists())
                    self.assertNotIn('PRIVATE_', result.stdout + result.stderr)
                    self.assertNotIn('fatal', result.stdout + result.stderr)


class DesignProfileCLITests(unittest.TestCase):
    """spec/design-review-criteria.md DR-06/DR-09 through the public entry with a fake Codex."""
    setUp = execution.CommonExecutionTests.setUp
    git = SnapshotRecheckCLITests.git
    review = SnapshotRecheckCLITests.review

    def prepare(self):
        (self.repo / 'design.md').write_text('step one\nstep two\n')
        (self.repo / 'src/a.py').write_text('def f():\n    return 1\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'design')

    def fake_findings(self, findings):
        # The fake Codex writes FIXTURE_CONTENT verbatim when set.
        path = self.root / 'content.json'
        path.write_text(json.dumps({'schema_version': 1, 'reviewed': ['design.md', 'src/a.py'], 'unreviewed': [],
                                    'findings': findings}))
        self.env['FIXTURE_CONTENT'] = str(path)

    def finding(self, file, line):
        return {'title': 'T-' + file, 'file': file, 'line': line, 'trigger': 't', 'impact': 'i', 'evidence': 'e',
                'suggestion': 's', 'unverified': [], 'severity': 'blocking'}

    def test_design_review_keeps_code_evidence_and_downgrades_the_rest(self):
        self.prepare()
        self.fake_findings([self.finding('src/a.py', 2), self.finding('design.md', 1)])
        result = self.review('--profile', 'design', '--paths', 'design.md', '--spec', 'src/a.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['criteria'], 'design-v1')
        self.assertEqual(report['execution_status'], 'completed')
        self.assertEqual([(item['file'], item['severity'], item.get('downgraded')) for item in report['findings']],
                         [('src/a.py', 'blocking', None), ('design.md', 'suggestion', 'no_code_evidence')])

    def test_recheck_with_a_different_criteria_never_starts_the_executor(self):
        self.prepare()
        self.fake_findings([])
        first = self.review('--paths', 'design.md', '--spec', 'src/a.py')
        self.assertEqual(first.returncode, 0, first.stderr)
        path = self.root / 'PRIVATE_DEFAULT_ROUND.json'
        path.write_text(first.stdout)
        result = self.review('--profile', 'design', '--paths', 'design.md', '--spec', 'src/a.py',
                             '--previous-report', str(path))
        self.assertEqual(result.returncode, 127, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn('previous_report_scope_mismatch', report['diagnostics'])
        self.assertFalse(report['backend_started'])
        self.assertFalse((self.root / 'prompt').exists())
        self.assertEqual(report['criteria'], 'design-v1')


if __name__ == '__main__':
    unittest.main()
