#!/usr/bin/env python3
"""Backend-specific model-free diagnostics; old Codex doctor remains intact."""
import os
from pathlib import Path
import shutil
import sys
from claude_review import PreflightError, preflight
from review_macos import BoundaryError
from review_native import NativeRunner, native_temporary
from delegate_capabilities import describe


def main():
    if os.environ.get('DELEGATE_REVIEW_DEPTH', '0') != '0':
        print('delegate: recursive delegation is not supported.', file=sys.stderr)
        return 64
    args = sys.argv[1:]
    if args in ([], ['--backend', 'codex'], ['--backend', 'claude-code']):
        print('后端能力（非可用性结论）：\n' + describe(), flush=True)
    if args in ([], ['--backend', 'codex']):
        path = Path(__file__).resolve().parents[1] / 'hooks/doctor.sh'
        os.execv('/bin/bash', ['/bin/bash', str(path)])
    if args != ['--backend', 'claude-code']:
        print('用法：review_doctor.py [--backend codex|claude-code]', file=sys.stderr)
        return 64
    print('delegate: host=unknown backend=claude-code（无模型体检）')
    temporary = None
    retained = False
    try:
        context = {'repository': str(Path.cwd().resolve()), 'files': {}, 'file_sha256': {},
                   'allowed_tools': ['Read']}
        temporary = native_temporary(context, 'delegate-doctor.')
        runner = NativeRunner(temporary, context)
        runner.runtime_preflight()
        facts = preflight(str(runner.claude), runner.invoke)
        print('本机 CLI、原有认证和进程边界预检通过：Claude ' + facts['version'])
        print('认证方式：' + facts['auth_method'] + '；提供者：' + facts['provider'])
        print('模型、额度、审查工具和跨宿主实际任务：未验证。')
        print('诊断完成；发现 0 个配置问题，不代表后端审查可用或远端/额度可用。')
    except (BoundaryError, PreflightError, ValueError, OSError) as error:
        code = str(error) if isinstance(error, (BoundaryError, PreflightError)) else 'native_environment_unavailable'
        retained = code in ('runtime_cleanup_unverified', 'probe_cleanup_unverified')
        print('条件不足：' + code)
        print('诊断完成；发现 1 个配置问题。未检查 Codex，未启动模型。')
        if retained:
            print('清理未核实；私有控制证据：' + str(temporary))
    finally:
        if temporary is not None and not retained:
            shutil.rmtree(temporary)
    return 0


if __name__ == '__main__':
    sys.exit(main())
