# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Resumable delegation and the approval mode change after v0.5.3 are recorded in [v0.6.0 release notes](v0.6.0.md). Historical acceptance records retain their original version/status without retroactive approval.

## Keep progress on run timeout (run-timeout, interface 1.2)

Contract: [docs/en/SPEC-run-timeout.md](../SPEC-run-timeout.md).

- **Every run prompt ends with a time budget**: the Codex main run gets the total deadline minus the wrap-up reserve (495 s at 540), and after the threshold (405 s at 540) the model should stop and start its answer with `TIME_UP:` followed by progress. Plain-run arguments (including `--ephemeral`) are unchanged.
- **Timeouts have a result line**: a timeout now prints the answer, metadata and `delegate: run_id=<id> status=timeout resumable=<true|false>`; the exit code is still 124.
- **Two wrap-up layers and a fallback**: after a resumable run is forcibly stopped, one more read-only round is resumed that only writes progress (at most 45 s). Plain runs, and wrap-up rounds that time out, fail, return nothing or have no session id, get a model-free fallback text; in write mode it lists the files changed during the run.
- **Resume after timeout**: `--resume` accepts resumable runIds with `status=timeout`; plain-run timeouts cannot be resumed.
- **Interface 1.2, additions only**: `"timeout"` is appended to `run.resume.statuses`, and `run.timeout: {"status": "timeout", "exitCode": 124}` is added.
- **Fix**: an occasional `PermissionError` (EPERM) from process-group cleanup in `run_codex.py` on macOS no longer interrupts cleanup.

### Upgrade notes

- **Decide success by exit code 0 first, then `status=done`.** Timeouts now have a result line too; a result line does not mean success.
- **`statuses` is an open set**: an unknown value must make the consumer stop or treat it as failure, never as completion.
- Consumers reading 1.1 are unaffected: a timeout still exits 124 and can still be treated as failure.

Not yet verified: timing margins under the real 540-second deadline, how often the wrap-up round has long tails, wrap-up on large contexts, other models, and whether write-mode resumes repeat writes; these await the paid verification.
