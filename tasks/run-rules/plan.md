# 实施计划：run-rules（含 1.3 收尾）

<!-- spec-guard: review approved -->

日期：2026-10-27。规格：[spec/run-rules.md](../../spec/run-rules.md)（用户 2026-10-27 批准，指纹 ea56d01837d0）。任务：[todo.md](todo.md)。前提：前四个模块已完成。

本模块是 1.3 的最后一个，所以本 Plan 还包含三件 1.3 的收尾工作：五个模块对旧合同的指向句汇总、1.3 付费合并实测（gate）和交付验收（gate）。

## 架构决定

- **规则段在 `codex-exec.sh` 里拼进提示词。** 文件校验（普通文件、不是软链接、UTF-8、非空、不超过 16 KiB、不含 NUL）放在 Python 里做，`codex-exec.sh` 只调用；原文原样放入，末尾缺换行时补一个。
- **四种调用共用一个拼接函数。** 普通 run 和可续跑 run 的规则段放在前言之后，续跑和接续的规则段放在最前；收尾轮不放。
- **旧合同的指向句集中在 Task 4。** 五个模块对 run-resume、run-timeout、channel、routing 这几个已批准规格的指向句与修订记录，在这里一次写完，交用户一次复审，再重新记录这些规格的批准标记。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Checkpoint 1 → Task 4 → Checkpoint 2
→ Checkpoint 3（gate：付费合并实测）→ Checkpoint 4（gate：交付验收）
```

## Task 1：`--rules-file` 校验与提示词拼接

**描述：**

- `delegate_backend.py` 解析 `--rules-file`（最多给一次）；
- `codex-exec.sh` 调用校验，不通过时退出 64，stderr 第一行为 `delegate: rules file not usable`，第二行写具体原因；
- 按四种调用的顺序拼进规则段；
- 结果文件加 `rules` 字段（路径、sha256、字节数）。

新建 `test-run-rules.py`。

**验收条件：**
- 先红后绿；
- RU-01：拒绝表每一项都退出 64，且不调用 Codex；
- RU-02：四种调用里规则段的位置正确，原文逐字节一致；收尾轮没有规则段；不带参数时提示词与 run-check 完成时相同；
- RU-03：结果文件有 `rules` 字段、不含原文。

**验证：** `python3 -B plugins/delegate/tests/test-run-rules.py`、`python3 -B plugins/delegate/tests/test-backend.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`

**依赖：** run-check 完成。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-rules.py`。**规模：** M。

## Task 2：接口 1.3 完整形状

**描述：** `interface.json` 加 `run.rules`；`delegate_capabilities.py` 给 codex 加 `rules` 能力事实；`test-interface.py` 断言 1.3 的完整字段集合，与规格文末的汇总逐项一致。

**验收条件：** RU-04；已有字段与断言不变；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 1。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/scripts/delegate_capabilities.py`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Task 3：命令说明、README 与待发行说明

**描述：**

- `run.md` 写 `--rules-file` 用法，以及它与 AGENTS.md 的关系（三条）；
- `help.md`、中英文 README、中英文待发行说明同步；
- 待发行说明补一节「1.3 汇总」，列出七个能力标记和升级提示。

**验收条件：** RU-05，中英文内容对应。

**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`

**依赖：** Task 2。**文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 1（report）：1.3 免费验证全绿

跑总验证（含五个模块的新测试、0.7.1 的回归、本机有 `codex` 时的假端点真机测试）、两项 plugin validate、`git diff --check`，结果记入 todo 后继续。

## Task 4：1.3 合同指向句汇总

**描述：** 五个模块各自规格「影响面」里要求的旧合同改动，在这里一次写完，中英文同步。原有条款只加指向句或修订记录，不改动：

- **`spec/run-resume.md`：**
  - 修订记录加一条：A7 只放开期限（run-longrun），记录用户原话；
  - 指向句：会话 ID 改从事件流取、状态文件新增字段（run-result）；`--continue` 与共用占位、状态类文件按 14 天保留（run-continue）。
- **`spec/run-timeout.md`：** 指向句：
  - 收尾轮加 `--json`、会话 ID 来源改变（run-result）；
  - 带 `--timeout` 时 `T` 的来源（run-longrun）；
  - 状态类文件的保留规则（run-continue）。
- **`spec/channel.md`：** 指向句：
  - Codex 参数加 `--json`、过程日志拆成两个文件（run-result）；
  - 期限上限可由 `--timeout` 放大（run-longrun）。
- **`spec/routing.md`：** 指向句：写入授权的例外（run-check）。

**验收条件：** RS-12、RC-08、RL-06、CK-08 的指向句部分完成。`verify-artifacts` 会报这四个规格「批准后已修订」，这是预期的；把改动交用户复审（Checkpoint 2），复审通过后重新记录批准标记。

**验证：** spec-guard `verify-artifacts.sh`、`git diff --check`

**依赖：** Checkpoint 1。**文件：** `spec/run-resume.md`、`spec/run-timeout.md`、`spec/channel.md`、`spec/routing.md` 及四个英文对应页。**规模：** M（只改文档）。

## Checkpoint 2（gate）：旧合同改动复审与本地提交

停下，把 Task 4 的 diff 交用户复审。复审通过后：

- 重新记录这四个规格的批准标记；
- 勾完本模块；
- 本地提交一次，不推送。

## Checkpoint 3（gate）：1.3 付费合并实测（RU-07）

停下，先报计划：在家目录的临时仓库里，用真实模型走一条完整链。

1. `--resumable --strict --rules-file` 起头；
2. `--continue --write --authorized-by --check` 接一轮；
3. 一轮 `--timeout`，用宿主后台模式；

另外，测前测后各记一次 `~/.codex/config.toml` 的 sha256。

预计 4～6 次 Codex 调用，上限 8 次。用户批准次数后再跑；结果写进 `docs/verification/` 下的新实测记录。有不成立的，回到对应模块的规格。

## Checkpoint 4（gate）：交付验收

停下，交用户验收实际 diff 和实测记录。不在本 Plan 授权范围内、要另行授权的有：

- 推送、开 PR；
- 版本号（`plugin.json`）、发版；
- 通知 module-crew。

发版前先告知 delegate 负责人，由负责人报 ecosystem-lead。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 规则段与项目 AGENTS.md 冲突时首行标记被挤掉 | 中 | 规则段写明首行标记不可改变；`--strict` 判 `unmarked` 兜底；合并实测观察 |
| 四个旧规格同时进入「批准后已修订」 | 低 | 集中在一个任务、一次复审，Checkpoint 2 为 gate |
| 合并实测超出次数 | 低 | 上限 8 次，到上限就停，照实记录 |

## 开放问题

无。
