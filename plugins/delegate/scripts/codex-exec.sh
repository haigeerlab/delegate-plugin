#!/bin/bash

set -u

usage() {
  printf '用法：%s [--write] [--model <slug>] [--effort <level>] [--] <任务>\n' "${0}" >&2
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
      --help|-h)
        usage
        exit 0
        ;;
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

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'delegate: 找不到 python3；请安装 Python 3 后重试。\n' >&2
  exit 127
fi
BACKEND_OUTPUT="$(python3 -B "${SCRIPT_DIR}/backend.py")"
BACKEND_STATUS=$?
if [ "${BACKEND_STATUS}" -ne 0 ]; then
  printf '%s\n' "${BACKEND_OUTPUT}" >&2
  exit "${BACKEND_STATUS}"
fi
if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" != true ]; then
  printf 'delegate: 当前目录不是 Git 工作区；请进入业务 Git 项目后重试。\n' >&2
  exit 64
fi

umask 077
TMP_ROOT="${TMPDIR:-/tmp}/delegate"
if [ -L "${TMP_ROOT}" ]; then
  printf 'delegate: 日志目录不能是软链接。\n' >&2
  exit 1
fi
mkdir -p "${TMP_ROOT}" && chmod 700 "${TMP_ROOT}" || exit 1
# Leave time for process cleanup and Git acceptance within the 600s Bash limit.
DELEGATE_TIMEOUT_SECONDS="$(python3 -c '
import os
try:
    seconds = int(os.environ.get("DELEGATE_TIMEOUT_SECONDS", "540"))
except ValueError:
    seconds = 540
print(min(seconds, 540) if seconds > 0 else 540)
')"
STAMP="$(date '+%Y%m%d%H%M%S')"
RUN_ID="${STAMP}.$$"
ANSWER="${TMP_ROOT}/${RUN_ID}.answer"
LOG="${TMP_ROOT}/${RUN_ID}.log"
PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱是只读的：不要修改文件、不要提交、不要启动服务、不要做任务之外的网络访问。'
SANDBOX='read-only'
GIT_BASELINE_HEAD=''
GIT_BASELINE_CHANGES=''

if [ "${WRITE_MODE}" -eq 1 ]; then
  SANDBOX='workspace-write'
  PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱允许写入当前工作目录：可以修改文件，但不要提交、不要推送、不要做任务之外的网络访问。'
  GIT_BASELINE_HEAD="$(git rev-parse --verify HEAD 2>/dev/null || printf '尚无提交')"
  GIT_BASELINE_STATUS="$(git status --porcelain)" || exit 1
  GIT_BASELINE_CHANGES="$(printf '%s' "${GIT_BASELINE_STATUS}" | python3 -c 'import sys; print(len(sys.stdin.read().splitlines()))')"
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

RUNNER_PID=''
EXEC_STARTED=0
emit_git_acceptance() {
  if [ "${WRITE_MODE}" -eq 1 ] && [ "${EXEC_STARTED}" -eq 1 ]; then
    printf '\ngit 验收（成功或失败均须查看；失败不会自动回滚）：\n'
    printf '基线 HEAD：%s\n' "${GIT_BASELINE_HEAD}"
    printf '跑之前工作区已有 %s 个未提交变更\n' "${GIT_BASELINE_CHANGES}"
    printf 'git status --short：\n'
    git status --short
    printf 'git diff --stat：\n'
    git diff --stat
    printf 'git diff --cached --stat：\n'
    git diff --cached --stat
  fi
}
finish() {
  EXIT_STATUS=$?
  trap - EXIT
  if [ -n "${RUNNER_PID}" ]; then
    kill -TERM "${RUNNER_PID}" 2>/dev/null || true
    wait "${RUNNER_PID}" 2>/dev/null || true
  fi
  if [ "${EXIT_STATUS}" -eq 0 ]; then
    emit_git_acceptance
  else
    emit_git_acceptance >&2
  fi
  cleanup_process_logs
  exit "${EXIT_STATUS}"
}
interrupted() {
  printf 'delegate: 委托被中断，正在停止执行进程组；失败不会自动回滚。\n' >&2
  exit "${1}"
}
trap finish EXIT
trap 'interrupted 143' TERM
trap 'interrupted 130' INT
trap 'interrupted 129' HUP

EXEC_STARTED=1
python3 -B "${SCRIPT_DIR}/run_codex.py" "${DELEGATE_TIMEOUT_SECONDS}" \
  env -u OPENAI_API_KEY -u CODEX_API_KEY codex exec \
  ${EXTRA[@]+"${EXTRA[@]}"} \
  -c 'forced_login_method="chatgpt"' -c 'model_provider="openai"' \
  --ephemeral --sandbox "${SANDBOX}" --color never \
  -o "${ANSWER}" -- "${PREAMBLE}

${TASK}" >"${LOG}" 2>&1 </dev/null &
RUNNER_PID=$!
wait "${RUNNER_PID}"
CODEX_STATUS=$?
RUNNER_PID=''

if [ "${CODEX_STATUS}" -eq 124 ]; then
  printf 'delegate: codex 超过 %s 秒被中止。完整过程日志：%s\n' "${DELEGATE_TIMEOUT_SECONDS}" "${LOG}" >&2
  exit 124
fi

if [ "${CODEX_STATUS}" -ne 0 ]; then
  printf 'delegate: codex 执行失败（退出 %s）。过程日志末尾（最后最多 40 行 / 16KiB）：\n' "${CODEX_STATUS}" >&2
  tail -c 16384 "${LOG}" | tail -n 40 >&2
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
