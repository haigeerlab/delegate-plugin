# 任务清单：reviewer-selection

计划：[plan.md](plan.md)；规格：[spec](../../spec/reviewer-selection.md)。
授权：用户 2026-11-24 对 Plan 原话「批准，开始实现」（重要需求，Plan 由用户批）。范围：改本仓库文件、跑免费测试；做到 Checkpoint 2（gate）停下。本地提交、推送、PR、发版与通知不在此授权内。用户接受先做本需求、上个需求的里程碑 M2 实跑往后放。

- [x] Task 1：选择逻辑
- [x] Task 2：参数、路由与报告
- [x] Task 3：体检 `--reviewers`
- [x] Task 4：接口 1.7
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 5：文档同步
- [x] Checkpoint 2（gate）：复审（本地提交须另行明确同意）
- [x] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-24）：** 新建 `test-reviewer-select.py`，先红（模块不存在）。实现 `reviewer_select.py` 的 `VENDORS`、`order()`、`choose()`、`describe()`：两个方向 × 三种可用组合、只查需要的家、未知主开发报错、显式后端有无主开发时的 `same_vendor`。套件登记进 `scripts/validate.sh`；`test-validation-discovery.py` 先红（夹具缺新套件）后补上转绿。

**Task 2（2026-11-24）：** `test-review-cli.py` 新增 `ReviewerSelectionCLITests` 5 项、`test-review-result.py` 新增 1 项，先红（3 失败 1 错误；参数错误那项旧实现本来就拒，作回归保留）。实现：审查命令 `--backend` 加 `auto`、新增 `--author-host`，`auto` 时必须给主开发、不接受 `--model`／`--effort`／`--max-turns`／`--max-budget-usd`；取完上下文后选择并改写转发的 `--backend`；都不可用时出「未审」报告；`base_report()` 加顶层 `reviewer`。`reviewer_select.real_checks()` 包两家现有无模型预检，测试可用 `DELEGATE_FIXTURE_REVIEWERS` 固定结果（另有用例断言不设该变量时用真实检查）。一处测试前提写错（缺失路径在选择之后才发现，`cross_vendor` 是对的），改用 `--base no-such-ref` 构造取上下文前失败。**卡在规格没覆盖的一点：**「未审」报告的顶层 `backend` 取什么值；`test-interface.py` 的守卫要求报告 `backend` 只能是 `codex`／`claude-code`，现实现写的 `auto` 违反这一条。已停下问用户。

**Task 3（2026-11-24）：** `test-review-backends.py` 新增 `ReviewerDoctorTests` 3 项，先红（4 处失败）。实现 `review_doctor.py --reviewers [--json]`：逐家无模型检查，JSON 为 `delegate.reviewers/v1`，`hint` 取 `null`／`add_second_vendor`／`no_reviewer_available`；文本在只一家时建议再开通、都不可用时说明会记为未审；总是退出 0；未知参数退出 64。原有 doctor 用法不变（`test-review-native.py`、`test-review-execution.py` 通过）。

**Task 2 收尾（2026-11-24）：** 用户选定「未审」报告 `backend` 为 `null`，原话「A：null」。补进 Spec 为 E7 并重新记录 Spec 批准。`unreviewed()` 改为 `base_report(None, …)`；端到端用例加断言 `backend` 为 `null`；`test-interface.py` 的后端取值守卫保持只认 `codex`／`claude-code`，另断言 `base_report(None,` 全仓只出现一次且是「未审」报告。

**Task 4（2026-11-24）：** `test-interface.py` 改为期待 1.7、`review.reviewer`、`doctor.reviewers`、稳定字段 `reviewer`，先红（2 处失败）；改 `interface.json` 后通过，另加断言接口里的厂商表与 `reviewer_select.VENDORS` 一致。

**Checkpoint 1（report，2026-11-24）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` → `validate: ok`；`claude plugin validate .`、`claude plugin validate ./plugins/delegate` → 均通过；`git diff --check` 通过。RS-10：现有套件断言未改（新增用例与测试用开关除外）。

**Task 5（2026-11-24）：** RS-11 逐项：
- 中文合同 `spec/reviewer-selection.md`（含 E7）与实现一致；英文 `docs/en/SPEC-reviewer-selection.md` 新建。
- 插件 `README.md`／`README.en.md`「对外接口」加「第二审查者的选择（接口 1.7 起）」条目。
- `commands/review.md`：只在参数提示加 `auto` 与 `--author-host`（渲染体积 3977 字节不变，上限 4000）；`commands/doctor.md` 加 `--reviewers [--json]` 一段（渲染 1296 字节）。
- 根 `README.md`／`README.en.md` 第 228 行：「不改用 Claude 自审」改为「写代码的会话绝不审自己的东西……」。全仓 `git grep` 旧说法，只剩上个需求的用法草案 `spec/usage/auto-takeover-review.md` 第 28 行（S110 规定老文档不改，未动）与历史验证记录。
- `spec/integration-interface.md` 及英文页加 1.7 `reviewer`／`doctor.reviewers` 指向与 `backend` 可为 `null` 的条件，只加不改。
- 中英文待发行说明加「第二审查者的选择」小节与读报告提示。
- Checkpoint 2：用户 2026-11-24 原话「通过，本地提交」。复审前全量验证 `validate: ok`、两次 `claude plugin validate` 通过、`git diff --check` 通过；integration-interface 的 1.7 指向随复审一并重新记录批准。
- Checkpoint 3：用户 2026-11-24 原话「通过，推送开 PR」。验收基于 848f8fe：`validate: ok`、两次 `claude plugin validate` 通过、`git diff --check 4bc497e HEAD` 通过、`module_scope.py check --base 4bc497e` 越界 0、`verify-artifacts` 7 通过 0 警告。未验证：两家真实 CLI 可用性下的实际选择，留到发版后实跑。
