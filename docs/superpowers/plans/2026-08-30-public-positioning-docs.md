# Public Positioning Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a concise public design document that explains delegate's problem, routing rule, operating flow, safety boundaries, and deliberate scope.

**Architecture:** `DESIGN.md` is the public positioning document. `README.md` remains the installation-and-usage entry point and receives one link. Existing `SPEC-*.md` files remain the engineering contracts.

**Tech Stack:** Markdown, repository-relative links, `/bin/bash scripts/validate.sh`.

---

### Task 1: Create the public design document

**Files:**
- Create: `DESIGN.md`
- Reference: `README.md:1-39`, `capability-map.md:1-42`, `SPEC-channel.md:5-17`, `SPEC-detection.md:5-18`, `SPEC-routing.md:5-37`

- [ ] **Step 1: Write the document around the five public questions**

Create `DESIGN.md` in Chinese with this structure:

```markdown
# delegate 的设计理念与边界

## 它为什么存在
## 唯一的分流判据：决策是否已定
## 从提议到验收的工作流
## 不可违反的安全与控制边界
## 它不试图成为什么
```

Use only established claims: context-economics mismatch; settled decisions versus open trade-offs; availability detection → proposal → explicit confirmation → Codex execution → concise result/Git evidence; default read-only; per-turn explicit `--write`; no automatic delegation; silent fallback; and process-log isolation. Link to `README.md`, `capability-map.md`, and the three `SPEC-*.md` files for details.

- [ ] **Step 2: Check the required structure and absence of a stale comparison table**

Run:

```bash
for heading in '它为什么存在' '唯一的分流判据：决策是否已定' '从提议到验收的工作流' '不可违反的安全与控制边界' '它不试图成为什么'; do
  rg -F -- "$heading" DESIGN.md
done
rg -n -i 'github|竞品|competitor' DESIGN.md
```

Expected: all headings are found; the final command produces no output.

- [ ] **Step 3: Commit the document**

```bash
git add DESIGN.md
git commit -m "docs: add public design positioning"
```

### Task 2: Add the README entry point

**Files:**
- Modify: `README.md:3-4`
- Reference: `DESIGN.md`

- [ ] **Step 1: Add one link after the opening positioning sentence**

Insert this paragraph after the sentence ending in “只把结论带回来。” and before `## 它解决什么`:

```markdown
设计理念、工作流与边界见 [DESIGN.md](DESIGN.md)。
```

Do not rewrite the existing pain-point explanation, routing table, installation instructions, commands, or limitations.

- [ ] **Step 2: Verify the exact link and surrounding README structure**

Run:

```bash
rg -n -F '设计理念、工作流与边界见 [DESIGN.md](DESIGN.md)。' README.md
sed -n '1,12p' README.md
```

Expected: the link appears once between the introduction and `## 它解决什么`.

- [ ] **Step 3: Commit the README link**

```bash
git add -p README.md
git commit -m "docs: link public design from readme"
```

Stage only the new top-of-file link hunk. Leave the pre-existing module-count
change unstaged.

### Task 3: Validate the documentation change

**Files:**
- Verify: `DESIGN.md`, `README.md`, `scripts/validate.sh`

- [ ] **Step 1: Check local Markdown link targets resolve**

Run:

```bash
for target in README.md capability-map.md SPEC-channel.md SPEC-detection.md SPEC-routing.md DESIGN.md; do
  test -f "$target"
done
```

Expected: exit status 0.

- [ ] **Step 2: Run repository validation**

Run:

```bash
/bin/bash scripts/validate.sh
```

Expected: `validate: ok`.

- [ ] **Step 3: Review the final change set**

Run:

```bash
git diff HEAD~2..HEAD --check
git log -2 --oneline
```

Expected: no whitespace errors; the two documentation commits are visible.
