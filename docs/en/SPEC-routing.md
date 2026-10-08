# Specification: routing (proposal-based executor routing)

[简体中文](../../SPEC-routing.md) | English

Current contract: 2026-10-08. Depends on detection and channel; historical `tasks/routing/` records do not replace this contract.

## Goal

Have the model consider delegation once task decisions are settled, while the user decides whether to execute. The model proposes and waits for an explicit affirmative response. Write mode requires explicit authorization in the current turn. Directly entering a specific delegation command authorizes that task.

These are command and skill instructions, not a wrapper authorization lock that cannot be bypassed. Hooks do not classify tasks, match task keywords, or invoke Codex.

## Implementation

UserPromptSubmit registers only one `prompt.sh` handler: `detect.sh --warm` first, then `route.sh`. Hosts may run handlers for the same event in parallel, so the implementation does not depend on ordering two independent handlers.

`route.sh` reads detection's shared valid-cache contract. When available, it emits one line of valid JSON containing local readiness, confirmation requirements, and a pointer to the delegate-routing skill. Missing, expired, identity-changed, invalid, or unavailable cache produces no output and exits 0 without probing again.

`skills/delegate-routing/SKILL.md` supplies six routing categories and post-execution rules. `/delegate:delegate` executes, `/delegate:doctor` refreshes, and `/delegate:help` provides static help. Hosts that support it may expose the skill itself as `/delegate:delegate-routing`.

## Routing and verification

Reviews, structure exploration, and reproduction/diagnosis can be read-only. A specific implementation task or batch mechanical edits require authorized write mode. Requirements, architecture trade-offs, result verification, and small edits remain in the main session. Read-only sandboxes restrict tests that write caches/files; obtain separate write authorization when necessary.

Do not expand the task scope. After success, inspect the final answer and, for writes, actual Git diffs and tests. After failure, still inspect Git evidence rather than assuming no changes occurred. Read only relevant log lines through the reported path, avoiding reintroducing the full log into context. Bash timeout=600000 milliseconds, coordinated with channel's 540-second execution deadline.

## Deterministic validation

Run the validation and evaluation commands below from the repository root:

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-routing.sh
python3 -B plugins/delegate/tests/test-backend.py
```

The original 9 assertions cover unavailable/missing/expired/invalid cache, single-line JSON, no re-probing, confirmation wording, and skill criteria. Additional backend tests cover cold-cache output in the same turn and the single sequential handler.

## Behavior evaluations and limitations

```bash
/bin/bash evals/propose-not-auto.sh --scaffold-only
/bin/bash evals/routing-fitness.sh --scaffold-only
# The following commands consume model quota
/bin/bash evals/propose-not-auto.sh
/bin/bash evals/routing-fitness.sh
```

_preflight checks that the CLI runs and performs native manifest validation on current source. Evaluations use `claude --plugin-dir <current-source-directory>`; an installed version number does not stand in for source-content loading verification. Scaffolds provide temporary stub CLIs, Git projects, and cache with current identity.

Exit statuses: 0=PASS, 1=FAIL, 2=NORUN. Missing usable output or tool failures are not classified as product failures.

- propose-not-auto's strict criterion is that exec was not called automatically; a proposal is only an observation. A single `claude -p` turn cannot establish interactive proposal behavior.
- routing-fitness compares a batch task with settled decisions against a task still requiring architectural choices. It parses only the complete first nonempty line `判断：委托` or `判断：自己做` (delegate or do it in the main session). Conditional statements, prefixes, or body examples are not verdicts and return NORUN.
- Global user rules and the installed environment may still affect the model; explicitly loading source does not completely isolate evaluation.

See the [v0.4.0 verification record](releases/v0.4.0.md) for real behavior-evaluation samples. Success requires passing deterministic contracts, free evaluators rejecting false positives, and explicit loading paths. “Always propose when appropriate” remains unverified by automated tests.
