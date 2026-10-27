# delegate plugin

[简体中文](README.md) | English

This directory is the delegate plugin itself and is what the installation cache contains. See the repository [README](https://github.com/haigeerlab/delegate-plugin/blob/main/README.en.md) for complete installation, option, verification, and troubleshooting guidance.

delegate sends scoped read-only reviews to Codex or Claude Code and sends general tasks with a settled plan to Codex. Choose the backend explicitly with `--backend`; Codex is the default. The plugin runs only on an explicit user request or confirmation and never delegates automatically.

## Installation

Run in your terminal:

```bash
claude plugin marketplace add haigeerlab/delegate-plugin
claude plugin install delegate@delegate-marketplace
```

After installing, open a new session or run `/reload-plugins`. To update, run `claude plugin update delegate@delegate-marketplace`.

## Commands

| Command | Purpose | Calls a backend model |
|---|---|---|
| `/delegate:review` | Read-only review of the scope given by `--paths`, `--base`, `--changes`, or `--context`, on the codex or claude-code backend | Yes, except with `--dry-run` |
| `/delegate:run` | Sends a confirmed task to Codex; read-only by default, writes files only with `--write` after explicit user authorization | Yes |
| `/delegate:doctor [--backend codex\|claude-code]` | Checks local prerequisites for the chosen backend | No |
| `/delegate:help` | Shows options, exit statuses, and migration notes | No |

In Codex the corresponding skills are `source-command-review`, `source-command-run`, `source-command-doctor`, and `source-command-help`. The old `/delegate:delegate` was removed in v0.5.0: use run for general tasks and review for structured reviews.

## Requirements

- All uses: a Git working tree, Python 3, and Bash (compatible with 3.2).
- Codex backend: a working `codex` on PATH, signed in through ChatGPT.
- Claude Code review backend (optional): macOS, the official Claude Code ≥2.1.295 already signed in, Node.js ≥22.12.0, an installed srt 0.0.79, and an available user GUI launchd domain.

The plugin installs no dependencies, signs in to nothing, and changes no global configuration: `--write` runs trust the current repository for that run only through `-c`, so Codex does not write a trust entry to `~/.codex/config.toml` (except when the check is uncertain, which is reported on stderr; see the [root README](../../README.en.md#output-and-verification)). Every run and Codex review uses `approval_policy="never"` instead of the local approval configuration: commands that leave the sandbox (such as `git commit` inside a worktree, or network access) are refused, and commits rely on prefix allow rules or the caller. Run `/delegate:doctor` before first use, and `/delegate:doctor --backend claude-code` before using the Claude backend.

## Layout

```text
.claude-plugin/plugin.json   Plugin manifest
interface.json               External interface version and capability declaration
commands/                    review, run, doctor, help session entries
skills/delegate-routing/     Routing criteria for explicit delegation requests
hooks/                       SessionStart readiness checks, cache, doctor entry
scripts/                     Backend invocation (Codex / Claude Code) and process management
tests/                       Offline stub tests and regressions
```

## Resumable delegation

`/delegate:run --resumable` tells Codex to finish the tasks not affected by pending decisions first and to stop only when the user must decide. It is off by default; when on, Codex keeps the session in its own session directory.

- The last line of every successful return and of every timeout: `delegate: run_id=<id> status=<done|needs-input|timeout> resumable=<true|false>`. **To decide success, check exit code 0 first, then `status=done`; a result line does not mean success.**
- `needs-input` exits 0; the answer starts with `NEED_USER:`, and everything after the marker is the question for the user.
- After the user answers: `/delegate:run --resume <runId> [--write] -- "<user answer>"`. The answer must be the user's own words or a paraphrase they accepted. Only the latest needs-input round can be resumed, in the same repository with the same write mode; the original model and effort are reused, and each round gets a new runId.
- Timeout (`status=timeout`, exit 124): the prompt carries a time budget, so the model should stop before the deadline and write its progress (first line `TIME_UP:`). If it is forcibly stopped, one more read-only round is resumed that only writes progress; if that also fails, a model-free fallback text is printed (session id, whether it can resume, and in write mode the changed files). A timed-out run can be continued with `--resume`, at the user's decision.
- A plain run (without `--resumable`) gets the same time budget and fallback and also ends in `status=timeout` with exit 124, but its session is not kept and it cannot be resumed.
- Known limits: a missing marker is classified as done; failed runs cannot be resumed.
- **Continue with the next task after done (since interface 1.3)**: `/delegate:run --continue <runId> [--write] -- "<next task>"` takes only a `done` round of a chain started with `--resumable` and carries on in the same Codex session, without starting a new session or rereading the project. A runId can be taken over only once; the task must come from an approved Plan or from the user.
- Chain state and result files are kept for 14 days; process logs keep only the latest 50 groups.

## Checks and pre-granted write authorization

- `/delegate:run --check "<command>"` (since interface 1.3): after a run ends `done`, delegate runs the check command as an argument list in the repository root (no shell, 600-second limit) and records it under `check` in the result file without changing the run's own status. Commands with shell operators are refused with the same rule as module-crew. The check runs outside the sandbox with your permissions, so the command may only come from check commands you approved in the project configuration.
- `/delegate:run --write --authorized-by <file>` (since interface 1.3): the consumer (module-crew) records the words you used to switch offloading on in a file; when the Spec and Plan are approved, the Task is inside the approved Plan and it is the same module in the same worktree, it need not wait for your nod on every Task. delegate only records the file's path and sha256 and requires the same file across the chain; it cannot verify the content.

## Long tasks

The default deadline is 540 seconds. `/delegate:run --timeout <seconds>` widens it to 541–7200 seconds (since interface 1.3); the deadline split, time budget, wrap-up and exit codes are the same as for the default. Above the host's foreground command limit (600 seconds for Claude Code's foreground Bash) it must be called in the host's background mode; delegate does not manage background processes, so stop a run by stopping that background task, and the abort reclaims every descendant process Codex started. A run ends within about `T + 30` seconds.

## Result file

Every run that started Codex writes one JSON result file, `${TMPDIR:-/tmp}/delegate/<runId>.result.json` (0600), for consumers to read by machine instead of parsing process logs.

- When there is a result line, the line before it is `delegate: result=<path>`; on failure, interruption, an unreaped executor (exit 125) or an empty answer, this line goes to stderr.
- Contents: `status`, `exitCode`, `runId`/`parent`/`chainRoot`, the session id, the commands Codex ran with their exit codes, the files changed in write mode, the text after `NEED_USER:`/`TIME_UP:`/`DONE:`, how a timeout was wrapped up, the abort-cleanup report, the duration, and tokens.
- Tokens come from Codex's `turn.completed` and are **cumulative for the whole session**: `usage.session` is the session total, `usage.run` is this run's usage (for a resumed round, the difference from the previous round). The total for a chain is the last `usage.session`; do not add the rounds up.
- `--strict`: the first line of the final answer must be `DONE:`, `NEED_USER:` (resumable only) or `TIME_UP:`. A missing marker gives `status=unmarked`, exit 1, and cannot be resumed. A project AGENTS.md that asks for another first-line format may push the marker out; `--strict` catches that.
- Codex's own session files are not read, so context usage, compaction and quota are not in the result file.
- Process logs are now two files: `<runId>.events.jsonl` (Codex's JSON event stream) and `<runId>.log` (stderr).

## External interface

For other plugins to integrate by version without reading this plugin's internals.

- **`interface.json`**: at the plugin root. `interface` is the interface version; `review.backends` and `run.backends` are the backends this version **supports**, not ones installed, signed in or funded on this machine; whether they run is still decided by `/delegate:doctor`. Adding optional fields bumps the minor version; removing, renaming or changing a field's meaning bumps the major version. Consumers check a major range such as `>=1.0,<2.0`.
- **Resume (since interface 1.1)**: `run.resume` is `{"optIn": "--resumable", "option": "--resume", "backends": ["codex"], "statuses": [...]}`. Consumers check `>=1.1,<2.0` before resuming; with 1.0 or without the field they behave as before and do not resume.
- **Timeout (since interface 1.2)**: `run.resume.statuses` is `["done", "needs-input", "timeout"]`, and `run.timeout` is `{"status": "timeout", "exitCode": 124}`. Consumers use `timeout` only with `>=1.2,<2.0`; on 1.1 a timeout still exits 124 and is treated as failure.
- **Result file (since interface 1.3)**: `run.result` is `{"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict", "statuses": [...]}`, and `run.usage` states how tokens are counted. Consumers read the result file with `>=1.3,<2.0` and the field present.
- **Continue (since interface 1.3)**: `run.continue` is `{"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable", "stateRetentionDays": 14}`.
- **Long tasks (since interface 1.3)**: `run.longRun` is `{"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540, "background": "caller"}`; `background: "caller"` means the caller owns the background run.
- **Check and write authorization (since interface 1.3)**: `run.check` is `{"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600, "operators": [...], "match": "token-prefix-or-suffix"}`, with the same operator rule as module-crew S30; `run.writeAuthorization` is `{"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization", "verifies": [...]}`. `run.write` stays `"explicit"`.
- **`statuses` is an open set**: later minor versions may append values. A consumer meeting an unknown value must stop or treat it as failure, never as completion; decide success by exit code 0 first, then `status=done`.
- **Review report (`review.report.schemaVersion: 1`)**: the standard output of `/delegate:review` is one JSON report (`--dry-run` prints a preview, not a report). The private copy path on standard error is not part of the interface. Stable fields:

| Field | Meaning |
|---|---|
| `schema_version` | Always `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`, `scope.baseline`, `scope.diff_sha256`, `scope.files` | Review target and fingerprint |
| `reviewed`, `unreviewed[]` (`{path, reason}`) | Reviewed and unreviewed files |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified}`; `line` may be `null` |
| `limitations` | Limitation statements |

Other fields are diagnostics and may change. A review has a conclusion only when `execution_status=completed` and `review_outcome` is `findings` or `no_findings_in_scope`; `no_findings_in_scope` does not mean there are no defects. A report is a third-party opinion, not user approval; cite it with delegate, the backend and the fingerprint.

## Feedback and license

Report problems and suggestions through [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues); report security problems through [private vulnerability reporting](https://github.com/haigeerlab/delegate-plugin/security/advisories/new). This plugin is released under the [MIT License](LICENSE).
