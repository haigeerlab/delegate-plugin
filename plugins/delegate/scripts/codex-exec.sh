#!/bin/bash

set -u

usage() {
  printf '用法：%s [--write] [--] <任务>\n' "${0}" >&2
}

TASK=''
TASK_COUNT=0
OPTIONS_ENDED=0
MODEL=''
EFFORT=''
EXTRA=()
WRITE_MODE=0

while [ "$#" -gt 0 ]; do
  ARG="${1}"
  shift

  if [ "${OPTIONS_ENDED}" -eq 0 ] && [ "${ARG}" = '--' ]; then
    OPTIONS_ENDED=1
    continue
  fi

  if [ "${OPTIONS_ENDED}" -eq 0 ]; then
    case "${ARG}" in
      --write)
        WRITE_MODE=1
        continue
        ;;
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
DELEGATE_TIMEOUT_SECONDS="${DELEGATE_TIMEOUT_SECONDS:-900}"
case "${DELEGATE_TIMEOUT_SECONDS}" in
  *[!0-9]*|'') DELEGATE_TIMEOUT_SECONDS=900 ;;
esac
STAMP="$(date '+%Y%m%d%H%M%S')"
RUN_ID="${STAMP}.$$"
ANSWER="${TMP_ROOT}/${RUN_ID}.answer"
LOG="${TMP_ROOT}/${RUN_ID}.log"
PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱是只读的：不要修改文件、不要提交、不要启动服务、不要做任务之外的网络访问。'
SANDBOX='read-only'
GIT_ACCEPTANCE=0
GIT_BASELINE_HEAD=''
GIT_BASELINE_CHANGES=''

if [ "${WRITE_MODE}" -eq 1 ]; then
  SANDBOX='workspace-write'
  PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱允许写入当前工作目录：可以修改文件，但不要提交、不要推送、不要做任务之外的网络访问。'
  if GIT_BASELINE_HEAD="$(git rev-parse HEAD 2>/dev/null)"; then
    GIT_BASELINE_CHANGES="$(git status --porcelain | wc -l | tr -d ' ')"
    GIT_ACCEPTANCE=1
  fi
fi

if [ -n "${MODEL}" ]; then
  EXTRA+=(-m "${MODEL}")
fi
if [ -n "${EFFORT}" ]; then
  EXTRA+=(-c "model_reasoning_effort=\"${EFFORT}\"")
fi

cleanup_process_logs() {
  python3 - "${TMP_ROOT}" <<'PY' >/dev/null 2>&1
import os
import sys

directory = sys.argv[1]
try:
    logs = []
    for entry in os.scandir(directory):
        if entry.name.endswith('.log'):
            try:
                logs.append((entry.stat().st_mtime, entry.path))
            except OSError:
                pass
    logs.sort(reverse=True)
    for _, log in logs[50:]:
        try:
            os.unlink(log)
        except OSError:
            continue
        answer = log[:-4] + '.answer'
        try:
            os.unlink(answer)
        except OSError:
            pass
except OSError:
    pass
PY
}

env -u OPENAI_API_KEY codex exec \
  ${EXTRA[@]+"${EXTRA[@]}"} \
  --ephemeral --sandbox "${SANDBOX}" --color never \
  -o "${ANSWER}" -- "${PREAMBLE}

${TASK}" >"${LOG}" 2>&1 </dev/null &
CODEX_PID=$!
START_SECONDS=${SECONDS}
TIMED_OUT=0

while kill -0 "${CODEX_PID}" 2>/dev/null; do
  if [ $((SECONDS - START_SECONDS)) -ge "${DELEGATE_TIMEOUT_SECONDS}" ]; then
    kill "${CODEX_PID}" 2>/dev/null || true
    wait "${CODEX_PID}" 2>/dev/null || true
    TIMED_OUT=1
    break
  fi
  sleep 0.25
done

if [ "${TIMED_OUT}" -eq 1 ]; then
  cleanup_process_logs
  printf 'delegate: codex 超过 %s 秒被中止。完整过程日志：%s\n' "${DELEGATE_TIMEOUT_SECONDS}" "${LOG}" >&2
  exit 124
fi

wait "${CODEX_PID}"
CODEX_STATUS=$?
cleanup_process_logs

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
if [ "${WRITE_MODE}" -eq 1 ]; then
  if [ "${GIT_ACCEPTANCE}" -eq 1 ]; then
    printf 'git 验收（Claude 必须看这一段，不要只信自述）：\n'
    printf '基线 HEAD：%s\n' "${GIT_BASELINE_HEAD}"
    printf '跑之前工作区已有 %s 个未提交变更\n' "${GIT_BASELINE_CHANGES}"
    printf 'git status --short：\n'
    git status --short
    printf 'git diff --stat：\n'
    git diff --stat
  else
    printf 'git 验收：当前目录不是 git 仓库，拿不到 diff；只能依据 Codex 自述，请谨慎采信。\n'
  fi
fi
printf '模型：%s / 推理档：%s\n' "${MODEL:-配置默认}" "${EFFORT:-配置默认}"
printf '过程日志（未进入本会话上下文）：%s（%s 字节；最终答复 %s 字节）\n' "${LOG}" "${LOG_BYTES}" "${ANSWER_BYTES}"
