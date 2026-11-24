# Spec: reviewer-selection (detecting and choosing the second reviewer)

[简体中文](../../spec/reviewer-selection.md) | English

Drafted 2026-11-24. Source and approvals as for [design-review-criteria](SPEC-design-review-criteria.md): ecosystem ledger S110 section 5 (second reviewer) and section 7 (delegate row); on 2026-11-24 the user confirmed the requirement and Q1-Q7, the capability-map insertion, the usage draft and this spec ("批准"). This spec doubles as the technical design and regression document, tier important. The Chinese page is the authoritative contract.

## Why

S110 requires a second reviewer for technical designs: prefer an AI from a vendor other than the author's; with only one vendor set up, use a fresh same-vendor session and say so in the report; with none available, record "unreviewed"; the session that wrote the code never reviews its own work; before work starts, detect the available AIs and tell the user. Today `/delegate:review` needs an explicit `--backend` (default `codex`), the report does not say who reviewed or how they were chosen, there is no "unreviewed" outcome, and the README still says "stop when Codex is unavailable, never fall back to Claude reviewing itself", which conflicts with S110 section 5 item 4.

## Assumptions

Confirmed by the user on 2026-11-24:

- **P1 Name the author.** `--backend auto` requires `--author-host claude-code|codex`; `auto` without it is an argument error.
- **P2 Availability uses model-free checks only.** The backends' existing pre-start checks (CLI present, version, logged in; plus the local boundary checks for Claude); no model request. If a check passes but the real run fails, the failure is reported; delegate does not retry with the other vendor.
- **P3 Report fields.** Top-level `reviewer: {vendor, backend, same_vendor, selection}`; "unreviewed" is `execution_status=conditions_missing`, `review_outcome=inconclusive`, diagnostic `no_reviewer_available`, `selection="none"`, exit 127.
- **P4 Never self-review.** Both backends start a fresh process session that inherits no caller context; this module documents it and replaces the README wording.
- **E1 Vendor names.** `codex` → `openai`, `claude-code` → `anthropic`; `--author-host` takes backend names and maps the same way.
- **E2 Order.** Author `claude-code`: check Codex first (`cross_vendor`), then Claude Code (`same_vendor_fallback`), else unreviewed. Author `codex` is symmetric.
- **E3 Explicit backends are labelled too.** With `--backend codex|claude-code`, `selection="explicit"`; `same_vendor` is computed when `--author-host` is given and `null` otherwise. Without `auto` everything else is the same as 0.11.0.
- **E7 The unreviewed report has `backend: null`.** When no backend started, top-level `backend` is `null` (as are `reviewer.vendor`, `reviewer.backend` and `reviewer.same_vendor`; `selection` is `none`). Contract: `backend` can be `null` only when `reviewer.selection == "none"`; otherwise it is still `codex` or `claude-code`. Found during implementation and not covered by the original spec; chosen by the user on 2026-11-24 ("A：null").
- **E4 `auto` takes no per-backend options.** `--backend auto` with `--model`, `--effort`, `--max-turns` or `--max-budget-usd` is an argument error.
- **E5 Doctor.** `/delegate:doctor --reviewers` runs the P2 checks for both vendors, reports each as available or not (with a fixed code), suggests adding a second vendor when only one is available, and says reviews will be recorded as unreviewed when none is; `--json` prints `{"schema": "delegate.reviewers/v1", "reviewers": [{"backend", "vendor", "available", "diagnostic"}], "hint"}` for spec-guard. It never blocks anything and exits 0.
- **E6 Interface 1.7**, additive, together with [design-review-criteria](SPEC-design-review-criteria.md).

## Design

1. **Options.** The review command accepts `--backend auto` and `--author-host codex|claude-code` (once) and checks P1 and E4 (exit 64).
2. **Choice.** New `reviewer_select.py`: pure `order(author)`, `choose(author, checks)` and `describe(backend, author, selection)`; `real_checks()` wraps the existing pre-start checks (Codex `backend.check_detailed()`, Claude the same local checks as `review_doctor.py --backend claude-code`). Tests pin the results with `DELEGATE_FIXTURE_REVIEWERS`; without that variable the real checks are always used.
3. **Routing.** After the context is read, `auto` chooses; the chosen backend then follows the unchanged route. With none available, an unreviewed report is written (no model starts), exit 127.
4. **Report.** `base_report()` adds top-level `reviewer`, also in placeholders.
5. **Doctor.** `review_doctor.py --reviewers [--json]` per E5; existing usages unchanged.
6. **Interface.** `interface` 1.7; `review.reviewer: {"option": "--backend auto", "authorOption": "--author-host", "field": "reviewer", "vendors": {...}, "selections": [...], "unreviewed": "no_reviewer_available"}`; `doctor.reviewers: {"option": "--reviewers", "json": "delegate.reviewers/v1"}`.
7. **Docs.** README and command help describe `auto`, `--author-host`, `reviewer` and how to read "unreviewed"; the root README wording becomes "the session that wrote the code never reviews its own work".

## Regression tests

| Id | Case | How | Evidence |
|---|---|---|---|
| RS-01 | Author claude-code: Codex available → codex/`cross_vendor`/`same_vendor=false`; Codex unavailable, Claude available → claude-code/`same_vendor_fallback`/`true`; neither → `none` | command | `test-reviewer-select.py` |
| RS-02 | Author codex: the three cases mirrored | command | `test-reviewer-select.py` |
| RS-03 | Unreviewed end to end: exit 127, `conditions_missing`, `inconclusive`, `no_reviewer_available`, `backend_started=false`, `backend` null, no model | command | `test-review-cli.py` |
| RS-04 | `auto` picks Codex and runs the stub: `reviewer` matches `backend`, other fields equal an explicit `--backend codex` run | command | `test-review-cli.py` |
| RS-05 | Explicit backend: `selection=explicit`; `same_vendor` computed with `--author-host`, `null` without | command | `test-review-cli.py`, `test-review-result.py` |
| RS-06 | Argument errors (exit 64): `auto` without `--author-host`; `auto` with per-backend options; invalid or repeated `--author-host` | command | `test-review-cli.py` |
| RS-07 | Placeholder reports written before the context is read carry `reviewer` | command | `test-review-cli.py` |
| RS-08 | `/delegate:doctor --reviewers`: both available, one available (with hint), none; `--json` matches `delegate.reviewers/v1`; existing usages unchanged | command | `test-review-backends.py` |
| RS-09 | `interface.json` is 1.7 with `review.reviewer` and `doctor.reviewers` as specified; both plugin validations pass | command | `test-interface.py` |
| RS-10 | Without `auto`/`--author-host`, all existing suites pass with unchanged assertions | command | `scripts/validate.sh` |
| RS-11 | Docs: zh/en contracts, plugin README, command help, root README, integration-interface pointer, unreleased notes | manual | checked item by item in the todo |

## Boundaries

- **Always:** behaviour unchanged without the new options; choose with model-free checks only; fixed diagnostic codes; zh/en in sync.
- **Ask first:** a third vendor; switching vendor after a failed run; guessing the author from environment variables; commit, push, release.
- **Never:** review inside the caller's session; report "unreviewed" as passed or failed; put credentials, paths or raw errors in reports or diagnostics.

## Open questions

- None.
