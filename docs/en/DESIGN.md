# delegate: design and boundaries

[简体中文](../../DESIGN.md) | English

Run execution and investigation for a settled approach through a separate Codex CLI invocation, returning only the final answer to Claude Code. The main session handles requirements, trade-offs, authorization, and verification. Separate execution reduces the process-log volume carried by that session, without guaranteeing lower total token usage or cost.

## Are the decisions settled?

Suitable work includes reviews, exploration across files, reproduction and diagnosis, a single task with a settled approach, and mechanical changes. If trade-offs or scope remain unresolved, keep the judgment in the main session. Writing files requires explicit user authorization in the current turn.

```text
SessionStart → refresh basic-readiness cache (no context output)
UserPromptSubmit → sequentially warm cache → inject confirmation rules and skill pointer if ready
Claude proposes a specific task → user confirms → command → wrapper checks authentication again
→ check Git working tree → codex exec in a new process group → answer / failure diagnostics
→ emit Git summary for write mode whether execution succeeds or fails → verify in main session
```

## Responsibilities

- `backend.py` provides shared checks for channel and detection: PATH, a working version command, and CLI-reported ChatGPT authentication.
- `channel` manages invocation, sandbox selection, logs, execution deadline, and process-group cleanup. It does not decide whether delegation is worthwhile.
- `detection` manages the readiness cache and doctor. It does not call models or promise remote connectivity or quota availability.
- `routing` reads valid cache and provides criteria. It does not classify by keywords or invoke Codex.
- Commands and the skill express authorization rules. The caller verifies correctness through actual diffs and tests.

## Execution contract

Default to `read-only`; explicit `--write` selects `workspace-write`. Both modes require a Git working tree without requiring it to be clean. Write mode records the baseline and existing changes. Once execution has started, every exit path emits a verification summary; failure does not automatically roll back changes.

The execution deadline defaults to and is capped at 540 seconds. Each authentication probe has a 5-second limit. Cleanup sends TERM to the process group, waits at most 2 seconds, then sends KILL. Normal exit also cleans up remaining processes in the group. Processes that detach fall outside this guarantee. The external Bash tool timeout is 600 seconds, leaving time for probing and cleanup.

stdin is `/dev/null`. The final answer written by `-o` is separate from the combined stdout/stderr process log. Cleanup attempts to retain the latest 50 pairs. Failure output is bounded to 40 lines/16KiB. No fixed log-to-answer compression ratio is promised.

Authentication follows CLI status and supports the CLI's own file or keychain storage without reading credential files. API-key and unknown states are rejected. Execution removes both API-key environment variables and selects ChatGPT login and the OpenAI provider. CLI behavior changes may cause conservative rejection.

## Control boundaries

Confirmation is a model instruction, not a wrapper lock that cannot be bypassed. Preamble restrictions against committing, pushing, publishing, and unrelated network access are also behavioral instructions. Actual sandbox boundaries depend on Codex and host configuration; workspace-write can include temporary directories and additional writable roots.

The cache represents recent local readiness only. Expiration, identity changes, or invalid cache cause silent degradation; execution probes authentication again. doctor forces refresh, but its Chinese-rule heuristics do not cover every project/global rule or validate network connectivity, quota, or model access.

## Trade-offs

Keep one Codex backend without prematurely introducing a provider abstraction. There is no background control plane, queue, resumption, or automatic retry. Reject non-Git directories in both modes to keep execution conditions and verification consistent. Preserve existing user changes and determine their attribution through diff review.

Free stub tests verify deterministic contracts. Live verification of real sandbox behavior, remote requests, and interactive model behavior is a deliberate user choice. Evaluations explicitly load source, distinguish PASS/FAIL/NORUN, and require a fixed first-line verdict to avoid false positives from body text. The [capability map](capability-map.md) and [README](../../README.en.md) provide module and usage entry points.
