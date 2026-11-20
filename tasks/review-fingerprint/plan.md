# 实施计划：review-fingerprint

<!-- spec-guard: review approved -->

日期：2026-11-20。规格：[spec/review-fingerprint.md](../../spec/review-fingerprint.md)（用户 2026-11-20 批准，原话「批准，写英文页和 Plan」，指纹 1e7ad24d735f）。任务：[todo.md](todo.md)。来源：总账 S98。

## 架构决定

- **算法与取数分开。** `review_fingerprint.py` 只有纯函数：输入「路径 → (from_mode, from_oid, to_mode, to_oid)」，输出规范文本和 sha256，不调 git。取数放在 `review_context.py`，用一次 `git diff --raw -z --no-renames --no-abbrev --no-relative` 拿到两侧条目。
- **路径集合复用现有结果。** P 就是现有代码里生成 `diff` 时用的那组名字（`changed` 中落在范围内的），不另算一遍，保证与 `diff_sha256` 覆盖的文件一致。
- **报告里只加字段。** `review_result.base_report()` 在 `scope` 下多输出 `fingerprint`；`delegate_backend.py` 里取上下文前失败的占位同步加 `fingerprint: None`。其他报告字段一个不改。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Checkpoint 1（report）→ Task 5 → Checkpoint 2（gate：复审与本地提交）
→ Checkpoint 3（gate：交付验收）
```

## Task 1：规范文本与 sha256（纯函数）

**描述：** 新建 `review_fingerprint.py`，提供 `canonical(entries)` 和 `fingerprint(entries)`；`entries` 是「路径 → 四元组」。按 UTF-8 字节序排序；版本头 `delegate-blob-pairs-v1`；返回 `{'algorithm': 'blob-pairs-v1', 'sha256': …, 'paths': […]}`。新建 `test-review-fingerprint.py`，并把 `review-fingerprint` 套件加进 `scripts/validate.sh` 和 `scripts/tests/test-validation-discovery.py`。

**验收条件：** 先红后绿；FP-01：固定测试向量的规范文本逐字节一致、sha256 等于测试里写死的值；空集合只有版本头；中文路径与大小写按字节序；64 位全零编号原样参与。

**验证：** `python3 -B plugins/delegate/tests/test-review-fingerprint.py`、`python3 -B scripts/tests/test-validation-discovery.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/review_fingerprint.py`、`plugins/delegate/tests/test-review-fingerprint.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`。**规模：** S。

## Task 2：commits 模式取两侧条目并生成指纹

**描述：** `review_context.py` 在 `commits` 模式下，对 P 跑一次 `git diff --raw …`，解析出四元组；解析出的路径集合与 P 不同，就报 `fingerprint_inputs_inconsistent`（`ContextError`）。结果写进上下文的 `fingerprint`；其他模式为 `None`。`--raw` 输出中的 `040000` 不会出现（diff 只列文件），但解析时按「不存在」处理以防万一。

**验收条件：** 先红后绿；FP-02：新增、删除、修改、只改权限、文件变软链接、文件变目录六种形态，结果与测试里用 `git ls-tree` 独立复算一致；FP-03：在仓库 `.git/config` 设 `diff.algorithm=patience`、`diff.noprefix=true`、`diff.context=10`、`core.quotepath=false`、`core.abbrev=12`，加 `.gitattributes` 的 `-diff`，`diff_sha256` 改变而指纹不变；FP-04：`staged`、`unstaged`、`working-tree` 为 `None`，被 `exclude` 的文件不在 `paths`，`paths` 与生成 diff 的文件集合相同；条目不一致时报固定码、没有半截指纹（用假 `git()` 返回缺一项的输出）。

**验证：** `python3 -B plugins/delegate/tests/test-review-context.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/review_context.py`、`plugins/delegate/tests/test-review-context.py`。**规模：** M。

## Task 3：报告输出 fingerprint

**描述：** `review_result.base_report()` 的 `scope` 加 `fingerprint`；`delegate_backend.py` 取上下文前失败的占位加 `fingerprint: None`；`delegate_cli.py` 若有按字段名白名单转发上下文的地方，同步加上。检查审查预览（`--dry-run`）是否需要显示，不需要就不改。

**验收条件：** 先红后绿；Codex 与 Claude Code 两个后端的报告都有 `scope.fingerprint`；取上下文前失败时为 `null`；`diff_sha256` 与已有字段的值不变（现有测试不改断言）。

**验证：** `python3 -B plugins/delegate/tests/test-review-result.py`、`python3 -B plugins/delegate/tests/test-review-cli.py`、`python3 -B plugins/delegate/tests/test-review-backends.py`

**依赖：** Task 2。**文件：** `plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/delegate_cli.py`（如需）、对应测试。**规模：** S。

## Task 4：接口 1.4

**描述：** `interface.json` 的 `interface` 改为 `"1.4"`，`review.report` 加 `fingerprint`；`test-interface.py` 的版本断言改为 1.4，新增 `review.report.fingerprint` 整体相等断言，并核对 `algorithm` 与 `review_fingerprint` 模块里的常量相同；断言报告的稳定字段里有 `scope.fingerprint`。

**验收条件：** 先红后绿；FP-05：`interface.json` 与规格一致，其余字段不变；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 3。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

总验证 `validate: ok`、两项 plugin validate、`git diff --check` 通过；把命令与结果记入 todo 后继续。

## Task 5：文档同步

**描述：**

- 插件中英文 README 的「对外接口」一节：报告字段表加 `scope.fingerprint`，写算法名、只在 `commits` 输出、`diff_sha256` 只在本机有效、使用方解读规则三条、浅克隆要能取到 `from`。
- `spec/integration-interface.md` 及英文页：在接口版本说明后加一句 1.4 的指向句，指向本规格；`run-rules` 规格里「1.4 的 run.restore…」那句不改（历史记录），在本规格 A6 已说明顺延。
- 中英文 `docs/releases/unreleased.md` 加本项。

**验收条件：** FP-06 完成。integration-interface 改动后 `verify-artifacts` 会报「批准后已修订」，这是预期的，在 Checkpoint 2 交你复审后重新记录批准标记。

**验证：** `verify-artifacts`、`git diff --check`

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：复审与本地提交

交你复审实际 diff，重点是 integration-interface 的指向句；通过后重新记录它的批准标记，`verify-artifacts` 恢复 0 警告，在本分支本地提交一次。

## Checkpoint 3（gate）：交付验收

按最终验收格式报告 FP-01～FP-07 的结果、证据位置和未验证项（跨 git 版本只靠算法保证，未实测）。推送、开 PR、合并、v0.9.0 发版和通知 ecosystem-lead 另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| `--raw` 输出受某个仓库配置影响 | 中 | FP-03 的配置干扰测试覆盖常见项；`--no-abbrev`、`--no-renames`、`--no-relative`、`-z` 显式写死 |
| 指纹路径集合与 diff 覆盖的文件不一致 | 高 | 复用同一组名字；不一致时报固定码，不出半截指纹 |
| 使用方把「指纹一致」当成「可以合并」 | 中 | README 和接口合同写明解读规则；delegate 不做这个判断 |
| 1.4 与原先预告的 1.4 内容冲突 | 低 | 规格 A6 写明顺延；那三项未立项 |

## 开放问题

- 无。浅克隆是使用方的部署问题，只在 README 提醒。
