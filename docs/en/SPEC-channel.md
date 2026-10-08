# Specification: channel (delegation channel)

[简体中文](../../spec/channel.md) | English

Current contract: 2026-10-08. Earlier records are preserved in the [historical archive](../archive/pre-spec-guard/README.md). Current `tasks/channel/` tracks maintenance reconciliation only; it neither retroactively accepts historical work nor overrides this specification.


## Tech stack and commands

Bash 3.2 wrapper, Python 3 standard library, Git, and Codex CLI; Claude Code hosts product commands. CLI versions vary by installation and are probed rather than assigned an unverified fixed minimum.
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
plugins/delegate/scripts/codex-exec.sh      → arguments, preflight, logs, Git output
plugins/delegate/scripts/backend.py         → shared channel/detection authentication
plugins/delegate/scripts/run_codex.py       → process groups, deadlines, cleanup
plugins/delegate/tests/test-channel.sh      → Shell stub assertions
plugins/delegate/tests/test-channel-regressions.py → Python unittest lifecycle/Git regressions
plugins/delegate/tests/test-backend.py      → shared authentication/configuration regressions
spec/channel.md                            → current Chinese contract
docs/en/SPEC-channel.md                    → current English contract
tasks/channel/plan.md / todo.md            → current maintenance steps and records
```

## Code style

Keep existing style without formatting refactors. Preserve Bash 3.2, braced `${VAR}` variables and existing empty-array guards; do not use `cmd | grep -q`. Python uses the standard library, four-space indentation and snake_case functions. Serialize JSON instead of manually escaping it.
This existing excerpt from `plugins/delegate/scripts/backend.py` illustrates actual style (context, not a new command):

```python
    env = os.environ.copy()
    for key in ('OPENAI_API_KEY', 'CODEX_API_KEY'):
        env.pop(key, None)
```

## Development boundaries

- **Always:** Read the contract before editing; reproduce behavior defects before fixing; preserve Bash 3.2 and bilingual contracts; review actual diffs and relevant tests.
- **Ask first:** New backends/dependencies/flags, sandbox defaults or authentication changes, or capabilities outside the module; obtain separate authorization for paid live checks, delegation, commits and remote writes.
- **Never:** Expose credentials or full private logs; weaken failing assertions; automatically roll back user changes; retroactively approve history or edit archives; treat stubs as complete host-behavior guarantees.

## Testing strategy

Shell suites use `stub-codex` and temporary fixtures; Python regressions use standard-library `unittest`. Locations are listed above; exact commands and assertion scope remain in the original contract. No line-coverage percentage is set or invented.
Assess coverage per clause and risk, including positive and negative cases. Source guarantees without independent assertions are marked partially covered in the matrix. Real-model, permission and interaction checks remain separate; paid samples require authorization.

## Goals and boundaries

Send one task with settled decisions to Codex, separate process logs, and return the final answer and a verifiable Git summary in write mode. This module does not handle classification, authorization that cannot be bypassed, result correctness, remote authentication validity, or publishing. Both modes require a Git working tree.

Implementation files are under `plugins/delegate/`: `scripts/codex-exec.sh` manages options, logs, and Git; shared `backend.py` checks basic authentication; `run_codex.py` manages the execution process group. Dependencies: Bash 3.2, Python 3, Git, and Codex CLI.

## Options and preflight

Run from the target Git working tree, replacing the script path with the actual source or installation location:

```bash
bash /path/to/delegate-plugin/plugins/delegate/scripts/codex-exec.sh [--write] [--model <slug>] [--effort <level>] [--] "task"
```

`--help/-h` does not invoke Codex. Unknown options, missing arguments, zero or multiple tasks, and non-Git directories exit 64. Model and reasoning effort are passed through without a potentially stale local allowlist.

Basic checks locate the CLI through PATH and run `codex --version` and `codex login status`, with a maximum of 5 seconds per probe. ChatGPT authentication must be recognized; API-key and unknown states are rejected. Execution does not trust hook cache. CLI/dependency failures exit 127; authentication failures are nonzero. Raw authentication output that may contain credential fragments is not echoed.

## Invocation and lifecycle

- Default sandbox is read-only; `--write` selects workspace-write only with explicit user authorization in the current turn.
- Remove `OPENAI_API_KEY` and `CODEX_API_KEY`; select CLI configuration `forced_login_method="chatgpt"` and `model_provider="openai"`.
- Use `--ephemeral`, no color, stdin=/dev/null, and a preamble defining non-interactive work and behavioral scope.
- `-o` writes the final answer; combined stdout/stderr goes to the process log.
- Codex starts in a new process group. The execution deadline defaults to and is capped at 540 seconds. `DELEGATE_TIMEOUT_SECONDS` can shorten it; invalid or non-positive values fall back to the default. The deadline excludes preflight probes and subsequent verification.
- On deadline or TERM/INT/HUP, send TERM to the process group, wait at most 2 seconds, then KILL remaining processes and reap the direct child. Normal exit also cleans up remaining processes in the group.
- External Bash timeout=600000 milliseconds. Timeout exits 124; signals correspond to 143/130/129. Other execution failures retain their status; an empty answer exits 1.
- Descendants that leave the process group are outside the cleanup guarantee. Behavioral instructions are not OS permission isolation; temporary directories and additional roots allowed by the real sandbox depend on host configuration.

## Writes and output

Existing uncommitted changes and Git repositories without HEAD are allowed. Before execution, record HEAD and the number of existing changes. Once execution has started, every exit path—success, failure, timeout, empty answer, or interruption—outputs the baseline, status --short, diff --stat, and diff --cached --stat. Successful output goes to stdout; failure output goes to stderr. Failure does not roll back changes. Statistics include existing edits, so actual diffs must be reviewed.

Success returns only the answer and metadata. The answer has no size limit and no fixed compression-ratio guarantee. Process files are stored in `${TMPDIR:-/tmp}/delegate/`, with directory mode 0700 and new-file mode 0600; a symlink directory is rejected. Failure output shows at most the final 40 lines/16KiB plus the full log path. After completion, cleanup attempts to retain the latest 50 pairs of logs and answers; cleanup failure does not change execution status. Individual logs have no size limit.

## Validation and success criteria

Run these validation commands from the repository root:

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-channel.sh
python3 -B plugins/delegate/tests/test-channel-regressions.py
python3 -B plugins/delegate/tests/test-backend.py
```

The original 24 assertions cover options, stdin, stdout separation, sandbox arguments, log cleanup, ordinary timeout, and Git baseline. Regressions cover bounded exit when TERM is ignored, descendants stopping file writes, wrapper interruption, Git evidence after failure/empty answer/timeout, output limits for a 100KB single-line error, rejection of non-Git execution, and help without the CLI. Backend regressions cover authentication rejection, execution configuration, and cache.

Free tests use stubs and verify invocation arguments and process management, not real CLI sandbox or paid-model behavior. `test-channel.sh --live` consumes quota and is excluded from aggregate validation; see the [v0.4.0 verification record](releases/v0.4.0.md) for real runs. Changes to invocation shape must pass aggregate validation; behavior changes first need a regression reproducing the failure. Additional backends, flags, sandbox defaults, or non-Git support require separately defined scope.

## Success criteria and verification mapping

The IDs below label existing contract clauses for the 2026-10-08 documentation reconciliation; they are not historical IDs or approvals.

- **CH-01：** Option and readiness exits match the existing contract; help does not invoke the CLI, and unknown/API-key authentication is rejected without echoing credentials.
- **CH-02：** Default read-only, authorized write arguments, ChatGPT/OpenAI configuration, and closed stdin are correct; stubs do not establish real sandbox permissions.
- **CH-03：** Deadlines and signals follow the existing lifecycle contract, with same-group cleanup; descendants leaving the group are outside the guarantee.
- **CH-04：** After execution starts, success/failure/empty-answer/timeout paths provide Git baseline and change summaries, retain existing changes, and do not roll back.
- **CH-05：** Answers and process logs remain separate, failure tails are bounded, and retention does not change execution status; permissions and symlinks follow the existing log contract.

See the [clause-to-evidence matrix](../verification/2026-10-08-contract-matrix.md) (administrative record in Chinese) for exact tests, implementation references and coverage gaps. The current maintenance plan Task 5 checks this mapping; it does not declare every product clause fully accepted.

## Open questions

Historical task-by-task acceptance, earlier approvals/plugin versions and complete interactive host behavior remain unverified. Current known coverage gaps are listed in the matrix; no new capability or stronger guarantee is introduced here.
