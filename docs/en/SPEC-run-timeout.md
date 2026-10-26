# Specification: run-timeout (keep progress on timeout, resume after timeout)

[简体中文](../../spec/run-timeout.md) | English

Drafted 2026-10-26. Prompted by ecosystem proposal S35: a single `/delegate:run` is capped at 540 seconds, and a timeout (exit 124) today leaves only the Git acceptance block — no final answer, no run_id result line, no way to resume, and half-edited files in the working tree. ecosystem-lead accepted it with: "S35 受理：先实测两个没验证的假设（中止后还能不能 resume、到期前能不能提示收尾），结果报你，再写 Spec 给我审；接口 1.2 只增不改。" (Accepted: first test the two unverified assumptions — can a stopped run be resumed, can the model be prompted to wrap up before the deadline — report back, then write the Spec for review; interface 1.2 is additions only.) The findings are in the [S35 probe record](../verification/2026-10-26-delegate-s35-timeout-probe.md). ecosystem-lead confirmed them and, through delegate-owner, listed what this spec must state: the wrap-up layers are combined; the wrap-up round has its own hard deadline and a model-free fallback; 1.2 is additions only and must define the result line and exit code; unverified items become assumptions; the killpg EPERM race is fixed; trust_level (S36) is out of scope. The consumer is module-crew's `crew-codex-offload` (project switch `codexOffload`), which always calls run with `--resumable`. It handles `done` / `needs-input` / `timeout` separately: on `timeout` it does not commit on Codex's behalf, hands the progress to the user, and resumes only with the user's consent; any status it does not recognise makes it stop and ask the user.

## Assumptions (confirmed by the user on 2026-10-26)

The user replied "继续" ("continue") to T1–T12. After options A (every run resumable) and B (compromise) were laid out for T2/T3, the user said: "选方案 B：普通 run 保留 --ephemeral，只加时间预算和兜底；同意为此修订 run-resume 的 Always 规则。" (Option B: plain runs keep `--ephemeral` and only gain the time budget and the fallback; I agree to revise run-resume's Always rule for this.) ecosystem-lead, through delegate-owner, accepted T7, T8, T9 and T10 and added requirements that are written into those clauses (a relay, not a user approval).

- **T1** New module `run-timeout`, depending on channel, integration-interface and run-resume. Each existing clause of those modules that this module supersedes gets one pointer sentence in its own spec (see "Impact"); nothing else changes.
- **T2** A plain run (without `--resumable`) still passes `--ephemeral` and its arguments are unchanged; resumable runs and resumes never passed it and are unchanged. review is out of scope.
- **T3** Every run (plain and resumable) and every resume round gets a time-budget paragraph in its prompt (first wrap-up layer). A model that stops on budget starts its final answer with `TIME_UP:`.
- **T4** When a resumable run or a resume is forcibly stopped and a session id is available, one read-only wrap-up round is resumed that only writes progress and runs no commands (second layer). It has its own hard deadline. Plain runs have no session to resume and get no wrap-up round.
- **T5** When a plain run is forcibly stopped, or the wrap-up round times out, fails or returns an empty answer, or there is no session id, a fixed fallback text is printed without calling the model; in write mode it lists the changed files.
- **T6** The overall deadline stays 540 seconds (`DELEGATE_TIMEOUT_SECONDS` can only shorten it). Wrap-up deadline `W = min(45, T // 6)`, main-run deadline `M = T − W`, prompt threshold for "start no new step" `S = max(M − 90, M // 2)`. For T=540: W=45, M=495, S=405. Plain runs are also stopped at M so both kinds share one threshold; the remaining time only serves the fallback and cleanup. These numbers are configuration constants defined in one place in code; the prompt only uses the computed values and never hard-codes them; they are calibrated in the paid verification at implementation time (ecosystem-lead's requirement).
- **T7** New end status `timeout`, covering both a model-initiated `TIME_UP:` and a forced stop; the exit code is always 124.
- **T8** On `status=timeout`, stdout carries the answer (progress or fallback text), the metadata block and the result line. The upgrade notes must say: to decide success, check exit code 0 first, then `status=done`; a result line does not mean success.
- **T9** `--resume` additionally accepts runIds whose status is `timeout`; all other rejection rules stay. Plain runs write no state file, so their runIds are still rejected with `run not found`.
- **T10** `interface.json` moves to `1.2`: `"timeout"` is appended to `run.resume.statuses` and `run.timeout` is added. No existing field is removed or changes meaning; the major version is unchanged. Precondition: it is documented that `statuses` is an open set — a consumer meeting an unknown value must stop or treat it as failure, never as completion. module-crew is currently the only consumer that reads run; spec-guard and decision-inbox do not.
- **T11** The killpg EPERM race in `run_codex.py` is fixed in this module.
- **T12** Out of scope: S36 (`--write` persisting project trust); review timeouts; the claude-code backend; changing the 540-second deadline; automatic resume (the consumer resumes only after the user agrees); resuming plain runs after a timeout.

### Unverified assumptions, to be tested at implementation time

These come from the "unverified" list of the probe record. The design assumes they hold; the Plan lists them as a paid gate with its own authorization. If one fails, this spec is revised. Results of Checkpoint 3 on 2026-10-26 follow each item; details in the [Checkpoint 3 record](../verification/2026-10-26-delegate-run-timeout-cp3.md).

- **H1** With the real 540-second deadline the model honours the T6 threshold with margins similar to the scaled-down probe (margin 1.1–3.2 s; 17–19 s from the threshold to exit).
- **H1** Result: holds. With the real 540-second deadline the model stopped itself at 412 s; total 422 s, 73 s before M.
- **H2 (revision R1)** Most wrap-up rounds return in 10–15 s, but server-side tails are not rare: across both probes, 2 of 8 samples exceeded 45 s (185 s; stopped after 45 s). On a tail, T4's hard deadline stops the wrap-up round and T5's fallback prints the fixed text, so the total stays within the limit; only the model-written progress is lost. Constants unchanged.
- **H3 (revision R1, still unverified)** On a forcibly stopped session with a large context, the wrap-up round still finishes within W. Checkpoint 3 could not build a large context: Codex truncates large command output, and sessions stayed around 32k tokens, where the wrap-up round took about 12–15 s. Sessions of a hundred thousand tokens or more were not tested; this stays an assumption.
- **H4** Models and reasoning efforts other than the local default follow the time budget and the `TIME_UP:` marker as well (the probe only covered `gpt-6.1-sol` at `none` and `high`).
- **H4** Result: holds (one model). `gpt-5.6-terra` stopped itself at 72 s (threshold 50 s, deadline 100 s).
- **H5** Resuming a write-mode run after a timeout does not repeat completed writes (held in the probe when the prompt said to check the file first; a half-written file was not tested). Checkpoint 3: it also held when the resume prompt did not say to check the file.
- **Finding (revision R1)** While a long command runs, Codex hands control back to the model, which can run `date +%s` and stop on budget; two runs deliberately stalled with `sleep 300` never reached a forced stop. The probe's inference that "a single long command defeats the first layer" does not hold. Forced stops come mainly from server-side tails (once the main run's first turn got no response for about 145 s), when the wrap-up round often stalls too, so the wrap-up deadline is not raised for tails.
- **Revision R1 (2026-10-26; the user's words: "选 A：常数不变，只修订规格 H2、H3 的措辞并记录新发现。" — option A: keep the constants, only revise the wording of H2 and H3 and record the new finding)**: H2 and H3 now read as above, with the finding and per-item results added; two passages are also aligned with the implementation (`.baseline` added to the retention list; tests use their own fake codex and do not change `stub-codex`). The T6 constants and all other clauses are unchanged.

## Impact

- **Plain-run prompt gains the time-budget paragraph (revises an approved rule):** run-resume's Always rule "a plain run is byte-for-byte identical to before" is revised, with the user's consent on 2026-10-26, to "a plain run is identical to before except for the time-budget paragraph". The "prompt unchanged" part of RR-01 is superseded by this module; arguments (including `--ephemeral`) are unchanged.
- **Plain runs actually run for `M` seconds:** channel's "default/maximum 540 seconds" is unchanged, but the Codex main run now gets at most `M` seconds (495 at 540); the rest is left for the wrap-up round or the fallback.
- **Timeout output:** supersedes run-resume A3 ("timeout … prints no such line") and the output part of channel's "timeout exits 124": a timeout now prints the answer and the result line, still with exit code 124.
- **A result line does not mean success:** timeouts now have a result line too. Consumers decide success by exit code 0 first, then `status=done`; this goes into the README and the release notes' upgrade section.
- **Resume rejection table:** in run-resume, `run not waiting for input` now triggers when the status is neither `needs-input` nor `timeout` (was: not `needs-input`).
- **Consumers:** a consumer that reads `1.1` still sees exit code 124 on timeout and can treat it as failure, never as completion. Only consumers checking `>=1.2,<2.0` use the `timeout` status and resume.
- **Unchanged:** plain runs still leave no session file on the machine; session retention for resumable runs is as today.

## Tech stack and commands

Bash 3.2 wrapper, Python 3 standard library, Git, Codex CLI (0.162.1 on the test machine). No new dependency, hook or command entry.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-run-timeout.py
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-interface.py
/bin/bash plugins/delegate/tests/test-channel.sh
python3 -B plugins/delegate/tests/test-channel-regressions.py
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/codex-exec.sh        → time-budget paragraph, deadline split, wrap-up round, fallback with file list, timeout output
plugins/delegate/scripts/run_codex.py         → stop_group also tolerates PermissionError (EPERM)
plugins/delegate/scripts/run_state.py         → TIME_UP detection, deadline constants and arithmetic, timeout state, resume accepts timeout
plugins/delegate/interface.json               → interface 1.2: timeout appended to statuses, run.timeout added
plugins/delegate/commands/run.md / help.md    → timeout output, resume, how to decide success
plugins/delegate/tests/test-run-timeout.py    → new: stub tests
plugins/delegate/tests/test-run-resume.py     → adjust only the assertions listed under Impact
plugins/delegate/tests/test-interface.py      → 1.2 assertions
plugins/delegate/tests/test-channel.sh / test-channel-regressions.py → plain-run prompt, EPERM regression
spec/run-timeout.md / docs/en/SPEC-run-timeout.md → this contract
spec/channel.md, spec/run-resume.md, spec/integration-interface.md and English pages → pointer sentences; run-resume's Always rule revised as in Impact
spec/CAPABILITY-MAP.md / docs/en/capability-map.md → new module row
plugins/delegate/README.md / README.en.md, docs/releases/unreleased.md and English page → usage, open-set note, upgrade note
```

## Behaviour contract

### Deadline constants and split

`T` is the overall deadline from the existing logic (default/maximum 540; `DELEGATE_TIMEOUT_SECONDS` can only shorten it). The cap 45 and divisor 6, the threshold margin 90 and divisor 2 are configuration constants defined in one place (tests read the same definition). `W = min(45, T // 6)`, `M = T − W`, `S = max(M − 90, M // 2)`. The main run is handed to `run_codex.py` with deadline `M`; the wrap-up round gets `W`. Both plus process cleanup stay within the 600-second Bash limit.

### Time-budget paragraph (first layer)

Appended to the end of every run's and every resume round's prompt (after the task body or the user's answer). `<T0>` is the epoch second just before Codex is started; `<M>` and `<S>` are the computed values:

> 【时间预算】本次运行开始于 epoch 秒 <T0>，<M> 秒后会被强制中止，中止时不保留未写出的答复。需要判断用时就运行 `date +%s`。已用时达到 <S> 秒后，不要再开始新的步骤，也不要启动预计会跨过期限的长命令，立即给出最终答复：第一行以 `TIME_UP:` 开头，后面写已完成的进度、做到一半的步骤（如有）、下一步应从哪里开始。

(Meaning: this run started at epoch second <T0> and is forcibly stopped after <M> seconds, losing any answer not yet written. Run `date +%s` to check elapsed time. Once <S> seconds have elapsed, start no new step and no long command likely to cross the deadline; give the final answer immediately, first line starting with `TIME_UP:`, followed by completed progress, any half-done step, and where to continue.)

Classification: an answer whose first non-blank text is `TIME_UP:` is `timeout`; otherwise resumable runs and resumes follow run-resume's `NEED_USER:` / `done` rules, and plain runs are `done`.

### Wrap-up round (second layer; resumable runs and resumes only)

When the main run of a resumable run or a resume exits 124 (forcibly stopped):

1. Take the session id from the process log (`session_id_from_log`). If none, go to the fallback.
2. Resume one round with `codex exec resume <session id>`, arguments as for resume but with the sandbox **fixed** to `-c sandbox_mode="read-only"` (also in write mode), deadline `W`, log `<runId>.wrapup`, answer `<runId>.wrapup.answer`. Prompt:

   > 【收尾】本次运行已到期被中止。不要再执行任何命令，也不要继续做任务。只写进度：第一行以 `TIME_UP:` 开头，后面写已完成的步骤及结果、做到一半的步骤（如有）、下一步应从哪里开始。

   (Meaning: this run hit its deadline and was stopped. Run no more commands and do not continue the task. Only write progress: first line starting with `TIME_UP:`, then completed steps and results, any half-done step, and where to continue.)

3. If the wrap-up round exits 0 with a non-empty answer, its answer becomes this run's answer (the status is `timeout` whether or not it starts with `TIME_UP:`).
4. Otherwise use the fallback.

When a plain run's main run exits 124, there is no wrap-up round; go straight to the fallback.

### Fallback (no model)

The answer is this fixed text:

```text
delegate: 已中止，未取得进度说明（<原因>）。会话 ID：<uuid|无>；可续跑：<是|否>。
<文件清单>
```

(Meaning: stopped, no progress obtained (<reason>). Session id: <uuid|none>; resumable: <yes|no>. Followed by the file list.)

`<原因>` is one of 「普通 run 不保留会话」 (plain runs keep no session), 「收尾轮超时」 (wrap-up round timed out), 「收尾轮失败（退出 N）」 (wrap-up round failed, exit N), 「收尾轮答复为空」 (empty wrap-up answer), 「未取得会话 ID」 (no session id). `<文件清单>` (file list): in write mode, a line 「改动的文件（与运行前比较）：」 (changed files, compared with before the run) followed by the `git status --porcelain` entries that are new or different from the pre-run baseline, one per line, or 「无」 (none); write mode therefore also records the full porcelain snapshot before the run (today only the count). In read-only mode, 「只读运行，不列文件」 (read-only run, no file list). Known limitation: a file already modified before the run and modified again keeps the same porcelain line and is not listed; the Git acceptance block's `git diff --stat` is authoritative.

### End status, output and exit code

| Case | status | Exit code | stdout |
|---|---|---|---|
| Completed normally | `done` | 0 | as today |
| First line `NEED_USER:` (resumable runs and resumes) | `needs-input` | 0 | as today |
| First line `TIME_UP:` (model stopped itself) | `timeout` | 124 | answer, metadata, result line |
| Resumable run / resume forcibly stopped | `timeout` | 124 | wrap-up answer or fallback text, metadata, result line |
| Plain run forcibly stopped | `timeout` | 124 | fallback text, metadata, result line |
| Failure, signal (143/130/129), empty answer | — | unchanged | unchanged, no result line |

- The metadata block is as today plus one line `收尾：<主动停|收尾轮|兜底（原因）>` (wrap-up: model stopped / wrap-up round / fallback (reason)).
- Result line: `delegate: run_id=<id> status=timeout resumable=<true|false>`, still the last stdout line. `resumable=true` exactly when it is a resumable run or resume, a session id was obtained and the state file was written. Plain runs are always `resumable=false`.
- The write-mode Git acceptance block is printed as usual (to stderr on non-zero exit, per the existing rule); nothing is rolled back.
- On a forced stop, stderr additionally carries `delegate: codex 超过 <M> 秒被中止。完整过程日志：<log>` (not printed when the model stopped itself).

### State file

Only resumable runs and resumes write a state file (as today); `status` may be `timeout`. The wrap-up round does not change `sessionId` (same session).

### Resume

- `--resume <runId>` accepts runIds whose status is `needs-input` or `timeout`; claim, repository, write-mode consistency and the other rejection rules are unchanged.
- Resuming from `timeout` sends the same content as a run-resume resume (`【用户答复】…`) plus the time-budget paragraph; the round is classified by run-resume's resumable rules and may itself end in `timeout`.
- Resuming a write-mode run after a timeout requires `--write` (same as the original run). delegate never decides on the user's behalf whether to resume.

### Retention and cleanup

The "keep the latest 50 log sets" rule is unchanged; deleting a set also deletes the same runId's `.answer`, `.state.json`, `.resumed`, `.wrapup`, `.wrapup.answer` and `.baseline` (the write-mode pre-run snapshot). Codex session files are still never read or deleted.

### killpg EPERM

`stop_group` in `run_codex.py` tolerates both `ProcessLookupError` and `PermissionError` on both `os.killpg` calls (macOS returns EPERM when only zombies remain in the group), then calls `process.wait()` as before. Exit codes are unaffected.

### Interface 1.2

```json
{
  "interface": "1.2",
  "review": {"command": "/delegate:review", "backends": ["codex", "claude-code"], "readOnly": true,
             "report": {"schemaVersion": 1}},
  "run": {
    "command": "/delegate:run", "backends": ["codex"], "write": "explicit",
    "resume": {"optIn": "--resumable", "option": "--resume", "backends": ["codex"],
               "statuses": ["done", "needs-input", "timeout"]},
    "timeout": {"status": "timeout", "exitCode": 124}
  },
  "doctor": {"command": "/delegate:doctor"}
}
```

Consumers use `timeout` when the version is `>=1.2,<2.0`. On `1.1`, or without `run.timeout`, behave as today: treat 124 as failure and do not resume.

`statuses` is an open set: later minor versions may append values, and a consumer meeting an unknown value must stop or treat it as failure, never as completion. JSON cannot hold comments, so this is stated in the README's external-interface section and in the pointer sentence in `spec/integration-interface.md`, plus their English pages.

## Code style

Keep the existing style: Bash 3.2 compatible, variables as `${VAR}`, the existing guard for empty-array expansion; Python standard library, 4-space indent, snake_case; no JSON parsing or deadline arithmetic in shell — leave it to `run_state.py`. Existing example (`run_codex.py`):

```python
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
```

## Testing strategy

`test-run-timeout.py` uses standard-library `unittest`, its own fake codex (as `test-run-resume.py` does; the shared `stub-codex` is not changed) and a temporary Git fixture, with `DELEGATE_TIMEOUT_SECONDS` shortened to a few seconds. The stub must tell the first round from a resume (for example reading `STUB_RESUME_ANSWER` and `STUB_RESUME_SLEEP_SECONDS` on resume) and be able to print a `session id:` line in its log. Coverage:

- plain runs still pass `--ephemeral` with other arguments unchanged; resumable runs and resumes still do not;
- every run and resume prompt contains the time-budget paragraph, with `<M>` and `<S>` computed from the constants and `DELEGATE_TIMEOUT_SECONDS`;
- first line `TIME_UP:` → `status=timeout`, exit 124, stdout has the answer and the result line, no wrap-up round (once for a plain run, once for a resumable run);
- a resumable run times out → exactly one wrap-up round with `exec resume`, read-only sandbox (also in write mode), the same session id and the wrap-up prompt; on success its answer is printed and `resumable=true`;
- wrap-up round times out, fails, returns empty, or no session id → fallback text with the right reason and `resumable`;
- a plain run times out → no wrap-up round, fallback reason 「普通 run 不保留会话」, `resumable=false`;
- write-mode timeout: the fallback lists changed files (changes that existed before the run are not listed) and the Git acceptance block is printed; read-only mode prints 「只读运行，不列文件」;
- a resumable-run timeout writes a state file; `--resume` accepts `timeout` and still rejects `done`; a plain-run timeout runId is rejected (`run not found`);
- cleanup also removes `.wrapup` and `.wrapup.answer`;
- signal interruption (143) triggers no wrap-up round and prints no result line;
- total time stays within `T` plus cleanup margin;
- `run_codex.py` does not crash and returns the original exit code when `os.killpg` raises `PermissionError` (injected or simulated).

`test-interface.py`: `interface == "1.2"`, `run.resume.statuses == ["done", "needs-input", "timeout"]`, `run.timeout == {"status": "timeout", "exitCode": 124}`, both command fields unchanged.

Existing tests only adjust the assertions listed under Impact (plain-run prompt with the time-budget paragraph, timeout behaviour, rejection condition), each listed in the Plan; all other assertions stay.

Write the tests first and see them fail, then implement. Stub tests prove arguments and flow only, not real-model behaviour.

**Paid verification (gate, separate authorization):** H1–H5 are tested at implementation time; the number of runs, models and expected duration are listed in the Plan's gate. Without authorization they stay "unverified".

## Boundaries

- **Always:** print the result line and whatever progress is available on timeout; the wrap-up round is always read-only; the fallback never calls a model; total time stays within the 600-second Bash limit; Chinese and English contracts stay in sync; `interface.json`, capability facts and tests change together.
- **Ask first:** changing the 540-second deadline or the T6 formula; having delegate resume automatically; making plain runs resumable (option A); adding the same mechanism to review; paid verification, commits, pushes, releases.
- **Never:** remove or change the meaning of an existing `interface.json` field, or bump the major version; run the wrap-up round with a write sandbox or let it run commands; report `timeout` as `done` or exit 0; change plain-run arguments; read or delete Codex session files; decide on resume for the user; handle S36 in this module.

## Success criteria and verification map

- **RT-01:** plain runs still pass `--ephemeral` with unchanged arguments; resumable runs and resumes keep their arguments (stub test).
- **RT-02:** every run and resume prompt contains the time-budget paragraph with correct `T0`, `M`, `S`, the numbers coming from the shared constants (stub test).
- **RT-03:** first line `TIME_UP:` → `timeout`, exit 124, answer + metadata + result line, no wrap-up round (stub test).
- **RT-04:** after a forced stop of a resumable run or resume, exactly one read-only wrap-up round runs with the right arguments and prompt; on success its answer is printed (stub test).
- **RT-05:** plain-run forced stop, wrap-up timeout, failure, empty answer or missing session id → fallback text with correct reason and `resumable` (stub test).
- **RT-06:** write-mode fallback lists changed files; the Git acceptance block is printed; no rollback (stub test).
- **RT-07:** total time within `T` plus cleanup margin (stub test, shortened deadline).
- **RT-08:** a resumable-run timeout writes a state file; `--resume` accepts `timeout`, rejects `done` and plain-run runIds; cleanup covers the new files (stub test).
- **RT-09:** signal, failure and empty-answer behaviour unchanged (stub tests, existing assertions).
- **RT-10:** `run_codex.py` tolerates EPERM (regression test).
- **RT-11:** `interface.json` is 1.2 with the fields above; both plugin validations pass.
- **RT-12:** `run.md`, `help.md`, Chinese and English READMEs, contracts, pointer sentences, the revised run-resume Always rule and release notes are in sync, including the open-set note and the "check the exit code first" upgrade note.
- **RT-13:** full validation, both plugin validations and `git diff --check` pass.
- **RT-14 (paid, gate):** H1–H5 tested and recorded; any failure goes back to this spec.

## Open questions

- The T6 constants (45, ÷6, 90, ÷2) stay unchanged after Checkpoint 3 per R1; they can be reassessed after H3 is tested or more tail samples exist.
- A model that misses `TIME_UP:` but finishes everything after the threshold is correctly `done`; a model that misses the marker after doing only part of the work is misclassified as `done` (a known limitation of the same kind as run-resume A5).
