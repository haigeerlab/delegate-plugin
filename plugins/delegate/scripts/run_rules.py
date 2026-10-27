#!/usr/bin/env python3
"""--rules-file: one per-delegation rules section, placed verbatim after the preamble (spec/run-rules.md)."""
import hashlib
import os
import stat
import sys

MAX_BYTES = 16384
HEAD = ('【项目规则（本次委托专用）】以下规则由调用方提供，只对本次委托有效；与上文冲突时以本节为准。'
        '但下面几条不能被本节改变：沙箱限制；不提交、不推送；最终答复第一行的标记（`NEED_USER:`、`TIME_UP:`，以及要求时的 `DONE:`）。')
TAIL = '【项目规则结束】'


def read(path):
    """(text, data, None) for a usable rules file, else (None, None, reason)."""
    try:
        info = os.lstat(path)
    except OSError:
        return None, None, '文件不存在或读不了'
    if stat.S_ISLNK(info.st_mode):
        return None, None, '是软链接'
    if not stat.S_ISREG(info.st_mode):
        return None, None, '不是普通文件'
    if info.st_size > MAX_BYTES:
        return None, None, '超过 16 KiB'
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'rb') as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError:
        return None, None, '读不了'
    if len(data) > MAX_BYTES:
        return None, None, '超过 16 KiB'
    if b'\0' in data:
        return None, None, '含 NUL 字符'
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return None, None, '不是合法 UTF-8'
    if not text.strip():
        return None, None, '为空'
    return text, data, None


def section(text):
    return HEAD + '\n\n' + (text if text.endswith('\n') else text + '\n') + '\n' + TAIL


def identity(path):
    """What the result file records: where the rules came from, never their text."""
    text, data, reason = read(path)
    if reason:
        return None
    return {'path': os.path.realpath(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def main(arguments):
    if len(arguments) == 2 and arguments[0] == 'section':
        text, _, reason = read(arguments[1])
        if reason:
            print('delegate: rules file not usable\n' + reason, file=sys.stderr)
            return 64
        sys.stdout.write(section(text))
        return 0
    print('delegate: run_rules usage error', file=sys.stderr)
    return 64


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
