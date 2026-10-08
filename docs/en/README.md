# Documentation index

[简体中文](../README.md) | English

Simplified Chinese is delegate's default documentation language. English counterparts cover maintained usage, design, technical specifications, contributions, and release notes. Both languages describe the same plugin and commands; runtime messages currently remain mainly Chinese.

## Choose a reading path

- First use: read [README](../../README.en.md) prerequisites and quick start, then check local readiness with `/delegate:doctor`.
- Daily use and troubleshooting: see README commands, output verification, and troubleshooting; `/delegate:help` is available inside a session.
- Design: read [Design and boundaries](DESIGN.md), then the [capability map](capability-map.md).
- Development and review: read the three current specifications and [Contributing](../../CONTRIBUTING.en.md), and run offline validation from the repository root.
- Upgrading: read [v0.4.0 release notes](releases/v0.4.0.md); see [Unreleased](releases/unreleased.md) for later changes.

## Maintained bilingual documentation

| Content | 简体中文 | English |
|---|---|---|
| Installation, usage, and troubleshooting | [README](../../README.md) | [README](../../README.en.md) |
| Documentation index | [文档索引](../README.md) | This page |
| Contributions and validation | [贡献指南](../../CONTRIBUTING.md) | [Contributing](../../CONTRIBUTING.en.md) |
| Design and boundaries | [设计](../../DESIGN.md) | [Design](DESIGN.md) |
| Module responsibilities | [能力图](../../capability-map.md) | [Capability map](capability-map.md) |
| Execution contract | [通道规格](../../SPEC-channel.md) | [Channel specification](SPEC-channel.md) |
| Detection and cache | [探测规格](../../SPEC-detection.md) | [Detection specification](SPEC-detection.md) |
| Routing and behavior evaluation | [路由规格](../../SPEC-routing.md) | [Routing specification](SPEC-routing.md) |
| Current release | [v0.4.0](../releases/v0.4.0.md) | [v0.4.0](releases/v0.4.0.md) |
| Subsequent changes | [未发布记录](../releases/unreleased.md) | [Unreleased](releases/unreleased.md) |
| Previous release record | [v0.3.1（历史）](../releases/v0.3.1.md) | [v0.3.1 (historical)](releases/v0.3.1.md) |

Start with README for installation and use. Current `SPEC-*.md` files define exact implementation and test contracts. Maintain both languages together. Report discrepancies so they can be checked against current implementation and validation results and corrected in both versions.

Project source and accompanying documentation use the [MIT License](../../LICENSE). See the [README license section](../../README.en.md#license) for a summary; the standard English text in LICENSE governs.

## Source entry points

The repository contains both marketplace and plugin source:

```text
.claude-plugin/marketplace.json       Marketplace manifest
plugins/delegate/
  .claude-plugin/plugin.json         Plugin manifest
  commands/                         delegate, doctor, help session entries
  skills/delegate-routing/          Routing criteria
  hooks/                            Readiness checks, cache, context injection
  scripts/                          Codex invocation and process management
  tests/                            Offline stub tests and regressions
scripts/                            Repository validation
evals/                              Behavior evaluators and optional model runs
```

Command files and the skill are host-executed instructions, currently written in Chinese. The English documents linked here explain their complete usage contract and do not register a second set of plugin commands.

## Historical and implementation records

These records preserve earlier approaches, checklists, and trade-offs. They are not current installation or behavior contracts. Old options, authentication criteria, performance figures, and unchecked boxes do not establish the state of the current version.

- Early module records, in their original mixed Chinese/English: [channel plan](../../tasks/channel/plan.md) / [tasks](../../tasks/channel/todo.md), [detection plan](../../tasks/detection/plan.md) / [tasks](../../tasks/detection/todo.md), [routing plan](../../tasks/routing/plan.md) / [tasks](../../tasks/routing/todo.md).
- Documentation designs from 2026-08-30, originally in English: [public positioning](../superpowers/specs/2026-08-30-public-positioning-design.md), [Chinese marketplace positioning](../superpowers/specs/2026-08-30-chinese-marketplace-positioning-design.md), [v0.3.0 release-note draft](../superpowers/specs/2026-08-30-v030-release-notes-design.md).
- Corresponding implementation records, originally in English: [public positioning](../superpowers/plans/2026-08-30-public-positioning-docs.md), [Chinese marketplace positioning](../superpowers/plans/2026-08-30-chinese-marketplace-positioning.md), [v0.3.0 release-note draft](../superpowers/plans/2026-08-30-v030-release-notes.md).
- This bilingual revision's administrative records, in Chinese: [plan](../../tasks/plan.md) / [tasks and verification](../../tasks/todo.md).

Historical and implementation records retain their original language rather than receiving individual translations. Maintained documents have complete bilingual reading paths through the table above.
