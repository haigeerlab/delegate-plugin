# 规格：integration-interface（对外接口说明与审查报告合同）

<!-- spec-guard: review approved 21ceaa25742a -->

简体中文 | [English](../docs/en/SPEC-integration-interface.md)

2026-10-17 起草，同日经用户批准。起因是生态接缝建议（spec-guard 在检查点提示可用 `/delegate:review` 做只读复核，decision-inbox 引用审查结论）。本模块只让 delegate 把已有能力和已有报告格式写成别的插件可以按版本依赖的说明，不新增审查行为。

## 前提（已于 2026-10-17 经用户确认 A1–A5）

- **A1** 只做两件事：发布 `interface.json`；把现有审查报告 `schema_version: 1` 写成对外合同。审查结果经邮箱回传不做：结果本来就回到发起审查的会话，跨会话转发归 agent-relay。
- **A2** `interface.json` 是静态声明，只写“支持什么”和接口版本，不声称后端此刻可用；可用性仍由 `/delegate:doctor` 现场检查。
- **A3** 本次不加“严重程度”字段，不改报告生成逻辑；只承诺 v1 现有字段。
- **A4** 不新增运行依赖；其他插件装没装，delegate 行为都不变。delegate 不探测、不调用其他插件。
- **A5** 按模块流程推进：本规格评审通过后再写 Plan 与代码。

## 技术栈与命令

静态 JSON 文件、Python 3 标准库 `unittest`；不新增脚本入口或 hook。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-interface.py
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/interface.json            → 新增：对外能力与接口版本（随插件分发）
plugins/delegate/tests/test-interface.py   → 新增：接口说明与源码事实一致性断言
plugins/delegate/README.md / README.en.md  → 新增“对外接口”一节：读取方式、版本规则、报告字段
plugins/delegate/scripts/delegate_capabilities.py → 只读引用：后端能力事实来源，不改
plugins/delegate/scripts/review_result.py  → 只读引用：报告字段事实来源，不改
spec/integration-interface.md              → 本合同
docs/en/SPEC-integration-interface.md      → 英文合同
docs/releases/unreleased.md                → 记一条待发行说明
```

## 接口说明 `interface.json`

放在插件根目录，与 agent-relay 的做法一致：使用方从宿主插件记录找到已启用的 delegate 安装路径，读这个文件，按 `interface` 版本范围判断，不读 delegate 内部文件。首版内容：

```json
{
  "interface": "1.0",
  "review": {
    "command": "/delegate:review",
    "backends": ["codex", "claude-code"],
    "readOnly": true,
    "report": {"schemaVersion": 1}
  },
  "run": {"command": "/delegate:run", "backends": ["codex"], "write": "explicit"},
  "doctor": {"command": "/delegate:doctor"}
}
```

- `backends` 表示该版本**支持**的后端，不表示本机已安装、已认证或有额度。使用方要提示“可以用 delegate 复核”时，不得据此断言能跑通。
- 版本规则：只增加可选字段为次版本（`1.x`）；删除、改名或改变字段含义为主版本（`2.0`）。使用方按主版本范围检查，如 `>=1.0,<2.0`。
- 文件读不到或解析失败，使用方应报“未知”，不当作没装；这是使用方的探测规则，delegate 只保证文件存在且有效。

## 审查报告合同（`schemaVersion: 1`）

**取得方式：** `/delegate:review` 的标准输出就是一份 JSON 报告（干跑 `--dry-run` 输出的是 `kind=review_preview` 预览，不是报告）。标准错误里 `delegate: artifacts=<路径>` 指向私有副本，路径和保留数量（最近 50 份）不属于合同。

**v1 稳定字段：**

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定 `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`、`scope.baseline`、`scope.diff_sha256`、`scope.files` | 审查对象与指纹：范围、基准、diff 摘要、每个文件的 sha256 |
| `reviewed` | 实际审完的文件 |
| `unreviewed[]` | `{path, reason}`，未审文件及原因 |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified}`，`line` 可为 `null` |
| `limitations` | 限制说明文本 |

其他字段（如 `host`、`diagnostics`、`observed_models`、`cleanup`、`usage`）照常输出，但属于诊断信息，可能随版本变化，使用方不应依赖。

**解读规则（使用方必须遵守）：**

- 只有 `execution_status=completed` 且 `review_outcome` 为 `findings` 或 `no_findings_in_scope` 时才算一次有结论的审查；其余一律按“未得出结论”处理。
- `no_findings_in_scope` 只表示该范围内没报出问题，不表示没有缺陷。
- 报告是第三方参考意见，不是用户批准，不授权修改、合并或交付。引用时注明来源 delegate、后端和指纹。

## 代码风格

保持已有风格。测试用标准库 `unittest`、4 空格缩进，事实从源码模块导入比较，不在测试里复制一份清单。现有事实来源示例（`plugins/delegate/scripts/delegate_capabilities.py`）：

```python
BACKENDS = {
    'codex': {'review': True, 'run': True, 'write': True,
              'options': ('--model', '--effort')},
    'claude-code': {'review': True, 'run': False, 'write': False,
                    'options': ('--model', '--max-turns', '--max-budget-usd')},
}
```

## 测试策略

`test-interface.py` 做免费的一致性断言，防止说明和代码漂移：

- `interface.json` 是合法 JSON，`interface` 形如 `主.次`；
- `review.backends` 等于 `BACKENDS` 中 `review` 为真的后端，`run.backends` 等于 `run` 为真的后端；
- `review.report.schemaVersion` 等于 `base_report()` 产出的 `schema_version`；
- 合同列出的稳定字段都出现在 `base_report()` 产出中，`findings` 条目字段集合等于 `FINDING_FIELDS`；
- `execution_status`、`review_outcome` 的合同取值与源码可产出的取值一致。

先让测试在没有 `interface.json` 时失败，再补文件转绿。不跑真实模型，不需要付费验证。

## 开发边界

- **Always：** 改报告字段或后端能力时同步 `interface.json`、README 与本合同，并让一致性测试守住；中英文合同同步。
- **Ask first：** 增加严重程度等新字段、提升 `schema_version` 或 `interface` 主版本、增加 `status` 之类可执行入口。
- **Never：** 在 delegate 里探测或调用其他插件；主动对外发送审查结果；把 `backends` 写成可用性保证；修改报告生成逻辑来迁就文档。

## 成功条件与验证映射

- **IF-01：** 插件根目录存在合法 `interface.json`，内容符合上文首版；`claude plugin validate ./plugins/delegate` 通过。
- **IF-02：** 一致性测试先红后绿，覆盖测试策略列出的五项断言。
- **IF-03：** 插件中英文 README 有“对外接口”一节，写明读取方式、版本规则、v1 稳定字段与解读规则。
- **IF-04：** 总验证脚本、两项 plugin validate、`git diff --check` 全部通过；现有测试不改断言。

## 开放问题

- spec-guard 的探测脚本和 decision-inbox 的引用写法由各自负责人实现；本模块合入后把接口说明通知它们，对接中发现的格式问题按次版本补充。
- 严重程度字段等使用方真正需要按级别展示时，另提变更。
