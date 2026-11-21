# Specification: review-severity (severity of review findings)

[简体中文](../../spec/review-severity.md) | English

Drafted 2026-11-21. Source: ecosystem ledger S101 "automatic takeover" merged plan r2 (plugin-ecosystem repository, `research/2026-11-21-自动接管合并方案.md`, commit bfce091, the delegate row in section 2), which the user approved in the user's words 「按推荐批准」 — "approved as recommended"; relayed by autopr-design (#21878). On 2026-11-21 the user confirmed starting the work and the assumptions in this session: 「接，按假设写规格」 — "Take it, write the spec per the assumptions"; the same day the user approved this spec and chose A for Q1: 「批准；Q1 A」 — "Approved; Q1 A". The Chinese page is the contract of record; this page mirrors it.

## Why

In the automatic takeover flow, Codex review findings fall into two classes: **blocking** (must be fixed, then re-reviewed; still unresolved after two rounds, hand it to a person) and **suggestion** (Claude decides whether to act and records one sentence of reasoning). Findings in delegate 0.9.0 carry only `title, file, line, trigger, impact, evidence, suggestion, unverified` with no severity, so a caller can only guess from the `impact` text, which is unreliable.

## Assumptions

Confirmed by the user on 2026-11-21 ("Take it, write the spec per the assumptions"):

- **A1** Two modules: this one covers severity only; re-review against the previous round is the follow-up module review-recheck. Both ship together in v0.10.0.
- **A2** Interface 1.4 → 1.5, fields added only; the review report `schema_version` stays `1`.
- **A3** autopr-design drafts the criteria, which are written into the "Criteria" section of this spec, agreed by both sides and approved by the user (received in #21881, see below).
- **A4** The review model labels each finding against the criteria; a caller treats a missing or unknown value as `blocking` (wording of the merged plan).

Proposed by this spec and confirmed at review (autopr-design's #21881 reply found no conflict with the orchestration):

- **A5 Strict validation.** The model must output `severity` for every finding, and the value must be `blocking` or `suggestion`. A missing or wrong value fails the whole review under the existing rules (diagnostic `finding_invalid`); delegate does not fill in `blocking` for the model. Reason: both backends enforce the schema through structured output, so this should not happen; if it does, the output cannot be trusted, and stopping on "no conclusion" is safer.
- **A6 Criteria carry a version name.** The criteria text as a whole has a name (first version `severity-v1`), published in `interface.json`. Any later change to the criteria takes a new name; an old name always means the same text. The report does not repeat the criteria name; the interface declaration is authoritative.
- **A7 No summary fields.** No "has blocking" or "blocking count" fields, and no "pass / fail"; callers count `findings[].severity` themselves. A review report is still not merge authorization.
- **A8 Criteria live only in delegate.** The criteria are fixed in delegate's review prompt; `--task` text cannot override or rewrite them. Changing the criteria goes through this repository's spec process.

Dependencies: [claude-review](SPEC-claude-review.md) (prompt and result validation shared by both backends), [integration-interface](SPEC-integration-interface.md) (`interface.json`, the report contract and versioning rules).

## Report field

Each `findings[]` item gains the required field `severity`:

```json
{"title": "…", "file": "…", "line": 12, "trigger": "…", "impact": "…",
 "evidence": "…", "suggestion": "…", "unverified": [], "severity": "blocking"}
```

- Values: `blocking` or `suggestion`, lowercase; there is no third value.
- delegate passes it through unchanged after result validation; wrapper fields such as `location_verified` are unchanged.
- With no findings, `findings` is an empty array; nothing else changes.

**Caller interpretation rules (also in the README and the interface contract):**

- A missing `severity` (for example in a report from 0.9.0 or earlier) or an unknown value is treated as `blocking`.
- Severity only matters when `execution_status=completed` and `review_outcome` is `findings` or `no_findings_in_scope`; otherwise stop on "no conclusion" and ignore the findings.
- `severity` is the review model's judgment against the criteria; delegate guarantees only the format and the value set, not that the judgment is right. No blocking findings does not mean no defects, still less that the change may be merged.

## Criteria `severity-v1`

Drafted by autopr-design and sent on 2026-11-21 (#21881), stating the user had approved them in the user's words 「按推荐批准」 — "approved as recommended"; archived in the plugin-ecosystem repository at `research/2026-11-18-自动PR系统设计/review-severity-criteria.md` (commit 5291680, including the U1 revision), identical to the text below. This text is identical to the prompt constant `SEVERITY_CRITERIA`.

```text
Mark a finding "blocking" when any of these is true:
B1. The change fails to do what the task or its stated acceptance criteria require, or contradicts them.
B2. You can name a concrete input or scenario where the change gives a wrong result, crashes, loses data, or breaks behavior that worked before.
B3. The change introduces a security risk: a committed secret, injection, untrusted input reaching a shell or eval, an auth or permission bypass, or broader token or workflow permissions.
B4. The change weakens verification: it deletes or loosens test assertions, skips or disables tests or checks, adds lint or type suppressions, or lowers thresholds, without the task asking for it.
B5. The change touches files or behavior outside the scope the task declares.
B6. The change performs an irreversible or destructive action (data migration, deletion, force push, publish, deploy, release) that the task did not explicitly ask for.
B7. The change adds or alters an external interface, a stored data format, or user-visible behavior that the task does not mention.
B8. The task requires tests for the new behavior and the change does not include them.

Mark a finding "suggestion" when none of B1-B8 applies, for example:
S1. Naming, readability, comments, style, or duplication.
S2. A refactor or simpler design that would not change behavior.
S3. Missing tests for new behavior when the task does not require them.
S4. Performance or robustness concerns without a concrete scenario that causes harm.

When unsure:
U1. If the finding would fall under B1-B8 were it true but you cannot confirm it from the code, mark it "blocking" and list in "unverified" what you could not confirm.
U2. Otherwise, if you cannot point to a specific requirement it violates or a concrete scenario where it fails, mark it "suggestion".
```

**U1 revision:** the draft U1 said `set "unverified" to true`, which does not fit delegate's `unverified` (an array of strings). On 2026-11-21 the user chose the fix (「批准；Q1 A」 — "Approved; Q1 A"); autopr-design agreed and updated the archive (#21904); the name stays `severity-v1`. Callers recognize such findings by a non-empty `unverified`.

## Prompt

`task_prompt()`, shared by both backends, appends a fixed passage after the existing instructions: it requires `severity` on every finding and includes the "Criteria" section verbatim. The Codex backend's `codex_prompt()` builds on `task_prompt()` and does not keep a separate copy. The `--task` text comes after the criteria, as data, and cannot override them (A8).

## Interface 1.5

`interface` in `interface.json` becomes `"1.5"`, and `review.report` gains:

```json
"severity": {"field": "findings[].severity", "values": ["blocking", "suggestion"],
             "criteria": "severity-v1", "missing": "blocking"}
```

Everything else is unchanged (including 1.4's `fingerprint`).

## Stack and commands

Python 3 standard library; tests use `unittest` and stubbed output, with no real model and no cost.

```bash
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-execution.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/scripts/review_result.py     → severity in FINDING_FIELDS and CONTENT_SCHEMA (enum, required); content_result validates the value
plugins/delegate/scripts/review_context.py    → task_prompt appends the criteria passage (constant SEVERITY_CRITERIA)
plugins/delegate/interface.json               → 1.5, review.report.severity
plugins/delegate/tests/test-review-result.py  → field validation, reports from both backends
plugins/delegate/tests/test-review-context.py → prompt contains the criteria, --task after the criteria
plugins/delegate/tests/test-interface.py      → 1.5 assertions
spec/review-severity.md, docs/en/SPEC-review-severity.md → this contract
spec/integration-interface.md and its English page → a pointer sentence for 1.5
Plugin README (both languages), unreleased notes → the external interface section
```

## Code style

Keep the existing style: 4-space indentation, standard library, fixed error codes only. Example (existing code in `review_result.py`):

```python
        for key in FINDING_FIELDS - {'line', 'unverified'}:
            if not isinstance(item[key], str) or not 1 <= len(item[key]) <= 4000:
                raise ResultError('finding_invalid')
```

## Test strategy

Write the tests first and confirm they fail, then implement.

- **Validation (`test-review-result.py`):** valid `blocking` and `suggestion` pass through unchanged; a missing `severity`, an uppercase value, an empty string, a third value, or a non-string all give `finding_invalid` and `execution_status=failed`; both the Claude and the Codex paths are covered.
- **Schema:** in `CONTENT_SCHEMA` and `schema_for_context()`, `severity` is a required enum and `additionalProperties` stays `false`.
- **Prompt (`test-review-context.py`, `test-review-execution.py`):** both backends' prompts contain `SEVERITY_CRITERIA` verbatim; `--task` appears after the criteria.
- **Interface:** `test-interface.py` asserts 1.5 and `review.report.severity`; the 1.4 content is unchanged.

Free tests cannot show how accurately the model labels against the criteria; this module runs no paid live tests, and accuracy is observed during the pilot.

## Boundaries

- **Always:** both backends share one structure and one set of criteria; values are strictly validated; the Chinese and English contracts, README and interface stay in sync.
- **Ask first:** adding a third value; changing any text of `severity-v1` (only a new name is allowed); adding summary or "pass" fields; raising the report `schema_version`; committing, pushing, releasing.
- **Never:** let `--task` override the criteria; fill in `severity` for the model; decide "may merge" inside delegate.

## Success criteria and verification map

- **SV-01:** valid values pass through unchanged; invalid or missing values give `finding_invalid` and `failed` (stub tests, both backends).
- **SV-02:** `severity` is a required enum in the structured-output schema.
- **SV-03:** both backends' prompts contain the criteria verbatim, with `--task` after the criteria.
- **SV-04:** `interface.json` is 1.5, `review.report.severity` matches this contract, existing fields are unchanged; both plugin validate runs pass.
- **SV-05:** the criteria section was drafted by autopr-design, agreed by both sides, and matches `SEVERITY_CRITERIA` verbatim.
- **SV-06:** the plugin README external interface section (both languages), the integration-interface pointer sentences (both languages), both contracts and the unreleased notes are in sync.
- **SV-07:** full validation, both plugin validate runs and `git diff --check` pass.

## Open questions

- ~~Q1 `unverified` in U1~~: settled, see the U1 revision in "Criteria".
- Labelling accuracy: observed during the pilot; if blocking issues are often labelled as suggestions, revise the criteria as `severity-v2`.
