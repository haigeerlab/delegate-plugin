#!/usr/bin/env python3
"""Basic Codex readiness and its shared, atomic cache contract."""
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = Path(os.environ.get('TMPDIR', '/tmp')) / 'delegate' / 'detection.json'
TTL_SECONDS = 8 * 60 * 60


def identity():
    codex = shutil.which('codex')
    try:
        version = json.loads((PLUGIN_ROOT / '.claude-plugin/plugin.json').read_text())['version']
    except (OSError, ValueError, KeyError):
        version = None
    return {'codex': os.path.realpath(codex) if codex else None,
            'codexHome': os.path.abspath(os.environ.get('CODEX_HOME', os.path.expanduser('~/.codex'))),
            'pluginRoot': str(PLUGIN_ROOT), 'pluginVersion': version}


def read_cache():
    try:
        data = json.loads(CACHE_FILE.read_text())
        age = time.time() - data['checkedAt']
        if (type(data['available']) is not bool or not isinstance(data['reason'], str)
                or isinstance(data['checkedAt'], bool) or not math.isfinite(age)
                or not 0 <= age <= TTL_SECONDS or data['identity'] != identity()):
            return None
        return data
    except (OSError, ValueError, KeyError, TypeError):
        return None


def write_cache(data):
    temporary = None
    try:
        if CACHE_FILE.parent.is_symlink():
            return False
        CACHE_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        CACHE_FILE.parent.chmod(0o700)
        with tempfile.NamedTemporaryFile(mode='w', dir=str(CACHE_FILE.parent), delete=False) as output:
            temporary = output.name
            json.dump(data, output, ensure_ascii=False)
            output.write('\n')
        os.replace(temporary, str(CACHE_FILE))
        return True
    except OSError:
        return False
    finally:
        if temporary and os.path.exists(temporary):
            try:
                os.unlink(temporary)
            except OSError:
                pass


def probe():
    wrapper = PLUGIN_ROOT / 'scripts/codex-exec.sh'
    if not os.access(str(wrapper), os.X_OK):
        return False, 'wrapper 缺失或不可执行：请修复 scripts/codex-exec.sh'
    sys.path.insert(0, str(PLUGIN_ROOT / 'scripts'))
    from backend import check
    status, reason = check()
    return status == 0, reason


def main(mode):
    data = None if mode in ('--print', '--session-start') else read_cache()
    if data is None:
        available, reason = probe()
        data = {'available': available, 'reason': reason, 'checkedAt': time.time(), 'identity': identity()}
        if not write_cache(data) and mode != '--print':
            data['available'] = False
    if mode == '--print':
        print('可用' if data['available'] else '不可用：' + data['reason'])
    elif mode not in ('--session-start', '--warm') and data['available']:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit',
              'additionalContext': 'Codex 基础条件可用（ChatGPT 登录；未验证远端连接或额度）'}}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else '')
    except Exception:
        if '--print' in sys.argv[1:]:
            print('不可用：基础探测失败，请检查 Python 3、Codex CLI 和插件文件')
