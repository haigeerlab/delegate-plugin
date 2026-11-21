# 规格：review-severity（审查发现的严重程度）

<!-- spec-guard: review approved 9514e71d1cef -->

简体中文 | [English](../docs/en/SPEC-review-severity.md)

2026-11-21 起草。来源：生态总账 S101「自动接管」合并方案 r2（plugin-ecosystem 仓 `research/2026-11-21-自动接管合并方案.md`，提交 bfce091，第 2 节 delegate 行），用户已批准该方案，原话「按推荐批准」；由 autopr-design 转达（#21878）。用户 2026-11-21 在本会话确认开工与前提，原话：「接，按假设写规格」；同日批准本规格并就 Q1 选 A，原话：「批准；Q1 A」。

## 起因

自动接管流程里，Codex 的审查意见要分成两类：**阻断**（必须改，改完复审，两轮仍未解决就交给人）和**建议**（Claude 自己决定改不改，写一句理由留档）。delegate 0.9.0 的发现只有 `title、file、line、trigger、impact、evidence、suggestion、unverified`，没有严重程度；调用方只能从 `impact` 文字去猜，不可靠。

## 前提

用户 2026-11-21 确认（「接，按假设写规格」）：

- **A1** 拆两个模块：本模块只做严重程度；复审对照上一轮是后续模块 [review-recheck](../spec/CAPABILITY-MAP.md)。两者都完成后一起发 v0.10.0。
- **A2** 接口 1.4 → 1.5，只增字段；审查报告 `schema_version` 仍为 `1`。
- **A3** 判据由 autopr-design 起草，写进本规格「判据」一节，双方确认、交用户批准（已于 #21881 收到，见下文）。
- **A4** 分类由审查模型按判据标；调用方缺字段或遇到不认识的值，一律按 `blocking` 处理（合并方案原文）。

本规格新提出、请用户审时一并确认（autopr-design #21881 回复与编排没有冲突）：

- **A5 严格校验。** 模型必须给每条发现输出 `severity`，取值只能是 `blocking` 或 `suggestion`；缺失或取值不对，整次审查按现有规则判 `failed`（诊断 `finding_invalid`），不由 delegate 替模型补成 `blocking`。理由：两个后端都用结构化输出强制 schema，正常不会出现；真出现说明这次输出不可信，按「没有结论就停」处理更安全。
- **A6 判据带版本名。** 判据文字整体有一个名字（第一版 `severity-v1`），写进 `interface.json`；以后改判据只能换新名字，旧名字永远指同一段文字。报告本身不重复写判据名，以接口声明为准。
- **A7 不加汇总字段。** 不新增「有无阻断」「阻断条数」之类的字段，也不新增「通过／不通过」；调用方按 `findings[].severity` 自己数。审查报告仍不是合并许可。
- **A8 判据只在 delegate 里。** 判据固定写在 delegate 的审查提示词里，`--task` 文字不能覆盖或改写它；要换判据走本仓库的规格流程。

依赖：[claude-review](claude-review.md)（两个后端共用的提示词与结果校验）、[integration-interface](integration-interface.md)（`interface.json` 与报告合同、版本规则）。

## 报告字段

`findings[]` 每一项新增必填字段 `severity`：

```json
{"title": "…", "file": "…", "line": 12, "trigger": "…", "impact": "…",
 "evidence": "…", "suggestion": "…", "unverified": [], "severity": "blocking"}
```

- 取值：`blocking`（阻断）或 `suggestion`（建议），小写，没有第三种。
- delegate 在结果校验后原样带出，wrapper 加的 `location_verified` 等字段不变。
- 没有发现时 `findings` 为空数组，没有别的变化。

**调用方的解读规则（写进 README 和接口合同）：**

- `severity` 缺失（例如读到 0.9.0 及以前的报告）或取值不认识，一律按 `blocking`。
- 只有 `execution_status=completed` 且 `review_outcome` 为 `findings` 或 `no_findings_in_scope` 时，严重程度才有意义；其他情况按「没有结论」停下，不看发现。
- `severity` 是审查模型按判据给的判断，delegate 只保证格式与取值，不保证判断正确。没有阻断发现不等于没有缺陷，更不等于可以合并。

## 判据 `severity-v1`

autopr-design 起草，2026-11-21 发来（#21881），称用户已批准，原话「按推荐批准」；存档在 plugin-ecosystem 仓 `research/2026-11-18-自动PR系统设计/review-severity-criteria.md`（提交 5291680，含 U1 修订），与下文逐字一致。本节文字与提示词常量 `SEVERITY_CRITERIA` 逐字一致。

```text
Mark a finding "blocking" when any of these is true:
B1. The change fails to do what the task or its stated acceptance criteria require, or contradicts them.
B2. You can name a concrete input or scenario where the change gives a wrong result, crashes, loses data, or breaks behavior that worked before.
B3. The change introduces a security risk: a committed secret, injection, untrusted input reaching a shell or eval, an auth or permission bypass, or broader token or workflow permissions.
B4. The change weakens verification: it deletes or loosens test assertions, skips or disables tests or checks, adds lint or type suppressions, or lowers thresholds, without the task asking for it.
B5. The change touches files or behavior outside the scope the task declares.
B6. The change performs an irreversible or destructive action (data migration, deletion, force push, publish, deploy, release) that the task did not explicitly ask for.
B7. The change adds or alters an external interface, a stored data format, or user-visible behavior that the task does not mention.
B8. The task requires tests for the new behavior and the change does not include them.

Mark a finding "suggestion" when none of B1-B8 applies, for example:
S1. Naming, readability, comments, style, or duplication.
S2. A refactor or simpler design that would not change behavior.
S3. Missing tests for new behavior when the task does not require them.
S4. Performance or robustness concerns without a concrete scenario that causes harm.

When unsure:
U1. If the finding would fall under B1-B8 were it true but you cannot confirm it from the code, mark it "blocking" and list in "unverified" what you could not confirm.
U2. Otherwise, if you cannot point to a specific requirement it violates or a concrete scenario where it fails, mark it "suggestion".
```

**U1 修订：** 原稿 U1 写的是 `set "unverified" to true`，与 delegate 的 `unverified`（字符串数组）不符。用户 2026-11-21 选定改法（原话「批准；Q1 A」），autopr-design 同意并同步存档（#21904）；名字仍为 `severity-v1`。调用方按「`unverified` 非空」识别这类发现。

## 提示词

两个后端共用的 `task_prompt()` 在现有说明之后追加一段固定文字：要求每条发现给出 `severity`，并逐字附上「判据」一节的内容。Codex 后端的 `codex_prompt()` 建立在 `task_prompt()` 之上，不另写一份。`--task` 的文字放在判据之后、作为数据部分，不能覆盖判据（A8）。

## 接口 1.5

`interface.json` 的 `interface` 改为 `"1.5"`，`review.report` 下新增：

```json
"severity": {"field": "findings[].severity", "values": ["blocking", "suggestion"],
             "criteria": "severity-v1", "missing": "blocking"}
```

其余字段不变（包括 1.4 的 `fingerprint`）。

## 技术栈与命令

Python 3 标准库，测试用 `unittest` 和桩输出，不跑真实模型、不付费。

```bash
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-execution.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/review_result.py     → FINDING_FIELDS 与 CONTENT_SCHEMA 加 severity（枚举、必填），content_result 校验取值
plugins/delegate/scripts/review_context.py    → task_prompt 追加判据段（常量 SEVERITY_CRITERIA）
plugins/delegate/interface.json               → 1.5，review.report.severity
plugins/delegate/tests/test-review-result.py  → 字段校验、两个后端的报告
plugins/delegate/tests/test-review-context.py → 提示词含判据、--task 在判据之后
plugins/delegate/tests/test-interface.py      → 1.5 断言
spec/review-severity.md、docs/en/SPEC-review-severity.md → 本合同
spec/integration-interface.md 及英文页        → 加 1.5 的指向句
插件 README 中英文、待发行说明                   → 对外接口一节同步
```

## 代码风格

保持现有风格：4 空格缩进，标准库，错误只用固定码。示例（`review_result.py` 现有写法）：

```python
        for key in FINDING_FIELDS - {'line', 'unverified'}:
            if not isinstance(item[key], str) or not 1 <= len(item[key]) <= 4000:
                raise ResultError('finding_invalid')
```

## 测试策略

先写测试并确认红，再实现。

- **校验（`test-review-result.py`）：** 合法的 `blocking`、`suggestion` 原样带出；缺 `severity`、取值为大写、空串、第三种值、非字符串，都判 `finding_invalid`、`execution_status=failed`；Claude 与 Codex 两条路径都覆盖。
- **结构：** `CONTENT_SCHEMA` 与 `schema_for_context()` 里 `severity` 是必填枚举，`additionalProperties` 仍为 `false`。
- **提示词（`test-review-context.py`、`test-review-execution.py`）：** 两个后端的提示词都逐字包含 `SEVERITY_CRITERIA`；`--task` 出现在判据之后。
- **接口：** `test-interface.py` 断言 1.5 与 `review.report.severity`；1.4 的内容不变。

模型按判据标得准不准，免费测试证明不了；本模块不做付费实测，由试点阶段观察。

## 开发边界

- **Always：** 两个后端共用同一结构、同一判据；取值严格校验；中英文合同、README、接口同步。
- **Ask first：** 增加第三种取值；修改 `severity-v1` 的任何文字（只能出新名字）；新增汇总或「通过」字段；提升报告 `schema_version`；提交、推送、发版。
- **Never：** 让 `--task` 覆盖判据；替模型补 `severity`；在 delegate 里判断「可以合并」。

## 成功条件与验证映射

- **SV-01：** 合法取值原样输出；非法或缺失判 `finding_invalid` 与 `failed`（桩测试，两个后端）。
- **SV-02：** 结构化输出 schema 里 `severity` 为必填枚举。
- **SV-03：** 两个后端的提示词逐字包含判据，`--task` 在判据之后。
- **SV-04：** `interface.json` 为 1.5，`review.report.severity` 与本合同一致，已有字段不变；两项 plugin validate 通过。
- **SV-05：** 判据一节已由 autopr-design 起草、双方确认，且与 `SEVERITY_CRITERIA` 逐字一致。
- **SV-06：** 插件中英文 README 的对外接口一节、integration-interface 中英文指向句、中英文合同、待发行说明同步。
- **SV-07：** 总验证、两项 plugin validate、`git diff --check` 通过。

## 开放问题

- ~~Q1 U1 里的 `unverified`~~：已定，见「判据」一节的 U1 修订。
- 模型标注的准确度：试点阶段观察；若常把该阻断的标成建议，改判据出 `severity-v2`。
