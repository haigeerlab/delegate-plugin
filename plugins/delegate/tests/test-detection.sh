#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DETECT_SCRIPT="${SCRIPT_DIR}/../hooks/detect.sh"
TEST_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-detection-test.XXXXXX")"
trap 'rm -rf "${TEST_TMPDIR}"' EXIT
TEST_BIN="${TEST_TMPDIR}/bin"
AUTH_FILE="${TEST_TMPDIR}/auth.json"
mkdir "${TEST_BIN}"
ln -s "${SCRIPT_DIR}/stub-codex" "${TEST_BIN}/codex"
printf '{}\n' > "${AUTH_FILE}"

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
  PATH="${1}" CODEX_AUTH_FILE="${2}" STUB_CALL_LOG="${3}" STUB_VERSION_EXIT="${4}" \
    "${5}" --print 2>"${TEST_TMPDIR}/stderr"
}

# 10：没有 codex 时 hook 必须静默成功，且 stdout 完全为空。
PATH='/usr/bin:/bin' CODEX_AUTH_FILE="${AUTH_FILE}" "${DETECT_SCRIPT}" \
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
CODEX_AUTH_FILE="${AUTH_FILE}" "${DETECT_SCRIPT}" --session-start \
  >"${TEST_TMPDIR}/ten-b.stdout" 2>"${TEST_TMPDIR}/ten-b.stderr"
STATUS=$?
OUTPUT="$(/bin/cat "${TEST_TMPDIR}/ten-b.stdout")"
if [ "${STATUS}" -eq 0 ] && [ -z "${OUTPUT}" ]; then
  pass '10b：SessionStart 模式即使可用也零输出'
else
  fail "10b：SessionStart 模式退出 ${STATUS}，stdout：${OUTPUT}"
fi

printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
