#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DETECT_SCRIPT="${SCRIPT_DIR}/../hooks/detect.sh"
TEST_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-detection-test.XXXXXX")"
trap 'chmod -R u+rwx "${TEST_TMPDIR}" 2>/dev/null; rm -rf "${TEST_TMPDIR}"' EXIT
TEST_BIN="${TEST_TMPDIR}/bin"
AUTH_FILE="${TEST_TMPDIR}/auth.json"
mkdir "${TEST_BIN}"
ln -s "${SCRIPT_DIR}/stub-codex" "${TEST_BIN}/codex"
printf '{}\n' > "${AUTH_FILE}"

# 兜底：套件一律在自己的 TMPDIR 下跑。现有断言都显式设了 TMPDIR，
# 但少设一次就会往真实 ${TMPDIR}/delegate/ 写缓存 ——
# test-channel.sh 就是这样积到 1310 个文件 / 9.3MB 才被发现的。
TMPDIR="${TEST_TMPDIR}"
export TMPDIR

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

assert_print_contains() {
  OUTPUT="${1}"
  PATTERN="${2}"
  NAME="${3}"

  case "${OUTPUT}" in
    *"${PATTERN}"*) pass "${NAME}" ;;
    *) fail "${NAME}（输出：${OUTPUT}）" ;;
  esac
}

run_print() {
  RUN_TMPDIR="${TEST_TMPDIR}/cache-${3##*/}"
  mkdir -p "${RUN_TMPDIR}"
  PATH="${1}" TMPDIR="${RUN_TMPDIR}" CODEX_AUTH_FILE="${2}" STUB_CALL_LOG="${3}" STUB_VERSION_EXIT="${4}" \
    "${5}" --print 2>"${TEST_TMPDIR}/stderr"
}

# 10：没有 codex 时 hook 必须静默成功，且 stdout 完全为空。
PATH='/usr/bin:/bin' TMPDIR="${TEST_TMPDIR}/ten-tmp" CODEX_AUTH_FILE="${AUTH_FILE}" "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/ten.stdout" 2>"${TEST_TMPDIR}/ten.stderr"
STATUS=$?
OUTPUT="$(/bin/cat "${TEST_TMPDIR}/ten.stdout")"
if [ "${STATUS}" -eq 0 ] && [ -z "${OUTPUT}" ]; then
  pass '10：无 codex 时 hook 退出 0 且 stdout 为空'
else
  fail "10：无 codex 时 hook 退出 ${STATUS}，stdout：${OUTPUT}"
fi

# 1：三级全过。
OUTPUT="$(run_print "${TEST_BIN}:/usr/bin:/bin" "${AUTH_FILE}" "${TEST_TMPDIR}/one.argv" 0 "${DETECT_SCRIPT}")"
if [ "${OUTPUT}" = '可用' ]; then
  pass '1：三级全过时显示可用'
else
  fail "1：三级全过时输出：${OUTPUT}"
fi

# 2：wrapper 不可执行。
COPY_ROOT="${TEST_TMPDIR}/copy"
mkdir -p "${COPY_ROOT}/hooks" "${COPY_ROOT}/scripts"
/bin/cp "${DETECT_SCRIPT}" "${COPY_ROOT}/hooks/detect.sh"
/bin/cp "${SCRIPT_DIR}/../scripts/codex-exec.sh" "${COPY_ROOT}/scripts/codex-exec.sh"
chmod +x "${COPY_ROOT}/hooks/detect.sh"
chmod -x "${COPY_ROOT}/scripts/codex-exec.sh"
OUTPUT="$(run_print "${TEST_BIN}:/usr/bin:/bin" "${AUTH_FILE}" "${TEST_TMPDIR}/two.argv" 0 "${COPY_ROOT}/hooks/detect.sh")"
assert_print_contains "${OUTPUT}" 'wrapper' '2：wrapper 不可执行时原因指向 wrapper'

# 3：codex 不在 PATH。
OUTPUT="$(run_print '/usr/bin:/bin' "${AUTH_FILE}" "${TEST_TMPDIR}/three.argv" 0 "${DETECT_SCRIPT}")"
assert_print_contains "${OUTPUT}" 'codex 不在 PATH' '3：codex 不在 PATH 时给出对应原因'

# 4：command -v 成功但 --version 失败。
OUTPUT="$(run_print "${TEST_BIN}:/usr/bin:/bin" "${AUTH_FILE}" "${TEST_TMPDIR}/four.argv" 1 "${DETECT_SCRIPT}")"
assert_print_contains "${OUTPUT}" 'npm install -g @openai/codex@latest' '4：codex 装坏时给出安装命令'

# 5：认证文件不存在。
OUTPUT="$(run_print "${TEST_BIN}:/usr/bin:/bin" "${TEST_TMPDIR}/missing-auth.json" "${TEST_TMPDIR}/five.argv" 0 "${DETECT_SCRIPT}")"
assert_print_contains "${OUTPUT}" '登录' '5：认证文件不存在时提示登录'

# 6：认证文件为空。
EMPTY_AUTH_FILE="${TEST_TMPDIR}/empty-auth.json"
: > "${EMPTY_AUTH_FILE}"
OUTPUT="$(run_print "${TEST_BIN}:/usr/bin:/bin" "${EMPTY_AUTH_FILE}" "${TEST_TMPDIR}/six.argv" 0 "${DETECT_SCRIPT}")"
assert_print_contains "${OUTPUT}" '登录' '6：认证文件为空时提示登录'

# 10b：SessionStart 只探测、不输出 —— 即使后端可用也必须零输出。
# 两个事件共用这个脚本，而 hookEventName 必须与实际事件一致；
# SessionStart 的输出契约没有可核对的依据，所以那一路干脆不输出。
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${TEST_TMPDIR}/ten-b-tmp" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/ten-b.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" --session-start \
  >"${TEST_TMPDIR}/ten-b.stdout" 2>"${TEST_TMPDIR}/ten-b.stderr"
STATUS=$?
OUTPUT="$(/bin/cat "${TEST_TMPDIR}/ten-b.stdout")"
if [ "${STATUS}" -eq 0 ] && [ -z "${OUTPUT}" ]; then
  pass '10b：SessionStart 模式即使可用也零输出'
else
  fail "10b：SessionStart 模式退出 ${STATUS}，stdout：${OUTPUT}"
fi

# 7：SessionStart 写好新鲜缓存后，默认模式不得再调用 codex。
CACHE_TMPDIR="${TEST_TMPDIR}/cache-fresh"
mkdir -p "${CACHE_TMPDIR}"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${CACHE_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/seven-warm.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" --session-start \
  >"${TEST_TMPDIR}/seven-warm.stdout" 2>"${TEST_TMPDIR}/seven-warm.stderr"
: > "${TEST_TMPDIR}/seven.argv"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${CACHE_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/seven.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/seven.stdout" 2>"${TEST_TMPDIR}/seven.stderr"
if [ ! -s "${TEST_TMPDIR}/seven.argv" ]; then
  pass '7：新鲜缓存命中时不再调用 codex'
else
  fail '7：新鲜缓存命中时仍调用了 codex'
fi

# 8：超过 8 小时的缓存必须重探。
if [ -f "${CACHE_TMPDIR}/delegate/detection.json" ]; then
  python3 -c 'import json, sys, time; p = sys.argv[1]; d = json.load(open(p)); d["checkedAt"] = int(time.time()) - 9 * 60 * 60; open(p, "w").write(json.dumps(d))' \
    "${CACHE_TMPDIR}/delegate/detection.json"
  : > "${TEST_TMPDIR}/eight.argv"
  PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${CACHE_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
    STUB_CALL_LOG="${TEST_TMPDIR}/eight.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
    >"${TEST_TMPDIR}/eight.stdout" 2>"${TEST_TMPDIR}/eight.stderr"
  if [ -s "${TEST_TMPDIR}/eight.argv" ]; then
    pass '8：过期缓存会重探 codex'
  else
    fail '8：过期缓存没有重探 codex'
  fi
else
  fail '8：SessionStart 没有写入缓存'
fi

# 9：非法 JSON 等同于没有缓存，必须静默重探。
printf 'not json\n' > "${CACHE_TMPDIR}/delegate/detection.json"
: > "${TEST_TMPDIR}/nine.argv"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${CACHE_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/nine.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/nine.stdout" 2>"${TEST_TMPDIR}/nine.stderr"
STATUS=$?
if [ "${STATUS}" -eq 0 ] && [ -s "${TEST_TMPDIR}/nine.argv" ]; then
  pass '9：非法缓存 JSON 不崩且会重探'
else
  fail "9：非法缓存 JSON 时状态 ${STATUS}，未重探或崩溃"
fi

# 11：可用、不可用、缓存损坏三种 hook 输出都只能为空或合法 JSON。
HOOK_VALID_TMPDIR="${TEST_TMPDIR}/hook-valid"
HOOK_UNAVAILABLE_TMPDIR="${TEST_TMPDIR}/hook-unavailable"
HOOK_BROKEN_TMPDIR="${TEST_TMPDIR}/hook-broken"
mkdir -p "${HOOK_VALID_TMPDIR}" "${HOOK_UNAVAILABLE_TMPDIR}" "${HOOK_BROKEN_TMPDIR}/delegate"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${HOOK_VALID_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/eleven-valid.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/eleven-valid.stdout" 2>"${TEST_TMPDIR}/eleven-valid.stderr"
PATH='/usr/bin:/bin' TMPDIR="${HOOK_UNAVAILABLE_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/eleven-unavailable.stdout" 2>"${TEST_TMPDIR}/eleven-unavailable.stderr"
printf 'not json\n' > "${HOOK_BROKEN_TMPDIR}/delegate/detection.json"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${HOOK_BROKEN_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/eleven-broken.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/eleven-broken.stdout" 2>"${TEST_TMPDIR}/eleven-broken.stderr"
if { [ ! -s "${TEST_TMPDIR}/eleven-valid.stdout" ] || python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/eleven-valid.stdout" 2>/dev/null; } \
  && { [ ! -s "${TEST_TMPDIR}/eleven-unavailable.stdout" ] || python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/eleven-unavailable.stdout" 2>/dev/null; } \
  && { [ ! -s "${TEST_TMPDIR}/eleven-broken.stdout" ] || python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/eleven-broken.stdout" 2>/dev/null; }; then
  pass '11：各场景 hook stdout 均为空或合法 JSON'
else
  fail '11：某个场景的 hook stdout 不是合法 JSON'
fi

# 7b：--session-start 一律实探，不吃缓存 —— 它的职责就是预热。
# （没有这条时，把 --session-start 改成先读缓存的变异会存活：装好 Codex 之后
#  即使重启 Claude Code 也要等缓存过期才被发现。）
SESSION_TMPDIR="${TEST_TMPDIR}/session-warm"
mkdir -p "${SESSION_TMPDIR}"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${SESSION_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/seven-b-warm.argv" "${DETECT_SCRIPT}" --session-start \
  >/dev/null 2>&1
: > "${TEST_TMPDIR}/seven-b.argv"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${SESSION_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/seven-b.argv" "${DETECT_SCRIPT}" --session-start \
  >/dev/null 2>&1
if [ -s "${TEST_TMPDIR}/seven-b.argv" ]; then
  pass '7b：--session-start 即使缓存新鲜也实探'
else
  fail '7b：--session-start 吃了缓存，没有实探'
fi

# 12a：缓存目录存在但不可写（写文件失败）→ 静默退 0，维持 JSON 契约。
FAIL_TMPDIR="${TEST_TMPDIR}/cache-unwritable"
mkdir -p "${FAIL_TMPDIR}/delegate"
chmod 000 "${FAIL_TMPDIR}/delegate"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${FAIL_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/twelve.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/twelve.stdout" 2>"${TEST_TMPDIR}/twelve.stderr"
STATUS=$?
chmod 700 "${FAIL_TMPDIR}/delegate"
if [ "${STATUS}" -eq 0 ] && { [ ! -s "${TEST_TMPDIR}/twelve.stdout" ] || python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/twelve.stdout" 2>/dev/null; }; then
  pass '12a：缓存写失败时仍退出 0 且 stdout 合法'
else
  fail "12a：缓存写失败时状态 ${STATUS} 或 stdout 非法"
fi

# 12b：缓存目录**建都建不出来**（父目录不可写）→ 同样静默退 0。
# 原来只做了 12a，而 `mkdir -p` 对已存在目录是成功的 ——
# mkdir 失败这条路径从没被走到，把 `|| return 1` 改成 `|| exit 1` 的变异存活了。
NOMKDIR_TMPDIR="${TEST_TMPDIR}/cache-nomkdir"
mkdir -p "${NOMKDIR_TMPDIR}"
chmod 500 "${NOMKDIR_TMPDIR}"
PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${NOMKDIR_TMPDIR}" CODEX_AUTH_FILE="${AUTH_FILE}" \
  STUB_CALL_LOG="${TEST_TMPDIR}/twelve-b.argv" STUB_VERSION_EXIT=0 "${DETECT_SCRIPT}" \
  >"${TEST_TMPDIR}/twelve-b.stdout" 2>"${TEST_TMPDIR}/twelve-b.stderr"
STATUS=$?
chmod 700 "${NOMKDIR_TMPDIR}"
if [ "${STATUS}" -eq 0 ] && { [ ! -s "${TEST_TMPDIR}/twelve-b.stdout" ] || python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/twelve-b.stdout" 2>/dev/null; }; then
  pass '12b：缓存目录建不出来时仍退出 0 且 stdout 合法'
else
  fail "12b：缓存目录建不出来时状态 ${STATUS} 或 stdout 非法"
fi

# 13：流程编排规则会让非交互委托停在确认请求，doctor 必须报告风险和固定修法。
DOCTOR_SCRIPT="${SCRIPT_DIR}/../hooks/doctor.sh"
RISK_AGENTS_FILE="${TEST_TMPDIR}/risk-AGENTS.md"
printf '不要直接开始改代码\n' > "${RISK_AGENTS_FILE}"
OUTPUT="$(CODEX_AGENTS_FILE="${RISK_AGENTS_FILE}" "${DOCTOR_SCRIPT}" 2>"${TEST_TMPDIR}/thirteen.stderr")"
case "${OUTPUT}" in
  *风险*仅适用于交互式会话*)
    pass '13：流程编排规则报告风险并给出非交互修法'
    ;;
  *)
    fail "13：没有报告风险或固定修法（输出：${OUTPUT}）"
    ;;
esac

# 13b（**反向**）：有流程编排规则、但已经声明了非交互豁免 → 不许报风险。
# 断言 14 只覆盖「完全没有规则」，覆盖不到「有规则但已修好」——
# 2026-08-29 在作者本人已经修好的 ~/.codex/AGENTS.md 上实测到了这个假警报，
# 而当时 18 条断言全绿。假警报比不报危害大。
EXEMPTED_AGENTS_FILE="${TEST_TMPDIR}/exempted-AGENTS.md"
printf '本节仅适用于交互式会话；非交互调用（codex exec）时整节跳过。\n复杂任务开场时，先按下面顺序启动，不要直接开始改代码：\n' > "${EXEMPTED_AGENTS_FILE}"
OUTPUT="$(CODEX_AGENTS_FILE="${EXEMPTED_AGENTS_FILE}" "${DOCTOR_SCRIPT}" 2>"${TEST_TMPDIR}/thirteen-b.stderr")"
STATUS=$?
if [ "${STATUS}" -ne 0 ]; then
  fail "13b：已豁免的 AGENTS.md 时 doctor 退出 ${STATUS}"
else
  case "${OUTPUT}" in
    *风险*) fail "13b：已声明非交互豁免却仍报风险（假警报）" ;;
    *已声明非交互豁免*) pass '13b：已豁免的流程编排规则不报风险' ;;
    *) fail "13b：既没报风险也没识别出豁免（输出：${OUTPUT}）" ;;
  esac
fi

# 14：干净的 AGENTS.md 不得产生假警报。
CLEAN_AGENTS_FILE="${TEST_TMPDIR}/clean-AGENTS.md"
printf '用中文回答\n' > "${CLEAN_AGENTS_FILE}"
OUTPUT="$(CODEX_AGENTS_FILE="${CLEAN_AGENTS_FILE}" "${DOCTOR_SCRIPT}" 2>"${TEST_TMPDIR}/fourteen.stderr")"
STATUS=$?
if [ "${STATUS}" -ne 0 ]; then
  fail "14：干净 AGENTS.md 时 doctor 退出 ${STATUS}"
else
  case "${OUTPUT}" in
    *风险*) fail "14：干净 AGENTS.md 产生风险报告（输出：${OUTPUT}）" ;;
    *) pass '14：干净 AGENTS.md 不报告风险' ;;
  esac
fi

# 15：没有 AGENTS.md 不是问题 —— 既要退 0，**也不许报成风险**。
# 只验退出码是不够的：doctor 永远退 0，把「没有 AGENTS.md」记成问题时
# 退出码一模一样（实测：那个变异存活过）。
MISSING_AGENTS_FILE="${TEST_TMPDIR}/no-such-AGENTS.md"
rm -f "${MISSING_AGENTS_FILE}"
OUTPUT="$(CODEX_AGENTS_FILE="${MISSING_AGENTS_FILE}" "${DOCTOR_SCRIPT}" 2>"${TEST_TMPDIR}/fifteen.stderr")"
STATUS=$?
if [ "${STATUS}" -ne 0 ]; then
  fail "15：AGENTS.md 不存在时 doctor 退出 ${STATUS}"
else
  case "${OUTPUT}" in
    *风险*)     fail "15：AGENTS.md 不存在被报成了风险（假警报）" ;;
    *未发现问题*) pass '15：AGENTS.md 不存在时退出 0 且不报问题' ;;
    *)          fail "15：小结没说通过（输出：${OUTPUT}）" ;;
  esac
fi

printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
