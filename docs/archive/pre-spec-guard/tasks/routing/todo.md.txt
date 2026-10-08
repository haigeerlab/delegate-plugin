# Tasks: routing

历史归档：本文保留早期实现时的方案与勾选状态，部分命令、认证判据、性能或测试约定已过时。当前合同见 [模块规格](../../SPEC-routing.md)，使用入口见 [README](../../README.md)。本文不作为当前任务清单。

计划见 [`plan.md`](plan.md)。断言编号对应 [`../../SPEC-routing.md`](../../SPEC-routing.md) 的 Testing Strategy 表。

---

## Task R1: route.sh —— 注入与零足迹

**Description:** 读 `detection` 写的缓存，可用才注入一行路由指针；不可用、缓存缺失或损坏一律**零注入**。**不做任何分类**。

**Acceptance criteria:**
- [ ] R1 断言：缓存说不可用 → 零注入
- [ ] R2 断言：缓存缺失 → 零注入（不猜）
- [ ] R3 断言：缓存说可用 → 一行合法 JSON
- [ ] R4 断言：注入内容含「等用户确认」之意，**不含**「我这就派」这类越闸措辞
- [ ] R5 断言：任何情况的 stdout 为空或可被 `json.load` 解析
- [ ] R6 断言：缓存损坏/不可读 → 退出 0、零噪音
- [ ] `route.sh` **不重新实现探测** —— 只读缓存（判据只能有一份实现）
- [ ] `hooks.json` 增加 route.sh 的 UserPromptSubmit 注册，脚本缺失不报错

**Verification:**
- [ ] `/bin/bash plugins/delegate/tests/test-routing.sh` 退出 0
- [ ] 变异：让不可用时也注入 → R1 必须变红
- [ ] 变异：注入里加一句「我这就派给 Codex」→ R4 必须变红

**Dependencies:** detection 的 D3（缓存）
**Files:** `plugins/delegate/hooks/route.sh`, `plugins/delegate/hooks/hooks.json`, `plugins/delegate/tests/test-routing.sh`
**Scope:** S

---

## Task R2: SKILL.md —— 判据与纪律

**Description:** 分流表落成 skill。**判断的依据是「这活里还有没有没定的决策」**，不是「难不难」。

**Acceptance criteria:**
- [ ] R7 断言：SKILL.md 含分流表的六类活（审查 / 摸结构 / 定位 / 单 task 实现 / 批量机械改动 / 不该派的）
- [ ] R8 断言：含「不许自动派」的明文
- [ ] 三条回来之后的纪律写明：不 `cat` 整个日志、`--write` 必看 git 验收块、`--write` 需用户当轮明确要求
- [ ] frontmatter 的 description 写得能被匹配到（参照 spec-guard 的经验：措辞决定会不会被加载）

**Verification:**
- [ ] 2 条断言全绿
- [ ] 变异：删掉「不许自动派」那句 → R8 必须变红

**Dependencies:** R1
**Files:** `plugins/delegate/skills/delegate-routing/SKILL.md`, `plugins/delegate/tests/test-routing.sh`
**Scope:** S

---

## Task R3: eval propose-not-auto

**Description:** **最重要的一条**：喂一个明显该派的任务，验模型**说了要委托什么**、且**没有自己调**。

**Acceptance criteria:**
- [ ] 三种结局：通过 / 不通过 / **没跑起来**（退出码 0 / 1 / 2）
- [ ] `--scaffold-only` 免费建脚手架并自检 hook 是否激活
- [ ] `--selftest` 喂已知输入给判决器自己（免费，进 `validate.sh`）
- [ ] `evals/_preflight.sh` 核对「装着的插件内容 == 仓库内容」，不一致就拒跑
- [ ] 「没有自动调」判**桩的调用日志**（文件系统）；「提议了」判 transcript ——
      这个不对称要在脚本注释里写明理由

**Verification:**
- [ ] `--selftest` 通过并接进 `validate.sh`
- [ ] `--scaffold-only` 通过
- [ ] 真跑一次通过

**Dependencies:** R2
**Files:** `evals/_preflight.sh`, `evals/propose-not-auto.sh`, `scripts/validate.sh`
**Scope:** M

---

## Task R4: eval routing-fitness

**Description:** 差分。两组只差一个变量：任务里还有没有没定的决策。

**Acceptance criteria:**
- [ ] 处理组（决策已定、只剩执行）→ 应当提议
- [ ] 对照组（还需取舍，比如「这两个方案选哪个」）→ **不应当**提议
- [ ] **对照组同时充当脚手架自检**：它要是也提议了，处理组的结果无从归因，
      这时给「没跑起来」而不是结论
- [ ] `--selftest` + `--scaffold-only`（免费）

**Verification:**
- [ ] `--selftest` 通过并接进 `validate.sh`
- [ ] 真跑一次，两组结果分开

**Dependencies:** R3
**Files:** `evals/routing-fitness.sh`, `scripts/validate.sh`
**Scope:** M

---

## Checkpoints

- [x] **H（R1–R2）** 9 条确定性断言全绿；不可用时零注入；注入不含越闸措辞
- [x] **I（R3–R4）** 两个 eval 的免费部分通过并接进 validate；真跑一次 `propose-not-auto` 通过
