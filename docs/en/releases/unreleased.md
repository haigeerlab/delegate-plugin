# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Technical design review and second reviewer (interface 1.7) after v0.11.0 is recorded in [v0.12.0 release notes](v0.12.0.md). Changes after v0.12.0 follow below. Historical acceptance records retain their original version/status without retroactive approval.

## Reference files no longer need a coverage report

Reference files passed with `--spec`/`--plan` that are outside this round's review scope no longer get `coverage_not_reported` when the reviewer does not mention them, and the round is no longer judged `review_incomplete` for it. Since 0.12.0 the prompt tells the reviewer not to report on reference files, so reviewers left them out and every review with `--spec` (including `--profile design`) ended `failed`. Coverage rules for reviewed files are unchanged; reference files the reviewer lists anyway follow the existing rules; `scope.files` still lists reference files with their sha256. The contract is S10 of the [spec](../SPEC-review-snapshot-recheck.md).

## Impact

Only the coverage check on review results changes, for both the Codex and Claude Code backends (including the guest path). The interface version and report structure are unchanged.

## Validation and known limitations

Unit tests cover a reference file left unreported, listed by the reviewer, a reviewed file left unreported, and a reference file that is also in scope; a stub end-to-end test covers `--paths … --spec …` completing in the default and `--profile design` profiles. The rerun with a real model happens after release, with the installed version.
