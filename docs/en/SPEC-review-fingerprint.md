# Specification: review-fingerprint (a patch fingerprint that can be recomputed on another machine)

[简体中文](../../spec/review-fingerprint.md) | English

Drafted 2026-11-20. Source: ecosystem ledger S98, autopr-design request 3a (plugin-ecosystem repository, `research/2026-11-18-自动PR系统设计/plugin-requests-draft.md`, commit 7560e19), forwarded by ecosystem-lead (#21652). On 2026-11-20 the user decided to take it on and write the spec as recommended, in the user's words: 「接，按推荐写规格」 — "Take it, write the spec as recommended"; the same day the user approved this spec and the new capability-map row: 「批准，写英文页和 Plan」 — "Approved, write the English page and the Plan." The Chinese page is the contract of record; this page mirrors it.

## Why

autopilot wants to recompute the patch fingerprint in a review report on GitHub Actions, to confirm that the review's conclusion belongs to exactly the patch about to be merged. Today's `scope.diff_sha256` is the sha256 of the `git diff` output text, which cannot do that:

- the repository's own `.git/config` (`diff.algorithm`, `diff.noprefix`, `diff.context`, `core.quotepath` and so on) and the repository's `.gitattributes` change the diff text;
- a different git version may produce different diff text; the abbreviation length of object ids on the `index` line also scales with the number of objects in the repository.

The first two can be pinned one by one with `-c`; the third cannot. As long as the fingerprint is taken over diff text, it cannot be stable across machines.

## Premises (confirmed by the user on 2026-11-20, as recommended)

- **A1** Add a fingerprint field `scope.fingerprint` that depends only on what git stores: the object id and file mode of each reviewed file before and after the change. It is independent of git configuration, the git version and the diff output format.
- **A2** `scope.diff_sha256` stays as it is, in computation and meaning; the documentation notes that it is only valid on the local machine and cannot be recomputed elsewhere. It is not hardened with `-c`: that would change existing values and still not address git version differences.
- **A3** The fingerprint is emitted only for the `commits` baseline (reviewing the changes between two commits). `staged`, `unstaged` and `working-tree` review content that is not committed and does not exist on other machines; for those modes the field is `null`.
- **A4** The recomputing side uses the same repository (same object format, both SHA-1 or both SHA-256). delegate does not translate between the two formats.
- **A5** delegate only specifies the algorithm, keeps it stable and publishes it in the interface; recomputation, comparing a PR's changed files and deciding whether to merge are the consumer's (autopilot's) job (the user's 11-19 principle: each plugin only does what is within its own capability).
- **A6** Fields are only added: interface version 1.3 → 1.4; the review report `schema_version` stays `1`. The 1.4 content previewed in [run-rules](SPEC-run-rules.md) (`run.restore`, `run.concurrent`, `doctor.quota`) has not been started and moves to the next minor version. Release version v0.9.0.

Depends on: [claude-review](SPEC-claude-review.md) (review context and report generation), [integration-interface](SPEC-integration-interface.md) (`interface.json`, the report contract and versioning rules).

## Fingerprint algorithm `blob-pairs-v1`

**Inputs:**

- `scope.baseline.from` and `scope.baseline.to` from the report: resolved full commit ids (delegate already outputs full ids).
- The reviewed path set P: file paths changed between `from` and `to` that fall in the review scope (`include` minus `exclude`), without rename detection. P covers exactly the files `diff_sha256` covers and is written as is to `scope.fingerprint.paths`.

**Two entries per path:** look up path p in the tree of commit `from` to get mode `from_mode` and object id `from_oid`; likewise in the tree of `to` for `to_mode` and `to_oid`.

- Modes are the 6-digit octal of the git tree, for example `100644`, `100755`, `120000` (symlink), `160000` (submodule).
- Object ids are full-length lowercase hexadecimal (40 digits in a SHA-1 repository, 64 in a SHA-256 repository).
- When the path does not exist on a side, or is a directory (`040000`) on that side, the entry is `000000` and an all-zero id of the repository's id length.

**Canonical text:**

```text
delegate-blob-pairs-v1\n
<p1>\0<from_mode> <from_oid> <to_mode> <to_oid>\n
<p2>\0<from_mode> <from_oid> <to_mode> <to_oid>\n
…
```

- The first line is the fixed version header `delegate-blob-pairs-v1` followed by a newline.
- One line per path, sorted ascending by the path's UTF-8 bytes.
- The path is written as is (UTF-8, no quoting, no escaping), followed by one NUL byte, then the four fields separated by single spaces, and a newline (`\n`) at the end of the line.
- When P is empty, the canonical text is the version header only.

**Result:** `sha256(bytes of the canonical text)`, as lowercase hexadecimal.

**Recomputation reference (not part of the contract; any tool that reads git trees will do):**

```bash
git --literal-pathspecs ls-tree -z --full-tree <commit> -- <path>
```

The output is `<mode> <type> <oid>\t<path>\0`; no output, or `type` `tree`, counts as "does not exist".

## Report field

`scope` gains `fingerprint`:

```json
"fingerprint": {
  "algorithm": "blob-pairs-v1",
  "sha256": "<64 lowercase hex digits>",
  "paths": ["<P, in UTF-8 byte order>"]
}
```

For a baseline other than `commits` it is `"fingerprint": null`. When the review fails or conditions are missing, the field is still emitted as long as the review context was obtained, the same as `diff_sha256`; when the run fails before the context is obtained, both are `null`.

**Reading rules for consumers (written into the README and the interface contract):**

- The fingerprint only proves "the patch the review saw = these changes of these paths from `from` to `to`". To make sure a PR has no files the review did not see, the consumer compares the PR's changed files with `paths` itself.
- Whether a review conclusion is usable still follows the reading rules of [integration-interface](SPEC-integration-interface.md) (`completed` with a conclusion). A matching fingerprint does not mean the review reached a conclusion, let alone that merging is approved.
- A consumer that meets an `algorithm` value it does not know must treat it as "cannot recompute", never as a match.

## Interface 1.4

`interface.json` changes `interface` to `"1.4"` and adds under `review.report`:

```json
"report": {"schemaVersion": 1,
           "fingerprint": {"field": "scope.fingerprint", "algorithm": "blob-pairs-v1",
                           "baselineModes": ["commits"]}}
```

Everything else is unchanged.

## Stack and commands

Python 3 standard library; tests use `unittest` and temporary git repositories, no real model, no paid runs.

```bash
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-fingerprint.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/review_fingerprint.py    → new: canonical text and sha256 (pure function, no git)
plugins/delegate/scripts/review_context.py        → commits baseline: read both entries, build fingerprint
plugins/delegate/scripts/review_result.py         → emit fingerprint under scope
plugins/delegate/scripts/delegate_backend.py      → placeholder for failures before the context adds fingerprint: null
plugins/delegate/interface.json                   → 1.4, review.report.fingerprint
plugins/delegate/tests/test-review-fingerprint.py → new: algorithm and fixed test vectors
plugins/delegate/tests/test-review-context.py     → baseline modes, repository configuration interference
plugins/delegate/tests/test-interface.py          → 1.4 assertions
scripts/validate.sh, scripts/tests/test-validation-discovery.py → register the new suite
spec/review-fingerprint.md, docs/en/SPEC-review-fingerprint.md → this contract
spec/integration-interface.md and its English page → pointer sentence for 1.4
plugin README (Chinese and English), unreleased notes → external interface section in sync
```

## Implementation notes

- Both entries come from one `git diff --raw -z --no-renames --no-abbrev --no-relative <from> <to> -- <P>`: it gives the two modes and full-length ids directly, and a missing side already reads `000000` with an all-zero id. It still goes through the existing `git()`, keeping the environment that shields global and system configuration.
- The path set obtained must equal P exactly; otherwise the fixed code `fingerprint_inputs_inconsistent` is reported and the whole review is treated as a context failure (at the same level as `input_changed`), with no partial fingerprint.
- The canonical text is produced by a pure function in `review_fingerprint.py`; tests call it directly, separately from the code that reads the entries.

## Code style

Keep the existing style: 4-space indentation, standard library, errors are fixed codes only, no paths, ids or git output in diagnostics. Example (existing code in `review_context.py`):

```python
    diff_args = ['diff', '--no-ext-diff', '--no-textconv', '--no-renames']
    if mode == 'commits':
        for key in ('from', 'to'):
            baseline[key] = git(root, 'rev-parse', '--verify', '--end-of-options', baseline[key] + '^{commit}').decode().strip()
```

## Test strategy

Write the tests first and see them fail, then implement.

- **Algorithm (`test-review-fingerprint.py`):** fixed test vectors (paths, modes and ids given by hand; assert the canonical text byte for byte and the sha256 value); the empty set; ordering by UTF-8 bytes (including Chinese paths and case); the 64-digit all-zero id of a SHA-256 repository.
- **Entries (`test-review-context.py`, temporary repositories):** added, deleted, modified, mode-only change, file to symlink, file to directory; results match an independent recomputation with `git ls-tree`.
- **Configuration independence:** for the same pair of commits, set `diff.algorithm=patience`, `diff.noprefix=true`, `diff.context=10`, `core.quotepath=false` and `core.abbrev=12` in the repository's `.git/config`, and add `-diff` in `.gitattributes`; assert that `diff_sha256` changes while `fingerprint.sha256` does not (which also shows the old fingerprint really is unstable).
- **Modes:** `staged`, `unstaged` and `working-tree` give `null`; files excluded by `exclude` are not in `paths`.
- **Interface:** `test-interface.py` asserts 1.4 and `review.report.fingerprint`; existing fields are unchanged.

Stability across git versions follows from the algorithm itself (only modes and ids stored in trees are used); this module does not measure it on several git versions.

## Boundaries

- **Always:** the value of `diff_sha256` is unchanged; the fingerprint uses only what trees store; Chinese and English contracts, READMEs and the interface stay in sync.
- **Ask first:** defining a fingerprint for non-`commits` modes; changing any detail of `blob-pairs-v1` (only a new algorithm name may be introduced; the old name always means the same algorithm); raising the report `schema_version`; commits, pushes, releases.
- **Never:** use diff text or configuration-dependent output in the fingerprint; emit a partial fingerprint; decide inside delegate on the consumer's behalf that "the patch matches, merging is fine".

## Success criteria and verification mapping

- **FP-01:** fixed test vectors, the empty set, ordering and the 64-digit all-zero id pass (stub tests).
- **FP-02:** entries for the six change shapes match an independent `git ls-tree` recomputation (temporary repositories).
- **FP-03:** under repository configuration and `.gitattributes` interference `fingerprint.sha256` is unchanged while `diff_sha256` changes (temporary repositories).
- **FP-04:** non-`commits` modes give `null`; `paths` covers the same files as `diff_sha256`; an inconsistent entry set reports `fingerprint_inputs_inconsistent` with no partial fingerprint.
- **FP-05:** `interface.json` is 1.4, `review.report.fingerprint` matches this contract, existing fields are unchanged; both plugin validations pass.
- **FP-06:** the external interface section of both plugin READMEs, the integration-interface pointer sentences in both languages, both contracts and the unreleased notes are in sync.
- **FP-07:** the full validation, both plugin validations and `git diff --check` pass.

## Open questions

- When autopilot recomputes, the checkout on Actions must be able to reach the `from` commit (a shallow clone needs deepening). This is the consumer's deployment concern; the README will mention it, delegate does not handle it.
- A fingerprint for local uncommitted content (`working-tree` and so on) would be a separate change with a new algorithm name.
