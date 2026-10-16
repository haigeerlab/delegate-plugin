# delegate

[简体中文](README.md) | English

A review and delegation plugin with shared Claude Code / Codex source command entry points. v0.5.0 provides **Codex / Claude Code read-only review** and the existing **Codex general execution** mode; Codex remains the default backend. The main session receives the final answer; process logs stay locally.

Four entries separate responsibilities: `/delegate:review` performs scoped read-only review, `/delegate:run` executes general Codex tasks, `/delegate:doctor` checks integration prerequisites, and `/delegate:help` explains capabilities and migration. Codex exposes the corresponding `source-command-*` skills.

Verification status: real reviews have succeeded in both directions (Codex→Claude Code and Claude Code→Codex); normal installation, display of all four entries, actual menu-to-script execution, and the model-free preview have been checked; the module has completed local acceptance under layered criteria. Security scenarios such as deliberately inducing model writes or recursive calls, authentication refresh, and abnormal natural helper processes remain unverified, and each existing real record applies only to the source version it ran against. See the [delivery and acceptance record](docs/verification/2026-10-13-delegate-delivery-status.md) and the [layered acceptance result](docs/verification/2026-10-14-delegate-layered-acceptance-result.md) (both Chinese).

The Claude backend uses an existing local srt, resolved from PATH by default or set to an absolute path with `DELEGATE_SRT_BIN`. A different model does not guarantee a more accurate review.

The main session handles requirements, design decisions, and final verification. The Codex backend accepts only ChatGPT authentication. It aims to reduce process context carried by the main session; usage is charged against the account signed into Codex, and lower total cost or token usage is not guaranteed.

Repository: [haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · Current release: [v0.5.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.5.0) · [Documentation index](docs/en/README.md)

## Contents

- [Use cases and boundaries](#use-cases-and-boundaries)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Commands and options](#commands-and-options)
- [Output and verification](#output-and-verification)
- [Updates and uninstalling](#updates-and-uninstalling)
- [Troubleshooting](#troubleshooting)
- [Architecture and documentation](#architecture-and-documentation)
- [Development, contributions, and feedback](#development-contributions-and-feedback)
- [Reporting a bug](#reporting-a-bug)
- [License](#license)

## Use cases and boundaries

Set the scope before execution. Writing files requires explicit user authorization in the current turn.

| Use case | Approach |
|---|---|
| Code review, regression investigation, security review | Read-only; specify the inspection scope and report format |
| Exploring structure across files or tracing calls | Read-only; specify entry points and questions |
| Diagnosing bugs, logs, or stack traces | Read-only; separately authorize write mode if tests or investigation need to create files or caches |
| Implementing one task with a settled approach and running relevant tests | `--write`; provide verifiable acceptance criteria |
| Batch renaming, migration, or mechanical edits | `--write`; specify files and exclusions |
| Requirements, architectural trade-offs, final verification, or a one-line edit | Keep the work in the main session |

Flow: explicit delegation request → establish scope and backend → use existing authorization or confirm a new proposal → review the answer and Git evidence → verify in the main session. Ordinary continuations add no delegation gate; settled decisions do not require delegation.

Directly entering a delegation command with a specific task also authorizes that task. Commands and the skill instruct the model to request confirmation; the wrapper does not enforce this through an authorization token that cannot be bypassed.

The plugin supports a single, non-interactive, synchronous delegation, model and reasoning-effort selection, read-only defaults, authorized writes, log separation, failure diagnostics, and a Git change summary. **Both modes require a Git working tree.**

It does not provide background jobs, queues, resumption, automatic retries, a third backend, or team quota management. It does not handle automatic commits, pushes, or publishing, and does not guarantee correct results or adherence to every instruction.

## Prerequisites

| Dependency | Requirement |
|---|---|
| Claude Code | Plugin support and a working `claude` command in the terminal |
| Codex CLI | A working `codex` command on PATH in the same environment, authenticated through ChatGPT |
| Python 3, Git, Bash | Required by the scripts; compatible with macOS Bash 3.2 |
| Target project | A Git working tree; existing uncommitted changes and repositories without commits are allowed |
| Node.js, npm | Required if you use the npm installation method below |
| Claude Code review backend (optional) | Needed only for `--backend claude-code`: macOS, the official Claude Code ≥2.1.295 already signed in, Node.js ≥22.12.0, an installed srt 0.0.79, and an available user GUI launchd domain; the plugin installs and signs in to nothing |

The Codex execution path keeps the v0.4.0 verified environment: Claude Code 2.1.291, Codex CLI 0.160.0, Python 3.10, and Bash 3.2. The v0.5.0 Claude review backend was tested on macOS 15.7.3 arm64 with the official Claude Code 2.1.296. These are tested versions, not a minimum compatibility guarantee. Windows and Linux have not been verified.

Authentication is checked through CLI status rather than the existence of `auth.json`. API-key and unrecognized authentication states are rejected. Execution removes `OPENAI_API_KEY` and `CODEX_API_KEY` and selects ChatGPT authentication and the OpenAI provider. Codex CLI manages credential storage, which may use a file under `CODEX_HOME` or the system keychain. [Codex authentication documentation](https://learn.chatgpt.com/docs/auth)

## Quick start

### 1. Install Codex and sign in

Run in your terminal:

```bash
npm install -g @openai/codex@latest
codex --version
codex login
codex login status
```

`codex login status` should display `Logged in using ChatGPT`. The plugin requires this explicit status before execution.

### 2. Install the plugin

Run in your terminal:

```bash
claude plugin marketplace add haigeerlab/delegate-plugin
claude plugin install delegate@delegate-marketplace
```

This repository is a marketplace containing the `delegate` plugin. Its installation identifier is `delegate@delegate-marketplace`.

### 3. Open your project and run diagnostics

Replace the path with your target Git project and start a new Claude Code session from your terminal:

```bash
cd /path/to/your-project
claude
```

Enter this in the **Claude Code session**:

```text
/delegate:doctor
```

Without options it checks the default Codex backend. Before using the Claude review backend, enter `/delegate:doctor --backend claude-code` instead to check srt, Node, the CLI version, and existing authentication.

On the Codex path, doctor refreshes local installation and authentication checks and inspects some Chinese-language rules in the global AGENTS.md. Neither backend's doctor makes a model request. Exit status 0 means diagnostics completed; read the issue count and reasons. Basic readiness does not verify remote connectivity, available quota, or model access.

### 4. Run your first read-only delegation

v0.5.0 uses `/delegate:run`. When upgrading from v0.4.0, migrate `/delegate:delegate` to run or review.

Enter this in the Claude Code session:

```text
/delegate:run Read git status --short for this project and explain the working-tree state; do not modify files
```

This makes a real Codex model request and consumes the signed-in account's quota. On successful completion, expect the final answer, model/effort hints, a process-log path, and byte counts. If no model is specified, the wrapper displays `配置默认` (configuration default); this does not mean it has discovered the actual model name.

For writes, explicitly authorize the current task before using `--write`, then review actual diffs and test results as described in [Output and verification](#output-and-verification).

## Commands and options

Terminal commands beginning with `claude plugin ...` manage installation. The `/delegate:...` entries below run inside Claude Code. Use the full namespace and the command inventory actually loaded by your host. [Official component documentation](https://code.claude.com/docs/en/plugins/components)

Codex 0.162.1 converts the four source commands to skills:

| Claude Code entry | Migrated Codex skill name |
|---|---|
| `/delegate:review` | `source-command-review` |
| `/delegate:run` | `source-command-run` |
| `/delegate:doctor` | `source-command-doctor` |
| `/delegate:help` | `source-command-help` |

Select the corresponding delegate skill in the Codex skill picker and provide the same arguments. The CLI opens that picker with `/skills` ([official documentation](https://learn.chatgpt.com/docs/developer-commands#use-skills-with-skills)). Codex's built-in `/review` is a separate entry and does not establish that delegate ran. Both hosts share the scripts; identical slash aliases are not required. Use the host's loaded inventory.

All four Codex migration artifacts and Claude Code 2.1.296 session-only source initialization have been checked. Subsequent four-entry display and S7 menu-to-public-script execution with complete dry-run output were checked; see the [actual output evidence](docs/verification/2026-10-14-delegate-s7-output-readback-result.md) (Chinese). Error-free automatic UI input remains unverified. The table describes execution-backend model calls only; interpreting a command can consume the primary host's model usage.

| Entry | Purpose | Calls an execution-backend model? |
|---|---|---|
| `/delegate:review` | Scoped read-only review through codex/claude-code | Yes, except dry-run |
| `/delegate:run [options] <task>` | Codex general task | Yes |
| `/delegate:doctor --backend <backend>` | Selected-backend diagnostics and capability description | No; CLI status checks only |
| `/delegate:help` | Options, examples, limitations, and troubleshooting | No |
| `/delegate:delegate-routing` | Routing-criteria skill, callable when supported by the host | No; a new model proposal needs confirmation, existing scope authorization does not |

```text
/delegate:review --backend claude-code --paths src/payments --model sonnet
/delegate:run --write Fix the null dereference using the agreed approach; run relevant tests and report results
/delegate:run --model <model-slug> --effort high Trace the login flow
```

| Option | Contract |
|---|---|
| No mode switch | `read-only` sandbox |
| `--write` | `workspace-write` sandbox; explicit user authorization in the current turn is required |
| `--model <slug>` | Pass the model name through; omission uses Codex configuration, invalid values fail in the CLI |
| `--effort <level>` | Pass reasoning effort through; valid values depend on the model and CLI version |
| `--` | End option parsing so a task may begin with `-` |
| `--help` / `-h` | Local wrapper usage without Codex; this is not an additional session command |

To run the source script directly, execute it from the **target Git project**, passing the task as one correctly quoted argument:

```bash
bash /path/to/delegate-plugin/plugins/delegate/scripts/codex-exec.sh --write "Apply the agreed fix and test it"
```

Set the Claude Bash tool timeout to `600000` milliseconds. The wrapper's Codex execution deadline defaults to, and is capped at, **540 seconds**. `DELEGATE_TIMEOUT_SECONDS` accepts a shorter positive integer; larger values are capped at 540, and invalid or non-positive values fall back to 540. Each authentication probe has a 5-second limit. Process-group cleanup waits at most 2 seconds before forced termination. The execution deadline excludes preflight checks and subsequent Git inspection. Processes that detach from the group are not guaranteed to be reclaimed.

## Dual-backend read-only review (v0.5.0)

v0.5.0 commands are review/run/doctor/help. Both hosts share their definitions; actual host names follow the loaded command list. The old v0.4.0 `/delegate:delegate` is removed: migrate general tasks to run and structured reviews to review. Legacy script calls remain valid; source changes do not update caches.

```text
/delegate:review --backend claude-code --paths src/payments --model sonnet
/delegate:review --backend codex --base main --head HEAD
/delegate:review --paths src/payments --module payments --spec spec/payments.md --plan tasks/payments/plan.md --dry-run
/delegate:review --context /path/review.json
```

Paths/module default to HEAD; workspace content requires explicit changes (staged/unstaged/working-tree). Untracked requires include-untracked with working-tree. Base/head selects a fixed commit diff; without paths, only changed files are selected. Paths/exclude/spec/plan/criterion are repeatable and root-relative; repo selects the worktree. Context is mutually exclusive with scope shortcuts. Dry-run shows hashes/scope/permissions without models, authentication checks or review conclusions. Terminal entry is `delegate-exec.sh review [options]`. See the [interface contract](spec/claude-review.md).


Select backend independently of model and host:

```bash
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend claude-code --review-context /path/review.json --model sonnet "Review the specified scope"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend codex --review-context /path/review.json "Review the same scope"
```

Claude requires explicit scope through review shortcuts or advanced context JSON, supports read-only review only, rejects `--write` / `--effort`, defaults to 12 turns, and accepts an optional estimated budget. Both backends receive the same fixed context, snapshot and result contract. The current path is Mac native only, requiring original Claude ≥2.1.295 (the inspected baseline), Node ≥22.12.0, srt 0.0.79 and an available user GUI launchd domain. macOS 15.7.3 arm64 was tested; kernel capability failures stop execution without reduced cleanup.

Resolve `claude`, `node` and `srt` from PATH, or specify existing absolute executables with `DELEGATE_CLAUDE_BIN`, `DELEGATE_NODE_BIN` and `DELEGATE_SRT_BIN`, for example prefixing the command with `DELEGATE_SRT_BIN=/absolute/existing/srt`. Reuse original local CLI authentication without credential copying, installation, upgrades, login or global changes. Old guest configuration is explicitly rejected. V1 rejects custom auth directories, API/provider environment overrides and local managed configuration instead of silently changing authentication. Missing conditions never switch backend. See the [claude-review contract](docs/en/SPEC-claude-review.md#executable-json-examples-and-configuration). `/delegate:doctor --backend claude-code` checks runtime dependencies, CLI and existing authentication inside the same Mac read-only boundary, without a model and Codex authentication cannot block this path.

Common reports separate execution status from review outcome and include reviewed/unreviewed scope and locatable evidence. Empty/invalid output, denials, limits or partial coverage never mean no findings. Final reports and safe diagnostic logs are separate under private `${TMPDIR:-/tmp}/delegate-review/`, retaining at most 50 groups; normal returns exclude raw process output. Normal real reviews succeeded in both directions; menu-to-script execution and dry-run were verified. Active model Write/recursion, auth refresh, natural abnormal helpers and long-term stability remain unverified. Additional live acceptance requires separate authorization.

## Output and verification

Success returns Codex's final answer, model/effort hints, the log path, and byte counts. Write mode also returns:

- Baseline HEAD, including repositories without commits, and the number of pre-existing uncommitted changes;
- `git status --short`;
- `git diff --stat` and `git diff --cached --stat`.

On execution failure, timeout, an empty answer, or interruption, **a write-mode task that has already started still emits its Git verification block to stderr**. Failure does not roll back changes. Statistics can include the user's pre-existing edits and do not identify who made each change; inspect actual diffs and test results. Treat Git inspection failures as errors rather than treating the summary as complete verification.

Process logs and answers are stored in `${TMPDIR:-/tmp}/delegate/`, with directory mode 0700 and new-file mode 0600. After success or failure, cleanup attempts to retain the latest **50 pairs** of `.log/.answer` files. Cleanup failure does not change the task's exit status. The count limit does not bound individual file sizes. Failure output shows at most the final 40 lines / 16KiB of the log and its full path. Read only the relevant lines when needed rather than bringing the entire log back into the session.

Codex's sandbox and host configuration determine read and write permissions. `workspace-write` may also allow temporary directories and additional roots. Instructions against committing, pushing, publishing, or unrelated network access are behavioral rules, not a substitute for the OS sandbox or host permissions.

## Updates and uninstalling

### Installation from a remote marketplace

Update manually, then start a new session to apply the updated plugin:

```bash
claude plugin update delegate@delegate-marketplace
```

Editing a separate local source checkout does not change a remote installation's cached copy. Remote plugin updates also depend on a change to the plugin version. Host background auto-update is disabled by default for third-party marketplaces, but users or administrators can enable it. delegate has no self-update feature; that does not mean the host can never update it automatically. [Official update documentation](https://code.claude.com/docs/en/plugins/host-marketplace)

### Local source and development loading

Clone the repository and register the local marketplace from the **repository root**:

```bash
git clone https://github.com/haigeerlab/delegate-plugin.git
cd delegate-plugin
claude plugin marketplace add "$PWD"
claude plugin install delegate@delegate-marketplace
```

A local marketplace identifies the installation source; it does not guarantee that the session reads that source directly. Check the registered `installPath` and actual files. The locally verified installation uses a cached copy: update and verify its contents before starting a new session or running `/reload-plugins`. Reloading alone does not refresh stale caches, and a same-version update does not prove replacement. For explicit source development, use `--plugin-dir` below and verify the loaded entry points. [Official marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces)

For development and evaluation, you can also explicitly load the source plugin directory from your target Git project:

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

If a marketplace with the same name is already registered, check its source first. Local loading and remote installation are alternatives; you do not need two installations. The `v0.5.0` tag fixes release source at one revision, while `main` continues to change.

### Uninstall

Run in your terminal, then start a new session:

```bash
claude plugin uninstall delegate@delegate-marketplace
```

If you no longer use the marketplace, remove it too:

```bash
claude plugin marketplace remove delegate-marketplace
```

Uninstalling does not roll back previous changes to your project. Temporary logs and readiness cache remain subject to the plugin's runtime cleanup and the system's temporary-directory policy.

## Troubleshooting

| Symptom | Check and next step |
|---|---|
| Command not found | Check loaded plugins, namespaces, and installation source; start a new session after updating, or load source with `--plugin-dir` during development |
| Codex missing or version command fails | Run `codex --version`; fix installation and PATH |
| Not signed in, API-key login, or unrecognized authentication | Run `codex login status`, then `codex login` to sign in with ChatGPT |
| No proposal after signing in | Refresh the cache with `/delegate:doctor`; proposals also depend on the task and model instructions |
| Not a Git working tree (64) | Enter the target Git repository; there is no non-Git bypass option |
| Invalid arguments (64) | Read `/delegate:help` or script `--help`; pass the task as one argument when running the script directly |
| Timeout (124) | Inspect the log tail and Git state, check task size, and decide manually whether to retry |
| Failure or empty answer | Inspect errors, log paths, and actual diffs; failed-task edits are not automatically reverted |
| Waiting for confirmation without doing the task | Inspect effective global/project AGENTS.md rules and exempt non-interactive execution from workflow sections intended only for interactive sessions |
| review reports a missing scope (64) | Provide one of `--paths`, `--base`, `--changes`, or `--context`; the whole project is never scanned automatically. Add `--dry-run` first to preview the resolved scope |
| Claude backend preconditions fail (127) | Run `/delegate:doctor --backend claude-code`; check the `claude`, `node`, and `srt` versions, and if needed set existing absolute paths with `DELEGATE_CLAUDE_BIN`, `DELEGATE_NODE_BIN`, or `DELEGATE_SRT_BIN`. It never falls back to Codex |
| Claude backend reports `native_authentication_environment_unverified` | The environment sets a custom auth directory, API key/token, third-party provider, or an `ANTHROPIC_BASE_URL` pointing anywhere other than the official endpoint. Check with `env \| grep -E '^(ANTHROPIC_\|CLAUDE_)'` and unset them in your terminal before rerunning. The `ANTHROPIC_BASE_URL=https://api.anthropic.com` (official default) that Claude Desktop sessions carry is accepted and does not trigger this error |
| Codex review reports `codex_inline_input_limit` | Review input exceeds 1 MiB and is neither truncated nor split automatically; review in smaller runs with narrower `--paths` or added `--exclude` |
| Review report is failed, inconclusive, or partially covered | Read the unreviewed scope and reasons in the report (permission denial, turn or budget limit, invalid output, and so on); none of these counts as a passing review |

Wrapper exit statuses: 64 for arguments/non-Git directories; 127 for basic CLI/Python failures; 124 for execution timeout; 129/130/143 for HUP/INT/TERM interruptions. An empty answer exits 1; other execution failures retain their nonzero status. review uses the same 64/127/124/129/130/143 conventions; a completed review exits 0 even when it reports findings. doctor always exits 0; assess the reported issue count.

doctor refreshes the temporary cache and does not modify project files. Its heuristics inspect only some Chinese global rules, not English or all project rules. It does not verify remote connectivity, quota, model access, or whether a token remains valid. Runtime diagnostics and skill instructions currently use mainly Chinese; bilingual documentation does not change these outputs.

## Architecture and documentation

| Module | Responsibility | Implementation |
|---|---|---|
| channel | Invocation, sandbox, process-group deadline/cleanup, answers and logs, Git evidence | `codex-exec.sh` + `run_codex.py` |
| detection | Shared basic checks, identity-bound cache, atomic writes, doctor | `backend.py` + `detect.py` + shell entry points |
| routing | Optional criteria and confirmation rules for explicit delegation requests | Commands + delegate-routing skill; silent legacy prompt/route entries |

v0.5.0 does not register UserPromptSubmit or probe/remind on every prompt. SessionStart silently refreshes readiness; doctor reports it on demand. The cache lasts 8 hours and is bound to the CLI path, Codex home, plugin root, and version. Future timestamps, old formats, identity changes, and invalid files invalidate it. Cached readiness does not guarantee current authentication; execution always checks login again.

See the [documentation index](docs/en/README.md) for reading order and language pairs. Read [Design](docs/en/DESIGN.md) for rationale and the [capability map](docs/en/capability-map.md) for module responsibilities. Exact contracts are in the [channel](docs/en/SPEC-channel.md), [detection](docs/en/SPEC-detection.md), and [routing](docs/en/SPEC-routing.md) specifications. Release changes are in [v0.5.0](docs/en/releases/v0.5.0.md); subsequent changes are in [Unreleased](docs/en/releases/unreleased.md).

## Development, contributions, and feedback

See [Development workflow](docs/en/development-workflow.md) for both AI hosts and project conventions. Chinese specifications use `spec/<id>.md`; historical records and current maintenance tasks are separate.

Run the free offline validation from the **repository root**:

```bash
/bin/bash scripts/validate.sh
```

The entry point covers syntax, manifest required fields, evaluator self-tests, three shell product suites, 15 loop-registered Python regression suites, the source-discovery regression and the isolation policy-only suite. v0.5.0 release validation passed 157 Python, 53 shell and 19 eval cases. Actual OS, host and live-model evidence is recorded separately, without labeling it as offline coverage. The free aggregate validation makes no model requests. Doctor rule tests now supply their own CLI stub, synthetic login state, and temporary log, without depending on an outer Codex installation or login. The [actual F8 fix verification in Chinese](docs/verification/2026-10-08-f8-applied.md) covers absent outer CLI and rejected outer login.

See [Contributing](CONTRIBUTING.en.md) for development conventions, individual tests, paid live verification, and bilingual maintenance. Use [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues) for problems and suggestions; follow the next section to report a bug.

## Reporting a bug

Report plugin failures through this repository's GitHub Issues. Do not file security problems publicly; report them privately as described in the [security policy](SECURITY.en.md).

1. [Search existing issues](https://github.com/haigeerlab/delegate-plugin/issues) for the same symptoms or a solution. If a matching issue exists, add your reproduction details there.
2. Sign in to GitHub, open [a new issue](https://github.com/haigeerlab/delegate-plugin/issues/new/choose), choose the "Bug 报告 / Bug report" template, and summarize the failure in a one-sentence title.
3. Fill in the template with enough information to reproduce the problem and submit it; without the template, copy the checklist below. Reports in Chinese or English are welcome.

```text
Environment: OS, plugin, Claude Code, Codex CLI, Python, and Bash versions
Installation: remote marketplace / local path / --plugin-dir
Command: specify read-only or --write; remove private task content
Reproduction steps: starting state and actions in order
Expected result: what should happen
Actual result: what happened and whether it happens every time
Exit status and error: retain the relevant original error text
/delegate:doctor: relevant diagnostic excerpts
For writes: Git state, pre-existing edits, and changes remaining after failure
```

Commands such as `claude --version` and `codex --version` show versions. Remove credentials, personal paths, and proprietary source before submitting; do not upload `auth.json`, API keys, or full process logs. See [Contributing: reporting issues](CONTRIBUTING.en.md#reporting-issues-and-suggesting-changes) for more detail.

## License

The project source and accompanying documentation are licensed under the [MIT License](LICENSE), with `Copyright (c) 2026 haigeerlab and contributors`. Commercial use, modification, and distribution are permitted; copyright and permission notices must be retained in distributions. The software is provided as is, without warranty. This is a summary; the standard English text in LICENSE governs.

An identical [LICENSE](plugins/delegate/LICENSE) is included in the plugin directory so standalone distribution or installation also carries the license.
