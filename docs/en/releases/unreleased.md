# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

The external interface description after v0.5.2 is recorded in [v0.5.3 release notes](v0.5.3.md). After v0.5.3:

- Resumable delegation ([run-resume](../SPEC-run-resume.md)): `/delegate:run --resumable` can stop to ask the user and return `needs-input`, and `--resume <runId>` continues the original Codex session with the user's answer; every successful return ends with the run_id and end status. The interface description moves to 1.1 and only adds `run.resume`. Every run and Codex review now passes `approval_policy="never"` instead of the local approval configuration; out-of-sandbox commands in write mode are refused. The real Codex resume check is recorded in this module's acceptance notes.

 Historical acceptance records retain their original version/status without retroactive approval.
