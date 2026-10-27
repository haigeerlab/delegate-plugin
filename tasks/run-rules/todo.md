# 任务清单：run-rules（含 1.3 收尾）

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-rules.md)。
授权：用户 2026-10-27 对 Plan 原话「批准」。范围：改本仓库文件、跑测试与构建、在本分支本地提交（每个模块收尾一次）；做到 run-rules 的 Checkpoint 2（gate）停下。付费调用、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：`--rules-file` 校验与提示词拼接
- [x] Task 2：接口 1.3 完整形状
- [x] Task 3：命令说明、README 与待发行说明
- [x] Checkpoint 1（report）：1.3 免费验证全绿
- [x] Task 4：1.3 合同指向句汇总
- [x] Checkpoint 2（gate）：旧合同改动复审与本地提交
- [x] Checkpoint 3（gate）：1.3 付费合并实测（RU-07）
- [x] Checkpoint 4（gate）：交付验收

## 记录

**Plan 修订 R1（2026-10-27）：** 文档任务改写进 `plugins/delegate/references/run.md`，`run.md` 只改 argument-hint 与「必须先读」指示；用户原话见 plan.md。

**Task 1（2026-10-27）：** `test-run-rules.py` 5 项中 4 项先红（2 失败、2 错误；「不带参数时提示词不变」本就成立），实现后通过。新增 `run_rules.py`（校验：普通文件、非软链接、UTF-8、非空、无 NUL、≤16 KiB；生成规则段；结果只取路径、sha256、字节数）。`codex-exec.sh` 用 `run_rules.py section` 生成整段（以结束标记收尾，所以命令替换不会吃掉原文末尾的换行），普通与可续跑 run 放在前言之后、任务之前，续跑与接续放在最前，收尾轮不放；结果文件加 `rules`。

**Task 2（2026-10-27）：** `test-interface.py` 新增 `test_interface_1_3_is_complete`，对 `interface.json` 做整体相等比对（与 run-rules 规格文末汇总逐项一致），并核对 `maxBytes` 与 `run_rules.MAX_BYTES` 相同；先红后绿。能力事实加 `rules`。修复：本轮跑 `claude plugin validate ./plugins/delegate` 时发现 run-check 提交里 `run.md` 的 argument-hint 有嵌套双引号导致 frontmatter 解析失败（详见 run-check 的 todo），已改为 `--check <命令>`。

**Task 3（2026-10-27）：** `--rules-file` 的用法与「与 AGENTS.md 的关系」三条写进 `references/run.md`；`run.md` 只改 argument-hint。「必须先读」那句列出全部六个参数后渲染超过 4000 字节，改为点名 `--continue`、`--check`、`--authorized-by`（涉及授权纪律的三项）再加「等 1.3 参数」，argument-hint 仍列出全部参数，渲染后 3972 字节。中英文 README 新增「规则片段」一节与接口条目；中英文待发行说明加本项与「1.3 汇总」。

**Checkpoint 1（report，2026-10-27）：** 1.3 免费验证全集：`test-run-rules.py`、`test-run-check.py`、`test-run-result.py`（含真实 Codex 连本机假端点的用例，实际执行）、`test-run-continue.py`、`test-run-longrun.py`、`test-run-resume.py`、`test-run-timeout.py`、`test-backend.py`、`test-write-trust.py`、`test-review-backends.py`、`test-review-cli.py`、`test-channel-regressions.py`、`test-reap-fake-endpoint.py`、`test-interface.py`、`test-command-migration.py` 全部 OK；`test-channel.sh` 24 通过、`test-routing.sh` 10 通过；总验证 `validate: ok`；两项 plugin validate 通过；`git diff --check` 通过。

**Task 4（2026-10-27）：** 五个模块对旧合同的改动一次写完，中英文同步，原有条款只加不改：`spec/channel.md`（1.3 指向：`--json`、日志拆分、结果文件、`--timeout`）、`spec/run-resume.md`（修订记录 R4：A7 只放开期限、`--continue`、会话 ID 来源与状态文件新字段、状态类文件 14 天保留、Never 规则不变）、`spec/run-timeout.md`（1.3 指向：收尾轮 `--json`、`--timeout` 时 `T` 的来源、保留规则）、`spec/routing.md`（写入授权例外），以及四个英文对应页。`verify-artifacts`：4 通过、2 警告（run-resume、run-timeout「批准后已修订」，预期内，等 Checkpoint 2 复审）。总验证 `validate: ok`，两项 plugin validate 通过。

**Checkpoint 2（gate，2026-10-27）：** 用户复审 Task 4 的四个旧规格改动，原话「批准」。已重新记录 `spec/run-resume.md`、`spec/run-timeout.md` 的批准标记（`channel.md`、`routing.md` 没有标记，不补）；`verify-artifacts` 恢复 0 警告。本地提交一次，未推送。下一步停在 Checkpoint 3（gate）报付费合并实测计划。

**Checkpoint 3（gate，2026-10-27）：** 用户原话「批准，最多 6 次」。实际 4 次付费调用，记录见 `docs/verification/2026-10-27-delegate-1.3-merged-live.md`。计划第 2 步的设计有误（只读链不能 `--continue --write`），实测时改为先免费验证拒绝、再以写模式新起一条链，多用 1 次调用，仍在上限内。结果：结果文件字段、`usage.run` 差值、`--continue`、`--authorized-by`、`--check`、带 `--strict` 时首行标记压过 AGENTS.md 都成立；`--timeout 660` 的运行只跑了 500 秒，「超过 540 秒仍正常结束」未验证，按约定不补跑。`config.toml` 测前测后一致。

**Checkpoint 4（gate，2026-10-27）：** 用户交付验收原话「批准」。接口 1.3 五个模块全部完成，本地提交 `e44379f`～`74a76ce` 加本次勾选提交，均未推送。已知未验证：`--timeout` 下超过 540 秒的真实运行。推送、开 PR、版本号、发版与通知 module-crew 另行授权；发版前先告知 delegate 负责人。
