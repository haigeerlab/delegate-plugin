# 实施计划：review-recheck

<!-- spec-guard: review approved -->

日期：2026-11-21。规格：[spec/review-recheck.md](../../spec/review-recheck.md)（用户 2026-11-21 批准，原话「批准」）。任务：[todo.md](todo.md)。来源：总账 S101 合并方案第 2 节。依赖已完成的 [review-severity](../review-severity/plan.md)。

## 架构决定

- **读取与取集合是纯函数。** 新建 `review_recheck.py`：`load(path)` 读字节、限 1 MiB、解析 JSON（重复键报错），返回 `(sha256, report)`；`blocking_set(report)` 校验结构并按规格顺序取阻断集合；`check_scope(previous, context)` 按 A9 比对。只抛 `ContextError` 固定码，不调 git、不碰模型。
- **复用上下文通道。** CLI 取完上下文后调用上述函数，把集合写进 `context['previous_findings']`，把 `{previous_report_sha256, previous_fingerprint}` 写进 `context['recheck_source']`。两者都随上下文走：`task_prompt()` 本来就把除 `files` 外的上下文以 JSON 数据附在提示词里，访客路径本来就转发这些字段且不做白名单（已核对 `review_transport.request_payload` 与 `review_guest_entry.py`）。
- **结构、校验、结论口径集中在 `review_result.py`。** `schema_for_context()` 在有 `previous_findings` 时加必填 `previous`；`content_result()` 校验 `previous` 并产出 `recheck.items`；`base_report()` 用 `context.get('recheck_source')` 给出 `recheck`（没有则 `null`）。现在 Claude 路径（`review_result.py:258`）和 Codex 路径（`review_execution.py:219`）各写了一遍「有发现即 findings」，改为共用一个小函数，按 A12 计算 `review_outcome`。
- **取上下文前失败不用改占位。** `base_report()` 用 `context.get()` 取 `recheck_source`，`delegate_backend.context_failure()` 的占位不带这个键时自然为 `null`；规格里「占位加 `recheck: null`」由此满足，测试照样断言。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Checkpoint 1（report）→ Task 6
→ Checkpoint 2（gate：复审与本地提交）→ Checkpoint 3（gate：交付验收）
```

## Task 1：读取上一轮报告、取阻断集合、比对范围

**描述：** 新建 `review_recheck.py` 与 `test-review-recheck.py`（纯函数测试，用手写的报告字典与临时文件），套件加进 `scripts/validate.sh` 与 `scripts/tests/test-validation-discovery.py`。

**验收条件：** 先红后绿；RC-02（只取 blocking／缺失／不认识，不取 suggestion；复审报告取未解决旧项加阻断新发现、不取 resolved；编号顺序；空集合；超过 100 条与字段超长报 `previous_report_invalid`）；RC-03 的判定部分（`paths`、`mode`、`commits` 下 `from` 不同报 `previous_report_scope_mismatch`，只有 `to` 不同通过）；RC-01 的读取部分（读不到、超 1 MiB、非 UTF-8、坏 JSON、重复键报 `previous_report_unreadable`；`schema_version`、未完成、没有结论、结构缺失报 `previous_report_invalid`）。

**验证：** `python3 -B plugins/delegate/tests/test-review-recheck.py`、`python3 -B scripts/tests/test-validation-discovery.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/review_recheck.py`、`plugins/delegate/tests/test-review-recheck.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`。**规模：** M。

## Task 2：`--previous-report` 参数接进审查

**描述：** `delegate_cli.py` 的 `review_arguments()` 加 `--previous-report`（重复报参数错误、空值报错）；`review()` 取完上下文后调用 Task 1 的函数，写入 `previous_findings` 与 `recheck_source`；失败走现有 `context_failure`（退出 127、模型不启动）；`--dry-run` 预览加 `previous_findings_count`。

**验收条件：** 先红后绿；RC-01 端到端（三个诊断码、退出 127、`backend_started=false`、`recheck` 为 `null`、诊断里没有路径和发现文字）；RC-03 在临时仓库上的一次 `commits` 正反例；RC-06 的 `--dry-run` 条数。

**验证：** `python3 -B plugins/delegate/tests/test-review-cli.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/tests/test-review-cli.py`。**规模：** S。

## Task 3：提示词说明

**描述：** `review_context.py` 加固定说明常量；`task_prompt()` 在 `previous_findings` 非空时把它放在判据之后、`Task:` 之前。集合为空或没有该键时提示词与现在逐字相同。

**验收条件：** 先红后绿；RC-06（两个后端的提示词都带说明与 `previous_findings` 数据、在 `Task:` 之前；没有时提示词不变）。

**验证：** `python3 -B plugins/delegate/tests/test-review-context.py`、`python3 -B plugins/delegate/tests/test-review-execution.py`

**依赖：** Task 2。**文件：** `plugins/delegate/scripts/review_context.py`、上述两个测试文件。**规模：** S。

## Task 4：输出结构、校验与报告

**描述：** `review_result.py`：`schema_for_context()` 在有集合时加必填 `previous`（`index` 枚举、`status` 枚举、`evidence` 字符串）；`content_result()` 校验每个 `index` 恰好一项、状态合法、证据 1～4000 字符，否则 `recheck_invalid`；产出 `recheck.items`（带原始发现）；`base_report()` 输出 `recheck`；结论口径抽成共用函数，Claude 与 Codex 两条路径都改用它。Codex 桩加一个带 `previous` 的模式。

**验收条件：** 先红后绿；RC-04（两个后端：合法通过；缺项、重复、未知编号、状态非法、证据为空 → `recheck_invalid` 与 `failed`）；RC-05（`recheck` 内容、A12 口径、失败时 `items` 为空但 sha 与指纹保留、不带参数时 `recheck` 为 `null` 且 schema 与 review-severity 后完全相同）。现有测试不改断言。

**验证：** `python3 -B plugins/delegate/tests/test-review-result.py`、`python3 -B plugins/delegate/tests/test-review-execution.py`

**依赖：** Task 3。**文件：** `plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/review_execution.py`、上述两个测试文件。**规模：** M。

## Task 5：接口

**描述：** `interface.json` 的 `review` 下加 `recheck`；`test-interface.py` 的整体比对加上它，`statuses` 与 `review_result` 里的枚举核对一致；报告稳定字段加 `recheck`。

**验收条件：** 先红后绿；RC-07；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 4。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`、两项 plugin validate、`git diff --check` 通过；把命令与结果记入 todo 后继续。

## Task 6：文档同步

**描述：**

- 插件中英文 README「对外接口」一节：加「复审对照上一轮（接口 1.5 起）」条目、报告字段表加 `recheck`、解读规则（只在有结论时看、本轮阻断集合怎么算、用两轮指纹核对复审的是修正后的补丁）。
- `spec/integration-interface.md` 及英文页：在 1.5 指向句之后补一句 `review.recheck` 的指向（只加不改）。
- 中英文 `docs/releases/unreleased.md` 加本项。
- 仓库根中英文 README 的故障排查表加 `previous_report_unreadable`、`previous_report_invalid`、`previous_report_scope_mismatch`（127）与 `recheck_invalid`。

**验收条件：** RC-08。integration-interface 改动后 `verify-artifacts` 会报「批准后已修订」，预期内，Checkpoint 2 交你复审后重新记录批准标记。

**验证：** `verify-artifacts`、`git diff --check`

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`、`README.md`、`README.en.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审与本地提交

交你复审实际 diff，重点是阻断集合的取法、结论口径的共用函数和 integration-interface 的指向句；通过后重新记录它的批准标记，`verify-artifacts` 恢复 0 警告，在本分支本地提交一次。

## Checkpoint 3（gate）：交付验收

按最终验收格式报告 RC-01～RC-09 的结果、证据位置和未验证项。推送、开 PR、v0.10.0 发版和通知 autopr-design 另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 上一轮报告被篡改或拿错 | 高 | 结构与长度校验、必须有结论、范围必须对得上；报告记 sha256 便于追查 |
| 上一轮发现文字里夹带指令 | 中 | 作为 JSON 数据放进提示词并明确只是数据；诊断只用固定码 |
| 两条路径的结论口径不一致 | 中 | 抽成一个共用函数，两条路径的测试都断言 |
| 提示词变长超过 Codex 内联上限 | 低 | 集合最多 100 条，每字段最多 4000 字符；超了照旧报 `codex_inline_input_limit` |
| 模型把没改的阻断判成已解决 | 中 | 免费测试证明不了；说明里要求拿不准写 `unresolved`，试点观察 |

## 开放问题

- 无。
