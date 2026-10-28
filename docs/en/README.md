# Documentation index

[简体中文](../README.md) | English

Simplified Chinese is delegate's default documentation language. English counterparts cover maintained usage, design, technical specifications, contributions, and release notes. Both languages describe the same plugin and commands; runtime messages currently remain mainly Chinese.

## Choose a reading path

- First use: read [README](../../README.en.md) prerequisites and quick start, then check local readiness with `/delegate:doctor`.
- Daily use and troubleshooting: see README commands, output verification, and troubleshooting; `/delegate:help` is available inside a session.
- Design: read [Design and boundaries](DESIGN.md), then the [capability map](capability-map.md).
- Development and review: read the module specifications and [Contributing](../../CONTRIBUTING.en.md), and run offline validation from the repository root. The new [Claude review specification](SPEC-claude-review.md) describes v0.5.0. Native Mac boundaries and isolated regressions passed; normal real reviews succeeded in both directions on their frozen source. Menu-to-script execution and dry-run were verified. Active model boundary attempts, authentication refresh and natural abnormal helpers remain unverified.
- Upgrading: read [v0.8.2 release notes](releases/v0.8.2.md); when upgrading from v0.4.0, also read the command migration in [v0.5.0](releases/v0.5.0.md); see [Unreleased](releases/unreleased.md) for later changes.

## Maintained bilingual documentation

| Content | 简体中文 | English |
|---|---|---|
| Installation, usage, and troubleshooting | [README](../../README.md) | [README](../../README.en.md) |
| Documentation index | [文档索引](../README.md) | This page |
| Contributions and validation | [贡献指南](../../CONTRIBUTING.md) | [Contributing](../../CONTRIBUTING.en.md) |
| Security reporting | [安全政策](../../SECURITY.md) | [Security policy](../../SECURITY.en.md) |
| Design and boundaries | [设计](../../DESIGN.md) | [Design](DESIGN.md) |
| Module responsibilities | [能力图](../../spec/CAPABILITY-MAP.md) | [Capability map](capability-map.md) |
| Execution contract | [通道规格](../../spec/channel.md) | [Channel specification](SPEC-channel.md) |
| Detection and cache | [探测规格](../../spec/detection.md) | [Detection specification](SPEC-detection.md) |
| Routing and behavior evaluation | [路由规格](../../spec/routing.md) | [Routing specification](SPEC-routing.md) |
| Claude reviews | [审查规格](../../spec/claude-review.md) | [Review specification](SPEC-claude-review.md) |
| External interface | [接口规格](../../spec/integration-interface.md) | [Interface specification](SPEC-integration-interface.md) |
| Resumable delegation | [续跑规格](../../spec/run-resume.md) | [Run-resume specification](SPEC-run-resume.md) |
| Run timeout | [超时规格](../../spec/run-timeout.md) | [Run-timeout specification](SPEC-run-timeout.md) |
| Write-mode trust | [信任规格](../../spec/write-trust.md) | [Write-trust specification](SPEC-write-trust.md) |
| Run result | [结果文件规格](../../spec/run-result.md) | [Run-result specification](SPEC-run-result.md) |
| Continue after done | [续接规格](../../spec/run-continue.md) | [Run-continue specification](SPEC-run-continue.md) |
| Long tasks | [长任务规格](../../spec/run-longrun.md) | [Run-longrun specification](SPEC-run-longrun.md) |
| Checks and write authorization | [检查规格](../../spec/run-check.md) | [Run-check specification](SPEC-run-check.md) |
| Rules section | [规则片段规格](../../spec/run-rules.md) | [Run-rules specification](SPEC-run-rules.md) |
| Current release | [v0.8.2](../releases/v0.8.2.md) | [v0.8.2](releases/v0.8.2.md) |
| Subsequent changes | [未发布记录](../releases/unreleased.md) | [Unreleased](releases/unreleased.md) |
| Previous release records | [v0.8.1](../releases/v0.8.1.md)、[v0.8.0](../releases/v0.8.0.md)、[v0.7.1](../releases/v0.7.1.md)、[v0.7.0](../releases/v0.7.0.md)、[v0.6.0](../releases/v0.6.0.md)、[v0.5.3](../releases/v0.5.3.md)、[v0.5.2](../releases/v0.5.2.md)、[v0.5.1](../releases/v0.5.1.md)、[v0.5.0](../releases/v0.5.0.md)、[v0.4.0](../releases/v0.4.0.md)、[v0.3.1（历史）](../releases/v0.3.1.md) | [v0.8.1](releases/v0.8.1.md), [v0.8.0](releases/v0.8.0.md), [v0.7.1](releases/v0.7.1.md), [v0.7.0](releases/v0.7.0.md), [v0.6.0](releases/v0.6.0.md), [v0.5.3](releases/v0.5.3.md), [v0.5.2](releases/v0.5.2.md), [v0.5.1](releases/v0.5.1.md), [v0.5.0](releases/v0.5.0.md), [v0.4.0](releases/v0.4.0.md), [v0.3.1 (historical)](releases/v0.3.1.md) |

Start with README for installation and use. Chinese `spec/<id>.md` contracts and their English counterparts define exact implementation and test contracts. Maintain both languages together. Report discrepancies so they can be checked against current implementation and validation results and corrected in both versions.

Project source and accompanying documentation use the [MIT License](../../LICENSE). See the [README license section](../../README.en.md#license) for a summary; the standard English text in LICENSE governs.

## Source entry points

The repository contains both marketplace and plugin source:

```text
.claude-plugin/marketplace.json       Marketplace manifest
plugins/delegate/
  .claude-plugin/plugin.json         Plugin manifest
  README.md                         Plugin-directory guide shipped with the installation cache
  commands/                         review, run, doctor, help session entries
  skills/delegate-routing/          Routing criteria
  hooks/                            SessionStart readiness checks, cache, doctor entry
  scripts/                          Backend invocation and process management
  tests/                            Offline stub tests and regressions
scripts/                            Repository validation
evals/                              Behavior evaluators and optional model runs
.github/ISSUE_TEMPLATE/             Bug report and feature request templates
```

Command files and the skill are host-executed instructions, currently written in Chinese. The English documents linked here explain their complete usage contract and do not register a second set of plugin commands.

## Current development workflow

[Development workflow and AI instructions](development-workflow.md) ([简体中文](../development-workflow.md)) explains both hosts, standard paths, checkpoint confirmation, and verification limits. Current module checklists in Chinese: [channel](../../tasks/channel/todo.md), [detection](../../tasks/detection/todo.md), [routing](../../tasks/routing/todo.md), [claude-review](../../tasks/claude-review/todo.md), [integration-interface](../../tasks/integration-interface/todo.md), [run-resume](../../tasks/run-resume/todo.md), [run-timeout](../../tasks/run-timeout/todo.md), [write-trust](../../tasks/write-trust/todo.md), [run-result](../../tasks/run-result/todo.md), [run-continue](../../tasks/run-continue/todo.md), [run-longrun](../../tasks/run-longrun/todo.md), [run-check](../../tasks/run-check/todo.md), [run-rules](../../tasks/run-rules/todo.md). The first three track adoption reconciliation without retroactive historical acceptance.

The [contract clause and evidence matrix](../verification/2026-10-08-contract-matrix.md), an administrative record in Chinese, maps 13 current clauses to source, tests, and gaps. Maintenance completion does not establish sufficient acceptance of every product clause.

The new `claude-review` [plan](../../tasks/claude-review/plan.md) / [tasks](../../tasks/claude-review/todo.md), in Chinese, separately track two-backend reviews. [ADR-002](decisions/ADR-002-claude-review-isolation.md) ([简体中文](../decisions/ADR-002-claude-review-isolation.md)) records CLI, snapshot, and isolation decisions. [ADR-003](decisions/ADR-003-review-process-boundary.md) ([简体中文](../decisions/ADR-003-review-process-boundary.md)) records the process-boundary revision and the Linux/VM approach, which the current release does not wire in. [ADR-004](decisions/ADR-004-native-mac-review.md) ([简体中文](../decisions/ADR-004-native-mac-review.md)) records the native Mac boundary now in use. The module is locally accepted under layered criteria; its real evidence remains source-version-specific and does not inherit other modules' live acceptance evidence.

## Historical and implementation records

These records preserve earlier approaches, checklists, and trade-offs. They are not current installation or behavior contracts. Old options, authentication criteria, performance figures, and unchecked boxes do not establish the state of the current version.

- Original module plans/tasks and bilingual-revision records: [byte-preserved archive](../archive/pre-spec-guard/README.md), retaining original paths, checkboxes, and SHA-256.
- Documentation designs from 2026-08-30 and their implementation records (public positioning, Chinese marketplace positioning, v0.3.0 release-note draft), originally in English: [byte-preserved archive](../archive/superpowers-2026-08-30/README.md), retaining original paths and SHA-256.
- This Spec Guard adoption's administrative records, in Chinese: [plan](../process/2026-10-08-adoption/plan.md) / [tasks and verification](../process/2026-10-08-adoption/todo.md) / [findings](../process/2026-10-08-adoption/report.md).
- Earlier repairs and live validation: [sanitized summary and exact local evidence index](../verification/2026-10-08-history.md), in Chinese.
- All verification records: [index grouped by series](verification/README.md), separating results/records from plans/previews; files stay in place.

Historical and implementation records retain their original language rather than receiving individual translations. Maintained documents have complete bilingual reading paths through the table above.

Administrative records in Chinese: [reconciliation of 119 historical unchecked entries](../verification/2026-10-08-historical-reconciliation.md) and [26 supplemental offline probes](../verification/2026-10-08-supplemental.md). Current evidence does not establish historical completion or approval.

[Mutation and business-directory snapshot verification](../verification/2026-10-08-mutation.md), an administrative record in Chinese, covers this batch and the F8 test-isolation gap.

Current command tool-scope decision: [ADR-001](decisions/ADR-001-command-tool-scope.md) ([简体中文](../decisions/ADR-001-command-tool-scope.md)). The latest [seven-condition batch results](../verification/2026-10-08-bulk.md), in Chinese, retain actual native-host evidence and the one incomplete condition.

The [final native interactive sample](../verification/2026-10-08-proposal.md), in Chinese, closes the remaining current sample condition: 106 supported, 13 superseded, zero unverified archived criteria. Historical completion/approval and broader product coverage gaps remain separate.
