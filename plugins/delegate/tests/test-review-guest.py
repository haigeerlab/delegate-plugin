#!/usr/bin/env python3
"""Offline snapshot/guest-boundary tests, without SSH or a VM."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('review_guest', SCRIPTS / 'review_guest.py')
guest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guest)


class GuestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-guest.')
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        self.target = self.root / 'target'
        self.source.mkdir(mode=0o700)
        self.target.mkdir(mode=0o700)
        (self.source / 'module').mkdir()
        (self.source / 'module' / 'code.py').write_bytes(b'print("fixture")\n')
        (self.source / 'excluded.txt').write_text('not in scope')

    def tearDown(self):
        self.temp.cleanup()

    def wire(self):
        return guest.pack_snapshot(self.source, ['module/code.py'])

    def test_fixed_scope_roundtrip_retains_bytes_and_only_included_files(self):
        files = guest.unpack_snapshot(self.wire(), self.target)
        self.assertEqual(files, ['module/code.py'])
        self.assertEqual((self.target / files[0]).read_bytes(), b'print("fixture")\n')
        self.assertFalse((self.target / 'excluded.txt').exists())
        self.assertEqual((self.target / files[0]).stat().st_mode & 0o777, 0o600)

    def test_source_symlink_directory_link_and_hardlink_are_rejected(self):
        (self.source / 'link').symlink_to(self.source / 'module' / 'code.py')
        (self.source / 'dir-link').symlink_to(self.source / 'module')
        os.link(self.source / 'module' / 'code.py', self.source / 'hardlink')
        for path in ['link', 'dir-link/code.py', 'hardlink']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                guest.pack_snapshot(self.source, [path])

    def test_traversal_absolute_git_and_duplicate_paths_are_rejected(self):
        for paths in [['../escape'], ['/absolute'], ['.git/config'], ['a/../b'],
                      ['a\\b'], ['a\nb'], ['module/code.py', 'module/code.py']]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                guest.pack_snapshot(self.source, paths)

    def test_tampered_hash_or_bytes_fail_before_any_write(self):
        for field, value in [('sha256', '0' * 64), ('data', 'not valid base64')]:
            document = json.loads(self.wire())
            document['files'][0][field] = value
            with self.assertRaises(ValueError):
                guest.unpack_snapshot(json.dumps(document).encode(), self.target)
            self.assertEqual(list(self.target.iterdir()), [])

    def test_invalid_later_record_does_not_leave_partial_snapshot(self):
        document = json.loads(self.wire())
        document['files'].append(dict(document['files'][0], path='../outside'))
        with self.assertRaises(ValueError):
            guest.unpack_snapshot(json.dumps(document).encode(), self.target)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_nonempty_target_and_target_alias_are_refused(self):
        (self.target / 'existing').write_text('untouched')
        with self.assertRaises(ValueError):
            guest.unpack_snapshot(self.wire(), self.target)
        self.assertEqual((self.target / 'existing').read_text(), 'untouched')
        alias = self.root / 'alias'
        alias.symlink_to(self.target)
        with self.assertRaises(ValueError):
            guest.unpack_snapshot(self.wire(), alias)

    def test_resource_limits_and_unknown_schema_are_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            guest.pack_snapshot(self.source, ['module/code.py'], max_bytes=2)
        for change in [{'schema_version': True}, {'extra': 'unknown'}, {'files': []}]:
            document = json.loads(self.wire())
            document.update(change)
            with self.assertRaises(ValueError):
                guest.unpack_snapshot(json.dumps(document).encode(), self.target)
        with self.assertRaises(ValueError):
            guest.unpack_snapshot(b'{"schema_version":1,"schema_version":1,"files":[]}', self.target)

    def test_file_directory_collision_is_rejected_before_write(self):
        document = json.loads(self.wire())
        first = document['files'][0]
        document['files'] = [dict(first, path='a'), dict(first, path='a-1'), dict(first, path='a/b')]
        with self.assertRaises(ValueError):
            guest.unpack_snapshot(json.dumps(document).encode(), self.target)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_plain_vm_configuration_rejects_shares_forwarding_or_provisioning(self):
        safe = {'plain': True, 'mounts': [], 'portForwards': [], 'provision': [],
                'ssh': {'forwardAgent': False}, 'containerd': {'system': False, 'user': False},
                'rosetta': {'enabled': False}}
        guest.validate_configuration(safe)
        for key, value in [('plain', False), ('mounts', [{'location': '~'}]),
                           ('portForwards', [{'static': True}]), ('provision', [{}]),
                           ('ssh', {'forwardAgent': True}), ('containerd', {'system': True}),
                           ('rosetta', {'enabled': True})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                guest.validate_configuration(dict(safe, **{key: value}))
        with self.assertRaises(ValueError):
            guest.validate_configuration({'plain': True})

    def test_exclusive_lease_never_reclaims_existing_lock(self):
        lease = guest.GuestLease(self.root, 'delegate-review-fixture')
        with lease:
            with self.assertRaises(FileExistsError):
                with guest.GuestLease(self.root, 'delegate-review-fixture'):
                    self.fail('concurrent guest use allowed')
        with guest.GuestLease(self.root, 'delegate-review-fixture'):
            pass

    def test_release_does_not_remove_a_replaced_ownership_record(self):
        lease = guest.GuestLease(self.root, 'delegate-review-fixture')
        lease.__enter__()
        lease.path.unlink()
        lease.path.write_text('other owner')
        with self.assertRaises(ValueError):
            lease.__exit__(None, None, None)
        self.assertEqual(lease.path.read_text(), 'other owner')


class GuestPromptTests(unittest.TestCase):
    """spec/review-snapshot-recheck.md SR-04: the guest rebuilds the context from the request and uses the Claude prompt."""

    def test_context_files_reach_the_guest_prompt(self):
        import sys
        from types import SimpleNamespace
        sys.path.insert(0, str(SCRIPTS))
        import claude_review
        import review_transport
        from review_context import CONTEXT_FILES_INSTRUCTION
        context = {'files': {'src/a.py': b'first\n'}, 'unreviewed': [], 'scope': {'include': ['src/a.py'], 'exclude': []},
                   'baseline': {'mode': 'commits'}, 'diff_sha256': 'a' * 64, 'file_sha256': {'src/a.py': 'b' * 64},
                   'allowed_tools': ['Read'], 'context_files': ['spec/a.md']}
        profile = {'guest_runtime_config': {}, 'guest_runtime_sha256': '0' * 64}
        request = json.loads(review_transport.request_payload(context, {}, 'run', profile, 30))
        rebuilt = dict(request['context'], files=context['files'])
        self.assertEqual(rebuilt['context_files'], ['spec/a.md'])
        prompts = []
        def invoke(argv, *, deadline, stdin=None):
            if '-p' in argv:
                prompts.append(stdin.decode('utf-8'))
                return {'execution_status': 'failed', 'cleanup': 'confirmed', 'diagnostics': [], 'stdout': b''}
            raise OSError()
        original = claude_review.preflight
        self.addCleanup(setattr, claude_review, 'preflight', original)
        claude_review.preflight = lambda executable, invoker: {'version': 'x', 'auth_method': 'm', 'provider': 'p'}
        args = SimpleNamespace(model=None, max_turns=12, max_budget_usd=None, task='TASK-MARKER')
        claude_review.execute('/opt/claude', args, rebuilt, invoke, timeout=30)
        self.assertLess(prompts[0].index(CONTEXT_FILES_INSTRUCTION), prompts[0].index('Task: TASK-MARKER'))

    def test_design_profile_reaches_the_guest_prompt(self):
        import sys
        sys.path.insert(0, str(SCRIPTS))
        import review_transport
        from review_context import DESIGN_CRITERIA, task_prompt
        context = {'files': {'src/a.py': b'x\n'}, 'file_sha256': {'src/a.py': 'b' * 64}, 'unreviewed': [],
                   'profile': 'design'}
        profile = {'guest_runtime_config': {}, 'guest_runtime_sha256': '0' * 64}
        request = json.loads(review_transport.request_payload(context, {}, 'run', profile, 30))
        self.assertEqual(request['context']['profile'], 'design')
        self.assertIn(DESIGN_CRITERIA, task_prompt('TASK-MARKER', dict(request['context'], files=context['files'])))


if __name__ == '__main__':
    unittest.main(verbosity=2)
