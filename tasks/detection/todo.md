# Tasks: detection

计划见 [`plan.md`](plan.md)。断言编号对应 [`../../SPEC-detection.md`](../../SPEC-detection.md) 的 Testing Strategy 表。

---

## Task D1: hook 骨架与「零足迹」

**Description:** 建 `hooks/hooks.json`、`hooks/detect.sh` 和 `tests/test-detection.sh`。**先做性质 1**：没装 Codex 的机器上必须静默退 0、零输出。这条不成立的话后面都不用做。

**Acceptance criteria:**
- [ ] `detect.sh` 支持 `--print`（人看的）与 hook 模式（输出 JSON 或什么都不输出）
- [ ] 断言 10：`PATH` 里没有 codex → hook 模式**退出 0 且 stdout 完全为空**
- [ ] `hooks.json` 注册 SessionStart 与 UserPromptSubmit，路径用 `${CLAUDE_PLUGIN_ROOT}`
- [ ] `hooks.json` 里的命令即使脚本缺失也不报错（照 spec-guard 的写法留兜底）

**Verification:**
- [ ] `/bin/bash scripts/validate.sh` 退出 0
- [ ] `/bin/bash plugins/delegate/tests/test-detection.sh` 退出 0
- [ ] 变异：把「零输出」那条去掉 → 断言 10 必须变红

**Dependencies:** channel 的 T1/T2（复用 validate.sh 与 stub-codex）
**Files:** `plugins/delegate/hooks/hooks.json`, `plugins/delegate/hooks/detect.sh`, `plugins/delegate/tests/test-detection.sh`
**Scope:** S

---

## Task D2: 三级探测阶梯

**Description:** 实现三级判据，每一级失败给出**不同且可执行**的原因。第 2 级是重点：`command -v` 为真不代表跑得起来。

**Acceptance criteria:**
- [ ] 断言 1：三级全过 → 可用
- [ ] 断言 2：wrapper 不可执行 → 不可用，原因指向 wrapper
- [ ] 断言 3：`codex` 不在 PATH → 不可用
- [ ] 断言 4：`codex` 在 PATH 但 `--version` 失败 → 不可用，提示含 `npm install -g @openai/codex@latest`
- [ ] 断言 5/6：`auth.json` 不存在 / 存在但为空 → 不可用，提示去登录
- [ ] `auth.json` 路径可用 `CODEX_AUTH_FILE` 覆盖（**测试绝不碰真实 `~/.codex/`**）

**Verification:**
- [ ] 6 条断言全绿
- [ ] 变异：把第 2 级换成只查 `command -v` → 断言 4 必须变红（这是真实故障的形状）

**Dependencies:** D1
**Files:** `plugins/delegate/hooks/detect.sh`, `plugins/delegate/tests/test-detection.sh`
**Scope:** S

---

## Task D3: 缓存

**Description:** SessionStart 探一次写 `${TMPDIR}/delegate/detection.json`，UserPromptSubmit 只读。**缓存坏了等于没缓存**——重探，不报错。

**Acceptance criteria:**
- [ ] 断言 7：缓存新鲜 → **不再调用 codex**（用 `stub-codex` 的调用日志为空来证明）
- [ ] 断言 8：缓存 `checkedAt` 超过 8 小时 → 重探（调用日志有一次）
- [ ] 断言 9：缓存文件是非法 JSON → 重探，不崩，退出 0
- [ ] 缓存文件写在 `${TMPDIR}` 下，**不写进任何项目目录**

**Verification:**
- [ ] 3 条断言全绿
- [ ] 变异：让缓存永不过期 → 断言 8 必须变红
- [ ] 手工确认跑完之后项目目录里没有新增文件

**Dependencies:** D2
**Files:** `plugins/delegate/hooks/detect.sh`, `plugins/delegate/tests/test-detection.sh`
**Scope:** M

---

## Task D4: 输出契约

**Description:** hook 的 stdout **要么为空、要么是合法 JSON**。非 JSON 会被宿主拒绝，**而且失败是静默的**——这是最难发现的一类故障。

**Acceptance criteria:**
- [ ] 断言 11：把 hook 的 stdout 喂给 `python3 -c 'json.load(sys.stdin)'`，空则跳过，非空必须解析成功
- [ ] 断言 12：构造一个探测内部失败点（比如缓存目录不可写）→ 仍退出 0、不注入噪音
- [ ] JSON 结构与 spec-guard 一致：`hookSpecificOutput.hookEventName` / `additionalContext`
- [ ] 注入的内容**只有事实**，不含「你应该派给 Codex」这类建议（那是 routing 的活）

**Verification:**
- [ ] 2 条断言全绿
- [ ] 变异：在输出前面多打一行普通文本 → 断言 11 必须变红

**Dependencies:** D3
**Files:** `plugins/delegate/hooks/detect.sh`, `plugins/delegate/tests/test-detection.sh`
**Scope:** S

---

## Task D5: 接入体检 doctor

**Description:** 按需跑的体检。除了安装与登录，重点查一件每轮 hook **不该**查的事：`~/.codex/AGENTS.md` 里有没有会让非交互委托死锁的流程编排规则。

**Acceptance criteria:**
- [ ] `hooks/doctor.sh` + `commands/doctor.md`（`allowed-tools: Bash`，脚本按 `${CLAUDE_PLUGIN_ROOT}` 引用）
- [ ] 断言 13：AGENTS.md 含「等确认 / 先出方案 / 不要直接开始改代码」这类模式 → 报告风险并给出修法（加交互式条件）
- [ ] 断言 14（**反向**）：AGENTS.md 干净 → **不报**
- [ ] 断言 15：没有 `~/.codex/AGENTS.md` → 不报错
- [ ] AGENTS.md 路径可覆盖，测试用临时文件，**绝不读用户真实的那份**

**Verification:**
- [ ] 3 条断言全绿，**15 条全绿**
- [ ] `/bin/bash scripts/validate.sh` 通过
- [ ] 变异：把「干净就不报」改成「总是报」 → 断言 14 必须变红

**Dependencies:** D4
**Files:** `plugins/delegate/hooks/doctor.sh`, `plugins/delegate/commands/doctor.md`, `plugins/delegate/tests/test-detection.sh`
**Scope:** M

---

## Checkpoints

- [x] **E（D1–D2）** 没装 Codex 时零输出退 0；三级阶梯每级可单独复现，尤其「`command -v` 为真但 `--version` 失败」
- [ ] **F（D3–D4）** 缓存命中不再调 codex；损坏缓存与内部失败点下仍退 0 且输出可被 `json.load` 解析
- [ ] **G（D5）** 15 条断言全绿；doctor 对含「等确认」的 AGENTS.md 报风险、对干净的不报
