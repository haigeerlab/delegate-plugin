# 任务清单：default-model

计划：[plan.md](plan.md)；规格：[spec](../../spec/default-model.md)（用户 2026-11-26 批准，原话「批准」）。
授权：用户 2026-11-26 对 Plan 原话「批准，开始实现」（重要需求，Plan 由用户批）。范围：改本仓库文件、跑免费测试；做到 Checkpoint 2（gate）停下。Codex 审查额度、本地提交、推送、PR、合并、发版与通知不在此授权内。
开工前修订：并行边界删掉 `run_state.py` 后的括注（用户原话「同意修改」）、加入 `docs/en/capability-map.md`（用户原话「加进边界」），两次都重新记录了 Spec 批准；越界检查 0。

- [x] Task 1：配置读取与取值
- [x] Task 2：入口与审查
- [x] Task 3：执行与续跑
- [x] Task 4：体检
- [x] Task 5：接口 1.8
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 6：文档同步
- [x] Checkpoint 2（gate）：审查与复审（本地提交须另行明确同意）
- [x] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-26）：** 新建 `test-default-model.py`（11 项），先红（模块不存在）；实现 `delegate_defaults.py`（`config_path`、`load`、`resolve`、`ConfigError.line`），两个 Python（3.10、系统 3.9.6）通过。DM-01 取值穷举 10 例；DM-02 路径 4 例；DM-03 函数层十个原因码全覆盖（另含空模型名、`opusplan`、重复键、非 UTF-8），字段类带字段路径、不回显值、文件不存在返回空配置。`--effort` 取值改用共享常量 `EFFORTS`（只移动不改值）。`run_suites.py` 给每个套件设空的私有 `XDG_CONFIG_HOME`，`test-run-suites.py` 新增用例先红后绿；新套件登记进 `validate.sh` 与发现测试夹具，发现测试里套件总数 35→36。

**Task 2（2026-11-26）：** `test-review-cli.py` 新增 `DefaultModelCLITests`，先红（5 失败 4 错误），实现后 9 项通过。实现：`delegate_cli.main()` 对 review／run 先读配置，错误按 E3 打一行退出 64；后端定了之后在 `delegate_backend.main()` 取值（`auto` 选中后同样走这里），续跑与接续记 `resumed`；`--dry-run` 预览带解析后的 `requested_model`、`model_source`、`requested_effort`；`base_report()` 新增 `model_source`，占位报告未带来源时按点名与否推断。覆盖：DM-03／DM-04 审查侧（配置写错、点名了也退出 64、stdout 为空、未启动模型）；DM-08 显式 codex（桩收到 `-m gpt-6.2-sol` 与 `model_reasoning_effort="high"`）、显式 claude-code、auto 选中两家、点名覆盖、无配置为 `host_default`；DM-09；DM-15（去掉 `CLAUDE_*`、设 `CODEX_THREAD_ID` 后 claude-code 仍读同一配置）。Claude 路径要过 Mac 本机边界，用例在进程内替换 `native_review` 只看它收到的模型；真实 Claude CLI 收到 `--model` 的那一步沿用现有 `claude_review.py` 第 132～133 行，未改。审查相关 7 个套件全部通过。

**Task 3（2026-11-26）：** `test-run-result.py` 新增 `DefaultModelFlowTests` 7 项，先红（6 个错误：结果文件没有 `modelSource`；配置写错那项已由 Task 2 的入口覆盖，先绿），实现后通过。实现：`delegate_backend.main()` 转发 run 时设 `DELEGATE_MODEL_SOURCE`／`DELEGATE_EFFORT_SOURCE`；`codex-exec.sh` 读取后立即 `unset`，按「值非空且声称 config 才是 config，非空为 explicit，空为 host_default，续跑一律 resumed」判定，未知或自相矛盾的值退回推断；两处「模型：… / 推理档：…」打印改为注明来源；`run_state.py result` 新增 `--model-source`／`--effort-source`，结果文件写 `modelSource`、`effortSource`。覆盖：DM-05（桩收到 `-m gpt-6.2-sol` 与 `model_reasoning_effort="high"`，两个来源都是 config，打印行注明）；DM-06；DM-07（`--resume` 和 `--continue` 在配置改了之后仍用原会话的 `gpt-6.2-sol`，来源 `resumed`）；DM-03／DM-04 run 侧（含点名和 `--resume` 时配置写错也退出 64、不启动 Codex）；DM-10（直接调 `codex-exec.sh` 不读配置）。执行相关 11 个套件与 `test-channel.sh` 通过。DM-07 原计划写在 `test-run-resume.py`／`test-run-continue.py`，实际写在 `test-run-result.py` 同一个类里（共用夹具），那两个文件未改。

**Task 4（2026-11-26）：** `test-default-model.py` 新增 `DoctorTests` 4 项，先红（6 处失败；`--reviewers` 那项先绿），实现后通过。`review_doctor.py` 在后端能力前打印「默认模型」一段（配置路径与是否存在、两家的模型与推理档及来源，claude-code 推理档写「不支持」）；配置写错时打印同一行错误，Codex 路径改为子进程跑完 `doctor.sh` 后返回 1，claude-code 路径跑完预检后返回 1；配置不存在或有效时仍 `exec doctor.sh`、退出码与今天相同（今天两条路径都是 0）。`--reviewers` 不变。`test-review-native`、`test-review-execution`、`test-review-backends`、`test-review-cli`、`test-detection.sh` 通过。

**Task 5（2026-11-26）：** `test-interface.py` 改为期待 1.8、顶层 `defaults`、稳定字段加 `model_source`，先红（2 处失败），改 `interface.json` 后 14 项通过；另断言 `defaults.sources`、`defaults.schema` 与 `delegate_defaults` 的常量一致。`claude plugin validate .`、`claude plugin validate ./plugins/delegate` 均通过。

**Checkpoint 1（report，2026-11-26）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0，100 秒，`validate: ok`，`Ran` 合计 583（上次全量 548，加上本模块新增的 35 项）；`claude plugin validate .`、`claude plugin validate ./plugins/delegate` 均通过；`git diff --check` 通过；产物校验 6 项通过。DM-13：没有配置文件时现有套件断言未改（只有发现测试里套件总数 35→36、接口测试期待 1.8 两处跟随本模块改动）。**越界检查 3 个范围外文件**：`scripts/run_suites.py`、`scripts/tests/test-run-suites.py`、`scripts/tests/test-validation-discovery.py`。它们在 Plan 的 Task 1 文件清单里，但 Spec 的并行边界漏写了，已停下问用户。

**越界处理（2026-11-26）：** 用户原话「补进边界」。三个文件加入 Spec 独占清单，重新记录 Spec 批准。

**Task 6（2026-11-26）：** DM-14 逐项：
- 插件 `README.md`／`README.en.md`：新增「默认模型配置」一节（路径、格式示例、优先级、auto 与续跑、报错读法、来源字段、只有 review／run 读），「对外接口」加「默认模型（接口 1.8 起）」条目。
- `commands/doctor.md`：加一句默认模型段与配置无效时退出 1，退出码说明改为「除配置无效外，退出 0 表示诊断完成」（渲染 1.3 KB 级）。**偏差**：`commands/review.md` 渲染 3992 字节、`run.md` 3971 字节，离 4000 上限分别只剩 8、29 字节，放不下一句中文，按 Plan 风险表「只加一句、改完量字节」的前提未改，说明放在 README；`test-command-migration.py` 通过。
- `spec/integration-interface.md`／英文页：加 1.8 一条，稳定字段表加 `model_source`。`spec/run-result.md`／英文页：字段说明加 `modelSource`、`effortSource`。两份中文合同因此显示「批准后已修订」，按 Plan 随 Checkpoint 2 复审重新记录。
- 中英文待发行说明：标题「按后端配置默认模型（接口 1.8）」，含变更、影响面（调用方转发配置错误、`requested_model` 含义）、验证与已知限制；用 `release_prepare.notes_parts` 解析两份均通过。
- 复验：全量 `validate.sh` 退出 0（97 秒，`Ran` 583）；两项 plugin validate 通过；`git diff --check` 通过；`check-shared-sections.py` 通过；产物校验 6 通过 2 警告（即上面两份合同待复审）；越界检查 0。

## External review

Checkpoint 2 · Codex 只读审查第 1 轮（2026-11-26，用户原话「同意审查」；`/delegate:review --backend codex --changes working-tree --include-untracked --spec spec/default-model.md`，安装版 0.12.6，模型未点名）：completed，审 32 个文件、未审 0，9 条阻断、1 条建议。逐条核对与处理：
1. 深层嵌套 JSON 让 `json.loads` 抛 `RecursionError`，绕过单行报错（属实）。改为按 `invalid_json` 处理，补 60000 层 `[` 用例，先红后绿。
2. 路径含换行会把错误拆成多行（属实）。`ConfigError.line()` 转义 `\`、换行、回车，补用例，先红后绿。
3. `HOME` 为相对路径时会读仓库里的 `.config`（属实）。`HOME` 不是绝对路径时改用账户主目录（`pwd`），补用例，先红后绿。
4. 环境里残留的 `DELEGATE_MODEL_SOURCE=config` 会把旧入口的点名误标为配置（属实）。来源改为由 `delegate_backend` 转发内部参数 `--model-source`／`--effort-source`，不再读环境变量；非法值退出 64。补「残留环境变量被忽略」「内部参数」两条用例，先红后绿。Spec 影响面第 4 条与 Plan 架构决定随之修订，待用户复审。
5. 十种错误只有一种经过两个入口（属实，测试缺口）。新增 `EntryErrorTests`：十种错误（root 下跳过 `unreadable`）各经 review、run 断言退出 64、stderr 恰为一行、stdout 为空；实现已在，直接通过；变异验证：临时让入口跳过读配置，20 处失败，还原后通过。
6. DM-15 没断言 Claude CLI 实际参数（属实）。用例改为调用真实的 `claude_review.execute()` 拼命令，只替换预检与调用器，断言 argv 里 `--model claude-opus-5-5`（点名、无配置各一例）；变异验证：临时删掉加 `--model` 的两行，3 处失败，还原后文件与原来一致。
7. `.claude/settings.local.json` 被纳入范围（不需要改）：它是本机设置，由全局 `~/.config/git/ignore` 忽略，不会提交，不属于本模块交付。另发现 review 的 `--include-untracked` 把只被全局 gitignore 忽略的文件也带进了审查输入，属于既有问题，单独提出，不在本模块改。
8. `commands/review.md`、`run.md` 没提默认模型（属实）。各加一句指向 README，压缩 review.md 一句冗余（「该工具设置核验…真实模型」→「该核验…模型」），渲染均为 3996 字节（上限 4000），`test-command-migration.py` 通过。
9. README 写成续跑「不读本文件」，实际仍会校验（属实）。中英文改为「不取值、仍校验，文件有错时续跑也退出 64」。
10. （建议）待发行说明「每项都先红」与记录不符、下游核对无出处（属实）。改为区分先红与补测直接通过，并注明 #23282。
复验：全量 `validate.sh` 退出 0（88 秒，`Ran` 587）；两项 plugin validate、`git diff --check` 通过；越界 0；产物校验 6 通过 3 警告（`default-model`、`integration-interface`、`run-result` 三份 Spec 批准后已修订，待用户复审）。

**Checkpoint 2（gate，2026-11-26）：** 用户复审审查处理与三份 Spec 修订（`default-model` 影响面第 4 条改为内部参数、`integration-interface` 1.8 条与 `model_source` 稳定字段、`run-result` 两个来源字段），原话「复审通过」；三份 Spec 已重新记录批准。未跑 Codex 第 2 轮。本地提交未授权。

**Checkpoint 3（gate，验收记录，2026-11-26）：** 基于 origin/main `d59cc42` 的未提交工作区。全量 `validate.sh` 退出 0（97 秒，`Ran` 587）；`claude plugin validate .`、`./plugins/delegate` 通过；`git diff --check` 通过；越界 0；产物校验 6 通过 0 警告。DM-01～DM-15 全部有命令证据（见上各 Task 记录）；DM-14 为人工核对。改动 32 个文件（27 修改、5 新增）。未验证：真实 Codex／Claude 实跑。用户 2026-11-26 原话「提交并推送开 PR」，验收通过并授权提交、推送、开 PR；合并与发版另问。
