# ADR-004: Claude review on the current native Mac

[简体中文](../../decisions/ADR-004-native-mac-review.md)

Date: 2026-10-10. Current source uses this decision; real model acceptance is incomplete. The user explicitly narrowed support to the current native Mac and requested continued implementation. This replaces ADR-003 guest deployment requirements, not historical failures, and does not authorize installation, model calls or Git delivery.

## Problem and decision

The old group runner failed detached-helper normal-exit, timeout and cancellation checks. Linux guest/cgroup model-free evidence added environment and independent-authentication preparation, while the user now wants native Mac. Denying all forks was also proved incompatible with original local authentication.

Use a temporary launchd job with a unique resource coalition, rather than relying on launchd group cleanup. A trusted anchor proves independent ownership and sole membership before startup; the kernel retains srt/CLI/proxy and fork/setsid/double-fork descendants. STOP reviewer members, prove enumeration equals kernel task count and all are stopped, then KILL using PID-generation-bound signals. Remove only this job and prove zero tasks. Fail closed, without inferring ownership from names, environment tags or PPID polling.

Sources: Apple [libproc wrappers](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/libsyscall/wrappers/libproc/libproc.c), [process identity/coalition ABI](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/sys/proc_info_private.h), [coalition counts](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/osfmk/mach/coalition.h), and [actual native evidence](../../verification/2026-10-10-claude-review-mac-native.md). Private ABI is not stable public API; layout, capabilities, counts and generation-bound signals were checked only on macOS 15.7.3 arm64. Mismatches on other versions fail instead of killing by name.

## Permissions and authentication

- Tools: requested Read/Glob/Grep subset, dontAsk, no Bash/writes/MCP/Web/delegation. Stop immediately on an unsafe init tool list. Also permit only StructuredOutput/schema and the officially retained EndConversation/session-end controls without expanding IO; a missing complete result remains incomplete. Retain fixed initialization reason codes only. Permit the passive ui_invalidate/ui.render prefix reproduced by original-CLI probes with fixed fields, at most 8 events/64 KiB; a valid init remains mandatory. Do not skip hooks, plugin installs or unknown events. Tool capability controls do not replace filesystem isolation.
- OS: srt 0.0.79 with explicit reads and only per-run writable access. Source/Git/configuration/snapshot/Keychains are unwritable and reviewer cannot access control. Only three first-party 443 endpoints; no LaunchAgents installation or global configuration writes.
- Context: fixed scope/snapshot, safe/restricted close ordinary project/plugin/Hook customization. Treat content as data and never widen scope.
- Authentication: original CLI uses existing local authentication without delegate reading/copying credentials. Read-only Keychains runtime access was proved necessary. Tool-level Read denies cover runtime grants with blockReadsOutsideWorkingDirectories. Official Read coverage for Grep/Glob is best effort; actual model-tool behavior remains unverified. Reject custom auth/provider environments, local managed configuration and old guest configuration without silently changing authentication.

## Implementation and acceptance

review_macos.py owns process membership/deadlines/control facts; review_native.py connects existing dependencies/policy/snapshot and the Claude adapter. Public routing, doctor, both source host command/skill entries and bilingual contracts share the native path. Preserve Codex defaults/old writes. Resolve existing PATH or explicit absolute executables only, without installation/upgrades/login. The anchor has its own finite deadline; uncatchable termination does not promise immediate cleanup. Shared system XPC services are not killed as owned descendants.

Free checks separately establish parameter/state contracts, actual OS write denial/lifecycle, the fixed fake-CLI public path. Original 2.1.295 returned authentication_missing, while the latest original 2.1.296 authentication passed under the strict boundary. The earlier cause remains unknown; neither user logout, the version change as a root-cause fix, nor real review readiness is established. Check normal/empty/malformed/denied/unsafe-tool/timeout outcomes, INT/TERM/HUP, fast forks, parent-first exit, unrelated sessions, PID reuse and atomic control publication. Preserve the old runner's red cases; verify equivalent actual assertions with the new runner instead of deleting/skipping failures.

Real -p, refresh, dynamic policy, network/TLS, tool read boundaries, write/recursion inducements and both real hosts need a finite live batch. CLI status/fake outputs do not establish approval, greater accuracy or delivery authorization. Installed caches, commits, pushes and releases remain unchanged.

Fix: srt proxy startup fails under the long default Mac TMPDIR. An actual long-path regression failed before the fix and passed afterwards. Native execution/doctor now use dedicated short directories under `/private/tmp`, retaining the same restrictions. Authentication failure is a separate unresolved condition.

### 2026-10-13: local installation paths and supervisor startup

The launchd interpreter may be unable to reopen plugin installation files under Documents. The main session stages only the three trusted supervisor/parser modules review_macos.py, review_result.py and claude_review.py inside the existing private control tree (0700 directory,0600 files), then starts the temporary job there. This step copies no source snapshots, credentials or other user data. The reviewer remains denied read/write access to the entire control tree; tools, network, identity proof, deadlines and cleanup are unchanged. It changes no system permissions, global configuration or authentication and switches no backend. Path-denial and model-free fix evidence is recorded separately; a startup probe does not establish a successful real-model review.
