#!/usr/bin/env python3
"""Timeout handling: deadlines, TIME_UP, wrap-up round and fallback; Codex is always a fake executable."""
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))

SESSION = '01a15f3b-0f2c-7d82-b5cc-7a1f711c11d2'
RUN = '20261026183015.12345'


class RunTimeoutUnitTests(unittest.TestCase):
    def setUp(self):
        self.state = importlib.import_module('run_state')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-timeout-')
        self.dir = Path(self.temp.name)
        self.dir.chmod(0o700)

    def tearDown(self):
        self.temp.cleanup()

    def test_deadlines(self):
        self.assertEqual(self.state.deadlines(540), (45, 495, 405))
        self.assertEqual(self.state.deadlines(60), (10, 50, 25))
        self.assertEqual(self.state.deadlines(2), (0, 2, 1))
        self.assertEqual((self.state.WRAPUP_CAP, self.state.WRAPUP_DIVISOR,
                          self.state.THRESHOLD_MARGIN, self.state.THRESHOLD_DIVISOR), (45, 6, 90, 2))

    def test_classify_time_up(self):
        self.assertEqual(self.state.classify('TIME_UP: 做完 1–3 步'), ('timeout', '做完 1–3 步'))
        self.assertEqual(self.state.classify('\n  TIME_UP:进度'), ('timeout', '进度'))
        self.assertEqual(self.state.classify('完成。\nTIME_UP: 不在第一行'), ('done', None))
        self.assertEqual(self.state.classify('TIME_UP: x', resumable=False), ('timeout', 'x'))
        self.assertEqual(self.state.classify('NEED_USER: 问题', resumable=False), ('done', None))
        self.assertEqual(self.state.classify('NEED_USER: 问题'), ('needs-input', '问题'))

    def test_changed_files(self):
        baseline = [' M a.txt', '?? old.txt']
        current = [' M a.txt', '?? old.txt', '?? new.txt', 'M  b.txt']
        self.assertEqual(self.state.changed_files(baseline, current), ['?? new.txt', 'M  b.txt'])
        self.assertEqual(self.state.changed_files(baseline, baseline), [])

    def write_answer(self, text):
        answer = self.dir / (RUN + '.answer')
        answer.write_text(text, encoding='utf-8')
        log = self.dir / (RUN + '.log')
        log.write_text('session id: %s\n' % SESSION, encoding='utf-8')
        return log, answer

    def test_record_plain_time_up_is_not_resumable(self):
        log, answer = self.write_answer('TIME_UP: 进度')
        line = self.state.record(self.dir, RUN, log, answer, str(self.dir), False, '', '', '', False)
        self.assertEqual(line, 'delegate: run_id=%s status=timeout resumable=false' % RUN)
        self.assertIsNone(self.state.read_state(self.dir, RUN))

    def test_record_forced_timeout_writes_state(self):
        log, answer = self.write_answer('兜底文字')
        line = self.state.record(self.dir, RUN, log, answer, str(self.dir), False, '', '', '', True, 'timeout')
        self.assertEqual(line, 'delegate: run_id=%s status=timeout resumable=true' % RUN)
        self.assertEqual(self.state.read_state(self.dir, RUN)['status'], 'timeout')

    def test_check_resume_accepts_timeout(self):
        log, answer = self.write_answer('TIME_UP: 进度')
        self.state.record(self.dir, RUN, log, answer, str(self.dir), False, '', '', '', True)
        reason, state = self.state.check_resume(self.dir, RUN, str(self.dir), False)
        self.assertIsNone(reason)
        self.assertEqual(state['sessionId'], SESSION)
        log, answer = self.write_answer('完成')
        self.state.record(self.dir, RUN, log, answer, str(self.dir), False, '', '', '', True)
        self.assertEqual(self.state.check_resume(self.dir, RUN, str(self.dir), False)[0], 'run not waiting for input')


FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, sys, time
args = sys.argv[1:]
if args == ["--version"]:
    print("codex stub 1.0")
    raise SystemExit(0)
if args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT")
    raise SystemExit(0)
with open(os.environ["STUB_CALL_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args, ensure_ascii=False) + "\n")
resume = args[:2] == ["exec", "resume"]
prefix = "STUB_RESUME_" if resume else "STUB_"
if os.environ.get("STUB_SESSION"):
    # delegate runs Codex with --json: the session id arrives as a thread.started event.
    if "--json" in args:
        print(json.dumps({"type": "thread.started", "thread_id": os.environ["STUB_SESSION"]}), flush=True)
    else:
        print("OpenAI Codex v0.162.1\n--------\nsession id: " + os.environ["STUB_SESSION"] + "\n--------", flush=True)
if os.environ.get(prefix + "WRITE"):
    with open(os.environ[prefix + "WRITE"], "a", encoding="utf-8") as handle:
        handle.write("changed by fake codex\n")
time.sleep(float(os.environ.get(prefix + "SLEEP", "0")))
for index, arg in enumerate(args[:-1]):
    if arg == "-o":
        with open(args[index + 1], "w", encoding="utf-8") as answer:
            answer.write(os.environ.get(prefix + "ANSWER", "fake answer\n"))
raise SystemExit(int(os.environ.get(prefix + "EXIT", "0")))
'''
RESULT_LINE = r'^delegate: run_id=([0-9]{14}\.[0-9]+) status=(done|needs-input|timeout) resumable=(true|false)$'


class RunTimeoutFlowTests(unittest.TestCase):
    def setUp(self):
        import os
        import subprocess
        self.subprocess = subprocess
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-timeout-flow-')
        self.base = Path(self.temp.name)
        (self.base / 'bin').mkdir()
        fake = self.base / 'bin' / 'codex'
        fake.write_text(FAKE_CODEX, encoding='utf-8')
        fake.chmod(0o755)
        (self.base / 'tmp').mkdir()
        self.logs = self.base / 'tmp' / 'delegate'
        self.calls = self.base / 'calls.log'
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        for command in (['init', '-q'], ['config', 'user.email', 't@example.invalid'], ['config', 'user.name', 't']):
            subprocess.run(['git', *command], cwd=self.repo, check=True)
        (self.repo / 'a.txt').write_text('a\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'a.txt'], cwd=self.repo, check=True)
        subprocess.run(['git', 'commit', '-qm', 'init'], cwd=self.repo, check=True)
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'DELEGATE_REVIEW_DEPTH')}
        self.env.update(PATH='%s:%s:/usr/bin:/bin' % (self.base / 'bin', Path(sys.executable).parent),
                        TMPDIR=str(self.base / 'tmp'), STUB_CALL_LOG=str(self.calls), STUB_SESSION=SESSION,
                        DELEGATE_TIMEOUT_SECONDS='60')

    def tearDown(self):
        self.temp.cleanup()

    def run_delegate(self, *args, **env):
        import time
        merged = dict(self.env, **env)
        start = time.monotonic()
        output = self.subprocess.run(['/bin/bash', str(PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run', *args],
                                     cwd=self.repo, env=merged, capture_output=True, text=True, timeout=90)
        output.elapsed = time.monotonic() - start
        return output

    def exec_calls(self):
        import json
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text(encoding='utf-8').splitlines()]

    def result(self, output, code=0):
        import re
        self.assertEqual(output.returncode, code, output.stdout + output.stderr)
        match = re.match(RESULT_LINE, output.stdout.rstrip('\n').splitlines()[-1])
        self.assertIsNotNone(match, output.stdout)
        return match.groups()

    def assert_budget(self, prompt, total):
        import re
        wrapup, main, threshold = self.state.deadlines(total)
        match = re.search(r'\n\n【时间预算】本次运行开始于 epoch 秒 ([0-9]+)，%d 秒后会被强制中止，中止时不保留未写出的答复。'
                          r'需要判断用时就运行 `date \+%%s`。已用时达到 %d 秒后，不要再开始新的步骤，也不要启动预计会跨过期限的长命令，'
                          r'立即给出最终答复：第一行以 `TIME_UP:` 开头，后面写已完成的进度、做到一半的步骤（如有）、下一步应从哪里开始。$'
                          % (main, threshold), prompt)
        self.assertIsNotNone(match, prompt)
        return int(match.group(1))

    @property
    def state(self):
        return importlib.import_module('run_state')

    def test_plain_run_keeps_arguments_and_appends_budget(self):
        import time
        output = self.run_delegate('--', '任务')
        self.assertEqual(self.result(output)[1:], ('done', 'false'))
        [call] = self.exec_calls()
        self.assertIn('--ephemeral', call)
        self.assertEqual(call[call.index('--sandbox') + 1], 'read-only')
        self.assertTrue(call[-1].startswith('【非交互委托】'))
        self.assertIn('\n\n任务\n\n【时间预算】', call[-1])
        started = self.assert_budget(call[-1], 60)
        self.assertLessEqual(abs(started - time.time()), 60)

    def test_resumable_run_appends_budget_without_ephemeral(self):
        output = self.run_delegate('--resumable', '--', '任务')
        self.assertEqual(self.result(output)[1:], ('done', 'true'))
        [call] = self.exec_calls()
        self.assertNotIn('--ephemeral', call)
        self.assert_budget(call[-1], 60)

    def test_budget_follows_shortened_deadline(self):
        self.run_delegate('--', '任务', DELEGATE_TIMEOUT_SECONDS='12')
        self.assert_budget(self.exec_calls()[0][-1], 12)

    def test_plain_time_up_is_timeout_without_wrapup(self):
        output = self.run_delegate('--', '任务', STUB_ANSWER='TIME_UP: 做完 1–3 步\n')
        self.assertEqual(self.result(output, 124)[1:], ('timeout', 'false'))
        self.assertIn('TIME_UP: 做完 1–3 步', output.stdout)
        self.assertIn('收尾：主动停', output.stdout)
        self.assertNotIn('被中止', output.stderr)
        self.assertEqual(len(self.exec_calls()), 1)

    def test_resumable_time_up_writes_timeout_state(self):
        import json
        output = self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='TIME_UP: 进度\n')
        run_id, status, resumable = self.result(output, 124)
        self.assertEqual((status, resumable), ('timeout', 'true'))
        state = json.loads((self.logs / (run_id + '.state.json')).read_text(encoding='utf-8'))
        self.assertEqual((state['status'], state['sessionId']), ('timeout', SESSION))
        self.assertEqual(len(self.exec_calls()), 1)

    def test_main_run_is_stopped_at_main_deadline(self):
        output = self.run_delegate('--', '任务', DELEGATE_TIMEOUT_SECONDS='12', STUB_SLEEP='30')
        self.assertEqual(output.returncode, 124, output.stderr)
        self.assertIn('超过 10 秒被中止', output.stderr)
        self.assertLess(output.elapsed, 20)

    WRAPUP_PROMPT = ('【收尾】本次运行已到期被中止。不要再执行任何命令，也不要继续做任务。只写进度：第一行以 `TIME_UP:` 开头，'
                     '后面写已完成的步骤及结果、做到一半的步骤（如有）、下一步应从哪里开始。')

    def stopped(self, *args, **env):
        # T=7 gives W=1, M=6: the main run is stopped at 6 s and the wrap-up round gets 1 s.
        env.setdefault('DELEGATE_TIMEOUT_SECONDS', '7')
        env.setdefault('STUB_SLEEP', '30')
        return self.run_delegate(*args, **env)

    def fallback_line(self, output):
        return [line for line in output.stdout.splitlines() if line.startswith('delegate: 已中止')]

    def test_wrapup_round_reports_progress(self):
        output = self.stopped('--resumable', '--', '任务', STUB_RESUME_ANSWER='TIME_UP: 做完 1–3 步\n')
        run_id, status, resumable = self.result(output, 124)
        self.assertEqual((status, resumable), ('timeout', 'true'))
        self.assertIn('TIME_UP: 做完 1–3 步', output.stdout)
        self.assertIn('收尾：收尾轮', output.stdout)
        self.assertIn('超过 6 秒被中止', output.stderr)
        self.assertLess(output.elapsed, 7 + 5)
        first, wrapup = self.exec_calls()
        self.assertEqual(wrapup, ['exec', 'resume', '-c', 'forced_login_method="chatgpt"', '-c', 'model_provider="openai"',
                                  '-c', 'approval_policy="never"', '-c', 'sandbox_mode="read-only"', '--json',
                                  '-o', str(self.logs / (run_id + '.wrapup.answer')), '--', SESSION, self.WRAPUP_PROMPT])
        self.assertTrue((self.logs / (run_id + '.wrapup')).exists())

    def test_wrapup_round_is_read_only_in_write_mode(self):
        output = self.stopped('--resumable', '--write', '--model', 'gpt-test', '--', '任务',
                              STUB_RESUME_ANSWER='TIME_UP: 进度\n')
        self.result(output, 124)
        first, wrapup = self.exec_calls()
        self.assertEqual(first[first.index('--sandbox') + 1], 'workspace-write')
        self.assertIn('-c', wrapup)
        self.assertIn('sandbox_mode="read-only"', wrapup)
        self.assertNotIn('sandbox_mode="workspace-write"', wrapup)
        self.assertEqual(wrapup[2:4], ['-m', 'gpt-test'])

    def assert_fallback(self, output, reason, session, resumable, calls):
        status = self.result(output, 124)
        self.assertEqual(status[1:], ('timeout', 'true' if resumable else 'false'))
        self.assertEqual(self.fallback_line(output),
                         ['delegate: 已中止，未取得进度说明（%s）。会话 ID：%s；可续跑：%s。'
                          % (reason, session or '无', '是' if resumable else '否')])
        self.assertIn('收尾：兜底（%s）' % reason, output.stdout)
        self.assertEqual(len(self.exec_calls()), calls)

    def test_plain_run_goes_straight_to_fallback(self):
        output = self.stopped('--', '任务')
        self.assert_fallback(output, '普通 run 不保留会话', None, False, 1)
        self.assertIn('只读运行，不列文件', output.stdout)

    def test_fallback_when_wrapup_times_out(self):
        output = self.stopped('--resumable', '--', '任务', STUB_RESUME_SLEEP='30')
        self.assert_fallback(output, '收尾轮超时', SESSION, True, 2)
        self.assertLess(output.elapsed, 7 + 5)

    def test_fallback_when_wrapup_fails(self):
        self.assert_fallback(self.stopped('--resumable', '--', '任务', STUB_RESUME_EXIT='2'),
                             '收尾轮失败（退出 2）', SESSION, True, 2)

    def test_fallback_when_wrapup_answer_is_empty(self):
        self.assert_fallback(self.stopped('--resumable', '--', '任务', STUB_RESUME_ANSWER=''),
                             '收尾轮答复为空', SESSION, True, 2)

    def test_fallback_without_session_id(self):
        self.assert_fallback(self.stopped('--resumable', '--', '任务', STUB_SESSION=''),
                             '未取得会话 ID', None, False, 1)

    def test_zero_wrapup_budget_skips_the_round(self):
        output = self.stopped('--resumable', '--', '任务', DELEGATE_TIMEOUT_SECONDS='2')
        self.assert_fallback(output, '收尾轮超时', SESSION, True, 1)

    def answer_lines(self, output):
        lines = output.stdout.splitlines()
        return lines[lines.index(self.fallback_line(output)[0]) + 1:lines.index('---')]

    def test_write_fallback_lists_files_changed_during_the_run(self):
        (self.repo / 'a.txt').write_text('edited before the run\n', encoding='utf-8')
        output = self.stopped('--write', '--', '任务', STUB_WRITE=str(self.repo / 'b.txt'))
        self.assert_fallback(output, '普通 run 不保留会话', None, False, 1)
        self.assertEqual(self.answer_lines(output), ['改动的文件（与运行前比较）：', '?? b.txt', ''])
        self.assertIn('git 验收', output.stderr)
        self.assertTrue((self.repo / 'b.txt').exists())

    def test_write_fallback_without_changes_says_none(self):
        output = self.stopped('--resumable', '--write', '--', '任务', STUB_RESUME_EXIT='1')
        self.assert_fallback(output, '收尾轮失败（退出 1）', SESSION, True, 2)
        self.assertEqual(self.answer_lines(output), ['改动的文件（与运行前比较）：', '无', ''])

    def test_retention_prunes_wrapup_and_baseline_files(self):
        import os
        self.logs.mkdir(mode=0o700)
        old = ['20261001000000.%d' % index for index in range(55)]
        suffixes = ('.log', '.answer', '.state.json', '.resumed', '.wrapup', '.wrapup.answer', '.baseline')
        for index, run_id in enumerate(old):
            for suffix in suffixes:
                path = self.logs / (run_id + suffix)
                path.write_text('x', encoding='utf-8')
                os.utime(path, (1000000 + index, 1000000 + index))
        self.result(self.run_delegate('--', '任务'))
        for run_id in old[:6]:
            for suffix in suffixes:
                self.assertFalse((self.logs / (run_id + suffix)).exists(), run_id + suffix)
        for suffix in suffixes:
            self.assertTrue((self.logs / (old[6] + suffix)).exists(), old[6] + suffix)

    def test_resume_after_timeout_continues_the_session(self):
        import json
        first, status, resumable = self.result(self.stopped('--resumable', '--', '任务',
                                                            STUB_RESUME_ANSWER='TIME_UP: 进度\n'), 124)
        output = self.run_delegate('--resume', first, '--', '继续', STUB_ANSWER='全部完成\n')
        second, status, resumable = self.result(output)
        self.assertEqual((status, resumable), ('done', 'true'))
        call = self.exec_calls()[-1]
        self.assertEqual(call[:2], ['exec', 'resume'])
        self.assertEqual(call[-2], SESSION)
        self.assertTrue(call[-1].startswith('【用户答复】继续\n\n请按上次约定继续'))
        self.assert_budget(call[-1], 60)
        state = json.loads((self.logs / (second + '.state.json')).read_text(encoding='utf-8'))
        self.assertEqual(state['parent'], first)
        again = self.run_delegate('--resume', second, '--', '再来')
        self.assertEqual(again.returncode, 64)
        self.assertIn('run not waiting for input', again.stderr)

    def test_plain_timeout_cannot_be_resumed(self):
        first = self.result(self.run_delegate('--', '任务', STUB_ANSWER='TIME_UP: 进度\n'), 124)[0]
        output = self.run_delegate('--resume', first, '--', '继续')
        self.assertEqual(output.returncode, 64)
        self.assertIn('run not found', output.stderr)
        self.assertEqual(len(self.exec_calls()), 1)

    def test_signal_interrupt_has_no_wrapup_or_result_line(self):
        import os
        import signal
        import time
        merged = dict(self.env, STUB_SLEEP='30')
        proc = self.subprocess.Popen(['/bin/bash', str(PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run',
                                      '--resumable', '--', '任务'], cwd=self.repo, env=merged,
                                     stdout=self.subprocess.PIPE, stderr=self.subprocess.PIPE, text=True)
        deadline = time.monotonic() + 10
        while not self.exec_calls() and time.monotonic() < deadline:
            time.sleep(.05)
        os.kill(proc.pid, signal.SIGTERM)
        out, err = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 143, err)
        self.assertNotIn('delegate: run_id=', out)
        self.assertEqual(len(self.exec_calls()), 1)


if __name__ == '__main__':
    unittest.main()
