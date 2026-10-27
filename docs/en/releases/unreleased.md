# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md). Unreleased changes after v0.7.0 follow. Historical acceptance records retain their original version/status without retroactive approval.

## Reclaiming commands started by Codex on abort (S41, planned as the 0.7.1 patch)

- **Problem:** Each shell command Codex runs starts in a new session and process group. When `/delegate:run` hit its deadline or received TERM/INT/HUP, only the Codex process group was cleaned up; the commands were adopted by init/launchd and kept running, and in write mode could still change the workspace after delegate reported completion.
- **Fix:** On abort, Codex is frozen first, all descendants are snapshotted, TERM goes to every descendant process group and to Codex as it is unfrozen, and what remains after one shared grace period of at most 2 seconds is killed. The final reap of the execution process waits at most 5 seconds; an interrupted wrapper waits at most 15+2 seconds for it.
- **New output (additive only):** On abort, stderr gains `delegate: 清理：…` lines with the descendant list and `无残留` (none left) or `仍有残留，PID=…` (survivors). If the execution process cannot be reaped, `delegate: 执行进程未能回收，PID=…` is printed and the exit status is **125** (new; treat as failure). If an interrupted wrapper's execution process does not exit, it prints `执行进程超时未退出，已强制结束（PID=…），其后代可能残留。` (forced to stop; descendants may survive). The process directory gains a `<runId>.cleanup` file, cleaned up together with its log.
- **Unchanged:** Interface 1.2; the result line `delegate: run_id=… status=…`, stdout, the state file and the 540-second deadline. Background processes Codex leaves after exiting normally remain outside the guarantee.
- **Verification scope:** Free regressions ran on macOS with a fake codex and with real Codex 0.162.1 against a local fake endpoint (no credentials). Linux hosts, reclaiming in write mode, and the real cause of the S38 T5b "no exit within 60 seconds" are not verified.
