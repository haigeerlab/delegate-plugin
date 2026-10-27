# 实施计划：run-result

<!-- spec-guard: review approved -->

日期：2026-10-27。规格：[spec/run-result.md](../../spec/run-result.md)（用户 2026-10-27 批准，指纹 43d83f5ab434）。任务：[todo.md](todo.md)。基准：main `64d7ece`（v0.7.1）。

本模块是 interface 1.3 五个模块里的第一个（顺序：run-result → run-continue → run-longrun → run-check → run-rules），其余四个都往本模块的结果文件里加字段。五个模块全部完成、做完 1.3 合并实测之前不发版。

## 架构决定

- **新增 `run_events.py` 只管读事件流。** 会话 ID、命令与退出码、`turn.completed` 用量、失败时要渲染的事件，都由它从 `.events.jsonl` 里取，作为纯函数并提供子命令。`codex-exec.sh` 只调子命令，shell 里不解析 JSON。
- **结果文件由 `run_state.py` 写。** 它已经负责状态文件的原子写入和权限，结果文件沿用同一套写法（0600、临时文件后 `rename`、拒绝软链接）。`.cleanup` 原文行的解析也放在这里。
- **结果文件在 `finish` 里写。** 0.7.1 的 `finish` 先 `stop_runner` 再输出；结果文件放在 `stop_runner` 之后、结果行之前写，这样被中断和退出 125 的情形也能写进清理结果。
- **`session_id_from_log` 保留。** 新增按事件流取会话 ID 的函数，`codex-exec.sh` 改用新函数；旧函数和它的单元测试不动（读旧日志时仍可用）。
- **测试用各自的假 codex。** 沿用 test-run-resume、test-run-timeout 的做法：测试文件里自带假 codex，按环境变量写 JSONL 与 `-o` 文件；不改共用的 `stub-codex`。
- **执行方式。** 串行，在主会话做，不派子代理。每个行为任务都先写测试并确认红，再实现转绿。

## 受影响的现有断言（有意的参数变化，不算削弱断言）

多了 `--json`、事件流与 stderr 分开存、会话 ID 改从事件流取之后，下面这些现有测试要跟着改。每处改动只把预期改成新参数或新格式，不放宽比对方式，理由逐条记进 todo：

- `test-run-resume.py`：自带假 codex 改为输出 `thread.started` 事件；普通 run、可续跑 run、续跑的参数逐项比对（第 189 行一带）加上 `--json`。
- `test-run-timeout.py`：自带假 codex 同上；收尾轮参数比对（第 240 行一带）加上 `--json`；第 50～51 行用文本日志构造会话 ID 的夹具，改为写事件文件。
- `test-channel.sh`：Codex 参数比对的几项加上 `--json`；「完整过程日志」路径断言不变（`.log` 仍在）。
- `test-write-trust.py`、`test-review-backends.py`：断言普通 run 实际参数的地方加上 `--json`。review 路径的断言不变（review 不加 `--json`）。
- `test-channel-regressions.py` 第 336 行：路径正则不变，另加一条断言事件流路径。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Checkpoint 1
→ Task 7 → Task 8 → Checkpoint 2
```

Task 3（所有 run 加 `--json` 并拆日志）改动面最大、会让现有测试变红，放在两个纯函数任务之后立即做，尽早暴露问题。

## Task 1：事件流解析 `run_events.py`

**描述：** 新增 `run_events.py`，提供以下函数与子命令：

- `session_id(path)`：取第一条 `thread.started` 的 `thread_id`；
- `commands(path)`：取 `command_execution` 的 `command`、`exit_code`、`status`，最多 200 条，`command` 截到 1000 个字符，超出时标记截断；
- `usage(path)`：取最后一条 `turn.completed` 的 `usage`（五个字段）；
- `render_recent(path, n=10)`：取最近的 error 与命令事件，各渲染成一行。

非 JSON 行一律跳过，不报错。新建 `test-run-result.py`，先写这一层的单元测试，夹具取自实测记录里的事件样例。

**验收条件：**
- 先红：模块不存在时测试失败；
- 再绿：RS-02 的会话 ID 部分、RS-03、RS-08 的渲染部分在单元层成立（取不到会话 ID 时返回空，非 JSON 行跳过，截断规则生效）。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/run_events.py`、`plugins/delegate/tests/test-run-result.py`。**规模：** S。

## Task 2：`run_state.py` 的判定、用量差值、结果文件与清理报告解析

**描述：** 在 `run_state.py` 增加：

- **判定：** `classify` 加 `strict` 参数，`--strict` 时识别 `DONE:`，缺标记返回 `unmarked`；不带 `strict` 时行为与今天相同。
- **状态文件：** 新增 `usageTotal`、`chainRoot`、`strict` 三个字段；读旧状态文件时缺这些字段按 `null` 处理。
- **用量：** `run_usage(session_usage, parent_total)` 取差值，任一边缺失时返回 `null` 与原因。
- **结果文件：** `write_result(directory, result)`，原子写入、权限 0600、拒绝软链接。
- **清理报告：** `parse_cleanup(lines)`，从 0.7.1 的报告原文里解析出 `leftoverPids`、`unreapedPid`、`wrapperForced`；解析不到时字段为空，`lines` 原样保留。
- **子命令 `result`：** 汇总以上各项、写出结果文件，供 `codex-exec.sh` 调用。

**验收条件：**
- 先红后绿；
- 判定表每一行（RS-04 单元部分）；
- `usage.run` 取差值与两种 `null` 情形（RS-07）；
- 结果文件为 0600，写到一半失败时不留半截文件；
- 清理报告解析用 0.7.1 的三种报告行做夹具；
- `test-run-resume.py`、`test-run-timeout.py` 现有单元断言不改，且通过。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-result.py`。**规模：** M。

## Task 3：所有 run 路径加 `--json`，拆开事件流与 stderr

**描述：** 在 `codex-exec.sh` 中：

- 普通 run、可续跑 run、续跑、收尾轮的 Codex 参数都加 `--json`（放在 `-o` 之前）；
- `run_codex.py` 的 stdout 写到 `<runId>.events.jsonl`（收尾轮写到 `.wrapup.events.jsonl`），stderr 写到 `.log` 或 `.wrapup`；
- 会话 ID 改用 `run_events.py session`。

按上面「受影响的现有断言」逐处更新现有测试。

**验收条件：**
- 先红：新集成测试断言 argv 含 `--json`、事件文件与 stderr 文件分开、会话 ID 来自 `thread_id`，测试失败；
- 再绿：RS-01、RS-02；
- 普通 run 除 `--json` 外参数逐项不变；
- 受影响的现有断言逐条更新并记入 todo，其余现有断言不改；
- 0.7.1 的回归（`test-channel-regressions.py`）不改，且通过。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`、`python3 -B plugins/delegate/tests/test-write-trust.py`、`python3 -B plugins/delegate/tests/test-review-backends.py`、`python3 -B plugins/delegate/tests/test-channel-regressions.py`、`/bin/bash plugins/delegate/tests/test-channel.sh`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-run-result.py`，以及上面列出的现有测试（改动只涉及预期参数与假 codex 的输出）。**规模：** L（行为改动集中在一个文件，其余是机械更新；拆开会让中间状态的测试保持红，所以不拆）。

## Task 4：写结果文件、`result=` 行、用量行与失败诊断

**描述：** 在 `codex-exec.sh` 中：

- 在 `finish` 里、`stop_runner` 之后调用 `run_state.py result`。有结果行的情形，把 `delegate: result=<路径>` 打印到 stdout 的结果行之前；其余情形打印到 stderr。
- 元数据块加一行「用量：…」。
- 失败诊断在 stderr 末尾之后追加「最近的事件：」（`run_events.py render`）和事件流路径。
- 写模式每次运行前都记录基线快照，用来生成 `changedFiles`。

**验收条件：**
- 先红后绿；
- RS-05：结果文件在每种结束情形下都写出，包括 `done`、`needs-input`、`timeout`（主动停、收尾轮、兜底）、`failed`、`interrupted`、`unreaped`（让桩执行器退出 125）、`empty`；拒绝时不写；
- RS-06：结果行仍是 stdout 的最后一行；
- RS-07：续跑的 `usage.run` 取差值；
- RS-08：失败诊断带上最近的事件。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`、`/bin/bash plugins/delegate/tests/test-channel.sh`

**依赖：** Task 2、Task 3。**文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-result.py`。**规模：** M。

## Task 5：`--strict`

**描述：**

- `delegate_backend.py` 解析并转发 `--strict`，可与 `--resumable`、`--resume` 同用；
- `codex-exec.sh` 在时间预算段之前插入结束标记段（可续跑版与普通版两种）；
- `unmarked` 时退出 1，输出答复、元数据、`result=` 行和结果行；
- 可续跑 run 的状态文件记 `unmarked`，`--resume` 按 `run not waiting for input` 拒绝。

**验收条件：**
- 先红后绿；
- RS-04：两种提示词段的原文逐字一致；`DONE:`、`NEED_USER:`、`TIME_UP:` 与缺标记四种情形都正确；被强制中止时的状态不受 `--strict` 影响；
- 不带 `--strict` 时提示词与 Task 3 之后相同。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`、`python3 -B plugins/delegate/tests/test-backend.py`

**依赖：** Task 4。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-run-result.py`。**规模：** M。

## Task 6：接口 1.3、能力事实与清理后缀

**描述：**

- `interface.json` 改为 `"1.3"`，加 `run.result`、`run.usage`；
- `delegate_capabilities.py` 给 codex 加 `result` 能力事实；
- `test-interface.py` 加 1.3 断言；
- 清理后缀表加 `.events.jsonl`、`.wrapup.events.jsonl`、`.result.json`，测试断言 50 组清理时一并删除。

**验收条件：**
- RS-09、RS-11；
- 已有字段与已有断言不变；
- 两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`python3 -B plugins/delegate/tests/test-run-result.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 4。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/scripts/delegate_capabilities.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-interface.py`、`plugins/delegate/tests/test-run-result.py`。**规模：** S。

## Checkpoint 1（report）：免费桩测试全绿

跑 Task 1～6 涉及的全部测试和 `git diff --check`，把命令、结果、偏离 Plan 之处记入 todo 后继续。

## Task 7：共用假端点与免费真机测试

**描述：**

- 把 `test-reap-fake-endpoint.py` 里的假 Responses 端点抽成 `tests/fake-responses.py`，加一个「回一条答复」模式；
- `test-reap-fake-endpoint.py` 改为引用它，断言不改；
- 在 `test-run-result.py` 加真机用例：用临时 `CODEX_HOME`，不发送也不读取凭据，没有 `codex` 时跳过；走一遍普通 run 和可续跑 run，比对结果文件里的会话 ID、命令、退出码、用量与事件一致。

**验收条件：** RS-10；`test-reap-fake-endpoint.py` 断言不变且通过；本机有 `codex` 时真机用例实际执行（不是跳过），结果记入 todo。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`、`python3 -B plugins/delegate/tests/test-reap-fake-endpoint.py`

**依赖：** Task 6。**文件：** `plugins/delegate/tests/fake-responses.py`、`plugins/delegate/tests/test-reap-fake-endpoint.py`、`plugins/delegate/tests/test-run-result.py`。**规模：** S。

## Task 8：命令说明、README 与待发行说明

**描述：** `run.md`、`help.md` 写结果文件、`result=` 行和 `--strict`。中英文 README 加「结果文件」一节，对外接口一节补 1.3 的 `run.result`、`run.usage`。中英文待发行说明写三条升级提示：

- 过程日志变成两个文件；
- 结果行之前多一行 `result=`；
- `unmarked` 与 `unreaped` 两种状态，并提醒先看退出码。

**验收条件：** RS-12 的命令、README、待发行说明部分；中英文内容对应。RS-12 的合同指向句部分在 run-rules 的汇总任务里完成。

**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`

**依赖：** Task 6。**文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（report）：模块收尾与本地提交

- 跑总验证、两项 plugin validate、`git diff --check`，结果记入 todo；
- 勾完本模块的 todo，把 `.agent/state.json` 的 `activeModule` 切到 `run-continue`；
- 本地提交一次：提交信息用中文，不推送。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| `--json` 让很多现有测试同时变红 | 中 | 集中在 Task 3 一次改完，逐条记录理由；只改预期参数，不放宽比对方式 |
| Codex 事件格式随版本变化 | 中 | 解析器跳过不认识的行和字段；免费真机测试（Task 7）用本机实际版本核对 |
| `finish` 里写结果文件时又收到信号 | 低 | 写入走原子 `rename`；信号处理沿用 0.7.1，`finish` 只执行一次 |
| 旧合同（run-resume、run-timeout、channel）的指向句没随本模块写 | 低 | 五个模块的指向句集中在 run-rules 的「1.3 合同指向句汇总」一次写完、一次交复审，避免已批准规格的指纹反复失效；RS-12 的指向句部分在那里验收 |

## 开放问题

无。D1、D2 都已定。
