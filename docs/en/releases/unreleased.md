# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Technical design review and second reviewer (interface 1.7) after v0.11.0 is recorded in [v0.12.0 release notes](v0.12.0.md). Reference files no longer need a coverage report after v0.12.0 is recorded in [v0.12.1 release notes](v0.12.1.md). Unreleased changes after v0.12.1 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: Review failure localization diagnostics -->

## Review failure localization diagnostics

When a Claude Code backend review fails, the report now carries extra fixed diagnostic codes that help locate the cause:
- a failed probe adds `probe_stage_version`, `probe_stage_help` or `probe_stage_auth`, naming which probe failed;
- a missing stdout file adds `stream_file_missing`; reading fewer bytes than were written adds `stream_read_short`;
- when the review did not complete, stderr output adds `backend_stderr_nonempty`; when it failed (rather than timing out or being cancelled) and the original CLI exited non-zero, `backend_exit_nonzero` is added too.

Existing codes, `execution_status`, exit codes and report fields are unchanged; byte counts, exit code values and stderr content never enter the report or logs. The contract is the "Review failure localization diagnostics" section of the [spec](../SPEC-claude-review.md).

## Impact

Only `diagnostics` in Claude Code backend review reports changes. The Codex backend and run are unaffected. `diagnostics` is diagnostic information, so the interface stays at 1.7.

## Validation and known limitations

Unit tests cover each of the three probes failing, stdout missing or read short, a non-zero exit and stderr output on an incomplete review, and no codes for stderr output on a completed review. The real Mac fixtures that need `--srt` are run separately. The original failure was not reproduced with a real model; the affected consumer will rerun it after release.
