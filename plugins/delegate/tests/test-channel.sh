#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXEC_SCRIPT="${SCRIPT_DIR}/../scripts/codex-exec.sh"
ORIGINAL_PATH="${PATH}"
LIVE_MODE=0

if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "${1}" != '--live' ]; }; then
  printf '用法：%s [--live]\n' "${0}" >&2
  exit 64
fi

if [ "$#" -eq 1 ]; then
  LIVE_MODE=1
fi

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

# 桩用 printf %q 记 argv，而 bash 3.2 的 %q 会把 UTF-8 打成 $'\346\262\231' 这种
# 八进制转义 —— **在 argv 日志里直接 grep 中文永远匹配不上**，写成
# `! grep 中文` 就是一条恒真的空断言（2026-08-29 实测：一个本该被抓的变异存活）。
# 要查参数内容一律走这里：eval 还原回原始字节，再用 case 比对。
LAST_CALL_ARGS=()
load_last_call_args() {
  LOAD_LINE="$(tail -n 1 "${1}")"
  eval "set -- ${LOAD_LINE#argv:}"
  LAST_CALL_ARGS=(${@+"${@}"})
}

last_arg_of() {
  load_last_call_args "${1}"
  LAST_ARG_VALUE=''
  for LOAD_ARG in ${LAST_CALL_ARGS[@]+"${LAST_CALL_ARGS[@]}"}; do
    LAST_ARG_VALUE="${LOAD_ARG}"
  done
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

# 8：模型与推理档都必须原样透传给 exec。
CALL_LOG="${TEST_TMPDIR}/eight.argv"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='答复' \
  "${EXEC_SCRIPT}" --model gpt-x --effort high '检查模型与推理档透传' \
  >"${TEST_TMPDIR}/eight.stdout" 2>"${TEST_TMPDIR}/eight.stderr"
STATUS=$?
EXEC_LINE="$(grep -F -- ' exec ' "${CALL_LOG}")"
if [ "${STATUS}" -eq 0 ] && printf '%s\n' "${EXEC_LINE}" | grep -F -- ' -m gpt-x' >/dev/null && printf '%s\n' "${EXEC_LINE}" | grep -F -- 'model_reasoning_effort=\"high\"' >/dev/null; then
  pass '8：--model 与 --effort 同时透传给 exec'
else
  fail '8：--model 或 --effort 未正确透传给 exec'
fi

# 9：未指定模型与推理档时，exec 不应显式覆盖配置默认值。
CALL_LOG="${TEST_TMPDIR}/nine.argv"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='答复' "${EXEC_SCRIPT}" '检查配置默认值' \
  >"${TEST_TMPDIR}/nine.stdout" 2>"${TEST_TMPDIR}/nine.stderr"
STATUS=$?
EXEC_LINE="$(grep -F -- ' exec ' "${CALL_LOG}")"
if [ "${STATUS}" -eq 0 ] && ! printf '%s\n' "${EXEC_LINE}" | grep -F -- ' -m ' >/dev/null && ! printf '%s\n' "${EXEC_LINE}" | grep -F -- 'model_reasoning_effort=' >/dev/null; then
  pass '9：未传模型与推理档时不覆盖配置默认值'
else
  fail '9：未传模型与推理档时仍覆盖了配置默认值'
fi

# 7：无效模型的 exec 失败必须原样失败，且不得删除 -m 后重试。
CALL_LOG="${TEST_TMPDIR}/seven.argv"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='答复' STUB_EXIT=3 \
  "${EXEC_SCRIPT}" --model invalid-slug '模拟无效模型' \
  >"${TEST_TMPDIR}/seven.stdout" 2>"${TEST_TMPDIR}/seven.stderr"
STATUS=$?
EXEC_CALLS="$(grep -F -- ' exec ' "${CALL_LOG}" | wc -l | tr -d ' ')"
if [ "${STATUS}" -ne 0 ] && [ "${EXEC_CALLS}" -eq 1 ]; then
  pass '7：无效模型失败时不删除 -m 重试'
else
  fail "7：无效模型退出 ${STATUS}，exec 调用 ${EXEC_CALLS} 次"
fi

# 9b：--model 缺少值必须作为用法错误退出。
STUB_CALL_LOG="${TEST_TMPDIR}/nine-b.argv" "${EXEC_SCRIPT}" --model \
  >"${TEST_TMPDIR}/nine-b.stdout" 2>"${TEST_TMPDIR}/nine-b.stderr"
assert_status 64 "$?" '9b：--model 缺少值退出 64'

# 11：--write 必须显式切换到 workspace-write，且写模式 preamble 不得声称只读。
CALL_LOG="${TEST_TMPDIR}/eleven.argv"
STUB_CALL_LOG="${CALL_LOG}" STUB_ANSWER='答复' "${EXEC_SCRIPT}" --write '检查写沙箱' \
  >"${TEST_TMPDIR}/eleven.stdout" 2>"${TEST_TMPDIR}/eleven.stderr"
STATUS=$?
last_arg_of "${CALL_LOG}"
case "${LAST_ARG_VALUE}" in
  *沙箱是只读的*) READONLY_CLAIMED=1 ;;
  *)              READONLY_CLAIMED=0 ;;
esac
if [ "${STATUS}" -eq 0 ] && grep -F -- ' --sandbox workspace-write' "${CALL_LOG}" >/dev/null && [ "${READONLY_CLAIMED}" -eq 0 ]; then
  pass '11：--write 使用 workspace-write，且任务不含只读 preamble'
else
  fail '11：--write 未使用 workspace-write，或任务仍含只读 preamble'
fi

# 12：git 仓库里的写调用必须输出可核验的基线、status 与 diff 段。
GIT_REPO="${TEST_TMPDIR}/twelve-repo"
mkdir "${GIT_REPO}"
(
  cd "${GIT_REPO}" || exit 1
  git init >/dev/null 2>&1
  printf '初始内容\n' > tracked.txt
  git add tracked.txt
  git -c user.email=t@t -c user.name=t commit -m init >/dev/null 2>&1
)
BASELINE_HEAD="$(cd "${GIT_REPO}" && git rev-parse HEAD)"
(
  cd "${GIT_REPO}" || exit 1
  STUB_CALL_LOG="${TEST_TMPDIR}/twelve.argv" STUB_ANSWER='答复' "${EXEC_SCRIPT}" --write '检查 git 验收块'
) >"${TEST_TMPDIR}/twelve.stdout" 2>"${TEST_TMPDIR}/twelve.stderr"
STATUS=$?
if [ "${STATUS}" -eq 0 ] && grep -F -- "${BASELINE_HEAD}" "${TEST_TMPDIR}/twelve.stdout" >/dev/null && grep -F -- 'git status --short' "${TEST_TMPDIR}/twelve.stdout" >/dev/null && grep -F -- 'git diff --stat' "${TEST_TMPDIR}/twelve.stdout" >/dev/null; then
  pass '12：git 仓库输出基线 HEAD、status 与 diff 验收段'
else
  fail '12：git 仓库缺少基线 HEAD、status 或 diff 验收段'
fi

# 13：非 git 目录必须说明无法验收，且不得伪造基线 HEAD。
NON_GIT_DIR="${TEST_TMPDIR}/thirteen-non-git"
mkdir "${NON_GIT_DIR}"
(
  cd "${NON_GIT_DIR}" || exit 1
  STUB_CALL_LOG="${TEST_TMPDIR}/thirteen.argv" STUB_ANSWER='答复' "${EXEC_SCRIPT}" --write '检查非 git 说明'
) >"${TEST_TMPDIR}/thirteen.stdout" 2>"${TEST_TMPDIR}/thirteen.stderr"
STATUS=$?
if [ "${STATUS}" -eq 0 ] && grep -F -- '不是 git 仓库' "${TEST_TMPDIR}/thirteen.stdout" >/dev/null && ! grep -F -- '基线 HEAD' "${TEST_TMPDIR}/thirteen.stdout" >/dev/null; then
  pass '13：非 git 目录说明拿不到 diff，且不伪造验收块'
else
  fail '13：非 git 目录缺少说明，或伪造了验收块'
fi

# 14：验收块必须报告调用前已有的未提交变更数。
GIT_REPO="${TEST_TMPDIR}/fourteen-repo"
mkdir "${GIT_REPO}"
(
  cd "${GIT_REPO}" || exit 1
  git init >/dev/null 2>&1
  printf '初始内容\n' > tracked.txt
  git add tracked.txt
  git -c user.email=t@t -c user.name=t commit -m init >/dev/null 2>&1
  printf '已修改\n' > tracked.txt
  printf '未跟踪\n' > untracked.txt
  STUB_CALL_LOG="${TEST_TMPDIR}/fourteen.argv" STUB_ANSWER='答复' "${EXEC_SCRIPT}" --write '检查未提交变更计数'
) >"${TEST_TMPDIR}/fourteen.stdout" 2>"${TEST_TMPDIR}/fourteen.stderr"
STATUS=$?
if [ "${STATUS}" -eq 0 ] && grep -F -- '跑之前工作区已有 2 个未提交变更' "${TEST_TMPDIR}/fourteen.stdout" >/dev/null; then
  pass '14：写模式验收块报告跑前 2 个未提交变更'
else
  fail '14：写模式验收块未正确报告跑前未提交变更数'
fi

if [ "${LIVE_MODE}" -eq 0 ]; then
  printf 'LIVE：已跳过（跳过不代表通过）；使用 --live 才会调用真实 codex。\n'
else
  LIVE_AUTH_FILE="${CODEX_AUTH_FILE:-${HOME}/.codex/auth.json}"
  if [ ! -s "${LIVE_AUTH_FILE}" ]; then
    printf 'LIVE：没跑起来（不是不通过）：认证文件不存在或为空：%s\n' "${LIVE_AUTH_FILE}" >&2
    exit 2
  fi

  if ! PATH="${ORIGINAL_PATH}" codex --version >/dev/null 2>&1; then
    printf 'LIVE：没跑起来（不是不通过）：原始 PATH 中的 codex --version 无法运行。\n' >&2
    exit 2
  fi

  LIVE_TMPDIR="${TEST_TMPDIR}/live-tmp"
  LIVE_RESULT="${TEST_TMPDIR}/live.stdout"
  mkdir "${LIVE_TMPDIR}"
  TMPDIR="${LIVE_TMPDIR}" PATH="${ORIGINAL_PATH}" "${EXEC_SCRIPT}" '只回复“好”。不要执行其他操作。' \
    >"${LIVE_RESULT}" 2>"${TEST_TMPDIR}/live.stderr"
  LIVE_STATUS=$?
  LIVE_LOG=''
  LIVE_ANSWER=''
  for LIVE_CANDIDATE in "${LIVE_TMPDIR}/delegate/"*.log; do
    if [ -f "${LIVE_CANDIDATE}" ]; then
      LIVE_LOG="${LIVE_CANDIDATE}"
    fi
  done
  for LIVE_CANDIDATE in "${LIVE_TMPDIR}/delegate/"*.answer; do
    if [ -f "${LIVE_CANDIDATE}" ]; then
      LIVE_ANSWER="${LIVE_CANDIDATE}"
    fi
  done

  if [ "${LIVE_STATUS}" -eq 0 ] && [ -s "${LIVE_ANSWER}" ]; then
    pass 'LIVE：真实只读委托答复非空'
  else
    fail "LIVE：真实只读委托没有非空答复（退出 ${LIVE_STATUS}）"
  fi

  if [ -n "${LIVE_LOG}" ] && [ -s "${LIVE_ANSWER}" ]; then
    LIVE_LOG_BYTES="$(wc -c < "${LIVE_LOG}" | tr -d ' ')"
    LIVE_ANSWER_BYTES="$(wc -c < "${LIVE_ANSWER}" | tr -d ' ')"
    if [ "${LIVE_LOG_BYTES}" -ge $((LIVE_ANSWER_BYTES * 40)) ]; then
      pass 'LIVE：过程日志字节数至少为最终答复的 40 倍'
    else
      fail "LIVE：过程日志 ${LIVE_LOG_BYTES} 字节，不足答复 ${LIVE_ANSWER_BYTES} 字节的 40 倍"
    fi
  else
    fail 'LIVE：找不到过程日志或最终答复，无法检查 40 倍体量比'
  fi
fi

printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
