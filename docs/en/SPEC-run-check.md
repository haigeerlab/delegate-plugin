# Specification: run-check (`--check` runs a check afterwards, `--authorized-by` gives write authorization in advance)

[简体中文](../../spec/run-check.md) | English

Drafted 2026-10-27; approved by the user on 2026-10-27, in the user's words: 「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」 — "Approve the five Specs run-result, run-continue, run-longrun, run-check and run-rules, and start the English pages and the Plan." It corresponds to items 4 and 5 and decision point 3 of ecosystem proposal S38, which the user approved on 2026-10-27, in the user's words: 「……写入授权按有条件折中……」 — "…write authorization takes the conditional compromise…" (full text in [run-result](SPEC-run-result.md)). The proposal's guard clause (originally in Chinese): "`--check` runs outside the sandbox with your permissions, so the command may only come from the checkCommand or quickCheckCommand in the project configuration that you approved, and may not be assembled on the fly by Codex or a module session."

## Premises (confirmed by the user on 2026-10-27; the ones this module uses)

- **S11** `--check "<command>"`:
  - Validation is copied from module-crew S30: POSIX `shlex.split`, matching `_SHELL_OPS` at the start or end of a token, and the three refusal messages are copied character for character (the messages mention module-crew; as required, they are copied as they are). On refusal it exits 64 and does not call Codex.
  - It runs only when the run ended as `done`, in the repository root, as an argument list; for any other status it is recorded as "skipped".
  - The check has its own deadline, 600 seconds by default, not counted in `--timeout`.
  - The exit code and the last 40 lines of output are written into the result file; a failed check does not change the run's status.
- **S12** `--authorized-by <file>`:
  - The file must be a readable regular file, not a symlink, and not empty; delegate only records the path, sha256 and size, and cannot verify the content.
  - `--write` must still be passed explicitly. The four conditions of the conditional compromise are written into `run.md`'s authorization discipline and are the consumer's responsibility; delegate only checks the same worktree (repository root) and that the whole chain uses the same authorization file (sha256).
  - The check command may only come from a checkCommand or quickCheckCommand in the project configuration that the user approved; this is also written into the discipline.

Depends on: [run-result](SPEC-run-result.md) (result file). Source of the operator rule: `_SHELL_OPS` and `_check_config` in module-crew `module_crew/merge.py:24`, as quoted by mc-coord in agent-relay message #11736.

## Impact

- **Authorization discipline (additions only):** today `run.md` and routing say "`--write` may be added only when the user explicitly asks in the current turn; saying 'continue' does not escalate write permission automatically". An exception is added: when the four conditions below are met and `--authorized-by` is given, the write is treated as authorized for this turn. The rest of the original rule is unchanged, and `run.write: "explicit"` is unchanged. The routing spec and the `delegate-routing` skill each get one sentence pointing here.
- **Execution outside the sandbox:** the `--check` command is run by delegate outside the Codex sandbox with the user's permissions. This is the first time delegate runs a caller-supplied command outside the sandbox, so it accepts only an argument list, does not go through a shell, and its source is restricted by discipline.
- **Consistency with module-crew:** the operator rule is shared with module-crew. delegate must be neither stricter nor looser; to change it, send the change to mc-coord first, change both sides together, and have the user approve.
- **interface:** adds `run.check` and `run.writeAuthorization`.

## Tech stack and commands

Same as [run-result](SPEC-run-result.md); one new test file:

```bash
python3 -B plugins/delegate/tests/test-run-check.py
```

## Project structure

```text
plugins/delegate/scripts/run_check.py           → new: check command validation (copied from S30), execution through run_codex.py, taking the last 40 lines
plugins/delegate/scripts/run_state.py           → state file records authorization; the authorization file is checked on resume
plugins/delegate/scripts/codex-exec.sh          → --check runs after Codex ends and before the Git acceptance block; --authorized-by validation and recording
plugins/delegate/scripts/delegate_backend.py    → parse and forward the two options, validate combinations
plugins/delegate/scripts/delegate_capabilities.py → codex gains the check and writeAuthorization capability facts
plugins/delegate/interface.json                 → run.check, run.writeAuthorization
plugins/delegate/commands/run.md / help.md      → usage and authorization discipline
plugins/delegate/skills/delegate-routing/SKILL.md → one sentence for the write-authorization exception
plugins/delegate/tests/test-run-check.py        → new: stub tests
plugins/delegate/tests/test-interface.py        → add two assertions
spec/run-check.md / docs/en/SPEC-run-check.md   → this contract
spec/routing.md and its English page            → pointer sentence
README (Chinese and English), pending release notes → in sync
```

## Behavior contract

### `--check`

**Syntax:** `run … --check "<command>" -- "<task>"`, usable with a plain run, `--resumable`, `--resume` and `--continue`, given at most once.

**Validation (while parsing arguments, before calling Codex):** exactly the same as module-crew S30:

```python
_SHELL_OPS = ("&&", "||", ";", "|", ">", "<", "`", "$(")
argv = shlex.split(command)          # POSIX mode
bad = next((t for t in argv if t.startswith(_SHELL_OPS) or t.endswith(_SHELL_OPS)), None)
```

On refusal it exits 64 without calling Codex, and stderr carries only the line below, **character for character**, with no `delegate: ` in front. The messages are literal program output that must match module-crew byte for byte, so they stay in Chinese; the English glosses are for readers of this page only:

| Case | Message (verbatim) | Gloss |
|---|---|---|
| cannot be split (`ValueError`) | `检查命令拆不开：{异常信息}` | "The check command cannot be split: {exception message}" |
| the split gives an empty list | `检查命令不能为空` | "The check command must not be empty" |
| a token starts or ends with an operator | `检查命令里有 shell 运算符（「{token}」）：module-crew 不经 shell 执行检查命令，运算符会被当成普通参数。改用两种写法之一：把这些步骤写进项目脚本，检查命令写这个脚本；或写成 /bin/sh -c '<原命令>'` | "The check command contains a shell operator ('{token}'): module-crew does not run check commands through a shell, so the operator would be treated as an ordinary argument. Use one of two forms: put these steps in a project script and give that script as the check command; or write it as /bin/sh -c '<original command>'" |

The boundaries that follow are copied, not redefined: an operator in the middle of a token is not blocked (`foo&&bar`, `a|b`); a whole quoted string counts as one token, so `/bin/sh -c 'make test && make lint'` passes; a lone `&`, `$VAR` and `2>&1` are not blocked; `>file` is blocked. The constant in `run_check.py` carries a comment stating its source and "changes go to mc-coord first".

**When it runs:** after Codex ends and the status is classified, before the Git acceptance block. It runs only when this run's status is `done` (exit code 0); in every other status (`needs-input`, `timeout`, `unmarked`, failure, interruption, empty answer) it does not run and is recorded as `skipped`.

**How it runs:**

- It reuses 0.7.1's `run_codex.py` as the executor: `python3 -B run_codex.py --report <runId>.check.cleanup 600 <argv…>`. It uses `Popen` with the argument list, does not go through a shell, puts the process in a new session, and on deadline or interruption reaps descendants as in S41; when the direct child cannot be reaped it exits 125.
- The working directory is the repository root (`git rev-parse --show-toplevel`); stdin is `/dev/null`; the environment is that of delegate itself, without Codex's environment (`DELEGATE_REVIEW_DEPTH` and so on).
- stdout and stderr are merged into `<runId>.check.log`; the last 40 lines are taken, at most 16 KiB. `.check.log` and `.check.cleanup` count as log-type files and are cleaned by the 50-set rule.
- The deadline is 600 seconds, defined as a constant in one place.

**The result file** gains:

```json
"check": {"command": "<original text>", "argv": ["…"], "status": "passed", "exitCode": 0,
          "durationSeconds": 12.4, "tail": "…"}
```

`status` is one of the following and is an open set:

- `passed`: exit code 0;
- `failed`: any other exit code;
- `timeout`: the deadline was exceeded (`run_codex.py` exited 124);
- `cannot-run`: failure to start (`run_codex.py` reports 「无法启动」, "cannot start", and exits 127), or the check command itself exits 126 or 127;
- `unreaped`: `run_codex.py` exited 125 and the check process could not be reaped; `check.cleanup` carries the original lines of `.check.cleanup`;
- `skipped`: the run did not end as `done`; in this case there are only the three fields `command`, `argv` and `status`.

**Output:** the metadata block gains one line `检查：<通过|失败（退出 N）|超时|跑不起来|未能回收|跳过>` (literal output; gloss: "check: <passed | failed (exit N) | timed out | cannot run | could not be reaped | skipped>"). The run's own status and exit code are **not affected by the check result**, and the result line is unchanged. A consumer looks at `check.status` and decides for itself.

### `--authorized-by`

**Syntax:** `run --write --authorized-by <file> …`, usable with a plain run, `--resumable`, `--resume` and `--continue` that use `--write`.

**Validation (before calling Codex, exit 64, stderr `delegate: <reason>`):**

| Reason | When |
|---|---|
| `--authorized-by requires --write` | there is no `--write` |
| `authorization file not usable` | the path does not exist, or is a symlink (by `lstat`), or is not a regular file, or cannot be read, or its size is 0, or it exceeds 64 KiB |
| `authorization mismatch` | on a resume or continue, the chain's state file already records an authorization file and this call gives none, or the file given now has a different sha256 from the recorded one |

**Recording:**

- The result file gains `"authorization": {"source": "file", "path": "<absolute path>", "sha256": "…", "bytes": N}`.
- In write mode without `--authorized-by` it is recorded as `{"source": "in-turn"}`, meaning the caller claims the user explicitly asked for writing in the current turn.
- A read-only run records `null`.
- The state file of a resumable chain records `authorization` (`path`, `sha256`) for later rounds to check. If the first round of a chain had no authorization file and a later round adds one, checking against it starts from that round.
- The metadata block gains one line `写入授权：文件 <路径>（sha256 <前 12 位>）` or `写入授权：当轮` (literal output; gloss: "write authorization: file <path> (sha256 <first 12 characters>)" or "write authorization: this turn").

delegate neither reads nor interprets the content of the authorization file; it only computes the sha256. Checking "the same worktree" relies on the existing repository-root comparison (`repository mismatch`).

### Authorization discipline (written into `run.md`; the routing skill gets one sentence pointing here)

When all four conditions below hold, the caller need not wait for the user to speak in the current turn and may pass `--write --authorized-by <file>`:

1. The user's own words from when the outsourcing switch was turned on have been recorded as this file by the consumer (module-crew);
2. This module's Spec and Plan are approved, and the dispatched Task is within the approved Plan;
3. The same module and the same worktree;
4. delegate writes the authorization source into every result, that is, the `authorization` field above, and the caller must not delete or rewrite it.

If any condition fails, fall back to the original rule: add `--write` only when the user explicitly asks in the current turn. delegate can only check the repository part of condition 3 and that the file is consistent; the rest is up to the caller. This is discipline at the command-instruction level, not a technical lock.

The `--check` command may only be taken from a checkCommand or quickCheckCommand in the project configuration that the user approved, and may not be written on the fly by Codex, the calling model or a module session. delegate cannot verify the source, so this too is discipline.

### Interface (this module's part)

`run` gains:

```json
"check": {"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600,
          "operators": ["&&", "||", ";", "|", ">", "<", "`", "$("], "match": "token-prefix-or-suffix"},
"writeAuthorization": {"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization",
                       "verifies": ["file-sha256-across-chain", "repository"]}
```

`run.write` is still `"explicit"`. Consumers check `>=1.3,<2.0` and that the fields exist.

## Code style

Same as [run-result](SPEC-run-result.md). The operator constant and the judgment are copied from module-crew's code:

```python
_SHELL_OPS = ("&&", "||", ";", "|", ">", "<", "`", "$(")   # S38, copied from module-crew S30 (merge.py:24); change via mc-coord
```

## Testing strategy

`test-run-check.py` (`unittest`, its own fake codex, temporary Git fixtures) covers:

- **Validation:** cannot be split, empty, and each operator appearing at the start and at the end of a token; for these cases the refusal text is compared character by character (identical to the original in #11736), exit 64, Codex not called. Boundaries that pass: `foo&&bar`, `/bin/sh -c 'a && b'`, `2>&1`, a lone `&`, `$VAR`.
- **Execution:** executed through `run_codex.py`, as an argument list, not through a shell (a `*` and the like in the command is not expanded), working directory is the repository root, stdin empty; `passed`, `failed`, `timeout` (shortened deadline), `cannot-run` (a nonexistent program, 126, 127), `unreaped` (the stub executor exits 125), `skipped` (`needs-input`, `timeout`, failure); the last 40 lines and the 16 KiB truncation; the run's exit code and result line are not affected by the check result; it runs before the Git acceptance block.
- **Authorization:** every row of the refusal table; `source: file`, `in-turn`, and `null` for read-only; sha256 checking along the chain (the same passes, a different or missing one is refused, and after one is added midway the new one is checked).
- `test-interface.py` adds two assertions. Write the tests first and confirm they fail before implementing.

## Boundaries

- **Always:** the operator rule matches module-crew character for character, guarded by tests; the check does not go through a shell; `run.write` is still `"explicit"`; keep Chinese and English contracts in sync.
- **Ask first:** changing the operator list or the way of judging (send to mc-coord first); letting the check result affect the run status; running the check in a status other than `done`; reading the content of the authorization file; the paid measurement, commits, pushes and releases.
- **Never:** run the check command through a shell; accept a check command produced by Codex; accept `--authorized-by` without `--write`; write the content of the authorization file into the result file.

## Success criteria and verification map

- **CK-01:** the three refusal messages are character-for-character identical, exit 64, Codex not called (stub tests).
- **CK-02:** each copied boundary passes or is blocked accordingly (stub tests).
- **CK-03:** the check runs only on `done`, as an argument list, not through a shell, in the repository root, with empty stdin, before the Git acceptance block (stub tests).
- **CK-04:** the six `check.status` values and the truncation rules are correct; the run status and exit code are not affected (stub tests).
- **CK-05:** every row of the `--authorized-by` refusal table exits 64; the three values of the `authorization` field are correct (stub tests).
- **CK-06:** the authorization file's sha256 is checked along the chain (stub tests).
- **CK-07:** `interface.json` contains `run.check` and `run.writeAuthorization`, and `run.write` is still `"explicit"`; both plugin validate runs pass.
- **CK-08:** the four authorization-discipline points in `run.md`, the check-command source discipline, the pointer sentences in the routing spec and skill, `help.md`, both READMEs, both contracts and the pending release notes are in sync.
- **CK-09:** full validation, both plugin validate runs and `git diff --check` pass.

## Open questions

- The refusal message says "module-crew does not run check commands through a shell", which reads with the wrong subject inside delegate. As required it is copied character for character; changing it requires module-crew to change it too and the user to approve.
- Whether a 600-second check deadline is enough for a full test run is unknown, with no data; module-crew's default is 1800 seconds. Whether to add `--check-timeout` is left for after the pilot (Ask first).
