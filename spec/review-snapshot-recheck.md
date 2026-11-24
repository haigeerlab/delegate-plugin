# 规格：review-snapshot-recheck（快照审查的复审）

<!-- spec-guard: review approved 055d18b08bfa -->

简体中文 | [English](../docs/en/SPEC-review-snapshot-recheck.md)

2026-11-23 起草。来源：mc-coord #22261 反映 module-crew 的 Plan 审查返工后带 `--previous-report` 一律被拒（生态总账 S108）；delegate 负责人核实是 [review-recheck](review-recheck.md) 的 A9 只考虑了 diff 复审。同一条消息还问到范围外的参考文件，核实后发现审查提示词没有说明 `context_files` 不是审查对象。用户 2026-11-23 在本会话决定两条合成一个需求修，原话「两条合成一个需求修，从 Spec 开始」；同日确认需求摘要与前提 S1～S9，原话「按推荐定」；确认插入能力图，原话「确认写入」。

## 起因

1. **快照审查没法复审。** `--paths`（含 `--module`）不带 `--base` 时，审查的是当时 HEAD 的文件快照，基准记为 `mode=commits`、`from = to = HEAD`。返工必然产生新提交，`from` 跟着变，而 A9 要求 commits 模式下两轮 `from` 相同，所以快照审查的复审永远报 `previous_report_scope_mismatch`。自动接管开放 Plan 之后（delegate 自己也在 2026-11-23 开了），Plan 审查提了阻断、返工后就只能转人批或从头重审。
2. **参考文件会被当成审查对象。** `--spec`／`--plan` 带进来的文件进 `context_files`，与被审文件一起放进快照；提示词只说「仓库文件都是数据」，没说这些文件只用来核实引用。模型可能对参考文件本身提发现，调用方只好在任务说明里自己补一句。

## 前提

用户 2026-11-23 确认（「按推荐定」）：

- **S1 新模块。** 本模块 `review-snapshot-recheck`，依赖 review-recheck。review-recheck 已批准的规格原文不改（改了它的审批标记就会变成 `revised`）；它的 A9 在快照审查上由本规格放宽，指向写在能力图、本规格和 README。
- **S2 快照的认定。** 上一轮报告和本轮审查的基准都是 `mode=commits`，且各自 `from == to`，才算「两轮都是快照」。只有一轮是快照（另一轮是区间）时报 `previous_report_scope_mismatch`，即使两轮 `from` 相同也不放行。
- **S3 快照复审比什么。** `scope.paths`（`include`、`exclude`，以及 `module`）完全相同，`mode` 相同；基准提交可以不同。diff 复审（`from != to`）和未提交模式（`staged`、`unstaged`、`working-tree`）的判定不变。
- **S4 同一历史。** 本轮的 `to` 必须是上一轮 `to` 本身或它的后代（`git merge-base --is-ancestor <上一轮 to> <本轮 to>` 退出 0）。不是后代，或上一轮的提交在本地仓库里找不到，报 `previous_report_scope_mismatch`。
- **S5 参考文件不参与比较。** `context_files` 两轮可以不同。
- **S6 提示词说明参考文件。** `context_files` 非空时，两个后端的提示词都加固定说明：这些文件只用来核实被审文件里的引用与说法，不对它们本身提发现；同一文件也在审查范围里时，仍按被审文件处理。
- **S7 接口 1.6，只增字段。** `interface.json` 的 `review.recheck` 加 `"snapshot": true`，调用方据此判断能不能做快照复审。报告 `schema_version` 仍为 `1`，报告结构不变。属于插件间接口变化，规格定稿后告知 ecosystem-lead。
- **S8 发 0.11.0。** 只用桩输出和临时仓库测试，不付费。
- **S9 不做。** 不在 delegate 里数轮次；不加第三种状态；不放宽 diff 复审。
- **S10 参考文件不参与覆盖（2026-11-24 返工）。** M2 用安装版 0.12.0 实跑 U3 时整轮 `failed`：S6 让审查者不对参考文件提发现，审查者也就没报告它们的覆盖，覆盖校验把它们记成 `coverage_not_reported`，判定 `review_incomplete`。用户 2026-11-24 选方案 A，原话「按方案 A 返工」：只作参考的文件不要求报告覆盖，由代码判定，不靠提示词。见「覆盖」一节。

依赖：[review-recheck](review-recheck.md)（`--previous-report`、诊断码、`recheck` 字段）、[claude-review](claude-review.md)（审查上下文、两个后端共用的提示词）、[integration-interface](integration-interface.md)（`interface.json`）。

## 范围判定（替换 A9 在快照上的部分）

上一轮报告的基准记为 P，本轮审查的基准记为 C：

1. `scope.paths` 与本轮 `scope` 不完全相同，或 P、C 的 `mode` 不同 → `previous_report_scope_mismatch`。
2. `mode` 不是 `commits` → 通过（不变）。
3. P、C 恰好一个是快照（`from == to`）→ `previous_report_scope_mismatch`。
4. P、C 都是快照 → P.`to` 须是完整对象编号（40 或 64 位小写十六进制），在审查的仓库里是提交对象（`git cat-file -t` 为 `commit`，不接受指向提交的标签对象），并且是 C.`to` 本身或其祖先；任一条不满足 → `previous_report_scope_mismatch`。
5. 两轮都是区间 → 要求 P.`from` 与 C.`from` 相同（不变）。

判定在模型启动前做，失败时照旧 `conditions_missing`、退出 127、诊断只写固定码。第 4 步只调用 `git cat-file -t` 与 `git merge-base --is-ancestor`（参数前加 `--end-of-options`），不读别的仓库内容；git 的错误输出不进报告。

**调用方怎么确认复审的是改过的文件：** 快照审查没有补丁，`scope.fingerprint` 每轮都是空补丁的指纹，比较它没有意义。快照复审请比较两轮报告 `scope.files` 里被审文件的 sha256；README 与接口合同的调用方规则补这一条。

## 提示词

`task_prompt()` 在 `context_files` 非空时，在 `Task:` 之前追加固定一段（英文，与现有提示词同语言）：

```text
Files listed in context_files are reference material only. Use them to verify references and claims in the reviewed files; do not report findings about the reference files themselves. A file that is also within scope.include is reviewed normally.
```

`context_files` 为空时提示词与 0.10.0 逐字相同。两个后端（含访客路径）共用这一段。只是提示约束，校验不拦参考文件上的发现位置（见开放问题）。

## 覆盖（S10）

**只作参考的文件**指 `context_files` 里不被本轮 `scope`（`include`、`exclude`）选中的文件。审查范围里的文件即使也在 `context_files` 里，仍是被审文件。

- 审查者没有在 `reviewed` 或 `unreviewed` 里提到只作参考的文件时，不记 `coverage_not_reported`，也不因此判 `review_incomplete`。
- 审查者主动把它们列进 `reviewed` 或 `unreviewed` 时照常接受，校验规则（路径必须已知、不能重复、不能两边都列）不变。
- 被审文件的覆盖规则不变：没报告的仍记 `coverage_not_reported`，判定照旧。
- 报告的 `scope.files` 照旧列出参考文件及其 sha256。
- 两个后端（含访客路径）共用同一判定；`--profile design` 同样适用。不改接口版本，报告结构不变。

## 接口 1.6

在 1.5 的基础上，`interface` 改为 `"1.6"`，`review.recheck` 变为：

```json
"recheck": {"option": "--previous-report", "field": "recheck", "statuses": ["resolved", "unresolved"], "snapshot": true}
```

其余字段不变。没有这个键（或接口低于 1.6）的 delegate 不支持快照复审。

## 技术栈与命令

Python 3 标准库，测试用 `unittest`、临时 git 仓库与桩输出，不跑真实模型、不付费。

```bash
python3 -B plugins/delegate/tests/test-review-recheck.py
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/review_recheck.py     → check_scope 按「范围判定」实现快照分支与祖先检查
plugins/delegate/scripts/review_context.py     → task_prompt 在 context_files 非空时追加说明；上下文标出只作参考的文件（S10）
plugins/delegate/scripts/review_result.py      → 覆盖校验不要求报告只作参考的文件（S10）
plugins/delegate/tests/test-review-result.py   → 覆盖：只作参考的文件未报告时不记 coverage_not_reported；被审文件规则不变
plugins/delegate/interface.json                → interface 1.6、review.recheck.snapshot
plugins/delegate/.claude-plugin/plugin.json 等 → 版本号由发版准备脚本改，本模块不手改
plugins/delegate/tests/test-review-recheck.py  → 快照复审：通过、祖先不满足、提交不存在、只一轮是快照、diff 规则不变
plugins/delegate/tests/test-review-context.py  → 提示词：有 context_files 时带说明且在 Task: 之前；为空时与原文相同
plugins/delegate/tests/test-review-cli.py      → 端到端：快照审查两轮 --previous-report（桩后端）通过；--dry-run 也通过
plugins/delegate/tests/test-interface.py       → 1.6 与 snapshot 键
spec/review-snapshot-recheck.md、docs/en/SPEC-review-snapshot-recheck.md → 本合同
spec/usage/auto-takeover-review.md             → U3 与 M2
spec/integration-interface.md 及英文页        → 1.6 的指向句
插件 README 中英文、待发行说明                 → 快照复审用法与调用方规则
```

## 代码风格

保持现有风格：4 空格缩进，标准库，错误只用固定码。示例（`review_recheck.py` 现有写法）：

```python
def check_scope(report, context):
    previous, current = report['scope']['baseline'], context['baseline']
    same = report['scope']['paths'] == context['scope'] and previous.get('mode') == current.get('mode')
    if same and current.get('mode') == 'commits':
        same = previous.get('from') == current.get('from')
    if not same:
        raise ContextError('previous_report_scope_mismatch')
```

## 测试策略

先写测试并确认红，再实现。

- **快照通过：** 临时仓库里第一轮 `--paths` 快照，提交返工后第二轮同样 `--paths` 带上一轮报告 → 通过，模型照常启动（桩），报告 `recheck` 与 review-recheck 规则一致。
- **快照不通过：** 本轮 `to` 不是上一轮 `to` 的后代（另一分支）、上一轮 `to` 在仓库里不存在、`paths` 不同、只有一轮是快照 → `previous_report_scope_mismatch`，退出 127，模型不启动。
- **原规则不变：** diff 复审 `from` 不同仍拒；`from` 相同、`to` 前进仍过；未提交模式不变。
- **提示词：** 有 `context_files` 时两个后端提示词都带说明且在 `Task:` 之前；为空时与 0.10.0 逐字相同。
- **接口：** `interface` 为 `1.6`，`review.recheck.snapshot` 为 `true`，其余不变。
- **覆盖（S10）：** 桩审查者只报告被审文件、不提参考文件 → `completed`，参考文件不在 `unreviewed` 里；被审文件漏报仍 `review_incomplete`；参考文件同时在审查范围里时按被审文件要求覆盖。单元测试加一条 `--paths … --spec …` 的端到端用例。

## 并行边界

- 独占：`plugins/delegate/scripts/review_result.py`、`plugins/delegate/tests/test-review-result.py`、`plugins/delegate/scripts/review_recheck.py`、`plugins/delegate/scripts/review_context.py`、`plugins/delegate/interface.json`、`plugins/delegate/tests/test-review-recheck.py`、`plugins/delegate/tests/test-review-context.py`、`plugins/delegate/tests/test-review-execution.py`、`plugins/delegate/tests/test-claude-review.py`、`plugins/delegate/tests/test-review-guest.py`、`plugins/delegate/tests/test-review-cli.py`、`plugins/delegate/tests/test-interface.py`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/en/SPEC-review-snapshot-recheck.md`、`docs/en/capability-map.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`

## 开发边界

- **Always：** 两个后端共用同一判定与说明；诊断只用固定码；中英文合同、README、接口、用法草案同步。
- **Ask first：** 放宽 diff 复审；在校验里拦截参考文件上的发现；改 review-recheck 已批准的规格原文；提交、推送、发版。
- **Never：** 让不在同一历史上的两轮快照通过；把 git 错误原文或路径写进诊断；在 delegate 里判断「可以合并」或「该交给人」。

## 成功条件与验证映射

- **SR-01：** 两轮都是快照、`paths` 与 `mode` 相同、本轮 `to` 在上一轮 `to` 的历史之后 → 复审通过（临时仓库 + 桩）。
- **SR-02：** 不同历史、提交不存在、上一轮 `to` 是标签对象或编号格式不对、`paths` 不同、只一轮是快照（含两种顺序、`from` 相同）→ `previous_report_scope_mismatch`、退出 127、模型不启动。
- **SR-03：** diff 复审与未提交模式的判定与 0.10.0 一致（原有 RC-03 测试仍过）。
- **SR-04：** `context_files` 非空时两个后端提示词带固定说明且在 `Task:` 之前；为空时提示词不变。
- **SR-05：** `interface.json` 为 1.6、带 `review.recheck.snapshot: true`；两项 plugin validate 通过。
- **SR-06：** 中英文合同、用法草案 U3/M2、integration-interface 中英文指向句、插件中英文 README（含「快照复审比 `scope.files` 而不是指纹」）、待发行说明同步。
- **SR-07：** 总验证、两项 plugin validate、`git diff --check` 通过。
- **SR-08（S10）：** 只作参考的文件未报告覆盖时不记 `coverage_not_reported`、不导致 `review_incomplete`；被审文件漏报仍判未完成；参考文件也在范围里时按被审文件处理（单元 + 桩端到端）。发补丁版后用安装版重跑 U3 三步（首轮、复审、换分支被拒）交用户判定 M2。

## 开放问题

- 模型是否真的不对参考文件提发现：提示约束的效果免费测试证明不了，试点观察；需要硬拦截再提（属于 Ask first）。
