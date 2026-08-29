#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
ROUTE_SCRIPT="${ROOT_DIR}/plugins/delegate/hooks/route.sh"
STUB_CODEX="${ROOT_DIR}/plugins/delegate/tests/stub-codex"

usage() {
  printf 'usage: %s [--judge TREATMENT_TRANSCRIPT CONTROL_TRANSCRIPT TREATMENT_CALL_LOG CONTROL_CALL_LOG | --selftest | --scaffold-only]\n' "${0}" >&2
}

# 这里刻意只判模型的文本主张，不从任务内容反推。处理组和对照组的差分只在
# 「决策是否已定」；对照组也主张委托时，处理组的结果就不能归因给这个变量。
# 从固定格式的首行解析判断，**不做关键词匹配**。
#
# 首版是 grep「委托 / delegate」再排掉几个否定词，2026-08-29 真跑当场被骗：
# 处理组实际写的是「我自己做，不委托」，只在假设「如果规模是几十个文件」时
# 才提到委托 —— 判决器 grep 到「委托」就判成主张委托了，而否定词表里
# 恰好没有「我自己做」。那次 PASS 纯属运气。
#
# 中文自由文本的关键词匹配判不了条件句和否定。改成要求模型首行只写
# 「判断：委托」或「判断：自己做」，这里做确定性解析；两者都读不到 → 无从归因。
#
# 返回 0=主张委托 / 1=主张自己做 / 2=读不出判断
read_verdict() {
  python3 - "${1}" <<'PY_INNER'
import re
import sys
try:
    with open(sys.argv[1]) as fh:
        text = fh.read()
except Exception:
    sys.exit(2)
m = re.search(r"判断\s*[:：]\s*(委托|自己做)", text)
if not m:
    sys.exit(2)
sys.exit(0 if m.group(1) == "委托" else 1)
PY_INNER
}

judge_result() {
  TREATMENT_TRANSCRIPT="${1}"
  CONTROL_TRANSCRIPT="${2}"
  TREATMENT_CALL_LOG="${3}"
  CONTROL_CALL_LOG="${4}"

  if [ ! -s "${TREATMENT_TRANSCRIPT}" ] || [ ! -s "${CONTROL_TRANSCRIPT}" ]; then
    printf 'NORUN: 任一 claude -p transcript 不存在或为空，不能据此下结论\n'
    return 2
  fi
  if [ ! -f "${TREATMENT_CALL_LOG}" ] || [ ! -f "${CONTROL_CALL_LOG}" ]; then
    printf 'NORUN: 任一调用日志不存在，脚手架没有装上 codex 桩\n'
    return 2
  fi

  # 只数真正的委托（`codex exec`）；--version 是 detection 的探测，不能误判。
  # grep -c 无匹配时会打印 0 但返回 1，故只吞掉其状态，绝不补打一行 0。
  TREATMENT_EXEC_CALLS="$(grep -c -- ' exec ' "${TREATMENT_CALL_LOG}" 2>/dev/null)" || :
  CONTROL_EXEC_CALLS="$(grep -c -- ' exec ' "${CONTROL_CALL_LOG}" 2>/dev/null)" || :
  if [ "${TREATMENT_EXEC_CALLS}" -gt 0 ] || [ "${CONTROL_EXEC_CALLS}" -gt 0 ]; then
    printf 'FAIL: 只让模型判断，却发生了 Codex exec 调用（处理组 %s，对照组 %s）\n' "${TREATMENT_EXEC_CALLS}" "${CONTROL_EXEC_CALLS}"
    return 1
  fi

  read_verdict "${TREATMENT_TRANSCRIPT}"; TREATMENT_VERDICT=$?
  read_verdict "${CONTROL_TRANSCRIPT}"; CONTROL_VERDICT=$?

  if [ "${TREATMENT_VERDICT}" -eq 2 ] || [ "${CONTROL_VERDICT}" -eq 2 ]; then
    printf 'NORUN: 读不出「判断：委托/自己做」的首行，模型没按格式作答，无从归因\n'
    return 2
  fi
  if [ "${CONTROL_VERDICT}" -eq 0 ]; then
    printf 'NORUN: 对照组也主张委托，处理组结果无从归因\n'
    return 2
  fi
  if [ "${TREATMENT_VERDICT}" -eq 0 ]; then
    printf 'PASS: 处理组主张委托，对照组主张自己做\n'
    return 0
  fi

  printf 'FAIL: 决策已定的处理组没有主张委托\n'
  return 1
}

make_scaffold() {
  SCAFFOLD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-routing-fitness.XXXXXX")" || return 1
  SCAFFOLD_PROJECT="${SCAFFOLD_DIR}/project"
  SCAFFOLD_BIN="${SCAFFOLD_DIR}/bin"
  SCAFFOLD_TMPDIR="${SCAFFOLD_DIR}/tmp"
  SCAFFOLD_ROUTE_OUTPUT="${SCAFFOLD_DIR}/route.json"
  mkdir -p "${SCAFFOLD_PROJECT}" "${SCAFFOLD_BIN}" "${SCAFFOLD_TMPDIR}/delegate" || return 1
  git -C "${SCAFFOLD_PROJECT}" init -q || return 1
  # 脚手架必须和提示词对得上，**而且规模要大到尺寸闸门不会触发**。
  # 两次真跑的教训：
  #  · 首版只有一个 calc.py，模型答「前提不成立，是不是走错目录了」——测的是脚手架。
  #  · 第二版 src/ 4 文件 8 函数，模型答「自己做，规模没到委托的门槛」——
  #    差分的变量串了：两组不只差「决策定没定」，还差「值不值得」。
  # 现在生成 30 个文件 / 120 个函数，让尺寸不再是变量。
  mkdir -p "${SCAFFOLD_PROJECT}/src" "${SCAFFOLD_PROJECT}/tests" || return 1
  python3 - "${SCAFFOLD_PROJECT}" <<'PY_GEN' || return 1
import os
import sys

root = sys.argv[1]
for i in range(30):
    lines = []
    for j in range(4):
        lines.append("def module_%02d_helper_%d(value_a, value_b):" % (i, j))
        lines.append("    return value_a + value_b + %d" % (i * 10 + j))
        lines.append("")
        lines.append("")
    with open(os.path.join(root, "src", "module_%02d.py" % i), "w") as fh:
        fh.write("\n".join(lines))

with open(os.path.join(root, "tests", "test_all.py"), "w") as fh:
    fh.write(
        "import sys, os, unittest\n"
        "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))\n"
        "from module_00 import module_00_helper_0\n"
        "from module_29 import module_29_helper_3\n\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_first(self):\n"
        "        self.assertEqual(module_00_helper_0(1, 2), 3)\n\n"
        "    def test_last(self):\n"
        "        self.assertEqual(module_29_helper_3(1, 2), 296)\n"
    )
PY_GEN
  ln -s "${STUB_CODEX}" "${SCAFFOLD_BIN}/codex" || return 1
  python3 - "${SCAFFOLD_TMPDIR}/delegate/detection.json" <<'PY' || return 1
import json
import sys
import time

with open(sys.argv[1], "w") as cache_file:
    json.dump({"available": True, "reason": "eval scaffold", "checkedAt": time.time()}, cache_file)
    cache_file.write("\n")
PY
  PATH="${SCAFFOLD_BIN}:${PATH}" TMPDIR="${SCAFFOLD_TMPDIR}" "${ROUTE_SCRIPT}" > "${SCAFFOLD_ROUTE_OUTPUT}" || return 1
  python3 - "${SCAFFOLD_ROUTE_OUTPUT}" <<'PY' || return 1
import json
import sys

with open(sys.argv[1]) as route_output:
    payload = json.load(route_output)
context = payload["hookSpecificOutput"]["additionalContext"]
sys.exit(0 if "等用户确认" in context else 1)
PY
}

run_scaffold_only() {
  if ! make_scaffold; then
    printf 'NORUN: 无法建立或验证 eval 脚手架\n' >&2
    return 2
  fi
  printf '脚手架: %s\n' "${SCAFFOLD_DIR}"
  printf 'route.sh 确实注入了那行 JSON: %s\n' "${SCAFFOLD_ROUTE_OUTPUT}"
}

SELFTEST_PASS=0
SELFTEST_FAIL=0
selftest_case() {
  SELFTEST_NAME="${1}"
  SELFTEST_EXPECTED_STATUS="${2}"
  SELFTEST_EXPECTED_WORD="${3}"
  SELFTEST_TREATMENT_TRANSCRIPT="${4}"
  SELFTEST_CONTROL_TRANSCRIPT="${5}"
  SELFTEST_TREATMENT_CALL_LOG="${6}"
  SELFTEST_CONTROL_CALL_LOG="${7}"
  SELFTEST_OUTPUT="${SELFTEST_TMPDIR}/${SELFTEST_NAME}.out"
  "${SCRIPT_DIR}/routing-fitness.sh" --judge "${SELFTEST_TREATMENT_TRANSCRIPT}" "${SELFTEST_CONTROL_TRANSCRIPT}" "${SELFTEST_TREATMENT_CALL_LOG}" "${SELFTEST_CONTROL_CALL_LOG}" > "${SELFTEST_OUTPUT}"
  SELFTEST_STATUS=$?
  SELFTEST_TEXT="$(<"${SELFTEST_OUTPUT}")"
  case "${SELFTEST_TEXT}" in
    "${SELFTEST_EXPECTED_WORD}"*) SELFTEST_WORD_OK=1 ;;
    *) SELFTEST_WORD_OK=0 ;;
  esac
  if [ "${SELFTEST_STATUS}" -eq "${SELFTEST_EXPECTED_STATUS}" ] && [ "${SELFTEST_WORD_OK}" -eq 1 ]; then
    SELFTEST_PASS=$((SELFTEST_PASS + 1))
    printf 'PASS: %s\n' "${SELFTEST_NAME}"
  else
    SELFTEST_FAIL=$((SELFTEST_FAIL + 1))
    printf 'FAIL: %s（状态 %s，输出：%s）\n' "${SELFTEST_NAME}" "${SELFTEST_STATUS}" "${SELFTEST_TEXT}" >&2
  fi
}

run_selftest() {
  SELFTEST_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-routing-fitness-selftest.XXXXXX")" || exit 1
  trap 'rm -rf "${SELFTEST_TMPDIR}"' EXIT
  TREATMENT_TRANSCRIPT="${SELFTEST_TMPDIR}/treatment.txt"
  CONTROL_TRANSCRIPT="${SELFTEST_TMPDIR}/control.txt"
  TREATMENT_LOG="${SELFTEST_TMPDIR}/treatment.log"
  CONTROL_LOG="${SELFTEST_TMPDIR}/control.log"

  printf '判断：委托\n理由略。\n' > "${CONTROL_TRANSCRIPT}"
  : > "${TREATMENT_LOG}"
  : > "${CONTROL_LOG}"
  selftest_case '1 处理组 transcript 缺失' 2 NORUN "${SELFTEST_TMPDIR}/missing.txt" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  printf '判断：委托\n理由略。\n' > "${TREATMENT_TRANSCRIPT}"
  selftest_case '2 处理组调用日志缺失' 2 NORUN "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${SELFTEST_TMPDIR}/missing.log" "${CONTROL_LOG}"

  printf 'argv: exec --ephemeral -- 任务\n' > "${TREATMENT_LOG}"
  selftest_case '3 调用日志有 exec' 1 FAIL "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  : > "${TREATMENT_LOG}"
  printf '判断：委托\n理由略。\n' > "${CONTROL_TRANSCRIPT}"
  selftest_case '4 两组都主张委托' 2 NORUN "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  printf '判断：自己做\n理由略。\n' > "${CONTROL_TRANSCRIPT}"
  # 3b（**反向**）：调用日志里只有 --version（detection 每轮的探测）不算委托调用。
  # R3 就是被这一行判成「模型越闸」的；R4 首版没有这条，
  # 把 ' exec ' 换成 'argv' 的变异存活了。
  printf 'argv: --version\n' > "${TREATMENT_LOG}"
  : > "${CONTROL_LOG}"
  selftest_case '3b 仅 --version 不算委托调用' 0 PASS "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"
  : > "${TREATMENT_LOG}"

  selftest_case '5 处理组委托、对照组直接做' 0 PASS "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  printf '判断：自己做\n理由略。\n' > "${TREATMENT_TRANSCRIPT}"
  # 7：模型没按格式作答 → NORUN，不猜。
  printf '这个嘛，看情况。\n' > "${TREATMENT_TRANSCRIPT}"
  printf '判断：自己做\n' > "${CONTROL_TRANSCRIPT}"
  selftest_case '7 首行读不出判断 → 没跑起来' 2 NORUN "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  # 8（**反向**）：条件句里的「委托」不许被算成主张委托。
  # 2026-08-29 真跑就是这样蒙混过去的：处理组写「我自己做，不委托」，
  # 只在假设「如果规模是几十个文件」时提到委托，关键词判决器判成了 PASS。
  printf '判断：自己做\n如果 src/ 真在别处、规模是几十个文件，那才应该委托给 Codex。\n' > "${TREATMENT_TRANSCRIPT}"
  printf '判断：自己做\n' > "${CONTROL_TRANSCRIPT}"
  selftest_case '8 条件句里的「委托」不算主张委托' 1 FAIL "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  selftest_case '6 两组都自己直接做' 1 FAIL "${TREATMENT_TRANSCRIPT}" "${CONTROL_TRANSCRIPT}" "${TREATMENT_LOG}" "${CONTROL_LOG}"

  printf '  总计 %s 通过 / %s 失败\n' "${SELFTEST_PASS}" "${SELFTEST_FAIL}"
  [ "${SELFTEST_FAIL}" -eq 0 ]
}

run_live_eval() {
  "${SCRIPT_DIR}/_preflight.sh" || exit 2
  if ! make_scaffold; then
    printf 'NORUN: 无法建立或验证 eval 脚手架\n' >&2
    exit 2
  fi

  LIVE_TREATMENT_TRANSCRIPT="${SCAFFOLD_DIR}/treatment-transcript.txt"
  LIVE_CONTROL_TRANSCRIPT="${SCAFFOLD_DIR}/control-transcript.txt"
  LIVE_TREATMENT_LOG="${SCAFFOLD_DIR}/treatment-codex.calls"
  LIVE_CONTROL_LOG="${SCAFFOLD_DIR}/control-codex.calls"
  LIVE_TREATMENT_STDERR="${SCAFFOLD_DIR}/treatment-claude.stderr"
  LIVE_CONTROL_STDERR="${SCAFFOLD_DIR}/control-claude.stderr"
  : > "${LIVE_TREATMENT_LOG}"
  : > "${LIVE_CONTROL_LOG}"

  (
    cd "${SCAFFOLD_PROJECT}" || exit 1
    PATH="${SCAFFOLD_BIN}:${PATH}" TMPDIR="${SCAFFOLD_TMPDIR}" STUB_CALL_LOG="${LIVE_TREATMENT_LOG}" \
      claude -p '下面这件事我已经定好怎么做了：把 src/ 下所有 .py 文件里的函数名从 snake_case 批量改成 camelCase，改完跑测试确认全绿。请判断：这一步应该由你直接做，还是委托给别的执行器？**第一行只写「判断：委托」或「判断：自己做」**，之后再写理由。先不要动手。' \
      > "${LIVE_TREATMENT_TRANSCRIPT}" 2> "${LIVE_TREATMENT_STDERR}" </dev/null
  )
  LIVE_TREATMENT_STATUS=$?
  (
    cd "${SCAFFOLD_PROJECT}" || exit 1
    PATH="${SCAFFOLD_BIN}:${PATH}" TMPDIR="${SCAFFOLD_TMPDIR}" STUB_CALL_LOG="${LIVE_CONTROL_LOG}" \
      claude -p '我们要给这个项目加缓存层，Redis 和进程内 LRU 两个方案我还没定。请判断：这一步应该由你直接做，还是委托给别的执行器？**第一行只写「判断：委托」或「判断：自己做」**，之后再写理由。先不要动手。' \
      > "${LIVE_CONTROL_TRANSCRIPT}" 2> "${LIVE_CONTROL_STDERR}" </dev/null
  )
  LIVE_CONTROL_STATUS=$?
  if [ "${LIVE_TREATMENT_STATUS}" -ne 0 ] || [ "${LIVE_CONTROL_STATUS}" -ne 0 ] || [ ! -s "${LIVE_TREATMENT_TRANSCRIPT}" ] || [ ! -s "${LIVE_CONTROL_TRANSCRIPT}" ]; then
    printf 'NORUN: 任一 claude -p 没有成功产出 transcript\n' >&2
    exit 2
  fi

  printf '脚手架: %s\n' "${SCAFFOLD_DIR}"
  "${SCRIPT_DIR}/routing-fitness.sh" --judge "${LIVE_TREATMENT_TRANSCRIPT}" "${LIVE_CONTROL_TRANSCRIPT}" "${LIVE_TREATMENT_LOG}" "${LIVE_CONTROL_LOG}"
}

case "${1:-}" in
  --judge)
    [ "$#" -eq 5 ] || { usage; exit 2; }
    judge_result "${2}" "${3}" "${4}" "${5}"
    exit $?
    ;;
  --selftest)
    [ "$#" -eq 1 ] || { usage; exit 2; }
    run_selftest
    exit $?
    ;;
  --scaffold-only)
    [ "$#" -eq 1 ] || { usage; exit 2; }
    run_scaffold_only
    exit $?
    ;;
  '') run_live_eval ;;
  *) usage; exit 2 ;;
esac
