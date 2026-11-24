# 规格：reviewer-selection（第二审查者的检测与选择）

<!-- spec-guard: review approved ee564b3bc2d5 -->

简体中文 | [English](../docs/en/SPEC-reviewer-selection.md)

2026-11-24 起草。来源与批准同 [design-review-criteria](design-review-criteria.md)：生态总账 S110 第五节（第二审查者）、第七节 delegate 行；用户 2026-11-24 确认需求与 Q1～Q7（「说完了，按推荐定」）、插入能力图（「确认写入」）、用法草案（「批准」）。本规格兼作技术方案与回归测试文档，档位为重要，由用户批；用户 2026-11-24 批准本规格，原话「批准」。

## 起因

S110 要求技术方案由第二审查者审：优先选与主开发不同厂商的 AI；只开通一家时用同厂商的独立会话并在报告里注明；都不可用时写明「未审」；写代码的会话绝不审自己的东西；开工前检测本机可用的 AI 并提示用户。现在 `/delegate:review` 只能由调用方显式给 `--backend`（默认 `codex`），报告里没有「审查者是哪家、是否同厂商、怎么选的」，也没有「未审」这种结局；README 还写着「Codex 不可用就停下、不改用 Claude 自审」，与 S110 第五节第 4 条冲突。

## 前提

用户 2026-11-24 确认（「说完了，按推荐定」）：

- **P1 声明主开发。** `--backend auto` 必须配 `--author-host claude-code|codex`；只给 `auto` 不给主开发 → 参数错误（需求 Q4）。
- **P2 可用性只做无模型检查。** 沿用两个后端现有的启动前检查（CLI 在、版本够、已登录；Claude 路径还有本机边界预检），不发模型请求。检查通过但真跑失败，按失败报告，不换另一家重试（需求 Q5）。
- **P3 报告字段。** 顶层 `reviewer: {vendor, backend, same_vendor, selection}`；「未审」为 `execution_status=conditions_missing`、`review_outcome=inconclusive`、诊断 `no_reviewer_available`、`selection="none"`、退出 127（需求 Q6）。
- **P4 绝不自审。** 两个后端都是新起的进程会话，不继承调用方上下文；这一点本来就成立，本模块把它写进文档，并替换 README 里「不改用 Claude 自审」的说法（需求 AC8）。

本规格新提出、请用户审时一并确认：

- **E1 厂商名。** `codex` → `openai`，`claude-code` → `anthropic`；`--author-host` 取值同后端名，按同一表换算厂商。
- **E2 选择顺序。** 主开发 `claude-code`：先查 Codex，可用选它（`cross_vendor`）；否则查 Claude Code，可用选它（`same_vendor_fallback`）；都不可用 → 未审。主开发 `codex` 对称：先 Claude Code，再 Codex。
- **E3 显式后端也标注。** 给了 `--backend codex|claude-code` 时 `selection="explicit"`；同时给了 `--author-host` 就算出 `same_vendor`，没给则 `same_vendor` 为 `null`（不知道主开发是谁）。不带 `auto` 时其余行为与 0.11.0 相同。
- **E7「未审」报告的 `backend` 为 `null`。** 没有任何后端启动时，报告顶层 `backend` 为 `null`（`reviewer` 的 `vendor`、`backend`、`same_vendor` 同为 `null`、`selection` 为 `none`）。合同：只有 `reviewer.selection == "none"` 时 `backend` 才可能为 `null`，其余情况仍只取 `codex`／`claude-code`。实现中发现、规格原未覆盖，用户 2026-11-24 选定，原话「A：null」。
- **E4 auto 时不接受只属于某一家的参数。** `--backend auto` 与 `--model`、`--effort`、`--max-turns`、`--max-budget-usd` 同时给 → 参数错误（事先不知道会选到哪家，这些参数没有确定含义）。
- **E5 体检。** `/delegate:doctor --reviewers` 依次对两家做 P2 的无模型检查，逐家给出可用或不可用（附固定诊断码），只有一家可用时提示「建议再开通一家，以便异厂商审查」，两家都不可用时说明审查会记为「未审」；加 `--json` 输出 `{"schema": "delegate.reviewers/v1", "reviewers": [{"backend", "vendor", "available", "diagnostic"}], "hint"}` 供 spec-guard 读。都不阻止任何操作，退出 0。
- **E6 接口 1.7。** 与 [design-review-criteria](design-review-criteria.md) 一起升 1.7，只增字段（见下节）。

依赖：[design-review-criteria](design-review-criteria.md)（同版发布、共用接口号）、[detection](detection.md)（Codex 基础检查 `backend.check_detailed()`）、[claude-review](claude-review.md)（Claude 本机边界预检与执行）。

## 现状调研

查过的：
- `delegate_backend.py`：`--backend` 取值 `codex|claude-code`，默认 `codex`；审查路由按 `args.backend` 分到 `codex_review` 或 `native_review`；取上下文失败走 `context_failure()`。
- `review_execution.codex_review()`：先 `backend.check_detailed()`，失败给 `codex_preflight_failed` 加原因、退出 127 或 1。
- `review_native` 与 `claude_review.preflight()`：本机 srt/Node 检查、CLI 版本与参数、原有认证；`review_doctor.py --backend claude-code` 已能单独跑这套检查。
- `review_doctor.py`：无参数或 `--backend codex` 时 `exec` 老的 `hooks/doctor.sh`；`--backend claude-code` 跑 Claude 预检。
- `review_result.base_report()`：报告顶层有 `backend`、`observed_models`，没有审查者选择信息。
- 根 README 第 228 行：「否则停下等人，不改用 Claude 自审」。

没查的：Claude Code 在没有 srt 的机器上能否作为审查者（现有预检会判不可用，按 P2 照实报告）。

## 影响面与实现方案

1. **参数。** `delegate_backend.py`／`delegate_cli.py`：`--backend` 增加 `auto`；新增 `--author-host codex|claude-code`（只能一次）；按 P1、E4 校验，不合格退出 64。
2. **选择。** 新文件 `reviewer_select.py`：纯函数 `order(author)` 给出候选顺序；`choose(author, checks)` 按 E2 逐家调用传入的检查函数，返回 `(backend 或 None, selection, 各家诊断)`。真实检查函数包两家现有预检（Codex：`backend.check_detailed()`；Claude：`NativeRunner.runtime_preflight()` + `claude_review.preflight()`，与 doctor 同一套），测试注入假检查。
3. **路由。** 取完上下文后，`auto` 先选再走原路由；选中后 `args.backend` 定为选中的后端，后续与显式指定完全相同（同一后端的预检会在执行时照旧再做一次）。没有可用的 → 生成「未审」报告（`base_report` + `no_reviewer_available` 与各家固定诊断码，`backend_started=false`），退出 127。
4. **报告。** `base_report()` 加顶层 `reviewer`；`context_failure()` 的占位也带（选择未发生时 `selection` 按参数取 `explicit` 或 `none`，厂商可推断时照填）。
5. **体检。** `review_doctor.py` 加 `--reviewers [--json]`，按 E5 输出；原有用法不变。
6. **接口。** `interface.json`：`interface` 升 `1.7`；`review.backends` 不变（仍为两家），`review` 下加 `reviewer: {"option": "--backend auto", "authorOption": "--author-host", "field": "reviewer", "vendors": {"codex": "openai", "claude-code": "anthropic"}, "selections": ["cross_vendor", "same_vendor_fallback", "explicit", "none"], "unreviewed": "no_reviewer_available"}`；`doctor` 下加 `reviewers: {"option": "--reviewers", "json": "delegate.reviewers/v1"}`。
7. **文档。** README 与命令说明加 `auto`、`--author-host`、`reviewer` 字段与「未审」读法；根 README 第 228 行改为「写代码的会话绝不审自己的东西：delegate 的审查总是新起会话；Codex 不可用时按 `--backend auto` 回退同厂商独立会话，或由调用方记为未审」。

## 技术栈与命令

Python 3 标准库，测试用 `unittest`、桩后端与注入的假检查，不跑真实模型、不付费。

```bash
python3 -B plugins/delegate/tests/test-reviewer-select.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-review-backends.py
python3 -B plugins/delegate/tests/test-review-result.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 代码风格

保持现有风格：4 空格缩进，标准库，诊断只用固定码；选择逻辑是不碰外部的纯函数，真实检查从外面传入。示例（`review_execution.codex_review()` 现有写法）：

```python
    status, _, diagnostic = backend.check_detailed()
    if status:
        execution['diagnostics'] = ['codex_preflight_failed', diagnostic]
```

## 回归测试

| 编号 | 用例 | 执行方式 | 证据 |
|---|---|---|---|
| RS-01 | 主开发 claude-code：Codex 可用 → codex／`cross_vendor`／`same_vendor=false`；Codex 不可用、Claude 可用 → claude-code／`same_vendor_fallback`／`true`；都不可用 → `none` | 命令 | `test-reviewer-select.py` |
| RS-02 | 主开发 codex：上述三种对称 | 命令 | `test-reviewer-select.py` |
| RS-03 | 「未审」端到端：两家检查都失败（桩）→ 退出 127、`conditions_missing`、`inconclusive`、诊断含 `no_reviewer_available`、`backend_started=false`、模型未启动 | 命令 | `test-review-cli.py` |
| RS-04 | `auto` 选中 Codex 后端到端跑桩：报告 `reviewer` 与 `backend` 一致，其余字段与显式 `--backend codex` 相同 | 命令 | `test-review-cli.py` |
| RS-05 | 显式后端：`selection=explicit`；带 `--author-host` 时算出 `same_vendor`，不带为 `null` | 命令 | `test-review-cli.py`、`test-review-result.py` |
| RS-06 | 参数错误（退出 64）：`auto` 不带 `--author-host`；`auto` 带 `--model`／`--effort`／`--max-turns`／`--max-budget-usd`；`--author-host` 非法或重复 | 命令 | `test-review-cli.py` |
| RS-07 | 取上下文前失败的占位报告也带 `reviewer` | 命令 | `test-review-cli.py` |
| RS-08 | `/delegate:doctor --reviewers`：两家可用、只一家可用（有提示）、都不可用（说明记为未审）三种文本；`--json` 结构与 `delegate.reviewers/v1` 一致；不带新参数时原有输出不变 | 命令 | `test-review-backends.py` 或新增套件 |
| RS-09 | `interface.json` 为 1.7，`review.reviewer`、`doctor.reviewers` 与本规格一致；两项 plugin validate 通过 | 命令 | `test-interface.py` |
| RS-10 | 回归老功能：不带 `auto`、`--author-host` 时现有全部套件不改断言通过 | 命令 | `scripts/validate.sh` |
| RS-11 | 文档：中英文合同、插件 README、命令说明、根 README 第 228 行、integration-interface 指向句、待发行说明同步 | 人工 | 逐项核对记入 todo |

## 风险与回滚

| 风险 | 影响 | 缓解 |
|---|---|---|
| 检查通过、真跑失败 | 中 | 按失败报告、不自动换家（P2）；调用方看到的是真实失败而不是「未审」 |
| Claude 预检较慢（本机边界） | 低 | 只在需要时查：Codex 先可用就不查 Claude（主开发为 claude-code 时） |
| 调用方忘了带 `--author-host` | 中 | `auto` 时强制要求，参数错误退出 64 |
| 「未审」被当成失败重试 | 中 | 固定诊断码 `no_reviewer_available`、`selection=none`；已在 #22369 告知 spec-guard |

回滚：不带 `auto`／`--author-host` 的调用与 0.11.0 相同；出问题时调用方改回显式后端即可。

## 方案取舍

- 不按环境变量猜主开发：Claude Code 与 Codex 的环境变量不稳定，猜错会造成自审；显式声明可验证。
- 检查通过后不在执行失败时自动换另一家：换家会把一次真实失败藏成成功，也可能把异厂商审查悄悄变成同厂商。
- 选择逻辑放在纯函数里：三种可用组合 × 两个方向都能用免费测试穷举。

## 并行边界

- 独占：`plugins/delegate/scripts/reviewer_select.py`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/review_doctor.py`、`plugins/delegate/interface.json`、`plugins/delegate/commands/review.md`、`plugins/delegate/commands/doctor.md`、`plugins/delegate/tests/test-reviewer-select.py`、`plugins/delegate/tests/test-review-cli.py`、`plugins/delegate/tests/test-review-backends.py`、`plugins/delegate/tests/test-review-result.py`、`plugins/delegate/tests/test-interface.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`README.md`、`README.en.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`docs/en/SPEC-reviewer-selection.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`

## 开发边界

- **Always：** 不带新参数时行为不变；选择只用无模型检查；诊断只用固定码；中英文同步。
- **Ask first：** 接入第三家；执行失败后自动换家；按环境变量猜主开发；提交、推送、发版。
- **Never：** 在调用方会话里审查；把「未审」报成通过或失败；在报告或诊断里写认证信息、路径或原始错误。

## 开放问题

- 无。
