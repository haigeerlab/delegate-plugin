# delegate: design and boundaries

[简体中文](../../DESIGN.md) | English

Run scoped read-only reviews through Codex or Claude Code CLI, and settled general tasks through Codex. Both hosts share the source entry points and receive the final answer. The main session handles requirements, trade-offs, authorization, and verification. Separate execution reduces the process-log volume carried by that session, without guaranteeing lower total token usage or cost.

## Are the decisions settled?

Suitable work includes reviews, exploration across files, reproduction and diagnosis, a single task with a settled approach, and mechanical changes. If trade-offs or scope remain unresolved, keep the judgment in the main session. Writing files requires explicit user authorization in the current turn.

```text
SessionStart → refresh basic-readiness cache (no context output)
Explicit user delegation, or confirmation of a concrete model proposal → review/run command
→ backend-specific parameters and live authentication → Git scope/worktree checks
→ selected backend → answer / failure diagnostics
→ emit Git summary for Codex run writes on every started exit path → main-session verification
UserPromptSubmit is retired; no per-prompt probing, reminders or repeated confirmations
```

## Responsibilities

Source commands are review/run/doctor/help. delegate_cli.py owns shortcut inputs and model-free previews; delegate_capabilities.py describes two explicit backends. The backend preserves legacy scripts. Review is always read-only; run currently supports Codex only. Shortcuts reuse common context capture, permissions and result validation. v0.5.0 includes these interfaces, with both local host installations checked; migration is specified in the [module contract](../../spec/claude-review.md).

The public `delegate-exec.sh` selects the backend and validates its parameters, retaining the `codex-exec.sh` compatibility path. The `claude-review` module manages common context/snapshots/results, Claude preflight and native Mac execution boundaries; it does not extend Spec Guard executors. Detection cache and hooks still describe default Codex readiness; explicit Claude selection bypasses that Codex authentication gate.

Claude is read-only review: tool restrictions narrow capabilities, safe/restricted narrow project/plugin context, srt constrains the entire CLI filesystem/network access; a temporary launchd job supplies an independent kernel resource coalition, with a STOP barrier, PID-generation signals and task-count checks for helper cleanup. Use only existing local CLI/authentication and dependencies, without installing LaunchAgents or changing global settings. Fixed snapshots retain original-path/hash mappings and treat content as data. The wrapper owns execution identity, so denials, parsing errors or insufficient coverage cannot mean no findings. Real reviews have succeeded in both directions, and actual menu-to-public-script execution and the complete dry-run have been checked; this evidence applies only to the source version each run used, and no fresh bidirectional live acceptance was done at release. Deliberately induced model writes or recursion, authentication refresh, abnormal natural helper processes, and long-term stability remain unverified; see the [module contract](SPEC-claude-review.md).

- `backend.py` provides shared checks for channel and detection: PATH, a working version command, and CLI-reported ChatGPT authentication.
- `channel` manages invocation, sandbox selection, logs, execution deadline, and process-group cleanup. It does not decide whether delegation is worthwhile.
- `detection` manages the readiness cache and doctor. It does not call models or promise remote connectivity or quota availability.
- `routing` provides criteria for explicit requests and uses backend-specific diagnostics when needed. Codex cache does not establish Claude readiness; it does not classify by keywords or automatically start execution.
- Commands and the skill express authorization rules. The caller verifies correctness through actual diffs and tests.

## Codex run execution contract

Default to `read-only`; explicit `--write` selects `workspace-write`. Both modes require a Git working tree without requiring it to be clean. Write mode records the baseline and existing changes. Once execution has started, every exit path emits a verification summary; failure does not automatically roll back changes.

The execution deadline defaults to and is capped at 540 seconds. Each authentication probe has a 5-second limit. On abort, cleanup freezes the Codex process group and snapshots its descendants along the ppid chain, sends TERM to descendant groups that changed process group or session and then TERM to the Codex group while unfreezing it, shares one grace period of at most 2 seconds, then sends KILL to what remains, and waits at most 5 seconds to reap the direct child. If it cannot be reaped, its PID is reported and the exit is 125; cleanup results go to `.cleanup` and are relayed to stderr (S41). Normal exit also cleans up remaining processes in the group; background processes Codex leaves after exiting normally fall outside this guarantee. The external Bash tool timeout is 600 seconds, leaving time for probing and cleanup.

stdin is `/dev/null`. The final answer written by `-o` is separate from the combined stdout/stderr process log. Cleanup attempts to retain the latest 50 pairs. Failure output is bounded to 40 lines/16KiB. No fixed log-to-answer compression ratio is promised.

Authentication follows CLI status and supports the CLI's own file or keychain storage without reading credential files. API-key and unknown states are rejected. Execution removes both API-key environment variables and selects ChatGPT login and the OpenAI provider. CLI behavior changes may cause conservative rejection.

## Control boundaries

Confirmation is a model instruction, not a wrapper lock that cannot be bypassed. Preamble restrictions against committing, pushing, publishing, and unrelated network access are also behavioral instructions. Actual sandbox boundaries depend on Codex and host configuration; workspace-write can include temporary directories and additional writable roots.

The cache represents recent local readiness only. Expiration, identity changes, or invalid cache cause silent degradation; execution probes authentication again. doctor forces refresh, but its Chinese-rule heuristics do not cover every project/global rule or validate network connectivity, quota, or model access.

## Trade-offs

Support exactly Codex and an optional Claude Code review backend, defaulting to Codex without automatic host-based selection. There is no background control plane, queue, resumption, or automatic retry. Reject non-Git directories in both modes to keep execution conditions and verification consistent. Preserve existing user changes and determine their attribution through diff review.

Free stub tests verify deterministic contracts. Live verification of real sandbox behavior, remote requests, and interactive model behavior is a deliberate user choice. Evaluations explicitly load source, distinguish PASS/FAIL/NORUN, and require a fixed first-line verdict to avoid false positives from body text. The [capability map](capability-map.md) and [README](../../README.en.md) provide module and usage entry points.
