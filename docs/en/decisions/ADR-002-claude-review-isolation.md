# ADR-002: CLI, snapshots and whole-process isolation for Claude review

[简体中文](../../decisions/ADR-002-claude-review-isolation.md) | English

See [ADR-004](ADR-004-native-mac-review.md) for current native Mac process control. Initial decisions and later Linux revision context below do not establish historical support.

Status: Accepted (design decision, not implementation/acceptance). Date: 2026-10-09.
Approval: after reviewing the design, implementation plan and three recommendations, the user replied “继续” (continue). This approves CLI, explicit backend selection, snapshots, whole-process isolation, rejection of effort in Claude v1 and macOS-first acceptance. It excludes installation, live calls, delegation and Git/external delivery.

## Context

Current delegate invokes only Codex CLI; the host does not determine the execution backend. Reuse deadlines, logs and process groups, but Claude hooks may create independent sessions, so group cleanup alone is not sufficient proof.
Official `claude -p` supports noninteractive execution. `--allowedTools` is not a complete allowlist. Bash sandboxing excludes file tools/hooks/MCP. `--safe-mode` preserves authentication but may retain managed hooks; `--bare` skips OAuth/keychain. Plan and read-only prompts cannot enforce isolation.

## Decision

Use the original user-installed Claude CLI; do not add Agent SDK simultaneously. A common entry explicitly accepts `codex|claude-code`, defaulting to Codex and preserving legacy behavior. Claude reviews only; reject writes and effort in v1 to avoid silent lowering of unsupported levels.
Reviewers read regular-file snapshots with fixed scope; the wrapper collects read-only Git information. Only Read/Glob/Grep, without execution, network tools, MCP, plugins, subagents or recursive delegation.
srt is an optional dependency required for Claude. It encloses the entire process: source/Git/global configuration unwritable, only per-run temporary paths writable. Override extra default writable paths and verify enforcement. Missing/incompatible/failed isolation refuses execution without fallback.
Do not read, copy or proxy credentials; the original CLI authenticates. If strict isolation conflicts with authentication or managed policy, report missing conditions without changing settings. Originally validate native macOS first; after its lifecycle failure, the user approved [ADR-003](ADR-003-review-process-boundary.md), using a dedicated local Linux VM with service/cgroup and srt. No new environment is runtime-accepted or claimed supported.

## Alternatives and consequences

Launching in source with a read-only prompt is simple but cannot block write tools, customization or helpers. Built-in Bash sandboxing has incomplete coverage; safe-mode/restricted alone cannot prove whole-CLI write boundaries. SDK supplies callbacks/types but still needs isolation and more dependencies, so defer it.
Snapshots cost capture time and omit live changes. Hash fixed inputs; report missing content as unreviewed rather than scanning more. srt adds Node/OS dependencies and authentication risks; pass the free isolation gate before implementing execution. Design approval does not prove the candidate runtime is available.

## Official basis and limitations

Research on 2026-10-09 used [CLI](https://code.claude.com/docs/en/cli-reference), [Bash sandbox](https://code.claude.com/docs/en/sandboxing), [hooks](https://code.claude.com/docs/en/hooks), [models](https://code.claude.com/docs/en/model-config) and [official srt](https://github.com/anthropics/sandbox-runtime).
[SDK documentation](https://code.claude.com/docs/en/agent-sdk/overview) restricts third-party claude.ai login/quota use, while the [help center](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan) says SDK, `claude -p` and third-party use still count against subscription limits. [Credential rules](https://code.claude.com/docs/en/legal-and-compliance) distinguish end-user login through the original CLI from credential mediation. Do not infer unlimited/fixed entitlements or bypass authentication.
During design srt was absent; the user separately approved a temporary 0.0.79 installation. Actual macOS policy/permission tests passed 13 cases, but detached-helper cleanup failed for timeout, cancellation and parent-first exit. Temporary probes outside the outer tool sandbox distinguished nested denial from host support; strict process-lifetime boundaries and original Claude compatibility remain unverified.
The first gate failed and no product entry is connected. The user subsequently approved ADR-003 and free implementation/tests. That decision supersedes native macOS-first acceptance while CLI/snapshots/strict permissions remain accepted. It neither authorizes runtime installation/guest login/live acceptance nor establishes them. See [actual evidence (Chinese administrative record)](../../verification/2026-10-09-claude-review.md) and [tasks](../../../tasks/claude-review/todo.md); Accepted does not mean acceptance complete.
