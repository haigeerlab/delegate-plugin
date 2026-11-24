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
    if args in (['--reviewers'], ['--reviewers', '--json']):
        return reviewers(json_output=len(args) == 2)
    if args in ([], ['--backend', 'codex'], ['--backend', 'claude-code']):
        print('后端能力（非可用性结论）：\n' + describe(), flush=True)
    if args in ([], ['--backend', 'codex']):
        path = Path(__file__).resolve().parents[1] / 'hooks/doctor.sh'
        os.execv('/bin/bash', ['/bin/bash', str(path)])
    if args != ['--backend', 'claude-code']:
        print('用法：review_doctor.py [--backend codex|claude-code] | --reviewers [--json]', file=sys.stderr)
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
        if runner.trust_diagnostics:
            print('系统证书导出：' + runner.trust_diagnostics[0] + '（不影响运行，沙箱只用 CLI 自带的公共根证书）')
        else:
            print('系统明确信任的证书：%d 张，已加入沙箱' % runner.trust_count)
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


def reviewers(*, json_output):
    """spec/reviewer-selection.md E5: list usable second reviewers; never blocks, always exits 0."""
    import json
    import reviewer_select
    checks = reviewer_select.real_checks()
    rows = []
    for name, vendor in reviewer_select.VENDORS.items():
        problem = checks[name]()
        rows.append({'backend': name, 'vendor': vendor, 'available': problem is None, 'diagnostic': problem})
    usable = sum(row['available'] for row in rows)
    hint = None if usable == len(rows) else 'add_second_vendor' if usable else 'no_reviewer_available'
    if json_output:
        print(json.dumps({'schema': 'delegate.reviewers/v1', 'reviewers': rows, 'hint': hint}, ensure_ascii=False))
        return 0
    print('delegate: 第二审查者（无模型检查，不发请求）')
    for row in rows:
        state = '可用' if row['available'] else '不可用（%s）' % row['diagnostic']
        print('%s（%s）：%s' % (row['backend'], row['vendor'], state))
    if hint == 'add_second_vendor':
        print('只有一家可用：技术方案会由同厂商的独立会话审查。建议再开通一家，以便异厂商审查。')
    elif hint == 'no_reviewer_available':
        print('两家都不可用：技术方案审查会记为「未审」，由回归测试兜底。')
    print('不阻止任何操作；模型、额度与真实审查未验证。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
