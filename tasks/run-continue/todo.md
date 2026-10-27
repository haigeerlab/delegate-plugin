# 任务清单：run-continue

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-continue.md)。
授权：用户 2026-10-27 对 Plan 原话「批准」。范围：改本仓库文件、跑测试与构建、在本分支本地提交（每个模块收尾一次）；做到 run-rules 的 Checkpoint 2（gate）停下。付费调用、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：校验的 continue 模式与按时间清理
- [x] Task 2：`--continue` 参数与执行
- [x] Task 3：接口与能力事实
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 4：命令说明、README 与待发行说明
- [x] Checkpoint 2（report）：模块收尾与本地提交

## 记录

**Plan 修订 R1（2026-10-27）：** 文档任务改写进 `plugins/delegate/references/run.md`，`run.md` 只改 argument-hint 与「必须先读」指示；用户原话见 plan.md。

**Task 1（2026-10-27）：** `test-run-continue.py` 的 `ContinueCheckTests`、`RetentionTests` 共 6 项先红，实现后通过。`run_state.py` 新增 `LOG_GROUPS`、`LOG_SUFFIXES`、`STATE_SUFFIXES`、`STATE_RETENTION_DAYS = 14` 与 `cleanup`（子命令 `cleanup <目录>`）；`check` 加可选的第 6 个参数 `continue`；`codex-exec.sh` 的内联清理改为调用该子命令。按 Plan 更新的现有断言：`test-run-resume.py` 的保留期测试（改名为 `test_retention_prunes_logs_but_keeps_recent_state`，新增断言：近期的 `.state.json`、`.resumed` 在日志被删后仍保留）；`test-run-timeout.py` 的保留期测试只列日志类后缀。另一处 Plan 未列：run-result 自己写的 `RetentionTests` 同样去掉 `.result.json`（它现在按时间清理）。三处都附了注释说明原因。

**Task 2（2026-10-27）：** `ContinueFlowTests` 5 项中 4 项先红（「`--resume` 遇到 done 仍按原文拒绝」本就成立）。`delegate_backend.py` 解析并转发 `--continue`，校验组合；`codex-exec.sh` 让 `--continue` 走续跑路径，只换校验模式（`continue`）与提示词（【下一个任务】），状态文件与结果文件记 `kind: "continue"`。偏离 Plan 两处：
- 规格写「`--resume` 与 `--continue` 共用占位」，但两者接受的状态互不相交（needs-input/timeout 与 done），同一 runId 上的另一个入口先被状态拒绝（`run not done` 或 `run not waiting for input`），走不到占位检查；测试按实际原因断言，占位共用由单元测试覆盖。
- `test-run-resume.py` 第 209 行的状态文件整体比对补上新增的 `kind` 字段，比对方式不变。

**Task 3（2026-10-27）：** `test-interface.py` 新增 `run.continue` 断言（并核对 14 天与 `run_state.STATE_RETENTION_DAYS` 相同），先红后绿；能力事实加 `continue`。

**Checkpoint 1（report，2026-10-27）：** `test-run-continue.py`（11 项）、`test-run-resume.py`、`test-run-timeout.py`、`test-write-trust.py`、`test-backend.py`、`test-review-backends.py`、`test-channel-regressions.py`、`test-reap-fake-endpoint.py`、`test-command-migration.py`、`test-interface.py` 全部 OK；`test-channel.sh` 24 通过 / 0 失败；`git diff --check` 通过。`test-run-result.py` 在这一轮里报过一次 1 个错误，没有留下输出；随后单独连跑 5 次（31 项）都通过，总验证里也通过，未能复现，原因不明，继续观察。

**Task 4（2026-10-27）：** 按 Plan 修订 R1：`--continue` 的用法与纪律写进 `references/run.md`；`run.md` 只在 argument-hint 加 `--continue`，并在「必须先读」那句里点名 `--continue`（渲染后不超过 4000 字节，`test-command-migration.py` 通过）。中英文 README、中英文待发行说明同步。`help.md` 只剩 29 字节余量，不改（Plan 原写「help.md 提示 `--resume` 遇到 done 改用 `--continue`」，这条提示改放在参考文件里）。

**Checkpoint 2（report，2026-10-27）：** 总验证 `validate: ok`（退出 0，无失败项）；两项 plugin validate 通过；`verify-artifacts` 4 通过；本地提交一次，未推送；`activeModule` 切到 `run-longrun`。
