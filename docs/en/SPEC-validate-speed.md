# Specification: validate-speed (faster free full validation)

[简体中文](../../spec/validate-speed.md) | English

Drafted 2026-11-25. Source: ecosystem-lead #22978 ("delegate test speedup", stating the user's words 「对，按这个发」 — "Yes, send it like this") and #22983 (standard v1.7.3, C2: quick check and a ceiling on full-run time). On 2026-11-25 the user said in this session 「先升钉再提速」 — "pin first, then speed up" — and after the pin (PR #53) merged, 「写提速 Spec」 — "write the speedup spec". The same day the user approved this spec: 「批准；Q1 A；Q2 A」 — "Approved; Q1 A; Q2 A". The revisions after acceptance and review (A8 change set and dependency expansion, rules 1 and 3, the A9 waiting approach) were re-reviewed by the user the same day: 「批准修订，本地提交」 — "Revision approved, commit locally". The Chinese page is the contract of record; this page mirrors it.

## Why

Every change made the session wait for the full `scripts/validate.sh` run. ecosystem-lead measured on main 941304c: 37 suites totalling about 505 seconds serially; the slowest were `test-run-timeout.py` at about 90 seconds (really waiting for timeouts) and `test-channel-regressions.py` at about 61 seconds (several real `sleep(3.2)` calls). CI rows: `macos-system` 12 min 3 s, `3.13` 8 min 48 s (PR #53, run 45593474833). There was no quick check that runs only the tests a change touches.

Local baseline (measured in this session on main 1575e4e, 8 cores): see "Baseline".

## Premises (confirmed by the user on 2026-11-25)

- **A1 Test tooling and tests only, no product changes.** Change `scripts/validate.sh`, add `scripts/run_suites.py` (parallel runner and `--quick` selection), and change the tests under `plugins/delegate/tests/` that really wait. Product code under `plugins/delegate/scripts/` is untouched; short deadlines in tests come only from existing environment variables (such as `DELEGATE_TIMEOUT_SECONDS`) and the stubs' own parameters.
- **A2 No CI file changes.** `.github/workflows/ci.yml` already calls `validate.sh`, so parallelism applies automatically and this module does not touch T4 files. CI timings before and after are still reported.
- **A3 Static checks stay first and serial.** JSON, shell, manifests, shared sections, Python syntax, local paths and the scripts' self-tests stay out of the pool, with unchanged order and failure text.
- **A4 Regression suites run in parallel.** The 3 `.sh` suites, 31 `.py` suites and `test-claude-isolation.py --policy-only`, 35 entries in one pool. Concurrency defaults to `os.cpu_count()`; `--jobs N` overrides; `--jobs 1` is serial. Python standard library only.
- **A5 Suites are isolated.** Each suite process gets its own new `TMPDIR`, removed afterwards. Reason: the product writes logs under `${TMPDIR}/delegate/` and prunes old logs beyond 50 groups; with a shared `TMPDIR`, one suite could delete files another suite is using. `HOME` is not changed globally; tests that set it keep doing so.
- **A6 Output and exit codes keep their shape.** Each suite's stdout and stderr are buffered and printed whole, in list order, with no interleaving. Failure text stays the original sentence (for example 「`<suite>` 回归测试未通过」); any failure makes the exit code 1. `release_prepare.py` counts tests from `Ran N tests in` lines and loop suites from `for SUITE in …; do … test-${SUITE}.py … done`; both stay parseable, so the release script is unchanged.
- **A7 Slowest suites at the end.** After a full run, the five slowest suites with seconds, and the pool's wall-clock, are printed to stderr.
- **A8 `--quick` runs only the suites the changes touch.**
  - Change set: from `git merge-base HEAD origin/main` to the working tree (including the index and untracked files; a rename counts as both its old and new name, and deleted files count). Without `origin/main` or a merge base, fall back to the full run.
  - First expand indirect product dependencies: when a file under `plugins/*/scripts/` is changed or deleted, other product scripts that mention its file name count as changed too, transitively until nothing is added (added during acceptance on 2026-11-25: with direct names only, a change to `review_init.py` missed the suites that use it through `review_result`).
  - Rules:
    1. A changed suite file runs that suite; other suites that load it (for example via `spec_from_file_location` or by running it) are selected too, as in rule 3.
    2. Changes only under `docs/`, `spec/`, `tasks/` or top-level `*.md` (Markdown inside the plugin, such as `commands/` and `skills/`, excepted) run no regression suite, only the static checks.
    3. Any other file: search the suite sources for its file name and run every suite that matches; a suite whose source has `.glob('*<suffix>')` and mentions the changed file's directory name (it reads the whole directory) also matches.
    4. If nothing matches, or `scripts/validate.sh`, `scripts/run_suites.py` or `.github/` changed, fall back to the full run.
  - Print which suites were selected and why; when falling back, give the reason. Static checks run in quick mode too.
- **A9 Remove real waiting without loosening assertions.**
  - `test-run-timeout.py`: lower `DELEGATE_TIMEOUT_SECONDS` and the stub's sleep within what the existing deadline formula allows.
  - `test-channel-regressions.py`: replace "the child writes a marker after 3 s and the test waits 3.2 s to confirm it did not" with a configurable child delay and a recorded start time; the test waits only until "start + delay + 0.5 s" before checking, also asserts that cleanup finished before the child would have written, and checks the child is no longer alive. Same meaning: still prove the child was reaped before it could write. (The earlier example, "write after 0.5 s, wait 0.8 s", is not workable: cleanup itself takes a second or two.)
  - Check every change against the original assertions; delete none and do not relax any condition.
- **A10 Documentation.**
  - The check entry in `AGENTS.md` follows C2 v1.7.3: full run `validate.sh`, quick check `validate.sh --quick`; day-to-day task work runs the quick check, the full run is kept for before merging and for CI.
  - Both `docs/development-workflow.md` pages are updated.
  - `CLAUDE.md` has no such line and imports the workflow page, so it is not edited; the shared-section check must still pass.
- **A11 One module, no usage draft.** Add `validate-speed` at the end of the capability map, depending on `release-prepare` (the release script parses `validate.sh`). `review-snapshot-recheck` has only R4 left (waiting for the M1 run); it is paused by insertion and resumed after this module merges.

## Baseline

Measured in this session on 2026-11-25 on main 1575e4e (8-core Mac, `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`, one run): exit 0, 407 seconds (6 min 47 s). The two-minute target of VS-2 is measured against this.

## Command

```text
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh [--quick] [--jobs N]
```

- Without arguments: static checks plus all regression suites, concurrency equal to the core count.
- Invalid arguments print usage and exit 64.

## Acceptance criteria

- **VS-1 Nothing fewer.** After a full run, the test count (sum of `Ran N tests`) and suite count are not lower than before: 512 tests and 31 Python loop suites. Removing real waiting deletes no test.
- **VS-2 Faster locally.** A full local run at default concurrency takes at most two minutes; report before and after.
- **VS-3 Parallel equals serial.** `--jobs 1` and the default both exit 0; with one suite made to fail, both exit 1 with the same failure text. Proven by `run_suites.py`'s own offline tests, not by running `validate.sh` recursively.
- **VS-4 Isolation.** A test proves each suite gets a distinct `TMPDIR` in parallel and that it is removed afterwards.
- **VS-5 No interleaving.** A test proves two suites writing at the same time are printed whole, in list order.
- **VS-6 Quick selection is right.** Each of rules 1–4 has an offline case: a temporary git repository with fake suites, asserting the selected suites and the fallback reason.
- **VS-7 Slowest list.** At the end of a full run, stderr names the five slowest suites with seconds.
- **VS-8 Release script unaffected.** `scripts/tests/test-release-prepare.py` and `test-validation-discovery.py` pass; `release_prepare.loop_suites` still counts 31 on the new `validate.sh`.
- **VS-9 Real waiting removed.** `test-run-timeout.py` and `test-channel-regressions.py`, timed alone, are clearly shorter than before; the numbers go into the todo. No fewer assertions.
- **VS-10 CI unchanged and reported.** `ci.yml` is not changed; both test rows on the PR still pass; report both timings against the previous ones.
- **VS-11 Documentation in sync.** The files listed in A10 are updated and the shared-section check passes.

## Boundaries

- **Always:** standard library only; Bash 3.2 compatible, shell tests with `/bin/bash`, Python with `-B`; run the full validation after every change; record the original assertions before changing a test.
- **Ask first:** anything that needs product code changes to shorten waiting; any change to `.github/workflows/`; `--quick` rules more aggressive than A8 (such as not running suites whose file name did not match).
- **Never:** delete or skip tests, loosen assertions, or trim the CI matrix; move suites that need a separately prepared guest (OS, SSH, live) into the offline checks; delete `scripts/check-frontmatter.py` in passing (discussed separately).

## Settled questions (previously open)

- **Q1 Does `--quick` run no regression suite when only documentation changed?** Settled as A, "yes" (A8 rule 2): no test reads these files, and the static checks cover links, local paths and shared sections. The conservative alternative, falling back to the full run on documentation changes, would make the quick check useless on documentation PRs.
- **Q2 Concurrency: core count, or capped?** Settled as A: core count, uncapped; on an 8-core machine the slowest single suite sets the wall-clock. CI's macOS machines have fewer cores, so concurrency drops automatically.
