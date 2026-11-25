# 实施计划：reviewer-selection

<!-- spec-guard: review approved -->

日期：2026-11-24。规格：[spec/reviewer-selection.md](../../spec/reviewer-selection.md)（用户 2026-11-24 批准，原话「批准」）。任务：[todo.md](todo.md)。用法草案：[s110-design-review](../../spec/usage/s110-design-review.md) M1。依赖 [design-review-criteria](../design-review-criteria/plan.md)（同一 PR 发版、共用接口 1.7）与已完成的 detection。

## 架构决定

- **选择是纯函数。** 新建 `reviewer_select.py`：`VENDORS = {'codex': 'openai', 'claude-code': 'anthropic'}`；`order(author)` 给候选顺序；`choose(author, checks)` 逐家调用传入的检查（返回 `None` 表示可用、或固定诊断码），得到 `(backend 或 None, selection, diagnostics)`；`describe(backend, author, selection)` 生成报告的 `reviewer` 对象。不碰进程与文件，测试穷举。
- **真实检查包现有预检。** `reviewer_select.real_checks()`：Codex 用 `backend.check_detailed()`；Claude Code 用与 `review_doctor.py --backend claude-code` 相同的 `native_temporary` + `NativeRunner.runtime_preflight()` + `claude_review.preflight()`，用完清理临时目录，只返回固定码。doctor 与审查路由共用这一份。
- **参数与路由。** `delegate_backend.py` 的 `--backend` 加 `auto`、新增 `--author-host`；`delegate_cli.review_arguments()` 按 P1、E4 校验（退出 64）。`review()` 取完上下文后：`auto` → `choose()`；选中则把 `args.backend` 定为它并照原路由走；都不可用 → `base_report` 生成「未审」报告（`conditions_missing`、`no_reviewer_available` 加各家诊断、`backend_started=false`），退出 127。选择结果放进 `context['reviewer']`，`base_report()` 从这里取，占位报告也带。
- **体检。** `review_doctor.py` 新增 `--reviewers [--json]`：调用 `real_checks()`，按规格 E5 输出文本或 `delegate.reviewers/v1` JSON；原有三种用法不变。
- **接口升 1.7。** `interface.json`：`interface` 改 `1.7`；`review.reviewer`、`doctor.reviewers` 按规格第 6 条；`report` 稳定字段加 `reviewer`。连同 design-review-criteria 的 `profiles` 一起构成 1.7。
- **执行方式。** 串行，在主会话写；每个行为任务先写测试并确认红，再实现。本模块在 design-review-criteria 完成后开工。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Checkpoint 1（report）→ Task 5
→ Checkpoint 2（gate：复审；本地提交须你另行明确同意）→ Checkpoint 3（gate：交付验收，含推送与开 PR 的授权请求）
```

## Task 1：选择逻辑

**描述：** 新建 `test-reviewer-select.py`（注入假检查）并确认红，再新建 `reviewer_select.py` 的纯函数部分；套件登记进 `scripts/validate.sh` 与 `scripts/tests/test-validation-discovery.py`。

**验收条件：** RS-01、RS-02（两个方向 × 三种可用组合的后端、`selection`、`same_vendor`）；`describe()` 在显式后端时给 `explicit`，有无 `--author-host` 分别为布尔值与 `null`（RS-05 的纯函数部分）；只查需要的家（先选中就不查第二家）。

**验证：** `python3 -B plugins/delegate/tests/test-reviewer-select.py`、`python3 -B scripts/tests/test-validation-discovery.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/reviewer_select.py`、`plugins/delegate/tests/test-reviewer-select.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`。**规模：** S。

## Task 2：参数、路由与报告

**描述：** 先在 `test-review-cli.py`、`test-review-result.py` 写用例确认红，再改 `delegate_backend.py`、`delegate_cli.py`、`review_result.base_report()`。端到端用 PATH 里的假 `codex`／去掉 `codex` 控制 Codex 可用性；Claude Code 可用性在测试里用环境开关让 `real_checks()` 返回固定码（只在测试环境变量下生效，参考现有 `FIXTURE_*` 写法；正式运行不读）。

**验收条件：** RS-03（「未审」端到端：退出 127、字段与诊断、模型未启动）；RS-04（`auto` 选中 Codex 跑桩，`reviewer` 与 `backend` 一致，其余与显式 `--backend codex` 相同）；RS-05（显式后端的 `reviewer`）；RS-06（参数错误退出 64）；RS-07（占位报告带 `reviewer`）。

**验证：** `python3 -B plugins/delegate/tests/test-review-cli.py`、`test-review-result.py`、`test-review-backends.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/reviewer_select.py`、上述三个测试文件。**规模：** M。

## Task 3：体检 `--reviewers`

**描述：** 先写用例确认红（注入假检查覆盖三种情况与 `--json`），再改 `review_doctor.py`。

**验收条件：** RS-08；不带新参数时原有输出不变（现有 doctor 用例不改断言）。

**验证：** `python3 -B plugins/delegate/tests/test-review-backends.py`（或新增的 doctor 套件，需登记进总验证）

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/review_doctor.py`、`plugins/delegate/tests/test-review-backends.py`。**规模：** S。

## Task 4：接口 1.7

**描述：** 先改 `test-interface.py` 期待 1.7、`review.reviewer`、`doctor.reviewers`、稳定字段 `reviewer` 并确认红，再改 `interface.json`。

**验收条件：** RS-09；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 2、Task 3。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`（含 RS-10：不带新参数时现有套件不改断言通过）、两项 plugin validate、`git diff --check`；把命令与结果记入 todo 后继续。

## Task 5：文档同步

**描述：** 插件中英文 README 与 `commands/review.md`、`commands/doctor.md` 加 `auto`、`--author-host`、`--reviewers`、`reviewer` 字段与「未审」读法；根中英文 README 第 228 行一带改为「写代码的会话绝不审自己的东西」的说法；`spec/integration-interface.md` 及英文页补 1.7 指向（只加不改）；中英文待发行说明加本项并把标题定为 0.12.0 的发版标题（两个模块合写）；新建英文合同 `docs/en/SPEC-reviewer-selection.md`。

**验收条件：** RS-11 逐项核对，位置记入 todo。

**验证：** `verify-artifacts`、`git diff --check`、逐项核对记录。

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`plugins/delegate/commands/review.md`、`plugins/delegate/commands/doctor.md`、`README.md`、`README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/en/SPEC-reviewer-selection.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审

文档同步完成后对当前树跑一遍总验证，再交你复审实际 diff，重点是选择顺序、「未审」报告和 README 的说法替换。你认可后重新记录 integration-interface 的批准标记；**本地提交是独立授权项**，只有你在这一步明确同意才提交。

## Checkpoint 3（gate）：交付验收

在最终交付树上重跑总验证、两项 plugin validate、`git diff --check`；按最终验收格式报告 RS-01～RS-11，列实际改动文件与越界检查。两个模块的推送与开 PR 在这里一并请你授权；发版 0.12.0、通知 ecosystem-lead 与 sg-coord 另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 测试用的可用性开关漏进正式运行 | 高 | 开关只在显式测试环境变量下生效，单独用例断言正式环境下不读 |
| Claude 预检留下临时目录 | 中 | 与 doctor 同一清理逻辑；清理未核实时按现有规则保留并报固定码 |
| 选择结果和真正执行的后端不一致 | 中 | 选中后只改 `args.backend` 再走原路由；端到端断言 `reviewer.backend == backend` |
| README 说法替换遗漏 | 低 | 全仓 grep「自审」逐处核对，记入 todo |

## 开放问题

- 无。

## 修订：Claude Code 探测期限放宽（2026-11-26）

**状态：** 用户 2026-11-26 批准本节，原话「批准，开始实现」。授权范围：本会话改代码、测试与文档并跑免费验证，做到 Checkpoint B 停下；审查用额度、提交、PR、合并、发版另行确认。

规格：[spec/claude-review.md](../../spec/claude-review.md)「Claude Code 探测期限放宽」节（用户 2026-11-26 批准，原话「批准；Q1 15 秒；Q2 不重试」）。对应 todo 的 Task 6、Task 7。

### 架构决定

- **期限常量**：`claude_review.py` 新增 `PROBE_DEADLINE = 15`，`_probe` 改用它；三个探测共用，`review --backend claude-code` 的预检和 auto 选择都走这里。
- **阶段码随检查结果带出**：检查函数的返回约定从「`None` 或一个固定码」扩为「`None`、一个固定码，或一组固定码（主码在前）」。`claude_check` 遇到带 `stage` 的 `PreflightError` 时返回 `(主码, 阶段码)`；`choose` 把一组码依次追加进诊断；`doctor --reviewers` 只显示主码，输出格式不变。
- **执行方式**：两处改动都只有几行，本会话直接写，不派 Codex（固定开销不值）。审查按 #22991 用 `/delegate:review --backend claude-code`（同厂商审查），会用 Claude 额度。

### 顺序

```text
Task 6.1 → Task 6.2 → Task 6.3 → Checkpoint A（report）→ Checkpoint B（gate：审查与提交）→ Task 7（gate，发版后）
```

### Task 6.1：期限 15 秒（CR-22）

- **描述**：`test-claude-review.py` 加用例：假调用器记录三个探测拿到的期限，应为 `[15, 15, 15]`；返回 `timed_out` 时仍报 `probe_timed_out` 加阶段码、`backend_started=false`。先确认失败，再改常量。
- **验证**：`python3 -B plugins/delegate/tests/test-claude-review.py`。
- **文件**：`plugins/delegate/scripts/claude_review.py`、`plugins/delegate/tests/test-claude-review.py`。**规模**：XS。

### Task 6.2：auto 选择带阶段码（CR-23）

- **描述**：`test-reviewer-select.py` 加用例：检查返回 `(probe_timed_out, probe_stage_help)` 时，`choose` 的诊断依次含这两个码，`--backend auto` 的「未审」报告 `diagnostics` 为 `no_reviewer_available` 加这些码；`claude_check` 遇 `PreflightError('probe_cleanup_unverified', stage=...)` 返回两码、遇 `authentication_missing` 只返回一码；`doctor --reviewers` 的 `diagnostic` 只显示主码。先确认失败，再改 `reviewer_select.py`、`review_doctor.py`。
- **验证**：`python3 -B plugins/delegate/tests/test-reviewer-select.py`、`python3 -B plugins/delegate/tests/test-review-backends.py`。
- **文件**：`plugins/delegate/scripts/reviewer_select.py`、`plugins/delegate/scripts/review_doctor.py`、`plugins/delegate/tests/test-reviewer-select.py`（必要时 `test-review-backends.py`）。**规模**：S。

### Task 6.3：文档

- **描述**：英文规格 `docs/en/SPEC-claude-review.md` 补同一节；中英待发行说明补一节（变更、影响面、验证）；todo 记录。
- **文件**：`docs/en/SPEC-claude-review.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`、`tasks/reviewer-selection/todo.md`。**规模**：XS。

### Checkpoint A（report）：`validate.sh --quick` 与全量各跑一次，`git diff --check`、产物校验通过，记进 todo。

### Checkpoint B（gate）：`/delegate:review --backend claude-code` 审全部 diff（用 Claude 额度），阻断先修；之后提交、PR、合并逐项经用户确认。

### Task 7（gate）：发版后用安装版去掉 Codex 连续跑 3 次 U2（CR-24，用模型额度），再交用户判定 M1。

### 风险

- 期限放宽后真卡住时 auto 和 doctor 最多多等 30 秒：规格已接受（最坏 45 秒）。
- 返回约定扩成「一组码」可能漏改调用方：调用方只有 `choose` 和 `doctor --reviewers` 两处（已 grep），各有用例覆盖。
