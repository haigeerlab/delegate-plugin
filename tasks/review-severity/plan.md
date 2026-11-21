# 实施计划：review-severity

<!-- spec-guard: review approved -->

日期：2026-11-21。规格：[spec/review-severity.md](../../spec/review-severity.md)（用户 2026-11-21 批准，原话「批准；Q1 A」）。任务：[todo.md](todo.md)。来源：总账 S101 合并方案第 2 节。

## 架构决定

- **判据是一个常量。** `review_context.py` 新增 `SEVERITY_CRITERIA`（与规格「判据」一节逐字一致）和一段要求输出 `severity` 的固定说明；`task_prompt()` 把它们放在现有说明之后、`Task:` 之前。Codex 的 `codex_prompt()` 本来就以 `task_prompt()` 开头，不另改。
- **结构和校验只改一处。** `review_result.py` 的 `FINDING_FIELDS` 加 `severity`；`CONTENT_SCHEMA` 里为 `{'type': 'string', 'enum': ['blocking', 'suggestion']}`，必填；`content_result()` 校验取值，不对报 `finding_invalid`。两个后端都经 `content_result()`，所以一次覆盖。
- **现有测试的发现夹具补 `severity`。** `test-review-result.py`、`test-review-execution.py`、`test-review-guest-integration.py`、`test-interface.py` 里构造发现的地方共 5 处，加 `severity` 后旧夹具会被判 `finding_invalid`。这是随合同更新测试数据，不改任何断言；改动在 Task 2 里先红后绿时一并处理并逐处列出。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Checkpoint 1（report）→ Task 4 → Checkpoint 2（gate：复审与本地提交）
→ Checkpoint 3（gate：交付验收）
```

## Task 1：提示词带上判据

**描述：** `review_context.py` 新增常量 `SEVERITY_CRITERIA` 与固定说明，`task_prompt()` 在现有说明之后、`Task:` 之前加入。测试断言两个后端的提示词都逐字包含 `SEVERITY_CRITERIA`，`--task` 文字出现在判据之后；另断言常量与 `spec/review-severity.md` 「判据」代码块逐字一致（测试读规格文件，防止两处漂移）。

**验收条件：** 先红后绿；SV-03、SV-05。

**验证：** `python3 -B plugins/delegate/tests/test-review-context.py`、`python3 -B plugins/delegate/tests/test-review-execution.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/review_context.py`、`plugins/delegate/tests/test-review-context.py`、`plugins/delegate/tests/test-review-execution.py`。**规模：** S。

## Task 2：结构与校验

**描述：** `review_result.py` 的 `FINDING_FIELDS`、`CONTENT_SCHEMA` 加必填枚举 `severity`，`content_result()` 校验取值。新增测试：合法两值原样带出；缺失、大写、空串、第三种值、非字符串均判 `finding_invalid` 且 `execution_status=failed`；Claude 路径（`claude_report`）与 Codex 路径（`review_execution`）各至少一项；`schema_for_context()` 里 `severity` 为必填枚举、`additionalProperties` 仍为 `false`。现有 5 处发现夹具补 `severity`。

**验收条件：** 先红后绿；SV-01、SV-02；现有测试除夹具补字段外不改断言。

**验证：** `python3 -B plugins/delegate/tests/test-review-result.py`、`python3 -B plugins/delegate/tests/test-review-execution.py`、`python3 -B plugins/delegate/tests/test-review-guest-integration.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/review_result.py`、上述三个测试文件。**规模：** S。

## Task 3：接口 1.5

**描述：** `interface.json` 的 `interface` 改为 `"1.5"`，`review.report` 加 `severity`；`test-interface.py` 版本断言改 1.5，整体比对改名为 `test_interface_1_5_is_complete`（1.4 内容原样加 `review.report.severity`），`FINDING_FIELDS` 加 `severity`，核对 `criteria` 名为 `severity-v1`、`values` 与 `review_result` 的枚举一致。

**验收条件：** 先红后绿；SV-04；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 2。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`、两项 plugin validate、`git diff --check` 通过；把命令与结果记入 todo 后继续。

## Task 4：文档同步

**描述：**

- 插件中英文 README「对外接口」一节：`findings[]` 字段表加 `severity`，写取值、判据名 `severity-v1`、缺失或不认识按 `blocking`、只在有结论时才看、`unverified` 非空表示 U1 那类拿不准的阻断、严重程度不是合并许可。
- `spec/integration-interface.md` 及英文页：在 1.4 指向句之后加一句 1.5 的指向句（只加不改）。
- 中英文 `docs/releases/unreleased.md` 加本项。

**验收条件：** SV-06。integration-interface 改动后 `verify-artifacts` 会报「批准后已修订」，预期内，Checkpoint 2 交你复审后重新记录批准标记。

**验证：** `verify-artifacts`、`git diff --check`

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审与本地提交

交你复审实际 diff，重点是判据进提示词的位置和 integration-interface 的指向句；通过后重新记录它的批准标记，`verify-artifacts` 恢复 0 警告，在本分支本地提交一次。

## Checkpoint 3（gate）：交付验收

按最终验收格式报告 SV-01～SV-07 的结果、证据位置和未验证项（模型标注准确度靠试点观察，本模块不做付费实测）。推送、开 PR 另行授权；v0.10.0 发版要等 review-recheck 完成。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 判据在规格和代码里两处漂移 | 高 | Task 1 的测试直接读规格代码块比对常量 |
| 加必填字段后旧夹具大面积失败，被误当成放松断言 | 中 | 只给夹具补字段、逐处列出，不改断言 |
| 判据段让 Codex 提示词超过 1 MiB 内联上限 | 低 | 判据约 2 KB；上限检查不变，超了照旧报 `codex_inline_input_limit` |
| 模型不按判据标、或常把阻断标成建议 | 中 | 免费测试证明不了；试点观察，需要时出 `severity-v2` |

## 开放问题

- 无。
