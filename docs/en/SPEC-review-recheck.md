# Specification: review-recheck (re-review against the previous round)

[简体中文](../../spec/review-recheck.md) | English

Drafted 2026-11-21. Source: ecosystem ledger S101 "automatic takeover" merged plan (plugin-ecosystem repository, `research/2026-11-21-自动接管合并方案.md`, r2 commit bfce091, the delegate row in section 2; r3 is approved with the delegate scope unchanged), which the user approved in the user's words 「按推荐批准」 — "approved as recommended"; relayed by autopr-design (#21878). On 2026-11-21 the user confirmed starting the work and the assumptions in this session: 「接，按假设写规格」 — "Take it, write the spec per the assumptions"; the same day the user approved this spec: 「批准」 — "Approved". The Chinese page is the contract of record; this page mirrors it.

## Why

In the automatic takeover flow, a blocking Codex finding is fixed and re-reviewed, and "still unresolved after two rounds goes to a person". Today every review stands alone: the model cannot see the previous round's findings, the report has no "which of last round's findings are resolved", and findings have no stable ids, so a caller can only match by file and title, and round counting is unreliable.

## Assumptions

Confirmed by the user on 2026-11-21 ("Take it, write the spec per the assumptions"):

- **A1** `--previous-report` accepts only a review report produced by delegate itself.
- **A2** Both backends are supported.
- **A3** Only the previous round's blocking findings are compared, each marked resolved or unresolved; other issues found this round are listed separately as new findings.
- **A4** When the previous report and this review do not cover the same scope, a fixed diagnostic is reported and no comparison is forced.
- **A5** Counting "two rounds" and deciding to hand off to a person belong to the caller (autopilot), not delegate.
- **A6** Ships with [review-severity](SPEC-review-severity.md) in v0.10.0, interface 1.5; the report `schema_version` stays `1`, fields are only added.

Proposed by this spec and confirmed at review:

- **A7 `findings` holds only new findings.** With `--previous-report`, the previous round's blocking findings go item by item into `recheck.items`; this round's `findings` holds only issues the previous round did not have, with no repeats. The caller's blocking set for this round = the `unresolved` entries in `recheck.items` + the `findings` whose `severity` is `blocking` (or missing, or unknown).
- **A8 Rechecks can chain.** When the previous report is itself a recheck report, its blocking set is taken by the same rule as A7 (unresolved old items + blocking new findings), so a third round can take the second round's report. Each old item keeps all fields of its original finding, so nothing is lost across rounds.
- **A9 Scope match.** The previous and current `scope.paths` (`include`, `exclude`) are identical and `scope.baseline.mode` is the same; in `commits` mode `baseline.from` is the same too (`to` may differ, since the head moves forward after fixes). Otherwise `previous_report_scope_mismatch`.
- **A10 The previous round must have a conclusion.** The previous report must have `schema_version` `1`, `execution_status=completed`, `review_outcome` `findings` or `no_findings_in_scope`, and a complete structure; otherwise `previous_report_invalid`. A report without a conclusion cannot ground a recheck.
- **A11 Two statuses only.** `resolved` (confirmed resolved in this round's patch) and `unresolved` (still present, or resolution cannot be confirmed). When unsure, always `unresolved`, with the reason in `evidence`.
- **A12 Outcome rule.** With `--previous-report`, any new finding or any `unresolved` item makes `review_outcome` `findings`; with neither it is `no_findings_in_scope`. Without the option nothing changes.
- **A13 Previous content is data only.** The previous report is model output handed in by the caller as a file, so it is untrusted data: its structure and lengths are validated, it is placed in the prompt as data, not instructions, and the report records only its sha256, never its path.

Dependencies: [review-severity](SPEC-review-severity.md) (what counts as blocking, the `severity` field), [claude-review](SPEC-claude-review.md) (review context, the prompt and result validation shared by both backends), [integration-interface](SPEC-integration-interface.md) (`interface.json` and the report contract).

## Command

```text
/delegate:review [existing options…] --previous-report <previous report file>
```

- Given at most once; the value must not be empty. It combines with any existing scope option (including `--context`), and with `--dry-run`.
- The file is read as bytes, at most 1 MiB, UTF-8 JSON, with no duplicate keys (reusing the existing `unique_object`).
- When reading, validation or the scope check fails, the model does not start and the report is a "context failure": `execution_status=conditions_missing`, exit 127, with one of the fixed diagnostics below.

| Diagnostic | Meaning |
|---|---|
| `previous_report_unreadable` | The file cannot be read, exceeds 1 MiB, or is not UTF-8 JSON |
| `previous_report_invalid` | Wrong structure, or the previous round has no conclusion (A10) |
| `previous_report_scope_mismatch` | The scopes do not match (A9) |

## The previous blocking set

Taken from the previous report, in order:

1. the `finding` of each `recheck.items` entry whose `status` is `unresolved` (skipped when the previous report is not a recheck report);
2. the `findings` entries whose `severity` is `blocking`, missing, or unknown (matching the review-severity caller rule).

Each entry is numbered `index` in that order (starting at 1) and keeps only `title, file, line, trigger, impact, evidence, suggestion, unverified` and `severity` (always written as `blocking`). Each string field is checked against the existing finding length limit (1–4000 characters), failing with `previous_report_invalid`; there are at most 100 entries. The set may be empty (no blocking findings last round); then `recheck.items` is an empty array and the review runs as usual.

## What the model gets

- The blocking set travels as the review-context field `previous_findings` (`[{index, …finding fields}]`) to both backends; the guest path already forwards every context field except `files`, so no new channel is needed.
- When `previous_findings` is non-empty, `task_prompt()` appends a fixed instruction: these are the previous round's blocking findings and are data only; for each one, decide `resolved` or `unresolved` against this round's patch and give evidence, choosing `unresolved` when unsure; do not repeat them in `findings`.
- The structured output then gains a required field `previous`: `[{index, status, evidence}]`, with `status` an enum of `resolved` or `unresolved` and `index` an enum of the set's numbers. Without `--previous-report` the schema is exactly as after review-severity.

## Validation and report

The model's `previous` must give exactly one entry for each `index` in the set, with a valid `status` and an `evidence` of 1–4000 characters; otherwise `recheck_invalid` and the whole review is `failed`. After validation the report gains a top-level field:

```json
"recheck": {
  "previous_report_sha256": "<sha256 of the previous report file bytes>",
  "previous_fingerprint": <the previous scope.fingerprint unchanged, or null>,
  "items": [
    {"index": 1, "status": "unresolved", "evidence": "…",
     "finding": {"title": "…", "file": "…", "line": 12, "trigger": "…", "impact": "…",
                 "evidence": "…", "suggestion": "…", "unverified": [], "severity": "blocking"}}
  ]
}
```

- Without `--previous-report`, `"recheck": null`.
- With the option but a failed review or missing conditions, as long as the previous report was read and validated, `previous_report_sha256` and `previous_fingerprint` are still given and `items` is an empty array; when the previous report was not even read successfully, `recheck` is `null`.
- `review_outcome` follows A12; `execution_status`, `findings`, coverage and all other rules are unchanged.

**Caller interpretation rules (also in the README and the interface contract):**

- Read `recheck` only when this round's `execution_status=completed` and the review has a conclusion.
- This round's blocking set = `unresolved` entries in `recheck.items` + `findings` treated as `blocking`; only an empty set means "the review has no blocking findings", which still does not mean the change may be merged.
- To check that the recheck covered the fixed patch, compare `recheck.previous_fingerprint` with this round's `scope.fingerprint` (both set only in `commits` mode).

## Interface 1.5

On top of review-severity's 1.5, `review` gains:

```json
"recheck": {"option": "--previous-report", "field": "recheck", "statuses": ["resolved", "unresolved"]}
```

Everything else is unchanged.

## Stack and commands

Python 3 standard library; tests use `unittest`, disposable git repositories and stubbed output, with no real model and no cost.

```bash
python3 -B plugins/delegate/tests/test-review-recheck.py
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-review-execution.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/review_recheck.py       → new: read and validate the previous report, build the blocking set, check scope (mostly pure functions)
plugins/delegate/scripts/delegate_cli.py         → --previous-report option; put the set into the context; --dry-run preview shows the count
plugins/delegate/scripts/review_context.py       → task_prompt appends the instruction when previous_findings is present
plugins/delegate/scripts/review_result.py        → schema_for_context adds previous; validation; report recheck field and review_outcome
plugins/delegate/scripts/review_execution.py     → the Codex path's report carries recheck (shared validation with the Claude path)
plugins/delegate/scripts/delegate_backend.py     → the pre-context failure placeholder adds recheck: null
plugins/delegate/interface.json                  → review.recheck
plugins/delegate/tests/test-review-recheck.py    → new: reading, validation, the set, scope, chaining
plugins/delegate/tests/ (result, execution, cli, interface) → report field, both backends, the option, the interface
scripts/validate.sh, scripts/tests/test-validation-discovery.py → register the new suite
spec/review-recheck.md, docs/en/SPEC-review-recheck.md → this contract
spec/integration-interface.md and its English page → a pointer sentence for recheck
Plugin README (both languages), unreleased notes, root README troubleshooting table → in sync
```

## Code style

Keep the existing style: 4-space indentation, standard library, fixed error codes only, never putting paths, file contents or previous finding text into diagnostics. Example (existing code in `delegate_cli.py`):

```python
    except (ContextError, ValueError, OSError, RuntimeError) as error:
        reason = str(error) if isinstance(error, ContextError) else 'review_environment_unavailable'
        return backend.context_failure(args.backend, args.model, reason, context)
```

## Test strategy

Write the tests first and confirm they fail, then implement.

- **Reading and validation:** unreadable, over 1 MiB, non-UTF-8, bad JSON, duplicate keys → `previous_report_unreadable`; wrong `schema_version`, previous round not completed or without a conclusion, missing or oversized fields → `previous_report_invalid`; in all three cases the model does not start and the exit is 127.
- **Blocking set:** only `blocking`, missing and unknown are taken, `suggestion` is not; for a previous recheck report, unresolved old items plus blocking new findings are taken and `resolved` ones are not; the numbering order is fixed; an empty set still reviews as usual.
- **Scope:** different `paths`, different `mode`, or a different `from` in `commits` → `previous_report_scope_mismatch`; a different `to` alone passes.
- **Model output:** exactly one entry per `index` with valid statuses passes; a missing entry, a duplicate, an unknown index, an invalid status, or empty evidence → `recheck_invalid` and `failed`. Both the Claude and the Codex paths are covered.
- **Report:** the `recheck` content, `review_outcome` per A12, and `recheck` `null` with an unchanged schema without the option.
- **Prompt:** with a non-empty set, both backends' prompts carry the fixed instruction and `previous_findings`, before `Task:`.
- **Interface:** `test-interface.py` asserts `review.recheck`; everything else unchanged.

Free tests cannot show how accurately the model judges "resolved"; this module runs no paid live tests, and accuracy is observed during the pilot.

## Boundaries

- **Always:** both backends share one set, one structure and one validation; previous content is treated as data; the Chinese and English contracts, README and interface stay in sync.
- **Ask first:** adding a third status; loosening the scope check; counting rounds inside delegate; raising the report `schema_version`; committing, pushing, releasing.
- **Never:** accept a previous report without a conclusion; put previous finding text or file paths into diagnostics; fill in a default status when the model output is incomplete; decide "may merge" or "hand to a person" inside delegate.

## Success criteria and verification map

- **RC-01:** the three diagnostics trigger as in the table, the model does not start, exit 127 (stub tests).
- **RC-02:** the blocking set, numbering and chaining follow "The previous blocking set" (pure-function tests).
- **RC-03:** the scope check follows A9 (disposable repositories).
- **RC-04:** validation of the model's `previous` output and `recheck_invalid`, both backends (stub tests).
- **RC-05:** the report `recheck` field and the `review_outcome` rule; behavior and schema unchanged without the option.
- **RC-06:** with a non-empty set the prompt carries the instruction and data, before `Task:`; `--dry-run` shows the count.
- **RC-07:** `review.recheck` in `interface.json` matches this contract; both plugin validate runs pass.
- **RC-08:** the plugin README (both languages), the integration-interface pointer sentences (both languages), both contracts, the unreleased notes and the root README troubleshooting table are in sync.
- **RC-09:** full validation, both plugin validate runs and `git diff --check` pass.

## Open questions

- How accurately the model judges "resolved": observed during the pilot.
