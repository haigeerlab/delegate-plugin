# Specification: routing (proposal-based executor routing)

[简体中文](../../spec/routing.md) | English


Per-prompt UserPromptSubmit routing reminders are removed. Codex readiness proves neither the host, delegation intent nor Claude availability. Explicit requests use shared commands/skill with independent host/backend selection: default Codex, explicit Claude only for scoped read-only review. No opposite-host auto-routing, parameter/model mixing or fallback; see [claude-review](SPEC-claude-review.md). Explicit delegation and write authorization remain required, without reconfirming the same authorized scope.

Since interface 1.3, write authorization has one exception: when the four conditions listed in [run-check](SPEC-run-check.md) all hold and `--authorized-by <file>` is given, the round counts as authorized; the rules are in the plugin's `references/run.md`, and the `delegate-routing` skill points to them. All other write rules are unchanged.

Current contract: 2026-10-13 (routing reminder fix); 2026-10-08 clauses and samples retain their historical scope. Earlier records are preserved in the [historical archive](../archive/pre-spec-guard/README.md). Current `tasks/routing/` tracks maintenance reconciliation and this fix; it neither retroactively accepts historical work nor overrides this specification.


## Tech stack and commands

Bash 3.2, Python 3 standard library, and Claude Code hooks/skills; detection provides facts and channel provides execution. Paid judge samples require Claude CLI; free self-tests use stubs.
This is a script plugin with no separate compilation build or development server. The existing contract below lists module tests. Aggregate checks and source loading are shown here; loading starts the host and does not delegate by itself.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
claude --plugin-dir "$PWD/plugins/delegate"
```

## Project structure

Paths are relative to the repository root; plugin-relative paths are explained in the original contract.

```text
plugins/delegate/hooks/prompt.sh            → silent compatibility entry for retired hooks
plugins/delegate/hooks/route.sh             → silent compatibility entry for retired routing reminders
plugins/delegate/hooks/hooks.json           → event registration
plugins/delegate/skills/delegate-routing/SKILL.md → six routing categories and confirmation rules
plugins/delegate/commands/                  → review / run / doctor / help
plugins/delegate/tests/test-routing.sh      → Shell stub assertions
plugins/delegate/tests/test-backend.py      → Python unittest cold-cache/handler regressions
evals/                                    → judge self-tests and optional paid samples
spec/routing.md                            → current Chinese contract
docs/en/SPEC-routing.md                    → current English contract
tasks/routing/plan.md / todo.md            → current maintenance steps and records
```

## Code style

Keep existing style without formatting refactors. Preserve Bash 3.2, braced `${VAR}` variables and existing empty-array guards; do not use `cmd | grep -q`. Python uses the standard library, four-space indentation and snake_case functions. Serialize JSON instead of manually escaping it.
This existing excerpt from `plugins/delegate/hooks/route.sh` illustrates actual style (context, not a new command):

```bash
# Compatibility no-op for callers of the retired per-prompt routing hook.
# Commands and delegate-routing handle explicit requests without guessing a host.
exit 0
```

## Development boundaries

- **Always:** Read the contract before editing; reproduce behavior defects before fixing; preserve Bash 3.2 and bilingual contracts; review actual diffs and relevant tests.
- **Ask first:** New backends/dependencies/flags, sandbox defaults or authentication changes, or capabilities outside the module; obtain separate authorization for paid live checks, delegation, commits and remote writes.
- **Never:** Expose credentials or full private logs; weaken failing assertions; automatically roll back user changes; retroactively approve history or edit archives; treat stubs as complete host-behavior guarantees.

## Testing strategy

Shell suites use `stub-codex` and temporary fixtures; Python regressions use standard-library `unittest`. Locations are listed above; exact commands and assertion scope remain in the original contract. No line-coverage percentage is set or invented.
Assess coverage per clause and risk, including positive and negative cases. Source guarantees without independent assertions are marked partially covered in the matrix. Real-model, permission and interaction checks remain separate; paid samples require authorization.

## Goal

Apply routing criteria only when the user explicitly requests delegation, routing, an independent review or executor selection. Settled decisions do not require delegation. An ordinary continuation advances authorized work without an extra delegation gate. New proposals wait for an affirmative response; direct commands and an already authorized scope may proceed. Writes still need explicit authorization.

These are command/skill instructions, not an unbypassable wrapper authorization lock. Identify hosts only through reliable main-session context, not Codex readiness or inherited environment hints. Unknown hosts receive no automatic direction advice. Claude→Codex and Codex→Claude follow explicit targets; the corresponding doctor reports basic conditions without backend fallback. Explicit same-host independent Codex reviews remain possible.

## Implementation

hooks.json no longer registers UserPromptSubmit. SessionStart still silently refreshes Codex readiness. prompt.sh and route.sh remain compatibility entries that exit 0 with no probing or injection, including old registrations referencing new source. No keyword classifier, guessed host, session deduplication state or new setting is needed. Readiness and delegation decisions are separate.

`skills/delegate-routing/SKILL.md` supplies six routing categories and post-execution rules. `/delegate:review` performs read-only reviews through either backend, `/delegate:run` performs existing Codex tasks, `/delegate:doctor` checks the selected backend, and `/delegate:help` reads model-free local help. Hosts that support it may expose the skill itself as `/delegate:delegate-routing`.

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

Ten shell assertions cover silence for every cache state, no re-probing, explicit confirmation and skill/command criteria. Backend regressions cover cold-cache silence without probing, no UserPromptSubmit registration, and 80 compatibility calls across Claude/Codex/unknown/conflicting environments, five prompts, two handlers and two repetitions. Explicit Codex run still starts Codex once in each of two host-environment fixtures. These are not native-host acceptance tests.

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

## Success criteria and verification mapping

The IDs below label existing contract clauses for the 2026-10-08 documentation reconciliation; they are not historical IDs or approvals.

- **RT-01：** Do not register UserPromptSubmit; retired prompt/route callbacks produce no output or probes across hosts, inputs, cache states and repetitions. SessionStart silently refreshes readiness.
- **RT-02：** Skill proposal/confirmation rules apply to explicit delegation requests without automatic execution or reconfirming authorized scope. Readiness/settled decisions must not force delegation or upgrade writes. Text/stubs do not establish complete host compliance.
- **RT-03：** The six routing categories, scope limits, and post-return answer/Git review instructions remain discoverable and consistent with channel arguments.
- **RT-04：** Eval judges distinguish PASS/FAIL/NORUN and reject false positives; single-turn samples do not establish complete interactive proposal behavior.

See the [clause-to-evidence matrix](../verification/2026-10-08-contract-matrix.md) (administrative record in Chinese) for exact tests, implementation references and coverage gaps. The current maintenance plan Task 5 checks this mapping; it does not declare every product clause fully accepted.

## Open questions

Historical task-by-task acceptance, earlier approvals/plugin versions and complete interactive host behavior remain unverified. Current known coverage gaps are listed in the matrix; no new capability or stronger guarantee is introduced here.
