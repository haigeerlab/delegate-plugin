# 任务清单：review-snapshot-recheck

计划：[plan.md](plan.md)；规格：[spec](../../spec/review-snapshot-recheck.md)。
授权：用户 2026-11-23 对修订后的 Spec 与 Plan 原话「批准，开始实现」（Codex 两轮仍有阻断，按规则交用户批）。范围：改本仓库文件、跑免费测试；做到 Checkpoint 2（gate）停下。本地提交、推送、PR、发版与通知不在此授权内。

- [x] Task 1：先写快照复审的测试并确认红
- [x] Task 2：实现快照复审的范围判定
- [x] Task 3：提示词说明参考文件
- [x] Task 4：接口 1.6
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 5：文档同步
- [x] Checkpoint 2（gate）：复审（本地提交须另行明确同意）
- [x] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-23）：** `test-review-recheck.py` 新增 `SnapshotScopeTests` 9 项（临时仓库，含 `--object-format=sha256`、附注标签、`refs/replace --graft`、`--filter=tree:0` 部分克隆）；`test-review-cli.py` 新增 `SnapshotRecheckCLITests` 2 项（借用 `test-review-execution.py` 的 Codex 桩，第一轮 `--paths` 快照带一条阻断，第二轮带 `--previous-report`；负例 7 种 × 真实运行与 `--dry-run`）。改实现前红：单元 `test_same_commit_and_descendant_pass`、`test_sha256_repository_passes`（报 mismatch）与 `test_mixed_snapshot_and_range_are_rejected_both_ways`（没拒）；CLI 正例（退出 127）与「先快照后区间」两例（没拒）。标签、编号格式、替换对象、部分克隆、另一历史、`paths` 不同等负例旧实现本来就拒，按 Plan 作为回归检查保留。「先区间后快照」的 CLI 例本轮 `from` 必然不同，旧实现也拒；`from` 相同的那种由单元测试覆盖。

**Task 2（2026-11-23）：** `review_recheck.check_scope` 加快照分支：恰好一轮快照即拒；两轮快照时 `same_history()` 校验 40/64 位小写十六进制且与本轮等长，`git cat-file -t` 须为 `commit`，再 `git merge-base --is-ancestor`；两次调用都 `--end-of-options`、`GIT_NO_REPLACE_OBJECTS=1`、`GIT_NO_LAZY_FETCH=1`、`GIT_TERMINAL_PROMPT=0`、stdin 接空、30 秒超时，任何失败按 mismatch。Task 1 的用例全绿。`PreviousReportCLITests` 的上一轮报告夹具原为 `from = to = old`（快照形状）而本轮是区间，按新规则属于混合基准被拒；夹具本意是区间报告，改为 `to = new`，断言不改。

**Task 3（2026-11-23）：** 先写断言并确认红（`CONTEXT_FILES_INSTRUCTION` 不存在）：`test-review-context.py` 新增 3 项（常量文本与规格一致；与复审说明共存时顺序为复审说明→本说明→`Task:`；`context_files` 为空或缺失时与改动前逐字相同，期望串按 0.10.0 原文写死）；`test-review-execution.py` 测 Codex 提示词；`test-claude-review.py` 从假调用的 stdin 截取 Claude 提示词；`test-review-guest.py` 走 `review_transport.request_payload` 还原访客上下文后截取提示词。实现后四个套件全绿。

**Task 4（2026-11-23）：** `test-interface.py` 改为期待 1.6 与 `snapshot: true`，先红（2 项失败）；改 `interface.json` 后通过。`scripts/tests/test-release-prepare.py` 里的 `1.5` 是自带夹具仓库的内容，不受影响。

**Checkpoint 1（report，2026-11-23）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` → `validate: ok`；`claude plugin validate .`、`claude plugin validate ./plugins/delegate` → 均 `Validation passed`；`git diff --check` 报英文待发行说明末尾多一空行（Task 5 期间写入），去掉后通过。

**Task 5（2026-11-23）：** SR-06 逐项：
- 中文合同 `spec/review-snapshot-recheck.md`、英文 `docs/en/SPEC-review-snapshot-recheck.md`：与实现一致（五步判定、对象检查、提示词原文）。
- 用法草案 `spec/usage/auto-takeover-review.md`：U3 与 M2 已在 Spec 阶段写入，与实现一致。
- 英文能力图 `docs/en/capability-map.md`：新行与构建顺序已同步。
- `spec/integration-interface.md` 及英文页：在 1.5 指向句后各加一条 1.6 指向，含快照复审比 `scope.files` sha256 的调用方规则；只加不改。`verify-artifacts` 因此报「批准后已修订」，留待 Checkpoint 2。
- 插件 `README.md`／`README.en.md`：「对外接口」加「快照审查的复审（接口 1.6 起）」条目；读报告规则补「快照复审比 `scope.files` sha256」。
- `docs/releases/unreleased.md` 及英文页：写入 0.11.0 的标题行、变化、影响面、验证与已知限制；「暂无未发布变更」改为「的未发布变更见下」（发版脚本两种都认）。

**Checkpoint 2（gate，2026-11-23）：** 用户复审实际 diff 后原话「通过，本地提交」。重新记录 `spec/integration-interface.md` 的批准标记，`verify-artifacts` 恢复 0 警告；在本分支本地提交一次（不推送）。

**Checkpoint 3（gate，2026-11-23）：** 最终提交 `8c9689d` 上重跑：`validate: ok`、两项 plugin validate 通过、`git diff --check` 通过、工作区干净；`module_scope.py check --base cecad55` 越界 0。SR-01～SR-07 全部通过，未实测：真实模型是否遵守参考文件说明、访客路径。用户原话「通过，推送开 PR」。拟回告（mc-coord #22261、ecosystem-lead）待 0.11.0 发版后给用户看全文再发。

## 返工：参考文件不参与覆盖（S10，2026-11-24）

起因：M2 用安装版 0.12.0 实跑 U3，首轮 `failed`／`review_incomplete`，`spec/calc.md` 记为 `coverage_not_reported`。用户原话「按方案 A 返工」。Spec 加 S10 与 SR-08，修订交用户复审后才动代码。

- [x] Checkpoint R0（gate）：Spec 修订（S10、覆盖一节、SR-08）用户复审 — 2026-11-24 用户原话「批准，开始实现」，已重新记录批准标记
- [x] Task R1：先写测试并确认红（`test-review-result.py` 覆盖三例；`test-review-cli.py` 加 `--paths … --spec …` 桩端到端，桩只报告被审文件） — 红：结果校验 3 例失败、端到端两档 `failed`（reviewed=1/2）
- [x] Task R2：实现（上下文标出只作参考的文件；`review_result` 覆盖校验跳过未报告的只作参考文件） — 在 `review_result.content_result` 用已有的 `context_files` 与 `scope` 判定，未新增上下文字段；两套测试转绿
- [x] Task R3：文档同步（待发行说明中英文；插件 README 如有覆盖说明则补一句） — 待发行说明中英文各加一节；插件 README 中英文各补一句
- [x] Checkpoint R1（report）：免费验证全绿 — 2026-11-24 `scripts/validate.sh` 退出 0；`claude plugin validate .` 与 `./plugins/delegate` 通过；`git diff --check` 无问题；verify-artifacts 6 通过 0 警告
- [x] Checkpoint R2（gate）：复审与本地提交（须另行明确同意） — 2026-11-24 用户原话「通过，本地提交」
- [ ] Checkpoint R3（gate）：交付验收，推送开 PR（须另行明确同意）
- [ ] Task R4：发补丁版后用安装版重跑 U3 三步，交用户判定 M2
