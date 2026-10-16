# Chinese marketplace positioning design

历史归档（2026-08-30）：保留当时的文档设计、计划及原始语言，未完成勾选不代表当前状态。本文中的执行步骤和约束仅属于该历史任务；当前使用与文档导航见 [README](../../../README.md) 和 [文档索引](../../README.md)。

## Goal

Make the marketplace and plugin manifests present one consistent Chinese public
positioning for `delegate`, without changing installation metadata or runtime
behavior.

## Scope

Change only the `description` field in these files:

- `.claude-plugin/marketplace.json`
- `plugins/delegate/.claude-plugin/plugin.json`

Keep `name`, `version`, `source`, owner metadata, commands, hooks, and all
implementation files unchanged.

## Content

The marketplace description will use the fuller value proposition:

> 把已决策的执行与查证工作委托给 Codex CLI，只带回结论；默认只读、必须确认、绝不自动派。

The plugin description will use the shorter equivalent:

> 将已决策的执行工作委托给 Codex CLI：默认只读、需用户确认、不自动派。

Both descriptions intentionally communicate the settled-decision routing rule,
context isolation, read-only default, and user confirmation gate. They make no
claim about multi-backend routing, autonomous orchestration, or durable
background jobs.

## Verification

1. Parse both JSON files with `python3 -m json.tool`.
2. Check the two exact descriptions with `rg -F`.
3. Run `/bin/bash scripts/validate.sh`.
