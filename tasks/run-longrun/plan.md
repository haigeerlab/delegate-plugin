# 实施计划：run-longrun

<!-- spec-guard: review approved -->

日期：2026-10-27。规格：[spec/run-longrun.md](../../spec/run-longrun.md)（用户 2026-10-27 批准，指纹 68219af7cc21）。任务：[todo.md](todo.md)。前提：run-result、run-continue 已完成；0.7.1 的清理已在 main（`64d7ece`）。

**修订 R1（2026-10-27，用户原话：「选 A：新增 plugins/delegate/references/run.md 放 1.3 用法和授权纪律，run.md 只加一句必须先读的指示；四个模块的文档任务按此修订，继续做。」）：** 命令说明渲染后不得超过 4000 字节（`test-command-migration.py`；超出时 Codex 跳过该 skill），`run.md` 已无余量。所以下文文档任务里「`run.md` 写……」的用法与纪律，一律改写进 `plugins/delegate/references/run.md`；`run.md` 只更新 frontmatter 的 argument-hint，并保留那一句「必须先读」的指示。对应成功条件里的命令说明部分，按写进参考文件验收。代码任务不变。

## 架构决定

- **只改「T 从哪来」。** `codex-exec.sh` 目前把 `DELEGATE_TIMEOUT_SECONDS` 夹到不超过 540，得到 `T`。带 `--timeout` 时 `T` 直接取参数值；不带时一行不改。`run_state.py deadlines` 的公式不变，只放宽它接受的 `T` 上限（到 7200）。
- **不碰清理。** `run_codex.py` 与 `stop_runner` 都不改。中止清理由 0.7.1 的回归测试守住。
- **范围校验放在 `delegate_backend.py`。** 和其他参数错误一样，在调用 Codex 之前退出 64；`codex-exec.sh` 再校验一次作为防线（它也能被直接调用）。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Checkpoint 1 → Task 3 → Checkpoint 2
```

## Task 1：`--timeout` 参数、期限与结果字段

**描述：**

- `delegate_backend.py` 解析 `--timeout`：只接受十进制整数，范围 541～7200，可与 `--resumable`、`--resume`、`--continue` 同用；
- `codex-exec.sh` 带 `--timeout` 时 `T` 取该值，忽略环境变量；
- `run_state.py deadlines` 接受到 7200 的值；
- 结果文件加 `timeoutSeconds`，不带 `--timeout` 时也写，值为默认算出的 `T`。

新建 `test-run-longrun.py`。

**验收条件：**
- 先红后绿；
- RL-01：540、7201、`abc`、`-1`、空值都退出 64，且不调用 Codex；
- RL-02：`--timeout 1800` 时，提示词里的 `M`、`S` 分别是 1755、1665，`run_codex.py` 收到的期限参数是 `--report <…>.cleanup 1755`；不带 `--timeout` 时与今天一致；
- RL-03：结果文件有 `timeoutSeconds`；
- RL-04：用桩断言 `M`、`W` 原样进入 `run_codex.py` 的参数；0.7.1 的 `test-reap-fake-endpoint.py`、`test-channel-regressions.py` 不改，且通过。

**验证：** `python3 -B plugins/delegate/tests/test-run-longrun.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`、`python3 -B plugins/delegate/tests/test-channel-regressions.py`、`python3 -B plugins/delegate/tests/test-reap-fake-endpoint.py`、`python3 -B plugins/delegate/tests/test-backend.py`

**依赖：** run-continue 完成。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-longrun.py`。**规模：** M。

## Task 2：接口与能力事实

**描述：** `interface.json` 加 `run.longRun`；`delegate_capabilities.py` 给 codex 加 `longRun` 能力事实；`test-interface.py` 加断言。

**验收条件：** RL-05；已有字段与断言不变；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 1。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/scripts/delegate_capabilities.py`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

跑本模块和前两个模块涉及的全部测试，以及 `git diff --check`，结果记入 todo 后继续。

## Task 3：命令说明、README 与待发行说明

**描述：**

- `run.md` 写 `--timeout` 和「后台调用要求」三条：超过宿主前台期限必须用后台模式；停止运行靠停掉宿主的后台任务；等待上限按 `T + 30` 秒留足；
- `help.md` 加 `--timeout`；
- 中英文 README 加「长任务」一节；
- 中英文待发行说明加 `--timeout`。

run-resume 的 A7 修订记录、run-timeout 与 channel 的指向句，在 run-rules 的汇总任务里写。

**验收条件：** RL-06 的命令、README、待发行说明部分，中英文内容对应。

**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`

**依赖：** Task 2。**文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（report）：模块收尾与本地提交

跑总验证、两项 plugin validate、`git diff --check`，结果记入 todo；勾完本模块，把 `activeModule` 切到 `run-check`；本地提交一次，不推送。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 使用方在前台调用大期限，被宿主的 600 秒期限杀掉 | 中 | `run.md` 写明必须用后台模式；被宿主杀掉时按信号处理，0.7.1 负责回收 |
| 没有真实的 541 秒以上实测 | 低 | 清理与期限长短无关，由 0.7.1 的回归覆盖；1.3 合并实测（run-rules）里安排一轮后台 `--timeout` |

## 开放问题

无。
