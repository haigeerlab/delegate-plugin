# ADR-003: Review process boundary revision

English | [简体中文](../../decisions/ADR-003-review-process-boundary.md)

2026-10-10: After the user narrowed scope to the current native Mac, [ADR-004](ADR-004-native-mac-review.md) defines the current execution environment. The old design/approvals/model-free evidence below remain historical, not deployment prerequisites.

Status: Accepted for design and free implementation/tests; not runtime-accepted. Date: 2026-10-09.
The user first approved read-only evaluation, then replied “继续” to the dedicated-VM recommendation. This supersedes ADR-002's native macOS-first portion and approves installation-free R1–R4 work. New runtime installation, guest login, model calls and delivery still require separate authorization. Design approval does not close the isolation gate.

## Evidence and interface findings

The macOS candidate passed 13 policy/permission cases. Its lifecycle suite passed 5 of 8; detached helpers survived timeout, cancellation, and parent-first exit. Fixture teardown killed its own helpers. The assertions remain red. See the [actual record](../../verification/2026-10-09-claude-review.md). The preceding read-only evaluation did not rerun tests or change candidate code.
Read-only PATH inventory on macOS 15.7.3 arm64 found `/usr/bin/ssh`, but no limactl/docker/podman/bwrap/socat/qemu-system-aarch64. This is not an exhaustive disk inventory; no usable Linux environment was verified.

| Mechanism | Documented behavior | Remaining condition |
| --- | --- | --- |
| Linux PID namespace | The kernel SIGKILLs namespace processes when its PID 1 dies | Actually create the namespace and terminate its init; killing a client alone is insufficient |
| bubblewrap | `--unshare-pid`, `--die-with-parent`, and `--new-session` provide distinct boundaries | Its default init can wait for descendants; main-process exit does not prove an empty namespace |
| Installed srt 0.0.79 | Uses those flags, user namespaces, and fresh `/proc` in strict mode; host Node proxies/socat sit outside bwrap | Enclose outer helpers too; a missing seccomp helper warning must fail strict preflight |
| cgroup v2 | Fork inherits membership; `cgroup.kill` kills the subtree including concurrent forks; events expose populated state | Reviewer must not access migration/control interfaces; unavailable management fails closed |
| systemd transient service | `KillMode=control-group` stops the unit; stop grace escalates to SIGKILL; `RuntimeMaxSec` bounds runtime | Use a service rather than a client-lifetime scope; validate the user manager and metadata/cleanup |
| Lima plain mode | Disables host mounts, dynamic forwarding, SSH agent forwarding, containerd, and guest agent | Static forwarding, provisioning, and base SSH setup remain; VM networking is not an egress policy |

Sources: [PID namespaces](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html), [bwrap options](https://github.com/containers/bubblewrap/blob/main/bwrap.xml), [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), [systemd kill](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.kill.xml), [service](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.service.xml), [systemd-run](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd-run.xml), [Lima plain mode](https://lima-vm.io/docs/config/plain/).
Installed **0.0.79** `dist/sandbox/linux-sandbox-utils.js` is the version-specific evidence: boundary flags at 2625/2766–2784, host bridges at 1072–1125, and missing-seccomp handling at 2633–2640. Its hash is in the actual record. Official [main source](https://github.com/anthropics/sandbox-runtime/blob/main/src/sandbox/linux-sandbox-utils.ts) and [README](https://github.com/anthropics/sandbox-runtime) cross-check the design, not release/runtime acceptance. Never enable weaker nested mode or automatically change system user-namespace policy.

## Options and recommendation

| Option | Benefit | Cost and scope |
| --- | --- | --- |
| Native macOS candidate | Existing CLI/authentication; fewest dependencies | Demonstrated detached-helper cleanup failure; do not enable it. This does not prove every native alternative impossible |
| Native Linux CLI + srt + transient service | No VM transport; cgroup encloses outer helpers | Requires Linux/systemd/cgroup v2; alone it cannot meet current Mac bidirectional acceptance |
| Dedicated Linux VM on macOS + that same unit | Keeps Mac main sessions and gains guest kernel boundaries | Adds VM, SSH transfer, guest authentication, and resources; usability remains unverified |

Recommend option three as the **next candidate for Mac validation and optional deployment**, first validating option two inside the guest. There remain exactly two backends, codex and claude-code; a VM is an execution environment. Preserve the existing native Codex path; no automatic backend/environment substitution.
Linux-only delivery requires explicitly accepting unsupported Mac Claude execution and incomplete local CR-10. A native Mac route still needs a proven CR-06 mechanism.

## Runtime contract

1. Host wrapper reads only declared source/Git scope. Transfer verified ordinary-file snapshots/fixed diffs into a dedicated guest directory and verify hashes again. Share no source repository, host home, Git, Keychain, SSH agent, or Docker socket. Reject symlinks, hardlinks, absolute paths, and `..`; never execute task data. Accept only bounded answer/report/filtered events back.
2. Each review owns one transient **service**, started by an available user manager. Trusted runner, srt/Node/proxies/socat/Claude all belong to its cgroup. Use `Type=exec`, `KillMode=control-group`, `SendSIGKILL=yes`, `TimeoutStopSec=2s`, and finite `RuntimeMaxSec`; no restart, delegation, or remain-after-exit. Hide cgroup control paths, user D-Bus and SSH sockets from the reviewer. Missing manager/namespace/seccomp capabilities produce conditions_missing, without global sysctl/AppArmor/linger changes.
3. After model-free preflight, run original `claude -p` with ADR-002's tool/context/filesystem/network restrictions. Permit only explicit endpoints required by the chosen authentication. Guest network access is not reviewer tool access. Source, configuration, and snapshot remain read-only; only invocation run/log/temp are writable. Tools remain Read/Glob/Grep.
4. Conclude every success/failure/timeout/cancellation by stopping the unit and confirming its cgroup has `populated=0`. Save unit Result/ExecMainStatus and runner cause first; do not interpret systemd-run exit alone or prematurely collect the unit. Do not read raw journal content or log credential-bearing argv/env.
5. Host cancellation sends a separate control request for this invocation's unit. Guest deadline remains effective after SSH loss; client exit does not establish guest completion. Failed control means unknown/failed and inconclusive; never rerun. The VM must be dedicated with ownership evidence and exclusive use. Stop it as containment only after confirming no unrelated work; never stop a shared user VM.
6. Host SSH helpers also receive invocation process-group cleanup. Verify both layers. Record the bounded guest lifetime after host disappearance; uncatchable host termination does not promise immediate cleanup. Unconfirmed cleanup must not report review success.
7. Add no general remote protocol, queue, or scheduler. VM mode accepts one explicitly supplied controlled local Lima guest with fixed start/status/cancel operations, not arbitrary remote hosts or shell strings. Missing VMs are not automatically created, started, or replaced.

Candidate baseline: original Claude **2.1.295**, srt **0.0.79**, Node **>=22.12.0**. Pin Linux/kernel/systemd/bwrap/socat/Lima versions and image digests during dependency preflight; there is no accepted version matrix yet. Test actual cgroup v2/cgroup.kill and manager attributes rather than inferring support from version strings. [Claude platform requirements](https://code.claude.com/docs/en/setup) do not validate this combination.

## Authentication and context

Original guest CLI uses authentication that the user previously configured in the guest: login or explicitly chosen API/provider credentials. Delegate does not read, copy, broker, or transmit host credentials over SSH, infer guest login from host login, or run login/setup-token. Model verification requires separate authorization.
Linux login uses `.credentials.json`; `CLAUDE_CONFIG_DIR` changes its location. Preflight and execution must use the same explicit guest authentication profile, with only necessary CLI credential paths readable and normal customization disabled. Do not switch to an empty directory and claim preserved login. If refresh needs to write original configuration, refuse/report incomplete; do not copy credentials into temp to evade restrictions. Users supply guest environment credentials; logs omit values. Do not silently substitute API/subscription/provider authentication or billing. [Official authentication](https://code.claude.com/docs/en/authentication).
Strict read-only authentication compatibility remains unknown. Managed Hooks/helpers that require denied capabilities fail closed; do not enable bare/bypass. Tool permissions bound actions; srt bounds filesystem/egress; safe/restricted and snapshots bound loaded context; service/cgroup bounds ownership/lifetime.

## Result increment and implementation sequence

Preserve the eight execution/review states and evidence fields. Add only `execution_environment` (native/specified VM, OS, verified versions) and `cleanup` (confirmed/unverified with necessary cause). Keep host/backend/requested/observed model separate and unknown without evidence. Restrict VM/PID/cgroup identifiers to diagnostic metadata; do not routinely expose personal paths. Pre-start failure states Claude never started. Valid structured output, successful units, and exit 0 do not establish a clean review.

| Slice | Files/size | Acceptance and stop |
| --- | --- | --- |
| R1 Platform contract | Both specs, both ADR-002 pages, plan (5 files, S) | Only after approval; preserve historical approval and red evidence |
| R2 Model-free Linux unit | New `review_service.py`, Linux lifecycle tests, existing policy/permission tests (up to 4 files, M) | Fake-manager failures and actual guest suites separately; code changes need revision approval |
| R3 Dedicated VM preflight/transfer | New `review_guest.py`, transfer fixtures, permission tests (up to 3 files, M) | No shared host dirs; ownership/lock/hashes/size/path/connection/cancellation classification pass; no real credentials |
| R4 Actual isolation gate | Actual record and todo (2 files, S) | Pin versions, run fake CLI through real permissions/lifecycle suites; pass/report limitations before Task 3 |

R2 covers setsid/double-fork/TERM refusal/parent-first exit/pipe retention/proxy children/rapid fork-exit/runner disappearance/INT-TERM-HUP/deadlines/unrelated sentinel, checking empty cgroups and cleaned proxies/sockets. R3 covers disconnect with guest deadline intact, lost cancellation replies without rerun, unrelated-task protection, read-only fake-auth refusal, and unavailable delegate/MCP/arbitrary Bash. Do not weaken, skip, or turn the native Mac red tests green to imply a native fix.
Before any installation request, identify runtime/image versions and digests, download sources, dedicated temp paths, disk/RAM/CPU bounds, provisioning contents, and removal. Revision approval excludes installation. Real authentication/model requests, both host acceptance runs, and Git/external delivery retain separate authorization. Checkpoint 1 remains open; Task 3 has not started.

R1 is synchronized. Candidate R2/R3 foundations passed 14/11 free tests; VM/SSH invocation and actual unit launch are not implemented or kernel/guest-accepted. Early unit collection fails closed, never inventing success; authoritative end-state retention must be validated in the real-manager slice. `--expand-environment=no` requires systemd >=254 plus actual flag/property checks. See the [dependency preview](../../verification/2026-10-09-claude-review-vm-preflight.md) (Chinese administrative record).

Subsequent implementation: the user authorized the fixed temporary VM and model-free probes with “继续 快速推进啊”. Actual Lima/Debian/Node/srt versions and digests were verified; 15 Linux and 2 real SSH tests passed, preserving native Mac failures. Added real service startup, trusted ExecStopPost end facts, Linux `/sys`/`/run` masking and arm64 bind/listen seccomp prohibition. Earlier absence-of-unit/VM statements describe their preceding stage. Public entries and product VM/SSH control remain unconnected, original CLI/auth/live remain unknown, and the gate awaits review. See the [current actual record](../../verification/2026-10-09-claude-review-linux.md).
