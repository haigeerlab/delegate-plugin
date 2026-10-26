# Specification: write-trust (write mode does not persist project trust)

[简体中文](../../spec/write-trust.md) | English

Drafted 2026-10-26. Origin: S35 verification found that the first `/delegate:run --write` run in a repository makes Codex append `[projects."<path>"] trust_level = "trusted"` to the user's `~/.codex/config.toml`, contradicting the plugin's "changes no global configuration" statement. The direction the user gave through ecosystem lead ecosystem-lead (original words): "S36 修行为：只在用户配置里没有这个仓库的信任条目时，才用 -c 内联表临时覆盖，不再写入 ~/.codex/config.toml；补测那两项没验证的；在修好之前，先在 README 里照实写明现在的行为。" (fix the behavior: only when the user configuration has no trust entry for this repository, override temporarily with an inline `-c` table instead of writing `~/.codex/config.toml`; run the two unverified probes; until fixed, describe the current behavior truthfully in the README). The user approved the probes and the README step in this session.

Evidence:
- Research by the S35 sub-session (openai/codex `rust-v0.162.1` source plus free probes): the write happens only when a new thread starts, the merged configuration has no `trust_level` for the project, and the effective permissions allow writing cwd. An inline table `-c 'projects={"<root>"={trust_level="trusted"}}'` stops the write; the dotted form and `--ignore-user-config` do not.
- Follow-up probes in this session, [2026-10-26-delegate-s36-trust-followup-probe.md](../verification/2026-10-26-delegate-s36-trust-followup-probe.md): the inline override is **merged by key** and does not replace other user entries; inside a worktree Codex keys trust by the **main repository path**, and from a worktree subdirectory only an override keyed by the main repository path works.

## Assumptions (A1–A9, confirmed by the user on 2026-10-26)

- **A1** New module `write-trust`, depending on channel and run-resume (it changes the write-mode arguments in `codex-exec.sh` that both use). Their existing clauses are unchanged; each gains one pointer sentence.
- **A2** Only calls that run Codex under `workspace-write` are affected: plain `--write` runs, `--write --resumable`, and `--resume … --write`. Read-only runs, read-only resumes and Codex-backend reviews get no extra argument (they never write trust).
- **A3** By the source, `exec resume` does not write trust, but write-mode resumes still get the same override: today the first run persists trust, so a resume reads "trusted"; once nothing is persisted, a resume without the override would drop from "trusted" to "unset", which differs from today.
- **A4** Whether the user configuration has an entry for this repository is decided from one file only: `${CODEX_HOME:-$HOME/.codex}/config.toml`. A missing file means "no entry". System, managed and in-repository `.codex/config.toml` files are not read (see open questions).
- **A5** No TOML parser is introduced (local Python 3.10 has no `tomllib`; the plugin installs no dependencies). A conservative text check is used instead: if any candidate key appears in the file as a **whole quoted string** (`"<key>"` or `'<key>'`), treat it as an existing entry and add no override. TOML keys containing `/` must be quoted, so a real entry is always seen; a false match only biases toward "no override", i.e. today's behavior (Codex may write), never toward wider trust.
- **A6** Candidate keys follow Codex's lookup order: the start directory (physical path, plus the logical `$PWD` when it is the same directory) and the trust root. The trust root is the parent of `git rev-parse --path-format=absolute --git-common-dir`, provided that directory is named `.git`; otherwise (submodules, `--separate-git-dir`, bare and so on) the check is "uncertain". The override is keyed by this trust root.
- **A7** When the check is uncertain, no override is added, the run proceeds, one line is printed on stderr, and the exit code is unchanged. Uncertain means: the configuration file exists but cannot be read or is not UTF-8; a candidate key contains `"`, `\` or a control character; or the trust root cannot be determined.
- **A8** Trust entries already written to the user configuration are neither removed nor reported; the interface version, `interface.json` and exit codes are unchanged.
- **A9** Verification has three layers: stub tests (arguments and decisions); a free real-CLI check (real Codex, isolated `CODEX_HOME`, no credentials, rejected with 401, confirming the generated override stops the write); and one paid real `--write` run confirming the sha256 of the real `~/.codex/config.toml` is unchanged (gate, separately authorized).

## Stack and commands

Bash 3.2 wrapper, Python 3 standard library, Git ≥2.31 (`--path-format`), Codex CLI 0.162.1 (the locally verified version). No new dependencies, hooks or command entries.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-write-trust.py
python3 -B plugins/delegate/tests/test-run-resume.py
/bin/bash plugins/delegate/tests/test-channel.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/codex_trust.py      → new: candidate keys, trust root, text check; prints the -c value or a notice (stdlib)
plugins/delegate/scripts/codex-exec.sh       → write-mode runs and write-mode resumes add the override after APPROVAL
plugins/delegate/tests/test-write-trust.py   → new: unit tests + stub integration tests
plugins/delegate/README.md / README.en.md    → line 26 back to "changes no global configuration", with the uncertain-check exception
README.md / README.en.md                     → rewrite the paragraph added in S36 step 2 to describe the new behavior
spec/write-trust.md / docs/en/SPEC-write-trust.md → this contract
spec/channel.md, spec/run-resume.md and English pages → one pointer sentence each
spec/CAPABILITY-MAP.md / docs/en/capability-map.md → new row (English page synced)
docs/releases/unreleased.md and English page → unreleased notes
docs/verification/2026-10-26-delegate-s36-*  → free real-CLI check and paid verification records
```

## Behavior contract

### When the override is added

Write-mode calls run `codex_trust.py` before starting Codex:

| Situation | Result |
|---|---|
| Configuration file absent | add override |
| No candidate key appears as a whole quoted string | add override |
| Found (whether `trusted`, `untrusted`, or the same path elsewhere) | no override, no notice |
| Uncertain (A7) | no override, notice on stderr |

The argument added (keyed by the trust root, placed after `-c approval_policy="never"`):

```text
-c projects={"<trust root>"={trust_level="trusted"}}
```

The trust root has already been checked for `"`, `\` and control characters, so wrapping it in double quotes yields a valid TOML key.

### Notice text (stderr, one line)

```text
delegate: 未能确认 Codex 用户配置里有没有本仓库的信任条目（<原因>），本次不加临时信任；Codex 可能会往 <配置文件路径> 写入一条信任记录。
```

(Meaning: delegate could not confirm whether the Codex user configuration has a trust entry for this repository (reason), so no temporary trust is added this time; Codex may write a trust entry to the configuration file.) `<原因>` is one of `配置文件无法读取` (file unreadable), `配置文件不是 UTF-8` (not UTF-8), `仓库路径含引号、反斜杠或控制字符` (path contains a quote, backslash or control character), `无法确定 Git 信任根` (Git trust root unknown).

### Unchanged

- Runtime trust is the same as today: the first `--write` run today also trusts in memory before persisting, and later runs read the persisted `trusted`. Now trust is granted temporarily on every run and never persisted.
- When the user already has an entry (including `untrusted`), arguments are identical to today.
- Read-only runs, read-only resumes and Codex reviews keep exactly today's arguments.
- `codex_trust.py` only reads the configuration file: it never writes it, changes permissions or creates directories.

## Code style

Follow existing code: Bash 3.2 compatible, `${VAR}` variables, empty arrays expanded with the existing guard; Python standard library, 4-space indentation, snake_case, pure functions separate from the command-line entry (as in `run_state.py`). Existing example (`codex-exec.sh`):

```bash
# Never let a configured approver let a delegated run leave its sandbox.
APPROVAL=(-c 'approval_policy="never"')
```

## Test strategy

`test-write-trust.py` (`unittest`, temporary Git fixtures, `CODEX_HOME` pointing to a temporary directory, PATH pointing to a fake Codex that records argv). Write the tests first and see them fail, then implement.

- Unit: no configuration file; `trusted`/`untrusted` entries in table-header, dotted and inline-table forms; single-quoted keys; similar paths (`<root>-sub`, `<root>/sub/deeper`) do not match; paths containing `"`; non-UTF-8; unreadable; trust-root directory not named `.git`.
- Integration: `--write` runs from the root and a subdirectory of a plain repository and of a worktree all use the main repository path as the key; `--write --resumable` and `--resume … --write` carry the override; read-only runs and read-only resumes do not; an uncertain check prints the notice, keeps the exit code and adds no override; the configuration file bytes are unchanged before and after.
- Assertions in existing `test-channel.sh`, `test-run-resume.py` and `test-review-backends.py` are not changed.

**Free real-CLI check (report):** with the arguments generated by `codex_trust.py`, run real `codex exec --sandbox workspace-write` with an isolated `CODEX_HOME` and no credentials (rejected with 401) for four cases — plain repository root, plain repository subdirectory, worktree subdirectory, existing `untrusted` entry — and confirm none writes; the sha256 of the real `~/.codex/config.toml` is identical before and after.

**Paid verification (gate, separately authorized):** in a new temporary Git repository under the home directory that Codex has never used, run one real `--write` with the current source (minimal task: write one file) and confirm the file is written and the sha256 of the real `~/.codex/config.toml` is unchanged.

## Boundaries

- **Always:** read configuration only; fall back to today's behavior with a notice when uncertain; never override an existing user entry; keep Chinese and English contracts in sync.
- **Ask first:** removing or rewriting existing user trust entries; reading system or managed configuration; adding a TOML parsing dependency; changing read-only arguments; paid verification, commits, pushes, releases.
- **Never:** write `~/.codex/config.toml` or any file under `CODEX_HOME`; raise a repository the user marked `untrusted` to `trusted`; use `--ignore-user-config` or the dotted form; change the interface version or `interface.json`.

## Success criteria and verification mapping

- **WT-01:** Write-mode runs carry the override when there is no entry, keyed by the trust root (plain repositories and worktrees, root and subdirectory) (stub tests).
- **WT-02:** With a quoted entry for any candidate key, no override is added and arguments match the pre-change ones (stub tests).
- **WT-03:** Each of the four uncertain reasons prints one notice line, adds no override and keeps the exit code (stub tests).
- **WT-04:** Write-mode resumable runs and write-mode resumes carry the override; read-only runs, read-only resumes and Codex reviews keep their arguments (stub tests).
- **WT-05:** The configuration file bytes are unchanged before and after a run (stub tests).
- **WT-06:** The free real-CLI check shows no write in all four cases, and the real configuration sha256 is unchanged (report).
- **WT-07:** Paid verification shows the real configuration sha256 unchanged (gate; marked "not verified" without authorization).
- **WT-08:** Chinese and English READMEs, contracts, pointer sentences and unreleased notes are in sync, and the README no longer says "`--write` currently changes Codex's user configuration".
- **WT-09:** Full validation, both plugin validations and `git diff --check` pass; existing test assertions are unchanged.

## Open questions

- Precedence between `-c` and the user configuration on the same key is not verified; this module never adds an override on a key the user already has, so it does not depend on it.
- `projects` entries in Codex's system configuration (such as `/etc/codex/config.toml`), managed configuration or project-level configuration are invisible to this module, which could temporarily raise a repository marked `untrusted` there to `trusted`. Whether to scan those files is undecided (scanning would only be more conservative).
- Symlinked paths: candidate keys include the physical path and the logical `$PWD`, but how Codex itself normalizes paths is not verified.
- Listing trust entries possibly left by earlier delegate versions in `/delegate:doctor` is out of scope.
- S35 (run-timeout) changes the same `codex-exec.sh`, README and capability-map lines; delegate-owner coordinates the order before implementation.
