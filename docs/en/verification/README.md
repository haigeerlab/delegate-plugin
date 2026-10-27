# Verification records index

[简体中文](../../verification/README.md) | English

`docs/verification/` holds acceptance runs, live validation, repair re-checks and review records. Files stay flat, dated and in place; they are not moved or rewritten, because other records, plans and JSON evidence cite them by path and SHA-256. This page is navigation only. The records themselves are in Chinese except where noted.

- **result/record**: the conclusion of one acceptance, repair or review round.
- **plan/preview**: a pre-execution plan, batch preview or handoff (`*-plan.md`, `*-preview.md`); matching `*-preview.json` and `*-handoff.json` files are the machine-readable drafts.
- **Companion data**: `*.json` files (results or previews) and `*.py.txt` files (the check scripts as used at the time, not current executables) sharing the record's prefix.

Records keep the version, authorization and status of their time; they are not current installation or behavior contracts. For the current state start from the [contract and verification matrix](../../verification/2026-10-08-contract-matrix.md) and the [current dual-backend delivery status](../../verification/2026-10-13-delegate-delivery-status.md); see the [historical evidence index](../../verification/2026-10-08-history.md) for evidence boundaries. The English redaction note is [2026-10-08-public-redaction.en.md](../../verification/2026-10-08-public-redaction.en.md).

## Spec Guard adoption batch and historical reconciliation (2026-10-08)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-08-batch-plan.md](../../verification/2026-10-08-batch-plan.md) | plan/preview | — |
| [2026-10-08-bulk.md](../../verification/2026-10-08-bulk.md) | result/record | [2026-10-08-bulk-closeout.py.txt](../../verification/2026-10-08-bulk-closeout.py.txt), [2026-10-08-bulk-results.json](../../verification/2026-10-08-bulk-results.json) |
| [2026-10-08-contract-matrix.md](../../verification/2026-10-08-contract-matrix.md) | result/record | — |
| [2026-10-08-f8-applied.md](../../verification/2026-10-08-f8-applied.md) | result/record | [2026-10-08-f8-applied-results.json](../../verification/2026-10-08-f8-applied-results.json) |
| [2026-10-08-historical-reconciliation.md](../../verification/2026-10-08-historical-reconciliation.md) | result/record | [2026-10-08-historical-reconciliation.json](../../verification/2026-10-08-historical-reconciliation.json) |
| [2026-10-08-history.md](../../verification/2026-10-08-history.md) | result/record | — |
| [2026-10-08-live.md](../../verification/2026-10-08-live.md) | result/record | [2026-10-08-live-results.json](../../verification/2026-10-08-live-results.json) |
| [2026-10-08-mutation.md](../../verification/2026-10-08-mutation.md) | result/record | [2026-10-08-mutation-results.json](../../verification/2026-10-08-mutation-results.json) |
| [2026-10-08-proposal-plan.md](../../verification/2026-10-08-proposal-plan.md) | plan/preview | — |
| [2026-10-08-proposal.md](../../verification/2026-10-08-proposal.md) | result/record | [2026-10-08-proposal-closeout.py.txt](../../verification/2026-10-08-proposal-closeout.py.txt), [2026-10-08-proposal-preparation.json](../../verification/2026-10-08-proposal-preparation.json), [2026-10-08-proposal-results.json](../../verification/2026-10-08-proposal-results.json) |
| [2026-10-08-public-redaction.en.md](../../verification/2026-10-08-public-redaction.en.md) | result/record | — |
| [2026-10-08-public-redaction.md](../../verification/2026-10-08-public-redaction.md) | result/record | [2026-10-08-public-redaction.json](../../verification/2026-10-08-public-redaction.json) |
| [2026-10-08-supplemental.md](../../verification/2026-10-08-supplemental.md) | result/record | [2026-10-08-supplemental-results.json](../../verification/2026-10-08-supplemental-results.json) |

Data without a dedicated record page: [2026-10-08-batch-preparation.json](../../verification/2026-10-08-batch-preparation.json), [doctor-isolation-proposal-results.json](../../verification/doctor-isolation-proposal-results.json), [doctor-isolation-proposal.patch.txt](../../verification/doctor-isolation-proposal.patch.txt), [doctor-isolation-proposal.py.txt](../../verification/doctor-isolation-proposal.py.txt), [f8-applied-check.py.txt](../../verification/f8-applied-check.py.txt), [historical-evidence.json](../../verification/historical-evidence.json), [live-batch-check.py.txt](../../verification/live-batch-check.py.txt), [mutation-check.py.txt](../../verification/mutation-check.py.txt), [supplemental-check.py.txt](../../verification/supplemental-check.py.txt).

## Claude review backend: isolation gate and Mac acceptance (2026-10-09 to 10-12)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-09-claude-review-linux.md](../../verification/2026-10-09-claude-review-linux.md) | result/record | — |
| [2026-10-09-claude-review-vm-preflight.md](../../verification/2026-10-09-claude-review-vm-preflight.md) | plan/preview | — |
| [2026-10-09-claude-review.md](../../verification/2026-10-09-claude-review.md) | result/record | — |
| [2026-10-10-claude-review-guest-cli.md](../../verification/2026-10-10-claude-review-guest-cli.md) | result/record | [2026-10-10-claude-review-guest-cli.json](../../verification/2026-10-10-claude-review-guest-cli.json) |
| [2026-10-10-claude-review-integration.md](../../verification/2026-10-10-claude-review-integration.md) | result/record | — |
| [2026-10-10-claude-review-mac-live-plan.md](../../verification/2026-10-10-claude-review-mac-live-plan.md) | plan/preview | — |
| [2026-10-10-claude-review-mac-native.md](../../verification/2026-10-10-claude-review-mac-native.md) | result/record | — |
| [2026-10-10-claude-review-mac-preflight.md](../../verification/2026-10-10-claude-review-mac-preflight.md) | result/record | — |
| [2026-10-10-claude-review-mac-reverse-plan.md](../../verification/2026-10-10-claude-review-mac-reverse-plan.md) | plan/preview | — |
| [2026-10-10-claude-review-mac-reverse-second-plan.md](../../verification/2026-10-10-claude-review-mac-reverse-second-plan.md) | plan/preview | — |
| [2026-10-12-claude-review-mac-reverse-fourth-current-plan.md](../../verification/2026-10-12-claude-review-mac-reverse-fourth-current-plan.md) | plan/preview | — |
| [2026-10-12-claude-review-mac-reverse-fourth-fixed-plan.md](../../verification/2026-10-12-claude-review-mac-reverse-fourth-fixed-plan.md) | plan/preview | — |
| [2026-10-12-claude-review-mac-reverse-fourth-plan.md](../../verification/2026-10-12-claude-review-mac-reverse-fourth-plan.md) | plan/preview | — |
| [2026-10-12-claude-review-mac-reverse-fourth-success.md](../../verification/2026-10-12-claude-review-mac-reverse-fourth-success.md) | result/record | [2026-10-12-claude-review-mac-reverse-fourth-success.json](../../verification/2026-10-12-claude-review-mac-reverse-fourth-success.json) |
| [2026-10-12-claude-review-mac-reverse-third-plan.md](../../verification/2026-10-12-claude-review-mac-reverse-third-plan.md) | plan/preview | — |

Data without a dedicated record page: [2026-10-10-claude-review-mac-live-first.json](../../verification/2026-10-10-claude-review-mac-live-first.json), [2026-10-10-claude-review-mac-live-followup-preview.json](../../verification/2026-10-10-claude-review-mac-live-followup-preview.json), [2026-10-10-claude-review-mac-live-fourth-preview.json](../../verification/2026-10-10-claude-review-mac-live-fourth-preview.json), [2026-10-10-claude-review-mac-live-fourth.json](../../verification/2026-10-10-claude-review-mac-live-fourth.json), [2026-10-10-claude-review-mac-live-second.json](../../verification/2026-10-10-claude-review-mac-live-second.json), [2026-10-10-claude-review-mac-live-third-preview.json](../../verification/2026-10-10-claude-review-mac-live-third-preview.json), [2026-10-10-claude-review-mac-live-third.json](../../verification/2026-10-10-claude-review-mac-live-third.json), [2026-10-10-claude-review-mac-reverse-current-preview.json](../../verification/2026-10-10-claude-review-mac-reverse-current-preview.json), [2026-10-10-claude-review-mac-reverse-first.json](../../verification/2026-10-10-claude-review-mac-reverse-first.json), [2026-10-10-claude-review-mac-reverse-handoff.json](../../verification/2026-10-10-claude-review-mac-reverse-handoff.json), [2026-10-10-claude-review-mac-reverse-preview.json](../../verification/2026-10-10-claude-review-mac-reverse-preview.json), [2026-10-10-claude-review-mac-reverse-second-handoff.json](../../verification/2026-10-10-claude-review-mac-reverse-second-handoff.json), [2026-10-10-claude-review-mac-reverse-second-preview.json](../../verification/2026-10-10-claude-review-mac-reverse-second-preview.json), [2026-10-10-claude-review-mac-startup.json](../../verification/2026-10-10-claude-review-mac-startup.json), [2026-10-12-claude-review-mac-reverse-fourth-current-preview.json](../../verification/2026-10-12-claude-review-mac-reverse-fourth-current-preview.json), [2026-10-12-claude-review-mac-reverse-fourth-driver-result.json](../../verification/2026-10-12-claude-review-mac-reverse-fourth-driver-result.json), [2026-10-12-claude-review-mac-reverse-fourth-fixed-preview.json](../../verification/2026-10-12-claude-review-mac-reverse-fourth-fixed-preview.json), [2026-10-12-claude-review-mac-reverse-fourth-preview.json](../../verification/2026-10-12-claude-review-mac-reverse-fourth-preview.json), [2026-10-12-claude-review-mac-reverse-second-result.json](../../verification/2026-10-12-claude-review-mac-reverse-second-result.json), [2026-10-12-claude-review-mac-reverse-third-handoff.json](../../verification/2026-10-12-claude-review-mac-reverse-third-handoff.json), [2026-10-12-claude-review-mac-reverse-third-preview.json](../../verification/2026-10-12-claude-review-mac-reverse-third-preview.json), [2026-10-12-claude-review-mac-reverse-third-result.json](../../verification/2026-10-12-claude-review-mac-reverse-third-result.json).

## Dual-backend interface and Codex source loading (2026-10-10 to 10-12)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-10-delegate-interface.md](../../verification/2026-10-10-delegate-interface.md) | result/record | [2026-10-10-delegate-interface.json](../../verification/2026-10-10-delegate-interface.json) |
| [2026-10-12-delegate-final-review.md](../../verification/2026-10-12-delegate-final-review.md) | result/record | [2026-10-12-delegate-final-review.json](../../verification/2026-10-12-delegate-final-review.json) |
| [2026-10-12-delegate-source-load-plan.md](../../verification/2026-10-12-delegate-source-load-plan.md) | plan/preview | — |
| [2026-10-12-delegate-source-load-result.md](../../verification/2026-10-12-delegate-source-load-result.md) | result/record | [2026-10-12-delegate-source-load-result.json](../../verification/2026-10-12-delegate-source-load-result.json) |

Data without a dedicated record page: [2026-10-12-delegate-preflight-fix.json](../../verification/2026-10-12-delegate-preflight-fix.json), [2026-10-12-delegate-source-load-preview.json](../../verification/2026-10-12-delegate-source-load-preview.json), [2026-10-12-node-environment-repair.json](../../verification/2026-10-12-node-environment-repair.json).

## Command migration, install sync and S1–S3 (2026-10-13)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-13-delegate-checkpoint3-review.md](../../verification/2026-10-13-delegate-checkpoint3-review.md) | result/record | [2026-10-13-delegate-checkpoint3-review.json](../../verification/2026-10-13-delegate-checkpoint3-review.json) |
| [2026-10-13-delegate-claude-desktop-entry-mismatch.md](../../verification/2026-10-13-delegate-claude-desktop-entry-mismatch.md) | result/record | [2026-10-13-delegate-claude-desktop-entry-mismatch.json](../../verification/2026-10-13-delegate-claude-desktop-entry-mismatch.json) |
| [2026-10-13-delegate-claude-install-staged-result.md](../../verification/2026-10-13-delegate-claude-install-staged-result.md) | result/record | [2026-10-13-delegate-claude-install-staged-result.json](../../verification/2026-10-13-delegate-claude-install-staged-result.json) |
| [2026-10-13-delegate-claude-refresh-fixed-result.md](../../verification/2026-10-13-delegate-claude-refresh-fixed-result.md) | result/record | [2026-10-13-delegate-claude-refresh-fixed-result.json](../../verification/2026-10-13-delegate-claude-refresh-fixed-result.json) |
| [2026-10-13-delegate-claude-refresh-result.md](../../verification/2026-10-13-delegate-claude-refresh-result.md) | result/record | [2026-10-13-delegate-claude-refresh-result.json](../../verification/2026-10-13-delegate-claude-refresh-result.json) |
| [2026-10-13-delegate-command-fixes-result.md](../../verification/2026-10-13-delegate-command-fixes-result.md) | result/record | [2026-10-13-delegate-command-fixes-result.json](../../verification/2026-10-13-delegate-command-fixes-result.json) |
| [2026-10-13-delegate-command-migration-fix.md](../../verification/2026-10-13-delegate-command-migration-fix.md) | result/record | [2026-10-13-delegate-command-migration-fix.json](../../verification/2026-10-13-delegate-command-migration-fix.json) |
| [2026-10-13-delegate-command-multiaxis-review.md](../../verification/2026-10-13-delegate-command-multiaxis-review.md) | result/record | [2026-10-13-delegate-command-multiaxis-review.json](../../verification/2026-10-13-delegate-command-multiaxis-review.json) |
| [2026-10-13-delegate-delivery-status.md](../../verification/2026-10-13-delegate-delivery-status.md) | result/record | — |
| [2026-10-13-delegate-host-command-loading.md](../../verification/2026-10-13-delegate-host-command-loading.md) | result/record | [2026-10-13-delegate-host-command-loading.json](../../verification/2026-10-13-delegate-host-command-loading.json) |
| [2026-10-13-delegate-local-activation-plan.md](../../verification/2026-10-13-delegate-local-activation-plan.md) | plan/preview | — |
| [2026-10-13-delegate-local-activation-result.md](../../verification/2026-10-13-delegate-local-activation-result.md) | result/record | [2026-10-13-delegate-local-activation-result.json](../../verification/2026-10-13-delegate-local-activation-result.json) |
| [2026-10-13-delegate-post-review-sync-complete-result.md](../../verification/2026-10-13-delegate-post-review-sync-complete-result.md) | result/record | [2026-10-13-delegate-post-review-sync-complete-result.json](../../verification/2026-10-13-delegate-post-review-sync-complete-result.json) |
| [2026-10-13-delegate-post-review-sync-plan.md](../../verification/2026-10-13-delegate-post-review-sync-plan.md) | plan/preview | — |
| [2026-10-13-delegate-post-review-sync-result.md](../../verification/2026-10-13-delegate-post-review-sync-result.md) | result/record | [2026-10-13-delegate-post-review-sync-result.json](../../verification/2026-10-13-delegate-post-review-sync-result.json) |
| [2026-10-13-delegate-post-review-sync-resume-result.md](../../verification/2026-10-13-delegate-post-review-sync-resume-result.md) | result/record | [2026-10-13-delegate-post-review-sync-resume-result.json](../../verification/2026-10-13-delegate-post-review-sync-resume-result.json) |
| [2026-10-13-delegate-remaining-acceptance-plan.md](../../verification/2026-10-13-delegate-remaining-acceptance-plan.md) | plan/preview | — |
| [2026-10-13-delegate-remaining-acceptance-result.md](../../verification/2026-10-13-delegate-remaining-acceptance-result.md) | result/record | [2026-10-13-delegate-remaining-acceptance-result.json](../../verification/2026-10-13-delegate-remaining-acceptance-result.json) |
| [2026-10-13-delegate-remaining-gap-plan.md](../../verification/2026-10-13-delegate-remaining-gap-plan.md) | plan/preview | — |
| [2026-10-13-delegate-routing-host-fix.md](../../verification/2026-10-13-delegate-routing-host-fix.md) | result/record | [2026-10-13-delegate-routing-host-fix.json](../../verification/2026-10-13-delegate-routing-host-fix.json) |
| [2026-10-13-delegate-s1-result.md](../../verification/2026-10-13-delegate-s1-result.md) | result/record | [2026-10-13-delegate-s1-result.json](../../verification/2026-10-13-delegate-s1-result.json) |
| [2026-10-13-delegate-s2-plan.md](../../verification/2026-10-13-delegate-s2-plan.md) | plan/preview | — |
| [2026-10-13-delegate-s2-recovery-result.md](../../verification/2026-10-13-delegate-s2-recovery-result.md) | result/record | [2026-10-13-delegate-s2-recovery-result.json](../../verification/2026-10-13-delegate-s2-recovery-result.json) |
| [2026-10-13-delegate-s2-result.md](../../verification/2026-10-13-delegate-s2-result.md) | result/record | [2026-10-13-delegate-s2-result.json](../../verification/2026-10-13-delegate-s2-result.json) |
| [2026-10-13-delegate-s2-resume-result.md](../../verification/2026-10-13-delegate-s2-resume-result.md) | result/record | [2026-10-13-delegate-s2-resume-result.json](../../verification/2026-10-13-delegate-s2-resume-result.json) |
| [2026-10-13-delegate-source-load-fixed-plan.md](../../verification/2026-10-13-delegate-source-load-fixed-plan.md) | plan/preview | — |
| [2026-10-13-delegate-source-load-fixed-result.md](../../verification/2026-10-13-delegate-source-load-fixed-result.md) | result/record | [2026-10-13-delegate-source-load-fixed-result.json](../../verification/2026-10-13-delegate-source-load-fixed-result.json) |
| [2026-10-13-spec-guard-workflow-check.md](../../verification/2026-10-13-spec-guard-workflow-check.md) | result/record | [2026-10-13-spec-guard-workflow-check.json](../../verification/2026-10-13-spec-guard-workflow-check.json) |

Data without a dedicated record page: [2026-10-13-delegate-installed-preview-result.json](../../verification/2026-10-13-delegate-installed-preview-result.json), [2026-10-13-delegate-local-activation-preview.json](../../verification/2026-10-13-delegate-local-activation-preview.json), [2026-10-13-delegate-post-review-sync-preview.json](../../verification/2026-10-13-delegate-post-review-sync-preview.json), [2026-10-13-delegate-source-load-fixed-preview.json](../../verification/2026-10-13-delegate-source-load-fixed-preview.json).

## Layered acceptance and S4–S7 (2026-10-14)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-14-delegate-acceptance-decision.md](../../verification/2026-10-14-delegate-acceptance-decision.md) | result/record | — |
| [2026-10-14-delegate-error-diagnostics-result.md](../../verification/2026-10-14-delegate-error-diagnostics-result.md) | result/record | [2026-10-14-delegate-error-diagnostics-result.json](../../verification/2026-10-14-delegate-error-diagnostics-result.json) |
| [2026-10-14-delegate-final-layered-review.md](../../verification/2026-10-14-delegate-final-layered-review.md) | result/record | [2026-10-14-delegate-final-layered-review.json](../../verification/2026-10-14-delegate-final-layered-review.json) |
| [2026-10-14-delegate-layered-acceptance-result.md](../../verification/2026-10-14-delegate-layered-acceptance-result.md) | result/record | [2026-10-14-delegate-layered-acceptance-result.json](../../verification/2026-10-14-delegate-layered-acceptance-result.json) |
| [2026-10-14-delegate-remaining-acceptance-feasibility.md](../../verification/2026-10-14-delegate-remaining-acceptance-feasibility.md) | result/record | [2026-10-14-delegate-remaining-acceptance-feasibility.json](../../verification/2026-10-14-delegate-remaining-acceptance-feasibility.json) |
| [2026-10-14-delegate-s4-read-boundary-plan.md](../../verification/2026-10-14-delegate-s4-read-boundary-plan.md) | plan/preview | — |
| [2026-10-14-delegate-s4-read-boundary-result.md](../../verification/2026-10-14-delegate-s4-read-boundary-result.md) | result/record | [2026-10-14-delegate-s4-read-boundary-result.json](../../verification/2026-10-14-delegate-s4-read-boundary-result.json) |
| [2026-10-14-delegate-s5-sync-plan.md](../../verification/2026-10-14-delegate-s5-sync-plan.md) | plan/preview | — |
| [2026-10-14-delegate-s5-sync-result.md](../../verification/2026-10-14-delegate-s5-sync-result.md) | result/record | [2026-10-14-delegate-s5-sync-result.json](../../verification/2026-10-14-delegate-s5-sync-result.json) |
| [2026-10-14-delegate-s6-auth-diagnosis.md](../../verification/2026-10-14-delegate-s6-auth-diagnosis.md) | result/record | [2026-10-14-delegate-s6-auth-diagnosis.json](../../verification/2026-10-14-delegate-s6-auth-diagnosis.json) |
| [2026-10-14-delegate-s6-diagnostic-followup-plan.md](../../verification/2026-10-14-delegate-s6-diagnostic-followup-plan.md) | plan/preview | [2026-10-14-delegate-s6-diagnostic-followup-plan.json](../../verification/2026-10-14-delegate-s6-diagnostic-followup-plan.json) |
| [2026-10-14-delegate-s6-diagnostic-followup-result.md](../../verification/2026-10-14-delegate-s6-diagnostic-followup-result.md) | result/record | [2026-10-14-delegate-s6-diagnostic-followup-result.json](../../verification/2026-10-14-delegate-s6-diagnostic-followup-result.json) |
| [2026-10-14-delegate-s6-read-boundary-plan.md](../../verification/2026-10-14-delegate-s6-read-boundary-plan.md) | plan/preview | — |
| [2026-10-14-delegate-s6-read-boundary-result.md](../../verification/2026-10-14-delegate-s6-read-boundary-result.md) | result/record | [2026-10-14-delegate-s6-read-boundary-result.json](../../verification/2026-10-14-delegate-s6-read-boundary-result.json) |
| [2026-10-14-delegate-s7-menu-plan.md](../../verification/2026-10-14-delegate-s7-menu-plan.md) | plan/preview | — |
| [2026-10-14-delegate-s7-menu-result.md](../../verification/2026-10-14-delegate-s7-menu-result.md) | result/record | [2026-10-14-delegate-s7-menu-result.json](../../verification/2026-10-14-delegate-s7-menu-result.json) |
| [2026-10-14-delegate-s7-output-readback-result.md](../../verification/2026-10-14-delegate-s7-output-readback-result.md) | result/record | [2026-10-14-delegate-s7-output-readback-result.json](../../verification/2026-10-14-delegate-s7-output-readback-result.json) |
| [2026-10-14-delegate-task6-runtime-timing-result.md](../../verification/2026-10-14-delegate-task6-runtime-timing-result.md) | result/record | [2026-10-14-delegate-task6-runtime-timing-result.json](../../verification/2026-10-14-delegate-task6-runtime-timing-result.json) |
| [2026-10-14-delegate-ui-and-s4-preview.md](../../verification/2026-10-14-delegate-ui-and-s4-preview.md) | plan/preview | — |
| [2026-10-14-delegate-validator-discovery-result.md](../../verification/2026-10-14-delegate-validator-discovery-result.md) | result/record | [2026-10-14-delegate-validator-discovery-result.json](../../verification/2026-10-14-delegate-validator-discovery-result.json) |

## Run timeout and write-mode trust: S35–S36 (2026-10-26)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-26-delegate-run-timeout-cp3.md](../../verification/2026-10-26-delegate-run-timeout-cp3.md) | result/record | — |
| [2026-10-26-delegate-s35-timeout-probe.md](../../verification/2026-10-26-delegate-s35-timeout-probe.md) | result/record | [2026-10-26-delegate-s35-timeout-probe.py.txt](../../verification/2026-10-26-delegate-s35-timeout-probe.py.txt) |
| [2026-10-26-delegate-s36-trust-followup-probe.md](../../verification/2026-10-26-delegate-s36-trust-followup-probe.md) | result/record | [2026-10-26-delegate-s36-trust-followup-probe.py.txt](../../verification/2026-10-26-delegate-s36-trust-followup-probe.py.txt) |
| [2026-10-26-delegate-s36-trust-probe.md](../../verification/2026-10-26-delegate-s36-trust-probe.md) | result/record | — |
| [2026-10-26-delegate-s36-write-trust-check.md](../../verification/2026-10-26-delegate-s36-write-trust-check.md) | result/record | [2026-10-26-delegate-s36-write-trust-check.py.txt](../../verification/2026-10-26-delegate-s36-write-trust-check.py.txt) |
| [2026-10-26-delegate-s36-write-trust-live.md](../../verification/2026-10-26-delegate-s36-write-trust-live.md) | result/record | — |

## Abort reaping and interface 1.3: S38, S41 (2026-10-27)

| Record | Kind | Companion data |
|---|---|---|
| [2026-10-27-delegate-s38-probe.md](../../verification/2026-10-27-delegate-s38-probe.md) | result/record | [2026-10-27-delegate-s38-probe.py.txt](../../verification/2026-10-27-delegate-s38-probe.py.txt), [2026-10-27-delegate-s38-fake-responses.py.txt](../../verification/2026-10-27-delegate-s38-fake-responses.py.txt), [2026-10-27-delegate-s38-term-repro.sh.txt](../../verification/2026-10-27-delegate-s38-term-repro.sh.txt) |
| [2026-10-27-delegate-1.3-merged-live.md](../../verification/2026-10-27-delegate-1.3-merged-live.md) | result/record | — |
