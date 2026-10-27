# Specification: run-continue (dispatch the next Task after done)

[简体中文](../../spec/run-continue.md) | English

Drafted 2026-10-27; approved by the user on 2026-10-27, in the user's words: 「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」 — "Approve the five Specs run-result, run-continue, run-longrun, run-check and run-rules, and start the English pages and the Plan." It corresponds to item 1 and decision point 1 of ecosystem proposal S38, which the user approved on 2026-10-27, in the user's words: 「……done 后可续跑（只限 --resumable 链）……」 — "…a run can be continued after done (only for `--resumable` chains)…" (full text in [run-result](SPEC-run-result.md)). Purpose: a module-crew module session uses one Codex session to do several Tasks of a module in turn, with Claude checking and committing between Tasks, so that every Task does not need a fresh session and a fresh read of the project.

## Premises (confirmed by the user on 2026-10-27; the ones this module uses)

- **S1** Additions only; the existing behavior of plain runs, `--resumable` and `--resume` is unchanged.
- **S7** Syntax `--continue <runId> [--write] -- "<next Task>"`:
  - It accepts only a runId on a chain started by `--resumable` whose status is `done`; `needs-input` and `timeout` still use `--resume`.
  - Everything else is as for `--resume`: the same repository root, `--write` matching the original run, model and effort reused, the `.resumed` placeholder ensuring a runId is continued only once, a new runId each round, `parent` pointing to the previous round.
  - The prompt starts with 【下一个任务】 ("next task").
- **S8** Logs and answers are still kept for the latest 50 sets; `.state.json`, `.resumed` and `.result.json` are deleted only 14 days after their last write.

Depends on: [run-resume](SPEC-run-resume.md) (state file, placeholder, refusal table) and [run-result](SPEC-run-result.md) (result file, `kind`, `chainRoot`, usage difference).

## Impact

- **run-resume contract (additions only):** one new resume entry point. The semantics of `--resume`, its refusal table and its answer discipline are unchanged. run-resume's A7 "resume timed-out or failed runs" is out of scope for this module; `--continue` accepts only `done`. The run-resume spec gets one sentence pointing here.
- **A runId has only one successor:** `--resume` and `--continue` share the `<runId>.resumed` placeholder; whoever takes it first wins, so a chain never forks.
- **Cleanup rule:** the keep-50-sets rule no longer deletes state files, placeholder files and result files; they are cleaned by age instead. The parts of run-resume "Retention and cleanup", run-timeout "Retention and cleanup" and run-result "Retention and cleanup" that say state files are deleted together with the log are superseded by this module; each gets one sentence pointing here. State files left by older versions stay readable as before.
- **interface:** adds `run.continue`; existing fields unchanged.

## Tech stack and commands

Same as [run-result](SPEC-run-result.md); one new test file:

```bash
python3 -B plugins/delegate/tests/test-run-continue.py
```

## Project structure

```text
plugins/delegate/scripts/codex-exec.sh          → --continue branch (reuses the --resume execution path, with its own prompt and validation)
plugins/delegate/scripts/run_state.py           → check gains a continue mode; constants and implementation for age-based cleanup
plugins/delegate/scripts/delegate_backend.py    → parse and forward --continue, validate combinations
plugins/delegate/scripts/delegate_capabilities.py → codex gains the continue capability fact
plugins/delegate/interface.json                 → run.continue
plugins/delegate/commands/run.md / help.md      → usage and discipline
plugins/delegate/tests/test-run-continue.py     → new: stub tests
plugins/delegate/tests/test-interface.py        → add run.continue assertions
spec/run-continue.md / docs/en/SPEC-run-continue.md → this contract
spec/run-resume.md, spec/run-timeout.md, spec/run-result.md and their English pages → one sentence each pointing to this module
README (Chinese and English), pending release notes → in sync
```

## Behavior contract

### Syntax

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --continue <runId> [--write] [--strict] -- "<next Task>"
```

- It can be combined with the other 1.3 options: `--strict` (run-result), `--timeout` (run-longrun), `--check` and `--authorized-by` (run-check), `--rules-file` (run-rules).
- It cannot be combined with `--resumable`, `--resume`, `--model`, `--effort`, `--review-context` or `--backend claude-code`; the task text must not be empty. A violation exits 64.

### Validation (Codex is not called, exit 64, stderr `delegate: <reason>`)

The order is the same as for `--resume`, with only the status condition replaced:

| Reason | When |
|---|---|
| `invalid run id` | the runId has the wrong format |
| `run not found` | no state file (a plain run has no state file, so "only chains started by `--resumable`" is guaranteed by this row) |
| `run not resumable` | the state file has no session id |
| `run not done` | the status is not `done` (use `--resume` for `needs-input` and `timeout`; `unmarked` cannot be continued). Failed, interrupted and unreaped (125) runs write no state file and are refused as `run not found` |
| `run already resumed` | the runId has already been continued by `--resume` or `--continue` |
| `repository mismatch` | the current Git root differs from the state file |
| `write mode mismatch` | whether `--write` is given differs from the original run |

When `--resume` meets a runId whose status is `done`, it still refuses with `run not waiting for input`, with the text unchanged; `--help` and `run.md` point the user to `--continue` instead.

### Execution

Exactly the same as resume: `codex exec resume <session id>`, `-c sandbox_mode=…`, fixed `approval_policy="never"`, the trust override in write mode, `--json` (run-result), model and effort reused from the state file, no `--ephemeral`; exclusively create `<runId>.resumed` before calling Codex.

What is sent to Codex (followed by the time-budget paragraph; with `--strict` the end-marker paragraph goes before the time-budget paragraph; with `--rules-file` the rules paragraph goes first, see run-rules):

> [Next task] <task text verbatim>
>
> The previous task has ended. Continue in this session with this new task, following the earlier agreement: first do the parts not affected by pending decisions; when the user must decide, start the first line of your final answer with `NEED_USER:`.

### Result

- A new runId; `parent` in the state file points to the runId being continued, `chainRoot` is inherited, `kind` is `continue`.
- The ending classification is the same as for a resumable run (`done` / `needs-input` / `timeout`, and `unmarked` with `--strict`), and it can be continued again by `--continue` or `--resume`.
- The result file has `kind: "continue"`; `usage.run` is the difference from the parent round, as in run-result.
- Write mode prints the Git acceptance block as usual, with the baseline recorded again before this round starts.

### Retention and cleanup

- Log-type files (`.log`, `.answer`, `.events.jsonl`, `.wrapup`, `.wrapup.answer`, `.wrapup.events.jsonl`, `.baseline`, 0.7.1's `.cleanup`, and run-check's `.check.log` and `.check.cleanup`) are still deleted by "the latest 50 sets". The cleanup outcome of `.cleanup` is already copied into the result file's `cleanup` field, so deleting it with the logs does not affect the chain.
- State-type files (`.state.json`, `.resumed`, `.result.json`) are not deleted by the 50-set rule; they are deleted when their modification time is older than 14 days. The 14 days is a constant defined in one place, and tests read it from there.
- Today's cleanup code is inline in `codex-exec.sh` (0.7.1 has just added `.cleanup` to its suffix list); this module moves the suffix lists and the 14-day constant into `run_state.py`, one table for each kind.
- Cleanup still happens at the end of every run, and a failure does not change the execution status.
- **Known limitation:** for a chain whose logs were deleted by the 50-set rule, `--continue` still works (it needs only the state file), but the process logs of the old rounds can no longer be found.

### Interface (this module's part)

`run` gains:

```json
"continue": {"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable",
             "stateRetentionDays": 14}
```

Consumers check `>=1.3,<2.0` and that `run.continue` exists. `accepts` is an open set; a consumer uses only the values it recognizes.

## Answer and authorization discipline (written into `run.md`)

- The task text of `--continue` must come from a Task in the approved Plan or from the user's own request; delegate cannot verify this, so it is discipline at the command-instruction level.
- The precondition of `--continue --write` is the same as for `--resume --write`: the original run was authorized to write, and the authorization was not withdrawn. Write authorization given in advance is covered by `--authorized-by` in [run-check](SPEC-run-check.md).
- A `done` from the previous round does not mean the previous Task was accepted; checking and committing are still done by the caller, and only then is the next Task dispatched.

## Code style

Same as [run-result](SPEC-run-result.md).

## Testing strategy

`test-run-continue.py` (`unittest`, its own fake codex, temporary Git fixtures) covers:

- the `--continue` argv (`exec resume`, sandbox, `approval_policy`, `--json`, reused model and effort, session id) and the prompt;
- the new runId, `parent`, `chainRoot` and `kind`;
- every row of the validation table exits 64 without calling Codex, including `run not done`;
- when `--resume` and `--continue` race for the same runId, only one succeeds;
- the Git acceptance block in write mode;
- cleanup: log-type files (including `.cleanup`) are deleted by the 50-set rule and state-type files by the 14-day rule (times built with `os.utime`), and `--continue` still works after more than 50 sets.

`test-interface.py` adds `run.continue` assertions. Write the tests first and confirm they fail before implementing.

## Boundaries

- **Always:** the behavior and text of `--resume` are unchanged; `--continue` and `--resume` share the placeholder; keep Chinese and English contracts in sync.
- **Ask first:** continuing an `unmarked` or failed run; allowing `--continue` to change the model or effort; changing the 14-day retention; the paid measurement, commits, pushes and releases.
- **Never:** continue a plain run; let a chain fork; write a Task or answer a question for the user; read or delete Codex session files.

## Success criteria and verification map

- **RC-01:** `--continue` on a `done` runId calls `codex exec resume` with arguments identical to a resume, and the prompt is the 【下一个任务】 ("next task") version (stub tests).
- **RC-02:** the new runId, `parent`, `chainRoot` and `kind: "continue"` are correct, and the result file's `usage.run` is the difference (stub tests).
- **RC-03:** every row of the validation table exits 64 without calling Codex (stub tests).
- **RC-04:** `--resume` and `--continue` share the placeholder, and a runId can be continued only once (stub tests).
- **RC-05:** write mode prints the Git acceptance block (stub tests).
- **RC-06:** state-type files are cleaned by the 14-day rule and log-type files by the 50-set rule; `--continue` still works after the logs are cleaned (stub tests).
- **RC-07:** `interface.json` contains `run.continue`; existing fields are unchanged; both plugin validate runs pass.
- **RC-08:** `run.md`, `help.md`, both READMEs, both contracts, the pointer sentences and the pending release notes are in sync, including the three discipline points.
- **RC-09:** full validation, both plugin validate runs and `git diff --check` pass.

## Open questions

- Context compaction in long chains: measurement T2 shows that Codex compacts automatically at about 94% of the window, transparently to the caller, and this module does not manage context; under D1 (see run-result), 1.3 does not read session files, so compaction cannot be observed in 1.3.
- Whether 14 days is enough: estimated from the typical cycle of a module, with no data; adjust it later from the module-crew pilot (Ask first).
