# Spec: review-snapshot-recheck (rechecking snapshot reviews)

[简体中文](../../spec/review-snapshot-recheck.md) | English

Drafted 2026-11-23. Source: mc-coord #22261 reported that module-crew's Plan reviews are always rejected when a second round passes `--previous-report` (ecosystem ledger S108); the delegate owner confirmed that A9 of [review-recheck](SPEC-review-recheck.md) only covered diff rechecks. The same message asked about out-of-scope reference files, which showed that the review prompt does not say `context_files` are not review targets. The user decided on 2026-11-23 in the owner session to fix both as one requirement ("两条合成一个需求修，从 Spec 开始"), confirmed the summary and assumptions S1–S9 ("按推荐定") and the capability-map insertion ("确认写入"). The Chinese page is the authoritative contract.

## Why

1. **Snapshot reviews cannot be rechecked.** `--paths` (including `--module`) without `--base` reviews a snapshot of HEAD, recorded as `mode=commits`, `from = to = HEAD`. Rework always creates a new commit, so `from` moves, and A9 requires the same `from` in `commits` mode: every snapshot recheck reports `previous_report_scope_mismatch`. Now that automatic takeover covers Plan approval (delegate itself enabled it on 2026-11-23), a blocking Plan finding can only go to a person or start a fresh review after rework.
2. **Reference files may be treated as review targets.** Files passed with `--spec`/`--plan` go into `context_files` and the snapshot; the prompt only says repository files are data, not that these are for verifying references. The model may report findings on them, and callers have to add a sentence to their task text.

## Assumptions

Confirmed by the user on 2026-11-23:

- **S1 New module.** `review-snapshot-recheck`, depending on review-recheck. The approved review-recheck spec text is not edited (that would mark its approval `revised`); this spec relaxes its A9 for snapshot reviews, and the capability map, this spec and the README point to that.
- **S2 What counts as a snapshot.** Both the previous report's and this round's baseline are `mode=commits` with `from == to`. If only one round is a snapshot (the other a range), `previous_report_scope_mismatch`, even when both rounds have the same `from`.
- **S3 What a snapshot recheck compares.** `scope.paths` (`include`, `exclude` and `module`) identical and the same `mode`; the commit may differ. Diff rechecks (`from != to`) and uncommitted modes (`staged`, `unstaged`, `working-tree`) are unchanged.
- **S4 Same history.** This round's `to` must be the previous `to` or a descendant of it (`git merge-base --is-ancestor <previous to> <current to>` exits 0). Otherwise, or when the previous commit is not in the local repository, `previous_report_scope_mismatch`.
- **S5 Reference files are not compared.** `context_files` may differ between rounds.
- **S6 The prompt explains reference files.** When `context_files` is non-empty, both backends' prompts add a fixed note: these files are only for verifying references and claims in the reviewed files; do not report findings on them; a file also within scope is reviewed normally.
- **S7 Interface 1.6, additive.** `interface.json` `review.recheck` gains `"snapshot": true` so callers can detect support. Report `schema_version` stays `1` and the report shape is unchanged. This is a cross-plugin interface change; ecosystem-lead is told once the spec is final.
- **S8 Release 0.11.0.** Tests use stubs and disposable repositories only; nothing paid.
- **S9 Not in scope.** No round counting in delegate; no third status; no relaxing of diff rechecks.
- **S10 Reference files do not count toward coverage (rework, 2026-11-24).** Running U3 of M2 with the installed 0.12.0 failed the whole round: S6 tells the reviewer not to report findings on reference files, so it also did not report their coverage, and the coverage check recorded them as `coverage_not_reported`, giving `review_incomplete`. On 2026-11-24 the user chose option A ("按方案 A 返工"): reference-only files need no coverage report, decided in code rather than by the prompt. See "Coverage".

Depends on [review-recheck](SPEC-review-recheck.md), [claude-review](SPEC-claude-review.md) and [integration-interface](SPEC-integration-interface.md).

## Scope check (replaces A9 for snapshots)

With P the previous report's baseline and C this round's:

1. `scope.paths` differs from this round's `scope`, or P and C have different `mode` → `previous_report_scope_mismatch`.
2. `mode` is not `commits` → pass (unchanged).
3. Exactly one of P and C is a snapshot (`from == to`) → `previous_report_scope_mismatch`.
4. Both P and C are snapshots → P.`to` must be a full object id (40 or 64 lowercase hex digits), a commit object in the reviewed repository (`git cat-file -t` is `commit`; a tag object pointing to a commit is not accepted), and C.`to` or an ancestor of it; otherwise → `previous_report_scope_mismatch`.
5. Both rounds are ranges → P.`from` must equal C.`from` (unchanged).

The check runs before the model starts; failure stays `conditions_missing`, exit 127, fixed diagnostic only. Step 4 only runs `git cat-file -t` and `git merge-base --is-ancestor` (with `--end-of-options`); git error output never enters the report.

**How callers confirm the files changed:** snapshot reviews have no patch, so `scope.fingerprint` is the empty-patch fingerprint every round. For snapshot rechecks compare the reviewed files' sha256 in both reports' `scope.files`; the README and interface caller rules add this.

## Prompt

When `context_files` is non-empty, `task_prompt()` adds this fixed paragraph before `Task:`:

```text
Files listed in context_files are reference material only. Use them to verify references and claims in the reviewed files; do not report findings about the reference files themselves. A file that is also within scope.include is reviewed normally.
```

With empty `context_files` the prompt is byte-identical to 0.10.0. Both backends (including the guest path) share it. It is a prompt constraint only; validation does not reject finding locations on reference files (see open questions).

## Coverage (S10)

A **reference-only file** is a file in `context_files` that this round's `scope` (`include`, `exclude`) does not select. A file under review that is also in `context_files` stays a reviewed file.

- When the reviewer mentions a reference-only file in neither `reviewed` nor `unreviewed`, no `coverage_not_reported` is recorded and the round is not judged `review_incomplete` for it.
- When the reviewer does list one in `reviewed` or `unreviewed`, it is accepted under the unchanged checks (known path, no duplicates, not on both sides).
- Coverage rules for reviewed files do not change: an unreported one is still recorded as `coverage_not_reported`.
- The report's `scope.files` still lists reference files with their sha256.
- Both backends (including the guest path) share the rule, and it applies to `--profile design` too. The interface version and report structure do not change.

## Interface 1.6

On top of 1.5, `interface` becomes `"1.6"` and `review.recheck` becomes:

```json
"recheck": {"option": "--previous-report", "field": "recheck", "statuses": ["resolved", "unresolved"], "snapshot": true}
```

Nothing else changes. A delegate without this key (or below 1.6) does not support snapshot rechecks.

## Commands

```bash
python3 -B plugins/delegate/tests/test-review-recheck.py
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/review_recheck.py     → check_scope: snapshot branch and ancestry check
plugins/delegate/scripts/review_context.py     → task_prompt: note when context_files is non-empty; context marks reference-only files (S10)
plugins/delegate/scripts/review_result.py      → coverage check does not require reference-only files (S10)
plugins/delegate/tests/test-review-result.py   → coverage: unreported reference-only files are not coverage_not_reported; reviewed-file rules unchanged
plugins/delegate/interface.json                → interface 1.6, review.recheck.snapshot
plugins/delegate/tests/test-review-recheck.py  → snapshot pass, not a descendant, missing commit, only one snapshot, diff rules unchanged
plugins/delegate/tests/test-review-context.py  → prompt note before Task:, unchanged when empty
plugins/delegate/tests/test-review-cli.py      → end to end: two snapshot rounds with --previous-report (stub backend); --dry-run too
plugins/delegate/tests/test-interface.py       → 1.6 and the snapshot key
spec/review-snapshot-recheck.md, this page     → contract
spec/usage/auto-takeover-review.md             → U3 and M2
spec/integration-interface.md and English page → pointer to 1.6
plugin README (zh/en), unreleased notes        → snapshot recheck usage and caller rule
```

## Code style

Unchanged: 4-space indentation, standard library, fixed diagnostic codes only (see the existing `check_scope` in `review_recheck.py`).

## Testing strategy

Tests first and confirmed red, then implementation.

- **Snapshot pass:** in a disposable repository, round one is a `--paths` snapshot; after a rework commit round two uses the same `--paths` with the previous report → pass, stub model starts, `recheck` follows review-recheck.
- **Snapshot reject:** current `to` not a descendant (another branch), previous `to` missing, different `paths`, only one round a snapshot → `previous_report_scope_mismatch`, exit 127, no model.
- **Unchanged rules:** diff recheck with a different `from` still rejected; same `from` with a newer `to` still passes; uncommitted modes unchanged.
- **Prompt:** both backends carry the note before `Task:` when `context_files` is non-empty; byte-identical to 0.10.0 when empty.
- **Interface:** `interface` is `1.6`, `review.recheck.snapshot` is `true`, nothing else changes.
- **Coverage (S10):** a stub reviewer that reports only reviewed files and omits reference files → `completed`, with reference files absent from `unreviewed`; an omitted reviewed file is still `review_incomplete`; a reference file that is also in scope needs coverage like any reviewed file. Add one end-to-end `--paths … --spec …` case.

## Concurrency boundary

- Exclusive: `plugins/delegate/scripts/review_result.py`, `plugins/delegate/tests/test-review-result.py`, `plugins/delegate/scripts/review_recheck.py`, `plugins/delegate/scripts/review_context.py`, `plugins/delegate/interface.json`, `plugins/delegate/tests/test-review-recheck.py`, `plugins/delegate/tests/test-review-context.py`, `plugins/delegate/tests/test-review-execution.py`, `plugins/delegate/tests/test-claude-review.py`, `plugins/delegate/tests/test-review-guest.py`, `plugins/delegate/tests/test-review-cli.py`, `plugins/delegate/tests/test-interface.py`, `plugins/delegate/README.md`, `plugins/delegate/README.en.md`, `spec/integration-interface.md`, `docs/en/SPEC-integration-interface.md`, `docs/en/SPEC-review-snapshot-recheck.md`, `docs/en/capability-map.md`, `docs/releases/unreleased.md`, `docs/en/releases/unreleased.md`

## Boundaries

- **Always:** one check and one note shared by both backends; fixed diagnostics only; zh/en contracts, README, interface and usage draft in sync.
- **Ask first:** relaxing diff rechecks; rejecting findings on reference files in validation; editing the approved review-recheck spec text; commit, push, release.
- **Never:** pass two snapshot rounds that are not on the same history; put git error text or paths in diagnostics; decide in delegate that a change may merge or must go to a person.

## Success criteria

- **SR-01:** both rounds snapshots, same `paths` and `mode`, current `to` at or after previous `to` → recheck passes (disposable repository + stub).
- **SR-02:** different history, missing commit, previous `to` a tag object or a malformed id, different `paths`, only one snapshot (both orders, same `from`) → `previous_report_scope_mismatch`, exit 127, no model.
- **SR-03:** diff and uncommitted-mode checks match 0.10.0 (existing RC-03 tests still pass).
- **SR-04:** non-empty `context_files` adds the fixed note before `Task:` for both backends; empty leaves the prompt unchanged.
- **SR-05:** `interface.json` is 1.6 with `review.recheck.snapshot: true`; both plugin validations pass.
- **SR-06:** zh/en contracts, usage draft U3/M2, integration-interface zh/en pointer, plugin README zh/en (including "compare `scope.files`, not the fingerprint, for snapshots") and unreleased notes in sync.
- **SR-07:** full validation, both plugin validations and `git diff --check` pass.
- **SR-08 (S10):** unreported reference-only files are not recorded as `coverage_not_reported` and do not cause `review_incomplete`; an omitted reviewed file is still incomplete; a reference file that is also in scope is handled as a reviewed file (unit + stub end-to-end). After a patch release, rerun all three U3 steps (first round, recheck, rejection on another branch) with the installed version for the user to judge M2.

## Open questions

- Whether the model really avoids findings on reference files: free tests cannot prove a prompt constraint; observe in the pilot, and propose a hard check separately if needed (Ask first).
