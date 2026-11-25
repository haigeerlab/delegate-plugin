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

## M1 实跑未通过：Claude Code 探测期限过短（2026-11-26）

用户 2026-11-26 让本会话实跑 `spec/usage/s110-design-review.md` 的 M1（原话「跑 s110 的 M1」），用安装版 0.12.3 在临时克隆里审一份故意带缺陷的演示技术方案（`version` 分支放在 `delegate_cli.py:200` 旧版回退之后）。用户判定不通过，原话「不通过，补探测期限任务」；未调用 milestone-mark。

- U1 一致：第一轮退出 0，`reviewer` 为 openai/codex/cross_vendor，判据 design-v1，1 条阻断指向 `delegate_cli.py:200`；改方案后第二轮 `recheck.items[1]` 为 resolved，新发现 1 条为 suggestion（`downgraded: second_round`）。本次未出现需降级为 `no_code_evidence` 的阻断，该路径未实际触发。
- U2 不稳定：PATH 去掉 Codex 后同一命令跑 3 次，前 2 次退出 127（`no_reviewer_available` + `codex_cli_missing` + `probe_timed_out`／`probe_cleanup_unverified`），第 3 次退出 0（anthropic/claude-code/same_vendor_fallback，模型 claude-opus-5-5）。直接调 `reviewer_select.claude_check` 6 次耗时 4～19 秒，1 次 `probe_timed_out`。原因：`claude_review._probe` 每个探测阶段期限固定 5 秒（`deadline=5`），Claude CLI 在沙箱里启动慢时超时，被判为不可用。doctor `--reviewers` 用同一检查，同样会时好时坏。
- U3 一致：退出 127，conditions_missing／inconclusive，`no_reviewer_available`，`selection=none`，`backend_started=false`。
- U4 一致：两家都在、只剩一家、两家都没有三种情况的列表与提示均与草案相符，退出 0。
- 本次实跑调用 Codex 3 次、Claude Code 1 次；演示仓库只在会话临时目录。

- [x] Task 6.0（gate）：规格修订。`spec/claude-review.md`「Claude Code 探测期限放宽」节，用户 2026-11-26 批准，原话「批准；Q1 15 秒；Q2 不重试」。修订前分段计时 18 次：三个探测各 0.3～0.6 秒、整体约 2 秒，未复现慢启动。
- [x] Task 6.1（report）：期限 15 秒（CR-22）。`test-claude-review.py` 原断言「三个探测期限都是 5」随规格修订改为 `[15, 15, 15]`，另断言 `PROBE_DEADLINE == 15`；先失败（`[5, 5, 5] != [15, 15, 15]`），加常量后通过。`review_native.py:157` 的运行时探测与 `review_guest_entry.py:186` 的访客探测仍为 5 秒，不属规格所说的三个 CLI 探测，实测超时码也都来自 CLI 探测，本次不改。
- [x] Task 6.2（report）：auto 选择带阶段码（CR-23）。新增 `choose` 按序写入「主码 + 阶段码」、`ClaudeCheckTests`（探测失败返回两码、`authentication_missing` 只返回一码）、`doctor --reviewers` 只显示主码 4 处用例，先失败（3 + 1），改 `reviewer_select.choose`／`claude_check` 与 `review_doctor.reviewers` 后 `test-reviewer-select.py`、`test-review-backends.py`、`test-claude-review.py` 通过。
- [x] Task 6.3（report）：文档。英文规格补同一节并在原 Q1 后注明已修订；中英待发行说明补「探测期限放宽到 15 秒」小节及影响面、验证段落。
- [x] Checkpoint A（report）：快检查、全量与产物校验。2026-11-26：`validate.sh --quick` 选 23/35 个套件，退出 0，85 秒；全量退出 0，101 秒，`Ran` 合计 547（542 + doctor 子命令 1 + 本次新增 4）；`git diff --check`、共享段、本机路径通过；产物校验 7 项通过。
- [x] Checkpoint B（gate）：`/delegate:review --backend claude-code` 审查与提交。用户回「审查」「提交并推送开 PR」「合并」：PR #57 合并（2193301），首轮 CI 的 `review-execution` 期限过紧另行修复后通过；随 0.12.4 发版。
- [ ] Task 7（gate）：Task 6 发版后用安装版重跑 M1 的 U2（至少连续 3 次），交用户判定 M1。

探测期限放宽 · 代码审查（2026-11-26，同厂商审查，`/delegate:review --backend claude-code`，安装版 0.12.3，模型 claude-opus-5-5；输入为工作区全部改动，排除本模块 plan、todo，依据 `spec/claude-review.md`；用户原话「审查」）：completed，审 10 个文件、未审 0，1 条阻断。
- 阻断 1：CR-23 只测了零件（`choose` 展开、`claude_check` 返回值、doctor 显示），没走 `--backend auto` 的「未审」报告端到端路径。属实，按建议在 `test-review-cli.py` 加 `test_unreviewed_report_names_the_failing_probe`：用测试开关让 Claude Code 返回「主码 + 阶段码」（探测超时、清理未确认两例），断言报告 `diagnostics` 依次为 `no_reviewer_available`、`codex_cli_missing`、主码、阶段码；另断言 `authentication_missing` 不带阶段码。实现已在，新用例直接通过；变异验证：临时把 `choose` 改成只追加主码，新用例两例都失败，随后还原（还原时 `cp` 带交互确认卡住一次，停掉后用 `/bin/cp -f` 还原并核对），`test-review-cli`、`test-reviewer-select`、`test-review-backends`、`test-claude-review` 全部通过。补测后全量退出 0，93 秒，`Ran` 合计 548。
- PR #57 首轮 CI（2026-11-26）：`test (3.13)` 通过；`test (macos-system)` 失败，`test-review-execution.py` 的 `test_codex_review_never_uses_a_configured_approver` 返回 124。原因：该文件所有用例把 `DELEGATE_TIMEOUT_SECONDS` 固定为 1 秒，正常模式也要求假 Codex 1 秒内跑完；PR #54 起套件并行，CI 系统 Python 负载下偶尔超时。与本次改动无关，属并行暴露的既有计时过紧。修复：只有 `hang` 模式（验证超时分支）保留 1 秒，其他模式 8 秒；断言 108 条不变。两个 Python 版本单独跑通过，系统 Python 全量退出 0（100 秒，548 项）。
