#!/bin/bash
#
# 核对「跑 eval 时装着的插件 == 仓库内容」。做不到就报「没跑起来」（退 2），不猜。
#
# --parse / --selftest 的存在理由和 spec-guard 的 check-readme-sync 取 root 参数一样：
# **是为了它自己能被测试**。首版把 `claude plugin list` 逐行过滤，只留含插件 id 的那一行，
# 而 Version 在**下一行** —— 版本永远匹配不上，preflight 恒退 2。
# 它报的是「没跑起来」这个安全结局，所以不会有人被吵到，eval 会安静地一直没用。

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_JSON="${SCRIPT_DIR}/../plugins/delegate/.claude-plugin/plugin.json"
PLUGIN_ID='delegate@delegate-marketplace'

norun() {
  printf '_preflight: %s\n' "${1}" >&2
  exit 2
}

# --parse <期望版本> <plugin-list 文本文件> → 0 一致 / 1 不一致或未安装
parse_plugin_list() {
  python3 - "${1}" "${2}" "${PLUGIN_ID}" <<'PY'
import re
import sys

expected, path, plugin_id = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as fh:
    lines = [line.rstrip("\n") for line in fh]

# 条目是「一行插件 id，后面跟若干缩进的字段行」。
# 只能在**本条目的**字段行里找 Version —— 顺着往下扫到别的条目里，
# 会把另一个插件的版本当成自己的。
block = None
for line in lines:
    if plugin_id in line:
        block = []
        continue
    if block is None:
        continue
    if line.strip() == "":
        continue
    if not (line.startswith(" ") or line.startswith("\t")):
        break          # 到了下一个条目
    if "@" in line:
        break          # 下一个条目（即使它是缩进的）
    block.append(line)

if block is None:
    sys.stderr.write("%s 未安装\n" % plugin_id)
    sys.exit(1)

found = None
for line in block:
    m = re.search(r"Version:\s*(\S+)", line)
    if m:
        found = m.group(1)
        break

if found is None:
    sys.stderr.write("%s 的条目里读不到 Version 字段\n" % plugin_id)
    sys.exit(1)
if found != expected:
    sys.stderr.write("装着的是 %s，仓库是 %s\n" % (found, expected))
    sys.exit(1)
PY
}

read_repo_version() {
  python3 - "${PLUGIN_JSON}" <<'PY'
import json
import sys
try:
    with open(sys.argv[1]) as fh:
        version = json.load(fh)["version"]
    if not isinstance(version, str) or not version:
        raise ValueError()
    print(version)
except Exception:
    sys.exit(1)
PY
}

run_selftest() {
  SELFTEST_DIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-preflight-selftest.XXXXXX")" || return 1
  trap 'rm -rf "${SELFTEST_DIR}"' EXIT
  PASS_COUNT=0
  FAIL_COUNT=0

  check() {
    parse_plugin_list "${2}" "${1}" >/dev/null 2>&1
    ACTUAL=$?
    if [ "${ACTUAL}" -eq "${3}" ]; then
      PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "${4}"
    else
      FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s（期望 %s，实际 %s）\n' "${4}" "${3}" "${ACTUAL}" >&2
    fi
  }

  printf '  ❯ delegate@delegate-marketplace\n    Version: 0.1.0\n    Scope: user\n' > "${SELFTEST_DIR}/ok.txt"
  check "${SELFTEST_DIR}/ok.txt" '0.1.0' 0 '版本一致（Version 在下一行）'

  printf '  ❯ delegate@delegate-marketplace\n    Version: 0.0.9\n' > "${SELFTEST_DIR}/old.txt"
  check "${SELFTEST_DIR}/old.txt" '0.1.0' 1 '版本不一致'

  printf '  ❯ other@other-marketplace\n    Version: 0.1.0\n' > "${SELFTEST_DIR}/absent.txt"
  check "${SELFTEST_DIR}/absent.txt" '0.1.0' 1 '插件未安装'

  # 关键反向用例：别的插件的 Version 不许被当成自己的。
  printf '  ❯ delegate@delegate-marketplace\n  ❯ other@other-marketplace\n    Version: 0.1.0\n' > "${SELFTEST_DIR}/leak.txt"
  check "${SELFTEST_DIR}/leak.txt" '0.1.0' 1 '不串到下一个条目的 Version'

  printf '  ❯ delegate@delegate-marketplace\n    Scope: user\n' > "${SELFTEST_DIR}/noversion.txt"
  check "${SELFTEST_DIR}/noversion.txt" '0.1.0' 1 '条目里没有 Version 字段'

  printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"
  [ "${FAIL_COUNT}" -eq 0 ]
}

case "${1:-}" in
  --selftest)
    run_selftest
    exit $?
    ;;
  --parse)
    [ "$#" -eq 3 ] || { printf '用法：%s --parse <期望版本> <plugin-list 文件>\n' "${0}" >&2; exit 2; }
    parse_plugin_list "${2}" "${3}"
    exit $?
    ;;
  '') ;;
  *) printf '用法：%s [--selftest | --parse <版本> <文件>]\n' "${0}" >&2; exit 2 ;;
esac

claude --version >/dev/null 2>&1 || norun 'claude CLI 不可执行（claude --version 失败）'
PLUGIN_VERSION="$(read_repo_version)" || norun '无法读取仓库 plugins/delegate 的 version'
PREFLIGHT_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-preflight.XXXXXX")" || norun '无法建立预检临时目录'
trap 'rm -rf "${PREFLIGHT_TMPDIR}"' EXIT
PLUGIN_LIST_FILE="${PREFLIGHT_TMPDIR}/plugin-list.txt"
claude plugin list > "${PLUGIN_LIST_FILE}" 2>&1 </dev/null || norun 'claude plugin list 运行失败'
parse_plugin_list "${PLUGIN_VERSION}" "${PLUGIN_LIST_FILE}" || norun '装着的 delegate 插件与仓库内容不一致'
exit 0
