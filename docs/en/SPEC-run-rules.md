# Specification: run-rules (`--rules-file`, a rules fragment for this delegation only)

[简体中文](../../spec/run-rules.md) | English

Drafted 2026-10-27; approved by the user on 2026-10-27, in the user's words: 「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」 — "Approve the five Specs run-result, run-continue, run-longrun, run-check and run-rules, and start the English pages and the Plan." It corresponds to item 9 of ecosystem proposal S38 (full text and the user's words in [run-result](SPEC-run-result.md)). The proposal's original text (in Chinese): "`--rules-file`: the fragment is placed as is after delegate's preamble, and on conflict the fragment wins (except for safety boundaries). Whether Codex reads AGENTS.md under a worktree must be measured."

## Premises (confirmed by the user on 2026-10-27; the ones this module uses)

- **S13** `--rules-file <file>`:
  - The content is placed as is after delegate's preamble and before the task, preceded by 【项目规则（本次委托专用）】 ("Project rules (for this delegation only)"), with a note that on conflict this section wins, except for the safety boundaries: the sandbox, no commit and no push, and the first-line marker.
  - UTF-8, at most 16 KiB, otherwise exit 64.
  - AGENTS.md is read by Codex itself; delegate neither reads nor splices it; the fragment holds only rules outside AGENTS.md that are specific to this one delegation.
  - The path and sha256 are written into the result file.
  - `--continue` and `--resume` may pass it again, in which case it is placed once more in that round's prompt.

Depends on: [run-result](SPEC-run-result.md) (result file; the end-marker paragraph of `--strict`).

## Measurement basis

Measurements T3 and T4 of the [S38 pre-measurements](../verification/2026-10-27-delegate-s38-probe.md): under a git worktree, Codex automatically reads the AGENTS.md at that worktree's root and follows it, and this AGENTS.md can change the answer format a delegate task asks for (the task asked for two lines, and the answer had a third line with a code word). Hence:

- Rules already in the project's AGENTS.md are read by Codex anyway, so `--rules-file` need not repeat them;
- if AGENTS.md demands "write such-and-such on the first line", it may crowd out `NEED_USER:` / `TIME_UP:` / `DONE:`. This is covered by run-result's `--strict` (a missing marker is judged `unmarked`), and this module stresses once more in the rules paragraph that the first-line marker must not change.

## Impact

- **Prompt (additions only):** the prompt gains a paragraph only with `--rules-file`; without it the prompt is completely unchanged.
- **interface:** adds `run.rules`. This module is the last of the five, so once it is written the capability markers of 1.3 are complete; see the summary at the end.

## Tech stack and commands

Same as [run-result](SPEC-run-result.md); one new test file:

```bash
python3 -B plugins/delegate/tests/test-run-rules.py
```

## Project structure

```text
plugins/delegate/scripts/codex-exec.sh          → read and validate the rules file, splice it into the prompt
plugins/delegate/scripts/delegate_backend.py    → parse and forward --rules-file
plugins/delegate/scripts/delegate_capabilities.py → codex gains the rules capability fact
plugins/delegate/interface.json                 → run.rules
plugins/delegate/commands/run.md / help.md      → usage and positioning
plugins/delegate/tests/test-run-rules.py        → new: stub tests
plugins/delegate/tests/test-interface.py        → add run.rules assertions and the 1.3 summary assertion
spec/run-rules.md / docs/en/SPEC-run-rules.md   → this contract
README (Chinese and English), pending release notes → in sync
```

## Behavior contract

### Syntax and validation

`run … --rules-file <file> -- "<task>"`, usable with a plain run, `--resumable`, `--resume` and `--continue`, given at most once. It is validated before Codex is called; on failure it exits 64 with stderr `delegate: rules file not usable`, and the specific reason on a separate line:

- the path does not exist, is a symlink (by `lstat`) or is not a regular file;
- it cannot be read;
- it is empty, or empty after stripping whitespace;
- it exceeds 16 KiB;
- it is not valid UTF-8;
- it contains a NUL character.

### Where it goes

For a plain run and a resumable run the prompt order is: preamble (non-interactive delegation or resumable delegation) → **rules paragraph** → task text → end-marker paragraph (`--strict`) → time-budget paragraph.

For `--resume` and `--continue` the order is: **rules paragraph** → 【用户答复】 ("User answer") or 【下一个任务】 ("Next task") → end-marker paragraph → time-budget paragraph.

The wrap-up round's prompt is fixed and has no rules paragraph.

The rules paragraph reads:

> [Project rules (for this delegation only)] The following rules are provided by the caller and apply only to this delegation; where they conflict with the text above, this section wins. But the following cannot be changed by this section: the sandbox restrictions; no commits and no pushes; the marker on the first line of the final answer (`NEED_USER:`, `TIME_UP:`, and `DONE:` when it is required).
>
> <file content verbatim>
>
> [End of project rules]

The file content is inserted verbatim, with no escaping and no truncation. If it lacks a trailing newline, one is added.

### Relationship with AGENTS.md (written into `run.md`)

- Codex itself reads the AGENTS.md at the root of the worktree that contains the working directory (measurement T3); delegate does not read, splice or check AGENTS.md.
- `--rules-file` holds only rules outside AGENTS.md that are specific to this one delegation, for example the acceptance criteria of this Task or a temporary convention of this module. The project's long-term rules belong in AGENTS.md.
- When the two conflict, there is no mechanism guaranteeing whom Codex actually obeys; the wording of the rules paragraph can only raise priority. If a reliable end marker is needed, also use `--strict`.

### Result

The result file gains `"rules": {"path": "<absolute path>", "sha256": "…", "bytes": N}`, absent when `--rules-file` is not given. The rules text itself is not written into the result file.

### Interface (this module's part)

`run` gains:

```json
"rules": {"option": "--rules-file", "maxBytes": 16384, "placement": "after-preamble",
          "projectInstructions": "codex-reads-agents-md"}
```

### The complete 1.3 shape (after all five modules)

```json
{
  "interface": "1.3",
  "review": {
    "command": "/delegate:review",
    "backends": ["codex", "claude-code"],
    "readOnly": true,
    "report": {"schemaVersion": 1}
  },
  "run": {
    "command": "/delegate:run", "backends": ["codex"], "write": "explicit",
    "resume": {"optIn": "--resumable", "option": "--resume", "backends": ["codex"],
               "statuses": ["done", "needs-input", "timeout"]},
    "timeout": {"status": "timeout", "exitCode": 124},
    "result": {"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict",
               "statuses": ["done", "needs-input", "timeout", "unmarked", "failed", "interrupted", "unreaped", "empty"]},
    "usage": {"in": "result.usage", "cumulative": "session", "perRun": "run"},
    "continue": {"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable",
                 "stateRetentionDays": 14},
    "longRun": {"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540,
                "background": "caller"},
    "check": {"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600,
              "operators": ["&&", "||", ";", "|", ">", "<", "`", "$("], "match": "token-prefix-or-suffix"},
    "writeAuthorization": {"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization",
                           "verifies": ["file-sha256-across-chain", "repository"]},
    "rules": {"option": "--rules-file", "maxBytes": 16384, "placement": "after-preamble",
              "projectInstructions": "codex-reads-agents-md"}
  },
  "doctor": {"command": "/delegate:doctor"}
}
```

Mapping between the proposal's capability markers and the fields: `run.result` → `run.result`; `run.usage` → `run.usage`; `run.continue` → `run.continue`; `run.longRun` → `run.longRun`; `run.check` (`shell: false`) → `run.check.shell`; `run.writeAuthorization` → `run.writeAuthorization`; `run.rules` → `run.rules`. 1.4's `run.restore`, `run.concurrent` and `doctor.quota` are not in 1.3.

## 1.3 combined measurement (paid, gate, separately authorized)

Once all five modules are done, run one paid measurement for all of them together, not separately in each module. In a temporary repository under the home directory, use a real model to walk one complete chain:

1. Start with `--resumable --strict --rules-file`;
2. Continue one round with `--continue --write --authorized-by --check`;
3. One round of `--timeout` (background mode).

Items to confirm:

- the result file's fields match the real events;
- `usage.run` takes the difference correctly;
- whether the first-line marker survives when the rules paragraph and AGENTS.md both exist;
- `--check` runs in a real working tree.

The number of runs and the cap are proposed separately at that time and the run goes ahead only after authorization.

## Code style

Same as [run-result](SPEC-run-result.md).

## Testing strategy

`test-run-rules.py` (`unittest`, its own fake codex) covers:

- every item of the refusal table exits 64 without calling Codex;
- in the four kinds of call (plain, resumable, resume, continue) the position of the rules paragraph and its text are byte-for-byte correct;
- the wrap-up round has no rules paragraph;
- without `--rules-file` the prompt is identical to before the change;
- the result file has the `rules` field and does not contain the rules text.

`test-interface.py` adds `run.rules` assertions and asserts the complete field set of 1.3 (the summary above). Write the tests first and confirm they fail before implementing.

## Boundaries

- **Always:** without `--rules-file` the prompt is unchanged; the rules paragraph states the safety boundaries that cannot be changed; keep Chinese and English contracts in sync.
- **Ask first:** reading or splicing AGENTS.md; relaxing the 16 KiB limit; letting the rules paragraph change the safety boundaries; the paid measurement, commits, pushes and releases.
- **Never:** modify, escape or truncate the rules text; write the rules text into the result file; put a rules paragraph in the wrap-up round.

## Success criteria and verification map

- **RU-01:** every item of the refusal table exits 64 without calling Codex (stub tests).
- **RU-02:** the position and byte-for-byte text of the rules paragraph are correct in the four kinds of call, the wrap-up round has no rules paragraph, and the prompt is unchanged without the option (stub tests).
- **RU-03:** the result file has `rules` (path, sha256, byte count) and not the text (stub tests).
- **RU-04:** `interface.json` is the complete 1.3, with fields consistent with the summary; existing fields are unchanged; both plugin validate runs pass.
- **RU-05:** `run.md` (relationship with AGENTS.md), `help.md`, both READMEs, both contracts and the pending release notes are in sync.
- **RU-06:** full validation, both plugin validate runs and `git diff --check` pass.
- **RU-07 (paid, gate, separately authorized):** the 1.3 combined measurement, with the result recorded in a verification record; anything that does not hold goes back to the spec of the corresponding module.

## Open questions

- Whom Codex obeys when the rules paragraph and AGENTS.md conflict can only be observed by measurement (RU-07) and cannot be guaranteed.
- The 16 KiB limit is an estimate; when it is exceeded, the advice is to put the content in AGENTS.md.
