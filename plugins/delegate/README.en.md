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
- Claude Code review backend (optional): macOS, the official Claude Code ≥2.1.295 already signed in, Node.js ≥22.12.0, an installed srt 0.0.79 (npm package `@anthropic-ai/sandbox-runtime`; `srt --version` must print `0.0.79`), and an available user GUI launchd domain.

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

## Rules section

`/delegate:run --rules-file <file>` (since interface 1.3) puts rules meant only for this delegation into the prompt verbatim (after the preamble, before the task, at most 16 KiB). They win on conflict, except that the sandbox, no commit/push and the first-line markers cannot be changed by them. Codex reads the AGENTS.md at the worktree root by itself; delegate neither reads nor merges it. Keep long-term project rules in AGENTS.md and only this delegation's rules in the section.

## Long tasks

The default deadline is 540 seconds. `/delegate:run --timeout <seconds>` widens it to 541–7200 seconds (since interface 1.3); the deadline split, time budget, wrap-up and exit codes are the same as for the default. Whenever `--timeout` is given it must be called in the host's background mode (anything above 540 seconds needs the background; do not judge by the 600-second limit of Claude Code's foreground Bash); delegate does not manage background processes, so stop a run by stopping that background task, and the abort reclaims every descendant process Codex started. A run ends within about `T + 30` seconds.

## Result file

Every run that started Codex writes one JSON result file, `${TMPDIR:-/tmp}/delegate/<runId>.result.json` (0600), for consumers to read by machine instead of parsing process logs.

- When there is a result line, the line before it is `delegate: result=<path>`; on failure, interruption, an unreaped executor (exit 125) or an empty answer, this line goes to stderr.
- Contents: `status`, `exitCode`, `runId`/`parent`/`chainRoot`, the session id, the commands Codex ran with their exit codes, the files changed in write mode, the text after `NEED_USER:`/`TIME_UP:`/`DONE:`, how a timeout was wrapped up, the abort-cleanup report, the duration, and tokens.
- Tokens come from Codex's `turn.completed` and are **cumulative for the whole session**: `usage.session` is the session total, `usage.run` is this run's usage (for a resumed round, the difference from the previous round). The total for a chain is the last `usage.session`; do not add the rounds up.
- `--strict`: the first line of the final answer must be `DONE:`, `NEED_USER:` (resumable only) or `TIME_UP:`. A missing marker gives `status=unmarked`, exit 1, and cannot be resumed. A project AGENTS.md that asks for another first-line format may push the marker out; `--strict` catches that.
- Codex's own session files are not read, so context usage, compaction and quota are not in the result file.
- Process logs are now two files: `<runId>.events.jsonl` (Codex's JSON event stream) and `<runId>.log` (stderr).

## Default model configuration

To stop naming a model every time, write per-backend defaults in `~/.config/delegate/config.json` (or `$XDG_CONFIG_HOME/delegate/config.json` when `XDG_CONFIG_HOME` is an absolute path). delegate only reads this file; it never creates or changes it, nor the Codex or Claude global configuration.

```json
{
  "schema": "delegate.config/v1",
  "defaults": {
    "codex": {"model": "gpt-6.2-sol", "effort": "high"},
    "claude-code": {"model": "claude-opus-5-5"}
  }
}
```

- Precedence: an explicit `--model`/`--effort` > this file > host default (nothing passed; Codex or Claude follows its own configuration). Model and effort are resolved separately.
- `--backend auto` uses the defaults of whichever backend it picks; `--resume` and `--continue` keep the model and effort recorded for the original session and take no values from this file, but the file is still checked: when it is invalid a resume exits 64 too.
- Every backend and field is optional; `claude-code` does not support `effort`. Extra keys, misspelt names, invalid model names or effort values are configuration errors: **when the file exists but is wrong, every review and run exits 64** with a single stderr line `delegate: invalid config <path>: <code>[ at <key>]`, never echoing the contents. Fix or delete the file to recover; a missing file is not an error.
- The model actually used and its source appear in the review report (`requested_model`, `model_source`), the result file (`model`, `modelSource`, `effort`, `effortSource`) and the run's "model / effort" line; `/delegate:doctor` lists the effective defaults first. Sources: `explicit`, `config`, `host_default`, `resumed`.
- Only `/delegate:review` and `/delegate:run` (`delegate-exec.sh review|run`) read the file; the legacy `codex-exec.sh` entry does not. A Claude Code review started from Codex reads the same file. The contract is in the [spec](../../docs/en/SPEC-default-model.md).

## External interface

For other plugins to integrate by version without reading this plugin's internals.

- **`interface.json`**: at the plugin root. `interface` is the interface version; `review.backends` and `run.backends` are the backends this version **supports**, not ones installed, signed in or funded on this machine; whether they run is still decided by `/delegate:doctor`. Adding optional fields bumps the minor version; removing, renaming or changing a field's meaning bumps the major version. Consumers check a major range such as `>=1.0,<2.0`.
- **Resume (since interface 1.1)**: `run.resume` is `{"optIn": "--resumable", "option": "--resume", "backends": ["codex"], "statuses": [...]}`. Consumers check `>=1.1,<2.0` before resuming; with 1.0 or without the field they behave as before and do not resume.
- **Timeout (since interface 1.2)**: `run.resume.statuses` is `["done", "needs-input", "timeout"]`, and `run.timeout` is `{"status": "timeout", "exitCode": 124}`. Consumers use `timeout` only with `>=1.2,<2.0`; on 1.1 a timeout still exits 124 and is treated as failure.
- **Result file (since interface 1.3)**: `run.result` is `{"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict", "statuses": [...]}`, and `run.usage` states how tokens are counted. Consumers read the result file with `>=1.3,<2.0` and the field present.
- **Continue (since interface 1.3)**: `run.continue` is `{"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable", "stateRetentionDays": 14}`.
- **Long tasks (since interface 1.3)**: `run.longRun` is `{"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540, "background": "caller"}`; `background: "caller"` means the caller owns the background run.
- **Check and write authorization (since interface 1.3)**: `run.check` is `{"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600, "operators": [...], "match": "token-prefix-or-suffix"}`, with the same operator rule as module-crew S30; `run.writeAuthorization` is `{"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization", "verifies": [...]}`. `run.write` stays `"explicit"`.
- **Rules section (since interface 1.3)**: `run.rules` is `{"option": "--rules-file", "maxBytes": 16384, "placement": "after-preamble", "projectInstructions": "codex-reads-agents-md"}`.
- **Patch fingerprint (since interface 1.4)**: `review.report.fingerprint` is `{"field": "scope.fingerprint", "algorithm": "blob-pairs-v1", "baselineModes": ["commits"]}`; the algorithm is in the [spec](../../docs/en/SPEC-review-fingerprint.md). It is a sha256 over only the mode and object id of each reviewed file in the two commit trees, independent of git configuration and the git version, so it can be recomputed on another machine (such as GitHub Actions); a shallow clone on Actions must still reach the `from` commit.
- **Finding severity (since interface 1.5)**: `review.report.severity` is `{"field": "findings[].severity", "values": ["blocking", "suggestion"], "criteria": "severity-v1", "missing": "blocking"}`. The review model labels each finding `blocking` or `suggestion` against the fixed criteria `severity-v1` (see the [spec](../../docs/en/SPEC-review-severity.md)); `--task` cannot change the criteria, and any later change takes a new name.
- **Re-review against the previous round (since interface 1.5)**: `review.recheck` is `{"option": "--previous-report", "field": "recheck", "statuses": ["resolved", "unresolved"]}`; the contract is in the [spec](../../docs/en/SPEC-review-recheck.md). Pass in the previous delegate report: each of its blocking findings goes into `recheck.items` marked resolved or unresolved, and this round's `findings` holds only new issues; the previous report must have a conclusion and the same scope.
- **Rechecking snapshot reviews (since interface 1.6)**: `review.recheck.snapshot` is `true`; the contract is in the [spec](../../docs/en/SPEC-review-snapshot-recheck.md). Snapshot reviews such as Plan reviews (`--paths` without `--base`, baseline `from == to`) can also take `--previous-report` after rework: when both rounds are snapshots only `paths` and `mode` are compared, and the current commit must be the previous commit or a descendant (another branch, a missing commit or a tag object reports `previous_report_scope_mismatch`); one snapshot round with one range round reports the same code. For reference files passed with `--spec`/`--plan`, the prompt says they only serve to verify references and get no findings of their own. Reference files outside the review scope need no coverage report from the reviewer; leaving them unmentioned is not missing coverage (since 0.12.1).
- **Technical design review (since interface 1.7)**: `review.profiles.design` is `{"option": "--profile design", "criteria": "design-v1", "downgraded": ["no_code_evidence", "second_round"]}`; the contract is in the [spec](../../docs/en/SPEC-design-review-criteria.md). `--profile design` reviews a technical design against criteria `design-v1`: a blocking finding must point to an existing line in a **reference file** (a file passed with `--spec`/`--plan` that is not under review), otherwise delegate records it as a suggestion marked `downgraded: "no_code_evidence"` without changing its text; with `--previous-report` the second round only checks the previous round, and new findings become suggestions marked `downgraded: "second_round"`; in the design profile an unlocated finding does not fail the whole review. The report gains top-level `criteria` (`severity-v1` or `design-v1`), which must match between rounds of a recheck (old reports without it read as `severity-v1`). When reviewing a design, pass the existing code and the requirement with `--spec`, or every blocking finding will be downgraded. Without `--profile`, behaviour and criteria are unchanged.
- **Choosing the second reviewer (since interface 1.7)**: `review.reviewer` declares `--backend auto` with `--author-host codex|claude-code`; the contract is in the [spec](../../docs/en/SPEC-reviewer-selection.md). `auto` requires naming the author; delegate uses model-free checks to prefer the other vendor, falls back to a fresh same-vendor session, and otherwise returns an "unreviewed" report: `execution_status=conditions_missing`, `review_outcome=inconclusive`, first diagnostic `no_reviewer_available`, top-level `backend` `null`, exit 127. `auto` cannot be combined with `--model`, `--effort`, `--max-turns` or `--max-budget-usd`. The report gains top-level `reviewer: {vendor, backend, same_vendor, selection}` with `vendor` `openai`/`anthropic` and `selection` `cross_vendor`/`same_vendor_fallback`/`explicit`/`none`; with an explicit backend and no author, `same_vendor` is `null`. Reviews always run in a fresh session, so the session that wrote the code never reviews its own work. `/delegate:doctor --reviewers [--json]` lists the reviewers available on this machine (JSON `delegate.reviewers/v1`) and suggests adding a second vendor when only one is set up; it never blocks anything.
- **`statuses` is an open set**: later minor versions may append values. A consumer meeting an unknown value must stop or treat it as failure, never as completion; decide success by exit code 0 first, then `status=done`.
- **Review report (`review.report.schemaVersion: 1`)**: the standard output of `/delegate:review` is one JSON report (`--dry-run` prints a preview, not a report). The private copy path on standard error is not part of the interface. Stable fields:

| Field | Meaning |
|---|---|
| `schema_version` | Always `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`, `scope.baseline`, `scope.diff_sha256`, `scope.files` | Review target and fingerprint; `diff_sha256` is the sha256 of the diff text, depends on local git configuration and version, and is only valid on the local machine |
| `scope.fingerprint` (since interface 1.4) | `{algorithm, sha256, paths}`; set only for the `commits` baseline, `null` for other baselines |
| `reviewed`, `unreviewed[]` (`{path, reason}`) | Reviewed and unreviewed files |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified, severity}`; `line` may be `null`; `severity` (since interface 1.5) is `blocking` or `suggestion` |
| `recheck` (since interface 1.5) | `null` without `--previous-report`; with it, `{previous_report_sha256, previous_fingerprint, items}` where `items[]` is `{index, status, evidence, finding}` and `status` is `resolved` or `unresolved` |
| `limitations` | Limitation statements |

Other fields are diagnostics and may change. A review has a conclusion only when `execution_status=completed` and `review_outcome` is `findings` or `no_findings_in_scope`; `no_findings_in_scope` does not mean there are no defects. A report is a third-party opinion, not user approval; cite it with delegate, the backend and the fingerprint. When recomputing `scope.fingerprint`: it only proves the patch the review saw is these changes of `paths` from `from` to `to`; compare the PR's changed files with `paths` yourself to rule out files the review did not see; a matching fingerprint does not mean a conclusion, let alone approval to merge; treat an unknown `algorithm` as "cannot recompute". When reading `severity`: treat a missing field (reports from 0.9.0 and earlier) or an unknown value as `blocking`; read it only when the review has a conclusion; a blocking finding with a non-empty `unverified` is one the reviewer could not confirm and labelled strictly per the criteria; severity is the model's judgment, and no blocking findings does not mean the change may be merged. On a re-review, this round's blocking set = `unresolved` entries in `recheck.items` + `findings` treated as `blocking`, read only when the review has a conclusion; to check that the re-review covered the fixed patch, compare `recheck.previous_fingerprint` with this round's `scope.fingerprint`; a snapshot recheck has no patch and the same fingerprint every round, so compare the sha256 values in both reports' `scope.files` instead.
- **Default model (since interface 1.8)**: top-level `defaults` declares the configuration location, `delegate.config/v1` and the source values; the review report gains the stable field `model_source` and the result file gains `modelSource` and `effortSource`. `requested_model` now means the model delegate actually passed to the backend (explicit or configured; `null` for the host default). See "Default model configuration" above and the [spec](../../docs/en/SPEC-default-model.md).

## Feedback and license

Report problems and suggestions through [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues); report security problems through [private vulnerability reporting](https://github.com/haigeerlab/delegate-plugin/security/advisories/new). This plugin is released under the [MIT License](LICENSE).
