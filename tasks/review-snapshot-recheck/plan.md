# 实施计划：review-snapshot-recheck

<!-- spec-guard: review approved -->

日期：2026-11-23。规格：[spec/review-snapshot-recheck.md](../../spec/review-snapshot-recheck.md)（用户 2026-11-23 批准，原话「批准」）。任务：[todo.md](todo.md)。依赖已完成的 [review-recheck](../review-recheck/plan.md)。

## 架构决定

- **只改 `check_scope`。** 范围判定集中在 `review_recheck.check_scope(report, context)`，按规格「范围判定」五步改写：先比 `paths` 与 `mode`；非 `commits` 直接通过；恰好一轮是快照即拒（两种顺序都拒，`from` 相同也拒）；两轮都是快照时做对象检查与祖先检查；两轮都是区间照旧比 `from`。CLI 调用点、诊断码与失败路径都不变。
- **对象检查与祖先检查用 git 子进程，不经 shell。** 上一轮 `to` 先按 40 或 64 位小写十六进制校验（兼容 SHA-1 与 SHA-256 仓库），且长度须等于本轮已解析的完整 `to`（防止 SHA-256 仓库里 40 位前缀被当缩写解析），不合格直接拒；再在 `context['repository']` 下运行 `git cat-file -t --end-of-options <上一轮 to>`，输出须是 `commit`（标签对象等一律拒）；最后 `git merge-base --is-ancestor --end-of-options <上一轮 to> <本轮 to>`，退出 0 通过。两次调用都设 `GIT_NO_REPLACE_OBJECTS=1`（判定以原始对象和历史为准，不受 `refs/replace` 影响）与 `GIT_NO_LAZY_FETCH=1`（部分克隆里缺对象时不向远端按需获取），stdin 接空。任何非 0 退出、超时、找不到 git 都按 `previous_report_scope_mismatch`；git 输出丢弃。
- **提示词加一段常量。** `review_context.py` 新增 `CONTEXT_FILES_INSTRUCTION`，`task_prompt()` 在 `context.get('context_files')` 非空时放在复审说明之后、`Task:` 之前；为空时提示词逐字不变。Codex、Claude Code 与访客路径都经 `task_prompt()`，测试分别从三条路径的桩里截取实际提示词断言。
- **接口只加键。** `interface.json` 的 `interface` 改 `1.6`，`review.recheck` 加 `"snapshot": true`；插件版本号留给发版准备脚本改。
- **执行方式。** 串行，在主会话写（用户 2026-11-23 定：实现类 task 自己写，不派 Codex）；每个行为任务先写测试并确认红，再实现。

## 顺序与依赖

```text
Task 1（测试先红）→ Task 2（实现转绿）→ Task 3 → Task 4 → Checkpoint 1（report）→ Task 5
→ Checkpoint 2（gate：复审；本地提交须你另行明确同意）→ Checkpoint 3（gate：交付验收）
```

## Task 1：先写快照复审的测试并确认红

**描述：** 在改任何实现之前，写好两层测试并运行确认红：

- `test-review-recheck.py`（临时 git 仓库，直接调 `check_scope`）：正例——同一提交、后代提交；负例——另一分支、上一轮 `to` 不存在、上一轮 `to` 是指向祖先提交的附注标签对象、编号格式不对（短编号、大写、选项样式如 `--all`、SHA-256 仓库里祖先提交的 40 位前缀）、用 `refs/replace` 把非祖先替换成祖先、部分克隆里缺失的对象（本机做不出部分克隆时跳过并记录）、`paths` 不同、上一轮快照本轮区间、上一轮区间本轮快照（两种混合都让 `from` 相同）；另建一个 `--object-format=sha256` 的临时仓库测同一提交与后代提交（本机 git 不支持时跳过并在记录里写明）。
- `test-review-cli.py`（桩后端，端到端）：第一轮 `--paths` 快照（桩输出至少一条阻断发现）得到报告，提交返工后第二轮同样 `--paths` 带 `--previous-report` 应通过，并断言执行器被调用、`execution_status=completed`、`recheck.previous_report_sha256` 与第一轮文件一致、`recheck.items` 含第一轮那条阻断；SR-02 每个负例参数化，逐例断言 `previous_report_scope_mismatch`、`execution_status=conditions_missing`、退出 127、`backend_started=false`、执行器未被调用、诊断不含路径与 git 输出；`--dry-run` 正反各一例，正例断言执行器未被调用。

**验收条件：** 返工后的快照正例（单元与端到端）和共享 `from` 的两种混合负例在现有代码下失败（红）；标签对象、编号格式、替换对象、缺失对象等负例在旧实现下可能已经通过，作为回归检查保留，不要求先红；原有 RC-03 用例仍通过；红的用例与原因记入 todo。

**验证：** `python3 -B plugins/delegate/tests/test-review-recheck.py`、`python3 -B plugins/delegate/tests/test-review-cli.py`

**依赖：** 无。**文件：** `plugins/delegate/tests/test-review-recheck.py`、`plugins/delegate/tests/test-review-cli.py`。**规模：** M。

## Task 2：实现快照复审的范围判定

**描述：** 按架构决定改 `check_scope`。预期不改 CLI；若 Task 1 的端到端用例暴露 CLI 需要改，停下说明再改。

**验收条件：** Task 1 的全部用例转绿；SR-01、SR-02、SR-03（原有 RC-03 用例不改断言仍过）。

**验证：** 同 Task 1 的两条命令。

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/review_recheck.py`。**规模：** S。

## Task 3：提示词说明参考文件

**描述：** 先在测试里写断言并确认红，再在 `review_context.py` 加 `CONTEXT_FILES_INSTRUCTION` 与条件拼接。断言分三处：`test-review-context.py` 直接测 `task_prompt()`；`test-review-execution.py` 从 Codex 桩截取实际提示词；Claude Code 与访客路径从各自现有测试的桩里截取（沿用现有套件截取提示词的写法）。

**验收条件：** SR-04——三条路径在 `context_files` 非空时都带完整固定说明且位于 `Task:` 之前，与复审说明共存时顺序固定；为空时提示词与改动前逐字相同（用改动前的期望字符串断言）。

**验证：** `python3 -B plugins/delegate/tests/test-review-context.py`、`python3 -B plugins/delegate/tests/test-review-execution.py`、`python3 -B plugins/delegate/tests/test-claude-review.py`、`python3 -B plugins/delegate/tests/test-review-guest.py`

**依赖：** 无（与 Task 1、2 独立，串行执行）。**文件：** `plugins/delegate/scripts/review_context.py`、上述四个测试文件。**规模：** S。

## Task 4：接口 1.6

**描述：** `interface.json` 改版本号并加 `review.recheck.snapshot`；`test-interface.py` 的整体比对同步。

**验收条件：** 先红后绿；SR-05；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 2。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`、两项 plugin validate、`git diff --check` 通过；把命令与结果记入 todo 后继续。

## Task 5：文档同步

**描述：**

- 插件中英文 README「对外接口」：加「快照复审（接口 1.6 起）」条目、调用方规则（快照复审比两轮 `scope.files` 的 sha256，不比指纹；`review.recheck.snapshot` 判断支持；混合基准与非同一历史报 mismatch）、提示词对参考文件的说明一句。
- `spec/integration-interface.md` 及英文页：在 1.5 指向句之后补一句 1.6 的指向，并在调用方规则里写入快照复审比 `scope.files` sha256 的要求（只加不改）。
- 中英文 `docs/releases/unreleased.md` 加本项。
- 核对已完成项：中英文合同（本模块 Spec 与英文页）、用法草案 U3/M2、英文能力图与实现一致，不一致就改。

**验收条件：** SR-06 逐项核对，把每一项的文件与位置记入 todo。integration-interface 改动后 `verify-artifacts` 报「批准后已修订」，预期内，Checkpoint 2 交你复审。

**验证：** `verify-artifacts`、`git diff --check`、逐项核对记录。

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`；核对时可能改 `docs/en/SPEC-review-snapshot-recheck.md`、`spec/usage/auto-takeover-review.md`、`docs/en/capability-map.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审

先在文档同步完成后对当前树跑一遍总验证；再交你复审实际 diff，重点是对象检查与祖先检查的失败分支、提示词说明和 integration-interface 的改动。你认可后我重新记录 integration-interface 的批准标记；**本地提交是独立授权项**：只有你在这一步明确同意提交，才在本分支本地提交；Codex 对 Plan 的批准不授权提交。

## Checkpoint 3（gate）：交付验收

在 integration-interface 批准标记重新记录（及经你同意的本地提交）之后，对最终交付树重跑 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`、`git diff --check`，用这次结果作为 SR-07；按最终验收格式报告 SR-01～SR-07 的结果、证据位置和未验证项，列出实际改动文件与越界检查结果。推送、开 PR、v0.11.0 发版、告知 ecosystem-lead 与 mc-coord 另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 拿另一条分支上的快照报告硬做对照 | 高 | 祖先检查；任何 git 失败都按对不上处理 |
| 上一轮报告里的 `to` 被篡改成 git 选项、表达式、缩写或标签对象 | 中 | 校验完整编号格式且与本轮等长，`cat-file -t` 须为 `commit`，参数前加 `--end-of-options`，不经 shell |
| 替换对象或部分克隆改变判定、触发联网 | 中 | `GIT_NO_REPLACE_OBJECTS=1`、`GIT_NO_LAZY_FETCH=1`、stdin 接空，用临时仓库验证 |
| 快照与区间混着复审 | 中 | 恰好一轮是快照即拒，两种顺序都测 |
| SHA-256 仓库被误拒 | 低 | 编号格式接受 40 或 64 位，用 SHA-256 临时仓库测 |
| 提示词改动波及没有参考文件的审查 | 中 | 为空时逐字不变，用改动前字符串断言；三条路径分别截取 |
| 快照复审时调用方误用指纹核对 | 低 | README 与接口合同写明比 `scope.files` |
| 模型仍对参考文件提发现 | 低 | 只是提示约束，开放问题里留观察 |

## 开放问题

- 无。

## 外部审查意见

<!-- spec-guard: codex-review round=1 blocking=8 sha256=7bd8f97e9520 -->

第 1 轮 8 条阻断全部采纳：混合基准一律拒并补两种顺序的测试；编号兼容 SHA-256；加 `cat-file -t` 拒标签对象（Spec 同步修订）；SR-02 负例全部参数化进 CLI 测试；端到端测试排到实现之前确认红；SR-04 分三条路径截取提示词断言；Task 5 补齐 SR-06 核对项与接口合同的调用方规则；本地提交改为 Checkpoint 2 上的独立授权。
<!-- spec-guard: codex-review round=2 blocking=6 sha256=0ff524223805 -->

第 2 轮：第 1 轮 8 条全部 resolved；新提 6 条阻断全部采纳：编号长度须与本轮一致；禁用替换对象与按需获取并加临时仓库用例；标签等负例改为回归检查、先红只要求快照正例与混合负例；CLI 正例补执行器、报告与 `recheck` 断言；SR-07 改在文档与标记完成后对最终树重跑。两轮仍有阻断，按规则交用户批。
