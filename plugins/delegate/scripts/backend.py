#!/usr/bin/env python3
"""Check the CLI and its active login method without a model request."""
import os
import shutil
import subprocess
import sys
from run_codex import stop_group


def probe_cli(command, env):
    process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True)
    try:
        output, _ = process.communicate(timeout=5)
        return process.returncode, output
    finally:
        stop_group(process)
        process.stdout.close()


def check_detailed():
    codex = shutil.which('codex')
    if not codex:
        return 127, '找不到 codex；codex 不在 PATH：请安装 Codex CLI 并确认 PATH', 'codex_cli_missing'
    env = os.environ.copy()
    for key in ('OPENAI_API_KEY', 'CODEX_API_KEY'):
        env.pop(key, None)
    stage = 'codex_version_probe'
    try:
        version_status, _ = probe_cli([codex, '--version'], env)
        if version_status != 0:
            return 127, 'codex 无法运行（装坏了）：请执行 npm install -g @openai/codex@latest 后重试', stage + '_failed'
        stage = 'codex_login_probe'
        login_status, login_output = probe_cli([codex, 'login', 'status'], env)
    except (OSError, subprocess.TimeoutExpired) as error:
        diagnostic = stage + ('_timeout' if isinstance(error, subprocess.TimeoutExpired) else '_unavailable')
        return 127, 'Codex 版本或认证状态探测失败或超时；请运行 codex --version 和 codex login status', diagnostic
    if login_status != 0:
        return 1, '未登录或无法验证认证状态：请运行 codex login 和 codex login status', 'codex_login_status_failed'
    # Never echo raw login output: API-key status can contain credential fragments.
    lines = login_output.decode('utf-8', 'replace').splitlines()
    if 'Logged in using ChatGPT' not in [line.strip() for line in lines]:
        return 1, '需要 ChatGPT 登录；当前是 API key 或无法识别的认证方式，请运行 codex login', 'codex_login_method_unsupported'
    return 0, 'Codex 基础条件可用（ChatGPT 登录；未验证远端连接或额度）', None


def check():
    # Keep the original two-value API and legacy CLI messages.
    return check_detailed()[:2]


if __name__ == '__main__':
    status, reason = check()
    print('delegate: ' + reason)
    sys.exit(status)
