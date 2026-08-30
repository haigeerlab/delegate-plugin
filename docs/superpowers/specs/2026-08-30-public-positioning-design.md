# Public positioning documentation design

## Goal

Give a first-time GitHub visitor a concise explanation of why `delegate` exists,
what it delegates, and the safety boundaries that distinguish it from a generic
`codex exec` wrapper. Keep installation and operational instructions in the
README; keep implementation detail and test contracts in the existing specs.

## Audience and success criteria

The audience is a Claude Code user who has not read the repository before.
After reading the public design document, they should understand:

1. the context-economics problem the plugin addresses;
2. the decision-completeness rule for delegation;
3. the detection, routing, execution, and verification flow;
4. the non-negotiable user-control and sandbox boundaries; and
5. what the project deliberately does not attempt to be.

Success means the public positioning can be read independently without
duplicating the complete technical specifications or making time-sensitive
feature claims about third-party projects.

## Proposed changes

### `DESIGN.md`

Add a new Chinese public document at the repository root with five sections:

1. **Why it exists** — explain the mismatch between a main session's durable
   context cost and the execution work that does not require continued judgment.
2. **The routing rule** — delegate only when decisions are settled and the
   remaining work is execution or verification.
3. **How it works** — show the flow: availability detection → suggestion →
   explicit user confirmation → sandboxed Codex execution → concise result and,
   in write mode, Git acceptance evidence.
4. **Safety and control boundaries** — no automatic delegation, read-only by
   default, per-turn explicit write consent, silent degradation, and process-log
   isolation.
5. **Positioning** — define the plugin as a lightweight, single-backend,
   confirmation-driven workflow contract. State that it does not aim to provide
   multi-provider routing, a durable background-job control plane, autonomous
   orchestration, or a broad MCP platform.

The document will link to `README.md`, `capability-map.md`, and `SPEC-*.md` for
installation and engineering evidence.

### `README.md`

Add one short link near the introduction: "设计理念与边界见 DESIGN.md". Do not
duplicate the design content or alter installation, command, or behavioral text.

## Non-goals

- No plugin behavior, command, hook, or test changes.
- No claims that this project is categorically better than any external project.
- No hard-coded competitor feature matrix that will become stale.
- No documentation site or new runtime dependency.

## Verification

1. Check the new document for placeholders, contradictions, and unsupported
   claims.
2. Verify the README link resolves locally.
3. Run the existing repository validation; documentation changes must not break
   the structure or shell checks.
