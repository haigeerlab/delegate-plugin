# Development workflow and AI instructions

[简体中文](../development-workflow.md) | English

The repository adopts Spec Guard's local multi-module convention on 2026-10-08 within the confirmed scope. This adds no runtime dependency to the product.
The [adoption plan and tasks](../process/2026-10-08-adoption/plan.md) are administrative records in Chinese. Adoption cannot establish earlier approvals.

## Development entry points

- The authoritative Chinese capability map is [`spec/CAPABILITY-MAP.md`](../../spec/CAPABILITY-MAP.md); module contracts are `spec/<id>.md`.
- Current plans and tasks are `tasks/<id>/plan.md` and `tasks/<id>/todo.md`. Keep modules separate; do not create root `SPEC-*.md` or shared `tasks/plan.md` files.
- `activeModule` in `.agent/state.json` is a local pointer. An empty value selects the next module in build order and does not establish historical approval.
- [AGENTS.md](../../AGENTS.md) supplies Codex project instructions. [CLAUDE.md](../../CLAUDE.md) supplies Claude Code instructions and imports the Chinese workflow. Machine-global configuration is not part of repository delivery.
- Read [Contributing](../../CONTRIBUTING.en.md) and relevant specifications before changing implementation. Keep English counterparts synchronized with Chinese contracts. Preserve Bash 3.2 compatibility, run shell tests with `/bin/bash`, and use Python `-B`.

## Requirements through acceptance

1. Define the problem, scope, exclusions, and success criteria. Review the capability map and specification for new capabilities; keep existing-module fixes within their agreed scope.
2. After specification confirmation, write the module plan, tasks, and verification method. Mark checkpoints `gate` or `report`; an unmarked checkpoint is a `gate`.
3. An interactive `gate` waits for explicit confirmation. A `report` records commands, results, and limits in todo and continues. File existence is not approval.
4. Reproduce behavior defects with a regression before fixing and verifying. Do not weaken assertions or mix unrelated refactoring into the change.
5. Record actual commands, results, unverified items, and evidence locations. The user reviews the actual diff; remote delivery requires its own specific authorization.

Specifications cover objectives, complete commands, directory responsibilities, code style with a real excerpt, testing strategy, and Always/Ask first/Never boundaries, with explicit success criteria and open questions. Headings may be in Chinese; migrating paths alone is insufficient.
Each task states its description, acceptance criteria, verification steps/commands, dependencies, affected files, and scope, normally limited to 1–5 files. Plans describe order, risks and mitigations, checkpoints, and open questions. Maintenance acceptance and product-clause acceptance are recorded separately.
The [contract verification matrix](../verification/2026-10-08-contract-matrix.md), an administrative record in Chinese, maps CH/DET/RT IDs to actual tests and gaps. These are current retrieval IDs rather than historical approval evidence.

Non-interactive `codex exec` must not wait for a person. Complete only authorized work and report omitted write, paid, or remote actions that lack authorization.
The current conversation determines approval. Records may preserve approval wording, dates, reviewed objects, and baselines, but must not invent past approvals.

## Verification

Run free checks from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

Resolve the currently enabled Spec Guard installation before running `phase-guard.sh` and `verify-artifacts.sh`; do not hardcode a cached version.
Structural success, phase `DONE`, and stub-test success describe file layout, current checklists, and deterministic contracts respectively. They do not establish historical approvals, remote publication, or all real-model behavior.
Paid live validation, delegation to another executor, Git commits, pushes, and publishing each require appropriate authorization; this convention grants none.

## History and current checklists

The [archive index](../archive/pre-spec-guard/README.md) preserves eight pre-adoption plans and task files byte for byte, with original paths, baseline commit, and SHA-256.
The `.md.txt` files retain original checkboxes and relative paths; they are neither current navigation nor current tasks. Historical documentation designs remain unchanged.
Current module checklists track adoption and content-completion maintenance. Historical unchecked items, gate approvals, and plugin versions must be assessed separately from evidence rather than marked complete in bulk.
The [historical verification summary](../verification/2026-10-08-history.md) is an administrative record in Chinese that distinguishes local original evidence from the repository-readable summary.

## Optional features and tickets

Documentation baseline, Local ticket ledger, and capability history ledger are not enabled. Their absence is not a violation; this adoption creates no tickets or tracker migration.
Use the corresponding plugin preview and confirmation flow before enabling any of them. Git remotes and phase `DONE` do not determine ticket backends or closure.
