#!/usr/bin/env python3
"""Exercise the suite runner with offline subprocess fixtures."""
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'run_suites.py'
SPEC = importlib.util.spec_from_file_location('run_suites', RUNNER)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.suites = {'alpha': 'tests/test-alpha.py',
                       'beta': 'tests/test-beta.sh',
                       'gamma': 'tests/test-gamma.py'}
        self.sources = {'tests/test-alpha.py': '# worker.py and config.v2.json',
                        'tests/test-beta.sh': '# worker and other-tool',
                        'tests/test-gamma.py': '# coworker worker_extra worker2 _worker'}

    def select(self, paths):
        return runner.select_suites(paths, self.suites, self.sources.__getitem__)

    def test_suite_file_selects_itself_and_suites_that_load_it(self):
        self.assertEqual(self.select(['tests/test-alpha.py']),
                         (['alpha'], ['alpha: tests/test-alpha.py']))
        # Suites load helpers from other suite files (spec_from_file_location, test-channel.sh --live).
        self.sources['tests/test-gamma.py'] = "spec_from_file_location('x', HERE / 'test-alpha.py')"
        self.assertEqual(self.select(['tests/test-alpha.py']),
                         (['alpha', 'gamma'], ['alpha: tests/test-alpha.py', 'gamma: tests/test-alpha.py']))
        self.suites['doc-suite'] = 'docs/test-doc.py'
        self.assertEqual(self.select(['docs/test-doc.py']),
                         (['doc-suite'], ['doc-suite: docs/test-doc.py']))

    def test_docs_and_root_markdown_select_no_suites(self):
        self.assertEqual(self.select(['docs/nested/worker.py', 'spec/worker.md',
                                      'tasks/worker.md', 'README.md']), ([], []))

    def test_stems_match_all_suites_as_whole_words(self):
        self.assertEqual(self.select(['plugins/delegate/scripts/worker.py']),
                         (['alpha', 'beta'],
                          ['alpha: plugins/delegate/scripts/worker.py',
                           'beta: plugins/delegate/scripts/worker.py']))

    def test_full_basename_and_regex_metacharacters_are_literal(self):
        self.sources['tests/test-beta.sh'] = '# configXv2.json'
        self.assertEqual(self.select(['settings/config.v2.json']),
                         (['alpha'], ['alpha: settings/config.v2.json']))

    def test_paths_accumulate_without_duplicate_reasons_in_suite_order(self):
        self.assertEqual(self.select(['src/worker.py', 'src/other-tool.sh', 'src/worker.py']),
                         (['alpha', 'beta'], ['alpha: src/worker.py',
                                              'beta: src/other-tool.sh, src/worker.py']))

    def test_plugin_markdown_is_not_doc_only(self):
        self.sources['tests/test-beta.sh'] = '# guide.md'
        self.assertEqual(self.select(['plugins/delegate/skills/guide.md']),
                         (['beta'], ['beta: plugins/delegate/skills/guide.md']))

    def test_unknown_paths_force_all_even_after_another_path_matches(self):
        for path in ('src/unknown.py', 'nested/README.md', 'plugins/delegate/commands/new.md'):
            with self.subTest(path=path):
                selected, reasons = self.select(['src/worker.py', path])
                self.assertIsNone(selected)
                self.assertIn(path, ' '.join(reasons))

    def test_runner_validator_and_github_always_force_all(self):
        for path in ('scripts/validate.sh', 'scripts/run_suites.py', '.github/workflows/ci.yml'):
            with self.subTest(path=path):
                self.suites['special'] = path
                selected, reasons = self.select([path])
                self.assertIsNone(selected)
                self.assertIn(path, ' '.join(reasons))

    def test_suites_globbing_the_changed_directory_are_selected(self):
        self.sources['tests/test-gamma.py'] = "for path in (PLUGIN / 'scripts').glob('*.py'): pass"
        self.sources['tests/test-beta.sh'] = "COMMANDS = PLUGIN / 'commands'\nCOMMANDS.glob('*.md')"
        self.assertEqual(self.select(['plugins/delegate/scripts/worker.py'])[0], ['alpha', 'gamma'])
        self.assertEqual(self.select(['plugins/delegate/scripts/fresh.py']),
                         (['gamma'], ['gamma: plugins/delegate/scripts/fresh.py']))
        self.assertEqual(self.select(['plugins/delegate/commands/fresh.md']),
                         (['beta'], ['beta: plugins/delegate/commands/fresh.md']))
        # Same suffix in another directory, or another suffix, is not a glob match.
        self.assertIsNone(self.select(['plugins/delegate/hooks/fresh.py'])[0])
        self.assertIsNone(self.select(['plugins/delegate/scripts/fresh.sh'])[0])

    def test_no_changes_selects_nothing_with_reason(self):
        self.assertEqual(self.select([]), ([], ['no changes against origin/main']))


class DependentTests(unittest.TestCase):
    def test_product_files_that_use_a_changed_file_count_as_changed(self):
        sources = {'plugins/p/scripts/base.py': 'VALUE = 1\n',
                   'plugins/p/scripts/middle.py': 'from base import VALUE\n',
                   'plugins/p/scripts/top.py': 'import middle\n',
                   'plugins/p/scripts/other.py': 'import baseline\n'}
        expanded, notes = runner.expand_dependents(['plugins/p/scripts/base.py', 'docs/x.md'], sources)
        self.assertEqual(expanded, ['docs/x.md', 'plugins/p/scripts/base.py',
                                    'plugins/p/scripts/middle.py', 'plugins/p/scripts/top.py'])
        self.assertEqual(notes, ['plugins/p/scripts/middle.py (uses plugins/p/scripts/base.py)',
                                 'plugins/p/scripts/top.py (uses plugins/p/scripts/middle.py)'])

    def test_deleted_product_files_still_expand(self):
        sources = {'plugins/p/scripts/user.py': 'import gone\n'}
        self.assertEqual(runner.expand_dependents(['plugins/p/scripts/gone.py'], sources),
                         (['plugins/p/scripts/gone.py', 'plugins/p/scripts/user.py'],
                          ['plugins/p/scripts/user.py (uses plugins/p/scripts/gone.py)']))

    def test_non_product_changes_are_not_expanded(self):
        sources = {'plugins/p/scripts/a.py': 'import notes\n'}
        self.assertEqual(runner.expand_dependents(['notes.txt'], sources), (['notes.txt'], []))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='delegate-run-suites.')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def suite(self, label, code, *args):
        script = self.root / (label + ' fixture.py')
        script.write_text(code, encoding='utf-8')
        return label, label + ' 回归测试未通过', [sys.executable, '-B', str(script), *args]

    def run_suites(self, suites, *options, payload=None):
        if payload is None:
            fields = []
            for label, failure, argv in suites:
                fields.extend([label, failure, str(len(argv)), *argv])
            payload = b''.join(os.fsencode(field) + b'\0' for field in fields)
        return subprocess.run([sys.executable, '-B', str(RUNNER), *options],
                              input=payload, capture_output=True, timeout=15)


    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.root), *args],
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.decode().strip()

    def commit(self):
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.invalid',
                 'commit', '-m', 'fixture')

    def quick_fixture(self, with_base=True):
        suites = [self.suite('alpha', '# widget.py\nprint("alpha")\n'),
                  self.suite('beta', '# widget\nprint("beta")\n'),
                  self.suite('gamma', 'print("gamma")\n')]
        self.git('init')
        (self.root / 'widget.py').write_text('# baseline\n')
        self.git('add', '.')
        self.commit()
        if with_base:
            self.git('update-ref', 'refs/remotes/origin/main', self.git('rev-parse', 'HEAD'))
        return suites

    def test_quick_git_changes_select_only_suites_that_mention_product(self):
        suites = self.quick_fixture()
        for state in ('committed', 'staged', 'unstaged', 'untracked'):
            with self.subTest(state=state):
                self.git('reset', '--hard', 'origin/main')
                if state == 'untracked':
                    self.git('rm', 'widget.py')
                    self.commit()
                    self.git('update-ref', 'refs/remotes/origin/main', self.git('rev-parse', 'HEAD'))
                (self.root / 'widget.py').write_text('# ' + state + '\n')
                if state in ('committed', 'staged'):
                    self.git('add', 'widget.py')
                if state == 'committed':
                    self.commit()
                result = self.run_suites(suites, '--quick', '--root', str(self.root), '--jobs', '2')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b'alpha\nbeta\n')
                self.assertTrue(result.stderr.startswith(b'validate: quick: 2 of 3 suites\n'))
                self.assertIn(b'validate: quick: alpha: widget.py\n', result.stderr)
                self.assertIn(b'validate: quick: beta: widget.py\n', result.stderr)
                self.assertNotIn(b'gamma:', result.stderr)

    def test_quick_rename_reports_old_and_new_names(self):
        suites = self.quick_fixture()
        self.git('mv', 'widget.py', 'renamed.py')
        result = self.run_suites(suites, '--quick', '--root', str(self.root))
        # renamed.py matches no suite, so quick must fall back; the old name must be in the change set.
        self.assertIn(b'running all suites', result.stderr)
        self.assertEqual(sorted(runner.git_changed_paths(self.root)), ['renamed.py', 'widget.py'])

    def test_merged_streams_keep_each_suite_together(self):
        code = 'import sys\nprint("OUT-%s", flush=True)\nprint("ERR-%s", file=sys.stderr, flush=True)\n'
        suites = [self.suite(name, code % (name, name)) for name in ('one', 'two')]
        fields = []
        for label, failure, argv in suites:
            fields.extend([label, failure, str(len(argv)), *argv])
        payload = b''.join(os.fsencode(field) + b'\0' for field in fields)
        result = subprocess.run([sys.executable, '-B', str(RUNNER)], input=payload,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
        lines = [line for line in result.stdout.decode().splitlines() if 'OUT-' in line or 'ERR-' in line]
        self.assertEqual(lines, ['OUT-one', 'ERR-one', 'OUT-two', 'ERR-two'])

    def test_quick_without_origin_main_falls_back_to_all(self):
        suites = self.quick_fixture(with_base=False)
        result = self.run_suites(suites, '--jobs', '1', '--root', str(self.root), '--quick')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'alpha\nbeta\ngamma\n')
        self.assertTrue(result.stderr.startswith(
            b'validate: quick: running all suites (no merge base with origin/main)\n'))

    def test_quick_with_no_changes_or_docs_only_runs_no_suites(self):
        suites = self.quick_fixture()
        for docs_only in (False, True):
            with self.subTest(docs_only=docs_only):
                if docs_only:
                    (self.root / 'README.md').write_text('fixture docs\n')
                result = self.run_suites(suites, '--quick', '--root', str(self.root))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b'')
                self.assertIn(b'validate: quick: 0 of 3 suites\n', result.stderr)
                if not docs_only:
                    self.assertIn(b'no changes against origin/main', result.stderr)

    def test_quick_selected_failure_keeps_isolation_and_failure_message(self):
        suites = self.quick_fixture()
        suites[0] = self.suite('alpha', '# widget.py\nimport os\n'
                               'print(os.environ["TMPDIR"])\nraise SystemExit(7)\n')
        result = self.run_suites(suites, '--quick', '--root', str(self.root))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(b'validate: quick: 1 of 3 suites\n', result.stderr)
        self.assertIn(('validate: ' + suites[0][1]).encode(), result.stderr)
        self.assertIn(b'validate: slowest suites:', result.stderr)
        self.assertFalse(Path(result.stdout.decode().strip()).exists())

    def test_serial_and_parallel_success_and_failure_match(self):
        for status in (0, 7):
            with self.subTest(status=status):
                suites = [self.suite('first', 'print("first")\n'),
                          self.suite('second', 'import time\ntime.sleep(0.03)\n'
                                     'print("second")\nraise SystemExit(%d)\n' % status),
                          self.suite('third', 'print("third")\n')]
                results = [self.run_suites(suites, '--jobs', str(jobs)) for jobs in (1, 4)]
                for result in results:
                    self.assertEqual(result.returncode, 1 if status else 0, result.stderr)
                    self.assertEqual(result.stdout, b'first\nsecond\nthird\n')
                    failures = [line for line in result.stderr.splitlines()
                                if '未通过'.encode() in line]
                    expected = [('validate: ' + suites[1][1]).encode()] if status else []
                    self.assertEqual(failures, expected)

    def test_tmpdirs_are_distinct_inherited_environment_is_kept_and_dirs_removed(self):
        suites = [self.suite(str(index), '''import os
from pathlib import Path
import sys
assert sys.stdin.buffer.read() == b''
assert os.environ['RUN_SUITES_SENTINEL'] == 'inherited'
directory = Path(os.environ['TMPDIR'])
assert directory.is_dir()
(directory / 'nested').mkdir()
(directory / 'nested' / 'marker').write_text('fixture')
print(directory)
raise SystemExit(int(sys.argv[1]))
''', str(index % 2)) for index in range(4)]
        from unittest.mock import patch
        with patch.dict(os.environ, {'RUN_SUITES_SENTINEL': 'inherited'}):
            result = self.run_suites(suites, '--jobs', '4')
        self.assertEqual(result.returncode, 1, result.stderr)
        paths = result.stdout.decode().splitlines()
        self.assertEqual(len(paths), 4)
        self.assertEqual(len(set(paths)), 4)
        for path in paths:
            self.assertFalse(Path(path).exists(), path)

    def test_each_suite_gets_an_empty_private_config_home(self):
        # spec/default-model.md: suites must never read the user's real ~/.config/delegate.
        suites = [self.suite(str(index), '''import os
from pathlib import Path
home = Path(os.environ['XDG_CONFIG_HOME'])
assert home.is_absolute() and home.is_dir() and not any(home.iterdir())
assert home != Path('/should/not/leak')
print(home)
''') for index in range(3)]
        from unittest.mock import patch
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': '/should/not/leak'}):
            result = self.run_suites(suites, '--jobs', '3')
        self.assertEqual(result.returncode, 0, result.stderr)
        paths = result.stdout.decode().splitlines()
        self.assertEqual(len(set(paths)), 3)

    def test_concurrent_large_binary_output_is_replayed_in_list_order(self):
        suites = []
        for label in ('first', 'second'):
            suites.append(self.suite(label, '''from pathlib import Path
import sys
import time
root, label = Path(sys.argv[1]), sys.argv[2]
(root / label).touch()
deadline = time.monotonic() + 5
while not all((root / name).exists() for name in ('first', 'second')):
    if time.monotonic() > deadline:
        raise SystemExit('suites did not overlap')
    time.sleep(0.005)
if label == 'first':
    time.sleep(0.05)
for _ in range(32):
    sys.stdout.buffer.write(label.encode() + b'\\xff' * 4096)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(label.encode() + b'\\xfe' * 4096)
    sys.stderr.buffer.flush()
    time.sleep(0.001)
''', str(self.root), label))
        result = self.run_suites(suites, '--jobs', '4')
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        expected_stdout = b''.join((label.encode() + b'\xff' * 4096) * 32
                                   for label in ('first', 'second'))
        expected_stderr = b''.join((label.encode() + b'\xfe' * 4096) * 32
                                   for label in ('first', 'second'))
        self.assertEqual(result.stdout, expected_stdout)
        self.assertTrue(result.stderr.startswith(expected_stderr))
        self.assertIn(b'validate: slowest suites:', result.stderr[len(expected_stderr):])

    def test_reports_five_slowest_suites_and_pool_wall_clock(self):
        suites = [self.suite('slow', 'import time\ntime.sleep(0.3)\n')]
        suites.extend(self.suite('fast-%d' % index, 'pass\n') for index in range(5))
        result = self.run_suites(suites, '--jobs', '4')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = result.stderr.decode()
        self.assertIn('validate: slowest suites:\n', report)
        entries = re.findall(r'^validate:   (.+): ([0-9]+\.[0-9])s$', report, re.M)
        self.assertEqual(len(entries), 5, report)
        self.assertEqual(entries[0][0], 'slow')
        self.assertEqual([float(seconds) for _, seconds in entries],
                         sorted((float(seconds) for _, seconds in entries), reverse=True))
        self.assertRegex(report, r'validate: pool wall-clock: [0-9]+\.[0-9]s\n$')

    def test_default_jobs_and_argv_boundaries(self):
        suite = self.suite('argv', 'import os, sys\n'
                           'sys.stdout.buffer.write(b"\\0".join(os.fsencode(x) for x in sys.argv[1:]))\n',
                           '', 'with spaces', '--jobs', 'literal; $HOME', '中文')
        result = self.run_suites([suite])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'\0with spaces\0--jobs\0literal; $HOME\0' + '中文'.encode())

    def test_missing_command_is_a_suite_failure(self):
        failure = 'missing command failed'
        result = self.run_suites([('missing', failure, [str(self.root / 'missing')])])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(('validate: ' + failure + '\n').encode(), result.stderr)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_bad_arguments_exit_64_with_usage_on_stderr(self):
        for args in (('--jobs',), ('--jobs', '0'), ('--jobs', '-1'), ('--jobs', '1.5'),
                     ('--jobs', 'bad'), ('--unknown',), ('--root',), ('--job', '2')):
            with self.subTest(args=args):
                result = self.run_suites([], *args)
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertIn(b'usage:', result.stderr)
                self.assertEqual(result.stdout, b'')

    def test_malformed_entries_exit_64(self):
        for payload in (b'not-terminated', b'label\0failure\0', b'label\0failure\0bad\0',
                        b'label\0failure\0' + b'0\0', b'label\0failure\0' + b'2\0only-one\0'):
            with self.subTest(payload=payload):
                result = self.run_suites([], payload=payload)
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertIn(b'usage:', result.stderr)
                self.assertNotIn(b'Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
