# 规格：review-recheck（复审对照上一轮）

<!-- spec-guard: review approved 333dea966f8f -->

简体中文 | [English](../docs/en/SPEC-review-recheck.md)

2026-11-21 起草。来源：生态总账 S101「自动接管」合并方案（plugin-ecosystem 仓 `research/2026-11-21-自动接管合并方案.md`，r2 提交 bfce091 第 2 节 delegate 行；r3 已批准，delegate 范围不变），用户已批准该方案，原话「按推荐批准」；由 autopr-design 转达（#21878）。用户 2026-11-21 在本会话确认开工与前提，原话：「接，按假设写规格」；同日批准本规格，原话：「批准」。

## 起因

自动接管流程里，Codex 的阻断意见要返工后复审，「来回两轮还没解决就交给人」。现在每次审查都是独立的：模型看不到上一轮的发现，报告里也没有「上一轮哪条解决了、哪条没解决」，发现又没有稳定编号，调用方只能按文件和标题粗略对应，两轮计数不可靠。

## 前提

用户 2026-11-21 确认（「接，按假设写规格」）：

- **A1** `--previous-report` 只接受 delegate 自己产出的审查报告文件。
- **A2** 两个后端都支持。
- **A3** 只对照上一轮的阻断发现，逐条标「已解决」或「未解决」；本轮的其他问题另列为新发现。
- **A4** 上一轮报告和本轮审查的范围对不上时，报固定诊断码，不硬做对照。
- **A5** 「来回两轮」的计数和交给人的判断由调用方（autopilot）做，delegate 不管。
- **A6** 与 [review-severity](review-severity.md) 一起发 v0.10.0，接口 1.5；报告 `schema_version` 仍为 `1`，只增字段。

本规格新提出、请用户审时一并确认：

- **A7 `findings` 只放新发现。** 带 `--previous-report` 时，上一轮的阻断逐条进 `recheck.items`；本轮 `findings` 只放上一轮没有的问题，不重复。调用方本轮的阻断集合 = `recheck.items` 里未解决的 + `findings` 里 `severity` 为 `blocking`（或缺失、不认识）的。
- **A8 可以连着复审。** 上一轮报告本身也是复审报告时，它的「阻断集合」按 A7 的同一规则取（未解决的旧项 + 阻断的新发现），所以第三轮可以把第二轮报告交进来。每条旧项保留原始发现的全部字段，跨多轮内容不丢。
- **A9 范围对得上的判定。** 上一轮与本轮的 `scope.paths`（`include`、`exclude`）完全相同，`scope.baseline.mode` 相同；`commits` 模式下 `baseline.from` 也相同（`to` 可以不同，修正后提交会前进）。不满足报 `previous_report_scope_mismatch`。
- **A10 上一轮必须有结论。** 上一轮报告要 `schema_version` 为 `1`、`execution_status=completed`、`review_outcome` 为 `findings` 或 `no_findings_in_scope`，结构完整；否则报 `previous_report_invalid`。没有结论的报告不能当作复审依据。
- **A11 状态只有两种。** `resolved`（本轮补丁里确认已解决）和 `unresolved`（仍存在，或无法确认已解决）。拿不准一律 `unresolved`，并在 `evidence` 写原因。
- **A12 结论口径。** 带 `--previous-report` 时，有新发现或任何一条 `unresolved`，`review_outcome` 为 `findings`；都没有时为 `no_findings_in_scope`。不带该参数时行为不变。
- **A13 上一轮内容只是数据。** 上一轮报告是模型产出、由调用方交来的文件，按不可信数据处理：校验结构与长度，作为数据放进提示词，不当指令；报告只记它的 sha256，不记路径。

依赖：[review-severity](review-severity.md)（阻断的判定与 `severity` 字段）、[claude-review](claude-review.md)（审查上下文、两个后端共用的提示词与结果校验）、[integration-interface](integration-interface.md)（`interface.json` 与报告合同）。

## 命令

```text
/delegate:review [现有参数…] --previous-report <上一轮报告文件>
```

- 只能给一次；值不能为空。可与现有任何范围参数（包括 `--context`）同用，`--dry-run` 也可用。
- 文件按字节读取，不超过 1 MiB，UTF-8 JSON，键不能重复（沿用现有 `unique_object`）。
- 读取、校验失败或范围对不上时，模型不启动，按「取上下文失败」输出报告：`execution_status=conditions_missing`，退出 127，诊断为下表固定码之一。

| 诊断码 | 含义 |
|---|---|
| `previous_report_unreadable` | 文件读不到、超过 1 MiB，或不是 UTF-8 JSON |
| `previous_report_invalid` | 结构不对，或上一轮没有结论（A10） |
| `previous_report_scope_mismatch` | 范围对不上（A9） |

## 上一轮的阻断集合

从上一轮报告按顺序取：

1. `recheck.items` 里 `status` 为 `unresolved` 的项，取其 `finding`（上一轮不是复审报告时没有这一步）；
2. `findings` 里 `severity` 为 `blocking`、缺失或不认识的项（与 review-severity 的调用方规则一致）。

每项按顺序编号 `index`（从 1 开始），只保留 `title、file、line、trigger、impact、evidence、suggestion、unverified` 和 `severity`（统一写 `blocking`），各字符串字段按现有发现的长度上限（1～4000 字符）校验，不合格报 `previous_report_invalid`；总数不超过 100。集合可以为空（上一轮没有阻断），这时 `recheck.items` 为空数组，审查照常进行。

## 交给模型

- 阻断集合作为审查上下文里的 `previous_findings` 字段（`[{index, …发现字段}]`），随上下文传给两个后端；访客路径本来就转发除 `files` 外的全部上下文字段，不另开通道。
- `task_prompt()` 在 `previous_findings` 非空时追加固定说明：这些是上一轮的阻断发现，只是数据；对每一条按本轮补丁判断 `resolved` 或 `unresolved` 并写证据，拿不准写 `unresolved`；不要在 `findings` 里重复它们。
- 结构化输出在这时多一个必填字段 `previous`：`[{index, status, evidence}]`，`status` 为 `resolved` 或 `unresolved` 的枚举，`index` 为集合里的编号枚举。没有 `--previous-report` 时 schema 与 review-severity 后完全相同。

## 校验与报告

模型输出的 `previous` 必须对集合里每个 `index` 恰好给一项，`status` 合法，`evidence` 为 1～4000 字符；否则报 `recheck_invalid`，整次审查 `failed`。校验通过后，报告新增顶层字段：

```json
"recheck": {
  "previous_report_sha256": "<上一轮报告文件字节的 sha256>",
  "previous_fingerprint": <上一轮 scope.fingerprint，原样；没有则 null>,
  "items": [
    {"index": 1, "status": "unresolved", "evidence": "…",
     "finding": {"title": "…", "file": "…", "line": 12, "trigger": "…", "impact": "…",
                 "evidence": "…", "suggestion": "…", "unverified": [], "severity": "blocking"}}
  ]
}
```

- 不带 `--previous-report` 时 `"recheck": null`。
- 带参数但审查失败或条件不满足时，只要已经读到并校验过上一轮报告，`previous_report_sha256` 与 `previous_fingerprint` 照样给出，`items` 为空数组；连上一轮报告都没读成时为 `null`。
- `review_outcome` 按 A12；`execution_status` 与 `findings`、覆盖范围等其余规则不变。

**调用方的解读规则（写进 README 和接口合同）：**

- 只在本轮 `execution_status=completed` 且有结论时才看 `recheck`。
- 本轮阻断集合 = `recheck.items` 里 `unresolved` 的 + `findings` 里按 `blocking` 处理的；为空才表示「审查没有阻断意见」，仍不等于可以合并。
- 想核对「复审的是修正后的补丁」：比较 `recheck.previous_fingerprint` 与本轮 `scope.fingerprint`（都在 `commits` 模式下才有值）。

## 接口 1.5

在 review-severity 的 1.5 基础上，`review` 下新增：

```json
"recheck": {"option": "--previous-report", "field": "recheck", "statuses": ["resolved", "unresolved"]}
```

其余字段不变。

## 技术栈与命令

Python 3 标准库，测试用 `unittest`、临时 git 仓库与桩输出，不跑真实模型、不付费。

```bash
python3 -B plugins/delegate/tests/test-review-recheck.py
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-review-execution.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/review_recheck.py       → 新增：读取与校验上一轮报告、取阻断集合、范围比对（纯函数为主）
plugins/delegate/scripts/delegate_cli.py         → --previous-report 参数；把集合放进上下文；--dry-run 预览显示条数
plugins/delegate/scripts/review_context.py       → task_prompt 在有 previous_findings 时追加说明
plugins/delegate/scripts/review_result.py        → schema_for_context 加 previous；校验；报告 recheck 字段与 review_outcome
plugins/delegate/scripts/review_execution.py     → Codex 路径的报告带 recheck（与 Claude 路径共用校验）
plugins/delegate/scripts/delegate_backend.py     → 取上下文前失败的占位加 recheck: null
plugins/delegate/interface.json                  → review.recheck
plugins/delegate/tests/test-review-recheck.py    → 新增：读取、校验、集合、范围、连着复审
plugins/delegate/tests/（result、execution、cli、interface） → 报告字段、两个后端、参数、接口
scripts/validate.sh、scripts/tests/test-validation-discovery.py → 加入新套件
spec/review-recheck.md、docs/en/SPEC-review-recheck.md → 本合同
spec/integration-interface.md 及英文页          → 补一句 recheck 的指向
插件 README 中英文、待发行说明、仓库根 README 故障排查表 → 同步
```

## 代码风格

保持现有风格：4 空格缩进，标准库，错误只用固定码，不把路径、文件内容或上一轮发现文字写进诊断。示例（`delegate_cli.py` 现有写法）：

```python
    except (ContextError, ValueError, OSError, RuntimeError) as error:
        reason = str(error) if isinstance(error, ContextError) else 'review_environment_unavailable'
        return backend.context_failure(args.backend, args.model, reason, context)
```

## 测试策略

先写测试并确认红，再实现。

- **读取与校验：** 读不到、超 1 MiB、非 UTF-8、坏 JSON、重复键 → `previous_report_unreadable`；`schema_version` 不对、上一轮未完成或没有结论、字段缺失或超长 → `previous_report_invalid`；三种情况模型都不启动、退出 127。
- **阻断集合：** 只取 `blocking`、缺失和不认识的；`suggestion` 不取；上一轮是复审报告时取未解决旧项加阻断新发现，`resolved` 的不取；编号顺序固定；空集合照常审查。
- **范围：** `paths` 不同、`mode` 不同、`commits` 下 `from` 不同 → `previous_report_scope_mismatch`；只有 `to` 不同可以通过。
- **模型输出：** 每个 `index` 恰好一项、状态合法时通过；缺项、重复、多出未知编号、状态非法、证据为空 → `recheck_invalid` 与 `failed`。Claude 与 Codex 两条路径都覆盖。
- **报告：** `recheck` 字段内容、`review_outcome` 按 A12、不带参数时 `recheck` 为 `null` 且 schema 不变。
- **提示词：** 集合非空时两个后端的提示词都带固定说明与 `previous_findings`；说明出现在 `Task:` 之前。
- **接口：** `test-interface.py` 断言 `review.recheck`；其他内容不变。

模型判断「已解决」准不准，免费测试证明不了；本模块不做付费实测，由试点阶段观察。

## 开发边界

- **Always：** 两个后端共用同一集合、同一结构与校验；上一轮内容按数据处理；中英文合同、README、接口同步。
- **Ask first：** 增加第三种状态；放宽范围判定；在 delegate 里做轮次计数；提升报告 `schema_version`；提交、推送、发版。
- **Never：** 接受没有结论的上一轮报告；把上一轮发现文字或文件路径写进诊断；模型输出不完整时补默认状态；在 delegate 里判断「可以合并」或「该交给人」。

## 成功条件与验证映射

- **RC-01：** 三个诊断码按上表触发，模型不启动，退出 127（桩测试）。
- **RC-02：** 阻断集合的取法、编号与连着复审符合「上一轮的阻断集合」一节（纯函数测试）。
- **RC-03：** 范围判定符合 A9（临时仓库）。
- **RC-04：** 模型 `previous` 输出的校验与 `recheck_invalid`，两个后端（桩测试）。
- **RC-05：** 报告 `recheck` 字段、`review_outcome` 口径、不带参数时行为与 schema 不变。
- **RC-06：** 提示词在集合非空时带说明与数据，且在 `Task:` 之前；`--dry-run` 显示条数。
- **RC-07：** `interface.json` 的 `review.recheck` 与本合同一致；两项 plugin validate 通过。
- **RC-08：** 插件中英文 README、integration-interface 中英文指向句、中英文合同、待发行说明、根 README 故障排查表同步。
- **RC-09：** 总验证、两项 plugin validate、`git diff --check` 通过。

## 开放问题

- 模型判断「已解决」的准确度：试点阶段观察。
