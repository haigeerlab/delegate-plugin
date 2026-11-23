# 实施计划：design-review-criteria

<!-- spec-guard: review approved -->

日期：2026-11-24。规格：[spec/design-review-criteria.md](../../spec/design-review-criteria.md)（用户 2026-11-24 批准，原话「批准」）。任务：[todo.md](todo.md)。用法草案：[s110-design-review](../../spec/usage/s110-design-review.md) M1（与 reviewer-selection 共用）。依赖已完成的 [review-snapshot-recheck](../review-snapshot-recheck/plan.md)。

## 架构决定

- **profile 随上下文走。** `delegate_cli.py` 解析 `--profile default|design`（只能一次），取完上下文后写进 `context['profile']`（默认档不写，保证默认档的上下文与提示词逐字不变）。访客路径本来转发除 `files` 外的全部上下文字段，不另开通道。
- **判据常量与提示词。** `review_context.py` 新增 `DESIGN_CRITERIA`（规格「design-v1 判据全文」逐字）与 `DESIGN_INSTRUCTION`；`task_prompt()` 在 `profile == 'design'` 时用 `DESIGN_CRITERIA` 替换 `SEVERITY_CRITERIA` 并在 `Task:` 前加 `DESIGN_INSTRUCTION`。另加 `criteria_name(context)` 返回 `severity-v1`／`design-v1`，供报告与复审共用。
- **降级集中在 `content_result()`。** design 档对每条发现按规格「实现方案」第 3 条处理：第二轮 → `second_round`；否则阻断且（位置核不上或文件不是参考文件）→ `no_code_evidence`；位置核不上不再让 `verified` 为假。参考文件 = 快照里有、但不被 `scope` 选中的文件（用 `review_context.selected()` 判断）。默认档代码路径不动。
- **报告与复审。** `base_report()` 加顶层 `criteria`；`delegate_backend.context_failure()` 的占位经 `base_report()` 同样带上。`review_recheck.check_scope()` 加判据比对（老报告缺字段按 `severity-v1`）。
- **接口先不升号。** `interface.json` 的 `review` 下加 `profiles`，`report` 稳定字段加 `criteria`；`interface` 号留给 reviewer-selection 一起升 1.7，两个模块同一个 PR 发版。
- **执行方式。** 串行，在主会话写（用户 2026-11-23 定：实现类 task 自己写）；每个行为任务先写测试并确认红，再实现。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Checkpoint 1（report）→ Task 5
→ Checkpoint 2（gate：复审；本地提交须你另行明确同意）→ Checkpoint 3（gate：交付验收）
```

## Task 1：`--profile` 参数与 design 提示词

**描述：** 先写测试确认红，再实现。`delegate_cli.py` 加参数与校验、`--dry-run` 预览显示 `profile`、`criteria`；`review_context.py` 加两个常量、`criteria_name()` 与 `task_prompt()` 分支。

**验收条件：** DR-01（`test-review-context.py` 直接测 `task_prompt()`；Codex、Claude Code、访客三条路径从桩里截取提示词：design 档带 `DESIGN_CRITERIA` 与 `DESIGN_INSTRUCTION`、不带 `SEVERITY_CRITERIA`，默认档与 0.11.0 逐字相同）；DR-07（`--profile` 重复、非法值退出 64；预览字段）。

**验证：** `python3 -B plugins/delegate/tests/test-review-context.py`、`test-review-execution.py`、`test-claude-review.py`、`test-review-guest.py`、`test-review-cli.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/scripts/review_context.py`、上述五个测试文件。**规模：** M。

## Task 2：降级与 `criteria` 字段

**描述：** 先写测试确认红，再改 `review_result.py` 的 `content_result()` 与 `base_report()`。

**验收条件：** DR-02（参考文件真实行保持 `blocking`；指向被审方案、行号不存在、`line` 为空 → `suggestion` + `no_code_evidence`，其余字段原样）；DR-03（design 档位置核不上不让整轮失败；默认档同样输入仍 `failed`／`review_incomplete`）；DR-04（第二轮新发现全为 `suggestion` + `second_round`，`recheck.items` 照旧）；DR-05（顶层 `criteria` 两档取值，取上下文前失败的占位也有）。

**验证：** `python3 -B plugins/delegate/tests/test-review-result.py`、`test-review-execution.py`

**依赖：** Task 1（`criteria_name()`）。**文件：** `plugins/delegate/scripts/review_result.py`、上述两个测试文件。**规模：** M。

## Task 3：复审判据一致与端到端

**描述：** 先写测试确认红，再改 `review_recheck.check_scope()`。`test-review-cli.py` 加端到端：临时仓库里 `--profile design --paths design.md --spec code.py`，桩后端第一轮返回一条指向 `code.py` 真实行的阻断与一条指向 `design.md` 的阻断。

**验收条件：** DR-06（上一轮判据不同、老报告缺字段按 `severity-v1` → `previous_report_scope_mismatch`、退出 127、不启动模型）；DR-09（端到端报告里两条分别为 `blocking` 与降级的 `suggestion`，`criteria=design-v1`）。

**验证：** `python3 -B plugins/delegate/tests/test-review-recheck.py`、`test-review-cli.py`

**依赖：** Task 2。**文件：** `plugins/delegate/scripts/review_recheck.py`、上述两个测试文件。**规模：** S。

## Task 4：接口声明

**描述：** 先改 `test-interface.py` 期待 `review.profiles` 与稳定字段 `criteria` 并确认红，再改 `interface.json`；`interface` 号不动。

**验收条件：** DR-08；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 2。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`（含 DR-10：现有套件不改断言通过）、两项 plugin validate、`git diff --check`；把命令与结果记入 todo 后继续。

## Task 5：文档同步

**描述：** 插件中英文 README「对外接口」加「技术方案审查（`--profile design`）」条目与读法（`criteria`、`downgraded`、必须用 `--spec` 带参考文件）；`commands/review.md` 的参数说明加 `--profile`；`spec/integration-interface.md` 及英文页在 1.6 指向句后补 `profiles` 指向（只加不改）；中英文待发行说明加本项；新建英文合同 `docs/en/SPEC-design-review-criteria.md`。

**验收条件：** DR-11 逐项核对，位置记入 todo；integration-interface 改动后 `verify-artifacts` 报「批准后已修订」属预期，Checkpoint 2 交你复审。

**验证：** `verify-artifacts`、`git diff --check`、逐项核对记录。

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`plugins/delegate/commands/review.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/en/SPEC-design-review-criteria.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审

文档同步完成后对当前树跑一遍总验证，再交你复审实际 diff，重点是降级判定、默认档不变的证据和 integration-interface 的改动。你认可后重新记录 integration-interface 的批准标记；**本地提交是独立授权项**，只有你在这一步明确同意才提交。

## Checkpoint 3（gate）：交付验收

在最终交付树上重跑 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、两项 plugin validate、`git diff --check`；按最终验收格式报告 DR-01～DR-11 的结果、证据位置、未验证项、实际改动文件与越界检查。推送与开 PR 等 reviewer-selection 也完成后，两个模块一个 PR、一起发 0.12.0，届时另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 默认档被波及 | 高 | 默认档不写 `context['profile']`；提示词用 0.11.0 原文断言；现有套件不改断言 |
| 参考文件判断错（把被审文件当证据） | 中 | 用与快照选择相同的 `selected()` 判断，单元测试覆盖被审文件、参考文件、两者重叠 |
| 降级掩盖真问题 | 中 | 只改 `severity`，原文与 `downgraded` 原因保留，测试断言其余字段不变 |
| 两个模块中间状态被发版 | 低 | 本模块不升接口号；两个模块同一 PR 发版 |

## 开放问题

- 无。
