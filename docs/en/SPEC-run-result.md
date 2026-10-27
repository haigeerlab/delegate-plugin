# Specification: run-result (structured result file, `--strict` and cost data)

[简体中文](../../spec/run-result.md) | English

Drafted 2026-10-27; approved by the user on 2026-10-27, in the user's words: 「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」 — "Approve the five Specs run-result, run-continue, run-longrun, run-check and run-rules, and start the English pages and the Plan." Prompted by ecosystem proposal S38 (handing a whole module over to Codex), which the user approved on 2026-10-27, in the user's words: 「S38 接口方案：假设全部确认，五个决定点按推荐批准——done 后可续跑（只限 --resumable 链）；A7 只放开期限、用 --timeout 轻方案；写入授权按有条件折中；1.3 一次到齐必须五项，1.4 做回滚与并发额度，第 10 项暂缓；授权 delegate-owner 先做 T1～T5 付费实测再写 Spec。」 — "S38 interface proposal: all assumptions confirmed, the five decision points approved as recommended — a run can be continued after done (only for `--resumable` chains); A7 only lifts the deadline, using the light `--timeout` option; write authorization takes the conditional compromise; 1.3 must deliver all five items at once, 1.4 does rollback and the concurrency quota, item 10 is deferred; delegate-owner is authorized to run the paid measurements T1–T5 before writing the Spec." This module corresponds to proposal item 3 (structured result) and item 8 (cost data) and is the first of the five 1.3 modules: the other four ([run-continue](SPEC-run-continue.md), [run-longrun](SPEC-run-longrun.md), [run-check](SPEC-run-check.md), [run-rules](SPEC-run-rules.md)) all add fields to this module's result file.

It rests on the [S38 pre-measurements](../verification/2026-10-27-delegate-s38-probe.md) (T1: `--json` event fields; T2: token counts are session-cumulative values).

## Premises (the user confirmed S1–S15 on 2026-10-27; the ones this module uses)

The user's words: 「D2 确认：孤儿清理先由 0.7.1 单独修，1.3 以它为前提。5 个模块拆分和 S1～S15 假设（S10 按 0.7.1 改）全部确认，开始插能力图并写 Spec。」 — "D2 confirmed: orphan cleanup is fixed separately in 0.7.1 first, and 1.3 builds on it. The five-module split and assumptions S1–S15 (S10 changed per 0.7.1) are all confirmed; start inserting into the capability map and writing the Specs."

- **S1** 1.3 is additions only: `run.write: "explicit"`, plain runs keeping `--ephemeral`, the 540-second default deadline, existing exit codes and the existing result line stay unchanged; the result line is still the last line of stdout. New capabilities take effect only through explicit arguments; only S3 and S4 apply to every run.
- **S2** This module moves `interface` to `1.3`; each of the other four modules adds its own capability marker; nothing is released until all five modules are done.
- **S3** Every run path adds `--json` when it calls Codex.
- **S4** Every run writes a result file, and stdout gets one more line `delegate: result=<path>` before the result line.
- **S5** The result file's fields are given below; tokens are recorded as "this run" and "whole session", where this run = this run's cumulative value − the parent run's cumulative value; values are never accumulated along the parent chain.
- **S6** `--strict`: the first line must be an end marker; a missing one is judged `unmarked` with exit code 1.
- **S14** Verification has three layers: stub tests; free tests that drive the real Codex against a local fake Responses endpoint; one paid measurement (a gate, separately authorized).
- **S15** This round of writing the Spec and Plan changes only `spec/`, `tasks/` and `docs/`: no product code, no model calls, no commits.

## Decisions already made

### D1: 1.3 does not read Codex's own session files (decided)

Chosen by the user in this session on 2026-10-27, in the user's words: 「D1 选 A：1.3 不读 Codex 会话文件，额度读取留给 1.4 的 doctor.quota。」 — "D1 option A: 1.3 does not read Codex session files; quota reading is left to 1.4's doctor.quota."

The measurements (T1, T2) show that context usage (`last_token_usage.input_tokens` and `model_context_window`), context compaction (`type: "compacted"` records), and quota and rate limits (`rate_limits`) exist only in Codex's session files, not in the `--json` event stream. Under D1:

- The result file uses only the `--json` event stream and delegate's own timing; context usage, compaction and quota never appear in it.
- run-resume's Never rule "read or delete Codex session files" is unchanged.
- Quota reading is left to be designed together with 1.4's `doctor.quota`; in 1.3, module-crew sees no signal that the context is nearly full or that a rate limit is near.

The other option at the time (read-only, take only the listed fields, and revise run-resume's Never rule) was not adopted.

### D2: where orphan-process cleanup lives (decided)

Confirmed by the user in this session on 2026-10-27 (words quoted above under "Premises"): orphan cleanup is fixed separately in delegate 0.7.1 first, and 1.3 builds on 0.7.1. 0.7.1 is merged into main and released (`64d7ece`, tag `v0.7.1`, channel spec revision S41). This module follows its actual implementation:

- On abort (deadline or TERM/INT/HUP), `run_codex.py` freezes Codex, snapshots its descendants, and reaps them by process group; it waits at most 5 seconds for the direct child. If reaping fails it reports `delegate: 执行进程未能回收，PID=<pid>` ("execution process could not be reaped, PID=<pid>") and **exits 125**; the wrapper treats that as an ordinary execution failure and prints no result line.
- The cleanup report is written to `<runId>.cleanup` and forwarded to stderr by the wrapper; `.cleanup` is already covered by the keep-50-sets rule.
- When `codex-exec.sh` is interrupted it sends TERM to the execution process and waits up to 15 seconds, then KILLs and waits up to 2 seconds; a forced end is reported on one more line.

This module records these in the result file (`status: "unreaped"`, the `cleanup` field) and does not change the cleanup flow itself.

## Impact

- **The process log becomes two files:** today Codex's stdout and stderr both go to `<runId>.log`. With `--json`, the event stream goes to `<runId>.events.jsonl` and stderr still goes to `<runId>.log`. The "end of the process log" printed on failure now comes from the stderr file, followed by up to 10 rendered events (see "Failure diagnostics"). The upgrade notes must say so: people and scripts that read the log text will see different content. The log is not part of the external contract, so the interface is unaffected.
- **Where the session id comes from:** with `--json` on, the log no longer has the `session id: <uuid>` line; the id is taken from `thread_id` of the first `thread.started` event. run-resume's "the session id is taken from the first `session id: <uuid>` line in the process log" and run-timeout's wrap-up round "reuses `session_id_from_log`" are superseded by this module; each gets one sentence pointing here.
- **One more stdout line:** on success, `needs-input`, `timeout` and `unmarked`, a line `delegate: result=<path>` comes before the result line. The result line's format and position are unchanged.
- **New status `unmarked`:** appears only with an explicit `--strict`. 1.2 already states that statuses are an open set and that an old consumer meeting an unknown status must treat it as a failure; its exit code is also 1.
- **Wrap-up round:** also gets `--json`; its events go to `<runId>.wrapup.events.jsonl`.
- **Output of `run_codex.py`:** since 0.7.1 it writes the cleanup report to its own stderr and to the `--report` file. After the split, its stderr goes into `<runId>.log` together with Codex's stderr; the events file receives only Codex's stdout.
- **review is out of scope:** the Codex-backend review gets no `--json` and writes no result file.

## Tech stack and commands

Bash 3.2 wrapper, Python 3 standard library, Git, Codex CLI 0.162.1 (the measured version). No new dependency, hook or command entry.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-run-result.py
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-run-timeout.py
python3 -B plugins/delegate/tests/test-interface.py
/bin/bash plugins/delegate/tests/test-channel.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/codex-exec.sh          → add --json and --strict, separate the event stream from stderr, write the result file, print one more result= line
plugins/delegate/scripts/run_events.py          → new: parse the event stream (thread_id, commands and exit codes, turn.completed usage, last reply)
plugins/delegate/scripts/run_state.py           → session id now from the event stream; state file gains usageTotal; classification gains DONE: and unmarked; result file writing
plugins/delegate/scripts/delegate_backend.py    → parse and forward --strict
plugins/delegate/scripts/delegate_capabilities.py → codex gains the result capability fact
plugins/delegate/interface.json                 → interface 1.3, run.result, run.usage
plugins/delegate/commands/run.md / help.md      → result file, --strict, upgrade notice
plugins/delegate/tests/test-run-result.py       → new: stub tests
plugins/delegate/tests/fake-responses.py        → new: the local fake Responses endpoint extracted from test-reap-fake-endpoint.py, with a "reply with an answer" mode added
plugins/delegate/tests/test-reap-fake-endpoint.py → switch to the shared fake endpoint; assertions unchanged
plugins/delegate/tests/test-interface.py        → add 1.3 assertions
plugins/delegate/README.md / README.en.md       → a result file section; external interface section gains 1.3
spec/run-result.md / docs/en/SPEC-run-result.md → this contract
spec/run-resume.md, spec/run-timeout.md, spec/channel.md and their English pages → one sentence each pointing to this module
docs/releases/unreleased.md and its English page → pending release notes
```

## Behavior contract

### Codex invocation

Plain run, resumable run, resume and wrap-up round all gain one `--json` after the existing arguments and before `-o`. All other arguments are unchanged (including the plain run's `--ephemeral`, `approval_policy="never"`, the trust override and stdin=/dev/null). Redirection becomes:

```bash
python3 -B run_codex.py --report "${CLEANUP}" "${MAIN_SECONDS}" env … codex "${CODEX_ARGS[@]}" \
  >"${TMP_ROOT}/${RUN_ID}.events.jsonl" 2>"${LOG}" </dev/null
```

The final answer is still taken from the `-o` file (measured in T1: identical, character for character, to the last `agent_message.text`).

### Event parsing (`run_events.py`)

Read the events file line by line; lines that are not JSON are skipped without error:

| What to take | From which event | Notes |
|---|---|---|
| Session id | `thread_id` of the first `{"type":"thread.started"}` | when missing, `resumable=false`, the same degradation as today |
| Commands | `type == "item.completed"` with `item.type == "command_execution"` | take `item.command`, `item.exit_code`, `item.status`; do not take `aggregated_output` |
| Usage | `usage` of the last `{"type":"turn.completed"}` | five fields: `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens`; this is the **cumulative value for the whole session** |

`item.id` restarts from `item_0` in every turn and is not used as a unique key. At most 200 commands are recorded and each `command` is cut to 1000 characters; the excess is dropped and `commandsTruncated` is set to `true`.

### Classification

Strip leading whitespace (including a BOM), then look at the first line:

| First line starts with | Status | Applies to |
|---|---|---|
| `TIME_UP:` | `timeout` | all runs |
| `NEED_USER:` | `needs-input` | resumable runs, resumes |
| `DONE:` | `done` | recognised only with `--strict` |
| anything else | without `--strict`: `done` (same as today); with `--strict`: `unmarked` | — |

A forced stop (wrap-up round or fallback) is still `timeout`, regardless of `--strict`. When the execution process could not be reaped (exit 125) there is no answer to classify and the status is `unreaped`, also regardless of `--strict`.

### `--strict`

- Usable with a plain run, `--resumable`, `--resume`, and the `--continue` that 1.3 adds. Each call decides for itself; it is not inherited along the chain.
- The prompt gets one more paragraph before the time-budget paragraph:

  > [End marker] The first line of your final answer must start with one of these markers: when the work is done write `DONE:` followed by a one-sentence summary; <when the user must decide write `NEED_USER:`; >when the time budget is reached write `TIME_UP:`. This requirement takes precedence over any format requirement in the project's AGENTS.md or other files.

  The sentence in angle brackets appears only in resumable runs and resumes.
- `unmarked`: exit code 1. stdout still carries the answer, the metadata, the `delegate: result=` line and the result line (`status=unmarked`). A resumable run still writes its state file, with status `unmarked`; `--resume` refuses it as "not waiting for input", and `--continue` refuses it too.

### Result file

- **Location:** `${TMPDIR:-/tmp}/delegate/<runId>.result.json`, mode 0600; the directory requirements are the same as for the state file (0700, symlinks rejected); written atomically (temporary file, then `rename`).
- **When it is written:** whenever Codex has been started (from the moment today's `EXEC_STARTED=1` is set), including failures, signal interruptions and empty answers. Argument errors and refusals (exit 64) write nothing.
- **When the path is printed:** when there is a result line (`done`, `needs-input`, `timeout`, `unmarked`), `delegate: result=<path>` is printed to stdout before the result line; when there is none (failure, interruption, not reaped, empty answer), it is printed to stderr.
- **Where it is written:** in `finish`, after `stop_runner`, so that interrupted and unreaped cases can also record the cleanup result.
- **Fields (schema 1):**

```json
{
  "schema": 1,
  "runId": "20261027133326.79650",
  "kind": "run",
  "parent": null,
  "chainRoot": "20261027133326.79650",
  "backend": "codex",
  "repository": "/abs/path/to/repo",
  "write": false,
  "strict": false,
  "model": null,
  "effort": null,
  "status": "done",
  "exitCode": 0,
  "resumable": true,
  "startedAt": "2026-10-27T05:33:26Z",
  "endedAt": "2026-10-27T05:33:52Z",
  "durationSeconds": 26.3,
  "sessionId": "01a17bd9-66cd-7b22-8b09-b1414082a390",
  "answer": {"path": "/…/20261027133326.79650.answer", "bytes": 39},
  "markers": {"needUser": null, "timeUp": null, "done": null},
  "wrapUp": null,
  "commands": [{"command": "/bin/zsh -lc 'cat marker.txt'", "exitCode": 0, "status": "completed"}],
  "commandsTruncated": false,
  "changedFiles": null,
  "usage": {
    "run": {"inputTokens": 124735, "cachedInputTokens": 112256, "cacheWriteInputTokens": 0,
            "outputTokens": 391, "reasoningOutputTokens": 0},
    "session": {"inputTokens": 124735, "cachedInputTokens": 112256, "cacheWriteInputTokens": 0,
                "outputTokens": 391, "reasoningOutputTokens": 0},
    "note": null
  },
  "cleanup": null,
  "logs": {"events": "/…/<runId>.events.jsonl", "stderr": "/…/<runId>.log"}
}
```

Field notes:

- `kind`: `run` (plain, or the start of a resumable chain) or `resume`; run-continue adds `continue`.
- `chainRoot`: the runId at the head of the chain. For a plain run and for a run that starts a resumable chain it equals its own runId; a resume inherits the value from the parent run's state file.
- `status`: when there is a result line it matches the result line; when there is none it is `failed` (Codex exited non-zero), `interrupted` (signal 129/130/143), `unreaped` (exit 125, the execution process could not be reaped) or `empty` (empty answer). The exit code is whatever `exitCode` says: for example, if a run is aborted at the deadline and then cannot be reaped, the exit code is 125, not 124, and the status is `unreaped`. This is an open set; a consumer meeting an unknown value must treat it as a failure.
- `markers`: the original text after the corresponding marker, or `null` if absent. `done` is filled only with `--strict`.
- `wrapUp`: when forcibly stopped, `{"mode": "收尾轮"|"兜底", "reason": <fallback reason or null>}` (`收尾轮` = wrap-up round, `兜底` = fallback); when the model itself wrote `TIME_UP:`, `{"mode": "主动停", "reason": null}` (`主动停` = stopped on its own); otherwise `null`.
- `changedFiles`: in write mode, the porcelain lines that are new or differ in content compared with the baseline taken before the run (the same algorithm as the run-timeout fallback, so write mode now records a baseline snapshot before every run, not only for timeouts); `null` in read-only mode.
- `usage.session`: the cumulative value of this run's last `turn.completed`; the wrap-up round is in the same session, so take the later one of the main run and the wrap-up round. `null` when there is no `turn.completed` at all (for example the run was killed midway).
- `usage.run`: this run's usage. For a plain run and for a run that starts a resumable chain it equals `usage.session`; for a resume it is `usage.session` minus the `usageTotal` in the parent run's state file. It is `null` when the parent's value is missing or this run's `session` is `null`, and `note` states the reason (「父轮用量未知」 — "the parent round's usage is unknown", or 「本次没有完成的轮次」 — "this run has no completed turn"). **The total usage of a whole chain is the last run's `usage.session`; do not add up the `session` values of the rounds.**
- `cleanup`: `null` when no abort happened and the wrapper did not force-end the execution process. Otherwise:

  ```json
  {"file": "/…/<runId>.cleanup", "lines": ["delegate: 清理：中止前 Codex 的后代进程 2 个：…", "delegate: 清理：中止后无残留"],
   "leftoverPids": [], "unreapedPid": null, "wrapperForced": false}
  ```

  (The `lines` examples read "cleanup: 2 descendant processes of Codex before the abort: …" and "cleanup: nothing left after the abort".) `lines` are the original lines of the `.cleanup` file (the reports of both the main run and the wrap-up round are in it), plus the lines the wrapper prints in `stop_runner`. `leftoverPids` comes from the line 「中止后仍有残留，PID=…」 ("still left after the abort, PID=…"), `unreapedPid` from the line 「执行进程未能回收，PID=…」 ("execution process could not be reaped, PID=…"), and `wrapperForced` records that the line 「执行进程超时未退出，已强制结束」 ("execution process did not exit in time and was force-ended") appeared. When parsing finds nothing, the field is empty or `null` and `lines` is kept as is. Leftovers after KILL are only reported and do not change the exit code, as in 0.7.1.
- Fields added by other modules: `authorization` and `check` (run-check), `rules` (run-rules), `timeoutSeconds` (run-longrun). A module's fields do not appear if that module is not used.

### State file

The state file of a resumable run or resume (`schema` still 1, a private file) gains `usageTotal` (this run's `usage.session`, may be `null`), `chainRoot` and `strict`. When an old state file lacks these fields they are treated as `null`, and `--resume` keeps working.

### Failure diagnostics

When Codex exits non-zero, stderr still first prints "the end of the process log (at most the last 40 lines / 16KiB)", taken from `<runId>.log` (stderr). It then appends "Recent events:" with at most 10 entries, chosen from the end of the event stream, only `type == "error"`, `item.type == "error"` and `command_execution`, each rendered as one line (for example `命令 /bin/zsh -lc '…' 退出 1`, meaning "command … exited 1"). The last line is still the full log path, now with the event stream path added.

### Metadata block

Unchanged, except that the success path gets one more line at the end (before the result line and the `result=` line):

```text
用量：本次输入 124,735（缓存 112,256）/ 输出 391；整个会话输入 124,735
```

(Gloss: "usage: this run input 124,735 (cached 112,256) / output 391; whole session input 124,735".) When usage is `null` it reads 「用量：未知（<note>）」 ("usage: unknown (<note>)").

### Retention and cleanup

When the keep-50-sets rule deletes a set, it also deletes `.events.jsonl`, `.wrapup.events.jsonl` and `.result.json`. (run-continue changes the state file and result file to time-based retention; see that module.)

### Interface 1.3 (this module's part)

`interface` becomes `"1.3"`, and `run` gains:

```json
"result": {"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict",
           "statuses": ["done", "needs-input", "timeout", "unmarked", "failed", "interrupted", "unreaped", "empty"]},
"usage": {"in": "result.usage", "cumulative": "session", "perRun": "run"}
```

No other existing field is removed or changed. Consumers check `>=1.3,<2.0` and that `run.result` exists to decide whether they can read the result file. The complete 1.3 after all five modules is summarized at the end of [run-rules](SPEC-run-rules.md).

## Code style

Same as run-resume: Bash 3.2 compatible, `${VAR}`, the existing empty-array guard; Python standard library, 4-space indentation, snake_case; JSON always produced by a serializer, never parsed in shell. Existing example (`run_state.py`):

```python
def classify(answer, resumable=True):
    text = answer.lstrip().lstrip('﻿').lstrip()
    if text.startswith(TIME_UP):
        return 'timeout', text[len(TIME_UP):].strip()
```

## Testing strategy

- **Stub tests (`test-run-result.py`, `unittest`):** use their own fake codex (written like test-run-timeout's) that writes preset JSONL and `-o` files according to the arguments. Coverage:
  - the argv of every run path contains `--json`, and a plain run's other arguments are identical item by item to before the change;
  - the event stream and stderr land in separate files;
  - the session id is taken from `thread_id`, with degradation when it is missing;
  - extraction of commands, exit codes and usage, skipping of non-JSON lines, truncation at 200 commands and 1000 characters;
  - every row of the classification table, including `unmarked` under `--strict` exiting 1;
  - for every kind of ending: the result file fields, 0600 permissions, atomic writing, and where the `result=` line goes, including `unreaped` with exit 125 and parsing of the `cleanup` field (with the original 0.7.1 report text as fixtures);
  - a resume's `usage.run` is the difference, and `null` when the parent's value is missing;
  - rendering of the failure diagnostics;
  - cleanup covers the new files.
- **Free real-machine test:** follow 0.7.1's `test-reap-fake-endpoint.py` (a local fake Responses endpoint, a temporary `CODEX_HOME`, no credentials sent or read, skipped when `codex` is absent). Extract the fake endpoint into the shared `fake-responses.py`, add a "reply with an answer" mode, and drive the real Codex through a plain run and a resumable run to confirm the event fields match the table above and that 0.7.1's reaping regression still passes.
- **`test-interface.py`:** `interface == "1.3"`, `run.result` and `run.usage` exist; existing assertions are unchanged.
- Write the tests first and confirm they fail before implementing.

**Paid measurement (a gate, separately authorized):** once all five modules are done, run it once with a real model for all of them (see run-rules, "1.3 combined measurement"); it is not run separately in this module.

## Boundaries

- **Always:** a plain run keeps its arguments and prompt apart from `--json` and the result file, guarded by tests; the result line stays the last line of stdout; keep Chinese and English contracts in sync; change `interface.json`, capability facts and tests together.
- **Ask first:** writing command output into the result file; changing the result line's format; the paid measurement, commits, pushes and releases.
- **Never:** change `review.command` or `doctor.command`, or bump the major version; write account information, credentials or the full conversation into the result file; read or delete Codex session files (D1); write the result file or state file into the business repository.

## Success criteria and verification map

- **RS-01:** the Codex arguments of every run path contain `--json`; a plain run's other arguments and `--ephemeral` are unchanged (stub tests).
- **RS-02:** the event stream goes to `.events.jsonl` and stderr to `.log`; the session id comes from `thread_id`, and `resumable=false` when it cannot be taken (stub tests).
- **RS-03:** commands, exit codes and usage are extracted as in the table above, non-JSON lines are skipped, and the truncation rules apply (stub tests).
- **RS-04:** every row of the classification table; with `--strict` a missing marker gives `unmarked`, exit 1, and the result line as usual (stub tests).
- **RS-05:** the result file is written for every kind of ending (including `unreaped` with exit 125 and `cleanup`), its fields match the example, 0600, atomic writing; nothing is written on a refusal (stub tests).
- **RS-06:** the `delegate: result=` line comes before the result line, the result line is still the last line, and when there is no result line the path is printed to stderr (stub tests).
- **RS-07:** `usage.run` is the difference, and `null` with a `note` when the parent's value is missing or this run had no completed turn (stub tests).
- **RS-08:** failure diagnostics contain the end of stderr and at most 10 rendered events (stub tests).
- **RS-09:** cleanup covers the added files (stub tests).
- **RS-10:** the fake endpoint driving the real Codex gives event fields consistent with the implementation; 0.7.1's reaping regression still passes (free real-machine test).
- **RS-11:** `interface.json` is 1.3 with `run.result` and `run.usage`; existing fields are unchanged; both plugin validate runs pass.
- **RS-12:** `run.md`, `help.md`, both READMEs, both contracts, the pointer sentences and the pending release notes are in sync, including the upgrade notice on "the log becomes two files", "the result line" and "`unmarked`".
- **RS-13:** full validation, both plugin validate runs and `git diff --check` all pass; existing test assertions are not changed (assertions that must be updated because of `--json` are listed one by one in the Plan with an explanation).

## Open questions

- Checked against 0.7.1 (`64d7ece`): the `cleanup` field takes the `.cleanup` original text and the wrapper's report lines directly, with no separate format; exit 125 is recorded as `unreaped`.
- Existing tests that assert Codex arguments equal item by item will fail because of the added `--json`. This is an intended argument change; the Plan lists each assertion to update, and it does not count as "weakening assertions".
