#!/usr/bin/env python3
"""--timeout widens the deadline only; cleanup stays with run_codex.py (0.7.1). Codex is a fake executable."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

_spec = importlib.util.spec_from_file_location('run_result_tests', Path(__file__).with_name('test-run-result.py'))
shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shared)

# Records the arguments run_codex.py receives, then runs the real interpreter.
PYTHON_SHIM = r'''#!/bin/sh
for ARG in "$@"; do
  case "${ARG}" in
    *run_codex.py) printf '%s\n' "$*" >> "${RUNNER_LOG}" ;;
  esac
done
exec "__PYTHON__" "$@"
'''


class LongRunTests(shared.FlowBase):
    def setUp(self):
        super().setUp()
        shim = self.base / 'bin' / 'python3'
        shim.write_text(PYTHON_SHIM.replace('__PYTHON__', sys.executable), encoding='utf-8')
        shim.chmod(0o755)
        self.runner_log = self.base / 'runner.log'
        self.env['RUNNER_LOG'] = str(self.runner_log)

    def runner_deadlines(self):
        return [line.split()[line.split().index('--report') + 2]
                for line in self.runner_log.read_text(encoding='utf-8').splitlines() if 'run_codex.py --report' in line]

    def result_of(self, output):
        line = [l for l in output.stdout.splitlines() if l.startswith('delegate: result=')][0]
        return json.loads(Path(line.split('=', 1)[1]).read_text(encoding='utf-8'))

    def test_invalid_values_are_refused_before_codex(self):
        for value in ('540', '7201', 'abc', '-1', '', '600.5', '0'):
            output = self.run_delegate('--timeout', value, '--', '任务')
            self.assertEqual(output.returncode, 64, value)
            self.assertEqual(output.stderr.strip().splitlines()[-1],
                             'delegate: --timeout must be an integer between 541 and 7200', value)
        self.assertFalse(self.calls.exists())

    def test_timeout_sets_the_deadline_and_ignores_the_environment(self):
        output = self.run_delegate('--timeout', '1800', '--', '任务', DELEGATE_TIMEOUT_SECONDS='60')
        self.assertEqual(output.returncode, 0, output.stderr)
        prompt = self.exec_calls()[-1][-1]
        self.assertIn('1755 秒后会被强制中止', prompt)
        self.assertIn('已用时达到 1665 秒后', prompt)
        self.assertEqual(self.runner_deadlines(), ['1755'])
        self.assertEqual(self.result_of(output)['timeoutSeconds'], 1800)
        for value, main in (('541', '496'), ('7200', '7155')):
            self.run_delegate('--timeout', value, '--', '任务')
            self.assertEqual(self.runner_deadlines()[-1], main)

    def test_without_timeout_nothing_changes(self):
        output = self.run_delegate('--', '任务')
        self.assertIn('50 秒后会被强制中止', self.exec_calls()[-1][-1])
        self.assertEqual(self.runner_deadlines(), ['50'])
        self.assertEqual(self.result_of(output)['timeoutSeconds'], 60)

    def test_timeout_applies_to_every_run_kind(self):
        first = self.run_id(self.run_delegate('--resumable', '--timeout', '900', '--', '任务', STUB_ANSWER='DONE: 好'))
        second = self.run_id(self.run_delegate('--continue', first, '--timeout', '1200', '--', '下一个'))
        self.run_delegate('--resumable', '--', '任务', STUB_ANSWER='NEED_USER: 问')
        waiting = self.run_id(self.run_delegate('--continue', second, '--', '再下一个', STUB_RESUME_ANSWER='NEED_USER: 问'))
        self.run_delegate('--resume', waiting, '--timeout', '600', '--', '答复')
        self.assertEqual([deadline for deadline in self.runner_deadlines()], ['855', '1155', '50', '50', '555'])

    def test_resumable_run_with_timeout(self):
        output = self.run_delegate('--resumable', '--timeout', '600', '--', '任务', STUB_SLEEP='0')
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(self.runner_deadlines(), ['555'])


if __name__ == '__main__':
    unittest.main()
