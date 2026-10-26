# 实施计划：run-resume

<!-- spec-guard: review approved -->

日期：2026-10-24。规格：[spec/run-resume.md](../../spec/run-resume.md)（用户 2026-10-24 批准，指纹 6954bad01627）。任务：[todo.md](todo.md)。
本计划覆盖免费的本地实现与验证，外加一次需单独授权的付费实测（Checkpoint 3）。提交、推送、PR、版本号与发版另行授权；发版前先告知 delegate 负责人，由其报 ecosystem-lead 判断影响。

## 架构决定

- 状态逻辑全部放进新增的 `run_state.py`（标准库），提供 runId 校验、会话 ID 提取、`NEED_USER:` 判定、状态文件读写、续跑占位和续跑前校验。`codex-exec.sh` 只调用它的子命令，shell 里不解析 JSON。
- 普通 run 的 Codex 调用一行不改；可续跑和续跑走新增分支。现有 `test-channel.sh` 第 16 项对 argv 和提示词的逐字断言保持原样，用来守住 RR-01。
- 新参数在 `delegate_backend.parse` 统一校验，转发给 `codex-exec.sh`；旧的直接调用 `codex-exec.sh` 的方式同样支持这两个参数。
- `delegate_capabilities.BACKENDS` 增加 `resume` 事实（codex 为真，claude-code 为假），作为 `interface.json` 中 `run.resume.backends` 的比对来源。
- 不改 `delegate-routing` skill：它只管何时提议委托；续跑由使用方按 `run.md` 调用。

## 顺序与依赖

Task 1 → Task 2 → Checkpoint 1 → Task 3 → Task 4 → Checkpoint 2 → Task 5 → Task 6 → Checkpoint 3 → Task 8 → Checkpoint 3c → Task 9 → Task 10 → Checkpoint 3b → Task 7 → Checkpoint 4。

2026-10-25 修订：Checkpoint 3 首次实测发现只读续跑仍能写文件，规格按 R1 修订，新增 Task 8 与 Checkpoint 3b；Task 1–6 的已完成记录保留。
同日规格按 R2 扩大到所有让 Codex 执行任务的调用，新增 Checkpoint 3c、Task 9、Task 10，并把 Checkpoint 3b 扩为同时验证当前源码的只读 run。
串行，在主会话做，不派子代理（每个 task 都小，派出去不省主会话轮次）。每个行为 task 先写测试并确认它红，再实现转绿。

## Task 1：`run_state.py` 纯函数与单元测试

**描述：** 新增 `run_state.py`，包含以下纯函数：

- `valid_run_id`：runId 格式校验；
- `session_id_from_log`：取日志里第一行 `session id: <uuid>`；
- `classify`：去掉开头空白后判断是否以 `NEED_USER:` 开头，返回状态和问题原文；
- `write_state` / `read_state`：0600 原子写入，拒绝软链接；
- `claim_resume`：排他创建 `.resumed`；
- `check_resume`：按规格拒绝表返回原因。

另外提供供 shell 调用的子命令入口。同时新增 `test-run-resume.py`，先写单元部分。

**验收条件：**
- 先红：模块不存在时，测试报缺模块失败；
- 再绿：每个函数的正反例都通过，包括：
  - 标记不在第一行时判为 `done`；
  - 非法 runId 如 `../x`、`1.2` 被拒；
  - 已存在 `.resumed` 时占位失败；
  - 状态文件权限为 0600。

**验证：** `python3 -B plugins/delegate/tests/test-run-resume.py`
**依赖：** 无。
**涉及文件：** `plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-resume.py`。
**规模：** S，2 文件。

## Task 2：结果行与 `--resumable`（RR-01、RR-02、RR-03）

**描述：** 先在 `test-run-resume.py` 加桩集成测试：临时 Git 仓库，PATH 指向 `stub-codex`，`STUB_STDOUT_TEXT` 模拟 `session id:` 日志头。然后实现：
- `delegate_backend.parse` 接受 `--resumable`，转发给 `codex-exec.sh`；
- `codex-exec.sh` 在 `--resumable` 时不传 `--ephemeral`，换成规格里的可续跑提示词；
- 成功后调 `run_state.py` 判定状态、写状态文件；
- 所有成功的 run 在 stdout 末尾输出结果行；
- 取不到会话 ID 时输出 `resumable=false`，并在 stderr 说明原因。

**验收条件：**
- 普通 run 的 argv 与提示词不变：`test-channel.sh` 原断言通过，新测试另外比对一次；
- 结果行格式正确；
- `--resumable` 的 argv 不含 `--ephemeral`，提示词含「先做不受待定决策影响的任务」；
- 状态文件字段齐全、权限 0600；
- `needs-input` 退出 0，答复完整输出；
- 失败、超时、空答复时不输出结果行，也不写状态文件。

**验证：**
- `python3 -B plugins/delegate/tests/test-run-resume.py`
- `/bin/bash plugins/delegate/tests/test-channel.sh`
- `python3 -B plugins/delegate/tests/test-channel-regressions.py`

**依赖：** Task 1。
**涉及文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/tests/test-run-resume.py`。
**规模：** M，4 文件。

## Checkpoint 1（report）：可续跑运行到位

把红绿输出和 `test-channel.sh` 结果记入 todo，然后继续。若普通 run 的现有断言变红，**停下报告**，不改旧断言迁就实现。

## Task 3：`--resume`（RR-04、RR-05、RR-06）

**描述：** 先写测试，再实现：
- `parse` 接受 `--resume <runId>`，校验参数组合：不能与 `--resumable`、`--model`、`--effort`、`--backend claude-code` 同用，答复不能为空；
- `codex-exec.sh` 的续跑分支依次做：`check_resume` 校验（状态、仓库根目录、写模式）→ `claim_resume` 占位 → 调用 `codex exec resume`；
  - 调用参数：`-c sandbox_mode=...`、沿用原来的 `-m` 和推理档、认证配置、`-o`、会话 ID、带用户答复的正文，stdin=/dev/null；
- 生成新 runId，写状态文件并带上 `parent`；
- 写模式输出 Git 验收块。

**验收条件：**
- 续跑 argv 与规格一致；
- 拒绝表每一行都退出 64，并且桩的调用日志为空；
- 写模式续跑输出验收块，只读续跑不输出；
- 能链式续跑：第二轮续跑第一轮返回的新 runId。

**验证：** `python3 -B plugins/delegate/tests/test-run-resume.py`
**依赖：** Task 2。
**涉及文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-resume.py`。
**规模：** M，4 文件。

## Task 4：保留清理与接口 1.1（RR-07、RR-08）

**描述：**
- 先写测试并确认它红：
  - `test-run-resume.py` 增加清理断言：超过 50 组时，状态文件和占位文件跟着日志一起删；
  - `test-interface.py` 增加 1.1 断言（`interface == "1.1"`、`run.resume` 与 `BACKENDS` 一致、两个 command 字段保持原值）。
- 再实现：
  - `codex-exec.sh` 的 `cleanup_process_logs` 删除同 runId 的 `.state.json` 和 `.resumed`；
  - `delegate_capabilities.BACKENDS` 增加 `resume`；
  - `interface.json` 改为规格中的 1.1 内容。
- 把 `run-resume` 加入 `scripts/validate.sh` 的 Python 套件清单，并同步 `scripts/tests/test-validation-discovery.py` 的夹具清单（上次 integration-interface 也需要这一处连带修改）。

**验收条件：**
- 新断言先红后绿，现有断言不改；
- 两项 plugin validate 通过；
- `test-review-cli.py` 中对 `BACKENDS` 的现有断言仍通过。

**验证：**
- `python3 -B plugins/delegate/tests/test-interface.py`
- `python3 -B plugins/delegate/tests/test-run-resume.py`
- `python3 -B plugins/delegate/tests/test-review-cli.py`
- `claude plugin validate ./plugins/delegate`

**依赖：** Task 3。
**涉及文件：** `plugins/delegate/interface.json`、`plugins/delegate/scripts/delegate_capabilities.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-interface.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`。
**规模：** M，6 文件，均为小改动。

## Checkpoint 2（report）：免费验证全绿

跑 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`，结果记入 todo，然后继续。若出现与本模块无关的既有失败，记录下来并停下报告。

## Task 5：命令说明与 README（RR-09 前半）

**描述：**
- `run.md`：
  - `argument-hint` 加入 `--resumable` 和 `--resume <runId>`；
  - 正文加入三件事：可续跑用法、结果行含义、答复与授权纪律（答复必须是用户原话或用户同意的转述；续跑写入的前提；`needs-input` 不是失败也不是批准）；
- `help.md`：补用法；
- 插件中英文 README：
  - 新增「可续跑委托」一节；
  - 「对外接口」一节补 1.1 与 `run.resume`，写明使用方读到 1.0 时按今天的做法处理。

**验收条件：** 中英文内容对应，字段名与规格一致，不出现私有项目名，不改其他章节。
**验证：** 逐项对照规格；`git diff --check`。
**依赖：** Task 4。
**涉及文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`。
**规模：** S，4 文件。

## Task 6：合同指向与待发行说明（RR-09 后半）

**描述：**
- `spec/channel.md`、`spec/integration-interface.md` 及其英文页，各加一句指向 run-resume（channel 说明 `--resumable` 和续跑见新模块；integration-interface 说明 1.1 的新增字段见新模块），原有条款不改；
- 中英文 `unreleased.md` 各记一条；
- 中英文能力图「目标」一段按需补一句。

**验收条件：** 只新增句子，不改原条款；中英文对应。
**验证：** `git diff` 只出现新增行；`git diff --check`。
**依赖：** Task 5。
**涉及文件：** `spec/channel.md`、`docs/en/SPEC-channel.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。
**规模：** S，6 文件，每个 1–3 行。

## Checkpoint 3（gate）：付费真实实测（RR-10）

**停下单独请求授权。** 授权内容：用本机真实 Codex 跑两次，大约消耗两次小任务的额度。

**做法：**
- 在家目录下新建临时 Git 仓库（不放 `/tmp`），放一个三步小任务，第 3 步留一个待定决策；
- 用当前源码 `delegate-exec.sh run --resumable` 跑一次，预期 `needs-input`，且第 1、2 步已经完成；
- 再 `--resume` 一次，答复指示 Codex 在只读模式下尝试写一个文件，预期被沙箱拒绝。

**确认：**
- 会话 ID 能取到；
- `-c sandbox_mode` 在 resume 里生效，`--` 分隔被接受；
- 上下文能接上；
- 是否先做了不受影响的步骤。

**善后：** 删除临时仓库。Codex 可能在 `~/.codex/config.toml` 自动写入受信任记录，若有，经你确认后再删。

**结果处理：**
- 结论记入 todo；
- 任何一项不成立，停下回到规格修订，不在实现里绕过；
- 未获授权时，RR-10 标「未验证」，继续 Task 7。

## Task 8：可续跑运行固定审批方式（规格 R1）

**描述：**
- 先改测试并确认它红：`test-run-resume.py` 中可续跑运行与续跑的 argv 断言加入 `-c approval_policy="never"`，并断言普通 run 的 argv 中**没有**这一项。
- 再实现：`codex-exec.sh` 在 `RESUMABLE=1`（含续跑）时向 Codex 参数加入 `-c 'approval_policy="never"'`，位置紧跟认证配置；普通 run 的参数不变。
- 同步 `run.md` 与中英文 README 的可续跑一节，各加一句：可续跑模式不使用本机配置的审批方式，越出沙箱的命令直接被拒。

**验收条件：** 新断言先红后绿；`test-channel.sh` 24 项仍全部通过；`help.md` 渲染后仍不超过 4000 字节。
**验证：**
- `python3 -B plugins/delegate/tests/test-run-resume.py`
- `/bin/bash plugins/delegate/tests/test-channel.sh`
- `python3 -B plugins/delegate/tests/test-command-migration.py`

**依赖：** 修订后的规格获批。
**涉及文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-run-resume.py`、`plugins/delegate/commands/run.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`。
**规模：** S，5 文件，均为一两行。

## Checkpoint 3c（gate）：已发布 v0.5.3 只读路径实测（RR-13 前半）

**停下单独请求授权。** 授权内容：用真实 Codex 跑 2 次最小任务。

**做法：**
- 用 `git archive v0.5.3` 把已发布版本导出到 scratchpad，不改本工作区。
- 在家目录下新建临时 Git 仓库，内含一个 `a.txt`。
- 用 v0.5.3 的 `delegate-exec.sh run`（只读）跑一次，提示词只有一句：在仓库根目录创建 `probe-run.txt`，内容 `x`，并报告是否成功。
- 用 v0.5.3 的 `delegate-exec.sh review --paths a.txt`（Codex 后端）跑一次，任务文本同样要求创建 `probe-review.txt`。

**记录：** 每次的日志头里的 approval 和 sandbox、是否写出文件（`git status`）、日志中有无审批事件。

**善后：** 删除临时仓库，核对 `~/.codex/config.toml` 哈希不变。结果写入 todo，并单独发一句给 delegate 负责人：现有只读 run 和 review 各自会不会写出文件。本检查点只记录事实，不论结果如何都继续 Task 9。

## Task 9：所有执行调用固定审批方式（规格 R2，代码与测试）

**描述：**
- 先改测试并确认它红：
  - `test-review-backends.py`：普通 run 的只读和写入调用，实际 argv 都含 `-c approval_policy="never"`；
  - `test-review-execution.py`：Codex review 的实际 argv 含该项；
  - `test-run-resume.py`：把普通 run 的「不含」断言改为「含」，位置紧跟认证配置（这条是本模块新写的断言，不属于既有断言）。
- 再实现：`codex-exec.sh` 对所有调用都加 `-c 'approval_policy="never"'`（去掉只在可续跑时才加的分支）；`review_execution.py` 的 Codex 调用加同一项。

**验收条件：** 新断言先红后绿；`test-channel.sh` 24 项仍通过；其他既有断言不改。
**验证：** `test-run-resume.py`、`test-review-backends.py`、`test-review-execution.py`、`test-channel.sh`、`test-channel-regressions.py`。
**依赖：** 修订后的规格获批（可与 Checkpoint 3c 的等待并行，但 3c 必须用 v0.5.3 副本跑，不受本 task 影响）。
**涉及文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/review_execution.py`、`plugins/delegate/tests/test-review-backends.py`、`plugins/delegate/tests/test-review-execution.py`、`plugins/delegate/tests/test-run-resume.py`。
**规模：** S，5 文件。

## Task 10：R2 的文档同步

**描述：**
- `run.md` 与中英文 README：把「可续跑模式固定审批方式」的说明改为「所有 run 与 Codex review 都固定 `approval_policy="never"`」，并写明写模式下越出沙箱的命令（如 worktree 里的 `git commit`）会被拒，提交靠前缀放行规则或由调用方完成。
- `spec/claude-review.md` 及英文页各加一句指向 run-resume 修订记录 R2。
- 中英文 `unreleased.md` 补一句。

**验收条件：** 中英文对应；`help.md` 渲染后不超过 4000 字节；只新增或改写上述句子。
**验证：** `test-command-migration.py`；`git diff --check`。
**依赖：** Task 9。
**涉及文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/claude-review.md`、`docs/en/SPEC-claude-review.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。
**规模：** S，7 文件，每个一两句。

## Checkpoint 3b（gate）：重测只读续跑（RR-10 未过的那一项）

**停下单独请求授权。** 授权内容：用真实 Codex 跑 3 次小任务（R2 起比原来多 1 次）。

**做法：** 与 Checkpoint 3 相同：家目录下新建临时仓库，跑一次只读 `--resumable`，命中待定决策后，再用只读 `--resume` 要求写文件。另用当前源码的普通只读 run 跑一次 Checkpoint 3c 的同一提示词（RR-13 后半）。

**确认：**
- 日志头的 approval 一项为 `never`；
- 写文件被拒，`git status` 为空（续跑与普通只读 run 都要）；
- 上下文仍能接上。

**善后与结果处理：** 与 Checkpoint 3 相同。仍不成立就停下，回到规格。

## Task 7：总验证与记录（RR-11）

**描述：** 运行全部免费验证，用当前启用的 Spec Guard 跑 `verify-artifacts.sh` 和 `phase-guard.sh`，把命令、结果和未验证项记入 todo。
**验收条件：** 下列命令全部退出 0。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

**依赖：** Checkpoint 3b 已执行或已记为未验证。
**涉及文件：** `tasks/run-resume/todo.md`。
**规模：** XS。

## Checkpoint 4（gate）：交付前人工验收

把实际 diff、验证结果和未验证项交给你审。之后的提交、PR、版本号与发版逐项等你授权。发版前先告知 delegate 负责人，由其报 ecosystem-lead。

## 影响面

- **普通 run：** 只多一行结果行。读 stdout 末行的调用方会看到变化，现有测试中没有这样的断言；`run.md` 会写明新增的这一行。
- **可续跑 run：** 会话会留在 `~/.codex/sessions`，所以必须显式打开。
- **接口：** 次版本升到 1.1，只增字段。spec-guard 依赖的两个 command 字段不动。

## 风险与缓解

- **resume 参数形态与帮助文本不符**（`--`、`-c sandbox_mode`）：由 Checkpoint 3 实测；不成立就回到规格修订。
- **普通 run 被意外改动：** 由 `test-channel.sh` 第 16 项的逐字 argv 断言和新测试双重守住。
- **模型漏写 `NEED_USER:`：** 规格已列为已知限制，`run.md` 提示使用方仍要读答复全文。
- **并发续跑同一 runId：** 用排他创建的占位文件防住，测试覆盖。
- **状态文件路径注入：** runId 严格正则校验，目录拒绝软链接，测试覆盖 `../` 类输入。

## 开放问题

- 版本号（是否 0.6.0）与发版时间留到 Checkpoint 4 之后，与 delegate 负责人一起定。
