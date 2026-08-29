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
  return 1
}

detect() {
  SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${0}")" && pwd)" || return 1
  WRAPPER="${SCRIPT_DIR}/../scripts/codex-exec.sh"

  if [ ! -x "${WRAPPER}" ]; then
    unavailable 'wrapper 缺失或不可执行：请安装或修复 plugins/delegate/scripts/codex-exec.sh'
    return 1
  fi

  if ! command -v codex >/dev/null 2>&1; then
    unavailable 'codex 不在 PATH：请安装 Codex CLI 并确认 PATH'
    return 1
  fi

  if ! codex --version >/dev/null 2>&1; then
    unavailable 'codex 装坏了：npm install -g @openai/codex@latest'
    return 1
  fi

  AUTH_FILE="${CODEX_AUTH_FILE:-${HOME}/.codex/auth.json}"
  if [ ! -s "${AUTH_FILE}" ]; then
    unavailable '未登录：请跑一次 codex 交互式登录'
    return 1
  fi

  return 0
}

DETECTION_REASON='探测失败'
if detect; then
  if [ "${PRINT_MODE}" -eq 1 ]; then
    printf '可用\n'
  elif [ "${QUIET_MODE}" -eq 0 ]; then
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Codex 后端可用"}}'
  fi
else
  if [ "${PRINT_MODE}" -eq 1 ]; then
    printf '不可用：%s\n' "${DETECTION_REASON}"
  fi
fi

exit 0
