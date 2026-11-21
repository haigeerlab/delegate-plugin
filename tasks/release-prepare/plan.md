# 实施计划：release-prepare

<!-- spec-guard: review approved -->

日期：2026-11-21。规格：[spec/release-prepare.md](../../spec/release-prepare.md)（用户 2026-11-21 批准，原话「批准」）。任务：[todo.md](todo.md)。来源：总账 S101 r3、ecosystem-lead #21885、autopr-design #21967。

## 架构决定

- **三层分开。** `scripts/release_prepare.py` 里分三块：① 纯函数改写（输入各文件文本与版本、测试数，输出新文本；不碰磁盘、不调 git）；② 检查执行（命令清单可注入，测试用假命令）；③ git 与流程（前提、切分支、提交、失败清理、重跑、JSON）。`scripts/release-prepare.sh` 只把标准输入接到 `/dev/null` 后调 Python。
- **测试数的先后。** Python 项数要跑完 `validate.sh` 才知道，所以改写时先写占位，跑 `validate.sh` 后填入实测值，再跑其余四项检查（plugin validate ×2、`git diff --check`、`verify-artifacts`）。`validate.sh` 只检查 JSON／Python／Bash 语法和测试，不读 Markdown，填数不影响它的结果。`--check` 模式在内存里改写，检查跑在未改写的工作区上（只读），只确认「能备好」。
- **锚点集中定义。** 要改的每一处（`plugin.json` 版本；中英文 README 的当前发行链接、发行源码标签、发行变化列表、循环回归套数与发布验证句；中英文文档索引的升级行、当前发行行、旧版列表行；中英文贡献指南的发布验证句与循环回归套数）写成一张锚点表，每项按当前措辞精确匹配；措辞变了就报 `release_docs_anchor_missing` 停下，不猜。
- **git 调用。** 一律参数数组、`GIT_TERMINAL_PROMPT=0`、标准输入 `/dev/null`；不屏蔽用户全局配置（要用用户身份和提交检查钩子，提交说明用中文）。
- **不递归。** 测试从不调真实 `validate.sh`；端到端只在 Checkpoint 3 在临时克隆上跑一次。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Checkpoint 1（report）→ Task 5
→ Checkpoint 2（gate：复审与本地提交）→ Checkpoint 3（gate：端到端与交付验收）
```

## Task 1：参数、前提与诊断码

**描述：** 新建 `release_prepare.py` 的参数解析与前提检查（版本格式、比当前新、标签不存在、工作区干净、`HEAD` 等于 `origin/main`、待发行说明形状、锚点齐全），`release-prepare.sh` 入口；新建 `scripts/tests/test-release-prepare.py`（临时仓库造缩小版布局）；测试登记进 `scripts/validate.sh` 与发现测试。

**验收条件：** 先红后绿；RP-01 中前提类诊断码（`usage_invalid`、`version_invalid`、`version_not_newer`、`tag_exists`、`worktree_dirty`、`base_not_main`、`release_notes_incomplete`、`release_docs_anchor_missing`）各至少一例，退出码与 JSON `reason` 正确。

**验证：** `python3 -B scripts/tests/test-release-prepare.py`、`python3 -B scripts/tests/test-validation-discovery.py`

**依赖：** 无。**文件：** `scripts/release_prepare.py`、`scripts/release-prepare.sh`、`scripts/tests/test-release-prepare.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`。**规模：** M。

## Task 2：改写（纯函数）

**描述：** 生成中英文 `v<X>.md`（标题取 `release-title`、搬入变更小节与「影响面」「验证与已知限制」、验证小节末尾补测试数句、加固定「更新」小节）、收回中英文待发行说明、`plugin.json` 版本、锚点表里每一处的新文本。

**验收条件：** 先红后绿；RP-03：每个输出与测试里写死的期望文本逐字一致（含中英文、含「旧版发行记录」前插上一版）。

**验证：** `python3 -B scripts/tests/test-release-prepare.py`

**依赖：** Task 1。**文件：** `scripts/release_prepare.py`、`scripts/tests/test-release-prepare.py`。**规模：** M。

## Task 3：检查执行与 JSON

**描述：** 检查清单（A15）可注入；从 `validate.sh` 输出累加 `Ran N tests` 得 Python 项数，从 `validate.sh` 的循环行数套数；从 `~/.claude/plugins/installed_plugins.json` 解析 spec-guard 安装路径找 `verify-artifacts.sh`（只读）；命令找不到报 `check_unavailable`，非 0 报 `check_failed`；组装输出 JSON（A9、`human_steps` 7 条带 `why`、接口版本取最新 `v*` 标签里的 `interface.json`）。

**验收条件：** 先红后绿；RP-01 中 `check_unavailable`、`check_failed`；RP-06（字段齐全、`human_steps` 7 条、`checks` 只列跑过的、命令为参数数组）。

**验证：** `python3 -B scripts/tests/test-release-prepare.py`

**依赖：** Task 2。**文件：** 同上。**规模：** S～M。

## Task 4：切分支、提交、失败清理、重跑与 `--check`

**描述：** 非 `--check`：切 `release/v<X>`、写文件、按「测试数的先后」跑检查、全过则提交一次（中文说明加尾注 `Release-Prepare: v<X>`）；失败按 A14 清理。同版本重跑按 A13 复用或报 `release_branch_conflict`。`--check`：不切分支、不写文件。入口不读标准输入。

**验收条件：** 先红后绿；RP-02（`--check` 前后仓库文件字节与全部引用一致）；RP-04（全过恰好一个带尾注的新提交、父提交为基线；失败时无提交、无分支、回到原分支）；RP-05（重跑复用同一 SHA；分支被改过时拒绝）；RP-06 的「给一个会阻塞的标准输入也能跑完」。

**验证：** `python3 -B scripts/tests/test-release-prepare.py`、`bash -n scripts/release-prepare.sh`

**依赖：** Task 3。**文件：** 同上。**规模：** M。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`、两项 plugin validate、`git diff --check`、`verify-artifacts` 通过；把命令与结果记入 todo 后继续。

## Task 5：文档

**描述：** 中英文贡献指南新增「发版」一节：待发行说明的固定形状（A10）与示例、怎么跑 `scripts/release-prepare.sh <版本> [--check]`、输出怎么看、七步人工步骤与原因、失败时怎么办。中英文待发行说明加一行模板说明的 HTML 注释（不含 `release-title` 字样，避免被当成标题行），历史段落不改。

**验收条件：** RP-07；`git diff --check` 通过。

**验证：** `git diff --check`、`verify-artifacts`

**依赖：** Checkpoint 1。**文件：** `CONTRIBUTING.md`、`CONTRIBUTING.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审与本地提交

交你复审实际 diff，重点是锚点表、失败清理与重跑逻辑、贡献指南的「发版」一节；通过后在本分支本地提交一次。

## Checkpoint 3（gate）：端到端与交付验收

在本仓库的临时克隆里（克隆本分支提交后的状态），按 A10 写一份临时待发行说明，用真实检查命令跑一次 `--check` 和一次正式准备（版本取一个不会发的测试号，如 `0.10.99`），把 JSON 与产出 diff 给你看，然后删除克隆；不推送。再按最终验收格式报告 RP-01～RP-08。推送、开 PR、合并另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 文档措辞以后被人改了，锚点匹配不上 | 中 | 精确匹配、找不到就报 `release_docs_anchor_missing` 停下，不猜；贡献指南写明改这些句子时同步改锚点表 |
| 失败清理误删别人的分支 | 高 | 只删本次运行新建的 `release/v<X>`；复用的分支失败时不删 |
| 检查跑得慢（`validate.sh` 约 5 分钟），调用方超时 | 中 | 贡献指南写明要用后台方式调用；脚本自身不设上限 |
| 用户的提交检查钩子拦下提交 | 低 | 提交说明用中文、带署名行；被拦按 `check_failed` 同等处理并清理 |
| 测试递归调用总验证 | 高 | 测试只用假命令；端到端只在 Checkpoint 3 手动跑 |

## 开放问题

- 无。
