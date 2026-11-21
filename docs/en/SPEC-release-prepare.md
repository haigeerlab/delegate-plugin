# Specification: release-prepare (release preparation up to "only your go-ahead is missing")

[简体中文](../../spec/release-prepare.md) | English

Drafted 2026-11-21. Source: ecosystem ledger S101 r3 (plugin-ecosystem repository, `research/2026-11-21-合并之后的接管梳理.md`, commit dd6c6d3, sections 1, 3 and 4), forwarded by ecosystem-lead (#21885, from autopr-design #21882), stating the user approved r3 in the user's words 「按推荐批准」 — "approved as recommended". On 2026-11-21 the user took the request on in this session and set its schedule (「接，排在后面」 — "Take it, schedule it later"), confirmed the requirement summary with Q1–Q4 as recommended (「都按推荐」 — "all as recommended"), and the same day approved this spec: 「批准」 — "Approved". The calling convention was agreed with autopr-design (#21966, #21967). The Chinese page is the contract of record; this page mirrors it.

## Why

autopilot's "plugin" template needs to call delegate's release steps. The repository has no release script today; v0.8.x through v0.10.0 were all prepared by hand: bump the version, write release notes, update links and test counts, run the checks. delegate is one of the four plugins the pipeline itself uses, so under option A in section 4 of that document it goes no further than "prepared, awaiting approval" (r3's `prepare` level): the AI finishes all preparation and stops where only the user's go-ahead is missing; release and local upgrade stay with a person.

## Assumptions

Confirmed by the user on 2026-11-21 ("all as recommended"):

- **A1 Prepared, awaiting approval.** On a new local release branch, prepare the version, commit once, run every free check, and print a summary with the impact, the check results and the commands a person must run; none of those commands is executed.
- **A2 Mechanics for the script, prose for the session.** Moving content, updating links and test counts is the script's job; prose such as the motivation and the impact is written beforehand by the calling AI session in the unreleased notes, and the script only checks it is there.
- **A3 Stop on failure.** Any failed precondition or check reports a fixed diagnostic, exits non-zero and leaves no partial commit.
- **A4 Repository script.** It lives in the repository root `scripts/` and is not shipped as a plugin command.
- **A5 Local only.** No push, PR, tag or merge, and no changes to the local installation, `~/.claude` or `~/.codex`; autopilot's orchestration pushes and opens PRs under a bot identity separately (third batch).
- **A6 One module**, no usage draft needed.

Constraints from autopr-design #21967 (adopted):

- **A7 Unattended.** No standard input, no confirmation prompts; `--check` only checks and writes nothing. Exit 0 = prepared (with `--check`, "would be prepared"); non-zero = stop for a person, with the reason in the JSON.
- **A8 No second commit on a rerun for the same version.** Either reuse the existing release commit or refuse explicitly.
- **A9 Output usable as evidence.** The JSON carries `schema` (`delegate.release-prepare/v1`), the base commit SHA and the release commit SHA; every check lists its command and exit code; every "command for a person" has one sentence on why a person must run it.

Proposed by this spec and confirmed at review:

- **A10 Fixed shape of the unreleased notes.** After the "recorded in…" paragraph, the Chinese `docs/releases/unreleased.md` and its English page must contain: one line `<!-- release-title: <title> -->`; this release's change sections (`## …`, one or more); `## 影响面` (English `## Impact`); `## 验证与已知限制` (English `## Validation and known limitations`). Any missing item reports `release_notes_incomplete`. The script moves these into `v<X>.md` unchanged, appends one sentence with the measured test counts to the validation section, adds the fixed `## 更新` / `## Update` section, and folds the unreleased notes back to one paragraph.
- **A11 Base must be the latest main.** The worktree is clean and `HEAD` equals the locally recorded `origin/main` (the script never goes online or fetches; the caller fetches first); otherwise `base_not_main` or `worktree_dirty`. The release branch is always `release/v<X>`, cut from the base.
- **A12 Version rules.** `<version>` looks like `X.Y.Z`, is greater than the current `plugin.json` version, and tag `v<X>` does not exist locally; otherwise `version_invalid`, `version_not_newer` or `tag_exists`.
- **A13 Rerun rule.** When `release/v<X>` exists: if it is exactly one commit ahead of the base and that commit's message carries the trailer `Release-Prepare: v<X>`, reuse it (no new commit, rerun the checks, report the same release commit SHA); otherwise `release_branch_conflict`.
- **A14 Cleanup on failure.** If checks fail after a new branch was created: discard this run's changes, switch back to the original branch and delete the newly created `release/v<X>`; the release commit SHA in the output is `null`. If checks fail on a reused branch: keep the branch and only report the failure.
- **A15 Checks.** `scripts/validate.sh` (Python test count taken from its output), `claude plugin validate .`, `claude plugin validate ./plugins/delegate`, `git diff --check`, and spec-guard's `verify-artifacts.sh` (path resolved from Claude's installed plugin record, never a hard-coded version). A command that cannot be found reports `check_unavailable` and counts as a failure.
- **A16 Interface change.** Compare the `interface.json` version in the latest version tag (the last `v*` by version order) with the current one and put both numbers in the JSON; no compatibility judgment.
- **A17 Testing.** Logic lives in `scripts/release_prepare.py`, with `.sh` as the entry only; free tests use disposable git repositories and fake check commands and never run `validate.sh` recursively. A real end-to-end run happens once at delivery acceptance, on a disposable clone, without pushing, and the clone is deleted afterwards.

Dependency: [integration-interface](SPEC-integration-interface.md) (the version in `interface.json`).

## Command

```text
scripts/release-prepare.sh <version> [--check]
```

- Only these two arguments; too many, too few or a bad format report `usage_invalid` with exit 64. Standard input is connected to `/dev/null`.
- Standard output carries one JSON document only (UTF-8, indent 2); progress logs go to standard error.
- Exit codes: 0 prepared; 1 stopped for a person (see `reason`); 64 argument error.

## Steps

1. Preconditions: arguments, version rules (A12), base (A11), unreleased notes shape (A10), and every anchor to be rewritten is found (otherwise `release_docs_anchor_missing`).
2. `--check`: perform step 3's rewrites in memory to confirm they can be done; run step 4's checks (read-only); no branch, no file writes, no commit.
3. Rewrite (not `--check`): cut `release/v<X>`; bump `plugin.json`; generate the Chinese and English `v<X>.md`; fold both unreleased notes; update the current-release links, release lists and release validation numbers in both READMEs, documentation indexes and contributing guides (the Python count is step 4's measured value; the loop suite count is read from `validate.sh`).
4. Checks (A15): run on the rewritten worktree; commit only if all pass.
5. Commit: one commit, message `chore: 准备 v<X> 发行` with a body and the trailer `Release-Prepare: v<X>`; print the JSON.

## Output

```json
{
  "schema": "delegate.release-prepare/v1",
  "mode": "prepare",
  "status": "ready",
  "reason": null,
  "version": {"before": "0.10.0", "after": "0.11.0"},
  "interface": {"last_release": "1.5", "now": "1.5"},
  "base": {"ref": "origin/main", "sha": "<40 hex>"},
  "release": {"branch": "release/v0.11.0", "sha": "<40 hex or null>", "reused": false},
  "notes": {"title": "…", "zh": "docs/releases/v0.11.0.md", "en": "docs/en/releases/v0.11.0.md"},
  "tests": {"python": 388, "loop_suites": 28},
  "checks": [{"name": "validate", "command": ["/bin/bash", "scripts/validate.sh"], "exit_code": 0}],
  "human_steps": [{"command": "…", "why": "…"}]
}
```

- `mode` is `prepare` or `check`; `status` is `ready` or `stopped`. With `stopped`, `reason` is a fixed diagnostic and `release.sha` is `null` (except on reuse per A13).
- `checks` lists every check actually run (checks not reached are omitted); commands are argument arrays with nothing beyond local paths.
- `human_steps` always has 7 entries, each with `why`: ① push `release/v<X>` and open a PR (remote write, done by orchestration or a person per A5); ② merge the PR (pipeline plugins release no further than `prepare`); ③ create and push an annotated tag on the merge commit; ④ `gh release create v<X> --verify-tag --notes-file docs/releases/v<X>.md`; ⑤ upgrade on the Claude Code side (affects every running session; the user orders it); ⑥ change `ref` in `~/.codex/config.toml` and upgrade on the Codex side (edits the user's global configuration); ⑦ reopen sessions and quit/reopen ChatGPT with ⌘Q (desktop actions). Commands ③ and ④ use the placeholder `<merge commit>`.

## Fixed diagnostics

`usage_invalid`, `version_invalid`, `version_not_newer`, `tag_exists`, `worktree_dirty`, `base_not_main`, `release_notes_incomplete`, `release_docs_anchor_missing`, `release_branch_conflict`, `check_unavailable`, `check_failed`. With `check_failed`, `checks` shows which check failed and its exit code.

## Stack and commands

A Bash 3.2 entry plus the Python 3 standard library; tests use `unittest`, disposable git repositories and fake check commands, with no network and no real model.

```bash
python3 -B scripts/tests/test-release-prepare.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
scripts/release-prepare.sh              → new: entry, stdin from /dev/null, calls Python
scripts/release_prepare.py              → new: preconditions, rewrites, checks, commit, JSON
scripts/tests/test-release-prepare.py   → new: disposable repositories and fake check commands
scripts/validate.sh                     → register the new test (syntax checks already cover the new scripts)
CONTRIBUTING.md, CONTRIBUTING.en.md     → new "Releasing" section: how to write the unreleased notes, how to run the script, the seven human steps
docs/releases/unreleased.md and English page → describe the A10 template (existing historical paragraphs untouched)
spec/release-prepare.md, docs/en/SPEC-release-prepare.md → this contract
```

## Code style

Keep the repository's style: 4-space indentation, standard library, fixed error codes only; git is always called with argument arrays, never through a shell, with interactive prompts off. Example (existing code in `plugins/delegate/scripts/review_context.py`):

```python
def git(repository, *arguments):
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
                   'GIT_OPTIONAL_LOCKS': '0', 'GIT_CONFIG_NOSYSTEM': '1',
                   'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_SYSTEM': '/dev/null',
                   'GIT_ATTR_NOSYSTEM': '1', 'GIT_LITERAL_PATHSPECS': '1',
                   'GIT_TERMINAL_PROMPT': '0'}
```

The difference: review must shield the user's global configuration, while the release script commits and needs the user's own commit identity and commit hooks, so it keeps only the argument arrays, `GIT_TERMINAL_PROMPT=0` and standard input from `/dev/null`, without shielding global configuration.

## Test strategy

Write the tests first and confirm they fail, then implement. Each disposable repository holds a reduced layout (`plugin.json`, `interface.json`, both unreleased notes, the anchor lines of the READMEs, contributing guides and documentation indexes); fake check commands return 0 or non-zero as needed and print a fake `Ran N tests`.

- **Arguments and preconditions:** at least one case per diagnostic; repository bytes unchanged before and after `--check` (including branches and refs in `.git`).
- **Rewrites:** version, both `v<X>.md` (title, moved sections, the appended test counts, `## Update`), folded unreleased notes, and every anchor rewrite match the expected text exactly.
- **Checks and commit:** with all checks passing, exactly one new commit with the trailer whose parent is the base; with any check failing, no new commit, `release/v<X>` deleted, back on the original branch.
- **Rerun:** a second run for the same version reuses the same commit SHA; a branch changed by someone else reports `release_branch_conflict`.
- **Output:** all JSON fields present, SHAs 40 hex characters, `human_steps` has 7 entries each with `why`; no standard input read (it completes even with a blocking stdin).
- **End to end (once at acceptance):** run with the real checks on a disposable clone of this repository, review the result, delete the clone, no push.

## Boundaries

- **Always:** unattended; write only this repository's worktree and local branches; keep both contracts and the contributing guides in sync.
- **Ask first:** adding any network access, push, PR, tag or other remote or irreversible action; changing the output `schema` version; changing the fixed shape of the unreleased notes; committing, pushing or releasing this module itself.
- **Never:** read standard input or prompt; touch `~/.claude`, `~/.codex` or the local installation; leave a release commit after a failed check; write the motivation or impact prose on the session's behalf.

## Success criteria and verification map

- **RP-01:** every fixed diagnostic triggers as described in "Fixed diagnostics", with the right exit code and `reason` (stub tests).
- **RP-02:** `--check` writes nothing (repository bytes and refs identical before and after) and exits 0 on success.
- **RP-03:** rewrites match the expected text exactly (A10, step 3).
- **RP-04:** with all checks passing, exactly one new commit with the trailer; on any failure, no commit, no branch, back on the original branch (A14).
- **RP-05:** a rerun for the same version reuses the commit, and a conflict is refused (A13).
- **RP-06:** the JSON matches "Output", `human_steps` has 7 entries each with `why`; no standard input is read.
- **RP-07:** the "Releasing" section in both contributing guides, the unreleased template description and both contracts are in sync.
- **RP-08:** full validation, both plugin validate runs and `git diff --check` pass; at acceptance, one end-to-end run on a disposable clone succeeds.

## Open questions

- None. Raise any change to the unreleased notes shape (A10) or the diagnostic list at spec review.

## Appendix: autopr-design's comments (#21967, verbatim in the Chinese page)

autopr-design agreed with all four points and added constraints from merged plan r3 and the safety kernel: an unattended entry `scripts/release-prepare.sh <version> [--check]` that reads no stdin and never prompts, `--check` writing nothing, exit 0 = prepared and non-zero = stop with the reason in the JSON, and no second commit on a rerun; JSON with `schema`, base SHA and release commit SHA, each check's command and exit code, and a reason for every human step; stopping at one commit on a local release branch, which is exactly r3's `prepare` level, with no `auto` follow-up needed for the four pipeline plugins; and no push, PR, local installation or `~/.codex` changes from the script, since autopilot's orchestration pushes and opens PRs under a bot identity (third batch) and local installation is a separate later step.
