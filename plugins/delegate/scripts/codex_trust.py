#!/usr/bin/env python3
"""Temporary Codex project trust for write runs; the user's Codex configuration is only read.

Codex persists `[projects."<root>"] trust_level = "trusted"` on the first workspace-write thread for a
project that has no trust level yet. An inline `-c projects={...}` override is merged by key and stops
that write, so it is offered only when the user's config.toml shows no entry for this project.
"""
import os
import subprocess
import sys

REASON_UNREADABLE = '配置文件无法读取'
REASON_ENCODING = '配置文件不是 UTF-8'
REASON_PATH = '仓库路径含引号、反斜杠或控制字符'
REASON_ROOT = '无法确定 Git 信任根'


def override(root):
    return 'projects={"%s"={trust_level="trusted"}}' % root


def trust_root(common_dir):
    # Codex keys trust by the main repository: the parent of the common .git directory.
    if not common_dir:
        return None
    common_dir = os.path.normpath(common_dir)
    if os.path.basename(common_dir) != '.git':
        return None
    return os.path.dirname(common_dir)


def candidate_keys(cwd, pwd, root):
    keys = [cwd]
    if pwd and os.path.isabs(pwd) and os.path.realpath(pwd) == os.path.realpath(cwd):
        keys.append(pwd)
    if root:
        keys.extend([root, os.path.realpath(root)])
    unique = []
    for key in keys:
        if key not in unique:
            unique.append(key)
    return unique


def _unsafe(key):
    return any(char in '"\\' or ord(char) < 0x20 or ord(char) == 0x7f for char in key)


def decide(config, keys, root):
    """Return (override value or None, reason or None); config is the file's bytes, or None if absent."""
    if root is None:
        return None, REASON_ROOT
    if any(_unsafe(key) for key in keys + [root]):
        return None, REASON_PATH
    if config is None:
        return override(root), None
    try:
        text = config.decode('utf-8')
    except UnicodeDecodeError:
        return None, REASON_ENCODING
    # Keys containing "/" must be quoted in TOML, so a real entry always shows a quoted path.
    for key in keys:
        if '"%s"' % key in text or "'%s'" % key in text:
            return None, None
    return override(root), None


def read_config(path):
    try:
        with open(path, 'rb') as handle:
            return handle.read(), None
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, REASON_UNREADABLE


def notice(reason, path):
    return ('delegate: 未能确认 Codex 用户配置里有没有本仓库的信任条目（%s），本次不加临时信任；'
            'Codex 可能会往 %s 写入一条信任记录。' % (reason, path))


def main():
    home = os.environ.get('CODEX_HOME') or os.path.join(os.path.expanduser('~'), '.codex')
    path = os.path.join(home, 'config.toml')
    cwd = os.getcwd()
    result = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                            capture_output=True, text=True, check=False)
    root = trust_root(result.stdout.strip()) if result.returncode == 0 else None
    keys = candidate_keys(cwd, os.environ.get('PWD', ''), root)
    config, reason = read_config(path)
    value = None
    if reason is None:
        value, reason = decide(config, keys, root)
    if reason:
        print(notice(reason, path), file=sys.stderr)
    if value:
        print(value)
    return 0


if __name__ == '__main__':
    sys.exit(main())
