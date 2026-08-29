#!/bin/bash

set -u

usage() {
  printf '用法：%s [--] <任务>\n' "${0}" >&2
}

TASK=''
TASK_COUNT=0
OPTIONS_ENDED=0
MODEL=''
EFFORT=''
EXTRA=()

while [ "$#" -gt 0 ]; do
  ARG="${1}"
  shift

  if [ "${OPTIONS_ENDED}" -eq 0 ] && [ "${ARG}" = '--' ]; then
    OPTIONS_ENDED=1
    continue
  fi

  if [ "${OPTIONS_ENDED}" -eq 0 ]; then
    case "${ARG}" in
      --model)
        if [ "$#" -eq 0 ]; then
          usage
          exit 64
        fi
        MODEL="${1}"
        shift
        continue
        ;;
      --effort)
        if [ "$#" -eq 0 ]; then
          usage
          exit 64
        fi
        EFFORT="${1}"
        shift
        continue
        ;;
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

if ! command -v codex >/dev/null 2>&1; then
  printf 'delegate: 找不到 codex；请安装 Codex CLI 后重试。\n' >&2
  exit 127
fi

if ! codex --version >/dev/null 2>&1; then
  printf 'delegate: codex 无法运行；请执行 npm install -g @openai/codex@latest 后重试。\n' >&2
  exit 127
fi

TMP_ROOT="${TMPDIR:-/tmp}/delegate"
mkdir -p "${TMP_ROOT}" || exit 1
STAMP="$(date '+%Y%m%d%H%M%S')"
RUN_ID="${STAMP}.$$"
ANSWER="${TMP_ROOT}/${RUN_ID}.answer"
LOG="${TMP_ROOT}/${RUN_ID}.log"
PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱是只读的：不要修改文件、不要提交、不要启动服务、不要做任务之外的网络访问。'

if [ -n "${MODEL}" ]; then
  EXTRA+=(-m "${MODEL}")
fi
if [ -n "${EFFORT}" ]; then
  EXTRA+=(-c "model_reasoning_effort=\"${EFFORT}\"")
fi

env -u OPENAI_API_KEY codex exec \
  ${EXTRA[@]+"${EXTRA[@]}"} \
  --ephemeral --sandbox read-only --color never \
  -o "${ANSWER}" -- "${PREAMBLE}

${TASK}" >"${LOG}" 2>&1 </dev/null
CODEX_STATUS=$?

if [ "${CODEX_STATUS}" -ne 0 ]; then
  printf 'delegate: codex 执行失败（退出 %s）。过程日志末尾（最后 40 行）：\n' "${CODEX_STATUS}" >&2
  tail -n 40 "${LOG}" >&2
  printf 'delegate: 完整过程日志：%s\n' "${LOG}" >&2
  exit "${CODEX_STATUS}"
fi

if [ ! -s "${ANSWER}" ]; then
  printf 'delegate: 产出为空（答复文件缺失或为空）。完整过程日志：%s\n' "${LOG}" >&2
  exit 1
fi

ANSWER_BYTES="$(wc -c < "${ANSWER}" | tr -d ' ')"
LOG_BYTES="$(wc -c < "${LOG}" | tr -d ' ')"
cat "${ANSWER}"
printf '\n---\n'
printf '模型：%s / 推理档：%s\n' "${MODEL:-配置默认}" "${EFFORT:-配置默认}"
printf '过程日志（未进入本会话上下文）：%s（%s 字节；最终答复 %s 字节）\n' "${LOG}" "${LOG_BYTES}" "${ANSWER_BYTES}"
