#!/bin/bash

set -u

usage() {
  printf '用法：%s [--] <任务>\n' "${0}" >&2
}

TASK=''
TASK_COUNT=0
OPTIONS_ENDED=0

for ARG in ${@+"${@}"}; do
  if [ "${OPTIONS_ENDED}" -eq 0 ] && [ "${ARG}" = '--' ]; then
    OPTIONS_ENDED=1
    continue
  fi

  if [ "${OPTIONS_ENDED}" -eq 0 ]; then
    case "${ARG}" in
      -*)
        usage
        exit 64
        ;;
    esac
  fi

  TASK_COUNT=$((TASK_COUNT + 1))
  TASK="${ARG}"
done

if [ "${TASK_COUNT}" -ne 1 ] || [ -z "${TASK}" ]; then
  usage
  exit 64
fi

TMP_ROOT="${TMPDIR:-/tmp}/delegate"
mkdir -p "${TMP_ROOT}" || exit 1
STAMP="$(date '+%Y%m%d%H%M%S')"
RUN_ID="${STAMP}.$$"
ANSWER="${TMP_ROOT}/${RUN_ID}.answer"
LOG="${TMP_ROOT}/${RUN_ID}.log"
PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱是只读的：不要修改文件、不要提交、不要启动服务、不要做任务之外的网络访问。'

env -u OPENAI_API_KEY codex exec \
  --ephemeral --sandbox read-only --color never \
  -o "${ANSWER}" -- "${PREAMBLE}

${TASK}" >"${LOG}" 2>&1 </dev/null
CODEX_STATUS=$?

if [ "${CODEX_STATUS}" -ne 0 ]; then
  exit "${CODEX_STATUS}"
fi

if [ ! -s "${ANSWER}" ]; then
  exit 1
fi

ANSWER_BYTES="$(wc -c < "${ANSWER}" | tr -d ' ')"
LOG_BYTES="$(wc -c < "${LOG}" | tr -d ' ')"
cat "${ANSWER}"
printf '\n---\n'
printf '过程日志（未进入本会话上下文）：%s（%s 字节；最终答复 %s 字节）\n' "${LOG}" "${LOG_BYTES}" "${ANSWER_BYTES}"
