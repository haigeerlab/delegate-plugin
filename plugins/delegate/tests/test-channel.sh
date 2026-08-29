#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXEC_SCRIPT="${SCRIPT_DIR}/../scripts/codex-exec.sh"
TEST_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-channel-test.XXXXXX")"
trap 'rm -rf "${TEST_TMPDIR}"' EXIT
TEST_BIN="${TEST_TMPDIR}/bin"
mkdir "${TEST_BIN}"
ln -s "${SCRIPT_DIR}/stub-codex" "${TEST_BIN}/codex"
PATH="${TEST_BIN}:${PATH}"
export PATH

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "${1}"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "${1}" >&2
}

assert_status() {
  EXPECTED_STATUS="${1}"
  ACTUAL_STATUS="${2}"
  NAME="${3}"
  if [ "${ACTUAL_STATUS}" -eq "${EXPECTED_STATUS}" ]; then
    pass "${NAME}"
  else
    fail "${NAME}（预期退出 ${EXPECTED_STATUS}，实际 ${ACTUAL_STATUS}）"
  fi
}

wait_for_file() {
  TARGET="${1}"
  ATTEMPTS=0
  while [ "${ATTEMPTS}" -lt 20 ]; do
    if [ -s "${TARGET}" ]; then
      return 0
    fi
    sleep 0.1
    ATTEMPTS=$((ATTEMPTS + 1))
  done
  return 1
}

# 1：过程 stdout 必须被日志文件隔离。
CALL_LOG="${TEST_TMPDIR}/one.argv"
RESULT="${TEST_TMPDIR}/one.stdout"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='简短答复' STUB_STDOUT_BYTES=100000 \
  "${EXEC_SCRIPT}" '测试过程日志隔离' >"${RESULT}" 2>"${TEST_TMPDIR}/one.stderr"
STATUS=$?
RESULT_BYTES="$(wc -c < "${RESULT}" | tr -d ' ')"
if [ "${STATUS}" -eq 0 ] && [ "${RESULT_BYTES}" -lt 100000 ] && ! grep -F -- 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' "${RESULT}" >/dev/null; then
  pass '1：100KB 过程输出未进入调用方 stdout'
else
  fail '1：100KB 过程输出泄漏到调用方 stdout'
fi

# stdin 持有者用有界的 sleep 且吞掉 stderr：
#   · 无限 while 循环杀不掉 —— 管道后台化时 $! 是**末端**命令的 PID
#   · 它继承套件的 stderr，于是 `test-channel.sh | grep` 永远等不到 EOF（实测挂 >10 分钟）
# 2a：先直接调用桩，证明永不关闭的 stdin 确实会阻塞。
CALL_LOG="${TEST_TMPDIR}/two-a.argv"
ANSWER="${TEST_TMPDIR}/two-a.answer"
( sleep 10 ) 2>/dev/null | STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='直接调用答复' STUB_READ_STDIN=1 \
  codex exec -o "${ANSWER}" -- '读取 stdin' >"${TEST_TMPDIR}/two-a.stdout" 2>"${TEST_TMPDIR}/two-a.stderr" &
PID=$!
if wait_for_file "${ANSWER}"; then
  fail '2a：直接调用桩在永不关闭 stdin 下应阻塞'
else
  pass '2a：直接调用桩在永不关闭 stdin 下未完成'
fi
kill "${PID}" 2>/dev/null || true

# 2b：wrapper 的 </dev/null 必须覆盖同样的永不关闭 stdin。
CALL_LOG="${TEST_TMPDIR}/two-b.argv"
RESULT="${TEST_TMPDIR}/two-b.stdout"
( sleep 10 ) 2>/dev/null | STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='经 wrapper 答复' STUB_READ_STDIN=1 \
  "${EXEC_SCRIPT}" '读取 stdin' >"${RESULT}" 2>"${TEST_TMPDIR}/two-b.stderr" &
PID=$!
if wait_for_file "${RESULT}"; then
  pass '2b：wrapper 在永不关闭 stdin 下限时内完成'
else
  fail '2b：wrapper 在永不关闭 stdin 下没有完成'
fi
kill "${PID}" 2>/dev/null || true

# 10：默认沙箱必须为只读。
CALL_LOG="${TEST_TMPDIR}/ten.argv"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='答复' "${EXEC_SCRIPT}" '检查只读沙箱' \
  >"${TEST_TMPDIR}/ten.stdout" 2>"${TEST_TMPDIR}/ten.stderr"
if grep -F -- ' --sandbox read-only' "${CALL_LOG}" >/dev/null; then
  pass '10：桩收到 --sandbox read-only'
else
  fail '10：桩未收到 --sandbox read-only'
fi

# 15a：缺任务参数。
STUB_CALL_LOG="${TEST_TMPDIR}/fifteen-a.argv" "${EXEC_SCRIPT}" \
  >"${TEST_TMPDIR}/fifteen-a.stdout" 2>"${TEST_TMPDIR}/fifteen-a.stderr"
assert_status 64 "$?" '15a：不给任务退出 64'

# 15b：未知选项。
STUB_CALL_LOG="${TEST_TMPDIR}/fifteen-b.argv" "${EXEC_SCRIPT}" --bogus \
  >"${TEST_TMPDIR}/fifteen-b.stdout" 2>"${TEST_TMPDIR}/fifteen-b.stderr"
assert_status 64 "$?" '15b：未知选项退出 64'

# 16：-- 后以 - 开头的文本是任务，不是选项。
CALL_LOG="${TEST_TMPDIR}/sixteen.argv"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='答复' "${EXEC_SCRIPT}" -- '-开头的任务' \
  >"${TEST_TMPDIR}/sixteen.stdout" 2>"${TEST_TMPDIR}/sixteen.stderr"
STATUS=$?
ARGV_LINE="$(tail -n 1 "${CALL_LOG}")"
eval "set -- ${ARGV_LINE#argv:}"
LAST_ARG=''
for ARG in ${@+"${@}"}; do
  LAST_ARG="${ARG}"
done
EXPECTED_TASK='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱是只读的：不要修改文件、不要提交、不要启动服务、不要做任务之外的网络访问。

-开头的任务'
if [ "${STATUS}" -eq 0 ] && [ "${LAST_ARG}" = "${EXPECTED_TASK}" ]; then
  pass '16：-- 后以 - 开头的任务正常执行'
else
  fail '16：-- 后以 - 开头的任务未正确传递'
fi

assert_status_and_stderr() {
  EXPECTED_STATUS="${1}"
  ACTUAL_STATUS="${2}"
  STDERR_FILE="${3}"
  PATTERN="${4}"
  NAME="${5}"

  if [ "${ACTUAL_STATUS}" -eq "${EXPECTED_STATUS}" ] && grep -F -- "${PATTERN}" "${STDERR_FILE}" >/dev/null; then
    assert_status "${EXPECTED_STATUS}" "${ACTUAL_STATUS}" "${NAME}"
  else
    fail "${NAME}（退出 ${ACTUAL_STATUS}；stderr 未含 ${PATTERN}）"
  fi
}

assert_nonzero_and_stderr() {
  ACTUAL_STATUS="${1}"
  STDERR_FILE="${2}"
  PATTERN="${3}"
  NAME="${4}"

  if [ "${ACTUAL_STATUS}" -ne 0 ] && grep -F -- "${PATTERN}" "${STDERR_FILE}" >/dev/null; then
    pass "${NAME}"
  else
    fail "${NAME}（退出 ${ACTUAL_STATUS}；stderr 未含 ${PATTERN}）"
  fi
}

# 3：codex 在 PATH 但 --version 无法运行时，给出可执行的安装提示。
CALL_LOG="${TEST_TMPDIR}/three.argv"
STDERR_FILE="${TEST_TMPDIR}/three.stderr"
STUB_CALL_LOG="${CALL_LOG}" STUB_VERSION_EXIT=1 STUB_ANSWER='答复' "${EXEC_SCRIPT}" '检查版本失败' \
  >"${TEST_TMPDIR}/three.stdout" 2>"${STDERR_FILE}"
assert_status_and_stderr 127 "$?" "${STDERR_FILE}" 'npm install -g @openai/codex@latest' '3：--version 失败退出 127 并提示安装命令'

# 4：PATH 中没有 codex 时，wrapper 本身仍能由绝对路径启动并报错。
STDERR_FILE="${TEST_TMPDIR}/four.stderr"
PATH='/usr/bin:/bin' STUB_CALL_LOG="${TEST_TMPDIR}/four.argv" "${EXEC_SCRIPT}" '检查缺失命令' \
  >"${TEST_TMPDIR}/four.stdout" 2>"${STDERR_FILE}"
assert_status_and_stderr 127 "$?" "${STDERR_FILE}" '找不到 codex' '4：codex 不在 PATH 时退出 127 并说明原因'

# 5：exec 失败时，stderr 必须回显过程日志尾部与完整日志路径。
CALL_LOG="${TEST_TMPDIR}/five.argv"
STDERR_FILE="${TEST_TMPDIR}/five.stderr"
STUB_CALL_LOG="${CALL_LOG}" STUB_VERSION_EXIT=0 STUB_EXIT=3 STUB_STDOUT_TEXT='可识别的过程文本' \
  "${EXEC_SCRIPT}" '检查 exec 失败' >"${TEST_TMPDIR}/five.stdout" 2>"${STDERR_FILE}"
STATUS=$?
if [ "${STATUS}" -eq 3 ] && grep -F -- '可识别的过程文本' "${STDERR_FILE}" >/dev/null && grep -F -- '过程日志：' "${STDERR_FILE}" >/dev/null; then
  assert_status 3 "${STATUS}" '5：exec 失败退出原码并回显日志尾部和路径'
else
  fail "5：exec 失败退出 ${STATUS}，或 stderr 缺少过程文本/日志路径"
fi

# 6：exec 成功但答复为空仍必须失败，并说明产出为空。
CALL_LOG="${TEST_TMPDIR}/six.argv"
STDERR_FILE="${TEST_TMPDIR}/six.stderr"
STUB_CALL_LOG="${CALL_LOG}" STUB_VERSION_EXIT=0 STUB_EXIT=0 STUB_ANSWER='' \
  "${EXEC_SCRIPT}" '检查空答复' >"${TEST_TMPDIR}/six.stdout" 2>"${STDERR_FILE}"
assert_nonzero_and_stderr "$?" "${STDERR_FILE}" '产出为空' '6：空答复退出非 0 并说明产出为空'

printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
