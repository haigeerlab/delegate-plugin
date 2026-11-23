# 任务清单：design-review-criteria

计划：[plan.md](plan.md)；规格：[spec](../../spec/design-review-criteria.md)。
授权：用户 2026-11-24 对 Plan 原话「批准，开始实现」（重要需求，Plan 由用户批）。范围：改本仓库文件、跑免费测试；做到 Checkpoint 2（gate）停下。本地提交、推送、PR、发版与通知不在此授权内。用户接受先做本需求、上个需求的里程碑 M2 实跑往后放。

- [x] Task 1：`--profile` 参数与 design 提示词
- [x] Task 2：降级与 `criteria` 字段
- [x] Task 3：复审判据一致与端到端
- [x] Task 4：接口声明
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 5：文档同步
- [x] Checkpoint 2（gate）：复审（本地提交须另行明确同意）
- [ ] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-24）：** 先写测试并确认红（`DESIGN_CRITERIA` 等不存在、`--profile` 未识别）：`test-review-context.py` 新增 `DesignPromptTests` 3 项（换判据、说明在 `Task:` 前、常量与规格逐字一致、`criteria_name()`）；Codex、Claude Code、访客三条路径各 1 项；`test-review-cli.py` 1 项（预览 `profile`／`criteria`，重复、非法、空值退出 64）。实现：`delegate_cli.py` 加 `--profile default|design`，design 时写 `context['profile']`，预览加两字段；`review_context.py` 加 `DESIGN_CRITERIA`、`DESIGN_INSTRUCTION`、`criteria_name()`。默认档提示词的逐字断言（上一模块的 `ContextFilesPromptTests`）照旧通过。

**Task 2（2026-11-24）：** `test-review-result.py` 新增 `DesignProfileTests` 6 项，先红（5 项失败）。实现：`content_result()` 在 design 档调用 `downgrade()`——只处理阻断；第二轮记 `second_round`，否则位置核不上或文件被审查范围选中记 `no_code_evidence`；位置核不上不再让 design 档整轮失败；`base_report()` 加顶层 `criteria`。默认档同输入仍 `failed`／`review_incomplete`。

**Task 3（2026-11-24）：** `test-review-recheck.py` 新增判据一致 1 项、`test-review-cli.py` 新增 `DesignProfileCLITests` 2 项。先红：判据不同的复审在旧实现下放行（退出 0）。端到端降级用例在 Task 2 后已经通过，作为回归保留。为端到端给 Codex 桩加了只在测试里读的 `FIXTURE_CONTENT`（写入指定的结构化结果）。实现：`check_scope()` 比较 `report.criteria`（缺省 `severity-v1`）与 `criteria_name(context)`。

**Task 4（2026-11-24）：** `test-interface.py` 期待 `review.profiles` 与稳定字段 `criteria`，先红后改 `interface.json`；`interface` 号仍为 1.6，按计划随 reviewer-selection 升 1.7。初版多写了规格里没有的 `field` 键，已去掉以与规格一致。

**Checkpoint 1（report，2026-11-24）：** 第一次总验证 `validate` 退出 1：`test-command-migration.py` 报 `review.md renders to 4362 UTF-8 bytes; Codex skips skills above 4000`——Task 5 在 `commands/review.md` 加的说明让命令超出 Codex 技能体积上限（原 3977 字节，余量 23 字节）。处理：说明段撤回，只在 `argument-hint` 加 `[--profile design]`（不计入渲染体积），读法放在插件 README。重跑：`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` → `validate: ok`；`claude plugin validate .`、`claude plugin validate ./plugins/delegate` → 均通过；`git diff --check` 通过。DR-10：现有套件断言未改（只给 Codex 桩加了测试用开关）。

**Task 5（2026-11-24）：** DR-11 逐项：
- 中文合同 `spec/design-review-criteria.md` 与实现一致；英文 `docs/en/SPEC-design-review-criteria.md` 新建，判据全文逐字相同。
- 用法草案 `spec/usage/s110-design-review.md` U1 与实现一致。
- 插件 `README.md`／`README.en.md`「对外接口」加「技术方案审查（接口 1.7 起）」条目。
- `commands/review.md`：只在参数提示加 `--profile design`（体积限制，见 Checkpoint 1）。
- `spec/integration-interface.md` 及英文页：1.6 指向句后加 1.7 `profiles` 指向，只加不改；`verify-artifacts` 因此报「批准后已修订」，留待 Checkpoint 2。
- 中英文待发行说明：标题 `技术方案审查与第二审查者（接口 1.7）`、变化、影响面、验证与限制；「暂无未发布变更」改为「的未发布变更见下」。reviewer-selection 完成后补它的小节。

**Checkpoint 2（gate，2026-11-24）：** 用户复审后原话「通过，本地提交」。重新记录 `spec/integration-interface.md` 的批准标记，`verify-artifacts` 恢复 0 警告；在本分支本地提交（含 S110 的能力图、用法草案、两个模块的 Spec 与 Plan；不推送）。
