#!/usr/bin/env python3
"""Two explicit executors; capabilities are not model or authentication claims."""

BACKENDS = {
    'codex': {'review': True, 'run': True, 'write': True, 'resume': True, 'result': True, 'continue': True, 'longRun': True,
              'options': ('--model', '--effort')},
    'claude-code': {'review': True, 'run': False, 'write': False, 'resume': False, 'result': False, 'continue': False, 'longRun': False,
                    'options': ('--model', '--max-turns', '--max-budget-usd')},
}


def describe():
    return '\n'.join(name + '：只读 review' + ('；run（默认只读，可显式 --write）' if value['run'] else '；不支持 run/写入')
                     + '；选项 ' + ' '.join(value['options']) for name, value in BACKENDS.items())
