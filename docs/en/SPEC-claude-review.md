# Specification: claude-review (optional Claude Code review backend)

[简体中文](../../spec/claude-review.md) | English

**Current release, 2026-10-16:** v0.5.1 fixes the Claude backend being refused when a Claude Desktop session injects the official `ANTHROPIC_BASE_URL`; see the [release notes](releases/v0.5.1.md). Free validation passed 162 Python / 53 shell / 19 eval with no new model calls; a complete Claude backend doctor run and real reviews inside Desktop remain unverified.

**v0.5.0 release, 2026-10-14:** v0.5.0 is published. Commit `c59b370` is on main and the development branch, with both local 0.5.0 installations matching source. Free release validation passed 157 Python / 53 shell / 19 eval cases, followed by 16 installed-entry checks and 48 result regressions. Release added no model runs; S2/S6/S7 retain their frozen source scopes. See the [delivery status](../verification/2026-10-13-delegate-delivery-status.md) (Chinese).

**Current acceptance criteria, 2026-10-14:** The user explicitly approved the layered acceptance revision. CR-03/06/09 follow the layers below, with production permissions, tool sets and product tests unchanged. Active model Write/recursion, auth refresh, natural helper variants, unresolved historical causes and long-term stability remain individually unverified; this does not retroactively pass the old criteria. S7 menu-to-script execution and the complete dry-run output are verified, with the failed automatic input/concurrent submission retained. Earlier status paragraphs retain their original versions/criteria; the module todo and evidence mapping contain current conclusions.

See [plan](../../tasks/claude-review/plan.md), [actual task results](../../tasks/claude-review/todo.md) and [ADR-002](decisions/ADR-002-claude-review-isolation.md). New commands, files and requirements below are an implementation contract, not current installed capabilities or passing tests.

## Goal and scope

- Exactly two execution backends: `codex` and `claude-code`. Host and backend are independent; selection is explicit and defaults to Codex.
- Claude v1 reviews defects, regression risks, Spec/Plan/implementation consistency and evidence within a specified scope. No automatic edits, fixes, commits, pushes, PR creation/merging or issue changes.
- Preserve existing Codex free-text and `--write` behavior. Introduce a common structured read-only review mode with equivalent context and results for both backends.
- Spec Guard only tracks development and context; do not expand its executor or add a runtime dependency. No automatic opposite-host routing, third backend, general scheduler, background queue or unlimited retries.
- V1 supports native Mac Claude only; macOS 15.7.3 arm64 was tested. Use existing CLI/local authentication and an independent kernel coalition, without expanding Linux/Windows support or preparing dependencies automatically. Old Linux/SSH checks are historical evidence. Preserve existing Codex platforms/default behavior.

## Dual-backend command interface (v0.5.0)

The user approved this interface revision with “继续”. Source slash commands are `/delegate:review`, `/delegate:run`, `/delegate:doctor`, and `/delegate:help`. Both review backends are read-only. Run preserves existing Codex free-text and explicit write behavior; Claude run is rejected. The source `/delegate:delegate` command is removed. Old codex-exec.sh and delegate-exec.sh calls without subcommands remain valid. Both hosts use the same source commands and public wrapper; host-generated installation caches do not update with source changes. Four-entry display and S7 menu-to-public-script/dry-run were verified; error-free automatic UI input remains unverified.

These slash spellings belong to Claude Code. Codex 0.162.1 migrates them to `source-command-review/run/doctor/help` skills, selected through the host's skill picker with the same arguments. Use the loaded inventory for display names; Codex's built-in `/review` is not this plugin entry. Parameters and script behavior are shared, without promising identical slash aliases. All four Codex migration artifacts and Claude CLI session-only source initialization were checked. Subsequent menu-to-public-script execution and complete dry-run output were verified; see [S7 readback](../verification/2026-10-14-delegate-s7-output-readback-result.md) (Chinese). Original automatic-input failures remain recorded. Help/doctor/dry-run do not call an execution-backend model; interpreting them can still consume primary-host model usage.

```text
/delegate:review --backend claude-code --paths src/payments --model sonnet
/delegate:review --backend codex --base main --head HEAD
/delegate:review --paths src/payments --module payments --spec spec/payments.md --plan tasks/payments/plan.md --dry-run
/delegate:run --write Apply the agreed fix and test it
```

The equivalent terminal entry is `delegate-exec.sh review|run`. Backend defaults to codex independently of host; model selection is separate, with no fallback. Two explicit entries in delegate_capabilities.py describe backend capabilities and options for help, doctor and validation. There is no dynamic registry or general scheduler.

Public commands and legacy `codex-exec.sh` share model ownership validation: known families and aliases are recognized case-insensitively through provider namespaces, preventing cross-backend selection without rewriting the supplied slug. Unknown custom slugs are validated by the selected backend CLI; failure never switches backend or model. Claude's automatic model-switching `opusplan` mode remains unsupported.
Git status may expose repository-wide dirty flags, but transport-path validation applies only to non-excluded files in the requested scope and explicit context. Unsupported names outside that scope or in exclusions do not block review. Unsupported selected paths still fail explicitly; Git-output and snapshot limits remain unchanged.

| Review option | Contract |
|---|---|
| `--repo` | Target Git worktree directory; default discovers the root from the current directory |
| `--paths` | Repeatable, one root-relative file/directory per occurrence; no `.`, wildcards or traversal |
| `--module` | Module label requiring paths; cannot combine with commit diff |
| `--base` / `--head` | Fixed commit diff; base required, head defaults to HEAD; resolved SHAs recorded |
| `--changes` | staged, unstaged or working-tree; mutually exclusive with base/head |
| `--include-untracked` | Only working-tree; explicitly includes untracked files |
| `--exclude` | Repeatable explicit exclusions |
| `--spec` / `--plan` | Repeatable context files under the same baseline/version policy, within the repository; exclusion conflicts rejected |
| `--criterion` | Repeatable acceptance criteria; empty list means no additional criteria |
| `--context` | Advanced original JSON; mutually exclusive with all scope shortcuts, but allows backend/model/limit options |
| `--dry-run` | Model-free input preview; no authentication/runtime checks and no review snapshots, logs or reports |

Paths/module alone read the specified HEAD files, excluding uncommitted content while still exposing repository dirty state in the preview/common context. Explicit changes selects workspace versions and retains paths/module type. Base/changes without paths derives only changed paths from that comparison (untracked only if explicitly included), never a project scan. An empty comparison returns conditions_missing/inconclusive without starting a model. The optional task defaults to a fixed read-only review instruction and never infers additional scope.

Shortcuts build the same schema_version=1 data as advanced JSON and reuse validate/capture/snapshot/result. Shortcut tools default to Read only, with the existing complete stop-condition set. Conflicting arguments, mixed backend options, missing scope and invalid paths are rejected. Review always rejects write. Existing authentication, OS isolation, executor restrictions and deadlines remain intact.

Preview has kind=review_preview and backend_started=false. It includes scope, baseline, file/diff hashes, collection omissions, dirty-state policy, permissions, requested model and stop conditions, without source/diff bodies or findings. Requested effort/turn/estimated-budget limits are exposed; missing limits are not actual usage. Host/observed model information remains unknown without execution evidence. backend_preflight=not_performed; a capability description is not readiness evidence. Existing Spec/Plan files cannot hide an empty primary review scope: collection omissions identify it and normal execution stops before model startup. Normal review returns the common report; run retains legacy free-text/Git verification. test-review-cli.py joins free aggregate validation; real host verification of the new entry is separate.

## Codex review input repair (2026-10-10)

The real Claude→Codex direction ran once but failed to review: no authorized local Read tool was available, while command execution was prohibited. All four files were unreviewed. Host ancestry/generation passed, backend_started=true and usage was reported; this is no longer an unexecuted test. See the [first reverse run](../verification/2026-10-10-claude-review-mac-reverse-first.json). On 2026-10-12 the repaired reverse review completed 4/4 with a checked core defect; see the [latest evidence](../verification/2026-10-12-claude-review-mac-reverse-fourth-success.json). The first failed run remains historical.

Codex common review now receives original paths, SHA-256 and UTF-8 contents directly from the validated bounded snapshot as JSON data over stdin. No Bash/MCP access is needed to obtain content, and scope/code execution is not expanded. Claude retains restricted Read/Glob/Grep access to the same snapshot. Both backends receive equivalent actual file information. Codex serialized input is capped at 1 MiB including task, metadata, diff and files; excess returns codex_inline_input_limit before CLI/model startup, without truncation or automatic batches. Dry-run shows transport, prompt byte size and cap, without content.

Codex review explicitly disables shell_tool, apps, plugins and multi_agent, disables web_search and sets empty MCP configuration, retaining the read-only sandbox. Model-free features list with the same settings must report each of the four switches uniquely as false; unsupported/enabled/invalid/failed probes return codex_review_tools_unverified without model startup. CLI 0.160.1 switch output was verified locally. This does not verify a live model's actual tool inventory or claim every control tool disabled. Legacy Codex run/free-text remains intact. Process logs do not retain real input contents.

A stderr summary exposes status/backend/started/reviewed and unreviewed counts/availability of backend usage, while stdout remains the machine-readable report. Usage with no review is not a pass. Product host=unknown and the separate acceptance harness's verified host describe different evidence; harness facts are not blindly copied into product output.

## Stack, files and command

Use Bash 3.2, Python 3 standard library, Git and existing source conventions; Python runs with `-B`. Avoid unrelated refactoring. The user installs the original CLI; the plugin does not install, upgrade, log in or change plugin state.
Claude support baseline is `2.1.295`, subject to actual required-flag checks; this is not claimed as their introduction version. Validate new Codex review capabilities without imposing an unconfirmed minimum on legacy calls.
`srt` is an optional Claude-only dependency, fixed at 0.0.79 with Node >=22.12.0. The current original local CLI 2.1.296 passed model-free version/capability/authentication checks under the strict boundary; a limited normal model review succeeded, while complete security acceptance remains unfinished. The minimum inspected compatibility baseline remains 2.1.295. Require a user GUI launchd domain and verified private Darwin libproc capabilities. Unexpected ABI/identity/counts stop execution without group-only fallback. The tested matrix is only this Mac; private ABI is not claimed stable across versions.

Current candidate responsibilities, relative to `plugins/delegate/` (fake CLIs are generated in temporary fixtures):

```text
scripts/delegate-exec.sh          → thin common entry
scripts/delegate_backend.py       → backend-specific arguments and dispatch
scripts/delegate_model.py         → shared model ownership checks for public and legacy entries
scripts/review_execution.py       → common Codex review and private artifacts
scripts/review_native.py          → native CLI/dependencies/policy integration
scripts/review_macos.py           → temporary launchd, kernel coalition, generation signals and cleanup
scripts/review_doctor.py          → backend-specific diagnostics without a model
scripts/review_context.py         → context validation, read-only Git, snapshots, path mapping
scripts/review_result.py          → shared result validation, evidence, redaction and rendering
scripts/claude_review.py          → Claude checks, argv, stream parsing and execution
scripts/review_isolation.py       → per-run srt policy, capability probes and launch
tests/test-claude-isolation.py    → actual OS permissions without a model
tests/test-review-backends.py     → dispatch, compatibility and arguments
tests/test-review-context.py      → scope, Git, snapshots, paths and input changes
tests/test-claude-review.py       → fake Claude responses and faults
tests/test-review-native.py       → native dispatch/cleanup failure/atomic control facts
tests/test-review-macos.py         → actual model-free Mac lifecycle/permissions
tests/test-review-mac-integration.py → actual public path with fixed fake CLI, no models
tests/test-claude-mac-probes.py     → pinned original local CLI model-free authentication
tests/test-review-lifecycle.py    → preserved native Mac failure evidence
tests/test-review-execution.py    → public end-to-end fake CLI/native boundary
tests/test-review-result.py       → result/model/coverage/location faults
tests/test-review-artifacts.py    → minimal artifacts, permissions and retention
```

Paths are relative to plugins/delegate. Reuse backend.py Codex checks and the old run_codex.py without changing defaults. Claude uses a per-job native resource coalition; old process-group/Linux/SSH fixtures do not prove this route.

```bash
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh "A decided Codex task"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend codex --write "An authorized Codex write task"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend claude-code --review-context /path/to/review.json --model sonnet "Review the specified scope"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend codex --review-context /path/to/review.json "Review the same scope"
```

| Option | codex | claude-code |
|---|---|---|
| `--backend` | Default `codex` | Explicit `claude-code` |
| `--model` | Codex model; selected CLI validates availability | Claude alias/ID; selected CLI validates availability |
| `--effort` | Preserve existing configuration, validate backend-specific values | Reject in v1; no forwarding or silent lowering |
| `--write` | Preserve legacy behavior; reject in structured review mode | Reject |
| `--review-context` | Optional; selects common read-only review mode | Required |
| `--max-turns` | Reject | Default 12; positive integer |
| `--max-budget-usd` | Reject | Optional positive finite number; client estimate can be exceeded |
| `--` / `--help` | End argument parsing / model-free help | Same |

Accept only defined options, with no arbitrary Claude flag passthrough. Validate before probing/executing. Reject obvious cross-family model names locally; other unavailable models fail through the selected CLI without dropping arguments or retrying. An omitted requested model is “default”; observed model still requires CLI evidence.

## Input and fixed scope

Context JSON uses `schema_version: 1`; reject unknown fields, wrong types or ambiguous scope. It is data, not executable configuration, and cannot carry commands, credentials or permission overrides.

| Field | Contract |
|---|---|
| `repository` / `working_directory` | Normalized absolute paths within the same valid Git working tree |
| `review_type` | `diff`, `module` or `paths` |
| `scope` | Included/excluded paths, module identity when needed, and diff boundary; never default to the whole project |
| `baseline` | Resolvable commit/branch or staged/unstaged comparison; record resolved SHA, HEAD and diff hash |
| `context_files` | Explicit Spec, Plan and acceptance files; empty means none provided |
| `acceptance_criteria` | Bounded review criteria |
| `uncommitted_changes` | Explicit inclusion/exclusion of staged, unstaged and untracked changes |
| `allowed_tools` | Subset of the fixed read tools; cannot add Bash/MCP/network/delegation |
| `stop_conditions` | Scope completion, denied permissions, missing context, deadline/turn/budget limits and changing inputs |

Diff reviews fix both endpoints; module reviews require file boundaries; project-range reviews enumerate paths. Missing context is reported to the host; the reviewer does not wait for answers or widen the scan.
The wrapper collects required read-only Git facts with fixed argv, disabling optional locks, external diff, textconv, fsmonitor and hook execution entry points. No user scripts, fetch or Git-state changes.
Copy regular files within scope into a snapshot; no source symlinks/hardlinks or real `.git`. Hash files and retain source mappings; changing inputs during capture abort. Binary files, submodules, out-of-scope links, disappearance, read errors and resource limits are unreviewed scope, never evidence of no findings.
Both backends receive equivalent task, scope, baseline, criteria, exclusions and stop conditions; CLI details may differ. Legacy free-text Codex calls retain their contract and do not imply structured “no findings.”

## Permissions, context and authentication

Run Claude in the snapshot with planned flags `-p --safe-mode --restricted --permission-mode dontAsk --permission-prompts none --tools Read,Glob,Grep --disable-slash-commands --strict-mcp-config --mcp-config <empty-config> --no-chrome --no-session-persistence --output-format stream-json --verbose --json-schema <common-schema>`.
Per-run settings disable ordinary hooks, connectors, Artifact, model fallback chains and content-triggered switching: `switchModelsOnFlag=false`, `fallbackModel=[]`. Do not use `--bare`, Plan, bypass permissions, resume or background mode. Ignored settings or unexpected available tools prevent success.
File tools supply only the requested Read/Glob/Grep subset. Write, Bash/PowerShell/REPL, MCP, Web, Skill, Agent, task/issue, workflow and monitoring tools are unavailable. Init validation also permits only StructuredOutput and EndConversation: the former supplies schema output; the latter is the session-ending tool which official documentation says a nonempty `--tools` list cannot remove. Neither grants file, execution or delegation capabilities; early termination without a complete result remains incomplete. Other tools, duplicate/invalid tool lists or nonempty MCP lists still stop execution immediately. [CLI reference](https://code.claude.com/docs/en/cli-reference), [tools reference](https://code.claude.com/docs/en/tools-reference#endconversation-tool-behavior).
Initialization failures retain fixed reason codes only, distinguishing empty, non-JSON, oversized output, a first event other than init, invalid tools, mismatched tools and unverified MCP. Do not retain raw fields, paths, error text or tool inputs.
A network-denied original 2.1.296 startup probe reproduced passive `system/ui_invalidate` events (event=`ui.render`) before init. Permit at most 8 such events, with only type/subtype/event and optional UUID-formatted uuid/session_id fields; the whole startup sequence through init is bounded to 64 KiB. A unique valid init with verified tools/MCP remains required. Hooks, plugin installation, control requests, model messages, unknown events or extra payloads cannot be skipped. Runtime and final parsing share validation; timeout, cancellation or a missing init still cannot pass.
Context control disables automatic CLAUDE.md, skills, plugins, memory and project customization. Explicit rules/code/diff/Issue/web/log contents remain review data, not instructions.
The original native Mac CLI uses existing local authentication without credential reads/copying or automatic login by delegate. srt grants its native authentication runtime read-only access to .claude, .claude.json and Keychains. Exact/recursive Read denies cover all runtime grants, with blockReadsOutsideWorkingDirectories enabled. Official Read coverage of Grep/Glob is described as best effort, not an OS allowlist; actual model-tool behavior remains a live gate. V1 rejects custom authentication directories, API/provider environment overrides and local managed configuration instead of silently dropping them or changing authentication. Sole exception: Claude Desktop Code sessions inject `ANTHROPIC_BASE_URL=https://api.anthropic.com`; the value is accepted only when it normalizes to the CLI default endpoint (https scheme, host case-insensitively equal to api.anthropic.com, empty port or 443, empty or `/` path, and no userinfo, query, fragment or whitespace). The child environment never inherits the variable, so accepting it does not change the actual endpoint; any other value still yields native_authentication_environment_unverified.
srt wraps the entire native Claude process; source/Git, user configuration, Keychains and snapshot are unwritable. Only the dedicated writable directory and necessary standard descriptors are writable; reviewer access to control is denied. Close extra srt default write paths. chmod and post-execution hashes do not replace enforcement.
Network access permits only verified execution/authentication endpoints, with no task network tools or inherited broad proxy/server exemptions. Ordinary model execution passed in batch four; authentication refresh, endpoint coverage and abnormal TLS remain unverified. Failed isolation, unknown provider policy, or managed hooks/helpers/settings preventing proof yield missing conditions; do not bypass policy or widen access.
The original CLI checks authentication in the same execution environment. Do not read/copy credentials or print raw auth output/fragments; retain only safe method/provider/status fields. Do not infer or switch between login, API key and other methods. Preflight cannot guarantee service, quota or model access; blocked refresh fails explicitly.
Host identity needs trustworthy host metadata; otherwise unknown. Plugin paths, installed CLIs and model self-identification are not proof. Both host entries share the contract without automatic backend selection.
Reject nested delegation at every delegate entry with a depth marker. Claude lacks execution/delegation tools and plugin loading. Legacy Codex discipline is not an unbypassable permission lock.

## Results, failures and logs

Shared review results use `schema_version: 1`; the wrapper owns execution metadata, rather than trusting model claims about exit status, identity or usage.

For Claude error terminals, preserve the fixed permission_denied fact from a nonempty permission_denials list before rejecting the result, without exposing tool input. Preserve claude_error_* codes for the four known error subtypes and claude_api_* codes for known assistant.error enums in a failed terminal stream, alongside backend_result_error. Unknown/malformed fields never become diagnostics; raw errors/message text is not retained. Generic error_during_execution does not establish an authentication, quota or service cause. Recovered assistant errors do not turn a successful terminal into failure; no retry or backend switching is added.

| Field | Meaning |
|---|---|
| `execution_status` | `completed`, `conditions_missing`, `failed`, `timed_out`, `cancelled` |
| `review_outcome` | `findings`, `no_findings_in_scope`, `inconclusive` |
| `host` / `backend` | Verified host or unknown; actual selected/started backend, with prelaunch failure explicit |
| `execution_environment` | Current native execution; verified CLI versions are separate, without guessed OS/host |
| `cleanup` | confirmed/unverified and necessary cause; unverified cleanup prevents success |
| `requested_model` / `observed_models` | Request separate from CLI evidence; aliases do not prove a version; missing evidence is unknown |
| `scope` / `reviewed` / `unreviewed` | Fixed baseline and coverage; gaps carry reasons |
| `findings` | Title, original repository path, checked line, trigger, impact, evidence, advice and unverified items |
| `diagnostics` / `limitations` | Safe failure classes and limits; cleanup uses the single `cleanup` field |
| `usage` | Only reported fields with clear semantics; missing is not zero and estimated cost is not billing |

Exit 0 is not review approval. `no_findings_in_scope` requires completion and full coverage. Permission denial, turn/budget exhaustion, partial coverage, empty output, missing terminal result, `is_error`, parse/schema failures cannot produce it. Preserve findings from partial work, but classify the overall review `inconclusive`.
Verify locations against the snapshot or an explicit diff side; unverifiable locations are marked accordingly, without invented lines. JSON validates form, not truth. The host must assess findings; conclusions never authorize merge/delivery.
Missing/unsupported CLI, isolation or prelaunch conditions yield `conditions_missing`; postlaunch auth/quota/service/nonzero failures yield `failed`. Exit codes: argument error 64, missing CLI/dependency 127, other failed/incomplete work nonzero, normal completion (including findings) 0, timeout 124, INT/TERM/HUP 130/143/129. Preserve the backend exit code separately.
Both backends generate an output schema from the current snapshot: enums for reviewed, unreviewed.path and findings.file contain only original paths, excluding the data/ prefix, exclusions and runtime paths. Empty snapshots do not generate invalid empty enums and remain incomplete. Coverage must not duplicate paths or overlap reviewed/unreviewed lists; the wrapper merges collection omissions and still enforces semantic validation. Schema compliance does not prove a review true. Coverage failures retain fixed detailed codes without arbitrary paths or raw text. Model/usage metadata supplied by the validated unique terminal event is retained before answer semantics are checked; errors, limits and bad coverage still fail, while absent metadata remains unknown, never zero by inference.

Preflight checks are bounded to 5 seconds each. Reuse the 540-second execution default/maximum and 600-second outer deadline. Record wrapper cause before bounded TERM/KILL cleanup of this run's Claude, isolation runtime and helpers; srt signals may yield exit 0 and cannot identify cancellation.
Before startup, a temporary launchd job proves its distinct resource coalition and sole trusted anchor. Reviewer fork/setsid/double-fork processes and srt/proxies retain that kernel ownership. Cleanup uses PID-generation STOP signals, proves all reviewer members stopped and enumeration equals kernel task count, then KILLs and verifies counts. Remove this unique job and confirm zero tasks; incomplete ownership/count/cleanup never succeeds. Preserve cancellation signal; the anchor has a finite deadline. Uncatchable SIGKILL does not promise immediate cleanup; system XPC services are not owned descendants and are not killed by name. No installation into user LaunchAgents or global configuration writes.
Test normal exit, TERM resistance, parent-first exit, descendants holding output and detached helpers. Report survivors or unverified ownership; do not claim complete cleanup or kill unrelated sessions. No automatic rerun, backend switch or reduced model parameters.
Store `.answer`, `.report.json` and filtered `.log`, directories 0700/files 0600, rejecting log-root symlinks. Default logs retain essential events/classes, not full inputs, thinking, tool responses, raw auth or raw stderr. Remove temporary snapshots after execution, retaining only needed hashes/scope/diagnostics. Reuse the latest-50-group retention with a log-size cap. Logging failures cannot become no findings.

## Verification and boundaries

**Always:** reproduce failure branches; fake CLIs and temporary Git projects for free tests; separate OS permission and model tests; consistent bilingual/native entries; check only evidenced completion.
**Ask first:** dependency installation/upgrades, real model/quota calls, delegation, commits/pushes/releases/external writes; stop at failed isolation gates or changed approved decisions.
**Never:** alter global configuration, real issues or archives; substitute allowedTools/prompts/Plan for isolation; bypass permissions; switch backends/models; call stubs/manifest/Hook smoke true cross-backend acceptance.

| Clause | Success and planned verification |
|---|---|
| CR-01 | Compatible default/legacy Codex read/write; backend tests and all existing tests |
| CR-02 | Explicit Claude starts only Claude; invalid/mixed arguments, effort/write fail; no fallback/retry |
| CR-03 | Under the production filesystem policy, controlled reviewer processes actually attempt and are denied writes to source, Git, configuration and snapshot files; only designated temporary paths are writable. Original Claude initialization exposes only allowed read and result/end tools. A real out-of-scope Read denial is recorded separately. Unobserved model Write attempts remain explicitly unverified and are not evidence of OS enforcement. |
| CR-04 | Three fixed scope types; Git does not execute helpers; changes/exclusions/links correct; context tests |
| CR-05 | Normal/findings/denied/limits/empty/malformed/errors classified; fake Claude tests |
| CR-06 | Real deadline/cancellation/helper cleanup; lifecycle tests, not just the parent PID. Validate kernel ownership, real deadlines/signals, detached/double-fork/parent-exit helpers and survival of unrelated processes. Report original CLI abnormal runs per version and state-invariance checks. Unobserved natural helper variants, unresolved historical causes and long-term stability remain limitations. Failures and unknown cleanup remain fail-closed. |
| CR-07 | Checked evidence and gaps retained; missing identity/usage unknown; result regressions |
| CR-08 | Credentials absent from logs; minimal retention, permissions, limits and cleanup checked |
| CR-09 | Every public and compatibility delegate entry rejects a nested marker before auth/runtime/model startup. Original Claude initialization exposes no execution, delegation or MCP tools, with project context isolated. The marker is cooperative protection, not an OS boundary. Unobserved model recursion attempts remain explicitly unverified. |
| CR-10 | Codex main session→native Mac Claude and Claude main session→native Codex separately record versions/backend/scope/permissions/results/limits |

Integrate new free, model-free tests into `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`. Native manifest checks: `claude plugin validate .` and `claude plugin validate ./plugins/delegate`.
Live host acceptance needs separate approval and explicitly loaded source. Use fixed small fixtures and verify source/Git/configuration unchanged. Missing auth/runtime/host conditions remain unverified. Different model perspectives do not guarantee accuracy.

## Official sources and historical routes (not current deployment requirements)

Research date: 2026-10-09; local versions and actual free results are in todo. Recheck exact CLI/runtime versions during implementation.
Official sources: [headless](https://code.claude.com/docs/en/headless), [CLI](https://code.claude.com/docs/en/cli-reference), [permissions](https://code.claude.com/docs/en/permissions), [authentication](https://code.claude.com/docs/en/authentication), [SDK](https://code.claude.com/docs/en/agent-sdk/overview), [Bash sandbox](https://code.claude.com/docs/en/sandboxing), [models/effort/fallback](https://code.claude.com/docs/en/model-config), [hooks](https://code.claude.com/docs/en/hooks), [srt](https://github.com/anthropics/sandbox-runtime).
During design srt was absent; the user subsequently authorized a dedicated temporary installation. The actual macOS policy/permission suite passed 13 cases (including 5 unit tests), but detached-helper cleanup failed for timeout, cancellation and parent-first exit. At that time the first implementation gate failed. The old group runner is not enabled for Claude; the later Linux revision is historical, and ADR-004 describes the new native runner. Numeric-proxy fixtures do not establish original Claude DNS/TLS/auth compatibility; both live host directions remain unverified. See [actual evidence (Chinese administrative record)](../verification/2026-10-09-claude-review.md). Nested sandbox-exec denial by the tool sandbox does not mean the host lacks isolation; actual probes ran outside that outer sandbox.
[ADR-003](decisions/ADR-003-review-process-boundary.md) now has design/free-implementation approval for the dedicated Linux VM/service revision; 15 Linux and 2 SSH model-free boundary probes passed in the dedicated temporary environment; original CLI startup/settings/authentication and tool permissions remain unverified. Platform approval is not a support claim. Official SDK/subscription statements have different scopes (ADR); no credential mediation or entitlement guarantees. If strict boundaries cannot be met, present a concrete revised decision rather than weakening CR-03/06.

Linux srt root denyRead preserves kernel directories, so additionally mask `/sys` and `/run`; allowLocalBinding=false does not establish Linux bind denial. The validated arm64 path adds `review_network.py` no_new_privs/seccomp bind/listen prohibition inside srt, failing closed without assuming other ABI support. Trusted per-service ExecStopPost retains end facts in a control directory unavailable to the reviewer, then the wrapper checks kernel cgroup emptiness; early unit collection is not resolved by guessing query results. See the [actual Linux record](../verification/2026-10-09-claude-review-linux.md) for proof and remaining original-CLI conditions. This was the 2026-10-09 stopping point; see below for later Checkpoint 1 acceptance and source progress.

## Executable JSON examples and configuration

As of 2026-10-10 the public backend and doctor use native Mac CLI+srt+coalition, without guest configuration. Prior VM/SSH failures and batches remain historical evidence; see the [native record](../verification/2026-10-10-claude-review-mac-native.md) for Mac boundaries, original model-free authentication and public fake-CLI checks. The normal real -p Codex→Claude review completed in batch four; active prohibited-tool attempts, authentication refresh, dynamic managed policy and a successful repaired reverse review remain unverified. No release or installed copy update occurred.

An explicit context (replace repository/workdir with the business Git root; `scope.include` rejects `.` and wildcards):

```json
{
  "schema_version": 1,
  "repository": "/absolute/business-repository",
  "working_directory": "/absolute/business-repository",
  "review_type": "diff",
  "scope": {"include": ["src/login"], "exclude": ["src/login/generated"]},
  "baseline": {"mode": "commits", "from": "main", "to": "HEAD"},
  "context_files": ["spec/login.md", "tasks/login/plan.md"],
  "acceptance_criteria": ["Failed login must not bypass permission checks"],
  "uncommitted_changes": {"staged": false, "unstaged": false, "untracked": false},
  "allowed_tools": ["Read", "Glob", "Grep"],
  "stop_conditions": ["scope_complete", "permission_denied", "context_missing", "limit_reached", "input_changed"]
}
```

`module` adds a `module` string to scope and still requires file boundaries; `paths` specifies finite include/exclude paths. `commits` resolves two SHAs, requires all uncommitted flags false, and snapshots target blobs rather than current files. `staged` compares HEAD→index with true/false/false flags and index snapshots. `unstaged` compares index→worktree with false/true/false flags; existing staged content is a baseline, outside that diff. `working-tree` compares HEAD→worktree, requires staged/unstaged true and explicit untracked true/false. These three noncommit baselines contain only `mode`. All modes record actual dirty state; omission never silently includes untracked files. Common mode requires HEAD; legacy free-text Codex retains unborn-repository support.

Limits: 256 regular files, 2 MiB/file, 8 MiB snapshot, 1 MiB diff, 64 KiB context JSON, 65536 task characters. Excess file scope fails before execution; binary/link/deleted-target/read failures become unreviewed. Location validation currently covers target snapshot lines; deleted old-side lines are not invented. Files live at `snapshot/data/<original path>` with the same mapping for both backends. Schema/control/logs stay outside the source project. Initial tool event is bounded to 64 KiB; stdout/stderr to 1 MiB with finite monitoring-interval overshoot, not a claimed instantaneous disk quota.

Resolve local dependencies from PATH, or select an existing independent installation without automatic installation/configuration changes:

```bash
DELEGATE_SRT_BIN=/absolute/existing/srt DELEGATE_NODE_BIN=/absolute/existing/node /bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend claude-code --review-context /path/review.json --model sonnet "Review the specified scope"
```

DELEGATE_CLAUDE_BIN may select an existing CLI. All three paths must name existing executable absolute paths and are canonicalized. Old DELEGATE_CLAUDE_GUEST_CONFIG fails explicitly with guest_configuration_no_longer_supported, never silently becoming local execution. Auth status and review use the same file boundary; only safe method/provider fields persist. The latest 2.1.296 claude.ai authentication preflight passed. The cause of earlier 2.1.295 authentication_missing results remains unknown; neither user logout nor the version change as a root-cause fix is established. Refresh and other methods remain unverified. Explicit API key/token/provider/CLAUDE_CONFIG_DIR overrides are rejected in v1 without login fallback; only an `ANTHROPIC_BASE_URL` equivalent to the official default endpoint is accepted (rules under "Permissions, context and authentication"). Only api.anthropic.com:443, claude.ai:443 and platform.claude.com:443 are permitted; no review network tools or broader endpoints. Unverified managed configuration fails without policy bypass.

Backend-specific model validation rejects the opposite model family, opusplan switching mode and invalid syntax. Unknown valid slugs fail through the selected CLI without removing flags/retrying. Claude effort is refused; Codex accepts none/minimal/low/medium/high/xhigh with actual model support enforced by CLI failure. Requested and observed models stay separate; multiple-model evidence or full-ID mismatch prevents completion. Absent model evidence means unknown, never a guessed alias version.

Reports include backend_started (review invocation, excluding version/auth probes), verified CLI version/safe authentication method, and unknown host when reliable evidence is absent. Codex retains cleanup_scope=existing_codex_process_group and its detached limitation; Claude uses cleanup_scope=kernel_coalition and cannot succeed with unverified identity/count/cleanup.

Common answer/report/log use 0700/0600 and at most 50 groups; logs contain only backend/status/safe codes, excluding raw stderr, authentication, thinking, tasks and tools. Confirmed cleanup removes snapshots/run directories. Unknown cleanup preserves trusted control facts in a 0700 directory; raw stdin/stdout/stderr files are deleted; retained_control appears only in the private report, without raw dumps. Findings may contain authorized scope data, not credential diagnostics. Real model calls and Git delivery require separate authorization.

Native execution/doctor use dedicated short 0700 directories under `/private/tmp`, avoiding srt proxy startup failure under the long default Mac TMPDIR. Final answer/report/log still use the common private artifact directory. The actual long-TMPDIR fake-CLI regression failed before the fix and passed afterwards.

2026-10-12 reverse batch-two reconciliation: the recipient reported one fixed driver run; the frozen Claude process had restarted, so the host guard stopped before model execution. Independent checks confirm unchanged four-file/context/Git inputs and absent marker/logs/result. This is not a successful review; a successful repaired reverse review is still unverified. A third batch only has a model-free preview with the current frozen host identity; no new message or model call has occurred. See the [third preview](../verification/2026-10-12-claude-review-mac-reverse-third-plan.md).

## Codex preflight diagnostics and invocation environment (2026-10-12)

Common review keeps codex_preflight_failed and adds a trusted stage code: codex_cli_missing, codex_version_probe_failed, codex_version_probe_timeout/unavailable, codex_login_probe_timeout/unavailable, codex_login_status_failed or codex_login_method_unsupported. These come from controlled check branches, never raw CLI stdout/stderr, credentials, paths or environment values. They retain backend_started=false, conditions_missing/inconclusive and unreviewed scope. The original two-value backend.check API, exit codes and legacy CLI messages remain compatible. An unexecutable version probe does not imply the user is logged out; no automatic installation, upgrade or login occurs.

Reverse batch three verified the actual Claude host ancestry, but Node12 at the front of the recipient Bash PATH prevented the Codex version probe: exit127, all four files unreviewed, no review backend start. Free source-side probes reproduced the Node12 failure and existing Node24.18.0 success; see the [third result](../verification/2026-10-12-claude-review-mac-reverse-third-result.json). A new acceptance driver pins an existing Node path/version/hash only for its child process; no user PATH/config changes and no runtime changes or retry inside the stopped approved batch. Successful repaired real reverse acceptance remains unverified.

### 2026-10-13: local installation paths and supervisor startup

The launchd interpreter may be unable to reopen plugin installation files under Documents. The main session stages only the three trusted supervisor/parser modules review_macos.py, review_result.py and claude_review.py inside the existing private control tree (0700 directory,0600 files), then starts the temporary job there. This step copies no source snapshots, credentials or other user data. The reviewer remains denied read/write access to the entire control tree; tools, network, identity proof, deadlines and cleanup are unchanged. It changes no system permissions, global configuration or authentication and switches no backend. Path-denial and model-free fix evidence is recorded separately; a startup probe does not establish a successful real-model review.

## Appendix: historical continuations (original status, not current conclusions)

**S5/S6 batch, 2026-10-14:** S5 synchronized the Task9l diagnostic fix into both hosts, passing 16 checks and 48 installed result regressions; Task9n standard-workspace validation passed 157/53/19. The S6 diagnostic follow-up verified the specified out-of-snapshot Read tool denial and exact target attribution, with confirmed cleanup. Review coverage was 1/4, failed/inconclusive; complete Task2/6/8 conditions remain unfinished. The causes of S4 and the original S6 authentication failure remain unknown, without a retroactive fix claim. See the [follow-up result](../verification/2026-10-14-delegate-s6-diagnostic-followup-result.md) (Chinese).

**2026-10-13 repair batch:** S2 verified ordinary bidirectional reviews and all four entries on its frozen source. Subsequent CMD-001/CMD-002/DOC-001 fixes passed free148/53/19 checks and are synchronized into both normal installations with 16 model-free checks. They have not been revalidated with real models or reloaded into existing sessions in this batch. Full security acceptance remains incomplete. See the [latest fix record](../verification/2026-10-13-delegate-command-fixes-result.md) (Chinese). Earlier dated status below retains its historical evidence and does not validate these new fixes.

Date: 2026-10-13. Status: native Mac implementation and free verification are complete; both directions have successful limited four-file real reviews. The latest Claude primary-session→Codex0.162.1/Node24.18.0 reviewed 4/4 files, with a checked core defect and unchanged inputs/Git/source; see the [closeout evidence](../verification/2026-10-12-claude-review-mac-reverse-fourth-success.md) (Chinese). The earlier Codex→Claude2.1.296 success covers its pinned historical source/versions only. New slash-host usability, active model write/recursive attempts, authentication refresh and abnormal helpers remain unverified; complete acceptance is unfinished. The latest strict authentication preflight passed; earlier failures retain an unknown cause. Scope is the current Mac; VM evidence is historical. Installation, additional model runs, commits, pushes and releases require separate authorization. The 2026-10-12 isolated Codex source installation succeeded, but native migration generated review/run/doctor only; help was missing. The size overflow is fixed and one native CLI installation produced all four command skills, independently checked in its actual cache. Desktop/Claude new-command behavior remains pending; see the [recheck result](../verification/2026-10-13-delegate-source-load-fixed-result.md) (Chinese).

On2026-10-13, separately authorized normal Codex activation switched to local source and reinstalled it. Four skills/61 files match, with SessionStart only. Claude2.1.296 actually loads four source commands in place from existing user configuration, with no Claude installation/settings changes. Installed preflight functions verified existing CLI/claude.ai authentication and cleanup with networking further denied. SRT still needs an explicit per-invocation temporary path; existing-session UI and model/quota remain unverified. The [batch evidence](../verification/2026-10-13-delegate-local-activation-result.md) (Chinese) does not close full Task2/6/8 acceptance.
