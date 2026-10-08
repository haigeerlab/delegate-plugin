# Specification: detection (local readiness and diagnostics)

[简体中文](../../SPEC-detection.md) | English

Current contract: 2026-10-08. Early `tasks/detection/` records remain historical.

## Goals and implementation

Provide recent local readiness for routing proposals. Failures degrade silently. Hooks do not call models, write to the target project, or delegate automatically. “Available” means only that the CLI runs and reports ChatGPT authentication; it **does not establish** remote connectivity, quota, model access, or continued token validity.

- `backend.py`: PATH, version command, and CLI authentication status; shared with channel.
- `detect.py`: wrapper executability, cache validity, atomic writes, and output contract.
- `detect.sh`: silent shell entry point, including degradation when Python is missing.
- `doctor.sh`: forced refresh and on-demand checks of Chinese global AGENTS.md rules.

## Authentication probes

Do not read `auth.json` directly or infer login from a credential file's existence or size. Follow CLI handling of CODEX_HOME and system credential storage. Version and login probes each have a 5-second limit. Raw status output is neither cached nor echoed with credential fragments. Accept only explicit CLI-reported ChatGPT authentication; API-key, unknown, or failed status is unavailable. Check again before real execution.

The old `CODEX_AUTH_FILE` is no longer a product authentication override. Only legacy test stubs use it to simulate CLI status.

## Cache contract

Path: `${TMPDIR:-/tmp}/delegate/detection.json`. Fields: boolean `available`, safe string `reason`, timestamp `checkedAt`, and object `identity`.

Identity includes the actual CLI path, effective Codex home, plugin root, and manifest version. Different identity, invalid field types, old formats, invalid JSON, future timestamps, or age greater than 8 hours invalidate the cache.

Write a temporary file in the same directory with mode 0600, then use `os.replace` to prevent partial JSON reads. The cache directory has mode 0700; a symlink directory is rejected. On write failure, hooks inject no readiness fact and still exit 0. Account switches or credential expiration are not guaranteed to invalidate immediately if CLI path and home remain unchanged. doctor forces refresh; execution always probes again.

## Entry points and output

- `--session-start`: force probing and write cache, silently.
- `--warm`: reuse valid cache or probe, silently.
- `--print`: force probing and print readiness or a safe reason; used by doctor. Direct probe results may still be reported if the cache is unwritable.
- Default: if cache is available, emit valid UserPromptSubmit JSON identifying only local readiness. Unavailability or internal failure produces no output and exits 0.
- Actual UserPromptSubmit uses `prompt.sh` to warm then route sequentially, avoiding races between parallel handlers.

## doctor

Refresh directly on every call and inspect `${CODEX_AGENTS_FILE:-${CODEX_HOME:-$HOME/.codex}/AGENTS.md}`. `CODEX_AGENTS_FILE` overrides only the diagnostic file, not the rules actually loaded by Codex.

Chinese heuristics look for rules requiring confirmation or an initial plan, and for non-interactive exemptions. Results do not cover English or every global/project rule; finding an exemption does not prove it covers every relevant section. Print diagnostic scope and issue count, always exiting 0. Only temporary cache is written; project files and rules are not modified.

## Validation

Run these commands from the repository root:

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-detection.sh
python3 -B plugins/delegate/tests/test-backend.py
```

The original 19 assertions cover wrapper/CLI/login failures, cache hits and invalidation, silent degradation, valid JSON, and doctor. Additional regressions cover CLI authentication without auth.json, rejecting API-key/unknown status without leakage, login failure, doctor refresh of stale cache, home identity changes, future timestamps, and sequential cold-start output.

Success criteria: failures do not inject misleading context; cache hits make no CLI status requests; doctor refresh is reproducibly verifiable; cache writes are atomic and identity-bound. No unmeasured <5ms promise is made. Python startup, file I/O, and CLI probes incur local overhead; real performance requires separate measurement.
