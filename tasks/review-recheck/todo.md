# 任务清单：review-recheck

计划：[plan.md](plan.md)；规格：[spec](../../spec/review-recheck.md)。
授权：用户 2026-11-21 对 Plan 原话「批准，开始实现」。范围：改本仓库文件、跑测试与构建、在本分支本地提交；做到 Checkpoint 2（gate）停下。推送、PR、发版与通知不在此授权内。

- [x] Task 1：读取上一轮报告、取阻断集合、比对范围
- [x] Task 2：`--previous-report` 参数接进审查
- [x] Task 3：提示词说明
- [x] Task 4：输出结构、校验与报告
- [x] Task 5：接口
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 6：文档同步
- [x] Checkpoint 2（gate）：复审与本地提交
- [ ] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-21）：** 新建 `test-review-recheck.py` 11 项，先红（模块不存在），新建 `review_recheck.py`（`load`、`blocking_set`、`check_scope`、`source`）后通过：读不到、超 1 MiB、非 UTF-8、坏 JSON、重复键、非对象 → `previous_report_unreadable`；没有结论、结构缺失、字段超长、超 100 条、旧项状态非法 → `previous_report_invalid`；只取 blocking／缺失／不认识，复审报告先取未解决旧项再取阻断新发现；`paths`、模式、`commits` 下 `from` 不同 → `previous_report_scope_mismatch`。套件登记进 `scripts/validate.sh` 与发现测试；撤掉夹具名时发现测试变红，恢复后变绿。

**Task 2（2026-11-21）：** `test-review-cli.py` 新增 `PreviousReportCLITests` 4 项，先红；`delegate_cli.py` 加 `--previous-report`（重复、空值退出 64）、取上下文后读入并写进 `previous_findings`／`recheck_source`、`--dry-run` 显示 `previous_findings_count`、帮助文字加一行。三个诊断码在真实审查与 `--dry-run` 下都退出 127、`backend_started=false`、执行器未被调用、输出不含文件路径与发现文字。一处测试自身问题：三个用例共用一个报告文件名，循环前被最后一次写入覆盖，改为各用各的文件名。

**Task 3（2026-11-21）：** `test-review-context.py` 新增 `RecheckPromptTests` 2 项、`test-review-execution.py` 新增 Codex 提示词 1 项，先红；`review_context.py` 加 `RECHECK_INSTRUCTION`，`task_prompt()` 在集合非空时把说明放在判据之后、`Task:` 之前，并且不再把 `recheck_source` 附进提示词、集合为空时不附 `previous_findings`，所以集合为空或没有该键时提示词与 review-severity 后逐字相同。

**Task 4（2026-11-21）：** `test-review-result.py` 新增 `RecheckReportTests` 6 项、`test-review-execution.py` 新增 Codex 端到端 2 项（经 `review --context … --previous-report …`），先红；`review_result.py` 加 `previous` 的 schema 与校验（缺项、重复、未知编号、状态非法、证据为空、多余键、整个缺失 → `recheck_invalid`、`failed`，`items` 为空但 sha 与上一轮指纹保留）、`base_report()` 输出 `recheck`、新增共用函数 `conclude()`，Claude 与 Codex 两条路径都改用它（Codex 那处原样逻辑删除）。另核对 `delegate_backend.py` 与 `review_transport.py` 里另两处设置结论的代码不受影响。现有测试未改断言。

**Task 5（2026-11-21）：** `test-interface.py` 整体比对加 `review.recheck`、稳定字段加 `recheck`、`statuses` 与 `review_result.RECHECK_STATUSES` 一致；先红后绿。`interface.json` 加 `review.recheck`。两项 plugin validate 通过。

**Checkpoint 1（report，2026-11-21）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0、`validate: ok`，Python 387 项（review-severity 后为 361，新增 26 项）；`claude plugin validate .` 与 `./plugins/delegate` 均通过；`git diff --check` 通过。

**Task 6（2026-11-21）：** 插件中英文 README 对外接口一节加「复审对照上一轮（接口 1.5 起）」条目、报告字段表加 `recheck`、解读规则补本轮阻断集合怎么算与两轮指纹核对；integration-interface 中英文各加一句 `recheck` 指向句（只加不改）；中英文 `unreleased.md` 加本项；仓库根中英文 README 故障排查表加四个诊断码。**超出 Plan 文件清单：** `commands/review.md`（参数提示与一段说明）和 `commands/help.md`（一行示例）也列着审查参数，一并补上。`git diff --check` 通过；`verify-artifacts` 4 通过、1 警告（integration-interface「批准后已修订」，预期内，等 Checkpoint 2 复审）。

**自查修复（2026-11-21，Checkpoint 1 之后）：** 看 diff 时发现：Claude 路径在合并内容之后才检查权限拒绝，`conclude()` 也可能因覆盖不全把审查降为 `failed`，这两种情况下 `recheck.items` 仍有内容，违反规格「审查失败时 `items` 为空数组」。先补测试 `test_failed_review_never_keeps_recheck_items`（权限拒绝、覆盖不全）并确认红，再加 `clear_recheck_items()`，在 `conclude()` 的失败分支、Claude 路径末尾和 `delegate_backend.py` 保存产物失败的降级分支调用；随后发现 `conclude()` 在超时／取消这类非完成状态下直接返回、同样会留下条目，一并改为清空并补一条断言（这条断言与修复同时写入，未单独确认先红）。`delegate_backend.py` 那一处没有单独测试（保存产物失败难以在免费测试里触发），按同一函数保证。修复后重跑：`validate: ok`，Python 388 项（比 Checkpoint 1 多这 1 项）；两项 plugin validate、`git diff --check` 通过。

**未验证：** 模型判断「已解决」的准确度（试点观察）；Codex／Claude 真实运行能否接受带 `previous` 的输出结构（付费，未测）；访客路径（一次性虚拟机）未运行，只靠上下文本来就整体转发。

**用法草案（2026-11-21）：** ecosystem-lead #21941 指出 S101 拆出两个模块却没有用法草案（spec-guard「用法草案」规则要求在第一个模块 Spec 之前审完）。补写 `spec/usage/auto-takeover-review.md`：入口 4 个、U1／U2、里程碑 M1 = review-severity, review-recheck；拆分核对无遗漏、无多余；对外接口与两份已批准 Spec 一致，Spec 未改。`verify-artifacts` 报用法草案结构正确。

**Checkpoint 2（gate，2026-11-21）：** 用户复审 review-recheck 改动、自查修复、integration-interface 指向句与补写的用法草案，原话「通过，本地提交」。已重新记录 `spec/integration-interface.md` 批准标记。本地提交一次，未推送；按拟稿回复 ecosystem-lead。下一步停在 Checkpoint 3（gate）交付验收。
