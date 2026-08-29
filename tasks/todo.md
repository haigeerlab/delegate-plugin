# Tasks: channel

计划见 [`plan.md`](plan.md)。断言编号对应 [`../SPEC-channel.md`](../SPEC-channel.md) 的 Testing Strategy 表。

---

## Task 1: 仓库骨架与校验器

**Description:** 建 marketplace 清单、插件清单、`scripts/validate.sh`。让「跑一条命令就知道仓库没坏」这件事从第一天就成立。

**Acceptance criteria:**
- [ ] `.claude-plugin/marketplace.json` 与 `plugins/delegate/.claude-plugin/plugin.json` 均为合法 JSON，含 `version`
- [ ] `validate.sh` 检查：JSON 语法、所有 `.sh` 的 `bash -n`、可执行位、`${VAR}` 写法（不许 `$VAR` 紧跟多字节）、不许 `cmd | grep -q`
- [ ] 喂一个已知坏输入（故意写 `$VAR中文`）时 `validate.sh` 非零退出

**Verification:**
- [ ] `/bin/bash scripts/validate.sh` 退出 0
- [ ] 手工注入坏输入后退出非 0，还原后回到 0

**Dependencies:** None
**Files:** `.claude-plugin/marketplace.json`, `plugins/delegate/.claude-plugin/plugin.json`, `scripts/validate.sh`
**Scope:** S

---

## Task 2: codex 桩与断言套骨架

**Description:** 建 `stub-codex` 和 `test-channel.sh`。桩由环境变量驱动：最终答复内容、退出码、往 stdout 吐多少过程文本、是否消费 stdin。断言套用 PASS/FAIL 计数，末行打「总计 N 通过 / M 失败」。**这是后面每个任务的验收载体，必须先有。**

**Acceptance criteria:**
- [ ] 桩把收到的完整 argv 写进一个可断言的调用日志
- [ ] 桩支持：`STUB_ANSWER` / `STUB_EXIT` / `STUB_STDOUT_BYTES` / `STUB_READ_STDIN`
- [ ] 断言套能把 `PATH` 指向桩，且**不触网**
- [ ] 空套跑出「总计 0 通过 / 0 失败」并退出 0

**Verification:**
- [ ] `/bin/bash plugins/delegate/tests/test-channel.sh` 退出 0
- [ ] 手工让桩 `STUB_EXIT=3`，确认调用日志里记下了 argv

**Dependencies:** T1
**Files:** `plugins/delegate/tests/stub-codex`, `plugins/delegate/tests/test-channel.sh`
**Scope:** S

---

## Task 3: 最小可用调用（只读端到端）

**Description:** `codex-exec.sh` 的第一版：接一个任务字符串，按四要素调用，过程输出落盘，只回最终答复。**本模块最高风险的部分，排在最前。**

**Acceptance criteria:**
- [ ] 调用含全部四要素：`env -u OPENAI_API_KEY`、`</dev/null`、`-o` + stdout 重定向、非交互 preamble
- [ ] 断言 1：桩吐 100KB 到 stdout → 调用方拿到的 stdout **不含**那 100KB
- [ ] 断言 2a（**反**）：`STUB_READ_STDIN=1` + stdin 是永不关闭的管道 + **不加** `</dev/null` → 桩阻塞
      —— 这条先证明「测法能复现真故障」，否则 2b 是空断言
- [ ] 断言 2b（**正**）：同样条件**加上** `</dev/null` → 桩在限时内完成
- [ ] 断言 10：桩收到 `--sandbox read-only`
- [ ] 断言 15/16：空任务或未知选项退出 **64**；以 `-` 开头的任务不被当成选项
- [ ] 输出末尾回报日志路径与「过程 N 字节 / 答复 M 字节」

**Verification:**
- [ ] `test-channel.sh` 新增 7 条断言全绿
- [ ] 断言 2a/2b 必须带超时上限，挂起要判失败而不是卡住套件
- [ ] **断言必须在 `/bin/bash` 下跑**：zsh 的 MULTIOS 会把多个输入重定向**拼接**
      而不是后者覆盖，在 zsh 里写这条会得出完全相反的结论（2026-08-29 实测踩到）

**Dependencies:** T2
**Files:** `plugins/delegate/scripts/codex-exec.sh`, `plugins/delegate/tests/test-channel.sh`
**Scope:** M

---

## Task 4: 失败路径要响

**Description:** 四种静默失败是这个模块存在的全部理由。让它们每一种都退出非 0，并在 stderr 给出可执行的下一步。

**Acceptance criteria:**
- [ ] 断言 3：`codex` 存在但 `--version` 失败 → 退出 **127** + 提示 `npm install -g @openai/codex@latest`
- [ ] 断言 4：`codex` 不在 PATH → 退出 127
- [ ] 断言 5：桩退出非 0 → 脚本退出非 0，stderr 回显日志尾部与完整日志路径
- [ ] 断言 6：桩退出 0 但答复文件为空 → **退出非 0**（不许把空当成功）

**Verification:**
- [ ] `test-channel.sh` 新增 4 条断言全绿
- [ ] 每条都同时断言退出码和 stderr 内容，不只断言其一

**Dependencies:** T3
**Files:** `plugins/delegate/scripts/codex-exec.sh`, `plugins/delegate/tests/test-channel.sh`
**Scope:** S

---

## Task 5: 模型与推理档透传

**Description:** `--model` / `--effort`。重点是**无效 slug 必须硬失败**——静默退回默认会让 `--model` 变成一句谎话。

**Acceptance criteria:**
- [ ] 断言 8：`--model X --effort high` → 桩收到 `-m X` 和 `-c model_reasoning_effort="high"`
- [ ] 断言 9：不传 → 桩**没有**收到 `-m`
- [ ] 断言 7：桩模拟无效 slug 的 400 → 脚本退出非 0
- [ ] 输出末尾回报实际使用的模型与推理档（不传时显示「配置默认」）
- [ ] 空数组展开写成 `${ARR[@]+"${ARR[@]}"}`（bash 3.2）

**Verification:**
- [ ] `test-channel.sh` 新增 3 条断言全绿
- [ ] `/bin/bash scripts/validate.sh` 通过（bash 3.2 静态检查）

**Dependencies:** T4
**Files:** `plugins/delegate/scripts/codex-exec.sh`, `plugins/delegate/tests/test-channel.sh`
**Scope:** S

---

## Task 6: `--write` 与 git 验收块

**Description:** 唯一有副作用的路径。输出必须带一段调用方能据以验收的客观证据——**因为模型的自述不可信**（实测撞到过自述说改了而 `git status` 是空的）。

**Acceptance criteria:**
- [ ] 断言 11：`--write` → 桩收到 `--sandbox workspace-write`
- [ ] 断言 12：git 仓库里 → 输出含基线 HEAD + `git status --short` + `git diff --stat`
- [ ] 断言 13：**非** git 目录 → 明说拿不到 diff，**不伪造验收块**
- [ ] 断言 14：跑前已有 N 个未提交变更 → 验收块把 N 报出来
- [ ] 默认仍是只读；`--write` 必须显式

**Verification:**
- [ ] `test-channel.sh` 新增 4 条断言全绿，**17 条全绿**
- [ ] `/bin/bash scripts/validate.sh` 通过

**Dependencies:** T5
**Files:** `plugins/delegate/scripts/codex-exec.sh`, `plugins/delegate/tests/test-channel.sh`
**Scope:** M

---

## Task 7: `/delegate` 命令与插件清单接线

**Description:** 把通道接成可用的斜杠命令，并把边界纪律写进命令文档——那些纪律靠模型读文档执行，不是靠代码。

**Acceptance criteria:**
- [ ] `commands/delegate.md` 的 `allowed-tools` 只放 `Bash(<脚本路径> *)`
- [ ] 文档写明：Bash timeout 设 600000；`--write` 必看验收块；**不要 `cat` 整个日志**
- [ ] 文档写明 `--write` 需用户当轮明确要求，Claude 不得自行升级
- [ ] `plugin.json` 正确声明 commands

**Verification:**
- [ ] `/bin/bash scripts/validate.sh` 通过（含清单一致性）
- [ ] 装进 user scope 后 `/delegate` 能跑通一次真实委托

**Dependencies:** T6
**Files:** `plugins/delegate/commands/delegate.md`, `plugins/delegate/.claude-plugin/plugin.json`
**Scope:** S

---

## Task 8: `--live` 真跑冒烟

**Description:** 桩验的是契约，`--live` 验的是契约**没和真 codex 漂移**。门控在 flag 后面，不进 `validate.sh`。

**Acceptance criteria:**
- [ ] `--live` 真调一次只读委托，答复非空
- [ ] 断言日志/答复体量比 **≥ 40×**
- [ ] 不带 `--live` 时这组被跳过且在输出里说明「跳过不代表通过」
- [ ] 前置检查 `codex --version` 与 `auth.json`，缺任一则报「**没跑起来**」而不是「不通过」

**Verification:**
- [ ] `/bin/bash plugins/delegate/tests/test-channel.sh --live` 通过
- [ ] 不带 flag 时套件仍全绿且明确标出跳过

**Dependencies:** T7
**Files:** `plugins/delegate/tests/test-channel.sh`
**Scope:** S

---

## Checkpoints

- [ ] **A（T1–T2）** `validate.sh` 通过；空套跑出总计行；桩可被环境变量驱动
- [ ] **B（T3–T4）** 只读委托端到端可用；100KB 过程输出不进 stdout；四种失败各自退非 0 且 stderr 有下一步 ← **最重要**
- [ ] **C（T5–T6）** 17 条断言全绿；`validate.sh` 通过
- [ ] **D（T7–T8）** `/delegate` 可用；`--live` 通过，体量比 ≥ 40×
