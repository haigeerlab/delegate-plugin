#!/usr/bin/env python3
"""--continue after a done round, and time-based retention of chain state; Codex is always a fake executable."""
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))
_spec = importlib.util.spec_from_file_location('run_result_tests', Path(__file__).with_name('test-run-result.py'))
shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shared)

SESSION = shared.SESSION
RUN = '20261027140000.111'


class ContinueCheckTests(unittest.TestCase):
    def setUp(self):
        self.state = importlib.import_module('run_state')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-continue-')
        self.dir = Path(self.temp.name)
        self.dir.chmod(0o700)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, status):
        self.state.write_state(self.dir, {'schema': 1, 'runId': RUN, 'sessionId': SESSION, 'repository': str(self.dir),
                                          'write': False, 'model': '', 'effort': '', 'status': status, 'parent': None})

    def test_continue_accepts_only_done(self):
        for status, reason in (('done', None), ('needs-input', 'run not done'), ('timeout', 'run not done'),
                               ('unmarked', 'run not done')):
            self.write(status)
            self.assertEqual(self.state.check_resume(self.dir, RUN, str(self.dir), False, 'continue')[0], reason, status)

    def test_resume_mode_unchanged(self):
        self.write('done')
        self.assertEqual(self.state.check_resume(self.dir, RUN, str(self.dir), False)[0], 'run not waiting for input')
        self.write('needs-input')
        self.assertIsNone(self.state.check_resume(self.dir, RUN, str(self.dir), False, 'resume')[0])

    def test_shared_claim_and_other_refusals(self):
        self.write('done')
        self.assertEqual(self.state.check_resume(self.dir, RUN, str(self.dir), True, 'continue')[0], 'write mode mismatch')
        self.assertEqual(self.state.check_resume(self.dir, RUN, '/', False, 'continue')[0], 'repository mismatch')
        self.assertEqual(self.state.check_resume(self.dir, 'bad', str(self.dir), False, 'continue')[0], 'invalid run id')
        self.assertTrue(self.state.claim_resume(self.dir, RUN))
        self.assertEqual(self.state.check_resume(self.dir, RUN, str(self.dir), False, 'continue')[0], 'run already resumed')


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.state = importlib.import_module('run_state')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-continue-retention-')
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make(self, run_id, suffixes, mtime):
        for suffix in suffixes:
            path = self.dir / (run_id + suffix)
            path.write_text('x', encoding='utf-8')
            os.utime(path, (mtime, mtime))

    def test_suffix_tables(self):
        self.assertEqual(self.state.STATE_RETENTION_DAYS, 14)
        self.assertEqual(set(self.state.STATE_SUFFIXES), {'.state.json', '.resumed', '.result.json'})
        self.assertLessEqual({'.answer', '.wrapup', '.wrapup.answer', '.baseline', '.cleanup', '.events.jsonl',
                              '.wrapup.events.jsonl'}, set(self.state.LOG_SUFFIXES))
        self.assertFalse(set(self.state.LOG_SUFFIXES) & set(self.state.STATE_SUFFIXES))

    def test_logs_by_count_and_state_by_age(self):
        now = time.time()
        logs = ('.log',) + tuple(self.state.LOG_SUFFIXES)
        runs = ['20261001000000.%d' % index for index in range(55)]
        for index, run_id in enumerate(runs):
            # Log files are recent but too many; the state of the oldest groups is only 13 days old.
            self.make(run_id, logs, now - 3600 + index)
            self.make(run_id, self.state.STATE_SUFFIXES, now - 13 * 86400)
        stale = '20260901000000.1'
        self.make(stale, self.state.STATE_SUFFIXES, now - 15 * 86400)
        self.state.cleanup(self.dir, now)
        for run_id in runs[:5]:
            for suffix in logs:
                self.assertFalse((self.dir / (run_id + suffix)).exists(), run_id + suffix)
            for suffix in self.state.STATE_SUFFIXES:
                self.assertTrue((self.dir / (run_id + suffix)).exists(), run_id + suffix)
        for suffix in logs:
            self.assertTrue((self.dir / (runs[5] + suffix)).exists(), runs[5] + suffix)
        for suffix in self.state.STATE_SUFFIXES:
            self.assertFalse((self.dir / (stale + suffix)).exists(), stale + suffix)

    def test_check_log_is_not_a_group_of_its_own(self):
        now = time.time()
        for index in range(50):
            self.make('20261001000000.%d' % index, ('.log', '.check.log'), now - 100 + index)
        self.state.cleanup(self.dir, now)
        self.assertEqual(len(list(self.dir.glob('*.check.log'))), 50)
        self.assertEqual(len([p for p in self.dir.glob('*.log') if not p.name.endswith('.check.log')]), 50)

    def test_cleanup_tolerates_missing_directory(self):
        self.state.cleanup(self.dir / 'missing', time.time())


class ContinueFlowTests(shared.FlowBase):
    def state_of(self, run_id):
        return json.loads((self.logs / (run_id + '.state.json')).read_text(encoding='utf-8'))

    def result_of(self, output):
        line = [l for l in output.stdout.splitlines() if l.startswith('delegate: result=')][0]
        return json.loads(Path(line.split('=', 1)[1]).read_text(encoding='utf-8'))

    def done_chain(self, *args, **env):
        output = self.run_delegate('--resumable', *args, '--', '第一个任务', STUB_ANSWER='DONE: 做完', **env)
        self.assertEqual(output.returncode, 0, output.stderr)
        return self.run_id(output)

    def test_continue_runs_the_next_task_in_the_same_session(self):
        first = self.done_chain('--model', 'gpt-x', '--effort', 'low')
        later = dict(shared.USAGE, input_tokens=201493)
        output = self.run_delegate('--continue', first, '--', '第二个任务', STUB_RESUME_ANSWER='完成第二个',
                                   STUB_RESUME_EVENTS=json.dumps([{'type': 'turn.completed', 'usage': later}]))
        self.assertEqual(output.returncode, 0, output.stderr)
        call = self.exec_calls()[-1]
        self.assertEqual(call[:2], ['exec', 'resume'])
        self.assertIn('-m', call)
        self.assertEqual(call[call.index('-m') + 1], 'gpt-x')
        self.assertIn('model_reasoning_effort="low"', call)
        self.assertIn('approval_policy="never"', call)
        self.assertIn('sandbox_mode="read-only"', call)
        self.assertEqual(call[call.index('-o') - 1], '--json')
        self.assertEqual(call[-2], SESSION)
        self.assertTrue(call[-1].startswith('【下一个任务】第二个任务\n\n上一个任务已经结束。请在本会话里接着做这个新任务，'
                                            '沿用之前的约定：先做不受待定决策影响的部分；需要用户拍板时，最终答复第一行以 `NEED_USER:` 开头。'
                                            '\n\n【时间预算】'), call[-1])
        second = self.run_id(output)
        state = self.state_of(second)
        self.assertEqual((state['parent'], state['chainRoot'], state['kind'], state['status']),
                         (first, first, 'continue', 'done'))
        result = self.result_of(output)
        self.assertEqual((result['kind'], result['parent'], result['chainRoot']), ('continue', first, first))
        self.assertEqual(result['usage']['run']['inputTokens'], 201493 - 124735)
        third = self.run_delegate('--continue', second, '--', '第三个任务')
        self.assertEqual(self.state_of(self.run_id(third))['chainRoot'], first)

    def test_refusals_do_not_start_codex(self):
        first = self.done_chain()
        waiting = self.run_id(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 问'))
        no_session = self.run_id(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='DONE: x', STUB_SESSION=''))
        other = self.base / 'other'
        other.mkdir()
        self.subprocess.run(['git', 'init', '-q'], cwd=other, check=True)
        before = len(self.exec_calls())
        cases = [
            (('--continue', 'bad-id', '--', '任务'), 'delegate: invalid run id'),
            (('--continue', '20261001000000.1', '--', '任务'), 'delegate: run not found'),
            (('--continue', no_session, '--', '任务'), 'delegate: run not resumable'),
            (('--continue', waiting, '--', '任务'), 'delegate: run not done'),
            (('--continue', first, '--write', '--', '任务'), 'delegate: write mode mismatch'),
        ]
        for args, message in cases:
            output = self.run_delegate(*args)
            self.assertEqual(output.returncode, 64, args)
            self.assertEqual(output.stderr.strip().splitlines()[-1], message, args)
        output = self.subprocess.run(['/bin/bash', str(shared.PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run',
                                      '--continue', first, '--', '任务'], cwd=other, env=self.env,
                                     capture_output=True, text=True, timeout=60)
        self.assertEqual((output.returncode, output.stderr.strip().splitlines()[-1]), (64, 'delegate: repository mismatch'))
        for args in (('--continue', first, '--resumable', '--', '任务'), ('--continue', first, '--resume', first, '--', '任务'),
                     ('--continue', first, '--model', 'gpt-x', '--', '任务'), ('--continue', first, '--effort', 'low', '--', '任务'),
                     ('--continue', first, '--', '   ')):
            self.assertEqual(self.run_delegate(*args).returncode, 64, args)
        self.assertEqual(len(self.exec_calls()), before)

    def test_one_successor_per_run(self):
        first = self.done_chain()
        self.assertEqual(self.run_delegate('--continue', first, '--', '下一个').returncode, 0)
        again = self.run_delegate('--continue', first, '--', '再来')
        self.assertEqual((again.returncode, again.stderr.strip().splitlines()[-1]), (64, 'delegate: run already resumed'))
        resumed = self.run_delegate('--resume', first, '--', '答复')
        self.assertEqual(resumed.returncode, 64)
        waiting = self.run_id(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 问'))
        self.assertEqual(self.run_delegate('--resume', waiting, '--', '答复', STUB_RESUME_ANSWER='DONE: 好').returncode, 0)
        # --resume and --continue accept disjoint statuses, so the other entry is refused by status first.
        late = self.run_delegate('--continue', waiting, '--', '下一个')
        self.assertEqual((late.returncode, late.stderr.strip().splitlines()[-1]), (64, 'delegate: run not done'))

    def test_resume_on_done_still_refused_with_old_text(self):
        first = self.done_chain()
        output = self.run_delegate('--resume', first, '--', '答复')
        self.assertEqual((output.returncode, output.stderr.strip().splitlines()[-1]), (64, 'delegate: run not waiting for input'))

    def test_write_continue_prints_git_acceptance(self):
        first = self.done_chain('--write')
        output = self.run_delegate('--continue', first, '--write', '--', '写入任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertIn('git 验收', output.stdout)
        self.assertIn('sandbox_mode="workspace-write"', self.exec_calls()[-1])


if __name__ == '__main__':
    unittest.main()
