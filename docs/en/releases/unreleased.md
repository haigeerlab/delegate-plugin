# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Unreleased changes after v0.11.0 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: Technical design review and second reviewer (interface 1.7) -->

This is a minor release after v0.11.0 for the ecosystem ledger's S110 development-flow rework: a second reviewer checks the technical design against the code, one round of review and one of fixes. The interface goes from `1.6` to `1.7`, additive only; report `schema_version` stays `1`. Without the new options nothing changes.

## Changes

### Technical design review (`--profile design`)

- `/delegate:review` gains `--profile default|design`. `design` uses criteria `design-v1`: a finding is blocking only when it cites a line in a reference file (passed with `--spec`/`--plan` and not under review) that shows the design will go wrong. The contract is in the [design-review-criteria spec](../SPEC-design-review-criteria.md).
- A blocking finding without such a line is recorded as a suggestion marked `downgraded: "no_code_evidence"`, text unchanged; in a second round with `--previous-report` only the previous round is checked and new findings become suggestions (`downgraded: "second_round"`); in the design profile an unlocated finding does not fail the whole review.
- The report gains top-level `criteria` (`severity-v1` or `design-v1`); both rounds of a recheck must use the same criteria, and old reports without it read as `severity-v1`.

### Choosing the second reviewer (`--backend auto`)

- `/delegate:review` gains `--backend auto` and `--author-host codex|claude-code`: model-free checks prefer the other vendor and fall back to a fresh same-vendor session; when neither is available the result is an "unreviewed" report (`conditions_missing`, diagnostic `no_reviewer_available`, `backend` `null`, exit 127) and no model starts. The contract is in the [reviewer-selection spec](../SPEC-reviewer-selection.md).
- The report gains top-level `reviewer: {vendor, backend, same_vendor, selection}` naming the reviewer's vendor, whether it is the same vendor, and how it was chosen.
- `/delegate:doctor --reviewers [--json]` lists the reviewers available on this machine and suggests adding a second vendor when only one is set up; it never blocks anything.
- Reviews always run in a fresh session, so the session that wrote the code never reviews its own work; this replaces the earlier wording "stop when Codex is unavailable, never fall back to Claude reviewing itself".

## Impact

- spec-guard's technical design review (design-review) calls `--profile design` and passes the existing files listed in the design's impact section and the requirement with `--spec`.
- Without `--profile`, prompt, criteria and validation are the same as v0.11.0.
- Report readers: the "unreviewed" report has `backend` `null` (only when `reviewer.selection == "none"`); `auto` may choose `claude-code`, so the review backend is no longer always codex.

## Validation and known limitations

Every behaviour was tested first and seen failing before the implementation. The prompt is asserted on the Codex, Claude Code and guest paths; downgrades, matching criteria on recheck and the end-to-end flow use stub backends and disposable repositories.

**Not tested live:** how accurately real models label against `design-v1`; the guest path (needs a disposable VM). Per the usage draft, after release run M1 with the installed version (calls models, paid) for the user to judge.
