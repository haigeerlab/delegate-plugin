# Specification: detection (local readiness and diagnostics)

[简体中文](../../spec/detection.md) | English

Current contract: 2026-10-08. Earlier records are preserved in the [historical archive](../archive/pre-spec-guard/README.md). Current `tasks/detection/` tracks maintenance reconciliation only; it neither retroactively accepts historical work nor overrides this specification.


## Tech stack and commands

Bash 3.2, Python 3 standard library, Git, and Codex CLI; Claude Code hosts hooks/doctor. Cache identity includes the plugin-manifest version; readiness follows direct probes or a bounded TTL.
This is a script plugin with no separate compilation build or development server. The existing contract below lists module tests. Aggregate checks and source loading are shown here; loading starts the host and does not delegate by itself.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
claude --plugin-dir "$PWD/plugins/delegate"
```

## Project structure

Paths are relative to the repository root; plugin-relative paths are explained in the original contract.

```text
plugins/delegate/hooks/detect.py            → identity cache, probes, atomic writes
plugins/delegate/hooks/detect.sh            → silent Shell entry point
plugins/delegate/hooks/doctor.sh            → refresh and instruction diagnostics
plugins/delegate/scripts/backend.py        → shared CLI authentication probes
plugins/delegate/tests/test-detection.sh    → Shell stub assertions
plugins/delegate/tests/test-backend.py      → Python unittest auth/identity/ordering regressions
spec/detection.md                            → current Chinese contract
docs/en/SPEC-detection.md                    → current English contract
tasks/detection/plan.md / todo.md            → current maintenance steps and records
```

## Code style

Keep existing style without formatting refactors. Preserve Bash 3.2, braced `${VAR}` variables and existing empty-array guards; do not use `cmd | grep -q`. Python uses the standard library, four-space indentation and snake_case functions. Serialize JSON instead of manually escaping it.
This existing excerpt from `plugins/delegate/hooks/detect.py` illustrates actual style (context, not a new command):

```python
        with tempfile.NamedTemporaryFile(mode='w', dir=str(CACHE_FILE.parent), delete=False) as output:
            temporary = output.name
            json.dump(data, output, ensure_ascii=False)
            output.write('\n')
        os.replace(temporary, str(CACHE_FILE))
```

## Development boundaries

- **Always:** Read the contract before editing; reproduce behavior defects before fixing; preserve Bash 3.2 and bilingual contracts; review actual diffs and relevant tests.
- **Ask first:** New backends/dependencies/flags, sandbox defaults or authentication changes, or capabilities outside the module; obtain separate authorization for paid live checks, delegation, commits and remote writes.
- **Never:** Expose credentials or full private logs; weaken failing assertions; automatically roll back user changes; retroactively approve history or edit archives; treat stubs as complete host-behavior guarantees.

## Testing strategy

Shell suites use `stub-codex` and temporary fixtures; Python regressions use standard-library `unittest`. Locations are listed above; exact commands and assertion scope remain in the original contract. No line-coverage percentage is set or invented.
Assess coverage per clause and risk, including positive and negative cases. Source guarantees without independent assertions are marked partially covered in the matrix. Real-model, permission and interaction checks remain separate; paid samples require authorization.

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

## Success criteria and verification mapping

The IDs below label existing contract clauses for the 2026-10-08 documentation reconciliation; they are not historical IDs or approvals.

- **DET-01：** Readiness follows CLI-reported ChatGPT authentication and bounded probes; it does not establish remote connectivity or quota.
- **DET-02：** Cache types, eight-hour TTL, future timestamps, and identity matching follow the existing contract; writes are atomic and failures degrade safely.
- **DET-03：** Forced refresh, cache reuse, silent output, and serial prompt ordering follow the existing entry-point contract.
- **DET-04：** Doctor refreshes and reports limited Chinese-rule diagnostics without editing business rules or treating heuristics as full instruction validation.

See the [clause-to-evidence matrix](../verification/2026-10-08-contract-matrix.md) (administrative record in Chinese) for exact tests, implementation references and coverage gaps. The current maintenance plan Task 5 checks this mapping; it does not declare every product clause fully accepted.

## Open questions

Historical task-by-task acceptance, earlier approvals/plugin versions and complete interactive host behavior remain unverified. Current known coverage gaps are listed in the matrix; no new capability or stronger guarantee is introduced here.
