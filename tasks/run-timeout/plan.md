# 实施计划：run-timeout

<!-- spec-guard: review approved -->

日期：2026-10-26。规格：[spec/run-timeout.md](../../spec/run-timeout.md)，用户 2026-10-26 原话「批准 run-timeout 的 Spec 和能力图新行。」，指纹 f45051d628d0。任务：[todo.md](todo.md)。

本计划覆盖免费的本地实现与验证，外加一次需单独授权的付费实测（Checkpoint 3）。提交、推送、PR、版本号与发版另行授权；发版前先告知 delegate 负责人，由其报 ecosystem-lead。

## 架构决定

- **计算集中在 `run_state.py`。** 期限常量与算式（`W`、`M`、`S`）、`TIME_UP:` 判定、改动文件清单（基线 porcelain 快照与运行后对比）都放进 `run_state.py`，作为纯函数并提供子命令。`codex-exec.sh` 只调用子命令、拼接输出，shell 里不做算术，也不解析 JSON。测试与实现从同一处常量读取。
- **普通 run 的参数一项不改。** 普通 run 只在提示词末尾追加时间预算段，交给 `run_codex.py` 的期限从 `T` 改为 `M`。可续跑 run 与续跑的参数也不变。
- **收尾轮复用续跑那套参数。** 收尾轮复用 `codex exec resume` 的参数拼法，只把沙箱固定为 `read-only`、期限换成 `W`、日志与答复换成 `.wrapup` 后缀。`W == 0`（总期限很短，例如测试里的 2 秒）时不启动 Codex，直接按「收尾轮超时」走兜底。规格写的是「期限 W 内没完成即超时」，0 秒期限必然超时，所以与规格一致。
- **超时也走成功路径的输出顺序。** `status=timeout` 时，答复、元数据、结果行都写到 stdout，与成功路径的顺序相同；退出码为 124。Git 验收块在非 0 退出时按现有规则写到 stderr，不改。
- **测试桩只做最小扩展。** `stub-codex` 能识别 `exec resume`，此时读 `STUB_RESUME_ANSWER`、`STUB_RESUME_SLEEP_SECONDS`；`STUB_SESSION_ID` 非空时往 stdout 打一行 `session id: <id>`。不设这些变量时，行为与今天相同。
- **不改的部分。** 不改 `delegate_backend.py`、`delegate_cli.py`，没有新参数；不改 review 路径。
- **执行方式。** 串行，在主会话做，不派子代理（每个 task 都不大，派出去省不了主会话轮次）。每个行为 task 都先写测试并确认它是红的，再实现，让它转绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Checkpoint 1
→ Task 4 → Task 5 → Task 6 → Task 7 → Checkpoint 2
→ Task 8 → Task 9 → Checkpoint 3 → Checkpoint 4
```

Task 1（EPERM）独立，先做，风险最低。Task 2 是后面所有 task 的计算基础。收尾轮（Task 4）风险最高，放在 Checkpoint 1 之后立即做。

## Task 1：killpg EPERM 修复

**描述：** `run_codex.py` 的 `stop_group` 里有两处 `os.killpg`，都改为同时捕获 `ProcessLookupError` 与 `PermissionError`，之后照常 `process.wait()`。在 `test-channel-regressions.py` 加回归测试：用模拟方式让 `os.killpg` 抛 `PermissionError`（导入模块后替换），断言 `stop_group` 不抛异常、能回收进程，`main()` 返回原退出码。

**验收条件：**
- 先红：修改前，模拟 EPERM 时测试因未捕获的 `PermissionError` 失败；
- 再绿：两处 killpg 都容忍 EPERM；现有超时、信号回归测试不变且通过（RT-10）。

**验证：** `python3 -B plugins/delegate/tests/test-channel-regressions.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/run_codex.py`、`plugins/delegate/tests/test-channel-regressions.py`。**规模：** XS。

## Task 2：`run_state.py` 的期限、判定与文件清单

**描述：** 在 `run_state.py` 增加以下内容：

- **期限常量与计算：** 常量 `WRAPUP_CAP = 45`、`WRAPUP_DIVISOR = 6`、`THRESHOLD_MARGIN = 90`、`THRESHOLD_DIVISOR = 2`；`deadlines(total)` 返回 `(W, M, S)`。
- **子命令 `deadlines <T>`：** 输出三行，分别是 W、M、S。
- **`TIME_UP:` 判定：** `classify` 先判 `TIME_UP:`（返回 `timeout`），再判 `NEED_USER:`；新增参数，指明普通 run 不判 `NEED_USER:`。
- **改动文件清单：** `changed_files(baseline_lines, current_lines)` 返回在当前 porcelain 中、但不在基线中的行；子命令 `changes <基线文件>` 读取当前 `git status --porcelain` 后输出清单。
- **记录超时状态：** `record` 支持 `status=timeout`。
- **续跑校验：** `check_resume` 接受 `needs-input` 与 `timeout`。

新建 `test-run-timeout.py`，先写这一层的单元测试。

**验收条件：**
- 先红：新函数缺失时测试失败；
- 再绿：
  - `deadlines(540) == (45, 495, 405)`；`deadlines(2)` 得到 `W == 0`、`M == 2`；`deadlines(60) == (10, 50, 25)`；
  - `TIME_UP:` 前有空白也能识别；标记不在第一行时不算；
  - 文件清单：基线里已有的行不列，新增的行要列；
  - `check_resume` 对 `timeout` 放行、对 `done` 拒绝。
- `test-run-resume.py` 现有单元断言全部不改，且通过。

**验证：** `python3 -B plugins/delegate/tests/test-run-timeout.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-timeout.py`。**规模：** S。

## Task 3：时间预算段、`M` 期限与 `TIME_UP` 结束

**描述：** 在 `codex-exec.sh` 中：

- 启动 Codex 前取 `T0` 和 `deadlines` 的结果，在所有 run 与续跑的提示词末尾追加规格中的时间预算段；
- 交给 `run_codex.py` 的期限改为 `M`；
- 答复判为 `timeout` 时：输出答复、元数据（加一行 `收尾：主动停`）与结果行 `status=timeout`，退出 124；
- 普通 run 的 `done` 路径不变。

同时调整两处受影响的已有断言，各自理由写进 todo 记录：

1. `test-channel.sh` 第 16 项：逐字比对改为「原提示词 + 时间预算段」。`T0` 每次运行不同，所以改用固定前缀加正则匹配。
2. `test-run-resume.py`：普通 run 的参数断言不改（仍含 `--ephemeral`）；只把提示词结尾断言为时间预算段，开头断言保持不变。

**验收条件：**
- 先红：新测试断言提示词含时间预算段、`TIME_UP:` 答复退出 124，测试失败；
- 再绿：
  - RT-01：普通 run 参数逐项不变；可续跑 run 与续跑参数不变；
  - RT-02：`<M>`、`<S>` 与 `deadlines` 输出一致；
  - RT-03：普通 run 与可续跑 run 各一例，`TIME_UP:` → 退出 124、stdout 末行 `status=timeout`、不调用收尾轮。

**验证：** `python3 -B plugins/delegate/tests/test-run-timeout.py`、`/bin/bash plugins/delegate/tests/test-channel.sh`、`python3 -B plugins/delegate/tests/test-run-resume.py`

**依赖：** Task 2。**文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-run-timeout.py`、`plugins/delegate/tests/test-channel.sh`、`plugins/delegate/tests/test-run-resume.py`。**规模：** M。

## Checkpoint 1（report）：第一道收尾到位

跑 Task 1–3 涉及的四个测试与 `git diff --check`，把命令和结果记入 todo 后继续。

## Task 4：收尾轮与兜底

**描述：** 在 `codex-exec.sh` 中，主运行退出 124 时按以下分支处理：

- **可续跑 run 与续跑：** 从日志取会话 ID，以只读沙箱、期限 `W` 跑一轮收尾，日志与答复用 `.wrapup` 后缀。收尾轮成功时用它的答复，元数据记 `收尾：收尾轮`；否则输出兜底文字，原因为规格所列之一，元数据记 `收尾：兜底（原因）`。
- **普通 run：** 直接输出兜底文字，原因为「普通 run 不保留会话」。

两种情况都输出结果行，退出 124；stderr 仍输出「超过 <M> 秒被中止」。可续跑 run 与续跑写入 `timeout` 状态文件。

`stub-codex` 加 `STUB_RESUME_ANSWER`、`STUB_RESUME_SLEEP_SECONDS`、`STUB_SESSION_ID`。

**验收条件：**
- 先红：新测试断言收尾轮调用与兜底文字，测试失败；
- 再绿：
  - RT-04：收尾轮只调用一次，参数为 `exec resume`、`-c sandbox_mode="read-only"`（写模式也一样）、同一会话 ID、收尾提示词；
  - RT-05：五种兜底原因各一例，`resumable` 正确；
  - RT-07：缩短期限下总耗时不超过 `T` 加清理余量；
  - RT-09：信号中断（143）不触发收尾、不输出结果行；现有 C23 与回归测试的断言不改，且通过。

**验证：** `python3 -B plugins/delegate/tests/test-run-timeout.py`、`/bin/bash plugins/delegate/tests/test-channel.sh`、`python3 -B plugins/delegate/tests/test-channel-regressions.py`

**依赖：** Task 3。**文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/stub-codex`、`plugins/delegate/tests/test-run-timeout.py`。**规模：** M。

## Task 5：写模式改动文件清单与清理

**描述：** 写模式启动前另存一份 porcelain 快照（放在日志目录，用 `<runId>.baseline` 命名）。兜底文字按规格附上文件清单；只读模式写「只读运行，不列文件」。保留清理时，同 runId 的 `.wrapup`、`.wrapup.answer`、`.baseline` 一并删除。

**验收条件：**
- 先红：新测试断言兜底文字附有文件清单、清理时删除新后缀文件，测试失败；
- 再绿：
  - RT-06：运行前已有的修改不列，运行中新增或改动的文件要列；Git 验收块照常输出；
  - RT-08 的清理部分：新后缀文件随日志一起删除；
  - 现有 RR-08 清理测试不改，且通过。

**验证：** `python3 -B plugins/delegate/tests/test-run-timeout.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`

**依赖：** Task 4。**文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-run-timeout.py`。**规模：** S。

## Task 6：从 `timeout` 续跑

**描述：** `--resume` 接受状态为 `timeout` 的 runId。续跑提示词与 run-resume 的续跑相同，末尾加时间预算段。`run_state.py` 的拒绝原因里，`run not waiting for input` 的触发条件按规格改。普通 run 超时的 runId 没有状态文件，照旧按 `run not found` 拒绝。

**验收条件：**
- 先红：新测试断言 `--resume` 接受 timeout 的 runId，测试失败；
- 再绿：
  - RT-08：可续跑 run 超时后能 `--resume`，`parent` 链正确；`done` 被拒；普通 run 超时的 runId 被拒；
  - `test-run-resume.py` 中「状态不是 needs-input」的拒绝断言，按影响面改为用 `done` 构造，并在 todo 记录里说明改动理由。

**验证：** `python3 -B plugins/delegate/tests/test-run-timeout.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`

**依赖：** Task 4。**文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-timeout.py`、`plugins/delegate/tests/test-run-resume.py`。**规模：** S。

## Task 7：接口 1.2

**描述：** `interface.json` 升到 1.2：`run.resume.statuses` 追加 `"timeout"`，新增 `run.timeout`。`test-interface.py` 更新版本与 `statuses` 断言，新增 `run.timeout` 断言；其余断言不改。

**验收条件：**
- 先红：测试改为期望 1.2 后失败；
- 再绿：RT-11 的断言全部通过，两项 plugin validate 都通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 6。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 2（report）：免费验证全绿

运行以下命令，把每条命令和结果记入 todo 后继续：

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## Task 8：命令说明、README 与待发行说明

**描述：** 更新以下文档：

- `run.md`、`help.md`：超时输出、`timeout` 状态、续跑，以及「先看退出码为 0、再看 `status=done`」；
- 中英文 README：可续跑一节、对外接口一节写明 `statuses` 是开放集合，补上 1.2；
- `docs/releases/unreleased.md` 及英文对应页：升级提示。

**验收条件：** RT-12 的文档部分齐全，中英文一致；validate 通过。

**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、人工比对中英文。

**依赖：** Task 7。**文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`（及英文页）。**规模：** M。

## Task 9：合同指向句与 Always 规则修订

**描述：** 按规格「影响面」改以下合同，每处只加一句指向本模块，或做影响面已列明的那一处修订，其余条款不动：

- `spec/run-resume.md`：Always 规则改为「普通 run 除时间预算段外与改动前一致」，并附用户 2026-10-26 原话；A3、RR-01 与拒绝表各加一句指向；
- `spec/channel.md`：超时输出与期限分配各加一句指向；
- `spec/integration-interface.md`：1.2 与开放集合说明加一句指向；
- 以上三份规格的英文对应页同步。

改动后，run-resume 的 Spec 内容变了，需要请用户复审 run-resume 的修订，再重新记录它的批准标记。

**验收条件：** RT-12 的合同部分齐全；修订只限影响面列出的几处；`/spec-guard:verify-artifacts` 通过。

**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`、人工比对中英文。

**依赖：** Task 8。**文件：** `spec/run-resume.md`、`spec/channel.md`、`spec/integration-interface.md`，以及它们的英文对应页。**规模：** M（6 个文件，每处只改一两句）。

## Checkpoint 3（gate）：付费真实实测 H1–H5

在家目录建临时 Git 仓库，用当前源码的 `/delegate:run` 实测。下表是预计用量，执行前会再列一次，取得单独授权后才跑：

| 编号 | 验证什么 | 做法 | 付费调用 | 耗时 |
|---|---|---|---|---|
| H1 | 真实 540 秒下守时 | `--resumable` 跑一个约 15 分钟的多步任务，看模型能否在 405 秒后主动 `TIME_UP:`、在 495 秒内结束 | 1 | 约 9 分钟 |
| H2 | 收尾轮的长尾 | 用一条跨期限的长命令让主运行被强制中止（`DELEGATE_TIMEOUT_SECONDS=120`），重复 4 次，记录收尾轮耗时 | 8（主运行 4 + 收尾 4） | 约 12 分钟 |
| H3 | 大上下文下的收尾 | 先读大量文件、再被强制中止，记录收尾轮耗时 | 2 | 约 4 分钟 |
| H4 | 其他模型 | 另选一个本机可用的模型，重复 H1 的缩短版 | 1 | 约 3 分钟 |
| H5 | 写模式续跑不重复写入 | 写模式超时后 `--resume`，续跑提示里不提醒「先看文件」，检查有没有重复写入 | 2 | 约 3 分钟 |

合计约 14 次付费调用、30 分钟左右。结果写进 `docs/verification/` 的验证记录；有不成立的，回到规格修订（T6 常数按实测校准也走规格修订）。没授权时标「未验证」，不影响 Checkpoint 4 交付免费部分。

## Checkpoint 4（gate）：交付验收

把实际 diff、各验证命令的结果、未验证项与后续事项交给用户验收。提交、推送、PR、版本号与发版都另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 收尾轮与主运行合计超出 Bash 600 秒 | 高 | `M + W = T ≤ 540`；RT-07 在缩短期限下实测总耗时 |
| 提示词改动打破使用方或既有测试 | 中 | 只追加末尾一段；受影响的已有断言只改两处，并逐条记录理由 |
| 收尾轮误用写沙箱 | 高 | 沙箱硬编码为 `read-only`，RT-04 在写模式下也断言 |
| 兜底文件清单漏列 | 低 | 规格已写明这一限制；以 Git 验收块的 `git diff --stat` 为准 |
| T6 常数在真实期限下不合适 | 中 | Checkpoint 3 校准；常数集中定义，调整只改一处 |
| run-resume 规格修订后它的批准标记失效 | 低 | Task 9 之后请用户复审，再重新记录标记 |

## 开放问题

- Checkpoint 3 的模型选择（H4）和次数，执行前再与用户确认。
- 改了 run-resume 规格后要请用户复审；这次复审是否与 Checkpoint 4 合并进行，届时由用户决定。
