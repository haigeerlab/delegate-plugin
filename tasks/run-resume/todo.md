# 任务清单：run-resume

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-resume.md)。
授权：用户 2026-10-24 对 Plan 原话“批准”。范围为 Task 1–Task 7 的本地实现与免费验证，做到 Checkpoint 4 停下；Checkpoint 3 付费实测、提交、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：`run_state.py` 纯函数与单元测试
- [x] Task 2：结果行与 `--resumable`
- [x] Checkpoint 1（report）：可续跑运行到位
- [x] Task 3：`--resume`
- [x] Task 4：保留清理与接口 1.1
- [x] Checkpoint 2（report）：免费验证全绿
- [x] Task 5：命令说明与 README
- [x] Task 6：合同指向与待发行说明
- [x] Checkpoint 3（gate）：付费真实实测（已执行；只读续跑写入一项未过，见记录）
- [x] Task 8：可续跑运行固定审批方式（规格 R1）
- [x] Checkpoint 3c（gate）：已发布 v0.5.3 只读路径实测
- [x] Task 9：所有执行调用固定审批方式（代码与测试）
- [x] Task 10：R2 的文档同步
- [x] Checkpoint 3b（gate）：重测只读续跑与当前只读 run
- [x] Task 7：总验证与记录
- [x] Checkpoint 4（gate）：交付前人工验收

## 记录

**Task 1（2026-10-24）：** RED：`python3 -B plugins/delegate/tests/test-run-resume.py` 8 项均因 `ModuleNotFoundError: No module named 'run_state'` 失败。GREEN：新增 `run_state.py` 后 8 项通过（含 `../x` 等非法 runId、标记不在第一行、软链接拒绝、0600 权限、排他占位）。

**Task 2（2026-10-24）：** RED：新增 7 项桩集成测试，5 项失败（`unrecognized arguments: --resumable`、普通 run 无结果行）。GREEN：改 `delegate_capabilities.py`（`resume` 事实提前到本 task，供参数校验用）、`delegate_backend.py`、`codex-exec.sh` 后 15 项通过。`delegate_cli.py` 经核对无需改动（run 子命令直接复用 `backend.parse`）。

**Checkpoint 1（2026-10-24，report）：** `/bin/bash plugins/delegate/tests/test-channel.sh` 24 通过 / 0 失败（第 16 项逐字 argv 与提示词断言未改仍通过）；`test-channel-regressions.py`、`test-backend.py`、`test-review-cli.py`、`test-command-migration.py`、`test-interface.py`、`test-review-backends.py` 均 OK。

**Task 3（2026-10-24）：** 续跑分支的 shell 代码在 Task 2 的同一次改动里已写入，因此新增 4 项续跑测试无法对“缺实现”显示红，直接 19 项通过。改用变异抽查证明测试有效（每项单独改坏、跑测试、再还原并 `cmp` 核对）：去掉 `-c sandbox_mode` → 2 项失败；不校验写模式 → 2 项失败；不做 `.resumed` 占位 → 1 项失败；可续跑仍带 `--ephemeral` → 1 项失败。还原后全绿。

**Task 4（2026-10-24）：** RED：`test-interface.py` 新断言 `'1.0' != '1.1'` 失败；清理测试因 `20261001000000.0.state.json` 未删除失败。GREEN：清理一并删除 `.state.json`、`.resumed`；`interface.json` 升 1.1；`scripts/validate.sh` 注册 `run-resume`，`scripts/tests/test-validation-discovery.py` 夹具清单补同名一项（连带改动，断言不变）。`test-interface.py` 8 项、`test-run-resume.py` 20 项、`test-review-cli.py`、发现回归均 OK；两项 `claude plugin validate` 均 `Validation passed`。

**Checkpoint 2（2026-10-24，report）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0，`validate: ok`。

**Task 5（2026-10-24）：** `run.md` 更新 `argument-hint`，新增结果行、可续跑用法与答复和授权纪律；`help.md` 补两条示例和一句用法；插件中英文 README 新增「可续跑委托 / Resumable delegation」一节，「对外接口」补 1.1 的 `run.resume`。

**Task 6（2026-10-24）：** channel、integration-interface 中英文合同各新增一句指向 run-resume，原条款未改；中英文 `unreleased.md` 各记一条。能力图「目标」段经核对无需补句（「不新增后台编排」仍成立）。`git diff --check` 通过，总验证重跑 `validate: ok`。

**Checkpoint 3 前的总验证复核（2026-10-24）：**

- 首次重跑退出 1，有两处失败：
  - `test-command-migration.py`：`help.md` 渲染后 4057 字节，超过 Codex 4000 字节上限。原因是本模块在 Task 5 加的内容，已压缩并删去一条示例，复测 OK。
  - `test-channel-regressions.py` 的 `test_timeout_kills_descendant_before_it_can_write_marker` 偶发失败：`run_codex.py` 第 29 行 `os.killpg(..., SIGKILL)` 抛出 `PermissionError`。本模块未改 `run_codex.py`。用 `git archive HEAD` 导出改动前副本，两份代码交替各跑 60 次：HEAD 失败 1/60，当前 0/60（另有一轮当前 1/30、HEAD 0/30）。判定为既有的时序竞态（TERM 后进程组只剩僵尸时 macOS 的 `killpg` 返回 EPERM），不在本模块范围，列为后续事项。
- 修正后重跑：见交付验收记录。
- `verify-artifacts.sh`：4 通过 · 1 警告 · 0 失败。警告是 `spec/integration-interface.md` 批准后已修订（Task 6 新增一行指向句），需用户复审后重新记录批准。

**Checkpoint 3（2026-10-25，gate，付费实测）：** 用户授权原话“授权实测”。Codex CLI 0.162.1，本机默认配置（`approval_policy = "on-request"`、`approvals_reviewer = "guardian_subagent"`、`sandbox_mode = "workspace-write"`）。临时仓库建在家目录 `~/delegate-rr10-probe-20261025000410`，三步任务，第 3 步的报告格式留作待定。

- 第 1 轮 `run --resumable`（只读），runId `20261025000415.68561`：`status=needs-input resumable=true`，退出 0。答复首行是 `NEED_USER:`，并且先完成了第 1、2 步（beta、5 行），未改文件。状态文件 `sessionId=01a16ea7-…` 与日志头一致。
- 第 2 轮 `run --resume 20261025000415.68561 -- "选 B。请把报告写进 report.md…"`，新 runId `20261025000437.70629`：`status=done resumable=true`，退出 0。
  - 成立：上下文接上了（直接用了 beta、5）；`--` 分隔被接受；日志头显示 `sandbox: read-only`，说明 `-c sandbox_mode` 进入了配置。
  - **不成立**：只读续跑**写出了 `report.md`**。日志里 `python3 … write_text` 显示 “succeeded in 0ms”，没有任何审批事件。推断是本机 `approval_policy=on-request` 加 `guardian_subagent` 代批了越出沙箱的命令（推断，未核实；与调研第 8 节第 4 轮现象相同）。
- 结论：RR-10 中“只读续跑写文件被拒”**未通过**。按 Plan 停下，回到规格修订，不在实现里绕过。
- 善后：`~/.codex/config.toml` 实测前后 sha256 均为 `ef71ded1…`，无新增信任记录；临时仓库已删除。Codex 会话文件由 Codex 自行保留，未读、未删。

**规格 R1 与 Plan 修订批准（2026-10-25）：** 用户对修订后的 Spec 和 Plan 原话“批准”（此前对修订方案原话“选 A”）。授权范围：Task 8 的本地实现与免费验证，做到 Checkpoint 3b 停下；重测、提交、PR、发版另行授权。

**Task 8（2026-10-25）：**
- RED：`test-run-resume.py` 加入审批参数断言后，2 项失败（`test_resumable_run_needs_input`、`test_resume_passes_session_answer_and_original_settings`）。
- GREEN：`codex-exec.sh` 在可续跑与续跑时加入 `-c 'approval_policy="never"'`，普通 run 不加。20 项通过；普通 run 另有断言确认参数里没有这一项。
- `/bin/bash plugins/delegate/tests/test-channel.sh` 24 通过 / 0 失败；`test-command-migration.py` OK（`help.md` 未改）。
- `run.md` 与中英文 README 各补一句说明。
- `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0；`git diff --check` 通过。

**规格 R2 与 Plan 修订批准（2026-10-25）：** 用户对 R2 修订后的 Spec 和 Plan 原话“批准”。授权范围：Task 9、Task 10 的本地实现与免费验证。Checkpoint 3c、3b 的付费实测、提交、PR、发版另行授权。

**Task 9（2026-10-25）：**
- RED：新增或改动的断言有 4 处失败：
  - `test-review-execution.py` 的 `test_codex_review_never_uses_a_configured_approver`；
  - `test-review-backends.py` 的 `test_codex_run_never_uses_a_configured_approver`（只读、写入两个子用例）；
  - `test-run-resume.py` 中普通 run 的整段 argv 断言。这条是本模块新写的，从“不含”改为“含”。
- GREEN：`codex-exec.sh` 改为一律传 `-c 'approval_policy="never"'`；`review_execution.py` 的 Codex 调用加同一项。
- 结果：`test-review-execution.py`、`test-review-backends.py`、`test-run-resume.py`、`test-channel-regressions.py`、`test-backend.py`、`test-review-cli.py` 均 OK；`test-channel.sh` 24 通过 / 0 失败；既有断言未改。

**Task 10（2026-10-25）：**
- `run.md` 与中英文 README 改为“所有 run 与 Codex 审查固定 `approval_policy="never"`”，写明写模式下越出沙箱的命令会被拒；同时去掉只针对可续跑模式的旧说法。
- `spec/claude-review.md` 及英文页各加一段指向 R2；中英文 `unreleased.md` 各补一句。
- 验证：`test-command-migration.py` OK（`help.md` 未改）；`scripts/validate.sh` 退出 0；两项 `claude plugin validate` 通过；`git diff --check` 通过。

**Checkpoint 3c（2026-10-25，gate，付费实测，RR-13 前半）：** 用户授权原话“授权 3c 和 3b”。用 `git archive v0.5.3` 导出已发布版本（其中不含任何 `approval_policy` 参数），本机配置同前（`on-request` + `guardian_subagent`）。临时仓库 `~/delegate-rr13-probe-20261025002201`，只含 `a.txt`。

- **v0.5.3 只读 run**（提示词：在仓库根目录创建 probe-run.txt…）：退出 0，未写出文件，`git status` 为空。日志头为 `approval: on-request`、`sandbox: read-only`。日志显示 Codex 只执行了一条检查文件是否存在的只读命令，答复说明“由于你要求不要修改文件，且沙箱为只读，我未尝试写入”。
  - **注意：** 是 v0.5.3 提示词开头的“不要修改文件”让模型没有尝试写入，沙箱和代批这一层**没有被考验到**。R1 的首次实测里，可续跑提示词没有这句话，写入就被放行了，因此不能据此证明只读 run 在技术上一定拦得住。
- **v0.5.3 Codex review**（`--paths a.txt`，任务文本要求创建 probe-review.txt）：`execution_status=completed`、`review_outcome=no_findings_in_scope`，未写出文件，`git status` 为空。review 带 `--ignore-user-config` 与 `features.shell_tool=false`，没有执行命令的工具。私有目录只保存摘要，无事件流可逐条核对。
- 善后：`~/.codex/config.toml` 哈希不变（`ef71ded1…`），临时仓库已删除。

**Checkpoint 3b（2026-10-25，gate，付费实测，RR-10 重测与 RR-13 后半）：** 用户授权原话“授权 3c 和 3b”。使用当前源码，临时仓库 `~/delegate-rr10b-probe-20261025002327`，三步任务与 Checkpoint 3 相同。

- 第 1 次 `run --resumable`（只读），runId `20261025002328.21825`：日志头 `approval: never`、`sandbox: read-only`。结果 `status=needs-input resumable=true`，先完成第 1、2 步，未改文件。
- 第 2 次 `run --resume 20261025002328.21825 -- "选 B。请把报告写进 report.md…"`，runId `20261025002349.24424`：日志头 `approval: never`、`sandbox: read-only`。结果 `status=done`，**未写出 `report.md`**，`git status` 为空；上下文接上了（直接用了 beta、5）。日志里没有执行任何命令，Codex 说明“当前环境仅允许读取文件，无法写入”后直接放弃。
- 第 3 次普通只读 run，用与 3c 相同的提示词，runId `20261025002411.26363`：日志头 `approval: never`。结果未写出文件，只执行了一条检查文件是否存在的只读命令。
- 判定：RR-10“只读续跑写文件被拒”按“文件未写出、`git status` 为空”这一结果成立；RR-13 后半成立。**限制：** 三次都是模型自己没有尝试写入，没有出现“写入命令被操作系统拒绝”的直接证据，审批方式为 `never` 时沙箱的技术拦截本身未被直接考验。与 R1 首次实测对比：在 `on-request` + `guardian_subagent` 下，模型尝试写入并成功；在 `never` 下，模型不再尝试。
- 善后：`~/.codex/config.toml` 哈希不变（`ef71ded1…`），临时仓库已删除。

**Task 7（2026-10-25，总验证与记录）：**
- `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0。
- `claude plugin validate .`、`claude plugin validate ./plugins/delegate` 均 `Validation passed`。
- `git diff --check` 通过。
- Spec Guard 0.84.1 `verify-artifacts.sh`：4 通过 · 1 警告 · 0 失败（`spec/integration-interface.md` 批准后新增一行指向句，待用户复审）。
- `phase-guard.sh`：BUILDING，下一 gate 为 Checkpoint 4。
- 未验证：
  - `approval_policy="never"` 时沙箱对写入命令的技术拦截，没有被直接考验到（见 3b）；
  - 写模式 run 在 `never` 下的真实行为（如 `git commit` 依赖前缀放行规则）没有实测；
  - Codex review 在本机配置下的事件流没有保存，无法逐条核对。
- 后续事项（不在本模块）：
  - `run_codex.py` 的 `killpg` EPERM 偶发竞态；
  - 已发布 `interface.json` 里 `readOnly: true` 的含义，由负责人报 ecosystem-lead。

**Checkpoint 4（2026-10-25，gate）：** 用户看过交付内容、实测结果、未验证项与后续事项后，原话“验收通过；integration-interface 复审通过”。`spec/integration-interface.md` 已重新记为批准。提交、推送、PR、版本号与发版仍未授权。
