#!/usr/bin/env python3
"""Result files, --json event parsing, --strict and usage; Codex is always a fake executable."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))

SESSION = '01a17bd7-5818-71b2-971d-dfe40eefa843'
RUN = '20261027133326.79650'
USAGE = {'input_tokens': 124735, 'cached_input_tokens': 112256, 'cache_write_input_tokens': 0,
         'output_tokens': 391, 'reasoning_output_tokens': 0}


def command_event(index, command, exit_code, status):
    return {'type': 'item.completed', 'item': {'id': 'item_%d' % index, 'type': 'command_execution',
                                               'command': command, 'aggregated_output': 'x' * 100,
                                               'exit_code': exit_code, 'status': status}}


# Shapes taken from the S38 probe record (T1).
EVENTS = [
    {'type': 'thread.started', 'thread_id': SESSION},
    {'type': 'turn.started'},
    {'type': 'item.completed', 'item': {'id': 'item_0', 'type': 'agent_message', 'text': '开始'}},
    {'type': 'item.started', 'item': {'id': 'item_1', 'type': 'command_execution',
                                      'command': "/bin/zsh -lc 'cat a.txt'", 'aggregated_output': '',
                                      'exit_code': None, 'status': 'in_progress'}},
    command_event(1, "/bin/zsh -lc 'cat a.txt'", 0, 'completed'),
    command_event(2, "/bin/zsh -lc 'cat does-not-exist.txt'", 1, 'failed'),
    {'type': 'item.completed', 'item': {'id': 'item_3', 'type': 'agent_message', 'text': '完成'}},
    {'type': 'turn.completed', 'usage': USAGE},
]


def write_events(path, events, junk=()):
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    for position, text in junk:
        lines.insert(position, text)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


class RunEventsTests(unittest.TestCase):
    def setUp(self):
        self.events = importlib.import_module('run_events')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-result-')
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_session_id_from_thread_started(self):
        path = write_events(self.dir / 'e.jsonl', EVENTS, junk=[(0, 'Reading additional input from stdin...')])
        self.assertEqual(self.events.session_id(path), SESSION)
        self.assertIsNone(self.events.session_id(write_events(self.dir / 'n.jsonl', EVENTS[1:])))
        self.assertIsNone(self.events.session_id(self.dir / 'missing.jsonl'))
        bad = write_events(self.dir / 'b.jsonl', [{'type': 'thread.started', 'thread_id': 'not-a-uuid'}])
        self.assertIsNone(self.events.session_id(bad))

    def test_commands_skip_non_json_and_started_items(self):
        path = write_events(self.dir / 'e.jsonl', EVENTS, junk=[(3, '{broken'), (5, 'plain text')])
        commands, truncated = self.events.commands(path)
        self.assertEqual(commands, [
            {'command': "/bin/zsh -lc 'cat a.txt'", 'exitCode': 0, 'status': 'completed'},
            {'command': "/bin/zsh -lc 'cat does-not-exist.txt'", 'exitCode': 1, 'status': 'failed'}])
        self.assertFalse(truncated)

    def test_commands_truncation(self):
        many = [command_event(index, 'c%d' % index, 0, 'completed') for index in range(205)]
        long = [command_event(0, 'x' * 1500, 0, 'completed')]
        commands, truncated = self.events.commands(write_events(self.dir / 'm.jsonl', many))
        self.assertEqual((len(commands), truncated), (self.events.MAX_COMMANDS, True))
        commands, truncated = self.events.commands(write_events(self.dir / 'l.jsonl', long))
        self.assertEqual((len(commands[0]['command']), truncated), (self.events.MAX_COMMAND_CHARS, True))
        self.assertEqual((self.events.MAX_COMMANDS, self.events.MAX_COMMAND_CHARS), (200, 1000))

    def test_usage_takes_last_turn_completed(self):
        later = dict(USAGE, input_tokens=201493)
        path = write_events(self.dir / 'e.jsonl', EVENTS + [{'type': 'turn.completed', 'usage': later}])
        self.assertEqual(self.events.usage(path), {
            'inputTokens': 201493, 'cachedInputTokens': 112256, 'cacheWriteInputTokens': 0,
            'outputTokens': 391, 'reasoningOutputTokens': 0})
        self.assertIsNone(self.events.usage(write_events(self.dir / 'n.jsonl', EVENTS[:-1])))

    def test_render_recent_failure_events(self):
        events = EVENTS[:-1] + [{'type': 'item.completed', 'item': {'id': 'item_9', 'type': 'error', 'message': '模型元数据缺失'}},
                                {'type': 'error', 'message': 'stream disconnected'}]
        lines = self.events.render_recent(write_events(self.dir / 'e.jsonl', events))
        self.assertEqual(lines, [
            "命令 /bin/zsh -lc 'cat a.txt' 退出 0",
            "命令 /bin/zsh -lc 'cat does-not-exist.txt' 退出 1",
            '错误 模型元数据缺失',
            '错误 stream disconnected'])
        many = [command_event(index, 'c%d' % index, 0, 'completed') for index in range(15)]
        self.assertEqual(len(self.events.render_recent(write_events(self.dir / 'm.jsonl', many))), 10)
        self.assertEqual(self.events.render_recent(self.dir / 'missing.jsonl'), [])


CLEANUP_LINES = [
    'delegate: 清理：中止前 Codex 的后代进程 2 个：91230(91230) 91275(91230)',
    'delegate: 清理：中止后仍有残留，PID=91275 91300',
    'delegate: 执行进程未能回收，PID=86911',
    'delegate: 执行进程超时未退出，已强制结束（PID=86878），其后代可能残留。',
]


class RunStateResultTests(unittest.TestCase):
    def setUp(self):
        self.state = importlib.import_module('run_state')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-result-state-')
        self.dir = Path(self.temp.name)
        self.dir.chmod(0o700)

    def tearDown(self):
        self.temp.cleanup()

    def test_classify_strict(self):
        classify = self.state.classify
        self.assertEqual(classify('DONE: 做完了', strict=True), ('done', '做完了'))
        self.assertEqual(classify('﻿  DONE:总结', strict=True), ('done', '总结'))
        self.assertEqual(classify('做完了', strict=True), ('unmarked', None))
        self.assertEqual(classify('结论\nDONE: 不在首行', strict=True), ('unmarked', None))
        self.assertEqual(classify('TIME_UP: 进度', strict=True), ('timeout', '进度'))
        self.assertEqual(classify('NEED_USER: 问题', strict=True), ('needs-input', '问题'))
        self.assertEqual(classify('NEED_USER: 问题', resumable=False, strict=True), ('unmarked', None))
        self.assertEqual(classify('DONE: x'), ('done', None))
        self.assertEqual(classify('没有标记'), ('done', None))

    def test_run_usage(self):
        session = {'inputTokens': 201493, 'cachedInputTokens': 176000, 'cacheWriteInputTokens': 0,
                   'outputTokens': 605, 'reasoningOutputTokens': 0}
        parent = {'inputTokens': 124735, 'cachedInputTokens': 112256, 'cacheWriteInputTokens': 0,
                  'outputTokens': 391, 'reasoningOutputTokens': 0}
        self.assertEqual(self.state.run_usage(session, parent, True), ({
            'inputTokens': 76758, 'cachedInputTokens': 63744, 'cacheWriteInputTokens': 0,
            'outputTokens': 214, 'reasoningOutputTokens': 0}, None))
        self.assertEqual(self.state.run_usage(session, None, False), (session, None))
        self.assertEqual(self.state.run_usage(session, None, True), (None, '父轮用量未知'))
        self.assertEqual(self.state.run_usage(None, parent, True), (None, '本次没有完成的轮次'))

    def test_write_result_is_private_and_atomic(self):
        path = self.state.write_result(self.dir, {'schema': 1, 'runId': RUN, 'status': 'done'})
        self.assertEqual(path, self.dir / (RUN + '.result.json'))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['status'], 'done')
        self.assertEqual([p.name for p in self.dir.iterdir()], [RUN + '.result.json'])
        with self.assertRaises(TypeError):
            self.state.write_result(self.dir, {'schema': 1, 'runId': RUN, 'bad': object()})
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['status'], 'done')
        self.assertEqual([p.name for p in self.dir.iterdir()], [RUN + '.result.json'])

    def test_parse_cleanup(self):
        self.assertIsNone(self.state.parse_cleanup([]))
        self.assertEqual(self.state.parse_cleanup(CLEANUP_LINES), {
            'lines': CLEANUP_LINES, 'leftoverPids': [91275, 91300], 'unreapedPid': 86911, 'wrapperForced': True})
        clean = ['delegate: 清理：中止前 Codex 的后代进程 0 个：无', 'delegate: 清理：中止后无残留']
        self.assertEqual(self.state.parse_cleanup(clean), {
            'lines': clean, 'leftoverPids': [], 'unreapedPid': None, 'wrapperForced': False})

    def test_state_records_usage_chain_and_strict(self):
        events = write_events(self.dir / (RUN + '.events.jsonl'), EVENTS)
        answer = self.dir / (RUN + '.answer')
        answer.write_text('DONE: 完成', encoding='utf-8')
        line = self.state.record(self.dir, RUN, self.dir / 'missing.log', answer, str(self.dir), False, '', '', '',
                                 True, events=events, strict=True)
        self.assertEqual(line, 'delegate: run_id=%s status=done resumable=true' % RUN)
        state = self.state.read_state(self.dir, RUN)
        self.assertEqual((state['sessionId'], state['chainRoot'], state['strict'], state['usageTotal']['inputTokens']),
                         (SESSION, RUN, True, 124735))
        child = '20261027133400.1'
        answer.write_text('NEED_USER: 问题', encoding='utf-8')
        self.state.record(self.dir, child, self.dir / 'missing.log', answer, str(self.dir), False, '', '', RUN, True,
                          events=events)
        self.assertEqual(self.state.read_state(self.dir, child)['chainRoot'], RUN)
        answer.write_text('没有标记', encoding='utf-8')
        unmarked = '20261027133500.1'
        line = self.state.record(self.dir, unmarked, self.dir / 'missing.log', answer, str(self.dir), False, '', '', '',
                                 True, events=events, strict=True)
        self.assertEqual(line, 'delegate: run_id=%s status=unmarked resumable=true' % unmarked)
        self.assertEqual(self.state.check_resume(self.dir, unmarked, str(self.dir), False)[0], 'run not waiting for input')

    def test_old_state_without_new_fields_still_resumes(self):
        self.state.write_state(self.dir, {'schema': 1, 'runId': RUN, 'sessionId': SESSION, 'repository': str(self.dir),
                                          'write': False, 'model': '', 'effort': '', 'status': 'needs-input', 'parent': None})
        self.assertIsNone(self.state.check_resume(self.dir, RUN, str(self.dir), False)[0])


FAKE_CODEX = r"""#!/usr/bin/env python3
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
sys.stderr.write(os.environ.get(prefix + "STDERR", "Reading additional input from stdin...\n"))
events = json.loads(os.environ.get(prefix + "EVENTS", "[]"))
if os.environ.get("STUB_SESSION") and "--json" in args:
    events = [{"type": "thread.started", "thread_id": os.environ["STUB_SESSION"]}] + events
for event in events:
    print(json.dumps(event, ensure_ascii=False), flush=True)
if os.environ.get(prefix + "TOUCH"):
    open(os.environ[prefix + "TOUCH"], "w").close()
time.sleep(float(os.environ.get(prefix + "SLEEP", "0")))
for index, arg in enumerate(args[:-1]):
    if arg == "-o":
        with open(args[index + 1], "w", encoding="utf-8") as answer:
            answer.write(os.environ.get(prefix + "ANSWER", "fake answer\n"))
raise SystemExit(int(os.environ.get(prefix + "EXIT", "0")))
"""
RESULT_LINE = r'^delegate: run_id=([0-9]{14}\.[0-9]+) status=([a-z-]+) resumable=(true|false)$'


class FlowBase(unittest.TestCase):
    def setUp(self):
        import os
        import subprocess
        self.subprocess = subprocess
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-result-flow-')
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
                        STUB_EVENTS=json.dumps(EVENTS[1:]), DELEGATE_TIMEOUT_SECONDS='60')

    def tearDown(self):
        self.temp.cleanup()

    def run_delegate(self, *args, **env):
        return self.subprocess.run(['/bin/bash', str(PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run', *args],
                                   cwd=self.repo, env=dict(self.env, **env), capture_output=True, text=True, timeout=90)

    def exec_calls(self):
        calls = [json.loads(line) for line in self.calls.read_text(encoding='utf-8').splitlines()]
        return [call for call in calls if call[:1] == ['exec']]

    def run_id(self, output):
        import re
        match = re.match(RESULT_LINE, output.stdout.splitlines()[-1])
        self.assertIsNotNone(match, output.stdout + output.stderr)
        return match.group(1)


class JsonEventsFlowTests(FlowBase):
    def test_every_run_path_passes_json_and_splits_streams(self):
        plain = self.run_delegate('--', '普通')
        self.assertEqual(plain.returncode, 0, plain.stderr)
        first = self.run_id(self.run_delegate('--resumable', '--', '可续跑', STUB_ANSWER='NEED_USER: 选哪个？'))
        resumed = self.run_delegate('--resume', first, '--', '选 A')
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        calls = self.exec_calls()
        self.assertEqual(len(calls), 3)
        for call in calls:
            self.assertEqual(call[call.index('-o') - 1], '--json')
        self.assertIn('--ephemeral', calls[0])
        run_id = self.run_id(plain)
        events = (self.logs / (run_id + '.events.jsonl')).read_text(encoding='utf-8')
        stderr = (self.logs / (run_id + '.log')).read_text(encoding='utf-8')
        self.assertIn('"thread.started"', events)
        self.assertNotIn('Reading additional input', events)
        self.assertIn('Reading additional input', stderr)
        self.assertNotIn('thread.started', stderr)

    def test_session_id_comes_from_thread_started(self):
        run_id = self.run_id(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 问题'))
        state = json.loads((self.logs / (run_id + '.state.json')).read_text(encoding='utf-8'))
        self.assertEqual(state['sessionId'], SESSION)
        self.assertEqual(state['usageTotal']['inputTokens'], 124735)
        output = self.run_delegate('--resumable', '--', '任务', STUB_SESSION='')
        self.assertTrue(output.stdout.rstrip().endswith('resumable=false'), output.stdout)

    def test_wrapup_round_also_uses_json(self):
        output = self.run_delegate('--resumable', '--', '任务', DELEGATE_TIMEOUT_SECONDS='12', STUB_SLEEP='30',
                                   STUB_RESUME_ANSWER='TIME_UP: 做完第 1 步')
        self.assertEqual(output.returncode, 124, output.stderr)
        run_id = self.run_id(output)
        wrapup = self.exec_calls()[-1]
        self.assertEqual(wrapup[:2], ['exec', 'resume'])
        self.assertEqual(wrapup[wrapup.index('-o') - 1], '--json')
        self.assertTrue((self.logs / (run_id + '.wrapup.events.jsonl')).exists())

    def test_failure_diagnostics_render_recent_events(self):
        output = self.run_delegate('--', '任务', STUB_EXIT='3', STUB_STDERR='认证失败\n',
                                   STUB_EVENTS=json.dumps(EVENTS[1:-1]))
        self.assertEqual(output.returncode, 3)
        self.assertIn('认证失败', output.stderr)
        self.assertIn("最近的事件：\n命令 /bin/zsh -lc 'cat a.txt' 退出 0", output.stderr)
        self.assertRegex(output.stderr, r'完整过程日志：\S+\.log；事件流：\S+\.events\.jsonl')


class ResultFileFlowTests(FlowBase):
    def result_of(self, output, stream='stdout'):
        import re
        text = getattr(output, stream)
        match = re.search(r'^delegate: result=(\S+)$', text, re.M)
        self.assertIsNotNone(match, output.stdout + output.stderr)
        path = Path(match.group(1))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        return json.loads(path.read_text(encoding='utf-8'))

    def test_done_plain_run(self):
        output = self.run_delegate('--', '任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        lines = output.stdout.splitlines()
        self.assertRegex(lines[-1], RESULT_LINE)
        self.assertRegex(lines[-2], r'^delegate: result=\S+\.result\.json$')
        self.assertIn('用量：本次输入 124,735（缓存 112,256）/ 输出 391；整个会话输入 124,735', output.stdout)
        result = self.result_of(output)
        run_id = self.run_id(output)
        self.assertEqual({key: result[key] for key in ('schema', 'runId', 'kind', 'parent', 'chainRoot', 'backend',
                                                       'write', 'strict', 'status', 'exitCode', 'resumable',
                                                       'sessionId', 'markers', 'wrapUp', 'changedFiles', 'cleanup',
                                                       'commandsTruncated')},
                         {'schema': 1, 'runId': run_id, 'kind': 'run', 'parent': None, 'chainRoot': run_id,
                          'backend': 'codex', 'write': False, 'strict': False, 'status': 'done', 'exitCode': 0,
                          'resumable': False, 'sessionId': SESSION,
                          'markers': {'needUser': None, 'timeUp': None, 'done': None}, 'wrapUp': None,
                          'changedFiles': None, 'cleanup': None, 'commandsTruncated': False})
        self.assertEqual(result['repository'], str(self.repo.resolve()))
        self.assertEqual([c['exitCode'] for c in result['commands']], [0, 1])
        self.assertEqual(result['usage']['run'], result['usage']['session'])
        self.assertEqual(result['usage']['session']['inputTokens'], 124735)
        self.assertEqual(result['answer']['path'], str(self.logs / (run_id + '.answer')))
        self.assertEqual(result['logs'], {'events': str(self.logs / (run_id + '.events.jsonl')),
                                          'stderr': str(self.logs / (run_id + '.log'))})
        self.assertGreaterEqual(result['durationSeconds'], 0)
        self.assertRegex(result['startedAt'], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$')

    def test_resume_usage_is_the_difference(self):
        first = self.run_id(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 选哪个？'))
        later = dict(USAGE, input_tokens=201493, cached_input_tokens=176000, output_tokens=605)
        output = self.run_delegate('--resume', first, '--', '选 A',
                                   STUB_RESUME_EVENTS=json.dumps([{'type': 'turn.completed', 'usage': later}]))
        result = self.result_of(output)
        self.assertEqual((result['kind'], result['parent'], result['chainRoot'], result['resumable']),
                         ('resume', first, first, True))
        self.assertEqual(result['usage']['run']['inputTokens'], 76758)
        self.assertEqual(result['usage']['session']['inputTokens'], 201493)
        self.assertEqual(result['usage']['note'], None)
        self.assertEqual(result['markers']['needUser'], None)

    def test_resume_without_parent_usage_has_note(self):
        first = self.run_id(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 问题',
                                              STUB_EVENTS='[]'))
        result = self.result_of(self.run_delegate('--resume', first, '--', '答复',
                                                  STUB_RESUME_EVENTS=json.dumps([{'type': 'turn.completed', 'usage': USAGE}])))
        self.assertEqual((result['usage']['run'], result['usage']['note']), (None, '父轮用量未知'))

    def test_needs_input_markers(self):
        result = self.result_of(self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 选 A 还是 B？\n进度'))
        self.assertEqual((result['status'], result['markers']['needUser']), ('needs-input', '选 A 还是 B？\n进度'))

    def test_forced_timeout_fallback_records_wrapup_and_cleanup(self):
        output = self.run_delegate('--', '任务', DELEGATE_TIMEOUT_SECONDS='4', STUB_SLEEP='30')
        self.assertEqual(output.returncode, 124, output.stderr)
        result = self.result_of(output)
        self.assertEqual((result['status'], result['exitCode']), ('timeout', 124))
        self.assertEqual(result['wrapUp'], {'mode': '兜底', 'reason': '普通 run 不保留会话'})
        self.assertTrue(any(line.startswith('delegate: 清理：中止前 Codex 的后代进程') for line in result['cleanup']['lines']))
        self.assertEqual(result['timeoutSeconds'] if 'timeoutSeconds' in result else None, None)

    def test_model_time_up(self):
        result = self.result_of(self.run_delegate('--', '任务', STUB_ANSWER='TIME_UP: 做完 1 步'))
        self.assertEqual((result['status'], result['wrapUp'], result['markers']['timeUp']),
                         ('timeout', {'mode': '主动停', 'reason': None}, '做完 1 步'))

    def test_failure_paths_print_result_to_stderr(self):
        cases = (({'STUB_EXIT': '3'}, 3, 'failed'), ({'STUB_EXIT': '125'}, 125, 'unreaped'),
                 ({'STUB_ANSWER': ''}, 1, 'empty'))
        for env, code, status in cases:
            output = self.run_delegate('--', '任务', **env)
            self.assertEqual(output.returncode, code, output.stderr)
            self.assertNotIn('delegate: result=', output.stdout)
            result = self.result_of(output, 'stderr')
            self.assertEqual((result['status'], result['exitCode'], result['resumable']), (status, code, False))

    def test_interrupted_run_writes_result(self):
        import os
        import signal
        import time
        process = self.subprocess.Popen(['/bin/bash', str(PLUGIN / 'scripts' / 'delegate-exec.sh'), 'run', '--', '任务'],
                                        cwd=self.repo, env=dict(self.env, STUB_SLEEP='30'),
                                        stdout=self.subprocess.PIPE, stderr=self.subprocess.PIPE, text=True)
        deadline = time.monotonic() + 20
        while not self.calls.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        time.sleep(0.5)
        os.kill(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=60)
        self.assertEqual(process.returncode, 143, stderr)
        self.assertNotIn('delegate: result=', stdout)
        result = self.result_of(type('Output', (), {'stdout': stdout, 'stderr': stderr})(), 'stderr')
        self.assertEqual((result['status'], result['exitCode']), ('interrupted', 143))

    def test_write_run_lists_changed_files(self):
        output = self.run_delegate('--write', '--', '任务', STUB_TOUCH=str(self.repo / 'new.txt'))
        self.assertEqual(output.returncode, 0, output.stderr)
        result = self.result_of(output)
        self.assertEqual((result['write'], result['changedFiles']), (True, ['?? new.txt']))

    def test_rejection_writes_no_result(self):
        output = self.run_delegate('--resume', '20261027000000.1', '--', '答复')
        self.assertEqual(output.returncode, 64)
        self.assertNotIn('delegate: result=', output.stdout + output.stderr)
        self.assertEqual(list(self.logs.glob('*.result.json')) if self.logs.exists() else [], [])


STRICT_RESUMABLE = ('【结束标记】最终答复的第一行必须以下列标记之一开头：做完了写 `DONE:`，后面接一句总结；'
                    '需要用户拍板时写 `NEED_USER:`；到了时间预算写 `TIME_UP:`。这一要求优先于项目 AGENTS.md 或其他文件里的格式要求。')
STRICT_PLAIN = ('【结束标记】最终答复的第一行必须以下列标记之一开头：做完了写 `DONE:`，后面接一句总结；'
                '到了时间预算写 `TIME_UP:`。这一要求优先于项目 AGENTS.md 或其他文件里的格式要求。')


class StrictFlowTests(FlowBase):
    def prompt(self):
        return self.exec_calls()[-1][-1]

    def test_strict_prompt_sections(self):
        self.run_delegate('--strict', '--', '任务甲', STUB_ANSWER='DONE: 完成')
        prompt = self.prompt()
        self.assertIn('任务甲\n\n' + STRICT_PLAIN + '\n\n【时间预算】', prompt)
        first = self.run_id(self.run_delegate('--resumable', '--strict', '--', '任务乙', STUB_ANSWER='NEED_USER: 问'))
        self.assertIn('任务乙\n\n' + STRICT_RESUMABLE + '\n\n【时间预算】', self.prompt())
        self.run_delegate('--resume', first, '--strict', '--', '答复', STUB_RESUME_ANSWER='DONE: 好')
        self.assertIn(STRICT_RESUMABLE + '\n\n【时间预算】', self.prompt())
        self.run_delegate('--', '任务丙')
        self.assertNotIn('【结束标记】', self.prompt())

    def test_strict_classification(self):
        output = self.run_delegate('--strict', '--', '任务', STUB_ANSWER='DONE: 全部完成\n细节')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertTrue(output.stdout.rstrip().endswith('status=done resumable=false'))
        output = self.run_delegate('--strict', '--', '任务', STUB_ANSWER='做完了，但没写标记')
        self.assertEqual(output.returncode, 1, output.stderr)
        lines = output.stdout.splitlines()
        self.assertIn('做完了，但没写标记', output.stdout)
        self.assertRegex(lines[-2], r'^delegate: result=')
        self.assertTrue(lines[-1].endswith('status=unmarked resumable=false'), lines[-1])
        result = json.loads(Path(lines[-2].split('=', 1)[1]).read_text(encoding='utf-8'))
        self.assertEqual((result['status'], result['exitCode'], result['strict']), ('unmarked', 1, True))
        output = self.run_delegate('--strict', '--', '任务', STUB_ANSWER='NEED_USER: 普通 run 不认')
        self.assertTrue(output.stdout.rstrip().endswith('status=unmarked resumable=false'))
        output = self.run_delegate('--strict', '--', '任务', STUB_ANSWER='TIME_UP: 进度')
        self.assertEqual(output.returncode, 124)

    def test_unmarked_resumable_cannot_be_resumed(self):
        output = self.run_delegate('--resumable', '--strict', '--', '任务', STUB_ANSWER='没有标记')
        self.assertEqual(output.returncode, 1)
        run_id = self.run_id(output)
        self.assertTrue(output.stdout.rstrip().endswith('status=unmarked resumable=true'))
        refused = self.run_delegate('--resume', run_id, '--', '答复')
        self.assertEqual((refused.returncode, refused.stderr.strip().splitlines()[-1]),
                         (64, 'delegate: run not waiting for input'))

    def test_strict_rejected_with_review_context(self):
        output = self.run_delegate('--strict', '--review-context', 'x.json', '--', '任务')
        self.assertEqual(output.returncode, 64)


class RetentionTests(FlowBase):
    def test_retention_prunes_event_and_result_files(self):
        import os
        self.logs.mkdir(mode=0o700)
        old = ['20261001000000.%d' % index for index in range(55)]
        suffixes = ('.log', '.events.jsonl', '.wrapup.events.jsonl', '.result.json', '.cleanup')
        for index, run_id in enumerate(old):
            for suffix in suffixes:
                path = self.logs / (run_id + suffix)
                path.write_text('x', encoding='utf-8')
                os.utime(path, (1000000 + index, 1000000 + index))
        self.assertEqual(self.run_delegate('--', '任务').returncode, 0)
        for run_id in old[:6]:
            for suffix in suffixes:
                self.assertFalse((self.logs / (run_id + suffix)).exists(), run_id + suffix)
        for suffix in suffixes:
            self.assertTrue((self.logs / (old[6] + suffix)).exists(), old[6] + suffix)


def load_fake_responses():
    import importlib.util
    spec = importlib.util.spec_from_file_location('fake_responses', Path(__file__).with_name('fake-responses.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def codex_available():
    import shutil
    return shutil.which('codex') is not None


@unittest.skipUnless(codex_available(), 'codex CLI not on PATH')
class RealCodexEventsTests(unittest.TestCase):
    """The real Codex CLI against a local fake endpoint: no model, no credentials, a throwaway CODEX_HOME."""

    def setUp(self):
        import os
        import subprocess
        self.subprocess = subprocess
        self.fake = load_fake_responses()
        self.events = importlib.import_module('run_events')
        self.state = importlib.import_module('run_state')
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-run-result-real-')
        self.base = Path(self.temp.name)
        (self.base / 'home').mkdir()
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)
        self.env = {key: value for key, value in os.environ.items() if key not in ('OPENAI_API_KEY', 'CODEX_API_KEY')}
        self.env['CODEX_HOME'] = str(self.base / 'home')

    def tearDown(self):
        self.temp.cleanup()

    def codex(self, server, name, head, tail):
        events = self.base / (name + '.events.jsonl')
        with open(events, 'w') as out, open(self.base / (name + '.log'), 'w') as err:
            done = self.subprocess.run(['codex', *head, *self.fake.provider_args(server),
                                        '-c', 'approval_policy="never"', '--json', '-o', str(self.base / (name + '.answer')),
                                        '--', *tail],
                                       cwd=self.repo, env=self.env, stdin=self.subprocess.DEVNULL, stdout=out, stderr=err,
                                       timeout=120)
        self.assertEqual(done.returncode, 0, (self.base / (name + '.log')).read_text())
        return events

    def test_event_fields_match_the_parser(self):
        server = self.fake.start([('call', 'echo first'), ('answer', 'DONE: 第一轮'),
                                  ('call', 'ls no-such-dir'), ('answer', 'DONE: 第二轮')])
        try:
            first = self.codex(server, 'first', ['exec', '--skip-git-repo-check', '--sandbox', 'read-only',
                                                 '--color', 'never'], ['go'])
            session = self.events.session_id(first)
            self.assertIsNotNone(session)
            commands, truncated = self.events.commands(first)
            self.assertEqual(len(commands), 1)
            self.assertIn('echo first', commands[0]['command'])
            self.assertEqual((commands[0]['exitCode'], commands[0]['status'], truncated), (0, 'completed', False))
            first_usage = self.events.usage(first)
            self.assertTrue(all(isinstance(value, int) for value in first_usage.values()), first_usage)
            self.assertEqual((self.base / 'first.answer').read_text(encoding='utf-8'), 'DONE: 第一轮')
            second = self.codex(server, 'second', ['exec', 'resume', '--skip-git-repo-check',
                                                   '-c', 'sandbox_mode="read-only"'], [session, 'again'])
            self.assertEqual(self.events.session_id(second), session)
            commands, _ = self.events.commands(second)
            self.assertEqual((commands[0]['exitCode'], commands[0]['status']), (1, 'failed'))
            second_usage = self.events.usage(second)
            # turn.completed is cumulative for the session, so a resumed turn only adds to it.
            self.assertGreater(second_usage['inputTokens'], first_usage['inputTokens'])
            run, note = self.state.run_usage(second_usage, first_usage, True)
            self.assertEqual((run['inputTokens'], note), (second_usage['inputTokens'] - first_usage['inputTokens'], None))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
