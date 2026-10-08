# delegate

[简体中文](README.md) | English

A Claude Code plugin that delegates execution and investigation to **Codex CLI** once the scope, approach, and acceptance criteria are settled. The main session receives the final answer; process logs stay on the local machine.

The main session handles requirements, design decisions, and final verification. The plugin accepts only Codex authenticated through ChatGPT. It aims to reduce process context carried by the main session; usage is charged against the account signed into Codex, and lower total cost or token usage is not guaranteed.

Repository: [haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · Current release: [v0.4.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.4.0) · [Documentation index](docs/en/README.md)

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

Flow: basic readiness check → Claude proposes a specific task → user confirms → Codex executes → review the answer and Git evidence → verify in the main session.

Directly entering a delegation command with a specific task also authorizes that task. Commands and the skill instruct the model to request confirmation; the wrapper does not enforce this through an authorization token that cannot be bypassed.

The plugin supports a single, non-interactive, synchronous delegation, model and reasoning-effort selection, read-only defaults, authorized writes, log separation, failure diagnostics, and a Git change summary. **Both modes require a Git working tree.**

It does not provide background jobs, queues, resumption, automatic retries, multiple backends, or team quota management. It does not handle automatic commits, pushes, or publishing, and does not guarantee correct results or adherence to every instruction.

## Prerequisites

| Dependency | Requirement |
|---|---|
| Claude Code | Plugin support and a working `claude` command in the terminal |
| Codex CLI | A working `codex` command on PATH in the same environment, authenticated through ChatGPT |
| Python 3, Git, Bash | Required by the scripts; compatible with macOS Bash 3.2 |
| Target project | A Git working tree; existing uncommitted changes and repositories without commits are allowed |
| Node.js, npm | Required if you use the npm installation method below |

v0.4.0 was verified with Claude Code 2.1.291, Codex CLI 0.160.0, Python 3.10, and Bash 3.2. These are tested versions, not a minimum compatibility guarantee. Windows has not been verified.

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

doctor refreshes local installation and authentication checks and inspects some Chinese-language rules in the global AGENTS.md. It makes no model request. Exit status 0 means diagnostics completed; read the issue count and reasons. Basic readiness does not verify remote connectivity, available quota, or model access.

### 4. Run your first read-only delegation

Enter this in the Claude Code session:

```text
/delegate:delegate Read git status --short for this project and explain the working-tree state; do not modify files
```

This makes a real Codex model request and consumes the signed-in account's quota. On successful completion, expect the final answer, model/effort hints, a process-log path, and byte counts. If no model is specified, the wrapper displays `配置默认` (configuration default); this does not mean it has discovered the actual model name.

For writes, explicitly authorize the current task before using `--write`, then review actual diffs and test results as described in [Output and verification](#output-and-verification).

## Commands and options

Terminal commands beginning with `claude plugin ...` manage installation. The `/delegate:...` entries below run inside Claude Code. Use the full namespace and the command inventory actually loaded by your host. [Official component documentation](https://code.claude.com/docs/en/plugins/components)

| Entry | Purpose | Executes a Codex task? |
|---|---|---|
| `/delegate:delegate [options] <task>` | Delegate one specific task | Yes |
| `/delegate:doctor` | Refresh basic checks and inspect some global Chinese rules | No; CLI status checks only |
| `/delegate:help` | Options, examples, limitations, and troubleshooting | No |
| `/delegate:delegate-routing` | Routing-criteria skill, callable when supported by the host | Criteria only; confirmation is still required |

```text
/delegate:delegate Review error handling in src/payments; report only findings supported by code evidence
/delegate:delegate --write Fix the null dereference using the agreed approach; run relevant tests and report results
/delegate:delegate --model <model-slug> --effort high Trace the login flow
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

Current Claude Code can load relative-path plugins in a local-path marketplace directly from source. Changes take effect in a new session or through `/reload-plugins`. This differs from a remote cached installation, and support depends on the host version. [Official local-loading documentation](https://code.claude.com/docs/en/plugin-marketplaces)

For development and evaluation, you can also explicitly load the source plugin directory from your target Git project:

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

If a marketplace with the same name is already registered, check its source first. Local loading and remote installation are alternatives; you do not need two installations. The `v0.4.0` tag fixes release source at one revision, while `main` continues to change.

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

Wrapper exit statuses: 64 for arguments/non-Git directories; 127 for basic CLI/Python failures; 124 for execution timeout; 129/130/143 for HUP/INT/TERM interruptions. An empty answer exits 1; other execution failures retain their nonzero status. doctor always exits 0; assess the reported issue count.

doctor refreshes the temporary cache and does not modify project files. Its heuristics inspect only some Chinese global rules, not English or all project rules. It does not verify remote connectivity, quota, model access, or whether a token remains valid. Runtime diagnostics and skill instructions currently use mainly Chinese; bilingual documentation does not change these outputs.

## Architecture and documentation

| Module | Responsibility | Implementation |
|---|---|---|
| channel | Invocation, sandbox, process-group deadline/cleanup, answers and logs, Git evidence | `codex-exec.sh` + `run_codex.py` |
| detection | Shared basic checks, identity-bound cache, atomic writes, doctor | `backend.py` + `detect.py` + shell entry points |
| routing | Inject confirmation requirements and a skill pointer based on valid cache | `prompt.sh` → `detect.sh --warm` → `route.sh` + skill |

UserPromptSubmit uses one sequential entry point. The cache lasts 8 hours and is bound to the CLI path, Codex home, plugin root, and version. Future timestamps, old formats, identity changes, and invalid files invalidate it. Cached readiness does not guarantee current authentication; execution always checks login again.

See the [documentation index](docs/en/README.md) for reading order and language pairs. Read [Design](docs/en/DESIGN.md) for rationale and the [capability map](docs/en/capability-map.md) for module responsibilities. Exact contracts are in the [channel](docs/en/SPEC-channel.md), [detection](docs/en/SPEC-detection.md), and [routing](docs/en/SPEC-routing.md) specifications. Release changes are in [v0.4.0](docs/en/releases/v0.4.0.md); subsequent changes are in [Unreleased](docs/en/releases/unreleased.md).

## Development, contributions, and feedback

See [Development workflow](docs/en/development-workflow.md) for both AI hosts and project conventions. Chinese specifications use `spec/<id>.md`; historical records and current maintenance tasks are separate.

Run the free offline validation from the **repository root**:

```bash
/bin/bash scripts/validate.sh
```

The entry point covers syntax, manifest required fields, evaluator self-tests, 3 shell product suites, and 2 Python regression suites. The baseline comprises 24 channel, 19 detection, and 9 routing assertions plus 17 Python regression tests. The free aggregate validation makes no model requests. Doctor rule tests now supply their own CLI stub, synthetic login state, and temporary log, without depending on an outer Codex installation or login. The [actual F8 fix verification in Chinese](docs/verification/2026-10-08-f8-applied.md) covers absent outer CLI and rejected outer login.

See [Contributing](CONTRIBUTING.en.md) for development conventions, individual tests, paid live verification, and bilingual maintenance. Use [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues) for problems and suggestions; follow the next section to report a bug.

## Reporting a bug

Report plugin failures through this repository's GitHub Issues:

1. [Search existing issues](https://github.com/haigeerlab/delegate-plugin/issues) for the same symptoms or a solution. If a matching issue exists, add your reproduction details there.
2. Sign in to GitHub, open [a new issue](https://github.com/haigeerlab/delegate-plugin/issues/new), and summarize the failure in a one-sentence title.
3. Copy the checklist below, fill in enough information to reproduce the problem, and submit it. Reports in Chinese or English are welcome.

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
