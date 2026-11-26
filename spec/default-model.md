# 规格：default-model（按后端配置默认模型）

<!-- spec-guard: review approved 11a84aa88f70 -->

简体中文 | [English](../docs/en/SPEC-default-model.md)

2026-11-26 起草。来源：ecosystem-lead #23280 转用户需求（用户原话「两步都做」：第 1 步改 Codex 全局配置已由 ecosystem-lead 做完，本模块是第 2 步）。用户 2026-11-26 确认需求复述与前提 P1～P6（「按建议确认」）、插入能力图（「确认插入」）。本规格兼作技术方案与回归测试文档，接口新增字段，档位为重要，由用户批。

## 起因

用户希望派审查或执行时不必每次点名模型：Codex 后端默认用 `gpt-6.2-sol`，Claude Code 后端默认用 Opus 5.5，有特殊需求才点名。现在 delegate 不点名时什么都不传：Codex 跟随 `~/.codex/config.toml`，Claude Code 落到 Claude CLI 的账号默认，不保证是 Opus 5.5；报告和结果文件也看不出这次的模型是点名的还是宿主默认。

## 前提

用户 2026-11-26 确认（「按建议确认」）：

- **P1 配置文件位置与格式。** `${XDG_CONFIG_HOME}/delegate/config.json`；`XDG_CONFIG_HOME` 未设或不是绝对路径时用 `~/.config/delegate/config.json`。按后端分 `model`、`effort` 两个字段（格式见下）。用户级，不进任何仓库；delegate 只读不写，不创建、不改 Codex／Claude 的全局配置。
- **P2 自动选审查者。** `--backend auto` 选中哪家就用哪家的配置默认值；`auto` 仍不接受点名 `--model`／`--effort`（reviewer-selection E4 不变）。
- **P3 续跑不用配置。** `--resume`、`--continue` 沿用原会话记下的模型和推理强度，不读配置里的值。
- **P4 不支持的参数照旧拒绝。** 配置给 `claude-code` 写 `effort` → 配置错误，不静默忽略。
- **P5 配置错就硬失败。** 文件存在但读不了、不是合法 JSON、结构不对、模型名不过 `model_error`、推理强度不在取值内，不管这次用不用得上，review／run 一律退出 64，不退回宿主默认。
- **P6 来源进报告与结果文件。** 新增字段，接口升 1.8，只增字段；按规矩先告诉 ecosystem-lead。
- **两家都写进 delegate 配置。** Codex 全局配置已是 `gpt-6.2-sol`，delegate 配置里仍写一份：来源显示为「配置」，以后改 Codex 全局配置不影响委托（用户按建议确认）。

本规格新提出、请用户审时一并确认：

- **E1 优先级与来源取值。** 每个后端分别对模型和推理强度取值：这次点名 > delegate 配置 > 宿主默认。来源取值 `explicit`（点名）、`config`（配置）、`host_default`（什么都不传，交给宿主）、`resumed`（续跑沿用原会话）。模型和推理强度各有一个来源，可以不同（例如点名模型、推理强度来自配置）。
- **E2 配置格式。** 只认下面这些键，多出来的键（含拼错的后端名、字段名）算配置错误，防止拼错后悄悄落到宿主默认：

  ```json
  {
    "schema": "delegate.config/v1",
    "defaults": {
      "codex": {"model": "gpt-6.2-sol", "effort": "high"},
      "claude-code": {"model": "claude-opus-5-5"}
    }
  }
  ```

  `schema` 必填且等于 `delegate.config/v1`；`defaults` 必填；每个后端和每个字段都可省略，省略即该项走宿主默认。`effort` 取值同 `--effort`（`none|minimal|low|medium|high|xhigh`）。文件须是普通文件（不跟随软链接）、不超过 64 KiB、UTF-8。文件不存在 = 没有配置，不算错误。
- **E3 错误输出。** 配置错误只打一行到 stderr：`delegate: invalid config <路径>: <固定原因码>[ at <字段路径>]`，字段路径指到出错的键（例如 `defaults.claude-code.effort`），整份文件的问题（读不了、不是 JSON 等）不带；只写键名，不写值。这一行以 `delegate: invalid config` 开头，和参数错误、执行器故障区分得开，module-crew、autopilot 等调用方可以原样转给用户（ecosystem-lead #23282 提醒）。原因码取 `unreadable`、`not_regular_file`、`too_large`、`invalid_json`、`invalid_schema`、`unknown_key`、`invalid_model`、`model_belongs_to_other_backend`、`invalid_effort`、`effort_not_supported`；不回显文件内容。
- **E10 两个宿主读同一份配置。** 配置只按 P1 的路径找，不看是哪个宿主调用：在 Codex 里调 `--backend claude-code` 审查，和在 Claude Code 里调一样读这份配置（用户原话「在 Codex 里需要 Claude Code 配合审查时用 Opus 5.5」，ecosystem-lead #23282 提醒）。
- **E4 报告字段。** 审查报告顶层新增 `model_source`（取值见 E1，审查没有续跑所以不出现 `resumed`），列入 v1 稳定字段。`requested_model` 改为「delegate 这次传给后端的模型」（点名或配置给的值；宿主默认时为 `null`），仍属诊断字段；`observed_models` 不变。报告不加推理强度字段（审查报告现在本来就没有）。
- **E5 结果文件字段。** run 结果文件新增 `modelSource`、`effortSource`（取值见 E1），`model`、`effort` 含义改为「delegate 这次传给 Codex 的值」（宿主默认时仍为 `null`，与今天相同）。结果文件 `schema` 仍为 `1`。
- **E6 运行时可见。** run 输出里的「模型：… / 推理档：…」一行在值后面注明来源，例如 `模型：gpt-6.2-sol（delegate 配置） / 推理档：宿主默认`；`--dry-run` 审查预览带 `requested_model` 与 `model_source`。
- **E7 体检。** `/delegate:doctor`（含 `--backend codex|claude-code`）在原输出前加一段「默认模型」：配置文件路径与是否存在；每个后端的模型和推理强度及来源（`config` 或 `host_default`）；配置错误时列出原因码，其余检查照常跑完，退出码为 1。配置不存在或有效时退出码与今天相同。`--reviewers` 输出不变。
- **E8 兼容入口不读配置。** 直接调用 `codex-exec.sh` 的旧兼容入口不读 delegate 配置，行为与今天相同（来源为 `explicit` 或 `host_default`）；只有经 `delegate-exec.sh`（`/delegate:review`、`/delegate:run`）进来的才读。
- **E9 接口 1.8。** `interface.json`：`interface` 升 `1.8`，顶层新增 `defaults: {"config": "${XDG_CONFIG_HOME:-~/.config}/delegate/config.json", "schema": "delegate.config/v1", "sources": ["explicit", "config", "host_default", "resumed"], "reportField": "model_source", "resultFields": ["modelSource", "effortSource"]}`。其余不变。

依赖：[reviewer-selection](reviewer-selection.md)（`auto` 选中后端后再取默认值）、[run-result](run-result.md)（结果文件字段）、[detection](detection.md)（doctor）。

## 现状调研

查过的（基于 main `d59cc42`）：
- `delegate_model.model_error(backend, model)`：模型名格式与「属于另一家」校验；`delegate_backend.parse()` 与 `codex-exec.sh` 都调它。
- `delegate_backend.parse()`：`--effort` 取值 `none|minimal|low|medium|high|xhigh`，Claude 后端不接受 `--effort`；`--resume`／`--continue` 不能带 `--model`／`--effort`。`main()` 把 run 的 `--model`／`--effort` 原样转给 `codex-exec.sh`；审查走 `codex_review()` 或 `native_review()`，都读 `args.model`。
- `codex-exec.sh`：`MODEL` 为空时不加 `-m`；续跑从 `run_state.py check` 的第 2、3 行取原会话的模型和推理强度（第 199～200 行）；第 544、596 行打印「模型：…（空为配置默认）」；结果文件写 `model`、`effort`。
- `claude_review.py` 第 132～133 行：`args.model` 为空时不加 `--model`。
- `review_result.base_report()`：报告有 `requested_model`、`observed_models`（诊断字段）；Claude 后端点名 `claude-*` 而观察到的不同 → `requested_model_not_observed`。
- `delegate_cli.review()`：`auto` 先按占位后端 `codex` 校验参数，取完上下文再 `reviewer_select.choose()` 定后端；`--dry-run` 预览带 `requested_model`。
- `review_doctor.py`：无参数或 `--backend codex` 时先打印后端能力再 `exec hooks/doctor.sh`；`--backend claude-code` 跑 Claude 预检。
- 仓库和本机都没有任何 delegate 用户级配置文件（`~/.config/delegate` 不存在）。

## 影响面与实现方案

1. **配置读取。** 新文件 `plugins/delegate/scripts/delegate_defaults.py`：`config_path()` 按 P1 算路径；`load(path)` 按 E2 校验，返回 `{backend: {model, effort}}` 或抛带 E3 原因码的错误；`resolve(backend, model, effort, config)` 是纯函数，按 E1 返回 `(model, model_source, effort, effort_source)`。校验复用 `delegate_model.model_error()` 和 `--effort` 的取值表，不另写一份。
2. **入口。** `delegate_cli.main()` 在分派 review／run 之前调 `load()`；出错按 E3 打印、退出 64（P5）。`--resume`／`--continue` 也先校验配置（P5「不管用不用得上」），但不取值，来源记 `resumed`（P3）。
3. **审查。** 显式后端：参数校验通过后用 `resolve()` 填 `args.model` 与来源。`auto`：`choose()` 定后端之后再 `resolve()`（P2）。Codex 审查同时得到推理强度（转成现有 `-c model_reasoning_effort=…`）；Claude 后端配置里不可能有 `effort`（E2/P4 已拦）。`base_report()` 与 `context_failure()` 加 `model_source`；`--dry-run` 预览同步（E6）。
4. **执行。** `delegate_backend.main()` 把解析后的 `--model`／`--effort` 转给 `codex-exec.sh`，来源经内部参数 `--model-source`／`--effort-source` 传入（不读环境变量，免得环境里残留的值把点名误标成配置）；`codex-exec.sh` 只接受 `explicit`／`config`／`host_default`，其他值退出 64，未给时按今天规则推断（有值为 `explicit`，空为 `host_default`），续跑一律 `resumed`（E8 兼容入口因此不变）。结果文件（`run_state.py` 写）加 `modelSource`、`effortSource`，打印行按 E6 注明来源。
5. **体检。** `review_doctor.py` 按 E7 在原输出前加「默认模型」一段。
6. **接口与文档。** `interface.json` 按 E9；`spec/integration-interface.md` 加 1.8 一条并把 `model_source` 列入稳定字段；`spec/run-result.md` 字段表加两项；插件 README、命令说明（`review.md`、`run.md`、`doctor.md`）加配置文件说明与示例；中英文同步；待发行说明。

## 技术栈与命令

Python 3 标准库与 Bash 3.2；测试用 `unittest`、桩 Codex／桩 Claude 与临时 `HOME`／`XDG_CONFIG_HOME`，不跑真实模型、不付费，不碰用户真实的 `~/.config`。

```bash
python3 -B plugins/delegate/tests/test-default-model.py
python3 -B plugins/delegate/tests/test-review-cli.py
python3 -B plugins/delegate/tests/test-run-result.py
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 代码风格

保持现有风格：4 空格缩进、标准库、诊断只用固定码；取值逻辑是不碰外部的纯函数，配置内容从外面传入。复用现有校验，例如（`delegate_backend.parse()` 现有写法）：

```python
    error = model_error(result.backend, result.model)
    if error:
        raise ArgumentError(error)
```

## 回归测试

| 编号 | 用例 | 执行方式 | 证据 |
|---|---|---|---|
| DM-01 | `resolve()` 穷举：模型与推理强度各自在「点名／配置有／配置无」下的取值与来源；点名覆盖配置 | 命令 | `test-default-model.py` |
| DM-02 | 配置路径：`XDG_CONFIG_HOME` 为绝对路径、未设、为相对路径三种 | 命令 | `test-default-model.py` |
| DM-03 | 配置错误逐个原因码（E3 十项各一例）→ review 与 run 都退出 64、stderr 只一行、字段类错误带字段路径、不回显值；文件不存在不算错 | 命令 | `test-default-model.py` |
| DM-04 | 配置有错但这次用不上（例如只有 `claude-code` 段写错、跑 Codex run；或 `--resume`）→ 仍退出 64 | 命令 | `test-default-model.py` |
| DM-05 | run 端到端（桩 Codex）：配置给模型与推理强度 → 桩收到 `-m gpt-6.2-sol` 与 `model_reasoning_effort="high"`；结果文件 `modelSource=config`、`effortSource=config`；打印行注明来源 | 命令 | `test-run-result.py` |
| DM-06 | run 点名 `--model` 覆盖配置：结果 `modelSource=explicit`，推理强度仍为 `config` | 命令 | `test-run-result.py` |
| DM-07 | 续跑与接续（`--resume`、`--continue`）：沿用原会话的模型和推理强度，不读配置值，来源 `resumed` | 命令 | `test-run-resume.py`、`test-run-continue.py` |
| DM-08 | 审查端到端：显式 `codex`、显式 `claude-code`、`auto` 选中两家各一次 → 桩收到配置的模型；报告 `model_source=config`、`requested_model` 为配置值；无配置时 `host_default` 与 `null` | 命令 | `test-review-cli.py` |
| DM-09 | `--dry-run` 预览带解析后的 `requested_model` 与 `model_source` | 命令 | `test-review-cli.py` |
| DM-10 | 直接调用 `codex-exec.sh` 兼容入口不读配置 | 命令 | `test-default-model.py` |
| DM-11 | doctor：无配置、有效配置、配置错误三种输出；错误时退出 1、其余检查照常；`--reviewers` 不变 | 命令 | `test-default-model.py` |
| DM-12 | `interface.json` 为 1.8，`defaults` 与 E9 一致；两项 plugin validate 通过 | 命令 | `test-interface.py` |
| DM-13 | 回归老功能：没有配置文件时现有全部套件不改断言通过 | 命令 | `scripts/validate.sh` |
| DM-15 | 从 Codex 宿主调用（桩环境：设 `CODEX_THREAD_ID`、去掉 `CLAUDE_*` 变量）`--backend claude-code` 审查 → 桩 Claude 收到配置的 `--model claude-opus-5-5`，报告 `model_source=config` | 命令 | `test-review-cli.py` |
| DM-14 | 文档：中英文合同、integration-interface、run-result 字段表、插件 README、命令说明、待发行说明同步 | 人工 | 逐项核对记入 todo |

## 风险与回滚

| 风险 | 影响 | 缓解 |
|---|---|---|
| 配置写错导致所有委托失败 | 中 | 错误一行写明路径与原因码；doctor 能单独查；删掉或改正文件即恢复 |
| 测试误读用户真实配置 | 中 | 所有套件用临时 `HOME` 与 `XDG_CONFIG_HOME`；新增一条静态检查确认套件没有读真实 `~/.config` |
| 配置的 Claude 模型名与账号不匹配 | 低 | 照旧由 Claude CLI 报错，按失败报告；`claude-*` 点名与观察不一致仍报 `requested_model_not_observed` |
| 使用方把 `requested_model` 当成「用户点名」 | 低 | 它本来是诊断字段；新增的 `model_source` 才是稳定字段，合同写明读法 |

回滚：删掉配置文件即与 0.12.6 行为相同；代码回退不影响结果文件 `schema 1` 的读法（只增字段）。

## 方案取舍

- 用 JSON 不用 TOML：Python 标准库 3.11 起才有 `tomllib`，macOS 自带的 `/usr/bin/python3` 是 3.9.6；JSON 用标准库就能严格校验。
- 多出来的键算错误：配置拼错是最可能的失误，静默落到宿主默认正是用户要避免的「以为用了 Opus 5.5 其实没有」。
- 不读 Codex／Claude 的全局配置来推算「宿主默认是哪个模型」：那是宿主的事，读了也可能不准；来源写 `host_default` 就够调用方判断。
- 不给 `--max-turns`、`--max-budget-usd` 配默认值：本次需求没有，按需再加。

## 并行边界

- 独占：`plugins/delegate/scripts/delegate_defaults.py`、`plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/review_doctor.py`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/interface.json`、`plugins/delegate/commands/review.md`、`plugins/delegate/commands/run.md`、`plugins/delegate/commands/doctor.md`、`plugins/delegate/tests/test-default-model.py`、`plugins/delegate/tests/test-review-cli.py`、`plugins/delegate/tests/test-run-result.py`、`plugins/delegate/tests/test-run-resume.py`、`plugins/delegate/tests/test-run-continue.py`、`plugins/delegate/tests/test-interface.py`、`scripts/validate.sh`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`spec/integration-interface.md`、`spec/run-result.md`、`docs/en/SPEC-integration-interface.md`、`docs/en/SPEC-run-result.md`、`docs/en/SPEC-default-model.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`、`docs/en/capability-map.md`、`scripts/run_suites.py`、`scripts/tests/test-run-suites.py`、`scripts/tests/test-validation-discovery.py`

## 开发边界

- **Always：** 没有配置文件时行为与 0.12.6 相同；点名永远优先；配置错就硬失败；诊断只用固定码；中英文同步。
- **Ask first：** 支持 TOML 或其他配置位置；给更多参数配默认值；读宿主全局配置推算模型；提交、推送、发版。
- **Never：** 写、创建或修改任何配置文件（delegate 自己的、Codex 的、Claude 的）；配置错时静默退回宿主默认；在输出里回显配置文件内容。

## 开放问题

- 无。
