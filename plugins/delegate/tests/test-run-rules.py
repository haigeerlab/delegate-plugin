#!/usr/bin/env python3
"""--rules-file: a per-delegation rules section placed verbatim after the preamble. Codex is a fake executable."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location('run_result_tests', Path(__file__).with_name('test-run-result.py'))
shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shared)

HEAD = ('【项目规则（本次委托专用）】以下规则由调用方提供，只对本次委托有效；与上文冲突时以本节为准。'
        '但下面几条不能被本节改变：沙箱限制；不提交、不推送；最终答复第一行的标记（`NEED_USER:`、`TIME_UP:`，以及要求时的 `DONE:`）。')
TAIL = '【项目规则结束】'
RULES = '本 Task 的验收口径：\n- 只改 src/a.py\n- 跑 make test\n\n'


def section(text):
    return HEAD + '\n\n' + (text if text.endswith('\n') else text + '\n') + '\n' + TAIL


class RulesFlowTests(shared.FlowBase):
    def setUp(self):
        super().setUp()
        self.rules = self.base / 'rules.md'
        self.rules.write_text(RULES, encoding='utf-8')

    def prompt(self):
        return self.exec_calls()[-1][-1]

    def result_of(self, output):
        line = [l for l in output.stdout.splitlines() if l.startswith('delegate: result=')][0]
        return json.loads(Path(line.split('=', 1)[1]).read_text(encoding='utf-8'))

    def test_refusals(self):
        link = self.base / 'link.md'
        link.symlink_to(self.rules)
        cases = {'missing': self.base / 'missing.md', 'link': link, 'directory': self.base}
        for name, data in (('empty', b''), ('blank', b'  \n\t\n'), ('big', b'x' * 16385), ('latin1', 'caf\xe9'.encode('latin-1')),
                           ('nul', b'a\x00b')):
            path = self.base / (name + '.md')
            path.write_bytes(data)
            cases[name] = path
        for name, path in cases.items():
            output = self.run_delegate('--rules-file', str(path), '--', '任务')
            self.assertEqual(output.returncode, 64, name)
            self.assertIn('delegate: rules file not usable\n', output.stderr, name)
        self.assertFalse(self.calls.exists())
        exact = self.base / 'exact.md'
        exact.write_bytes(b'x' * 16384)
        self.assertEqual(self.run_delegate('--rules-file', str(exact), '--', '任务').returncode, 0)

    def test_placement_in_each_kind_of_call(self):
        self.run_delegate('--rules-file', str(self.rules), '--', '任务甲')
        prompt = self.prompt()
        self.assertTrue(prompt.startswith('【非交互委托】'))
        self.assertIn('不要做任务之外的网络访问。\n\n' + section(RULES) + '\n\n任务甲\n\n【时间预算】', prompt)
        first = self.run_id(self.run_delegate('--resumable', '--rules-file', str(self.rules), '--strict', '--', '任务乙',
                                              STUB_ANSWER='DONE: 好'))
        prompt = self.prompt()
        self.assertTrue(prompt.startswith('【可续跑委托】'))
        self.assertIn(section(RULES) + '\n\n任务乙\n\n【结束标记】', prompt)
        second = self.run_id(self.run_delegate('--continue', first, '--rules-file', str(self.rules), '--', '任务丙',
                                               STUB_RESUME_ANSWER='NEED_USER: 问'))
        self.assertTrue(self.prompt().startswith(section(RULES) + '\n\n【下一个任务】任务丙'))
        self.run_delegate('--resume', second, '--rules-file', str(self.rules), '--', '答复')
        self.assertTrue(self.prompt().startswith(section(RULES) + '\n\n【用户答复】答复'))
        no_newline = self.base / 'one.md'
        no_newline.write_text('只有一行', encoding='utf-8')
        self.run_delegate('--rules-file', str(no_newline), '--', '任务丁')
        self.assertIn(section('只有一行\n'), self.prompt())

    def test_without_rules_the_prompt_is_unchanged(self):
        self.run_delegate('--', '任务')
        self.assertNotIn('【项目规则', self.prompt())

    def test_wrapup_round_has_no_rules(self):
        output = self.run_delegate('--resumable', '--rules-file', str(self.rules), '--', '任务',
                                   DELEGATE_TIMEOUT_SECONDS='12', STUB_SLEEP='30', STUB_RESUME_ANSWER='TIME_UP: 进度')
        self.assertEqual(output.returncode, 124, output.stderr)
        self.assertTrue(self.prompt().startswith('【收尾】'))
        self.assertNotIn('【项目规则', self.prompt())

    def test_result_records_identity_not_text(self):
        output = self.run_delegate('--rules-file', str(self.rules), '--', '任务')
        result = self.result_of(output)
        self.assertEqual(result['rules'], {'path': str(self.rules.resolve()),
                                           'sha256': hashlib.sha256(self.rules.read_bytes()).hexdigest(),
                                           'bytes': len(self.rules.read_bytes())})
        self.assertNotIn('只改 src/a.py', json.dumps(result, ensure_ascii=False))
        self.assertNotIn('rules', self.result_of(self.run_delegate('--', '任务')))


if __name__ == '__main__':
    unittest.main()
