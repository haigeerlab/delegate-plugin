#!/usr/bin/env python3
"""--check (module-crew S30 operator rule, no shell) and --authorized-by; Codex is a fake executable."""
import importlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / 'scripts'))
_spec = importlib.util.spec_from_file_location('run_result_tests', Path(__file__).with_name('test-run-result.py'))
shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shared)

# Refusal texts exactly as mc-coord sent them (agent-relay #11736, module-crew main abb0432).
OPERATOR_TEXT = ('检查命令里有 shell 运算符（「{token}」）：module-crew 不经 shell 执行检查命令，运算符会被当成普通参数。'
                 "改用两种写法之一：把这些步骤写进项目脚本，检查命令写这个脚本；或写成 /bin/sh -c '<原命令>'")
EMPTY_TEXT = '检查命令不能为空'
SPLIT_TEXT = '检查命令拆不开：{error}'
OPERATORS = ('&&', '||', ';', '|', '>', '<', '`', '$(')


class CheckValidationTests(unittest.TestCase):
    def setUp(self):
        self.check = importlib.import_module('run_check')

    def test_operator_table_is_module_crew_s30(self):
        self.assertEqual(self.check.SHELL_OPS, OPERATORS)

    def test_refusal_texts(self):
        with self.assertRaises(ValueError) as caught:
            shlex.split('make "test')
        self.assertEqual(self.check.validate('make "test'), (None, SPLIT_TEXT.format(error=caught.exception)))
        self.assertEqual(self.check.validate(''), (None, EMPTY_TEXT))
        self.assertEqual(self.check.validate('   '), (None, EMPTY_TEXT))
        self.assertEqual(self.check.validate('make test && make lint'), (None, OPERATOR_TEXT.format(token='&&')))

    def test_every_operator_at_token_start_and_end(self):
        for op in OPERATORS:
            for command in ('make %sx' % op, 'make x%s' % op):
                argv, refusal = self.check.validate(command)
                self.assertIsNone(argv, command)
                self.assertEqual(refusal, OPERATOR_TEXT.format(token=shlex.split(command)[1]), command)

    def test_copied_boundaries(self):
        for command, argv in (('foo&&bar', ['foo&&bar']), ('a|b', ['a|b']),
                              ("/bin/sh -c 'make test && make lint'", ['/bin/sh', '-c', 'make test && make lint']),
                              ('make test 2>&1', ['make', 'test', '2>&1']), ('run &', ['run', '&']),
                              ('echo $VAR', ['echo', '$VAR'])):
            self.assertEqual(self.check.validate(command), (argv, None), command)
        self.assertEqual(self.check.validate('make >file'), (None, OPERATOR_TEXT.format(token='>file')))


class CheckRefusalFlowTests(shared.FlowBase):
    def test_refusal_prints_only_the_text_and_does_not_start_codex(self):
        for command, text in (('make "test', None), ('', EMPTY_TEXT), ('make && lint', OPERATOR_TEXT.format(token='&&'))):
            output = self.run_delegate('--check', command, '--', '任务')
            self.assertEqual(output.returncode, 64, command)
            last = output.stderr.strip().splitlines()[-1]
            if text is None:
                self.assertTrue(last.startswith('检查命令拆不开：'), last)
            else:
                self.assertEqual(last, text)
        self.assertFalse(self.calls.exists())
        self.assertEqual(self.run_delegate('--check', 'a', '--check', 'b', '--', '任务').returncode, 64)


class CheckRunFlowTests(shared.FlowBase):
    def setUp(self):
        super().setUp()
        self.order = self.base / 'order.log'
        script = self.repo / 'check.sh'
        script.write_text('#!/bin/sh\n'
                          'printf "check cwd=%s args=%s\\n" "$(pwd -P)" "$*" >> "' + str(self.order) + '"\n'
                          'if read line; then echo "stdin had data"; fi\n'
                          'i=0; while [ $i -lt 45 ]; do echo "line $i"; i=$((i+1)); done\n'
                          'sleep "${CHECK_SLEEP:-0}"\n'
                          'exit "${CHECK_EXIT:-0}"\n', encoding='utf-8')
        script.chmod(0o755)
        self.subprocess.run(['git', 'add', 'check.sh'], cwd=self.repo, check=True)
        self.subprocess.run(['git', 'commit', '-qm', 'check'], cwd=self.repo, check=True)

    def result_of(self, output):
        lines = [l for l in (output.stdout + output.stderr).splitlines() if l.startswith('delegate: result=')]
        return json.loads(Path(lines[0].split('=', 1)[1]).read_text(encoding='utf-8'))

    def test_passed_runs_without_shell_in_repo_root(self):
        output = self.run_delegate('--check', './check.sh "*" b', '--', '任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertIn('检查：通过', output.stdout)
        self.assertEqual(self.order.read_text(encoding='utf-8').strip(),
                         'check cwd=%s args=* b' % self.repo.resolve())
        check = self.result_of(output)['check']
        self.assertEqual((check['command'], check['argv'], check['status'], check['exitCode']),
                         ('./check.sh "*" b', ['./check.sh', '*', 'b'], 'passed', 0))
        tail = check['tail'].splitlines()
        self.assertEqual((len(tail), tail[-1]), (40, 'line 44'))
        self.assertNotIn('stdin had data', check['tail'])
        self.assertGreaterEqual(check['durationSeconds'], 0)

    def test_failed_check_does_not_change_the_run(self):
        output = self.run_delegate('--check', './check.sh', '--', '任务', CHECK_EXIT='3')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertTrue(output.stdout.rstrip().endswith('status=done resumable=false'))
        self.assertIn('检查：失败（退出 3）', output.stdout)
        check = self.result_of(output)['check']
        self.assertEqual((check['status'], check['exitCode']), ('failed', 3))

    def test_cannot_run_and_timeout(self):
        for command, env, status, label in (('./no-such-program', {}, 'cannot-run', '检查：跑不起来'),
                                            ('./check.sh', {'CHECK_EXIT': '126'}, 'cannot-run', '检查：跑不起来'),
                                            ('./check.sh', {'CHECK_EXIT': '127'}, 'cannot-run', '检查：跑不起来'),
                                            ('./check.sh', {'CHECK_SLEEP': '30', 'DELEGATE_CHECK_TIMEOUT_SECONDS': '2'},
                                             'timeout', '检查：超时')):
            output = self.run_delegate('--check', command, '--', '任务', **env)
            self.assertEqual(output.returncode, 0, output.stderr)
            self.assertIn(label, output.stdout, command)
            self.assertEqual(self.result_of(output)['check']['status'], status, command)

    def test_check_timeout_can_only_shorten(self):
        run_check = importlib.import_module('run_check')
        self.assertEqual(run_check.CHECK_TIMEOUT_SECONDS, 600)
        self.assertEqual(run_check.check_timeout({'DELEGATE_CHECK_TIMEOUT_SECONDS': '9999'}), 600)
        self.assertEqual(run_check.check_timeout({'DELEGATE_CHECK_TIMEOUT_SECONDS': 'x'}), 600)
        self.assertEqual(run_check.check_timeout({'DELEGATE_CHECK_TIMEOUT_SECONDS': '5'}), 5)
        self.assertEqual(run_check.check_timeout({}), 600)

    def test_unreaped_status_from_executor(self):
        run_check = importlib.import_module('run_check')
        self.assertEqual(run_check.status_of(125, ''), 'unreaped')
        self.assertEqual(run_check.status_of(124, ''), 'timeout')
        self.assertEqual(run_check.status_of(127, 'delegate: 无法启动 Codex：x'), 'cannot-run')
        self.assertEqual(run_check.status_of(143, ''), 'failed')

    def test_skipped_when_not_done(self):
        for env, code in (({'STUB_ANSWER': 'NEED_USER: 问'}, 0), ({'STUB_ANSWER': 'TIME_UP: 进度'}, 124),
                          ({'STUB_EXIT': '3'}, 3)):
            args = ('--resumable',) if 'NEED_USER' in env.get('STUB_ANSWER', '') else ()
            output = self.run_delegate(*args, '--check', './check.sh', '--', '任务', **env)
            self.assertEqual(output.returncode, code, output.stderr)
            self.assertEqual(self.result_of(output)['check'],
                             {'command': './check.sh', 'argv': ['./check.sh'], 'status': 'skipped'})
        self.assertFalse(self.order.exists())

    def test_check_runs_before_git_acceptance(self):
        output = self.run_delegate('--write', '--check', './check.sh', '--', '任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertLess(output.stdout.index('检查：通过'), output.stdout.index('git 验收'))

    def test_no_check_field_without_option(self):
        self.assertNotIn('check', self.result_of(self.run_delegate('--', '任务')))


class AuthorizationFlowTests(shared.FlowBase):
    def setUp(self):
        super().setUp()
        self.grant = self.base / 'grant.txt'
        self.grant.write_text('用户原话：打开外包开关\n', encoding='utf-8')

    def result_of(self, output):
        lines = [l for l in (output.stdout + output.stderr).splitlines() if l.startswith('delegate: result=')]
        return json.loads(Path(lines[0].split('=', 1)[1]).read_text(encoding='utf-8'))

    def sha(self, path):
        import hashlib
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_refusals(self):
        link = self.base / 'link.txt'
        link.symlink_to(self.grant)
        empty = self.base / 'empty.txt'
        empty.write_text('', encoding='utf-8')
        big = self.base / 'big.txt'
        big.write_bytes(b'x' * (64 * 1024 + 1))
        cases = [(('--authorized-by', str(self.grant), '--', '任务'), 'delegate: --authorized-by requires --write')]
        for path in (link, empty, big, self.base / 'missing.txt', self.base):
            cases.append((('--write', '--authorized-by', str(path), '--', '任务'), 'delegate: authorization file not usable'))
        for args, message in cases:
            output = self.run_delegate(*args)
            self.assertEqual(output.returncode, 64, args)
            self.assertIn(message, output.stderr, args)
        self.assertFalse(self.calls.exists())

    def test_sources_are_recorded(self):
        output = self.run_delegate('--write', '--authorized-by', str(self.grant), '--', '任务')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(self.result_of(output)['authorization'],
                         {'source': 'file', 'path': str(self.grant.resolve()), 'sha256': self.sha(self.grant),
                          'bytes': self.grant.stat().st_size})
        self.assertIn('写入授权：文件 %s（sha256 %s）' % (self.grant.resolve(), self.sha(self.grant)[:12]), output.stdout)
        output = self.run_delegate('--write', '--', '任务')
        self.assertEqual(self.result_of(output)['authorization'], {'source': 'in-turn'})
        self.assertIn('写入授权：当轮', output.stdout)
        output = self.run_delegate('--', '任务')
        self.assertIsNone(self.result_of(output)['authorization'])
        self.assertNotIn('写入授权', output.stdout)

    def test_chain_must_keep_the_same_file(self):
        first = self.run_id(self.run_delegate('--resumable', '--write', '--authorized-by', str(self.grant), '--', '任务',
                                              STUB_ANSWER='DONE: 好'))
        same = self.base / 'same.txt'
        same.write_bytes(self.grant.read_bytes())
        output = self.run_delegate('--continue', first, '--write', '--', '下一个')
        self.assertEqual((output.returncode, output.stderr.strip().splitlines()[-1]), (64, 'delegate: authorization mismatch'))
        other = self.base / 'other.txt'
        other.write_text('别的授权\n', encoding='utf-8')
        output = self.run_delegate('--continue', first, '--write', '--authorized-by', str(other), '--', '下一个')
        self.assertEqual((output.returncode, output.stderr.strip().splitlines()[-1]), (64, 'delegate: authorization mismatch'))
        output = self.run_delegate('--continue', first, '--write', '--authorized-by', str(same), '--', '下一个')
        self.assertEqual(output.returncode, 0, output.stderr)

    def test_authorization_added_mid_chain_is_checked_from_then_on(self):
        first = self.run_id(self.run_delegate('--resumable', '--write', '--', '任务', STUB_ANSWER='DONE: 好'))
        second = self.run_id(self.run_delegate('--continue', first, '--write', '--authorized-by', str(self.grant),
                                               '--', '下一个'))
        output = self.run_delegate('--continue', second, '--write', '--', '再下一个')
        self.assertEqual((output.returncode, output.stderr.strip().splitlines()[-1]), (64, 'delegate: authorization mismatch'))


if __name__ == '__main__':
    unittest.main()
