#!/bin/bash

ISSUE_COUNT=0
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${0}")" 2>/dev/null && pwd)"

printf '安装与登录\n'
if [ -n "${SCRIPT_DIR}" ]; then
  DETECTION_OUTPUT="$("${SCRIPT_DIR}/detect.sh" --print 2>&1)"
else
  DETECTION_OUTPUT='不可用：无法定位 detect.sh'
fi
printf '%s\n' "${DETECTION_OUTPUT}"
case "${DETECTION_OUTPUT}" in
  不可用*) ISSUE_COUNT=$((ISSUE_COUNT + 1)) ;;
esac

printf '\nAGENTS.md 体检\n'
AGENTS_FILE="${CODEX_AGENTS_FILE:-${HOME}/.codex/AGENTS.md}"
if [ ! -f "${AGENTS_FILE}" ]; then
  printf '没有全局 AGENTS.md，不影响委托\n'
else
  AGENTS_CONTENT="$(/bin/cat "${AGENTS_FILE}" 2>/dev/null)"

  ORCHESTRATION=0
  case "${AGENTS_CONTENT}" in
    *等确认*|*等待确认*|*请确认*|*确认后*|*先出方案*|*先做方案*|*先给方案*|*不要直接开始改代码*|*不要直接改代码*|*不得直接修改*)
      ORCHESTRATION=1
      ;;
  esac

  # 已经声明的非交互豁免要认出来。
  # 不认它就会在**已经修好的**文件上报警报，并建议加一条已经在那儿的规则 ——
  # 2026-08-29 在作者本人的 ~/.codex/AGENTS.md 上实测到过。
  # 测试没抓住：断言 14 只覆盖「完全没有流程编排规则」，没覆盖「有规则但已豁免」。
  EXEMPTED=0
  case "${AGENTS_CONTENT}" in
    *仅适用于交互式会话*|*非交互*跳过*) EXEMPTED=1 ;;
  esac

  if [ "${ORCHESTRATION}" -eq 0 ]; then
    printf '未发现会让非交互委托死锁的规则\n'
  elif [ "${EXEMPTED}" -eq 1 ]; then
    printf '发现流程编排规则，但已声明非交互豁免 —— 不影响委托\n'
  else
    ISSUE_COUNT=$((ISSUE_COUNT + 1))
    printf '风险：发现可能让非交互委托死锁的流程编排规则。\n'
    printf '修法：在该节开头加一条「本节仅适用于交互式会话；非交互调用（codex exec）时整节跳过，直接执行到底」。\n'
    printf '原因：codex exec 是非交互的，没有人能回答确认请求，Codex 可能停在“请确认后我执行”而什么都不做；全局 AGENTS.md 没有按调用关闭的开关（-c project_doc_max_bytes=0 只关项目级；experimental_instructions_file 在 0.150.1 已不存在）。\n'
  fi
fi

printf '\n小结：'
if [ "${ISSUE_COUNT}" -eq 0 ]; then
  printf '通过，未发现问题\n'
else
  printf '发现 %s 个问题\n' "${ISSUE_COUNT}"
fi

exit 0
