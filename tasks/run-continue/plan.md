# 实施计划：run-continue

<!-- spec-guard: review approved -->

日期：2026-10-27。规格：[spec/run-continue.md](../../spec/run-continue.md)（用户 2026-10-27 批准，指纹 339bdbf978f2）。任务：[todo.md](todo.md)。前提：run-result 已完成（结果文件、`kind`、`chainRoot`、用量差值）。

## 架构决定

- **复用续跑的执行路径。** `--continue` 在 `codex-exec.sh` 里和 `--resume` 走同一个 `exec resume` 分支，只换三处：校验条件（`run not done`）、提示词（【下一个任务】）、`kind`。不复制一份执行代码。
- **校验放进 `run_state.py check`。** 加一个模式参数（`resume` 或 `continue`），两种模式共用拒绝表的其余各行。
- **清理挪进 `run_state.py`。** 今天的清理代码内联在 `codex-exec.sh` 里（0.7.1 刚往后缀表加了 `.cleanup`）。改为在 `run_state.py` 里集中定义两张后缀表和 14 天常量，`codex-exec.sh` 只调用子命令。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 受影响的现有断言（有意的行为变化）

状态类文件不再随 50 组清理删除，下面两处现有断言要改：不再断言 `.state.json` 和 `.resumed` 随日志删除，改为断言它们留下、并按 14 天删除。理由记入 todo。

- `test-run-resume.py` 第 254、260 行一带；
- `test-run-timeout.py` 第 310 行一带。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Checkpoint 1 → Task 4 → Checkpoint 2
```

## Task 1：校验的 continue 模式与按时间清理

**描述：** `run_state.py`：

- `check` 加模式参数：`continue` 模式只接受 `done`，否则拒绝 `run not done`；`resume` 模式行为不变。
- 新增两张后缀表：日志类含 `.cleanup`、`.events.jsonl` 等，状态类为 `.state.json`、`.resumed`、`.result.json`；新增常量 `STATE_RETENTION_DAYS = 14`；新增子命令 `cleanup <目录>`。
- `codex-exec.sh` 的 `cleanup_process_logs` 改为调用这个子命令。

新建 `test-run-continue.py`。

**验收条件：**
- 先红后绿；
- RC-03 的 `run not done` 一行；
- RC-06：用 `os.utime` 构造 15 天前与 13 天前的状态文件，前者删除、后者留下；日志类超过 50 组时删除最旧的；
- 上面两处现有断言按理由更新，其余不变。

**验证：** `python3 -B plugins/delegate/tests/test-run-continue.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`、`/bin/bash plugins/delegate/tests/test-channel.sh`

**依赖：** run-result 完成。**文件：** `plugins/delegate/scripts/run_state.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-run-continue.py`、`plugins/delegate/tests/test-run-resume.py`、`plugins/delegate/tests/test-run-timeout.py`。**规模：** M。

## Task 2：`--continue` 参数与执行

**描述：**

- `delegate_backend.py` 解析 `--continue <runId>`，校验组合：不能与 `--resumable`、`--resume`、`--model`、`--effort`、`--review-context`、claude-code 后端同用，任务不能为空；
- `codex-exec.sh` 加 `--continue` 分支：先校验（continue 模式），再占位，然后走续跑执行路径；
- 提示词按规格原文；状态文件与结果文件写 `kind: "continue"`，并沿用 `chainRoot`。

**验收条件：**
- 先红后绿；
- RC-01：argv 与提示词逐字一致；
- RC-02：新 runId、`parent`、`chainRoot`、`kind`，`usage.run` 取差值；
- RC-03：校验表每一行都退出 64，且不调用 Codex；
- RC-04：先 `--resume` 再 `--continue` 同一 runId（以及顺序反过来）都只有第一个成功；
- RC-05：写模式输出 Git 验收块。

**验证：** `python3 -B plugins/delegate/tests/test-run-continue.py`、`python3 -B plugins/delegate/tests/test-backend.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-continue.py`。**规模：** M。

## Task 3：接口与能力事实

**描述：** `interface.json` 加 `run.continue`；`delegate_capabilities.py` 给 codex 加 `continue` 能力事实；`test-interface.py` 加断言。

**验收条件：** RC-07；已有字段与断言不变；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 2。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/scripts/delegate_capabilities.py`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

跑本模块和 run-result 涉及的全部测试，以及 `git diff --check`，结果记入 todo 后继续。

## Task 4：命令说明、README 与待发行说明

**描述：**

- `run.md` 写 `--continue` 用法和纪律三条；
- `help.md` 写 `--continue`，并提示「`--resume` 遇到 `done` 请改用 `--continue`」；
- 中英文 README 加「接着派下一个 Task」一节；
- 中英文待发行说明写 `--continue`，以及「状态文件改为保留 14 天」。

合同指向句在 run-rules 的汇总任务里写。

**验收条件：** RC-08 的命令、README、待发行说明部分，中英文内容对应。

**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`

**依赖：** Task 3。**文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（report）：模块收尾与本地提交

跑总验证、两项 plugin validate、`git diff --check`，结果记入 todo；勾完本模块，把 `activeModule` 切到 `run-longrun`；本地提交一次，不推送。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 状态类文件按时间清理后，本机 `$TMPDIR/delegate` 里的文件变多 | 低 | 状态文件很小；14 天上限；超过 50 组的日志照删 |
| `--resume` 与 `--continue` 并发抢同一个 runId | 低 | 共用排他创建的 `.resumed` 占位，由测试守住 |
| 挪动清理代码时，0.7.1 新加的 `.cleanup` 被漏掉 | 中 | 后缀表集中定义，测试逐个后缀断言 |

## 开放问题

无。
