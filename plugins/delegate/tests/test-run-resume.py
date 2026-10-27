#!/usr/bin/env python3
"""Resumable run state, result line and --resume flow; Codex is always a fake executable."""
import importlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))

SESSION = '01a15f3b-0f2c-7d82-b5cc-7a1f711c11d2'
RUN = '20261024183015.12345'


class RunStateUnitTests(unittest.TestCase):
    def setUp(self):
        self.state = importlib.import_module('run_state')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-state-')
        self.dir = Path(self.temp.name)
        self.dir.chmod(0o700)

    def tearDown(self):
        self.temp.cleanup()

    def record(self, **changes):
        value = {'schema': 1, 'runId': RUN, 'sessionId': SESSION, 'repository': str(self.dir.resolve()),
                 'write': False, 'model': '', 'effort': '', 'status': 'needs-input', 'parent': None}
        value.update(changes)
        self.state.write_state(self.dir, value)
        return value

    def test_run_id_format(self):
        for value in (RUN, '20261024183015.1'):
            self.assertTrue(self.state.valid_run_id(value), value)
        for value in ('', '../x', '1.2', RUN + '/', RUN + '\n', '2026102418301.1', '20261024183015.', 'a' * 14 + '.1'):
            self.assertFalse(self.state.valid_run_id(value), repr(value))

    def test_session_id_from_log(self):
        log = self.dir / 'run.log'
        log.write_text('OpenAI Codex v0.162.1\n--------\nmodel: x\nsession id: %s\n--------\nuser\n'
                       'session id: 11111111-1111-1111-1111-111111111111\n' % SESSION, encoding='utf-8')
        self.assertEqual(self.state.session_id_from_log(log), SESSION)
        log.write_text('no header\nsession id: not-a-uuid\n', encoding='utf-8')
        self.assertIsNone(self.state.session_id_from_log(log))
        self.assertIsNone(self.state.session_id_from_log(self.dir / 'missing.log'))

    def test_classify(self):
        self.assertEqual(self.state.classify('NEED_USER: 选 A 还是 B？\n进度：T1 完成'),
                         ('needs-input', '选 A 还是 B？\n进度：T1 完成'))
        self.assertEqual(self.state.classify('\n  ﻿NEED_USER:问题'), ('needs-input', '问题'))
        self.assertEqual(self.state.classify('完成了。\nNEED_USER: 不在第一行'), ('done', None))
        self.assertEqual(self.state.classify('need_user: 小写不算'), ('done', None))

    def test_state_round_trip_and_permissions(self):
        value = self.record()
        path = self.dir / (RUN + '.state.json')
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(self.state.read_state(self.dir, RUN), value)
        self.assertIsNone(self.state.read_state(self.dir, '20261024183015.99'))
        self.assertIsNone(self.state.read_state(self.dir, '../x'))

    def test_state_rejects_symlinks(self):
        target = self.dir / 'elsewhere.json'
        target.write_text('{}', encoding='utf-8')
        (self.dir / (RUN + '.state.json')).symlink_to(target)
        self.assertIsNone(self.state.read_state(self.dir, RUN))
        linked = self.dir / 'linked'
        linked.symlink_to(self.dir)
        with self.assertRaises(OSError):
            self.state.write_state(linked, {'runId': '20261024183015.2'})

    def test_claim_is_exclusive(self):
        self.assertTrue(self.state.claim_resume(self.dir, RUN))
        self.assertFalse(self.state.claim_resume(self.dir, RUN))
        self.assertEqual(stat.S_IMODE((self.dir / (RUN + '.resumed')).stat().st_mode), 0o600)

    def check(self, run_id=RUN, repository=None, write=False):
        return self.state.check_resume(self.dir, run_id, repository or str(self.dir), write)

    def test_check_resume_accepts_waiting_run(self):
        value = self.record()
        self.assertEqual(self.check(), (None, value))

    def test_check_resume_refusals(self):
        self.assertEqual(self.check('../x')[0], 'invalid run id')
        self.assertEqual(self.check()[0], 'run not found')
        self.record(sessionId=None)
        self.assertEqual(self.check()[0], 'run not resumable')
        self.record(status='done')
        self.assertEqual(self.check()[0], 'run not waiting for input')
        self.record()
        other = tempfile.TemporaryDirectory(prefix='delegate-other-repo-')
        self.addCleanup(other.cleanup)
        self.assertEqual(self.check(repository=other.name)[0], 'repository mismatch')
        self.assertEqual(self.check(write=True)[0], 'write mode mismatch')
        self.state.claim_resume(self.dir, RUN)
        self.assertEqual(self.check()[0], 'run already resumed')


FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
if args == ["--version"]:
    print("codex stub 1.0")
    raise SystemExit(0)
if args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT")
    raise SystemExit(0)
with open(os.environ["STUB_CALL_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args, ensure_ascii=False) + "\n")
if os.environ.get("STUB_SESSION"):
    # delegate runs Codex with --json: the session id arrives as a thread.started event.
    if "--json" in args:
        print(json.dumps({"type": "thread.started", "thread_id": os.environ["STUB_SESSION"]}))
    else:
        print("OpenAI Codex v0.162.1\n--------\nsession id: " + os.environ["STUB_SESSION"] + "\n--------")
for index, arg in enumerate(args[:-1]):
    if arg == "-o":
        with open(args[index + 1], "w", encoding="utf-8") as answer:
            answer.write(os.environ.get("STUB_ANSWER", "fake answer\n"))
if os.environ.get("STUB_TOUCH"):
    open(os.environ["STUB_TOUCH"], "w").close()
raise SystemExit(int(os.environ.get("STUB_EXIT", "0")))
'''
RESULT_LINE = r'^delegate: run_id=([0-9]{14}\.[0-9]+) status=(done|needs-input) resumable=(true|false)$'


class RunFlowTests(unittest.TestCase):
    def setUp(self):
        import subprocess
        self.subprocess = subprocess
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-resume-')
        self.base = Path(self.temp.name)
        (self.base / 'bin').mkdir()
        fake = self.base / 'bin' / 'codex'
        fake.write_text(FAKE_CODEX, encoding='utf-8')
        fake.chmod(0o755)
        (self.base / 'tmp').mkdir()
        self.logs = self.base / 'tmp' / 'delegate'
        self.calls = self.base / 'calls.log'
        self.repo = self.make_repo('repo')
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'DELEGATE_REVIEW_DEPTH')}
        self.env.update(PATH='%s:%s:/usr/bin:/bin' % (self.base / 'bin', Path(sys.executable).parent),
                        TMPDIR=str(self.base / 'tmp'), STUB_CALL_LOG=str(self.calls), STUB_SESSION=SESSION,
                        DELEGATE_TIMEOUT_SECONDS='20')

    def tearDown(self):
        self.temp.cleanup()

    def make_repo(self, name):
        repo = self.base / name
        repo.mkdir()
        for command in (['init', '-q'], ['config', 'user.email', 't@example.invalid'], ['config', 'user.name', 't']):
            self.subprocess.run(['git', *command], cwd=repo, check=True)
        (repo / 'a.txt').write_text('a\n', encoding='utf-8')
        self.subprocess.run(['git', 'add', 'a.txt'], cwd=repo, check=True)
        self.subprocess.run(['git', 'commit', '-qm', 'init'], cwd=repo, check=True)
        return repo

    def run_delegate(self, *args, cwd=None, **env):
        merged = dict(self.env, **env)
        return self.subprocess.run(['/bin/bash', str(PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run', *args],
                                   cwd=cwd or self.repo, env=merged, capture_output=True, text=True, timeout=60)

    def exec_calls(self):
        import json
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text(encoding='utf-8').splitlines()]

    def result(self, output):
        import re
        self.assertEqual(output.returncode, 0, output.stderr)
        match = re.match(RESULT_LINE, output.stdout.rstrip('\n').splitlines()[-1])
        self.assertIsNotNone(match, output.stdout)
        return match.groups()

    def state_of(self, run_id):
        import json
        return json.loads((self.logs / (run_id + '.state.json')).read_text(encoding='utf-8'))

    def test_plain_run_keeps_codex_arguments_and_adds_result_line(self):
        output = self.run_delegate('--', '任务', STUB_ANSWER='NEED_USER: 普通 run 不判定\n')
        run_id, status, resumable = self.result(output)
        self.assertEqual((status, resumable), ('done', 'false'))
        [call] = self.exec_calls()
        answer = str(self.logs / (run_id + '.answer'))
        self.assertEqual(call[:-1], ['exec', '-c', 'forced_login_method="chatgpt"', '-c', 'model_provider="openai"',
                                     '-c', 'approval_policy="never"', '--ephemeral', '--sandbox', 'read-only', '--color', 'never', '--json', '-o', answer, '--'])
        self.assertTrue(call[-1].startswith('【非交互委托】没有人能回答你的提问'))
        self.assertIn('\n\n任务\n\n【时间预算】', call[-1])  # run-timeout appends the time budget
        self.assertIn('NEED_USER: 普通 run 不判定', output.stdout)
        self.assertFalse((self.logs / (run_id + '.state.json')).exists())

    def test_resumable_run_needs_input(self):
        output = self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 除零怎么处理？\n进度：T1 完成\n')
        run_id, status, resumable = self.result(output)
        self.assertEqual((status, resumable), ('needs-input', 'true'))
        self.assertIn('NEED_USER: 除零怎么处理？\n进度：T1 完成', output.stdout)
        [call] = self.exec_calls()
        self.assertNotIn('--ephemeral', call)
        self.assertEqual(call[1:7], ['-c', 'forced_login_method="chatgpt"', '-c', 'model_provider="openai"',
                                     '-c', 'approval_policy="never"'])
        self.assertEqual(call[call.index('--sandbox') + 1], 'read-only')
        self.assertTrue(call[-1].startswith('【可续跑委托】'))
        self.assertIn('先做不受待定决策影响的任务，碰到需要用户拍板的决策', call[-1])
        self.assertIn('沙箱是只读的', call[-1])
        state = self.state_of(run_id)
        self.assertEqual(state, {'schema': 1, 'runId': run_id, 'sessionId': SESSION,
                                 'repository': os.path.realpath(self.repo), 'write': False, 'model': '',
                                 'effort': '', 'status': 'needs-input', 'parent': None,
                                 'chainRoot': run_id, 'strict': False, 'kind': 'run', 'authorization': None,
                                 'usageTotal': None})
        self.assertEqual(stat.S_IMODE((self.logs / (run_id + '.state.json')).stat().st_mode), 0o600)

    def test_resumable_run_done_records_model_and_effort(self):
        output = self.run_delegate('--resumable', '--model', 'gpt-test', '--effort', 'high', '--', '任务')
        run_id, status, resumable = self.result(output)
        self.assertEqual((status, resumable), ('done', 'true'))
        state = self.state_of(run_id)
        self.assertEqual((state['status'], state['model'], state['effort']), ('done', 'gpt-test', 'high'))

    def test_resumable_without_session_id_is_not_resumable(self):
        output = self.run_delegate('--resumable', '--', '任务', STUB_SESSION='', STUB_ANSWER='NEED_USER: 问题\n')
        run_id, status, resumable = self.result(output)
        self.assertEqual((status, resumable), ('needs-input', 'false'))
        self.assertIn('没有会话 ID', output.stderr)
        self.assertIsNone(self.state_of(run_id)['sessionId'])

    def test_resumable_write_result_line_follows_git_acceptance(self):
        output = self.run_delegate('--resumable', '--write', '--', '任务', STUB_TOUCH=str(self.repo / 'new.txt'))
        run_id, status, resumable = self.result(output)
        self.assertIn('git 验收', output.stdout)
        self.assertLess(output.stdout.index('git 验收'), output.stdout.index('delegate: run_id='))
        [call] = self.exec_calls()
        self.assertEqual(call[call.index('--sandbox') + 1], 'workspace-write')
        self.assertIn('沙箱允许写入当前工作目录', call[-1])
        self.assertIs(self.state_of(run_id)['write'], True)

    def test_failed_or_empty_runs_print_no_result_line_and_no_state(self):
        for env in ({'STUB_EXIT': '3'}, {'STUB_ANSWER': ''}):
            output = self.run_delegate('--resumable', '--', '任务', **env)
            self.assertNotEqual(output.returncode, 0)
            self.assertNotIn('delegate: run_id=', output.stdout + output.stderr)
        self.assertEqual(list(self.logs.glob('*.state.json')), [])

    def test_claude_code_rejects_resumable(self):
        output = self.run_delegate('--backend', 'claude-code', '--resumable', '--', '任务')
        self.assertEqual(output.returncode, 64)
        self.assertEqual(self.exec_calls(), [])

    def test_retention_prunes_logs_but_keeps_recent_state(self):
        # run-continue: logs keep the latest 50 groups; chain state is pruned by age, not with its logs.
        self.logs.mkdir(mode=0o700)
        old = ['20261001000000.%d' % index for index in range(55)]
        for index, run_id in enumerate(old):
            for suffix in ('.log', '.answer', '.state.json', '.resumed'):
                path = self.logs / (run_id + suffix)
                path.write_text('x', encoding='utf-8')
                if suffix in ('.log', '.answer'):
                    os.utime(path, (1000000 + index, 1000000 + index))
        self.result(self.run_delegate('--', '任务'))
        for run_id in old[:6]:
            for suffix in ('.log', '.answer'):
                self.assertFalse((self.logs / (run_id + suffix)).exists(), run_id + suffix)
        for run_id in old:
            for suffix in ('.state.json', '.resumed'):
                self.assertTrue((self.logs / (run_id + suffix)).exists(), run_id + suffix)
        for run_id in old[6:]:
            for suffix in ('.log', '.answer'):
                self.assertTrue((self.logs / (run_id + suffix)).exists(), run_id + suffix)

    def waiting_run(self, *args, **env):
        env.setdefault('STUB_ANSWER', 'NEED_USER: 选 A 还是 B？\n')
        run_id, status, resumable = self.result(self.run_delegate('--resumable', *args, '--', '任务', **env))
        self.assertEqual((status, resumable), ('needs-input', 'true'))
        return run_id

    def test_resume_passes_session_answer_and_original_settings(self):
        first = self.waiting_run('--model', 'gpt-test', '--effort', 'high')
        output = self.run_delegate('--resume', first, '--', '选 A')
        second, status, resumable = self.result(output)
        self.assertNotEqual(second, first)
        self.assertEqual((status, resumable), ('done', 'true'))
        call = self.exec_calls()[-1]
        self.assertEqual(call[:-1], ['exec', 'resume', '-m', 'gpt-test', '-c', 'model_reasoning_effort="high"',
                                     '-c', 'forced_login_method="chatgpt"', '-c', 'model_provider="openai"',
                                     '-c', 'approval_policy="never"', '-c', 'sandbox_mode="read-only"', '--json', '-o', str(self.logs / (second + '.answer')),
                                     '--', SESSION])
        # run-timeout appends the time budget after the unchanged resume prompt.
        self.assertTrue(call[-1].startswith('【用户答复】选 A\n\n请按上次约定继续：先做不受待定决策影响的任务；'
                                            '还需要用户拍板时，最终答复第一行以 `NEED_USER:` 开头。\n\n【时间预算】'))
        self.assertNotIn('git 验收', output.stdout)
        state = self.state_of(second)
        self.assertEqual((state['parent'], state['sessionId'], state['model'], state['effort']),
                         (first, SESSION, 'gpt-test', 'high'))

    def test_resume_chains_and_each_question_resumes_once(self):
        first = self.waiting_run()
        second, status, _ = self.result(self.run_delegate('--resume', first, '--', '选 A',
                                                          STUB_ANSWER='NEED_USER: 还有一个问题\n'))
        self.assertEqual(status, 'needs-input')
        third, status, _ = self.result(self.run_delegate('--resume', second, '--', '选 B'))
        self.assertEqual((status, self.state_of(third)['parent']), ('done', second))
        calls = len(self.exec_calls())
        again = self.run_delegate('--resume', first, '--', '再答一次')
        self.assertEqual(again.returncode, 64)
        self.assertIn('delegate: run already resumed', again.stderr)
        self.assertEqual(len(self.exec_calls()), calls)

    def test_write_resume_prints_git_acceptance(self):
        first = self.waiting_run('--write')
        output = self.run_delegate('--resume', first, '--write', '--', '选 A', STUB_TOUCH=str(self.repo / 'b.txt'))
        self.result(output)
        self.assertIn('git 验收', output.stdout)
        self.assertIn('b.txt', output.stdout)
        self.assertIn('sandbox_mode="workspace-write"', self.exec_calls()[-1])

    def assert_refused(self, reason, *args, cwd=None):
        calls = len(self.exec_calls())
        output = self.run_delegate(*args, cwd=cwd)
        self.assertEqual(output.returncode, 64, (args, output.stdout, output.stderr))
        self.assertIn(reason, output.stderr)
        self.assertNotIn('delegate: run_id=', output.stdout)
        self.assertEqual(len(self.exec_calls()), calls, args)

    def test_resume_refusals_do_not_start_codex(self):
        waiting = self.waiting_run()
        finished = self.result(self.run_delegate('--resumable', '--', '任务'))[0]
        no_session = self.result(self.run_delegate('--resumable', '--', '任务', STUB_SESSION='',
                                                   STUB_ANSWER='NEED_USER: 问题\n'))[0]
        plain = self.result(self.run_delegate('--', '任务'))[0]
        self.assert_refused('invalid run id', '--resume', '../x', '--', '答复')
        self.assert_refused('run not found', '--resume', '20261024183015.99', '--', '答复')
        self.assert_refused('run not found', '--resume', plain, '--', '答复')
        self.assert_refused('run not resumable', '--resume', no_session, '--', '答复')
        self.assert_refused('run not waiting for input', '--resume', finished, '--', '答复')
        self.assert_refused('repository mismatch', '--resume', waiting, '--', '答复', cwd=self.make_repo('other'))
        self.assert_refused('write mode mismatch', '--resume', waiting, '--write', '--', '答复')
        for extra in (('--resumable',), ('--model', 'gpt-test'), ('--effort', 'high')):
            self.assert_refused('--resume cannot be combined', '--resume', waiting, *extra, '--', '答复')
        self.assert_refused('does not support', '--backend', 'claude-code', '--resume', waiting, '--', '答复')
        self.assert_refused('empty or oversized task', '--resume', waiting, '--', '   ')
        self.assertFalse((self.logs / (waiting + '.resumed')).exists())
        self.result(self.run_delegate('--resume', waiting, '--', '答复'))


if __name__ == '__main__':
    unittest.main()
