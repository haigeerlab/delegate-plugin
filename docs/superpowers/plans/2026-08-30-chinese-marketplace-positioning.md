# Chinese Marketplace Positioning Implementation Plan

历史归档（2026-08-30）：保留当时的文档设计、计划及原始语言，未完成勾选不代表当前状态。本文中的执行步骤和约束仅属于该历史任务；当前使用与文档导航见 [README](../../../README.md) 和 [文档索引](../../README.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Present `delegate` consistently in Chinese across the marketplace and plugin manifests without changing metadata or runtime behavior.

**Architecture:** Two manifest `description` fields communicate the same positioning at different lengths. The marketplace uses the full value proposition; the plugin manifest uses a concise equivalent. JSON syntax and the repository's manifest validator enforce the result.

**Tech Stack:** JSON, Python JSON parser, `/bin/bash scripts/validate.sh`.

---

### Task 1: Update the marketplace description

**Files:**
- Modify: `.claude-plugin/marketplace.json:10`

- [ ] **Step 1: Replace only the marketplace `description` value**

Set the plugin entry's `description` field to:

```json
"description": "把已决策的执行与查证工作委托给 Codex CLI，只带回结论；默认只读、必须确认、绝不自动派。"
```

Keep the marketplace name, owner, plugin name, and source unchanged.

- [ ] **Step 2: Parse and inspect the changed field**

Run:

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
rg -n -F '把已决策的执行与查证工作委托给 Codex CLI，只带回结论；默认只读、必须确认、绝不自动派。' .claude-plugin/marketplace.json
```

Expected: JSON parsing succeeds and the exact description appears once.

### Task 2: Update the plugin description

**Files:**
- Modify: `plugins/delegate/.claude-plugin/plugin.json:4`

- [ ] **Step 1: Replace only the plugin `description` value**

Set the field to:

```json
"description": "将已决策的执行工作委托给 Codex CLI：默认只读、需用户确认、不自动派。"
```

Keep the plugin `name` and `version` unchanged.

- [ ] **Step 2: Parse and inspect the changed field**

Run:

```bash
python3 -m json.tool plugins/delegate/.claude-plugin/plugin.json >/dev/null
rg -n -F '将已决策的执行工作委托给 Codex CLI：默认只读、需用户确认、不自动派。' plugins/delegate/.claude-plugin/plugin.json
```

Expected: JSON parsing succeeds and the exact description appears once.

### Task 3: Validate and commit the manifest-only change

**Files:**
- Verify: `.claude-plugin/marketplace.json`
- Verify: `plugins/delegate/.claude-plugin/plugin.json`
- Verify: `scripts/validate.sh`

- [ ] **Step 1: Run repository validation**

Run:

```bash
/bin/bash scripts/validate.sh
```

Expected: `validate: ok`.

- [ ] **Step 2: Check the change scope**

Run:

```bash
git diff --check
git diff -- .claude-plugin/marketplace.json plugins/delegate/.claude-plugin/plugin.json
```

Expected: no whitespace errors; only the two `description` values differ.

- [ ] **Step 3: Commit the two manifest files**

```bash
git add .claude-plugin/marketplace.json plugins/delegate/.claude-plugin/plugin.json
git commit -m "docs: localize marketplace positioning"
```

Expected: the commit contains exactly the two manifest files.
