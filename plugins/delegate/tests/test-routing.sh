#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROUTE_SCRIPT="${SCRIPT_DIR}/../hooks/route.sh"
SKILL_FILE="${SCRIPT_DIR}/../skills/delegate-routing/SKILL.md"
TEST_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/delegate-routing-test.XXXXXX")"
trap 'chmod -R u+rwx "${TEST_TMPDIR}" 2>/dev/null; rm -rf "${TEST_TMPDIR}"' EXIT
TEST_BIN="${TEST_TMPDIR}/bin"
mkdir "${TEST_BIN}"
ln -s "${SCRIPT_DIR}/stub-codex" "${TEST_BIN}/codex"

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

write_cache() {
  CACHE_TMPDIR="${1}"
  AVAILABLE="${2}"
  mkdir -p "${CACHE_TMPDIR}/delegate"
  python3 - "${CACHE_TMPDIR}/delegate/detection.json" "${AVAILABLE}" <<'PY'
import json
import sys
import time

with open(sys.argv[1], "w") as cache_file:
    json.dump({"available": sys.argv[2] == "true", "reason": "test", "checkedAt": int(time.time())}, cache_file)
    cache_file.write("\n")
PY
}

run_route() {
  RUN_TMPDIR="${1}"
  RUN_NAME="${2}"
  PATH="${TEST_BIN}:/usr/bin:/bin" TMPDIR="${RUN_TMPDIR}" STUB_CALL_LOG="${TEST_TMPDIR}/${RUN_NAME}.argv" \
    "${ROUTE_SCRIPT}" >"${TEST_TMPDIR}/${RUN_NAME}.stdout" 2>"${TEST_TMPDIR}/${RUN_NAME}.stderr"
  RUN_STATUS=$?
}

UNAVAILABLE_TMPDIR="${TEST_TMPDIR}/unavailable"
MISSING_TMPDIR="${TEST_TMPDIR}/missing"
AVAILABLE_TMPDIR="${TEST_TMPDIR}/available"
BROKEN_TMPDIR="${TEST_TMPDIR}/broken"
write_cache "${UNAVAILABLE_TMPDIR}" false
write_cache "${AVAILABLE_TMPDIR}" true
mkdir -p "${BROKEN_TMPDIR}/delegate"
printf 'not json\n' > "${BROKEN_TMPDIR}/delegate/detection.json"

# R1：不可用缓存绝不注入。
run_route "${UNAVAILABLE_TMPDIR}" r1
if [ "${RUN_STATUS}" -eq 0 ] && [ ! -s "${TEST_TMPDIR}/r1.stdout" ]; then
  pass 'R1：不可用缓存时 route.sh 零输出且退出 0'
else
  fail 'R1：不可用缓存时 route.sh 没有零输出或没有退出 0'
fi

# R2：缺缓存时不猜。
run_route "${MISSING_TMPDIR}" r2
if [ "${RUN_STATUS}" -eq 0 ] && [ ! -s "${TEST_TMPDIR}/r2.stdout" ]; then
  pass 'R2：缓存缺失时 route.sh 零输出且退出 0'
else
  fail 'R2：缓存缺失时 route.sh 没有零输出或没有退出 0'
fi

# R3：可用的新鲜缓存只注入一行合法 JSON，且绝不触发探测桩。
: > "${TEST_TMPDIR}/r3.argv"
run_route "${AVAILABLE_TMPDIR}" r3
if [ "${RUN_STATUS}" -eq 0 ] && [ "$(wc -l < "${TEST_TMPDIR}/r3.stdout" | tr -d ' ')" -eq 1 ] \
  && python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/r3.stdout" 2>/dev/null \
  && [ ! -s "${TEST_TMPDIR}/r3.argv" ]; then
  pass 'R3：可用新鲜缓存注入一行合法 JSON，且不重新探测'
else
  fail 'R3：可用新鲜缓存没有合法单行 JSON，或调用了探测桩'
fi

# R4：指针保留确认闸门，不许有越闸措辞。
if python3 - "${TEST_TMPDIR}/r3.stdout" <<'PY'
import json
import sys

context = json.load(open(sys.argv[1]))["hookSpecificOutput"]["additionalContext"]
if "等用户确认" not in context or "我这就派" in context or "正在委托" in context:
    sys.exit(1)
PY
then
  pass 'R4：路由指针要求等用户确认，且不含越闸措辞'
else
  fail 'R4：路由指针缺少确认闸门或含越闸措辞'
fi

# R5：各缓存状态的 stdout 均为空或合法 JSON。
run_route "${BROKEN_TMPDIR}" r5-broken
R5_OK=1
for R5_NAME in r1 r2 r3 r5-broken; do
  if [ -s "${TEST_TMPDIR}/${R5_NAME}.stdout" ] \
    && ! python3 -c 'import json, sys; json.load(sys.stdin)' < "${TEST_TMPDIR}/${R5_NAME}.stdout" 2>/dev/null; then
    R5_OK=0
  fi
done
if [ "${R5_OK}" -eq 1 ]; then
  pass 'R5：不可用、缺失、损坏、可用缓存的 stdout 均为空或合法 JSON'
else
  fail 'R5：存在既非空又不是合法 JSON 的 stdout'
fi

# R2b：缓存**过期**（checkedAt 超过 8 小时）→ 同样零注入。不猜。
# 没有这条时，「忽略缓存过期」的变异会存活：Codex 早就装坏了，
# route.sh 却还在照着一份 3 天前的缓存提议委托。
STALE_CACHE_DIR="${TEST_TMPDIR}/stale/delegate"
mkdir -p "${STALE_CACHE_DIR}"
python3 -c 'import json,sys,time; json.dump({"available":True,"reason":"Codex 后端可用","checkedAt":int(time.time())-9*3600}, open(sys.argv[1],"w"))' \
  "${STALE_CACHE_DIR}/detection.json"
TMPDIR="${TEST_TMPDIR}/stale" "${ROUTE_SCRIPT}" \
  >"${TEST_TMPDIR}/r2b.stdout" 2>"${TEST_TMPDIR}/r2b.stderr"
STATUS=$?
if [ "${STATUS}" -eq 0 ] && [ ! -s "${TEST_TMPDIR}/r2b.stdout" ]; then
  pass 'R2b：过期缓存时零注入'
else
  fail "R2b：过期缓存仍然注入了（退出 ${STATUS}）"
fi

# R6：损坏缓存只是静默零输出，绝不重新探测或报错。
if [ "${RUN_STATUS}" -eq 0 ] && [ ! -s "${TEST_TMPDIR}/r5-broken.stdout" ] \
  && [ ! -s "${TEST_TMPDIR}/r5-broken.stderr" ]; then
  pass 'R6：非法缓存时退出 0、零输出、零噪音'
else
  fail 'R6：非法缓存时没有静默退出'
fi

# R7：skill 覆盖分流表的六类活。
SKILL_TEXT="$(/bin/cat "${SKILL_FILE}" 2>/dev/null || :)"
R7_OK=1
for R7_KEYWORD in '代码审查' '跨文件摸结构' '复现 bug' '单个 task 的实现' '批量机械改动' '需求澄清'; do
  case "${SKILL_TEXT}" in
    *"${R7_KEYWORD}"*) ;;
    *) R7_OK=0 ;;
  esac
done
if [ "${R7_OK}" -eq 1 ]; then
  pass 'R7：SKILL.md 含分流表的六类活'
else
  fail 'R7：SKILL.md 缺少分流表的某类活'
fi

# R8：自动派必须是明确禁止项。
case "${SKILL_TEXT}" in
  *'绝不自动派：只提议，等用户一个明确的肯定答复再调。'*) pass 'R8：SKILL.md 原样禁止自动派' ;;
  *) fail 'R8：SKILL.md 缺少原样的自动派禁令' ;;
esac

printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
