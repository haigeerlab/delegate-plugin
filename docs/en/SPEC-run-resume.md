# Specification: run-resume (resumable delegation)

[简体中文](../../spec/run-resume.md) | English

Drafted 2026-10-24. Prompted by ecosystem proposal S32 (smooth multi-module parallelism and quota offload): on 2026-10-24 the user approved the interface proposal ("approve as recommended"), which moves the delegate interface from `1.0` to `1.1`, additions only. The consumer is module-crew's quota-offload switch `codexOffload`: after Spec and Plan are approved in a Claude session, the coordinator hands implementation to Codex through `/delegate:run`. When Codex reaches a decision the user must make, it stops, the coordinator relays the question, and the run resumes with the user's answer. Evidence: section 8 of the research report, where `codex exec resume <session id> "<answer>"` kept context across three resumes. Codex stopped too early there, so the prompt has to say to finish unaffected work first.

## Assumptions (confirmed by the user on 2026-10-24 as A1–A8)

- **A1** New module `run-resume`, depending on channel and integration-interface. No existing clause in channel or integration-interface changes; each gets one pointer sentence to this module.
- **A2** Resumable mode is opt-in: run gains `--resumable`. A run without it behaves byte-for-byte as today (prompt, `--ephemeral`, Codex arguments); the only addition is the A3 result line. (Since R2 a fixed approval option is also added; see the revision history.)
- **A3** Every successfully returned run appends `delegate: run_id=<id> status=<done|needs-input> resumable=<true|false>` to stdout. `needs-input` still exits 0. Timeout, failure and empty answer keep their existing exit codes and print no such line.
- **A4** Resume is `--resume <runId> [--write] -- "<user answer>"`. Only the latest round with status `needs-input` is accepted. It must run in the same repository root, `--write` must match the original run, and `--model` and `--effort` are not accepted (the original settings are reused). Each round gets a new runId. State files are pruned with the existing log retention. delegate never deletes Codex's own session files.
- **A5** `needs-input` is detected only through the prompt-defined `NEED_USER:` marker, not `--output-schema`. A model that omits the marker is classified `done`; this is a known limitation.
- **A6** `interface.json` moves to `1.1` and only adds the optional field `run.resume`. `review.command`, `doctor.command` and every other existing field stay unchanged; the major version is unchanged.
- **A7** Out of scope: a background daemon (callers use Bash background mode); changing the 540-second deadline; resuming timed-out or failed runs; git commit permission (module-crew's prefix allow rules); resume for the claude-code backend.
- **A8** Two verification layers: free stub tests, plus one paid real run. The paid run is a gate in the Plan with its own authorization.

## Revision history

- **R1 (2026-10-25, user chose "option A"):** In the first paid run (RR-10), the read-only resume log header said `sandbox: read-only`, yet a file-writing command still succeeded with no approval event in the log. The inferred cause is the user's local Codex configuration `approval_policy = "on-request"` with `approvals_reviewer = "guardian_subagent"` approving the out-of-sandbox command, which conflicts with S32 decision 7 ("no approvals by an automatic review agent"). Revision: resumable runs and every resume round always pass `-c approval_policy="never"`, so out-of-sandbox commands are refused outright and never sent to any approver; commits in write mode are still governed by the consumer's prefix allow rules (research section 8.1 verified them under `never`). Plain runs are unchanged; whether plain runs are affected by the local approval configuration in the same way is out of scope and tracked as a follow-up.
- **R2 (2026-10-25; the user's words relayed by the delegate owner: "extend the approval_policy=\"never\" revision to every run, resume and review call path, and test whether the existing read-only paths get approved"; effective after review and approval in this session):** R1 extends to every delegate call that has Codex carry out work: plain run (read-only and write), resumable run, resume and the Codex review backend all pass `-c approval_policy="never"`. Probe-only calls that use no model (`codex --version`, `codex login status`, `codex features list`) are excluded. This replaces "plain runs are unchanged" in R1: plain runs gain only this option; prompt and other arguments are unchanged. One more paid check runs the published v0.5.3 read-only run and review under the local approval configuration to see whether they write a file; the delegate owner uses the result to judge the meaning of `readOnly: true` in the published interface.
  - Impact: in write-mode runs, commands that need to leave the sandbox (such as `git commit` inside a worktree, or network access) could previously be approved by the local approver and are now refused; consumers that need commits keep relying on prefix allow rules or commit on the caller side.
  - This module therefore changes one argument in `review_execution.py`, owned by claude-review, and adds one pointer sentence to `spec/claude-review.md` and its English page.

## Tech stack and commands

Bash 3.2 wrapper, Python 3 standard library, Git and the Codex CLI (help text checked locally on 0.162.1). No new dependency, hook or command entry; the command is still `/delegate:run`.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-interface.py
/bin/bash plugins/delegate/tests/test-channel.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/codex-exec.sh        → --resumable / --resume branches, result line, state cleanup
plugins/delegate/scripts/run_state.py         → new: runId validation, state files, NEED_USER classification, session id extraction (stdlib)
plugins/delegate/scripts/delegate_backend.py  → parse and forward the two new options, validate combinations
plugins/delegate/scripts/delegate_cli.py      → let the run subcommand accept the new options
plugins/delegate/scripts/delegate_capabilities.py → add the codex resume capability fact
plugins/delegate/interface.json               → interface 1.1, run.resume
plugins/delegate/commands/run.md / help.md    → usage and answer discipline
plugins/delegate/tests/test-run-resume.py     → new: stub tests
plugins/delegate/tests/test-interface.py      → 1.1 assertions
plugins/delegate/scripts/review_execution.py  → R2: fixed approval option on the Codex review call (one argument)
plugins/delegate/tests/test-review-backends.py → R2: assert plain run (read-only, write) actual arguments include it
plugins/delegate/tests/test-review-execution.py → R2: assert Codex review actual arguments include it
spec/claude-review.md / docs/en/SPEC-claude-review.md → R2: one pointer sentence each to this revision history
plugins/delegate/README.md / README.en.md     → resumable section; interface section updated for 1.1
spec/run-resume.md / docs/en/SPEC-run-resume.md → this contract
spec/channel.md, spec/integration-interface.md and English pages → one pointer sentence each
docs/releases/unreleased.md and English page  → pending release notes
```

## Behavior contract

### Plain run (no `--resumable`)

The prompt, `--ephemeral` and other arguments are the same as today; the only addition is `-c approval_policy="never"` after the auth configuration (R2). On success the existing metadata block is followed by:

```text
delegate: run_id=20261024183015.12345 status=done resumable=false
```

`run_id` is the existing `RUN_ID` used for log file names (`<14-digit timestamp>.<pid>`).

### Resumable run (`--resumable`)

- `--ephemeral` is not passed, so Codex keeps the session in its own session directory (`~/.codex/sessions`). `-c approval_policy="never"` is added (R1) instead of the approval mode in the user's configuration. Everything else (auth configuration, sandbox, model, effort, `-o`, stdin=/dev/null, process group and 540-second deadline) matches a plain run.
- The resumable prompt replaces the existing "non-interactive delegation" preamble. Its sandbox sentence is the same as the current read-only or write variant:

  > [Resumable delegation] Your final answer will be relayed to the user; after the user answers, this session continues with that answer. First do the tasks not affected by pending decisions, and stop only when a decision needs the user (a trade-off the spec does not cover, a test that cannot be made to fail first, a high-risk irreversible action). To stop, start the first line of your final answer with `NEED_USER:` followed by the question for the user, then the progress so far and the options. If the user is not needed, finish the work and do not start the first line with `NEED_USER:`.

- The session id is taken from the first `session id: <uuid>` line in the process log. If none is found, the run still returns, with `resumable=false` and the reason on stderr.
- Classification: an answer that starts with `NEED_USER:` after leading whitespace is `needs-input`; anything else is `done`. On `needs-input` the whole answer is still printed, and **the question text is everything after the marker**.
- A successful return writes `${TMPDIR:-/tmp}/delegate/<runId>.state.json` (0600 in a 0700 directory, symlinks rejected) with: `schema` (1), `runId`, `sessionId`, `repository` (real path of the Git root), `write`, `model`, `effort`, `status`, `parent` (previous runId for a resume, otherwise `null`).

### Resume (`--resume <runId>`)

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --resume <runId> [--write] -- "<user answer>"
```

- Runs `codex exec resume`. The Codex sandbox can only be passed as `-c sandbox_mode="read-only|workspace-write"` (`resume` has no `--sandbox`). Model and effort come from the state file. `-c approval_policy="never"` is always passed as well (R1). Auth configuration, `-o`, stdin=/dev/null, process group and deadline match a plain run; `--ephemeral` is not passed.
- Text sent to Codex:

  > [User answer] <answer verbatim>
  >
  > Continue as agreed: first do the tasks not affected by pending decisions; if the user is needed again, start the first line of your final answer with `NEED_USER:`.

- Each round gets a new runId and log. The result line and classification are the same as for a resumable run, and `parent` in the state file points to the previous round, so resumes can chain.
- Write mode prints the same Git acceptance block as existing writes, with the baseline recorded again before the round starts.
- Before starting, delegate exclusively creates `<runId>.resumed` so one question cannot be resumed twice. If something fails after the marker is created but before Codex starts, the marker stays and a new resumable run is needed.

**Refusals (exit 64, Codex not called, stderr `delegate: <reason>`):**

| Reason | When |
|---|---|
| `invalid run id` | runId does not match `^[0-9]{14}\.[0-9]+$` |
| `run not found` | no state file (not `--resumable`, run failed, or pruned by retention) |
| `run not resumable` | the state file has no session id |
| `run not waiting for input` | status is not `needs-input` |
| `run already resumed` | the runId has already been resumed |
| `repository mismatch` | the current Git root differs from the state file |
| `write mode mismatch` | `--write` differs from the original run |
| invalid combination | `--resume` combined with `--resumable`, `--model`, `--effort` or `--backend claude-code`; empty answer |

### Retention and cleanup

When the existing "keep the latest 50 logs" pruning deletes a log, it also deletes that runId's `.state.json` and `.resumed`. Cleanup failure does not change the run status. Codex's own session files are managed by Codex; delegate neither reads nor deletes them.

### Interface 1.1

```json
{
  "interface": "1.1",
  "review": {
    "command": "/delegate:review",
    "backends": ["codex", "claude-code"],
    "readOnly": true,
    "report": {"schemaVersion": 1}
  },
  "run": {
    "command": "/delegate:run", "backends": ["codex"], "write": "explicit",
    "resume": {"optIn": "--resumable", "option": "--resume", "backends": ["codex"],
               "statuses": ["done", "needs-input"]}
  },
  "doctor": {"command": "/delegate:doctor"}
}
```

Consumers check `>=1.1,<2.0` before resuming. If they read `1.0` or find no `run.resume`, they behave as today (no resume). Like `backends`, `resume.backends` means supported, not available.

## Answer and authorization discipline (written into `run.md`)

- The answer passed to `--resume` must be the user's own reply verbatim, or a paraphrase the user explicitly accepted. The calling model must not answer a `needs-input` question on the user's behalf. delegate cannot verify this; it is command-level discipline, not a technical lock.
- A resume with `--write` requires that the original run was authorized to write and that the user's answer did not withdraw that authorization. delegate only checks that `--write` matches the original run; it does not authorize anything for the user.
- `needs-input` is neither a failure nor an approval; the question goes to the user as written.

## Code style

Keep the existing style: Bash 3.2 compatible, `${VAR}` expansions, the existing empty-array guard; Python standard library, 4-space indentation, snake_case; JSON produced by a serializer. Shell code does not parse JSON; `run_state.py` does. Existing example (`codex-exec.sh`):

```bash
if [ -n "${MODEL}" ]; then
  EXTRA+=(-m "${MODEL}")
fi
```

## Testing strategy

`test-run-resume.py` uses standard-library `unittest`, the existing `stub-codex` (which records argv and writes `STUB_ANSWER` to the `-o` file) and temporary Git fixtures; the stub may gain an optional log header. Coverage:

- a plain run passes exactly the same Codex arguments as before, and stdout only gains the result line;
- `--resumable` arguments, prompt, state file content and permissions, session id extraction, and the fallback when no session id is found;
- `done` and `needs-input` classification, including leading whitespace and a marker that is not on the first line;
- resume arguments (`exec resume`, `-c sandbox_mode`, reused model and effort, session id, answer text), the new runId and `parent`;
- every row of the refusal table exits 64 without calling the stub;
- write-mode resume prints the Git acceptance block;
- cleanup also deletes state files.

`test-interface.py` adds: `interface == "1.1"`; `run.resume.backends` equals the backends whose `resume` is true in `BACKENDS`; `review.command == "/delegate:review"` and `doctor.command == "/delegate:doctor"`. Existing assertions are unchanged.

Tests are written first and shown to fail before implementation. Stub tests prove arguments and flow only, not real Codex behavior.

**Paid real run (gate, separately authorized):** with real Codex, in a temporary Git repository under the home directory (not `/tmp`, to avoid sandbox false passes), run `--resumable` until it hits a pending decision, then `--resume` once. Confirm three things:

- the session id can be extracted from the log;
- `-c sandbox_mode` takes effect on resume (writing a file during a read-only resume is refused);
- the context carries over.

## Boundaries

- **Always:** keep plain runs byte-for-byte unchanged, guarded by tests; keep Chinese and English contracts in sync; change `interface.json`, capability facts and tests together.
- **Ask first:** making every run resumable by default; resuming timed-out or failed runs; structured answers through `--output-schema`; changing the 540-second deadline; the paid run, commits, pushes and releases.
- **Never:** change `review.command` or `doctor.command`, or bump the major version; silently escalate to write on resume; let any call that has Codex carry out work inherit the user's configured approval mode (including approvals by an automatic review agent); answer a `needs-input` question for the user; read or delete Codex session files; write state files or session ids into the business repository.

## Success criteria and verification map

- **RR-01:** Without `--resumable`, the prompt and other arguments are unchanged, the arguments gain only `approval_policy="never"` (R2), and output gains only the result line (stub tests).
- **RR-02:** `--resumable` omits `--ephemeral`, always passes `approval_policy="never"`, uses the prompt containing "first do the tasks not affected by pending decisions … stop only when", writes a 0600 state file and extracts the session id; without a session id it falls back to `resumable=false` (stub tests).
- **RR-03:** `done` / `needs-input` follows the marker; `needs-input` exits 0 and the answer is printed in full (stub tests).
- **RR-04:** Resume calls `codex exec resume` with the right sandbox, `approval_policy="never"`, model, effort, session id and answer, and produces a new runId with a `parent` chain (stub tests).
- **RR-05:** Every row of the refusal table exits 64 without calling Codex (stub tests).
- **RR-06:** Write-mode resume prints the Git acceptance block; read-only resume does not (stub tests).
- **RR-07:** `interface.json` is 1.1 with `run.resume`; both command fields keep their values; the consistency test passes; both plugin validate runs pass.
- **RR-08:** Retention also prunes state files (stub tests).
- **RR-09:** `run.md`, `help.md`, both READMEs, both contracts and the release notes are in sync and include the answer and authorization discipline.
- **RR-10:** The paid run confirms session id extraction, the resume sandbox (writing during a read-only resume is refused) and context continuity (gate, separately authorized; marked unverified without authorization). First run on 2026-10-25: session id, the `--` separator, context continuity and finishing unaffected tasks first all held; writing during a read-only resume was **not refused**, so this item is re-run after the R1 revision.
- **RR-11:** Full validation, both plugin validate runs and `git diff --check` pass; existing test assertions are unchanged.
- **RR-12 (R2):** The arguments actually passed to Codex by plain run (read-only, write), resumable run, resume and Codex review all include `-c approval_policy="never"`, asserted by stub tests on the recorded argv, not on source text.
- **RR-13 (R2, paid, gate, separately authorized):** Run the published v0.5.3 read-only run and Codex review once each with a minimal prompt (asking to write a file in the repository) under the local `approval_policy="on-request"` and `approvals_reviewer="guardian_subagent"`, and record whether a file is written; after the change, run the current read-only run once to confirm the write is refused. Report the result to the delegate owner separately.

## Open questions

- Confirmed by the first run: `codex exec resume` accepts `--`, and `-c sandbox_mode` reaches the resume configuration. Whether `approval_policy="never"` makes a read-only resume refuse writes is confirmed by the re-run after R1; if it still fails, this specification is revised again.
- Whether the published v0.5.3 read-only run and review get writes approved by the local approval configuration is checked by RR-13; the result bears on `readOnly: true` in the published `interface.json` and is reported by the delegate owner to ecosystem-lead. This module does not change that field.
- What to do when a large module exceeds 540 seconds belongs to the S32 rollout checks (research section 9.5), not this module.
- Whether timed-out runs should be resumable waits for data from the LIVE-SAAS pilot.
