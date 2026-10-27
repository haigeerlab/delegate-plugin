# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md). Historical acceptance records retain their original version/status without retroactive approval.

After v0.7.1 (interface 1.3; not released until all five modules are done):

- **Result file (run-result)**: every run that started Codex writes a JSON result file; the result line is preceded by `delegate: result=<path>`. New `--strict`: a missing first-line end marker gives `unmarked`, exit 1. The interface adds `run.result` and `run.usage`.
- **Continue (run-continue)**: new `--continue <runId>` carries on with the next task in the same Codex session after a `done` round of a `--resumable` chain. State, claim and result files are now kept for 14 days instead of being pruned with the latest 50 logs. The interface adds `run.continue`.
- **Long tasks (run-longrun)**: new `--timeout <seconds>` widens the deadline to 541–7200 seconds; the default is still 540 seconds, and above the host's foreground limit the caller must use background mode, as delegate does not manage background processes. Abort cleanup is the one from v0.7.1. The result file records `timeoutSeconds`. The interface adds `run.longRun`.

Upgrade notes:
- Process logs are now two files: `<runId>.events.jsonl` (the event stream of Codex run with `--json`) and `<runId>.log` (stderr); the log tail printed to stderr on failure changes accordingly and is followed by the most recent events. Scripts that read log text need adjusting; logs are not part of the interface.
- The result line is still the last line of stdout, but it is now preceded by a `delegate: result=` line.
- The result file `status` adds `unmarked` (only with `--strict`) and, where there is no result line, `failed`, `interrupted`, `unreaped` and `empty`. Decide success by exit code 0 first, then `status=done`.
