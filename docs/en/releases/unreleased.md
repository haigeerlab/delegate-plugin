# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). Unreleased changes after v0.8.6 follow.

## Review reports add a recomputable patch fingerprint (interface 1.4)

- The review report `scope` gains `fingerprint`: `{"algorithm": "blob-pairs-v1", "sha256": …, "paths": […]}`. It is set only for a baseline between two commits (`commits`) and is `null` for other baselines.
- The fingerprint uses only the mode and object id of each reviewed file in the two commit trees, independent of repository configuration, `.gitattributes` and the git version, so it can be recomputed on another machine such as GitHub Actions to bind a review conclusion to a specific patch. The algorithm is in the [review-fingerprint spec](../SPEC-review-fingerprint.md).
- `scope.diff_sha256` is unchanged: still the sha256 of the diff text, valid only on the local machine.
- `interface.json` moves to 1.4 with a `fingerprint` description under `review.report`; the report `schema_version` stays `1`, fields are only added.
- New fixed diagnostic `fingerprint_inputs_inconsistent`: reported when the file entries obtained do not match the reviewed files; no partial fingerprint is emitted.

 Historical acceptance records retain their original version/status without retroactive approval.
