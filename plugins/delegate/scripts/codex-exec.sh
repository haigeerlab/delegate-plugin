#!/bin/bash

set -u

if [ "${DELEGATE_REVIEW_DEPTH:-0}" != '0' ]; then
  printf 'delegate: recursive delegation is not supported.\n' >&2
  exit 64
fi

usage() {
  printf '用法：%s [--write] [--model <slug>] [--effort <level>] [--resumable] [--] <任务>\n' "${0}" >&2
  printf '      %s --resume <runId> [--write] [--] <用户答复>\n' "${0}" >&2
}

TASK=''
TASK_COUNT=0
OPTIONS_ENDED=0
MODEL=''
EFFORT=''
EXTRA=()
WRITE_MODE=0
RESUMABLE=0
RESUME_ID=''
RESUME_GIVEN=0

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
      --resumable)
        RESUMABLE=1
        continue
        ;;
      --resume)
        if [ "$#" -eq 0 ] || [ "${RESUME_GIVEN}" -eq 1 ]; then
          usage
          exit 64
        fi
        RESUME_ID="${1}"
        RESUME_GIVEN=1
        shift
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
if [ "${RESUME_GIVEN}" -eq 1 ] && { [ "${RESUMABLE}" -eq 1 ] || [ -n "${MODEL}" ] || [ -n "${EFFORT}" ]; }; then
  printf 'delegate: --resume cannot be combined with --resumable, --model or --effort\n' >&2
  exit 64
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'delegate: 找不到 python3；请安装 Python 3 后重试。\n' >&2
  exit 127
fi
TMP_ROOT="${TMPDIR:-/tmp}/delegate"
SESSION_ID=''
if [ "${RESUME_GIVEN}" -eq 1 ]; then
  # Refuse before probing Codex so a stale or foreign runId never reaches the CLI.
  if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" != true ]; then
    printf 'delegate: 当前目录不是 Git 工作区；请进入业务 Git 项目后重试。\n' >&2
    exit 64
  fi
  RESUME_STATE="$(python3 -B "${SCRIPT_DIR}/run_state.py" check "${TMP_ROOT}" "${RESUME_ID}" \
    "$(git rev-parse --show-toplevel)" "${WRITE_MODE}")" || exit "$?"
  SESSION_ID="$(printf '%s\n' "${RESUME_STATE}" | sed -n 1p)"
  MODEL="$(printf '%s\n' "${RESUME_STATE}" | sed -n 2p)"
  EFFORT="$(printf '%s\n' "${RESUME_STATE}" | sed -n 3p)"
  RESUMABLE=1
fi
python3 -B "${SCRIPT_DIR}/delegate_model.py" codex "${MODEL}" || exit "$?"
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

EPHEMERAL=(--ephemeral)
# Never let a configured approver let a delegated run leave its sandbox.
APPROVAL=(-c 'approval_policy="never"')
REPO_ROOT="$(git rev-parse --show-toplevel)" || exit 1
PARENT_RUN_ID=''
PROMPT="${PREAMBLE}

${TASK}"
if [ "${RESUMABLE}" -eq 1 ]; then
  # Resumable sessions are persisted by Codex; keep the sandbox sentence and swap only the opening.
  EPHEMERAL=()
  PROMPT='【可续跑委托】你的最终答复会转给用户；用户答复后，会带着答复在本会话里接着跑。先做不受待定决策影响的任务，碰到需要用户拍板的决策（规格没覆盖的取舍、测试改不红、高风险不可逆操作）再停。要停时，最终答复第一行以 `NEED_USER:` 开头，后面写要问用户的问题，再写已完成的进度和可选项；不需要用户时照常做到底，第一行不要写 `NEED_USER:`。'"${PREAMBLE#*并把完整结论写进最终答复。}

${TASK}"
fi
if [ "${RESUME_GIVEN}" -eq 1 ]; then
  PARENT_RUN_ID="${RESUME_ID}"
  PROMPT="【用户答复】${TASK}

请按上次约定继续：先做不受待定决策影响的任务；还需要用户拍板时，最终答复第一行以 \`NEED_USER:\` 开头。"
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
        for suffix in ('.answer', '.state.json', '.resumed'):
            try:
                os.unlink(log[:-4] + suffix)
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
    if [ -n "${RESULT_LINE}" ]; then
      printf '%s\n' "${RESULT_LINE}"
    fi
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

CODEX_ARGS=(exec ${EXTRA[@]+"${EXTRA[@]}"} -c 'forced_login_method="chatgpt"' -c 'model_provider="openai"' \
  ${APPROVAL[@]+"${APPROVAL[@]}"} ${EPHEMERAL[@]+"${EPHEMERAL[@]}"} --sandbox "${SANDBOX}" --color never -o "${ANSWER}" -- "${PROMPT}")
if [ "${RESUME_GIVEN}" -eq 1 ]; then
  # `exec resume` has no --sandbox or --color; the sandbox is set through config instead.
  CODEX_ARGS=(exec resume ${EXTRA[@]+"${EXTRA[@]}"} -c 'forced_login_method="chatgpt"' -c 'model_provider="openai"' \
    ${APPROVAL[@]+"${APPROVAL[@]}"} -c "sandbox_mode=\"${SANDBOX}\"" -o "${ANSWER}" -- "${SESSION_ID}" "${PROMPT}")
  python3 -B "${SCRIPT_DIR}/run_state.py" claim "${TMP_ROOT}" "${RESUME_ID}" || exit 64
fi

RESULT_LINE=''
EXEC_STARTED=1
python3 -B "${SCRIPT_DIR}/run_codex.py" "${DELEGATE_TIMEOUT_SECONDS}" \
  env -u OPENAI_API_KEY -u CODEX_API_KEY DELEGATE_REVIEW_DEPTH=1 codex "${CODEX_ARGS[@]}" \
  >"${LOG}" 2>&1 </dev/null &
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
RESULT_LINE="$(python3 -B "${SCRIPT_DIR}/run_state.py" record "${TMP_ROOT}" "${RUN_ID}" "${LOG}" "${ANSWER}" \
  "${REPO_ROOT}" "${WRITE_MODE}" "${MODEL}" "${EFFORT}" "${PARENT_RUN_ID}" "${RESUMABLE}")"
