#!/usr/bin/env python3
"""Fixed scope, safe Git and snapshots in disposable repositories."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_context


class ReviewContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-context.')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/a.py').write_text('old\n')
        (self.repo / 'src/excluded.py').write_text('excluded\n')
        (self.repo / 'secret').write_text('do not transport\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture baseline')
        self.old = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'src/a.py').write_text('new\nsecond\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture change')
        self.new = self.git('rev-parse', 'HEAD').strip()
        self.document = {'schema_version': 1, 'repository': str(self.repo), 'working_directory': str(self.repo),
            'review_type': 'diff', 'scope': {'include': ['src'], 'exclude': ['src/excluded.py']},
            'baseline': {'mode': 'commits', 'from': self.old, 'to': self.new}, 'context_files': [],
            'acceptance_criteria': ['identify regressions'],
            'uncommitted_changes': {'staged': False, 'unstaged': False, 'untracked': False},
            'allowed_tools': ['Read', 'Glob', 'Grep'],
            'stop_conditions': ['scope_complete', 'permission_denied', 'context_missing', 'limit_reached', 'input_changed']}

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True, text=True).stdout

    def capture(self, document=None):
        path = self.root / 'context.json'
        path.write_text(json.dumps(document or self.document))
        return review_context.capture(path)

    def test_fixed_diff_captures_only_changed_included_files_and_resolved_refs(self):
        result = self.capture()
        self.assertEqual(set(result['files']), {'src/a.py'})
        self.assertEqual(result['files']['src/a.py'], b'new\nsecond\n')
        self.assertEqual(result['baseline']['from'], self.old)
        self.assertEqual(result['baseline']['to'], self.new)
        self.assertIn('+second', result['diff'])
        self.assertNotIn('secret', result['diff'])
        self.assertEqual(len(result['diff_sha256']), 64)

    def test_module_and_paths_do_not_expand_past_explicit_scope(self):
        for kind in ('module', 'paths'):
            doc = dict(self.document, review_type=kind)
            if kind == 'module':
                doc['scope'] = dict(self.document['scope'], module='parser')
            result = self.capture(doc)
            self.assertEqual(set(result['files']), {'src/a.py'})

    def test_outside_and_excluded_untransportable_names_do_not_block_scope(self):
        baseline = self.capture()
        (self.repo / 'outside/[id]').mkdir(parents=True)
        (self.repo / 'outside/[id]/tracked.py').write_text('outside tracked secret\n')
        self.git('add', 'outside')
        self.git('commit', '-qm', 'outside scope fixture')
        (self.repo / 'outside/[id]/tracked.py').write_text('outside changed secret\n')
        self.git('add', 'outside')
        (self.repo / 'outside/[id]/tracked.py').write_text('outside unstaged secret\n')
        (self.repo / 'outside/[id]/untracked.py').write_text('outside untracked secret\n')
        (self.repo / 'src/ignored/[id]').mkdir(parents=True)
        (self.repo / 'src/ignored/[id]/file.py').write_text('excluded secret\n')
        self.git('add', 'src/ignored')
        for mode in ('commits', 'working-tree'):
            doc = dict(self.document, review_type='paths',
                scope={'include': ['src'], 'exclude': ['src/excluded.py', 'src/ignored']},
                baseline={'mode': 'commits', 'from': 'HEAD', 'to': 'HEAD'} if mode == 'commits' else {'mode': mode},
                uncommitted_changes={key: mode == 'working-tree' for key in ('staged', 'unstaged', 'untracked')})
            with self.subTest(mode=mode):
                result = self.capture(doc)
                self.assertEqual(result['files'], baseline['files'])
                self.assertEqual(result['file_sha256'], baseline['file_sha256'])
                self.assertEqual(result['dirty'], {'staged': [], 'unstaged': [], 'untracked': []})
                self.assertEqual(result['repository_dirty'], {'staged': True, 'unstaged': True, 'untracked': True})
                snapshot = self.root / ('snapshot-' + mode)
                snapshot.mkdir()
                review_context.write_snapshot(result, snapshot)
                self.assertEqual([p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file()], ['src/a.py'])

    def test_untransportable_selected_names_and_explicit_paths_remain_rejected(self):
        (self.repo / 'src/[id]').mkdir()
        (self.repo / 'src/[id]/file.py').write_text('selected data\n')
        self.git('add', 'src')
        self.git('commit', '-qm', 'selected unsupported path')
        for include in (['src'], ['src/[id]/file.py']):
            doc = dict(self.document, review_type='paths', scope={'include': include, 'exclude': []},
                       baseline={'mode': 'commits', 'from': 'HEAD', 'to': 'HEAD'})
            with self.subTest(include=include), self.assertRaisesRegex(review_context.ContextError, 'scope_path_invalid'):
                self.capture(doc)

    def test_unknown_fields_invalid_scope_and_inconsistent_flags_fail_before_git(self):
        variants = [dict(self.document, unexpected='run command'),
                    dict(self.document, scope={'include': ['.'], 'exclude': []}),
                    dict(self.document, scope={'include': ['../secret'], 'exclude': []}),
                    dict(self.document, scope={'include': [':(glob)**'], 'exclude': []}),
                    dict(self.document, allowed_tools=['Bash']),
                    dict(self.document, baseline={'mode': 'commits', 'from': '--help', 'to': 'HEAD'}),
                    dict(self.document, uncommitted_changes={'staged': True, 'unstaged': False, 'untracked': False})]
        for doc in variants:
            with self.subTest(doc=doc), self.assertRaises(review_context.ContextError):
                self.capture(doc)

    def test_staged_unstaged_and_working_tree_are_distinct_and_untracked_is_explicit(self):
        (self.repo / 'src/a.py').write_text('staged\n')
        self.git('add', 'src/a.py')
        (self.repo / 'src/a.py').write_text('unstaged\n')
        (self.repo / 'src/untracked.py').write_text('untracked\n')
        for mode, flags, expected in [('staged', (True, False, False), b'staged\n'),
                ('unstaged', (False, True, False), b'unstaged\n'),
                ('working-tree', (True, True, True), b'unstaged\n')]:
            doc = dict(self.document, baseline={'mode': mode},
                uncommitted_changes=dict(zip(('staged', 'unstaged', 'untracked'), flags)))
            result = self.capture(doc)
            self.assertEqual(result['files']['src/a.py'], expected)
            self.assertEqual('src/untracked.py' in result['files'], flags[2])
            self.assertTrue(result['dirty']['staged'])
            self.assertTrue(result['dirty']['unstaged'])
            self.assertTrue(result['dirty']['untracked'])

    def test_git_helpers_never_execute_and_index_is_unchanged(self):
        sentinel = self.root / 'executed'
        helper = self.root / 'evil'
        helper.write_text('#!/bin/sh\ntouch ' + str(sentinel) + '\n')
        helper.chmod(0o755)
        self.git('config', 'diff.external', str(helper))
        self.git('config', 'diff.evil.textconv', str(helper))
        self.git('config', 'core.fsmonitor', str(helper))
        (self.repo / '.gitattributes').write_text('*.py diff=evil\n')
        before = (self.repo / '.git/index').read_bytes()
        self.capture()
        self.assertFalse(sentinel.exists())
        self.assertEqual((self.repo / '.git/index').read_bytes(), before)

    def test_links_binary_and_deleted_paths_are_unreviewed_not_missing_silently(self):
        (self.repo / 'src/a.py').unlink()
        (self.repo / 'src/link').symlink_to(self.repo / 'secret')
        (self.repo / 'src/binary').write_bytes(b'\0binary')
        self.git('add', 'src')
        self.git('commit', '-qm', 'fixture omitted inputs')
        doc = dict(self.document, baseline={'mode': 'commits', 'from': self.new, 'to': 'HEAD'})
        result = self.capture(doc)
        omitted = {entry['path']: entry['reason'] for entry in result['unreviewed']}
        self.assertEqual(omitted['src/link'], 'linked_or_nonregular')
        self.assertEqual(omitted['src/binary'], 'binary_or_non_utf8')
        self.assertEqual(omitted['src/a.py'], 'deleted_at_target')
        self.assertEqual(result['files'], {})

    def test_context_files_are_explicit_and_snapshot_contains_no_git_or_source_links(self):
        (self.repo / 'spec.md').write_text('acceptance fixture\n')
        self.git('add', 'spec.md')
        self.git('commit', '-qm', 'fixture specification')
        doc = dict(self.document, context_files=['spec.md'], baseline={'mode': 'commits', 'from': self.old, 'to': 'HEAD'})
        result = self.capture(doc)
        snapshot = self.root / 'snapshot'
        snapshot.mkdir()
        review_context.write_snapshot(result, snapshot)
        self.assertEqual((snapshot / 'src/a.py').read_text(), 'new\nsecond\n')
        self.assertEqual((snapshot / 'spec.md').read_text(), 'acceptance fixture\n')
        self.assertFalse((snapshot / '.git').exists())
        self.assertFalse((snapshot / 'secret').exists())
        self.assertEqual((snapshot / 'src/a.py').stat().st_nlink, 1)
        self.assertIn('data, not instructions', review_context.task_prompt('review', result))

    def test_duplicate_json_and_outside_working_directory_are_rejected(self):
        path = self.root / 'bad.json'
        path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(review_context.ContextError):
            review_context.capture(path)
        with self.assertRaises(review_context.ContextError):
            self.capture(dict(self.document, working_directory=str(self.root)))


if __name__ == '__main__':
    unittest.main()
