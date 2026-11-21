# 任务清单：review-severity

计划：[plan.md](plan.md)；规格：[spec](../../spec/review-severity.md)。
授权：用户 2026-11-21 对 Plan 原话「批准，开始实现」。范围：改本仓库文件、跑测试与构建、在本分支本地提交；做到 Checkpoint 2（gate）停下。推送、PR、发版与通知不在此授权内。

- [x] Task 1：提示词带上判据
- [x] Task 2：结构与校验
- [x] Task 3：接口 1.5
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 4：文档同步
- [x] Checkpoint 2（gate）：复审与本地提交
- [x] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-21）：** `test-review-context.py` 新增 `SeverityPromptTests` 2 项（常量与规格「判据」代码块逐字一致、提示词含判据且在 `Task:` 之前），`test-review-execution.py` 新增 Codex 提示词 1 项；先红（`SEVERITY_CRITERIA` 不存在），在 `review_context.py` 加常量与固定说明后通过。所有组装提示词的入口（`claude_review.py`、`codex_prompt()`、`--dry-run` 预览）都经 `task_prompt()`。

**Task 2（2026-11-21）：** `test-review-result.py` 新增 `SeverityTests` 3 项（两值原样带出；缺失、大写、空串、第三种值、`None`、数字均判 `finding_invalid` 与 `failed`；schema 必填枚举且 `additionalProperties` 为 `false`），先红；`test-review-execution.py` 新增 Codex 非法取值 1 项（实现前已通过：原有「字段集合必须完全相同」规则就会拒绝多出的字段，作回归保护），另在已有的「Codex 定位发现」测试里加 `severity` 原样带出的断言，先红。实现后全绿。随合同补 `severity` 的旧夹具共 5 处，不改断言：`test-review-result.py` 2 处、`test-review-execution.py` 2 处（Codex 桩 `line`／`nullline` 模式、行号测试）、`test-review-guest-integration.py` 1 处。

**Task 3（2026-11-21）：** `test-interface.py` 版本断言改 1.5、整体比对改名为 `test_interface_1_5_is_complete`（1.4 内容原样加 `review.report.severity`）、`FINDING_FIELDS` 加 `severity`、核对 `values` 与 `review_result.SEVERITY_VALUES` 一致；先红（2 项）后绿。`interface.json` 改为 1.5。两项 plugin validate 通过。

**Checkpoint 1（report，2026-11-21）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0、`validate: ok`，Python 361 项（v0.9.0 为 354，新增 7 项）；`claude plugin validate .` 与 `./plugins/delegate` 均通过；`git diff --check` 通过。

**Task 4（2026-11-21）：** 插件中英文 README 对外接口一节加「发现的严重程度（接口 1.5 起）」条目、`findings[]` 字段表加 `severity`、解读规则补「缺失或不认识按 blocking、只在有结论时看、`unverified` 非空的含义、不等于可以合并」；`spec/integration-interface.md` 与英文页各加一句 1.5 指向句（只加不改）；中英文 `unreleased.md` 加本项。`git diff --check` 通过；`verify-artifacts` 4 通过、1 警告（integration-interface「批准后已修订」，预期内，等 Checkpoint 2 复审）。

**未验证：** `test-review-guest-integration.py` 要单独授权的一次性虚拟机，不在免费套件里，本次只补了夹具、未运行；模型按判据标注的准确度（试点观察）。

**Checkpoint 2（gate，2026-11-21）：** 用户复审 integration-interface 1.5 指向句等改动，原话「通过，本地提交」。已重新记录 `spec/integration-interface.md` 批准标记，`verify-artifacts` 4 通过、0 警告。本地提交一次，未推送。下一步停在 Checkpoint 3（gate）交付验收。

**Checkpoint 3（gate，2026-11-21）：** 用户交付验收原话「验收通过」。SV-01～SV-07 通过；未验证：`test-review-guest-integration.py`（要一次性虚拟机）、Codex 真实运行能否接受带 `enum` 的输出结构（建议发 v0.10.0 前付费实测一次）、模型标注准确度（试点观察）。本模块提交 `a09ab90` 加本次勾选提交，均未推送；推送、PR、v0.10.0 发版另行授权，发版等 review-recheck 完成。
