# Specification: run-longrun (`--timeout` lifts the deadline)

[简体中文](../../spec/run-longrun.md) | English

Drafted 2026-10-27; approved by the user on 2026-10-27, in the user's words: 「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」 — "Approve the five Specs run-result, run-continue, run-longrun, run-check and run-rules, and start the English pages and the Plan." It corresponds to item 2 and decision point 2 of ecosystem proposal S38, which the user approved on 2026-10-27, in the user's words: 「……A7 只放开期限、用 --timeout 轻方案……」 — "…A7 only lifts the deadline, using the light `--timeout` option…" (full text in [run-result](SPEC-run-result.md)). A module's Task can run for ten-odd minutes, and today's 540-second cap forcibly stops it.

## Premises (confirmed by the user on 2026-10-27; the ones this module uses)

- **S1** Additions only; the default deadline is still 540 seconds, and `DELEGATE_TIMEOUT_SECONDS` can still only shorten the default deadline.
- **S9** `--timeout <seconds>` can only enlarge the deadline, in the range 541–7200. Beyond 540 seconds the caller must invoke it in the host's background mode; delegate does not manage background processes and has no detach, status or cancel. The main run, the wrap-up round and the threshold are still computed with the same formulas as in run-timeout.
- **S10 (revised per D2)** Orphan-process cleanup is fixed separately by delegate 0.7.1 (on abort, reap the descendant process groups Codex started, put a limit on the final `wait()`, report the cleanup result truthfully). This module builds on 0.7.1 and designs no cleanup of its own. The user's words: 「D2 确认：孤儿清理先由 0.7.1 单独修，1.3 以它为前提。」 — "D2 confirmed: orphan cleanup is fixed separately in 0.7.1 first, and 1.3 builds on it."

Depends on: [run-timeout](SPEC-run-timeout.md) (deadline formulas, time-budget paragraph, wrap-up round, fallback), [run-result](SPEC-run-result.md) (result file), and delegate 0.7.1's cleanup fix (merged into main as `64d7ece`, channel spec revision S41).

## Why 0.7.1 is a prerequisite

The root-cause investigation of measurements T5 and T5b ([record](../verification/2026-10-27-delegate-s38-probe.md)) found two things:

- Shell commands run by Codex live in a new session and process group. When delegate aborts Codex, Codex itself exits but does not reap the command it is running, so the command becomes an orphan and keeps running.
- Once, `run_codex.py` did not exit for 60 seconds after receiving SIGTERM; the root cause was not located, and the most likely place is the final `wait()` that has no upper limit.

The longer the deadline, the more likely a long command (a test, a build) happens to be running at the moment of the abort. So cleanup has to be reliable before the deadline is lifted. 0.7.1 fixed the former (on abort it freezes Codex, snapshots descendants and reaps by process group, and commands that changed session are covered too) and put a limit on the latter (it waits at most 5 seconds for the direct child and exits 125 if reaping fails; when the wrapper is interrupted it waits at most 15+2 seconds). The real root cause of the "60 seconds without exiting" is still not located, but it can no longer hang the host indefinitely.

## Impact

- **run-resume A7 (only half lifted):** A7's original text "not doing: a background daemon…; changing the 540-second deadline…" is revised to: the default deadline is still 540 seconds and only an explicit `--timeout` can enlarge it; "delegate does not manage background processes" stays. The run-resume spec gets one entry in its revision history pointing to this module, recording the user's words.
- **run-timeout T6 (additions only):** "the overall deadline stays 540 seconds; `DELEGATE_TIMEOUT_SECONDS` can only shorten it" becomes "without `--timeout`, …"; with `--timeout`, `T` takes that value. Formulas and constants are unchanged. The run-timeout spec gets one sentence pointing here.
- **channel:** "deadline default/maximum 540 seconds" becomes "default 540 seconds; the maximum can only be raised to 7200 seconds by `--timeout`", with one sentence pointing here.
- **The 600-second Bash limit:** the caller's responsibility. delegate cannot know whether it runs in the background, so it does no detection; `run.md` states that in a foreground call `--timeout` must not exceed the host Bash's deadline.

## Tech stack and commands

Same as [run-result](SPEC-run-result.md); one new test file:

```bash
python3 -B plugins/delegate/tests/test-run-longrun.py
```

## Project structure

```text
plugins/delegate/scripts/codex-exec.sh          → parse --timeout, compute T; the rest of the flow is unchanged
plugins/delegate/scripts/run_state.py           → deadlines accepts a T of 541–7200 (formulas unchanged)
plugins/delegate/scripts/delegate_backend.py    → parse and forward --timeout, validate the range and combinations
plugins/delegate/scripts/delegate_capabilities.py → codex gains the longRun capability fact
plugins/delegate/interface.json                 → run.longRun
plugins/delegate/commands/run.md / help.md      → usage, background-call requirement
plugins/delegate/tests/test-run-longrun.py      → new: stub tests + fake-endpoint real-machine cleanup test
plugins/delegate/tests/test-interface.py        → add run.longRun assertions
spec/run-longrun.md / docs/en/SPEC-run-longrun.md → this contract
spec/run-resume.md, spec/run-timeout.md, spec/channel.md and their English pages → pointer sentences and revision history
README (Chinese and English), pending release notes → in sync
```

## Behavior contract

### Syntax and validation

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --timeout <seconds> [other options] -- "<task>"
```

- Usable with a plain run, `--resumable`, `--resume` and `--continue`. Each call gives its own value; it is not inherited along the chain.
- The value must be a decimal integer in the range 541–7200; otherwise exit 64 with stderr `delegate: --timeout must be an integer between 541 and 7200`.
- Without `--timeout` the behavior is exactly the same as today.

### Deadline

- With `--timeout`, `T` takes that value and `DELEGATE_TIMEOUT_SECONDS` is ignored; without it, as today.
- By run-timeout's formulas: `W = min(45, T // 6)`, `M = T − W`, `S = max(M − 90, M // 2)`. For example with `T = 1800`: `W = 45`, `M = 1755`, `S = 1665`. The constants are unchanged.
- The time-budget paragraph, wrap-up round, fallback, ending statuses and exit codes are all the same as in run-timeout, only with larger numbers.
- Process cleanup on abort uses 0.7.1's implementation entirely; this module does not change `run_codex.py`'s cleanup logic. The main run and the wrap-up round are still each invoked through `run_codex.py --report <runId>.cleanup <deadline>`, with the deadline argument being `M` and `W` respectively.
- **Wall-clock upper bound:** one run takes at most about `T + 30` seconds. The part beyond `T` comes from two abort cleanups (about 13 seconds at most each: up to 5 seconds to list processes, 2 seconds of grace, 5 seconds to reap, 1 second to check for leftovers) and the wrapper's wrap-up. The waiting limit the caller gives a background task should be no less than this.
- **Exit 125:** if reaping fails after an abort under a long deadline, the same as 0.7.1: exit 125, no result line, and the result file status is `unreaped` (see run-result).

### Result

- The result file gains `"timeoutSeconds": <T>`; without `--timeout` it is the default computed `T` (540 today), so every result shows its deadline.
- When aborted, the `cleanup` field is filled from 0.7.1's report (see run-result).
- The metadata block is unchanged.

### Background-call requirement (written into `run.md`)

- When `--timeout` is larger than the host's foreground command deadline (Claude Code's foreground Bash limit is 600 seconds), call it in the host's background mode and wait for the host's completion notification instead of polling.
- delegate provides no background start, query or cancel; to stop a run, stop that host background task, and delegate handles it as a received signal (exit 143 / 130 / 129; 0.7.1 takes care of reaping the processes).
- After it ends, read the result file from `delegate: result=<path>`.

### Interface (this module's part)

`run` gains:

```json
"longRun": {"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540,
            "background": "caller"}
```

`background: "caller"` means the caller is responsible for the background. Consumers check `>=1.3,<2.0` and that `run.longRun` exists.

## Code style

Same as [run-result](SPEC-run-result.md).

## Testing strategy

- **Stub tests (`test-run-longrun.py`):**
  - argument validation: 540, 7201, non-integers, negative numbers and an empty value all exit 64 without calling Codex;
  - the choice of `T`: with `--timeout` the environment variable is ignored, without it as today;
  - `W`, `M` and `S` reach the prompt and the deadline argument of `run_codex.py` (using the actual argv recorded by the stub, not by comparing source text);
  - `timeoutSeconds` is written into the result file.
- **Cleanup under long deadlines is not tested separately:** 0.7.1 has no deadline-scaling hook and this module adds none. Cleanup behavior does not depend on how long the deadline is; it is covered by 0.7.1's `test-reap-fake-endpoint.py` (real Codex against the local fake endpoint) and `test-channel-regressions.py`, and this module only requires that they keep passing. This module uses a stub to assert that the `M` and `W` computed from `--timeout` reach the arguments of `run_codex.py --report … <deadline>` unchanged, and does not run a real wait of more than 541 seconds.
- `test-interface.py` adds `run.longRun` assertions. Write the tests first and confirm they fail before implementing.

## Boundaries

- **Always:** without `--timeout` it is identical to today; cleanup uses only 0.7.1's implementation; keep Chinese and English contracts in sync.
- **Ask first:** changing the 7200 upper limit; changing the formulas or constants under `--timeout`; delegate managing background processes itself; the paid measurement, commits, pushes and releases.
- **Never:** relax the default 540 seconds; change 0.7.1's cleanup flow or constants; fork or detach processes itself.

## Success criteria and verification map

- **RL-01:** an out-of-range or non-integer `--timeout` exits 64 without calling Codex (stub tests).
- **RL-02:** with `--timeout`, `T` takes that value, and `W`, `M` and `S` reach the prompt and deadline arguments by the formulas; without it, identical to today (stub tests).
- **RL-03:** the result file contains `timeoutSeconds`; when aborted, `cleanup` is filled as in 0.7.1 (stub tests).
- **RL-04:** the `M` and `W` computed from `--timeout` reach `run_codex.py --report <runId>.cleanup <deadline>`; 0.7.1's reaping regressions (`test-reap-fake-endpoint.py`, `test-channel-regressions.py`) keep passing (stub tests + existing regressions).
- **RL-05:** `interface.json` contains `run.longRun`; existing fields are unchanged; both plugin validate runs pass.
- **RL-06:** the run-resume revision history (A7 lifts only the deadline), the pointer sentences in run-timeout and channel, `run.md`, `help.md`, both READMEs, both contracts and the pending release notes are in sync, including the background-call requirement.
- **RL-07:** full validation, both plugin validate runs and `git diff --check` pass.

## Open questions

- Checked against 0.7.1 (`64d7ece`): the cleanup flow, the `--report` file, exit 125 and the wrapper's 15+2 second limit agree with this spec; 0.7.1 has no deadline-scaling hook, so cleanup under long deadlines is covered by the existing regressions (see Testing strategy).
- The 7200-second cap is estimated for "one Task" with no data; adjust it later from the pilot (Ask first).
- Under a long deadline the wrap-up round's context is larger and wrapping up may take longer (run-timeout H3 is still unverified); the wrap-up deadline is still 45 seconds, and a failure goes to the fallback without affecting the overall deadline.
