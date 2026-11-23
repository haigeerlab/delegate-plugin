# Spec: design-review-criteria (technical design review criteria)

[简体中文](../../spec/design-review-criteria.md) | English

Drafted 2026-11-24. Source: ecosystem ledger S110 "development-flow rework", sections 5 and 7 (delegate row), assigned by ecosystem-lead #22330; spec-guard interface draft v1 (sg-coord #22364). On 2026-11-24 the user confirmed the requirement and Q1-Q7 ("说完了，按推荐定"), the capability-map insertion ("确认写入"), the usage draft [s110-design-review](../../spec/usage/s110-design-review.md) ("批准") and this spec ("批准"). Under the S110 transition this repository still uses the Spec/Plan flow; this spec doubles as the technical design and regression document, tier important. The Chinese page is the authoritative contract.

## Why

S110 changes the flow to requirement → technical design → regression → tasks → implementation → regression-based acceptance; a second reviewer checks the design against the code, one round of review and one of fixes. The existing criteria `severity-v1` are made for code patches and mark "does not meet the task" or "missing tests" as blocking; applied to designs they produce exactly the "only complains it is not complete enough, never passes in two rounds" behaviour seen after S101. S110 requires blocking findings on a design to be proven with code, and the second round to only check the previous one.

## Assumptions

Confirmed by the user on 2026-11-24:

- **P1 Entry.** `/delegate:review --profile design`, criteria `design-v1`; without it (or `--profile default`) criteria stay `severity-v1` and behaviour is the same as 0.11.0.
- **P2 Code evidence is checked mechanically.** A blocking finding must point to an existing line in a **reference file**; otherwise delegate records it as a suggestion marked `downgraded: "no_code_evidence"`, text unchanged.
- **P3 The caller brings the old code.** The caller passes the existing files listed in the design's impact section with `--spec`/`--plan`; delegate does not look for files itself.
- **P4 The second round only checks.** With `--previous-report`, new findings in this round are suggestions marked `downgraded: "second_round"`.
- **D1 Reference file.** A file in the snapshot that is not selected by the review scope (`scope.include`/`exclude`), i.e. one brought in only through `--spec`/`--plan` (or `context_files` in `--context`). The requirement is a reference file too: a design contradicting a requirement line is valid evidence. The design under review is never evidence.
- **D2 Unlocated findings do not fail a design review.** Today any finding whose line cannot be verified fails the review (`review_incomplete`). In the design profile such findings become suggestions per P2 (`no_code_evidence`), with the line cleared and the note kept in `unverified`; the overall conclusion is not affected. The default profile is unchanged.
- **D3 When both reasons apply, `second_round` is recorded.**
- **D4 A recheck needs the same criteria.** The previous report's `criteria` must equal this round's (old reports without it read as `severity-v1`); otherwise `previous_report_scope_mismatch`.
- **D5 The report gains `criteria`.** Top-level `criteria` is `severity-v1` or `design-v1`; downgraded findings carry `downgraded`. Report `schema_version` stays `1`.

Depends on [review-snapshot-recheck](SPEC-review-snapshot-recheck.md), [review-recheck](SPEC-review-recheck.md), [review-severity](SPEC-review-severity.md) and [claude-review](SPEC-claude-review.md). The interface version goes to 1.7 together with [reviewer-selection](SPEC-reviewer-selection.md).

## Design

1. **Option.** `delegate_cli.py` gains `--profile default|design` (once); `context['profile']` is set only for `design`, and the guest path forwards it with the context. `--dry-run` shows `profile` and `criteria`.
2. **Criteria and prompt.** `review_context.py` adds `DESIGN_CRITERIA` (full text below) and `DESIGN_INSTRUCTION`; `task_prompt()` uses `DESIGN_CRITERIA` instead of `SEVERITY_CRITERIA` for `profile == 'design'` and adds the instruction before `Task:`. The default prompt is byte-identical to 0.11.0.
3. **Validation and downgrade.** In the design profile `review_result.content_result()` downgrades blocking findings: second round → `second_round`; otherwise unlocated or not in a reference file → `no_code_evidence`. Unlocated findings no longer make the review unverified (D2). The default profile is unchanged.
4. **Report.** `base_report()` adds top-level `criteria`, also in placeholders written before the context is read.
5. **Recheck.** `review_recheck.check_scope()` also compares criteria (D4).
6. **Interface.** `interface.json` `review` gains `profiles: {"default": {"criteria": "severity-v1"}, "design": {"option": "--profile design", "criteria": "design-v1", "downgraded": ["no_code_evidence", "second_round"]}}`; the version number is raised to 1.7 with reviewer-selection, so the two ship together.

## design-v1 criteria (verbatim)

```text
You are reviewing a technical design, not code. Reference files (context_files that are not under review) contain the existing code, the requirement and contracts the design must fit.
Mark a finding "blocking" only when you can cite a specific line in a reference file that shows the design will go wrong, and one of these holds:
D1. Following the design breaks behavior that exists today: a caller, contract, data format or test shown in the cited line would stop working.
D2. The design relies on something the code does not have or that works differently from what the design assumes (a function, field, option, file or behavior), as the cited line shows.
D3. The design contradicts the requirement or an interface contract at the cited line.
D4. The design would let untrusted input reach a shell, eval, a secret or a permission check shown at the cited line.
D5. The design leaves out an existing caller or file that must change for it to work, as the cited line shows.
Set "file" and "line" of a blocking finding to that reference line. Everything else is a "suggestion": missing detail, wording, structure, alternatives, risks you cannot tie to a reference line, and anything about the design text itself.
```

## Commands

```bash
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-review-execution.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-review-recheck.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Regression tests

| Id | Case | How | Evidence |
|---|---|---|---|
| DR-01 | `--profile design`: prompts on both backends and the guest path carry `DESIGN_CRITERIA` and the instruction, not `SEVERITY_CRITERIA`; the default prompt is byte-identical to 0.11.0 | command | `test-review-context.py`, `test-review-execution.py`, `test-claude-review.py`, `test-review-guest.py` |
| DR-02 | design: blocking on a real reference line stays `blocking`; on the design, a missing line or `line` null → `suggestion` + `no_code_evidence`, text unchanged | command | `test-review-result.py` |
| DR-03 | design: unlocated findings do not fail the review; the same input in the default profile still fails with `review_incomplete` | command | `test-review-result.py` |
| DR-04 | design second round: new findings all `suggestion` + `second_round`; `recheck.items` unchanged | command | `test-review-result.py`, `test-review-execution.py` |
| DR-05 | Top-level `criteria`: `severity-v1` by default, `design-v1` for design; also in placeholders | command | `test-review-result.py`, `test-review-cli.py` |
| DR-06 | Different previous `criteria` (old reports read as `severity-v1`) → `previous_report_scope_mismatch`, exit 127, no model | command | `test-review-recheck.py`, `test-review-cli.py` |
| DR-07 | `--profile` repeated or invalid → exit 64; `--dry-run` shows `profile`, `criteria` | command | `test-review-cli.py` |
| DR-08 | `interface.json` `review.profiles` matches this spec; both plugin validations pass | command | `test-interface.py` |
| DR-09 | End to end: `--profile design --paths design.md --spec code.py` with a stub backend; one evidenced and one unevidenced blocking finding come out as `blocking` and a downgraded `suggestion` | command | `test-review-cli.py` |
| DR-10 | Existing behaviour: all existing suites pass with unchanged assertions | command | `scripts/validate.sh` |
| DR-11 | zh/en contracts, usage draft, plugin README, integration-interface pointer and unreleased notes in sync | manual | checked item by item in the todo |

## Risks and rollback

- The model cites the design itself as evidence → files under review never count.
- A downgrade hides a real problem → only `severity` changes; text, location and reason stay visible.
- The default profile is affected → byte-for-byte prompt check and unchanged existing suites.
- The caller forgets reference files → every blocking finding is downgraded; the README and the spec-guard agreement (#22369) say they must be passed.

Rollback: only options and fields are added; callers that drop `--profile design` get the old behaviour.

## Boundaries

- **Always:** default profile byte-identical; one set of criteria and validation for both backends and the guest path; change only `severity`, never the model's text; zh/en in sync.
- **Ask first:** changing `severity-v1`; failing a whole design review; deciding in delegate whether to review or to let a change through; commit, push, release.
- **Never:** count the design under review as evidence; silently drop a downgraded finding; put paths or model text in diagnostics.

## Open questions

- How accurately models label against `design-v1`: observe in usage-draft M1 after release.
