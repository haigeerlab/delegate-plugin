# Specification: integration-interface (published interface and review report contract)

[简体中文](../../spec/integration-interface.md) | English

Drafted 2026-10-17 and approved by the user the same day. Prompted by ecosystem seam suggestions (spec-guard offering `/delegate:review` as a read-only second opinion at checkpoints; decision-inbox citing review conclusions). This module only turns delegate's existing capabilities and existing report format into a description other plugins can depend on by version. It adds no review behavior.

## Assumptions (confirmed by the user on 2026-10-17 as A1–A5)

- **A1** Two deliverables only: publish `interface.json`; document the existing review report `schema_version: 1` as an external contract. Returning results through the mailbox is out of scope: results already return to the session that started the review, and cross-session forwarding belongs to agent-relay.
- **A2** `interface.json` is a static declaration of what is supported plus an interface version. It never claims a backend is available right now; availability is still checked live by `/delegate:doctor`.
- **A3** No severity field this time and no change to report generation; only the existing v1 fields are promised.
- **A4** No new runtime dependency; delegate behaves the same whether other plugins are installed or not. delegate neither probes nor calls other plugins.
- **A5** Follow the module workflow: Plan and code only after this specification is approved.

## Tech stack and commands

A static JSON file and Python 3 standard-library `unittest`; no new script entry or hook.

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-interface.py
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Project structure

```text
plugins/delegate/interface.json            → new: external capabilities and interface version (shipped with the plugin)
plugins/delegate/tests/test-interface.py   → new: consistency assertions between the description and source facts
plugins/delegate/README.md / README.en.md  → new "External interface" section: how to read it, version rules, report fields
plugins/delegate/scripts/delegate_capabilities.py → read-only reference: source of backend capability facts, unchanged
plugins/delegate/scripts/review_result.py  → read-only reference: source of report field facts, unchanged
spec/integration-interface.md              → Chinese contract
docs/en/SPEC-integration-interface.md      → this contract
docs/releases/unreleased.md                → one pending release note
```

## Interface description `interface.json`

Placed at the plugin root, following agent-relay: a consumer finds the enabled delegate install path from the host's plugin record, reads this file and checks the `interface` version range, without reading delegate internals. First version:

```json
{
  "interface": "1.0",
  "review": {
    "command": "/delegate:review",
    "backends": ["codex", "claude-code"],
    "readOnly": true,
    "report": {"schemaVersion": 1}
  },
  "run": {"command": "/delegate:run", "backends": ["codex"], "write": "explicit"},
  "doctor": {"command": "/delegate:doctor"}
}
```

- `backends` lists backends this version **supports**, not ones installed, authenticated or funded on this machine. A consumer suggesting a delegate review must not claim from it that the review will run.
- Version rules: adding optional fields is a minor version (`1.x`); removing, renaming or changing the meaning of a field is a major version (`2.0`). Consumers check a major range such as `>=1.0,<2.0`.
- If the file cannot be read or parsed, consumers should report "unknown", not "not installed". That is the consumer's probe rule; delegate only guarantees the file exists and is valid.

## Review report contract (`schemaVersion: 1`)

**How to obtain it:** the standard output of `/delegate:review` is one JSON report (`--dry-run` prints a `kind=review_preview` preview, not a report). The `delegate: artifacts=<path>` line on standard error points to a private copy; its path and retention (latest 50) are not part of the contract.

**v1 stable fields:**

| Field | Meaning |
|---|---|
| `schema_version` | Always `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`, `scope.baseline`, `scope.diff_sha256`, `scope.files` | Review target and fingerprint: scope, baseline, diff digest, per-file sha256 |
| `reviewed` | Files actually reviewed |
| `unreviewed[]` | `{path, reason}`, files not reviewed and why |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified}`; `line` may be `null` |
| `limitations` | Limitation statements |

Other fields (such as `host`, `diagnostics`, `observed_models`, `cleanup`, `usage`) are still emitted but are diagnostics that may change between versions; consumers should not depend on them.

**Interpretation rules (consumers must follow):**

- A review has a conclusion only when `execution_status=completed` and `review_outcome` is `findings` or `no_findings_in_scope`; anything else means "no conclusion".
- `no_findings_in_scope` only means nothing was reported within that scope, not that there are no defects.
- A report is a third-party opinion, not user approval, and does not authorize modification, merge or delivery. Cite it with the source delegate, the backend and the fingerprint.

## Code style

Keep the existing style. Tests use standard-library `unittest`, 4-space indentation, and import facts from source modules for comparison instead of copying a list into the test. Existing source of facts (`plugins/delegate/scripts/delegate_capabilities.py`):

```python
BACKENDS = {
    'codex': {'review': True, 'run': True, 'write': True,
              'options': ('--model', '--effort')},
    'claude-code': {'review': True, 'run': False, 'write': False,
                    'options': ('--model', '--max-turns', '--max-budget-usd')},
}
```

## Testing strategy

`test-interface.py` runs free consistency assertions so the description cannot drift from the code:

- `interface.json` is valid JSON and `interface` has the form `major.minor`;
- `review.backends` equals the backends with `review` true in `BACKENDS`, and `run.backends` those with `run` true;
- `review.report.schemaVersion` equals the `schema_version` produced by `base_report()`;
- every stable field in the contract appears in `base_report()` output, and the `findings` item field set equals `FINDING_FIELDS`;
- the contract values of `execution_status` and `review_outcome` match the values the source can produce.

The test fails first without `interface.json`, then turns green once the file is added. No real model and no paid verification.

## Boundaries

- **Always:** when report fields or backend capabilities change, update `interface.json`, the READMEs and this contract together, guarded by the consistency test; keep the Chinese and English contracts in sync.
- **Ask first:** new fields such as severity, raising `schema_version` or the `interface` major version, adding an executable entry such as `status`.
- **Never:** probe or call other plugins from delegate; send review results outward on its own; present `backends` as an availability guarantee; change report generation to fit the documentation.

## Success criteria and verification mapping

- **IF-01:** a valid `interface.json` exists at the plugin root matching the first version above; `claude plugin validate ./plugins/delegate` passes.
- **IF-02:** the consistency test goes red then green and covers the five assertions in the testing strategy.
- **IF-03:** both plugin READMEs have an "External interface" section covering how to read it, version rules, v1 stable fields and interpretation rules.
- **IF-04:** the full validation script, both plugin validations and `git diff --check` pass; existing test assertions are unchanged.

## Open questions

- spec-guard's probe script and decision-inbox's citation format are implemented by their own owners; after this module lands, notify them of the interface description and add any format needs found during integration as minor versions.
- A severity field will be proposed separately once a consumer actually needs to display findings by level.
