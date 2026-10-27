# 任务清单：run-check

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-check.md)。
授权：用户 2026-10-27 对 Plan 原话「批准」。范围：改本仓库文件、跑测试与构建、在本分支本地提交（每个模块收尾一次）；做到 run-rules 的 Checkpoint 2（gate）停下。付费调用、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：检查命令校验（照抄 S30）
- [x] Task 2：检查命令执行与结果
- [x] Task 3：`--authorized-by`
- [x] Task 4：接口与能力事实
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 5：授权纪律、命令说明、README 与待发行说明
- [x] Checkpoint 2（report）：模块收尾与本地提交

## 记录

**Plan 修订 R1（2026-10-27）：** 文档任务改写进 `plugins/delegate/references/run.md`，`run.md` 只改 argument-hint 与「必须先读」指示；用户原话见 plan.md。

**Task 1（2026-10-27）：** `test-run-check.py` 的校验测试先红（1 失败、4 错误），实现后通过。`run_check.py` 的 `SHELL_OPS`、判定方式与三条文案逐字照抄 #11736；测试也逐字写入这三条原文比对，并覆盖每个运算符在 token 开头和结尾两种位置，以及照抄的边界（`foo&&bar`、`a|b`、`/bin/sh -c '...'`、`2>&1`、单个 `&`、`$VAR` 放行；`>file` 拦截）。拒绝时 stderr 只输出文案、不加 `delegate: ` 前缀：`delegate_backend.py` 新增 `CheckRefused`，`delegate_cli.py`、`delegate_backend.py` 的打印处按类型决定是否加前缀；`codex-exec.sh` 被直接调用时也先校验一次。

**Task 2（2026-10-27）：** `CheckRunFlowTests` 8 项先红（3 失败、4 错误），实现后通过。检查命令经 `run_codex.py --report <runId>.check.cleanup <期限>` 执行：输出写 `.check.log`，结果写 `.check.json`，再并入结果文件的 `check` 字段；只在 `done` 时执行，在 Git 验收块之前；元数据块加「检查：…」一行。`.check.log`、`.check.cleanup`、`.check.json` 归入日志类后缀。偏离规格一处：为测试超时加了只能缩短期限的环境变量 `DELEGATE_CHECK_TIMEOUT_SECONDS`（写法同 `DELEGATE_TIMEOUT_SECONDS`，默认与上限都是 600 秒）。`unreaped` 只在单元层用 `status_of(125)` 验证，没有构造真实的回收失败。

**Task 2 回归中发现并修复的缺陷（2026-10-27）：** `.check.log` 也以 `.log` 结尾，run-continue 的 `cleanup` 把它当成一组日志的主文件计数和删除，导致多删（`test-run-continue.py` 的保留期测试变红）。第一次修成「只认 `<合法 runId>.log`」又让 channel 的 C20（日志名为 `fake-NNN.log`）漏删；最终规则为「以 `.log` 结尾且不以 `.check.log` 结尾」，与原来的计数口径一致。新增回归 `test_check_log_is_not_a_group_of_its_own`。`test-run-continue.py`、`test-backend.py`（live harness 内含 C20）、`test-channel.sh` 均通过。

**Task 3（2026-10-27）：** `AuthorizationFlowTests` 4 项先红（2 失败、2 错误），实现后通过。`run_state.py` 新增 `authorization_file`（`lstat` 拒软链接、非普通文件、空、超过 64 KiB，只算 sha256）与子命令 `authorization`；`check` 加第 7 个参数（本次的 sha256），状态文件记 `authorization`，链上已记录时不给或不同都拒绝 `authorization mismatch`；结果文件加 `authorization`（`file`、`in-turn`、`null`）；元数据块加「写入授权：…」。按 Plan 更新：`test-run-resume.py` 状态文件整体比对补上 `authorization: null`。

**Task 4（2026-10-27）：** `test-interface.py` 加 `run.check`、`run.writeAuthorization` 断言（期限与运算符直接对照 `run_check.py` 的常量，`run.write` 仍为 `"explicit"`），先红后绿；能力事实加 `check`、`writeAuthorization`（顺带把两行过长的字典拆成多行，内容不变）。

**Checkpoint 1（report，2026-10-27）：** `test-run-check.py`（17 项）、`test-run-result.py`、`test-run-continue.py`、`test-run-longrun.py`、`test-run-resume.py`、`test-run-timeout.py`、`test-backend.py`、`test-write-trust.py`、`test-review-backends.py`、`test-review-cli.py`、`test-channel-regressions.py`、`test-reap-fake-endpoint.py`、`test-command-migration.py`、`test-interface.py` 全部 OK；`test-channel.sh` 24 通过 / 0 失败；`git diff --check` 通过。

**Task 5（2026-10-27）：** 按 Plan 修订 R1，`--check`、`--authorized-by` 的用法与两条纪律（写入授权四条件、检查命令来源）写进 `references/run.md`；`run.md` 只在 argument-hint 与「必须先读」那句里加两个参数（`test-command-migration.py` 通过）；`delegate-routing` 的 SKILL.md 在「`--write` 必须用户在该轮明确要求」后加一句例外并指向参考文件（`test-routing.sh` 10 通过）；中英文 README 新增「检查与事先写入授权」一节与接口条目，中英文待发行说明同步。routing 规格的指向句按 Plan 留到 run-rules 的汇总任务。

**Checkpoint 2（report，2026-10-27）：** 总验证 `validate: ok`；两项 plugin validate 通过；`verify-artifacts` 4 通过；本地提交一次，未推送；`activeModule` 切到 `run-rules`。
