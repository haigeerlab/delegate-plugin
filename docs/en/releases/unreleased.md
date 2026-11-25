# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Technical design review and second reviewer (interface 1.7) after v0.11.0 is recorded in [v0.12.0 release notes](v0.12.0.md). Reference files no longer need a coverage report after v0.12.0 is recorded in [v0.12.1 release notes](v0.12.1.md). Review failure localization diagnostics after v0.12.1 is recorded in [v0.12.2 release notes](v0.12.2.md). Unreleased changes after v0.12.2 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: Fix Claude Code backend reviews always failing on macOS -->

## Fix Claude Code backend reviews always failing on macOS

Since v0.10.0, `review --backend claude-code` on macOS ended `failed` every time, reviewing 0 files, with only `stream_empty_or_oversized` in diagnostics (plus `backend_exit_nonzero` since v0.12.2). The supervisor runs from a few code files staged in a private directory, but imports later added to `review_result` (`review_recheck`, `review_context` and others) were not staged with them; the supervisor raised `ModuleNotFoundError` on its first init-event check and then cleaned up the original CLI it had just started.

This release moves the init-event check into `review_init.py`, which depends only on the standard library, and the supervisor now stages only `review_macos.py`, `review_init.py` and `claude_review.py`; the guest staging list gains `review_init.py`, `review_fingerprint.py`, `review_recheck.py` and `reviewer_select.py`. An unexpected supervisor exception now records the fixed code `anchor_internal_error` instead of empty diagnostics. The contract is the "Missing modules in staged supervisor code" section of the [spec](../SPEC-claude-review.md).

## Impact

Only Claude Code backend reviews (the macOS native path and the guest path) change. The Codex backend and run are unaffected. Review behavior, report fields and the interface version (1.7) are unchanged.

## Validation and known limitations

A new import-closure test copies each staging list into an isolated directory, imports its entry modules and statically scans every import statement in the listed files (including lazy imports inside functions); both lists failed before the fix and pass after it. The init-check functions exported from `review_result` are still the same objects, and the supervisor fallback diagnostic has an offline test. The real Mac fixtures that need `--srt` are run separately; there is no Lima environment on this Mac, so the guest path only gets the import-closure test. The rerun with a real model happens after release, with the installed version.
