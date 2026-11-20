# 任务清单：review-fingerprint

计划：[plan.md](plan.md)；规格：[spec](../../spec/review-fingerprint.md)。
授权：用户 2026-11-20 对 Plan 原话「批准，开始实现」。范围：改本仓库文件、跑测试与构建、在本分支本地提交；做到 Checkpoint 2（gate）停下。推送、PR、发版与通知不在此授权内。

- [x] Task 1：规范文本与 sha256（纯函数）
- [x] Task 2：commits 模式取两侧条目并生成指纹
- [x] Task 3：报告输出 fingerprint
- [x] Task 4：接口 1.4
- [x] Checkpoint 1（report）：免费验证全绿
- [x] Task 5：文档同步
- [x] Checkpoint 2（gate）：复审与本地提交
- [x] Checkpoint 3（gate）：交付验收

## 记录

**Task 1（2026-11-20）：** 新建 `test-review-fingerprint.py`，4 项在模块不存在时先红（ImportError），新建 `review_fingerprint.py`（`canonical`、`fingerprint`、`ALGORITHM`）后通过。固定测试向量的 sha256 `dede2917…81bc` 由手工拼出的字节另行算出写死；空集合 `e1355a48…f974`。套件加进 `scripts/validate.sh` 与发现测试，`test-validation-discovery.py` 通过。

**Task 2（2026-11-20）：** `test-review-context.py` 新增 `FingerprintContextTests` 4 项（只复用原夹具，不继承原测试），先红（3 个 KeyError、1 个未报错），实现 `tree_fingerprint()` 后 16 项全过。六种形态与 `git --literal-pathspecs ls-tree` 独立复算一致；配置干扰（`diff.algorithm`、`diff.noprefix`、`diff.context`、`core.quotepath`、`core.abbrev` 加 `.git/info/attributes` 的 `*.txt -diff`）下 `diff_sha256` 改变、指纹不变；三种未提交基准为 `None`；假 `git()` 少给一项时报 `fingerprint_inputs_inconsistent`。属性写在 `.git/info/attributes` 而不是工作区 `.gitattributes`，与 `.gitattributes` 同一机制，又不产生未跟踪文件。一处测试自身的问题：文件变软链接时 diff 文字里同一路径有两个 `diff --git` 头，测试里去重。

**Task 3（2026-11-20）：** `test-review-result.py` 新增 3 项先红后绿：`base_report` 原样带出 `scope.fingerprint`；上下文没有该键时为 `null`；`context_failure` 的占位为 `null`。`base_report` 用 `context.get('fingerprint')`，现有测试构造的上下文不用改。访客路径（`review_transport.request_payload`）本来就转发除 `files` 外的全部上下文字段，无需改动；`--dry-run` 预览未加此字段（规格未要求）。

**Task 4（2026-11-20）：** `test-interface.py` 版本断言改为 1.4、整体比对改为 `test_interface_1_4_is_complete`（1.3 内容原样加 `review.report.fingerprint`）、`SCOPE_FIELDS` 加 `fingerprint`、核对 `algorithm` 与 `review_fingerprint.ALGORITHM` 相同；先红（2 项）后绿。`interface.json` 改为 1.4。

**Checkpoint 1（report，2026-11-20）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0、`validate: ok`；`claude plugin validate .` 与 `./plugins/delegate` 均通过；`git diff --check` 通过。

**Task 5（2026-11-20）：** 插件中英文 README 的对外接口一节加「补丁指纹（接口 1.4 起）」条目、报告字段表加 `scope.fingerprint` 并注明 `diff_sha256` 只在本机有效、解读规则补三条（对比 `paths`、一致不等于可合并、未知算法按无法复算）、提醒浅克隆要能取到 `from`；`spec/integration-interface.md` 与英文页各加一句 1.4 指向句（只加不改）；中英文 `unreleased.md` 加本项；仓库根中英文 README 的故障排查表加 `fingerprint_inputs_inconsistent`（Plan 未列，按诊断码惯例补上）。总验证 `validate: ok`、两项 plugin validate、`git diff --check` 通过。`verify-artifacts` 4 通过、1 警告（integration-interface「批准后已修订」，预期内，等 Checkpoint 2 复审）。

**Checkpoint 2（gate，2026-11-20）：** 用户复审 integration-interface 指向句等改动，原话「通过，本地提交」。已重新记录 `spec/integration-interface.md` 批准标记，`verify-artifacts` 4 通过、0 警告。本地提交一次，未推送。下一步停在 Checkpoint 3（gate）交付验收。

**Checkpoint 3（gate，2026-11-20）：** 用户交付验收原话「验收通过」。FP-01～FP-07 通过；未验证：跨 git 版本一致性（靠算法保证）、真实模型审查报告里的字段（付费，规格未要求）。本模块提交 `248036a` 加本次勾选提交，均未推送。推送、PR、v0.9.0 发版与回复 ecosystem-lead 另行授权。
