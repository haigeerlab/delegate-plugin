# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Unreleased changes after v0.10.0 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: Rechecking snapshot reviews (interface 1.6) -->

This is a minor release after v0.10.0. **Snapshot reviews such as Plan reviews (`--paths`/`--spec`/`--plan` without `--base`) can now be rechecked with `--previous-report` after rework, and the prompt says that reference files passed with `--spec`/`--plan` are only for verifying references.** The interface goes from `1.5` to `1.6`, additive only; report `schema_version` stays `1` and the report shape is unchanged.

The cause: module-crew reported that every Plan review recheck after rework failed with `previous_report_scope_mismatch` (ecosystem ledger S108). A snapshot review records `from = to = HEAD at the time`; rework moves to a new commit, while v0.10.0 required the same `from` in both rounds. The spec and plan were approved by the user in the owner session; the contract is in the [review-snapshot-recheck spec](../SPEC-review-snapshot-recheck.md).

## Changes

### Rechecking snapshot reviews

- When both rounds are snapshots (`from == to` each), only `paths` and `mode` are compared and the commit may move forward; the previous commit must be a full object id (40 or 64 hex digits), a commit object in the local repository (tag objects are rejected), and the current commit or an ancestor of it. The check ignores `refs/replace` and never fetches missing objects.
- If one round is a snapshot and the other a range, `previous_report_scope_mismatch`, even with the same `from` (v0.10.0 let this through).
- Range (`--base/--head`) and uncommitted-mode rechecks are unchanged.
- Snapshot reviews have no patch, so `scope.fingerprint` is the same every round; to confirm the files changed, compare the sha256 values in both reports' `scope.files`.

### Reference-file note

- When `context_files` is non-empty, both backends' prompts (including the guest path) add a fixed note: these files only serve to verify references and claims in the reviewed files; do not report findings on them; files also within scope are reviewed normally. With empty `context_files` the prompt is byte-identical to v0.10.0. It is a prompt constraint only; validation does not reject findings on reference files.

### Interface 1.6

`interface.json` `review.recheck` gains `"snapshot": true`; a delegate without this key does not support snapshot rechecks.

## Impact

- Callers (module-crew Plan reviews, autopilot) can recheck snapshot reviews with `--previous-report`; detect support with `review.recheck.snapshot`. Passing a snapshot report to a range recheck with the same `from` is rejected from this release on.
- Without the new option and without reference files nothing changes; no migration needed.

## Validation and known limitations

Every behaviour was tested first and seen failing before the implementation (exceptions are noted in the module todo). `test-review-recheck.py` and `test-review-cli.py` use disposable git repositories (including a SHA-256 repository, annotated tags, `refs/replace` and a partial clone) and stub backends to cover passing and every rejection; the prompt is asserted on the Codex, Claude Code and guest paths.

**Not tested live:** whether real models follow "no findings on reference files"; the guest path (needs a disposable VM). Per the usage draft, after release run U3 with the installed version (calls Codex, paid) for the user to judge.
