#!/bin/bash

set -u

if [ "${DELEGATE_REVIEW_DEPTH:-0}" != '0' ]; then
  printf 'delegate: recursive delegation is not supported.\n' >&2
  exit 64
fi

usage() {
  printf '用法：%s [--write] [--model <slug>] [--effort <level>] [--resumable] [--strict] [--] <任务>\n' "${0}" >&2
  printf '      %s --resume <runId> [--write] [--strict] [--] <用户答复>\n' "${0}" >&2
  printf '      %s --continue <runId> [--write] [--strict] [--] <下一个任务>\n' "${0}" >&2
}

TASK=''
TASK_COUNT=0
OPTIONS_ENDED=0
MODEL=''
EFFORT=''
EXTRA=()
WRITE_MODE=0
RESUMABLE=0
STRICT=0
RESUME_ID=''
RESUME_GIVEN=0
TIMEOUT_GIVEN=''
CONTINUE_GIVEN=0

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
      --strict)
        STRICT=1
        continue
        ;;
      --resume|--continue)
        if [ "$#" -eq 0 ] || [ "${RESUME_GIVEN}" -eq 1 ]; then
          usage
          exit 64
        fi
        # --continue reuses the resume path; only the accepted status and the prompt differ.
        if [ "${ARG}" = '--continue' ]; then
          CONTINUE_GIVEN=1
        fi
        RESUME_ID="${1}"
        RESUME_GIVEN=1
        shift
        continue
        ;;
      --timeout)
        if [ "$#" -eq 0 ] || [ -n "${TIMEOUT_GIVEN}" ]; then
          usage
          exit 64
        fi
        case "${1}" in
          ''|*[!0-9]*) TIMEOUT_GIVEN='invalid' ;;
          *) if [ "${#1}" -le 4 ] && [ "${1}" -ge 541 ] && [ "${1}" -le 7200 ]; then TIMEOUT_GIVEN="${1}"; else TIMEOUT_GIVEN='invalid'; fi ;;
        esac
        if [ "${TIMEOUT_GIVEN}" = 'invalid' ]; then
          printf 'delegate: --timeout must be an integer between 541 and 7200\n' >&2
          exit 64
        fi
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
  printf 'delegate: --resume or --continue cannot be combined with --resumable, --model or --effort\n' >&2
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
  CHECK_MODE='resume'
  [ "${CONTINUE_GIVEN}" -eq 1 ] && CHECK_MODE='continue'
  RESUME_STATE="$(python3 -B "${SCRIPT_DIR}/run_state.py" check "${TMP_ROOT}" "${RESUME_ID}" \
    "$(git rev-parse --show-toplevel)" "${WRITE_MODE}" "${CHECK_MODE}")" || exit "$?"
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
# An explicit --timeout widens the total; the split below is unchanged (run-longrun).
if [ -n "${TIMEOUT_GIVEN}" ]; then
  DELEGATE_TIMEOUT_SECONDS="${TIMEOUT_GIVEN}"
fi
# Split the deadline: Codex's main run gets MAIN_SECONDS, a wrap-up round WRAPUP_SECONDS.
DEADLINES="$(python3 -B "${SCRIPT_DIR}/run_state.py" deadlines "${DELEGATE_TIMEOUT_SECONDS}")" || exit 1
WRAPUP_SECONDS="$(printf '%s\n' "${DEADLINES}" | sed -n 1p)"
MAIN_SECONDS="$(printf '%s\n' "${DEADLINES}" | sed -n 2p)"
THRESHOLD_SECONDS="$(printf '%s\n' "${DEADLINES}" | sed -n 3p)"
STAMP="$(date '+%Y%m%d%H%M%S')"
RUN_ID="${STAMP}.$$"
ANSWER="${TMP_ROOT}/${RUN_ID}.answer"
LOG="${TMP_ROOT}/${RUN_ID}.log"
EVENTS="${TMP_ROOT}/${RUN_ID}.events.jsonl"
CLEANUP="${TMP_ROOT}/${RUN_ID}.cleanup"
PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱是只读的：不要修改文件、不要提交、不要启动服务、不要做任务之外的网络访问。'
SANDBOX='read-only'
GIT_BASELINE_HEAD=''
GIT_BASELINE_CHANGES=''

if [ "${WRITE_MODE}" -eq 1 ]; then
  SANDBOX='workspace-write'
  PREAMBLE='【非交互委托】没有人能回答你的提问或确认请求，也不会有后续轮次。不要先出方案等确认，直接做到底，并把完整结论写进最终答复。沙箱允许写入当前工作目录：可以修改文件，但不要提交、不要推送、不要做任务之外的网络访问。'
  GIT_BASELINE_HEAD="$(git rev-parse --verify HEAD 2>/dev/null || printf '尚无提交')"
  GIT_BASELINE_STATUS="$(git status --porcelain)" || exit 1
  # Kept so a timeout fallback can list what changed during the run.
  printf '%s\n' "${GIT_BASELINE_STATUS}" > "${TMP_ROOT}/${RUN_ID}.baseline" || exit 1
  GIT_BASELINE_CHANGES="$(printf '%s' "${GIT_BASELINE_STATUS}" | python3 -c 'import sys; print(len(sys.stdin.read().splitlines()))')"
fi

EPHEMERAL=(--ephemeral)
# Never let a configured approver let a delegated run leave its sandbox.
APPROVAL=(-c 'approval_policy="never"')
# Write runs would make Codex persist project trust in the user's config.toml; trust it for this run only.
TRUST=()
if [ "${WRITE_MODE}" -eq 1 ]; then
  TRUST_OVERRIDE="$(python3 -B "${SCRIPT_DIR}/codex_trust.py")"
  if [ -n "${TRUST_OVERRIDE}" ]; then
    TRUST=(-c "${TRUST_OVERRIDE}")
  fi
fi
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
  if [ "${CONTINUE_GIVEN}" -eq 1 ]; then
    PROMPT="【下一个任务】${TASK}

上一个任务已经结束。请在本会话里接着做这个新任务，沿用之前的约定：先做不受待定决策影响的部分；需要用户拍板时，最终答复第一行以 \`NEED_USER:\` 开头。"
  fi
fi

if [ -n "${MODEL}" ]; then
  EXTRA+=(-m "${MODEL}")
fi
if [ -n "${EFFORT}" ]; then
  EXTRA+=(-c "model_reasoning_effort=\"${EFFORT}\"")
fi

cleanup_process_logs() {
  python3 -B "${SCRIPT_DIR}/run_state.py" cleanup "${TMP_ROOT}" >/dev/null 2>&1
}

RUNNER_PID=''
EXEC_STARTED=0
RESULT_LINE=''
RESULT_STATUS=''
WRAPUP_MODE=''
WRAPUP_REASON=''
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
wait_runner_gone() {
  # `wait` itself has no timeout; poll against wall-clock seconds instead.
  WAIT_UNTIL=$((SECONDS + ${1}))
  while kill -0 "${RUNNER_PID}" 2>/dev/null && [ "${SECONDS}" -lt "${WAIT_UNTIL}" ]; do
    sleep 0.1
  done
  ! kill -0 "${RUNNER_PID}" 2>/dev/null
}
stop_runner() {
  kill -TERM "${RUNNER_PID}" 2>/dev/null || true
  # run_codex.py needs about 10 seconds for a full abort cleanup.
  if wait_runner_gone 15; then
    wait "${RUNNER_PID}" 2>/dev/null || true
    return 0
  fi
  kill -KILL "${RUNNER_PID}" 2>/dev/null || true
  if wait_runner_gone 2; then
    wait "${RUNNER_PID}" 2>/dev/null || true
    # Into the cleanup report, which finish forwards to stderr and copies into the result file.
    printf 'delegate: 执行进程超时未退出，已强制结束（PID=%s），其后代可能残留。\n' "${RUNNER_PID}" >> "${CLEANUP}"
  else
    printf 'delegate: 执行进程未能回收，PID=%s\n' "${RUNNER_PID}" >> "${CLEANUP}"
  fi
  return 1
}
run_kind() {
  if [ "${CONTINUE_GIVEN}" -eq 1 ]; then
    printf 'continue'
  elif [ "${RESUME_GIVEN}" -eq 1 ]; then
    printf 'resume'
  else
    printf 'run'
  fi
}
write_result_file() {
  RESULT_RESUMABLE=0
  case "${RESULT_LINE}" in
    *' resumable=true') RESULT_RESUMABLE=1 ;;
  esac
  if [ -n "${RESULT_LINE}" ]; then
    RESULT_STATUS="${RESULT_LINE#* status=}"
    RESULT_STATUS="${RESULT_STATUS%% *}"
  elif [ -z "${RESULT_STATUS}" ]; then
    case "${EXIT_STATUS}" in
      125) RESULT_STATUS='unreaped' ;;
      129|130|143) RESULT_STATUS='interrupted' ;;
      *) RESULT_STATUS='failed' ;;
    esac
  fi
  RESULT_KIND="$(run_kind)"
  if RESULT_PATH="$(python3 -B "${SCRIPT_DIR}/run_state.py" result --directory "${TMP_ROOT}" --run-id "${RUN_ID}" \
    --kind "${RESULT_KIND}" --parent "${PARENT_RUN_ID}" --repository "${REPO_ROOT}" --status "${RESULT_STATUS}" \
    --exit-code "${EXIT_STATUS}" --started "${T0}" --answer "${ANSWER}" --events "${EVENTS}" --log "${LOG}" \
    --wrapup-events "${TMP_ROOT}/${RUN_ID}.wrapup.events.jsonl" --wrapup-mode "${WRAPUP_MODE}" \
    --wrapup-reason "${WRAPUP_REASON}" --baseline "${TMP_ROOT}/${RUN_ID}.baseline" --cleanup "${CLEANUP}" \
    --model "${MODEL}" --effort "${EFFORT}" --write "${WRITE_MODE}" --resumable "${RESULT_RESUMABLE}" \
    --resumable-mode "${RESUMABLE}" --strict "${STRICT}" --timeout-seconds "${DELEGATE_TIMEOUT_SECONDS}")"; then
    if [ -n "${RESULT_LINE}" ]; then
      printf 'delegate: result=%s\n' "${RESULT_PATH}"
    else
      printf 'delegate: result=%s\n' "${RESULT_PATH}" >&2
    fi
  else
    printf 'delegate: 结果文件写入失败。\n' >&2
  fi
}
finish() {
  EXIT_STATUS=$?
  trap - EXIT
  if [ -n "${RUNNER_PID}" ] && ! stop_runner && [ "${EXIT_STATUS}" -eq 0 ]; then
    EXIT_STATUS=1
  fi
  if [ "${EXIT_STATUS}" -eq 0 ]; then
    emit_git_acceptance
  else
    emit_git_acceptance >&2
  fi
  if [ -s "${CLEANUP}" ]; then
    cat "${CLEANUP}" >&2
  fi
  if [ "${EXEC_STARTED}" -eq 1 ]; then
    write_result_file
  fi
  if [ -n "${RESULT_LINE}" ]; then
    printf '%s\n' "${RESULT_LINE}"
  fi
  cleanup_process_logs
  exit "${EXIT_STATUS}"
}
interrupted() {
  RESULT_STATUS='interrupted'
  printf 'delegate: 委托被中断，正在停止执行进程组；失败不会自动回滚。\n' >&2
  exit "${1}"
}
trap finish EXIT
trap 'interrupted 143' TERM
trap 'interrupted 130' INT
trap 'interrupted 129' HUP

if [ "${STRICT}" -eq 1 ]; then
  STRICT_ASK=''
  if [ "${RESUMABLE}" -eq 1 ]; then
    STRICT_ASK='需要用户拍板时写 `NEED_USER:`；'
  fi
  PROMPT="${PROMPT}

【结束标记】最终答复的第一行必须以下列标记之一开头：做完了写 \`DONE:\`，后面接一句总结；${STRICT_ASK}到了时间预算写 \`TIME_UP:\`。这一要求优先于项目 AGENTS.md 或其他文件里的格式要求。"
fi
T0="$(date '+%s')"
PROMPT="${PROMPT}

$(printf '【时间预算】本次运行开始于 epoch 秒 %s，%s 秒后会被强制中止，中止时不保留未写出的答复。需要判断用时就运行 `date +%%s`。已用时达到 %s 秒后，不要再开始新的步骤，也不要启动预计会跨过期限的长命令，立即给出最终答复：第一行以 `TIME_UP:` 开头，后面写已完成的进度、做到一半的步骤（如有）、下一步应从哪里开始。' \
  "${T0}" "${MAIN_SECONDS}" "${THRESHOLD_SECONDS}")"
CODEX_ARGS=(exec ${EXTRA[@]+"${EXTRA[@]}"} -c 'forced_login_method="chatgpt"' -c 'model_provider="openai"' \
  ${APPROVAL[@]+"${APPROVAL[@]}"} ${TRUST[@]+"${TRUST[@]}"} ${EPHEMERAL[@]+"${EPHEMERAL[@]}"} --sandbox "${SANDBOX}" --color never --json -o "${ANSWER}" -- "${PROMPT}")
if [ "${RESUME_GIVEN}" -eq 1 ]; then
  # `exec resume` has no --sandbox or --color; the sandbox is set through config instead.
  CODEX_ARGS=(exec resume ${EXTRA[@]+"${EXTRA[@]}"} -c 'forced_login_method="chatgpt"' -c 'model_provider="openai"' \
    ${APPROVAL[@]+"${APPROVAL[@]}"} ${TRUST[@]+"${TRUST[@]}"} -c "sandbox_mode=\"${SANDBOX}\"" --json -o "${ANSWER}" -- "${SESSION_ID}" "${PROMPT}")
  python3 -B "${SCRIPT_DIR}/run_state.py" claim "${TMP_ROOT}" "${RESUME_ID}" || exit 64
fi

EXEC_STARTED=1
python3 -B "${SCRIPT_DIR}/run_codex.py" --report "${CLEANUP}" "${MAIN_SECONDS}" \
  env -u OPENAI_API_KEY -u CODEX_API_KEY DELEGATE_REVIEW_DEPTH=1 codex "${CODEX_ARGS[@]}" \
  >"${EVENTS}" 2>"${LOG}" </dev/null &
RUNNER_PID=$!
wait "${RUNNER_PID}"
CODEX_STATUS=$?
RUNNER_PID=''

if [ "${CODEX_STATUS}" -eq 124 ]; then
  printf 'delegate: codex 超过 %s 秒被中止。完整过程日志：%s\n' "${MAIN_SECONDS}" "${LOG}" >&2
  # Wrap-up: one read-only resume round that only reports progress, else a model-free fallback.
  FALLBACK_REASON=''
  STOPPED_SESSION=''
  if [ "${RESUMABLE}" -eq 1 ]; then
    STOPPED_SESSION="$(python3 -B "${SCRIPT_DIR}/run_events.py" session "${EVENTS}")"
  fi
  if [ "${RESUMABLE}" -ne 1 ]; then
    # An --ephemeral session id exists in the log but is never persisted, so it is not reported.
    FALLBACK_REASON='普通 run 不保留会话'
  elif [ -z "${STOPPED_SESSION}" ]; then
    FALLBACK_REASON='未取得会话 ID'
  elif [ "${WRAPUP_SECONDS}" -le 0 ]; then
    FALLBACK_REASON='收尾轮超时'
  else
    WRAPUP_ANSWER="${TMP_ROOT}/${RUN_ID}.wrapup.answer"
    WRAPUP_PROMPT='【收尾】本次运行已到期被中止。不要再执行任何命令，也不要继续做任务。只写进度：第一行以 `TIME_UP:` 开头，后面写已完成的步骤及结果、做到一半的步骤（如有）、下一步应从哪里开始。'
    python3 -B "${SCRIPT_DIR}/run_codex.py" --report "${CLEANUP}" "${WRAPUP_SECONDS}" \
      env -u OPENAI_API_KEY -u CODEX_API_KEY DELEGATE_REVIEW_DEPTH=1 codex exec resume ${EXTRA[@]+"${EXTRA[@]}"} \
      -c 'forced_login_method="chatgpt"' -c 'model_provider="openai"' ${APPROVAL[@]+"${APPROVAL[@]}"} \
      -c 'sandbox_mode="read-only"' --json -o "${WRAPUP_ANSWER}" -- "${STOPPED_SESSION}" "${WRAPUP_PROMPT}" \
      >"${TMP_ROOT}/${RUN_ID}.wrapup.events.jsonl" 2>"${TMP_ROOT}/${RUN_ID}.wrapup" </dev/null &
    RUNNER_PID=$!
    wait "${RUNNER_PID}"
    WRAPUP_STATUS=$?
    RUNNER_PID=''
    if [ "${WRAPUP_STATUS}" -eq 124 ]; then
      FALLBACK_REASON='收尾轮超时'
    elif [ "${WRAPUP_STATUS}" -ne 0 ]; then
      FALLBACK_REASON="收尾轮失败（退出 ${WRAPUP_STATUS}）"
    elif [ ! -s "${WRAPUP_ANSWER}" ]; then
      FALLBACK_REASON='收尾轮答复为空'
    else
      cp "${WRAPUP_ANSWER}" "${ANSWER}" || exit 1
    fi
  fi
  [ -n "${FALLBACK_REASON}" ] && : > "${ANSWER}"
  WRAPUP_MODE='收尾轮'
  WRAPUP_REASON="${FALLBACK_REASON}"
  [ -n "${FALLBACK_REASON}" ] && WRAPUP_MODE='兜底'
  TIMEOUT_LINE="$(python3 -B "${SCRIPT_DIR}/run_state.py" record "${TMP_ROOT}" "${RUN_ID}" "${LOG}" "${ANSWER}" \
    "${REPO_ROOT}" "${WRITE_MODE}" "${MODEL}" "${EFFORT}" "${PARENT_RUN_ID}" "${RESUMABLE}" timeout --events "${EVENTS}" \
    --strict "${STRICT}" --kind "$(run_kind)" --wrapup-events "${TMP_ROOT}/${RUN_ID}.wrapup.events.jsonl")"
  if [ -n "${FALLBACK_REASON}" ]; then
    RESUMABLE_TEXT='否'
    case "${TIMEOUT_LINE}" in *' resumable=true') RESUMABLE_TEXT='是' ;; esac
    {
      printf 'delegate: 已中止，未取得进度说明（%s）。会话 ID：%s；可续跑：%s。\n' \
        "${FALLBACK_REASON}" "${STOPPED_SESSION:-无}" "${RESUMABLE_TEXT}"
      if [ "${WRITE_MODE}" -eq 1 ]; then
        printf '改动的文件（与运行前比较）：\n'
        CHANGED="$(python3 -B "${SCRIPT_DIR}/run_state.py" changes "${TMP_ROOT}/${RUN_ID}.baseline")"
        printf '%s\n' "${CHANGED:-无}"
      else
        printf '只读运行，不列文件\n'
      fi
    } > "${ANSWER}"
  fi
  cat "${ANSWER}"
  printf '\n---\n'
  printf '模型：%s / 推理档：%s\n' "${MODEL:-配置默认}" "${EFFORT:-配置默认}"
  printf '过程日志（未进入本会话上下文）：%s（%s 字节）\n' "${LOG}" "$(wc -c < "${LOG}" | tr -d ' ')"
  if [ -n "${FALLBACK_REASON}" ]; then
    printf '收尾：兜底（%s）\n' "${FALLBACK_REASON}"
  else
    printf '收尾：收尾轮\n'
  fi
  python3 -B "${SCRIPT_DIR}/run_state.py" usage-line "${TMP_ROOT}" "${EVENTS}" \
    "${TMP_ROOT}/${RUN_ID}.wrapup.events.jsonl" "${PARENT_RUN_ID}"
  RESULT_LINE="${TIMEOUT_LINE}"
  exit 124
fi

if [ "${CODEX_STATUS}" -ne 0 ]; then
  printf 'delegate: codex 执行失败（退出 %s）。过程日志末尾（最后最多 40 行 / 16KiB）：\n' "${CODEX_STATUS}" >&2
  tail -c 16384 "${LOG}" | tail -n 40 >&2
  RECENT_EVENTS="$(python3 -B "${SCRIPT_DIR}/run_events.py" render "${EVENTS}")"
  if [ -n "${RECENT_EVENTS}" ]; then
    printf '最近的事件：\n%s\n' "${RECENT_EVENTS}" >&2
  fi
  printf 'delegate: 完整过程日志：%s；事件流：%s\n' "${LOG}" "${EVENTS}" >&2
  exit "${CODEX_STATUS}"
fi

if [ ! -s "${ANSWER}" ]; then
  RESULT_STATUS='empty'
  printf 'delegate: 产出为空（答复文件缺失或为空）。完整过程日志：%s\n' "${LOG}" >&2
  exit 1
fi

ANSWER_BYTES="$(wc -c < "${ANSWER}" | tr -d ' ')"
LOG_BYTES="$(wc -c < "${LOG}" | tr -d ' ')"
RECORDED="$(python3 -B "${SCRIPT_DIR}/run_state.py" record "${TMP_ROOT}" "${RUN_ID}" "${LOG}" "${ANSWER}" \
  "${REPO_ROOT}" "${WRITE_MODE}" "${MODEL}" "${EFFORT}" "${PARENT_RUN_ID}" "${RESUMABLE}" --events "${EVENTS}" \
  --strict "${STRICT}" --kind "$(run_kind)")"
cat "${ANSWER}"
printf '\n---\n'
printf '模型：%s / 推理档：%s\n' "${MODEL:-配置默认}" "${EFFORT:-配置默认}"
printf '过程日志（未进入本会话上下文）：%s（%s 字节；最终答复 %s 字节）\n' "${LOG}" "${LOG_BYTES}" "${ANSWER_BYTES}"
python3 -B "${SCRIPT_DIR}/run_state.py" usage-line "${TMP_ROOT}" "${EVENTS}" '' "${PARENT_RUN_ID}"
RESULT_LINE="${RECORDED}"
case "${RESULT_LINE}" in
  *' status=timeout '*)
    WRAPUP_MODE='主动停'
    printf '收尾：主动停\n'
    exit 124
    ;;
  *' status=unmarked '*)
    exit 1
    ;;
esac
