# 任务清单：run-longrun

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-longrun.md)。
授权：用户 2026-10-27 对 Plan 原话「批准」。范围：改本仓库文件、跑测试与构建、在本分支本地提交（每个模块收尾一次）；做到 run-rules 的 Checkpoint 2（gate）停下。付费调用、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：`--timeout` 参数、期限与结果字段
- [x] Task 2：接口与能力事实
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 3：命令说明、README 与待发行说明
- [x] Checkpoint 2（report）：模块收尾与本地提交

## 记录

**Plan 修订 R1（2026-10-27）：** 文档任务改写进 `plugins/delegate/references/run.md`，`run.md` 只改 argument-hint 与「必须先读」指示；用户原话见 plan.md。

**Task 1（2026-10-27）：** `test-run-longrun.py` 5 项。测试用一个 `python3` 垫片记录 `run_codex.py` 实际收到的期限参数（不比对源码文本）。第一次运行时垫片自身有 bug（占位符替换误伤了 `printf '%s'`），那次的失败不算先红证据；修好测试后临时换回改动前的三个脚本重跑，3 失败、2 错误，恢复后 5 项通过。实现：`delegate_backend.py` 校验 `--timeout`（541～7200 的十进制整数，否则 `delegate: --timeout must be an integer between 541 and 7200`、退出 64），与 `--review-context` 同用时拒绝；`codex-exec.sh` 再校验一次，带 `--timeout` 时 `T` 取该值、忽略环境变量；结果文件加 `timeoutSeconds`（不带时也写，值为默认算出的 `T`）。`run_state.deadlines` 本来就不限上限，不用改。
另：run-result 的 `test_forced_timeout_fallback_records_wrapup_and_cleanup` 原来给本模块留了占位断言（`timeoutSeconds` 不存在），按规格改为断言等于该测试的期限 4。

**Task 2（2026-10-27）：** `test-interface.py` 加 `run.longRun` 断言，先红后绿；能力事实加 `longRun`。

**Checkpoint 1（report，2026-10-27）：** `test-run-longrun.py`、`test-run-continue.py`、`test-run-result.py`（31 项）、`test-run-resume.py`、`test-run-timeout.py`、`test-backend.py`、`test-write-trust.py`、`test-channel-regressions.py`、`test-reap-fake-endpoint.py`、`test-command-migration.py`、`test-interface.py` 全部 OK；`test-channel.sh` 24 通过 / 0 失败；`git diff --check` 通过。RL-04 的回收回归（0.7.1 的两组测试）不改，仍通过。

**Task 3（2026-10-27）：** 按 Plan 修订 R1，`--timeout` 的用法与「后台调用要求」三条写进 `references/run.md`；`run.md` 只在 argument-hint 与「必须先读」那句里加 `--timeout`；中英文 README 新增「长任务」一节与接口条目，中英文待发行说明同步；`help.md` 不改（余量不足）。run-resume 的 A7 修订记录、run-timeout 与 channel 的指向句按 Plan 留到 run-rules 的汇总任务。

**Checkpoint 2（report，2026-10-27）：** 总验证 `validate: ok`；两项 plugin validate 通过；`verify-artifacts` 4 通过；本地提交一次，未推送；`activeModule` 切到 `run-check`。
