# 规格：design-review-criteria（技术方案审查判据）

<!-- spec-guard: review approved 3cb2df80f0a2 -->

简体中文 | [English](../docs/en/SPEC-design-review-criteria.md)

2026-11-24 起草。来源：生态总账 S110「开发流程改版」第五节、第七节 delegate 行（plugin-ecosystem 仓 `research/2026-11-24-开发流程改版/需求.md`），由 ecosystem-lead #22330 分派；spec-guard 接口草案 v1（sg-coord #22364）。用户 2026-11-24 在本会话确认需求与 Q1～Q7，原话「说完了，按推荐定」；确认插入能力图，原话「确认写入」；批准用法草案 [s110-design-review](usage/s110-design-review.md)，原话「批准」。按 S110 的过渡安排，本仓库仍按现有 Spec/Plan 流程：本规格兼作技术方案与回归测试文档，档位为重要，由用户批；用户 2026-11-24 批准本规格，原话「批准」。

## 起因

S110 把开发流程改为「需求 → 技术方案 → 回归 → 拆任务 → 实现 → 按回归验收」，技术方案由第二审查者对照代码审一轮、修一轮。现有 `/delegate:review` 的判据 `severity-v1` 是给代码补丁用的：它把「做不到任务要求」「缺测试」等判为阻断，套到技术方案上，正是 S101 推广后看到的「只挑写得不够全、两轮都过不去」。S110 要求技术方案的阻断必须拿代码证明，第二轮只核对上一轮。

## 前提

用户 2026-11-24 确认（「说完了，按推荐定」）：

- **P1 入口。** `/delegate:review` 加 `--profile design`，判据名 `design-v1`；不带或 `--profile default` 时判据仍是 `severity-v1`，行为与 0.11.0 相同（需求 Q1）。
- **P2 机械校验代码证据。** 阻断必须指向一个**参考文件**里存在的行；不满足就由 delegate 改记为建议，在该条上标 `downgraded: "no_code_evidence"`，原文不改（需求 Q2）。
- **P3 老代码由调用方带进来。** 调用方用 `--spec`／`--plan` 把技术方案影响面列的已有文件作为参考文件传入；delegate 不自己找文件（需求 Q3）。
- **P4 第二轮只核对。** 带 `--previous-report` 时，本轮新发现一律记为建议，标 `downgraded: "second_round"`（需求 R3）。

本规格新提出、请用户审时一并确认：

- **D1 什么算参考文件。** 在本次快照里、且不在审查范围（`scope.include`／`exclude` 选中的文件）里的文件，也就是只经 `--spec`／`--plan`（或 `--context` 的 `context_files`）带进来的文件。需求文档本身也是参考文件：方案和需求文档某一行矛盾，同样可以作为阻断的证据。被审的技术方案本身永远不算证据。
- **D2 位置核不上的发现在 design 档不让整轮失败。** 现在任何发现的行号核不上，整次审查判 `failed`（`review_incomplete`）。design 档里这类发现按 P2 改记为建议（`downgraded: "no_code_evidence"`），行号置空并照旧在 `unverified` 里写明，不影响整轮结论。默认档不变。
- **D3 两种降级同时成立时记 `second_round`。** 第二轮的发现不论有没有证据都只是建议，标第二轮的原因更准确。
- **D4 复审要求判据一致。** 上一轮报告的 `criteria` 必须与本轮相同（老报告没有这个字段，按 `severity-v1`）；不同报 `previous_report_scope_mismatch`。避免拿代码审查的报告去复审技术方案。
- **D5 报告新增 `criteria`。** 顶层 `criteria` 为 `severity-v1` 或 `design-v1`；findings 里被降级的条目多一个 `downgraded` 字段，其余条目不变。报告 `schema_version` 仍为 `1`。

依赖：[review-snapshot-recheck](review-snapshot-recheck.md)（快照复审）、[review-recheck](review-recheck.md)（`--previous-report` 与 `recheck`）、[review-severity](review-severity.md)（`severity` 字段与调用方规则）、[claude-review](claude-review.md)（两个后端共用的提示词与结果校验）。接口版本与 [reviewer-selection](reviewer-selection.md) 一起升 1.7。

## 现状调研

查过的：
- `review_context.py`：`SEVERITY_CRITERIA` 常量（B1～B8 判阻断、S1～S3 判建议）在 `task_prompt()` 里无条件写入；两个后端与访客路径都经 `task_prompt()`。
- `review_result.py`：`content_result()` 逐条校验发现，`file` 必须在快照里、`line` 在范围内，否则 `location_verified=false` 且整轮 `verified=False`，`conclude()` 判 `failed`／`review_incomplete`。`schema_for_context()` 把 `file` 限为快照里的路径。
- `delegate_cli.py`：`review_arguments()` 解析参数；`--spec`／`--plan` 进 `context_files`；`--previous-report` 在取完上下文后读入。
- `review_recheck.py`：`check_scope()` 比 `paths`、`mode` 与基准。
- `interface.json`：1.6，`review.report.severity.criteria` 为 `severity-v1`。

没查的：真实模型按新判据标注的准确度（免费测试证明不了）。

## 影响面与实现方案

1. **参数。** `delegate_cli.py` 新增 `--profile default|design`（只能给一次）；`context['profile']` 记下，访客路径随上下文转发。`--dry-run` 预览显示 `profile` 与 `criteria`。
2. **判据与提示词。** `review_context.py` 新增常量 `DESIGN_CRITERIA`（全文见下节），`task_prompt()` 在 `profile == 'design'` 时用它替换 `SEVERITY_CRITERIA`，并在 `Task:` 之前加一句固定说明「被审的是技术方案；阻断必须引用参考文件里的行」。默认档提示词与 0.11.0 逐字相同。
3. **校验与降级。** `review_result.content_result()` 在 design 档：对每条发现，若本轮是第二轮 → `severity` 改为 `suggestion`、`downgraded: "second_round"`；否则若 `severity == "blocking"` 且（位置核不上，或 `file` 不是参考文件）→ 改为 `suggestion`、`downgraded: "no_code_evidence"`；位置核不上的发现在 design 档不再把 `verified` 置为假（D2）。默认档逻辑不变。
4. **报告。** `base_report()` 加顶层 `criteria`；取上下文前失败的占位也带（无 profile 时为 `severity-v1`）。
5. **复审。** `review_recheck.check_scope()` 加 D4 的判据比对。
6. **接口。** `interface.json` 的 `review` 下加 `profiles: {"default": {"criteria": "severity-v1"}, "design": {"option": "--profile design", "criteria": "design-v1", "downgraded": ["no_code_evidence", "second_round"]}}`，`report` 稳定字段加 `criteria`。接口号在 reviewer-selection 一起升 1.7；本模块单独完成时先不改 `interface` 号（避免中间状态发版）。

## design-v1 判据全文

```text
You are reviewing a technical design, not code. Reference files (context_files that are not under review) contain the existing code, the requirement and contracts the design must fit.
Mark a finding "blocking" only when you can cite a specific line in a reference file that shows the design will go wrong, and one of these holds:
D1. Following the design breaks behavior that exists today: a caller, contract, data format or test shown in the cited line would stop working.
D2. The design relies on something the code does not have or that works differently from what the design assumes (a function, field, option, file or behavior), as the cited line shows.
D3. The design contradicts the requirement or an interface contract at the cited line.
D4. The design would let untrusted input reach a shell, eval, a secret or a permission check shown at the cited line.
D5. The design leaves out an existing caller or file that must change for it to work, as the cited line shows.
Set "file" and "line" of a blocking finding to that reference line. Everything else is a "suggestion": missing detail, wording, structure, alternatives, risks you cannot tie to a reference line, and anything about the design text itself.
```

## 技术栈与命令

Python 3 标准库，测试用 `unittest`、临时 git 仓库与桩后端，不跑真实模型、不付费。

```bash
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-review-execution.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-review-recheck.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 代码风格

保持现有风格：4 空格缩进，标准库，诊断只用固定码；模型原文不改，只改 `severity` 并加标记。示例（`review_result.py` 现有写法）：

```python
        location = data is not None and type(line) is int and 1 <= line <= len(data.splitlines())
        value = dict(item, location_verified=location)
```

## 回归测试

| 编号 | 用例 | 执行方式 | 证据 |
|---|---|---|---|
| DR-01 | `--profile design` 时两个后端与访客路径的提示词带 `DESIGN_CRITERIA` 与固定说明、不带 `SEVERITY_CRITERIA`；默认档提示词与 0.11.0 逐字相同 | 命令 | `test-review-context.py`、`test-review-execution.py`、`test-claude-review.py`、`test-review-guest.py` |
| DR-02 | design 档：阻断指向参考文件真实行 → 保持 `blocking`；指向被审方案、指向不存在的行、`line` 为空 → `suggestion` + `no_code_evidence`，原文不变 | 命令 | `test-review-result.py` |
| DR-03 | design 档：位置核不上的发现不让整轮失败；默认档同样输入仍 `failed`／`review_incomplete` | 命令 | `test-review-result.py` |
| DR-04 | design 档第二轮：新发现全部 `suggestion` + `second_round`；`recheck.items` 照旧 | 命令 | `test-review-result.py`、`test-review-execution.py` |
| DR-05 | 报告顶层 `criteria`：默认 `severity-v1`、design `design-v1`；取上下文前失败的占位也有 | 命令 | `test-review-result.py`、`test-review-cli.py` |
| DR-06 | 上一轮 `criteria` 不同（含老报告缺字段按 `severity-v1`）→ `previous_report_scope_mismatch`、退出 127、不启动模型 | 命令 | `test-review-recheck.py`、`test-review-cli.py` |
| DR-07 | `--profile` 重复、取值非法 → 参数错误退出 64；`--dry-run` 显示 `profile`、`criteria` | 命令 | `test-review-cli.py` |
| DR-08 | `interface.json` 的 `review.profiles` 与本规格一致；两项 plugin validate 通过 | 命令 | `test-interface.py` |
| DR-09 | 端到端：临时仓库里 `--profile design --paths design.md --spec code.py` 跑桩后端，第一轮一条有证据的阻断、一条无证据的阻断，报告各为 `blocking` 与降级的 `suggestion` | 命令 | `test-review-cli.py` |
| DR-10 | 回归老功能：现有全部套件不改断言通过（默认档行为、快照复审、severity 校验） | 命令 | `scripts/validate.sh` |

成功条件与上表一一对应：DR-01～DR-10 全部通过，加上中英文合同、用法草案、插件 README、integration-interface 指向句、待发行说明同步（DR-11，人工核对，执行方式：人工）。

## 风险与回滚

| 风险 | 影响 | 缓解 |
|---|---|---|
| 模型把技术方案自己的行当证据 | 中 | 机械校验：被审范围内的文件永远不算证据 |
| 降级掩盖了真问题 | 中 | 只改 `severity`，原文、位置、`downgraded` 原因都保留，调用方和用户都看得到 |
| 默认档被波及 | 高 | 默认档提示词逐字比对、现有套件不改断言 |
| 调用方没带参考文件 | 中 | 所有阻断都会降级，审查等于只有建议；在 README 与对 spec-guard 的约定（#22369）里写明必须带 |

回滚：本模块只增参数与字段，不带 `--profile design` 的调用不受影响；出问题时调用方不传该参数即可退回原行为。

## 方案取舍

- 降级而不判失败：整轮失败会让技术方案审查经常作废，而 S110 要的是「只拦能证明的问题」。
- 机械校验而不只靠提示词：模型常把「方案没写 X」当阻断，提示词挡不住。
- 不按扩展名区分「代码」：需求文档、接口合同里的行同样能证明方案出错，按「是不是参考文件」区分更稳。

## 并行边界

- 独占：`plugins/delegate/scripts/review_context.py`、`plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/review_recheck.py`、`plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/interface.json`、`plugins/delegate/commands/review.md`、`plugins/delegate/tests/test-review-context.py`、`plugins/delegate/tests/test-review-result.py`、`plugins/delegate/tests/test-review-execution.py`、`plugins/delegate/tests/test-review-cli.py`、`plugins/delegate/tests/test-review-recheck.py`、`plugins/delegate/tests/test-claude-review.py`、`plugins/delegate/tests/test-review-guest.py`、`plugins/delegate/tests/test-interface.py`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/en/SPEC-design-review-criteria.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`

## 开发边界

- **Always：** 默认档逐字不变；两个后端与访客路径共用同一判据与校验；只改 `severity`、不改模型原文；中英文同步。
- **Ask first：** 改 `severity-v1`；让 design 档整轮失败；在 delegate 里决定审不审或能否放行；提交、推送、发版。
- **Never：** 把被审方案本身当证据；悄悄删掉降级的发现；在诊断里写路径或模型原文。

## 开放问题

- 模型按 `design-v1` 标注的准确度：发版后按用法草案 M1 实跑观察。
