# v0.3.0 Release Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Chinese source text for a future `delegate` v0.3.0 GitHub Release.

**Architecture:** `docs/releases/v0.3.0.md` is the reviewable source of truth; it links to existing public docs and does not trigger a remote release.

**Tech Stack:** Markdown and `/bin/bash scripts/validate.sh`.

---

### Task 1: Add v0.3.0 release-body source

**Files:**
- Create: `docs/releases/v0.3.0.md`

- [ ] **Step 1: Write the Chinese Release body**

Include headings `# delegate v0.3.0` and `## 为什么存在`, `## 适合委托的工作`, `## 安全边界`, `## 安装与首次使用`, and `## 已知限制`. State only repository-supported facts: settled-decision routing, no automatic delegation, read-only default, explicit `--write`, process-log isolation, and the documented routing-evaluation limitation.

- [ ] **Step 2: Verify content and repository validation**

Run:

```bash
rg -n -F '# delegate v0.3.0' docs/releases/v0.3.0.md
/bin/bash scripts/validate.sh
```

Expected: title found and `validate: ok`.

- [ ] **Step 3: Commit the release body**

```bash
git add docs/releases/v0.3.0.md
git commit -m "docs: add v0.3.0 release notes"
```
