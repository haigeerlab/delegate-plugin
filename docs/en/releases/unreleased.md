# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Unreleased changes after v0.9.0 follow.

## Review findings gain a severity (interface 1.5)

- Each finding in the review report gains the required field `severity`: `blocking` or `suggestion`. The review model labels it against the fixed criteria `severity-v1`, which are in the [review-severity spec](../SPEC-review-severity.md); `--task` cannot change the criteria.
- If the model omits it or gives a wrong value, the whole review is `failed` (diagnostic `finding_invalid`); delegate does not fill it in.
- A reader treats a missing field (reports from 0.9.0 and earlier) or an unknown value as `blocking`; no blocking findings does not mean the change may be merged.
- `interface.json` moves to 1.5 with a `severity` description under `review.report`; the report `schema_version` stays `1`, fields are only added.

Historical acceptance records retain their original version/status without retroactive approval.
