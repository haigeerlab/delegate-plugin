# Contributing

[简体中文](CONTRIBUTING.md) | English

Thank you for helping improve delegate. Start with the [README](README.en.md), [Design and boundaries](docs/en/DESIGN.md), and the [current specifications](docs/en/README.md) for the affected module. Historical task records provide background and do not override current contracts.

## Reporting issues and suggesting changes

Search existing [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues) first. A new report should include:

- Claude Code, Codex CLI, Python, Bash, operating-system, and plugin versions;
- Installation method: remote marketplace, local path, or `--plugin-dir`;
- Minimal reproduction steps, expected and actual behavior, and exit status;
- Relevant `/delegate:doctor` diagnostics and necessary log excerpts;
- Git state for write-mode issues, including whether uncommitted changes existed beforehand.

Share only what is needed to reproduce the issue. Remove credentials, personal paths, proprietary source, and unrelated private material before submitting. Do not upload `auth.json`, API keys, full process logs, or machine identity paths from the cache.

## Development setup

See the [README prerequisites](README.en.md#prerequisites). Validate manifests from this repository's root:

```bash
claude plugin validate .
claude plugin validate ./plugins/delegate
```

Explicitly load the source plugin directory from a target Git project when developing:

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

An installed version number matching the source version does not prove that source content was loaded. See [Updates and uninstalling](README.en.md#updates-and-uninstalling) for remote caches, local paths, and reloading.

## Project AI and workflow conventions

Read [Development workflow and AI instructions](docs/en/development-workflow.md) before development. Codex uses project `AGENTS.md`; Claude Code uses project `CLAUDE.md`. Chinese specifications live in `spec/`, and module plans/tasks in `tasks/<id>/`. The [archive index](docs/archive/pre-spec-guard/README.md) preserves original records; do not execute them as active tasks.

## Changes and validation

Keep changes focused. For behavior changes, add a regression that reproduces the failure before fixing the implementation; do not weaken assertions to make tests pass. Update affected specifications and help text so documentation remains consistent with behavior.

Run the free offline validation from the **repository root**:

```bash
/bin/bash scripts/validate.sh
```

The entry point checks JSON/Python/Bash syntax, executable permissions, manifest required fields, evaluator self-tests, and registered shell product and Python regression suites. v0.11.0 release validation passed 432 Python, 53 shell and 19 eval cases (v0.10.0: 388 Python; v0.9.0: 354 Python; v0.8.6: 343 Python; v0.8.5: 333 Python; v0.8.4: 330 Python; v0.8.3, v0.8.2, v0.8.1 and v0.8.0: 328 Python; v0.7.1: 253 Python; v0.7.0: 247 Python; v0.6.0: 196 Python; v0.5.3: 173 Python; v0.5.2: 166 Python; v0.5.1: 162 Python; v0.5.0: 157 Python). The aggregate includes 28 loop-registered Python regression suites, source-discovery regression and isolation policy-only tests. Actual OS/host/live evidence is separate. The 52 product assertions and 17 Python regressions of v0.4.0 are a historical baseline only. The free aggregate entry point makes no model calls. The four doctor rule checks use run_doctor with this suite's controlled CLI, synthetic login state, and temporary log, rather than inheriting outer installation/authentication state. [Actual verification in Chinese](docs/verification/2026-10-08-f8-applied.md) passed the aggregate suite without an outer Codex CLI, and all 19 detection assertions passed both with no outer CLI and with an outer rejected login.

When changing source commands, the free suite also checks Codex 0.162.1's automatic migration size constraint: the generated skill's UTF-8 body and wrapper must total at most 4000 bytes. Oversized commands are skipped without failing installation. Keep entry points concise and detailed development records in documentation. This offline check does not replace actual installation or host usability acceptance.

Syntax discovery excludes only the root `.git` and ignored local `.agent/acceptance` artifacts, so private 0600 installation backups are not treated as executable source. Other `.agent` files, similar directory names, and product source remain checked. Private evidence is verified per batch; all product suites remain enabled. Run `python3 -B scripts/tests/test-validation-discovery.py` for isolated discovery regressions without model calls.

To isolate a failure, run individual suites:

```bash
/bin/bash plugins/delegate/tests/test-channel.sh
/bin/bash plugins/delegate/tests/test-detection.sh
/bin/bash plugins/delegate/tests/test-routing.sh
python3 -B plugins/delegate/tests/test-backend.py
python3 -B plugins/delegate/tests/test-channel-regressions.py
python3 -B plugins/delegate/tests/test-command-migration.py
/bin/bash evals/propose-not-auto.sh --scaffold-only
/bin/bash evals/routing-fitness.sh --scaffold-only
```

Free stubs verify deterministic invocation and process contracts; they do not prove real CLI sandbox or model behavior. The following commands **call models and consume quota**, are excluded from the aggregate validation, and should be run deliberately for a defined verification purpose:

```bash
/bin/bash plugins/delegate/tests/test-channel.sh --live
/bin/bash evals/propose-not-auto.sh
/bin/bash evals/routing-fitness.sh
```

Evaluations explicitly load source with `--plugin-dir`. Exit statuses are 0=PASS, 1=FAIL, and 2=NORUN. routing-fitness accepts only the complete first nonempty line `判断：委托` or `判断：自己做` (delegate or do it in the main session). A single `claude -p` turn cannot establish that interactive sessions always propose delegation when appropriate; global rules may also affect results. See the [routing specification](docs/en/SPEC-routing.md).

Keep Bash 3.2 compatibility: use `${VAR}`, guard empty arrays with `${ARR[@]+"${ARR[@]}"}`, and avoid `cmd | grep -q`. Run shell tests with `/bin/bash` to avoid zsh redirection differences.

## Maintaining bilingual documentation

- `README.md` and root design/specification documents remain Chinese. `README.en.md`, `CONTRIBUTING.en.md`, and `docs/en/` provide English counterparts.
- Correct Chinese facts and reading flow first, then synchronize English. Wording may suit each audience, but options, defaults, exit statuses, permissions, failure semantics, and verification scope must agree.
- Keep language switches in both directions for maintained documentation. English navigation should normally link to English counterparts. Clearly identify source and historical records available only in Chinese or their original language.
- Task examples may be translated. Preserve command names, options, environment variables, paths, and diagnostic or evaluation strings that require exact matching.
- Preserve historical facts and checkbox states, adding archive notices that point to current contracts. Do not rewrite an old design as though later behavior had already been implemented.

After editing documentation, check file links, heading anchors, and code fences, and run `git diff --check`. The [documentation index](docs/en/README.md) lists language pairs.

## Releasing

`scripts/release-prepare.sh` takes release preparation as far as "only your go-ahead is missing": one commit on a new local release branch, with no push, PR, tag or change to the local installation. The contract is in the [release-prepare specification](docs/en/SPEC-release-prepare.md).

**1. Write the unreleased notes first.** Each change adds content after the "recorded in…" paragraph of `docs/en/releases/unreleased.md` and its Chinese page. Before a release both must contain:

```text
<!-- release-title: Title of this release -->

(optional introduction)

## This release's change sections (one or more)

## Impact

## Validation and known limitations
```

The Chinese page uses `## 影响面` and `## 验证与已知限制`. A missing title line, change section or either of those two sections stops the script with `release_notes_incomplete`. The motivation, impact and validation prose is written by a person or the calling session; the script only moves it.

**2. Rehearse, then prepare.** Run `git fetch` first, then, in a clean worktree matching `origin/main`:

```bash
/bin/bash scripts/release-prepare.sh 0.11.0 --check
```

```bash
/bin/bash scripts/release-prepare.sh 0.11.0
```

`--check` only checks and writes nothing. A real run cuts `release/v<version>`, bumps the version, generates both release notes, folds the unreleased notes, updates the current-release links and release validation numbers in the READMEs, documentation indexes and this guide, then runs full validation, both `claude plugin validate` runs, `git diff --check` and spec-guard's `verify-artifacts`, and commits once. Full validation takes about 5 minutes; in Claude Code, run it in the background.

**3. Read the output.** Standard output is one JSON document (`schema` `delegate.release-prepare/v1`): only exit 0 with `status` `ready` means prepared; otherwise read `reason` (a fixed diagnostic) and which entry in `checks` failed with which exit code. When a check fails, the script deletes the release branch it created and returns to the original branch, leaving no commit; a rerun for the same version reuses the existing release commit, and a branch changed by someone else reports `release_branch_conflict`.

**4. The seven human steps.** The JSON `human_steps` lists each command with its reason: push and open a PR, merge, create an annotated tag on the merge commit, `gh release create --verify-tag`, upgrade on the Claude Code side, change `ref` and upgrade on the Codex side, reopen sessions and quit/reopen with ⌘Q. delegate is a plugin the pipeline itself uses, so all seven need the user's consent.

The script finds the sentences to rewrite by their exact wording (`anchors()` in `scripts/release_prepare.py`). When changing the current-release or release-validation sentences in the READMEs, documentation indexes or this guide, update that anchor table and `scripts/tests/test-release-prepare.py` too; on a mismatch the script stops with `release_docs_anchor_missing` instead of guessing.

## Submitting a pull request

Use a separate branch and submit a focused PR. Describe the concrete problem, resulting behavior or reading flow, validation performed, and its limitations. Behavior changes, documentation synchronization, and necessary tests can be reviewed together; avoid unrelated refactoring.

Check manifests and relevant validation before submission, and inspect the actual diff. A write-mode delegation can leave changes after either success or failure; the model's own account is not sufficient to verify correctness.

This project uses the [MIT License](LICENSE). Ensure contributions are compatible with it and retain required copyright and license notices for third-party material.
