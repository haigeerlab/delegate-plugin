#!/bin/bash

PRINT_MODE=0
QUIET_MODE=0

case "${1:-}" in
  --print)
    PRINT_MODE=1
    ;;
  --session-start)
    # SessionStart 只探测、不输出。
    # 两个事件共用这个脚本，但 hookSpecificOutput 的 hookEventName 必须与实际事件一致；
    # 而 SessionStart 的输出契约本仓没有可核对的依据，**不猜**：
    # 这一路只负责把探测跑一遍（D3 起用来预热缓存），stdout 保持为空。
    QUIET_MODE=1
    ;;
esac

unavailable() {
  DETECTION_REASON="${1}"
  DETECTION_AVAILABLE=0
  return 0
}

probe() {
  DETECTION_AVAILABLE=0
  DETECTION_REASON='探测失败'
  SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${0}")" 2>/dev/null && pwd)" || return 0
  WRAPPER="${SCRIPT_DIR}/../scripts/codex-exec.sh"

  if [ ! -x "${WRAPPER}" ]; then
    unavailable 'wrapper 缺失或不可执行：请安装或修复 plugins/delegate/scripts/codex-exec.sh'
    return 0
  fi

  if ! command -v codex >/dev/null 2>&1; then
    unavailable 'codex 不在 PATH：请安装 Codex CLI 并确认 PATH'
    return 0
  fi

  if ! codex --version >/dev/null 2>&1; then
    unavailable 'codex 装坏了：npm install -g @openai/codex@latest'
    return 0
  fi

  AUTH_FILE="${CODEX_AUTH_FILE:-${HOME}/.codex/auth.json}"
  if [ ! -s "${AUTH_FILE}" ]; then
    unavailable '未登录：请跑一次 codex 交互式登录'
    return 0
  fi

  DETECTION_AVAILABLE=1
  DETECTION_REASON='Codex 后端可用'
  return 0
}

CACHE_FILE="${TMPDIR:-/tmp}/delegate/detection.json"

read_cache() {
  [ -f "${CACHE_FILE}" ] || return 1

  CACHE_DATA="$(python3 -c '
import json
import sys
import time

try:
    data = json.load(open(sys.argv[1]))
    available = data["available"]
    reason = data["reason"]
    checked_at = data["checkedAt"]
    if type(available) is not bool or not isinstance(reason, str):
        raise ValueError()
    if "|" in reason or "\n" in reason or "\r" in reason:
        raise ValueError()
    if isinstance(checked_at, bool) or not isinstance(checked_at, (int, float)):
        raise ValueError()
    if time.time() - checked_at > 8 * 60 * 60:
        raise ValueError()
    print(("1" if available else "0") + "|" + reason)
except Exception:
    sys.exit(1)
' "${CACHE_FILE}" 2>/dev/null)" || return 1

  case "${CACHE_DATA}" in
    1\|*) DETECTION_AVAILABLE=1 ;;
    0\|*) DETECTION_AVAILABLE=0 ;;
    *) return 1 ;;
  esac
  DETECTION_REASON="${CACHE_DATA#*|}"
  return 0
}

write_cache() {
  mkdir -p "${TMPDIR:-/tmp}/delegate" 2>/dev/null || return 1
  python3 -c '
import json
import sys
import time

with open(sys.argv[1], "w") as cache_file:
    json.dump({
        "available": sys.argv[2] == "1",
        "reason": sys.argv[3],
        "checkedAt": int(time.time()),
    }, cache_file)
    cache_file.write("\n")
' "${CACHE_FILE}" "${DETECTION_AVAILABLE}" "${DETECTION_REASON}" 2>/dev/null
}

emit_hook() {
  python3 -c '
import json
import sys

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": sys.argv[1],
    },
}, ensure_ascii=False))
' "${DETECTION_REASON}" 2>/dev/null || :
}

DETECTION_AVAILABLE=0
DETECTION_REASON='探测失败'
if [ "${QUIET_MODE}" -eq 1 ]; then
  probe
  write_cache >/dev/null 2>&1 || :
elif ! read_cache; then
  probe
  write_cache >/dev/null 2>&1 || :
fi

if [ "${PRINT_MODE}" -eq 1 ]; then
  if [ "${DETECTION_AVAILABLE}" -eq 1 ]; then
    printf '可用\n'
  else
    printf '不可用：%s\n' "${DETECTION_REASON}"
  fi
elif [ "${QUIET_MODE}" -eq 0 ] && [ "${DETECTION_AVAILABLE}" -eq 1 ]; then
  emit_hook
fi

exit 0
