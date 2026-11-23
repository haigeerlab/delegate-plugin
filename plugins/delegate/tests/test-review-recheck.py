#!/usr/bin/env python3
"""Previous report reading, blocking set and scope check (pure functions, no git or model)."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_context import ContextError
import review_recheck

FROM, TO = 'a' * 40, 'b' * 40
SCOPE = {'include': ['src'], 'exclude': []}


def finding(title, severity='blocking', **values):
    item = {'title': title, 'file': 'src/a.py', 'line': 1, 'trigger': 't', 'impact': 'i', 'evidence': 'e',
            'suggestion': 's', 'unverified': [], 'severity': severity}
    item.update(values)
    if severity is None:
        del item['severity']
    return item


def report(findings=(), recheck=None, **values):
    value = {'schema_version': 1, 'execution_status': 'completed',
             'review_outcome': 'findings' if findings else 'no_findings_in_scope',
             'scope': {'paths': copy.deepcopy(SCOPE), 'baseline': {'mode': 'commits', 'from': FROM, 'to': TO},
                       'diff_sha256': 'f' * 64, 'fingerprint': {'algorithm': 'blob-pairs-v1', 'sha256': 'c' * 64,
                                                                'paths': ['src/a.py']}, 'files': {}},
             'findings': list(findings), 'recheck': recheck}
    value.update(values)
    return value


def context(**baseline):
    return {'scope': copy.deepcopy(SCOPE), 'baseline': dict({'mode': 'commits', 'from': FROM, 'to': 'd' * 40}, **baseline)}


class LoadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-recheck.')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'previous.json'

    def code(self, call):
        with self.assertRaises(ContextError) as caught:
            call()
        return str(caught.exception)

    def test_valid_file_returns_sha256_of_bytes_and_report(self):
        data = json.dumps(report([finding('x')])).encode()
        self.path.write_bytes(data)
        sha, value = review_recheck.load(str(self.path))
        self.assertEqual(sha, hashlib.sha256(data).hexdigest())
        self.assertEqual(value['findings'][0]['title'], 'x')

    def test_unreadable_inputs(self):
        cases = [None, b'\xff\xfe', b'{bad', b'{"a":1,"a":2}', b'[]', b' ' * (1024 * 1024 + 1)]
        for data in cases:
            if data is None:
                target = str(self.path) + '.missing'
            else:
                self.path.write_bytes(data)
                target = str(self.path)
            self.assertEqual(self.code(lambda: review_recheck.load(target)), 'previous_report_unreadable', data)


class BlockingSetTests(unittest.TestCase):
    def code(self, value):
        with self.assertRaises(ContextError) as caught:
            review_recheck.blocking_set(value)
        return str(caught.exception)

    def test_takes_blocking_missing_and_unknown_but_not_suggestion(self):
        items = review_recheck.blocking_set(report([
            finding('b'), finding('s', 'suggestion'), finding('m', None), finding('u', 'critical')]))
        self.assertEqual([(item['index'], item['title'], item['severity']) for item in items],
                         [(1, 'b', 'blocking'), (2, 'm', 'blocking'), (3, 'u', 'blocking')])
        self.assertEqual(set(items[0]), {'index', 'title', 'file', 'line', 'trigger', 'impact', 'evidence',
                                         'suggestion', 'unverified', 'severity'})

    def test_chained_recheck_takes_unresolved_old_items_then_blocking_new_findings(self):
        recheck = {'previous_report_sha256': 'e' * 64, 'previous_fingerprint': None, 'items': [
            {'index': 1, 'status': 'resolved', 'evidence': 'fixed', 'finding': finding('old-fixed')},
            {'index': 2, 'status': 'unresolved', 'evidence': 'still', 'finding': finding('old-open')}]}
        items = review_recheck.blocking_set(report([finding('new'), finding('tip', 'suggestion')], recheck=recheck))
        self.assertEqual([(item['index'], item['title']) for item in items], [(1, 'old-open'), (2, 'new')])

    def test_empty_set_is_allowed(self):
        self.assertEqual(review_recheck.blocking_set(report()), [])
        self.assertEqual(review_recheck.blocking_set(report([finding('s', 'suggestion')])), [])

    def test_previous_round_without_conclusion_is_invalid(self):
        for values in ({'schema_version': 2}, {'execution_status': 'failed'}, {'review_outcome': 'inconclusive'},
                       {'execution_status': 'conditions_missing'}):
            self.assertEqual(self.code(report([finding('x')], **values)), 'previous_report_invalid', values)

    def test_malformed_structure_is_invalid(self):
        broken = [report(findings='x'), report(scope=None), report([finding('')]), report([finding('x' * 4001)]),
                  report([finding('x', line='1')]), report([finding('x', unverified='no')]),
                  report([finding('x', file=3)]), report([finding('x')] * 101),
                  report(recheck={'items': [{'index': 1, 'status': 'open', 'evidence': 'e', 'finding': finding('x')}]}),
                  report(recheck={'items': 'x'})]
        value = report([finding('x')])
        del value['findings'][0]['impact']
        broken.append(value)
        for value in broken:
            self.assertEqual(self.code(value), 'previous_report_invalid')


class ScopeTests(unittest.TestCase):
    def test_same_scope_and_from_with_new_head_passes(self):
        review_recheck.check_scope(report(), context())

    def test_mismatches(self):
        cases = [(report(), dict(context(), scope={'include': ['src', 'docs'], 'exclude': []})),
                 (report(), dict(context(), scope={'include': ['src'], 'exclude': ['src/x']})),
                 (report(), context(**{'from': 'e' * 40})),
                 (report(), {'scope': copy.deepcopy(SCOPE), 'baseline': {'mode': 'working-tree'}})]
        for previous, current in cases:
            with self.assertRaises(ContextError) as caught:
                review_recheck.check_scope(previous, current)
            self.assertEqual(str(caught.exception), 'previous_report_scope_mismatch')

    def test_criteria_must_match(self):
        # spec/design-review-criteria.md D4: old reports without criteria read as severity-v1.
        review_recheck.check_scope(report(), context())
        review_recheck.check_scope(report(criteria='severity-v1'), context())
        review_recheck.check_scope(report(criteria='design-v1'), dict(context(), profile='design'))
        for previous, current in [(report(), dict(context(), profile='design')),
                                  (report(criteria='design-v1'), context()),
                                  (report(criteria='other'), context())]:
            with self.assertRaises(ContextError) as caught:
                review_recheck.check_scope(previous, current)
            self.assertEqual(str(caught.exception), 'previous_report_scope_mismatch')

    def test_uncommitted_modes_compare_mode_only(self):
        previous = report()
        previous['scope']['baseline'] = {'mode': 'working-tree', 'head': FROM}
        review_recheck.check_scope(previous, {'scope': copy.deepcopy(SCOPE), 'baseline': {'mode': 'working-tree', 'head': TO}})

    def test_source_keeps_sha_and_previous_fingerprint(self):
        value = report()
        self.assertEqual(review_recheck.source(value, 'e' * 64),
                         {'previous_report_sha256': 'e' * 64, 'previous_fingerprint': value['scope']['fingerprint']})
        value['scope']['fingerprint'] = None
        self.assertIsNone(review_recheck.source(value, 'e' * 64)['previous_fingerprint'])


def git(root, *args, env=None):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, env=env).stdout.strip()


def commit(root, message):
    (root / 'plan.md').write_text(message + '\n')
    git(root, 'add', '-A')
    git(root, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '-m', message)
    return git(root, 'rev-parse', 'HEAD')


def snapshot(commit_id, mode='commits'):
    return {'mode': mode, 'from': commit_id, 'to': commit_id}


class SnapshotScopeTests(unittest.TestCase):
    """spec/review-snapshot-recheck.md: snapshot rounds may move forward on the same history."""

    def repository(self, object_format=None):
        temporary = tempfile.TemporaryDirectory(prefix='delegate-snapshot.')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        command = ['init', '-q'] + (['--object-format=' + object_format] if object_format else []) + [str(root)]
        subprocess.run(['git', *command], check=True, capture_output=True, stdin=subprocess.DEVNULL)
        return root

    def check(self, root, previous_baseline, current_baseline, scope=None):
        previous = report()
        previous['scope']['baseline'] = previous_baseline
        current = {'repository': str(root), 'scope': copy.deepcopy(scope or SCOPE), 'baseline': current_baseline}
        review_recheck.check_scope(previous, current)

    def rejects(self, *args, **kwargs):
        with self.assertRaises(ContextError) as caught:
            self.check(*args, **kwargs)
        self.assertEqual(str(caught.exception), 'previous_report_scope_mismatch')

    def test_same_commit_and_descendant_pass(self):
        root = self.repository()
        first = commit(root, 'one')
        second = commit(root, 'two')
        self.check(root, snapshot(first), snapshot(first))
        self.check(root, snapshot(first), snapshot(second))

    def test_sha256_repository_passes(self):
        root = self.repository('sha256')
        first = commit(root, 'one')
        second = commit(root, 'two')
        self.assertEqual(len(first), 64)
        self.check(root, snapshot(first), snapshot(second))
        self.rejects(root, snapshot(first[:40]), snapshot(second))

    def test_other_history_and_missing_commit_are_rejected(self):
        root = self.repository()
        base = commit(root, 'base')
        main = commit(root, 'main')
        git(root, 'checkout', '-q', '-b', 'other', base)
        other = commit(root, 'other')
        self.rejects(root, snapshot(main), snapshot(other))
        self.rejects(root, snapshot('0' * 40), snapshot(other))

    def test_malformed_previous_ids_are_rejected(self):
        root = self.repository()
        first = commit(root, 'one')
        second = commit(root, 'two')
        for value in (first[:12], first.upper(), '--all', 'HEAD', first + 'x'):
            self.rejects(root, snapshot(value), snapshot(second))

    def test_tag_object_is_rejected(self):
        root = self.repository()
        first = commit(root, 'one')
        git(root, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'tag', '-a', '-m', 'tag', 'v1', first)
        tag_object = git(root, 'rev-parse', 'refs/tags/v1')
        second = commit(root, 'two')
        self.assertNotEqual(tag_object, first)
        self.rejects(root, snapshot(tag_object), snapshot(second))

    def test_replace_refs_are_ignored(self):
        root = self.repository()
        base = commit(root, 'base')
        main = commit(root, 'main')
        git(root, 'checkout', '-q', '-b', 'other', base)
        other = commit(root, 'other')
        # Pretend `other` descends from `main`: only the replace ref says so.
        git(root, 'replace', '--graft', other, main)
        self.assertEqual(subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', main, other],
                                        stdin=subprocess.DEVNULL).returncode, 0)
        self.rejects(root, snapshot(main), snapshot(other))

    def test_mixed_snapshot_and_range_are_rejected_both_ways(self):
        root = self.repository()
        first = commit(root, 'one')
        second = commit(root, 'two')
        self.rejects(root, snapshot(first), {'mode': 'commits', 'from': first, 'to': second})
        self.rejects(root, {'mode': 'commits', 'from': first, 'to': second}, snapshot(first))

    def test_different_paths_are_rejected(self):
        root = self.repository()
        first = commit(root, 'one')
        second = commit(root, 'two')
        self.rejects(root, snapshot(first), snapshot(second), scope={'include': ['docs'], 'exclude': []})

    def test_missing_object_in_partial_clone_is_rejected_without_fetching(self):
        source = self.repository()
        first = commit(source, 'one')
        second = commit(source, 'two')
        git(source, 'config', 'uploadpack.allowFilter', 'true')
        clone = Path(tempfile.mkdtemp(prefix='delegate-partial.'))
        self.addCleanup(subprocess.run, ['rm', '-rf', str(clone)])
        result = subprocess.run(['git', 'clone', '-q', '--no-local', '--filter=tree:0', '--depth=1',
                                 'file://' + str(source), str(clone / 'c')], capture_output=True, stdin=subprocess.DEVNULL)
        if result.returncode != 0:
            self.skipTest('partial clone unavailable')
        clone = clone / 'c'
        self.assertNotEqual(subprocess.run(['git', '-C', str(clone), 'cat-file', '-e', first],
                                           env=dict(os.environ, GIT_NO_LAZY_FETCH='1'),
                                           capture_output=True, stdin=subprocess.DEVNULL).returncode, 0)
        self.rejects(clone, snapshot(first), snapshot(second))
        self.assertNotEqual(subprocess.run(['git', '-C', str(clone), 'cat-file', '-e', first],
                                           env=dict(os.environ, GIT_NO_LAZY_FETCH='1'),
                                           capture_output=True, stdin=subprocess.DEVNULL).returncode, 0,
                            'the check must not fetch the missing object')


if __name__ == '__main__':
    unittest.main()
