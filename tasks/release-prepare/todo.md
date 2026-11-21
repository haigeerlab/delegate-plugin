# 任务清单：release-prepare

计划：[plan.md](plan.md)；规格：[spec](../../spec/release-prepare.md)。
授权：用户 2026-11-21 对 Plan 原话「批准，开始实现」。范围：改本仓库文件、跑测试与构建、在本分支本地提交；做到 Checkpoint 2（gate）停下。推送、PR、合并与通知不在此授权内。

- [x] Task 1：参数、前提与诊断码
- [x] Task 2：改写（纯函数）
- [x] Task 3：检查执行与 JSON
- [x] Task 4：切分支、提交、失败清理、重跑与 `--check`
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 5：文档
- [x] Checkpoint 2（gate）：复审与本地提交
- [x] Checkpoint 3（gate）：端到端与交付验收

## 记录

**Task 1（2026-11-21）：** 新建 `scripts/tests/test-release-prepare.py`（缩小版仓库布局的临时仓库）5 项，先红（模块不存在），新建 `scripts/release_prepare.py` 的参数解析、前提检查、待发行说明形状与锚点检查后通过：`usage_invalid`（退出 64）、`version_invalid`、`version_not_newer`、`tag_exists`、`worktree_dirty`、`base_not_main`、`release_notes_incomplete`、`release_docs_anchor_missing` 各有用例。入口 `scripts/release-prepare.sh`（标准输入接 `/dev/null`，可执行）。测试登记进 `scripts/validate.sh`：先改 `validate.sh` 使发现测试变红，再给发现测试加夹具变绿。

**Task 2（2026-11-21）：** `RenderTests` 4 项先红（`render` 为桩），实现后通过：中英文 `v<X>.md`、待发行说明收回、版本号、README／文档索引／贡献指南各锚点，与写死的期望文本逐字一致；占位数先保留、待实测后填入。

**Task 3（2026-11-21）：** `CheckAndReportTests` 5 项先红，实现检查执行（可注入；按序跑、记命令与退出码、找不到报 `check_unavailable`、非 0 报 `check_failed`、`validate` 无测试数也算失败）、spec-guard 路径从 Claude 已安装插件记录解析、接口版本取最新 `v*` 标签、7 条人工步骤带原因、`--check` 流程。测试夹具改为每个进程只建一次模板仓库再复制，套件从 68 秒降到约 16 秒。

**Task 4（2026-11-21）：** `PrepareTests` 6 项先红，实现切 `release/v<X>`、先写占位跑 `validate`、填实测数并暂存后跑其余检查、提交一次（中文说明加尾注 `Release-Prepare: v<X>`）；失败时重置、删本次新建文件与分支、回到原分支；重跑复用、分支被改过报 `release_branch_conflict`、复用时失败保留分支；`--check` 前后文件与引用一致；替换标准输入为一读就报错的对象也能跑完。

**自查修复（2026-11-21）：** 在真实仓库文档上核对时发现循环回归套数算成 3：真实 `validate.sh` 有两个 `for SUITE in` 循环，先出现的是 3 个 shell 套。夹具只有一个循环所以没测出。先补测试 `test_loop_suites_counts_the_python_loop_not_the_shell_loop`（夹具里放两个循环，并核对真实仓库）确认红，再改为只数循环体里跑 `test-${SUITE}.py` 的那个；真实仓库得 28。真实文档的全部锚点已核对命中。

**Checkpoint 1（report，2026-11-21）：** 修复后在最终代码上重跑：`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0、`validate: ok`，Python 409 项（v0.10.0 为 388，新增本模块 21 项）；`claude plugin validate .` 与 `./plugins/delegate` 均通过；`git diff --check` 通过；`verify-artifacts` 5 通过、0 警告。

**Task 5（2026-11-21）：** 中英文贡献指南新增「发版」／「Releasing」一节（待发行说明格式与示例、`--check` 与正式运行、读输出、七步人工、改措辞时同步锚点表）；中英文待发行说明在语言切换行后加一行格式说明注释（不在「已归入」段之后，不影响解析），历史段落未改。`git diff --check` 通过。

**未验证：** 用真实检查命令的端到端（Checkpoint 3 在临时克隆上做）；提交检查钩子拦截时的清理只靠 `git commit` 失败走同一清理分支，未单独测试。

**Checkpoint 2（gate，2026-11-21）：** 用户复审锚点表、失败清理与重跑、贡献指南「发版」一节与自查修复，原话「通过，本地提交」。本地提交一次，未推送；按拟稿回复 sg-coord #21972。下一步 Checkpoint 3（gate）：临时克隆上端到端，再交付验收。

**Checkpoint 3 端到端（2026-11-21）：** 在 scratchpad 里 `git clone --no-local` 本分支提交 `49265c8`，按 A10 格式写入临时中英文待发行说明并提交，`origin/main` 指向该提交（模拟 fetch），克隆里设与本仓库相同的提交身份。真实检查命令：`/bin/bash scripts/release-prepare.sh 0.10.99 --check` 退出 0、`ready`，五项检查全部 0，Python 409、循环回归套 28，前后引用一致、工作区干净；`/bin/bash scripts/release-prepare.sh 0.10.99` 退出 0、`ready`，在 `release/v0.10.99` 上恰好一个提交（父提交为基线、带尾注），改动 11 个文件，工作区干净；生成的中英文发行说明、收回的待发行说明、README／贡献指南／文档索引／`plugin.json` 改写人工核对无误。克隆已删除，远端没有 `release/*` 分支，未推送。

**Checkpoint 3（gate，2026-11-21）：** 用户交付验收原话「验收通过」。RP-01～RP-08 通过；Spec 批准后未改。未验证：提交检查钩子拦截时的清理（未单独测试）；在没有 Claude Code 安装 spec-guard 的机器上会报 `check_unavailable`。本模块提交 `49265c8` 加本次勾选提交，均未推送；推送、PR、合并与通知 ecosystem-lead／autopr-design 另行授权。插件与接口未变，不需要发新版本。
