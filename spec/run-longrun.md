# 规格：run-longrun（`--timeout` 放开期限）

<!-- spec-guard: review approved 68219af7cc21 -->

简体中文 | [English](../docs/en/SPEC-run-longrun.md)

2026-10-27 起草；用户 2026-10-27 批准，原话：「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」对应生态方案 S38 第 2 项与决定点 2，用户 2026-10-27 批准原话：「……A7 只放开期限、用 --timeout 轻方案……」（全文见 [run-result](run-result.md)）。一个模块的 Task 可能要跑十几分钟，今天 540 秒的上限会把它强制中止。

## 前提（2026-10-27 用户确认，本模块用到的几条）

- **S1** 只增不改；默认期限仍是 540 秒，`DELEGATE_TIMEOUT_SECONDS` 仍只能缩短默认期限。
- **S9** `--timeout <秒>` 只能放大期限，范围 541～7200。超过 540 秒必须由调用方用宿主后台模式调用；delegate 不托管后台进程，没有 detach、status、cancel。主运行、收尾轮与阈值仍按 run-timeout 的同一套公式算。
- **S10（按 D2 修订）** 孤儿进程清理由 delegate 0.7.1 单独修（中止时回收 Codex 起的后代进程组、最后的 `wait()` 加上限、清理结果如实报告）。本模块以 0.7.1 为前提，不另行设计清理。用户原话：「D2 确认：孤儿清理先由 0.7.1 单独修，1.3 以它为前提。」

依赖：[run-timeout](run-timeout.md)（期限公式、时间预算段、收尾轮、兜底）、[run-result](run-result.md)（结果文件）、delegate 0.7.1 的清理修复（已合入 main `64d7ece`，channel 规格修订 S41）。

## 为什么必须以 0.7.1 为前提

实测 T5 与 T5b 根因排查（[记录](../docs/verification/2026-10-27-delegate-s38-probe.md)）发现两件事：

- Codex 执行的 shell 命令跑在新的会话和进程组里。delegate 中止 Codex 时，Codex 自己会退出，但不回收正在执行的命令，命令会成为孤儿继续运行。
- 有一次 `run_codex.py` 收到 SIGTERM 后 60 秒没有退出，根因没有定位，最可能卡在没有上限的最后一个 `wait()`。

期限越长，中止时恰好有长命令（测试、构建）在跑的概率越大。所以放开期限之前，清理必须先可靠。0.7.1 已修好前者（中止时冻结 Codex、快照后代、按进程组回收，换了会话的命令也在保证内），并给后者加了上限（直接子进程最多等 5 秒，回收不了退出 125；wrapper 被中断时最多等 15+2 秒）。「60 秒不退出」的真实根因仍未定位，但不会再无限挂住宿主。

## 影响面

- **run-resume A7（只放开一半）：** A7 原文「不做：后台守护进程……；改 540 秒期限……」修订为：默认期限仍是 540 秒，只有显式 `--timeout` 能放大；「delegate 不托管后台进程」保留。run-resume 规格在修订记录里加一条指向本模块，记录用户原话。
- **run-timeout T6（只增）：** 「总期限仍是 540 秒，`DELEGATE_TIMEOUT_SECONDS` 只能缩短」改为「未带 `--timeout` 时……」；带 `--timeout` 时 `T` 取该值。公式与常量不变。run-timeout 规格加一句指向本模块。
- **channel：** 「期限默认/上限 540 秒」改为「默认 540 秒；上限只能由 `--timeout` 放大到 7200 秒」，加一句指向本模块。
- **Bash 600 秒上限：** 由调用方负责。delegate 无法知道自己是不是在后台运行，所以不做检测；`run.md` 写明前台调用时 `--timeout` 不得超过宿主 Bash 的期限。

## 技术栈与命令

同 [run-result](run-result.md)；新增测试文件：

```bash
python3 -B plugins/delegate/tests/test-run-longrun.py
```

## 项目结构

```text
plugins/delegate/scripts/codex-exec.sh          → 解析 --timeout，算 T；其余流程不变
plugins/delegate/scripts/run_state.py           → deadlines 接受 541～7200 的 T（公式不变）
plugins/delegate/scripts/delegate_backend.py    → 解析并转发 --timeout，校验范围与组合
plugins/delegate/scripts/delegate_capabilities.py → codex 增加 longRun 能力事实
plugins/delegate/interface.json                 → run.longRun
plugins/delegate/commands/run.md / help.md      → 用法、后台调用要求
plugins/delegate/tests/test-run-longrun.py      → 新增：桩测试 + 假端点真机清理测试
plugins/delegate/tests/test-interface.py        → 加 run.longRun 断言
spec/run-longrun.md / docs/en/SPEC-run-longrun.md → 本合同
spec/run-resume.md、spec/run-timeout.md、spec/channel.md 及英文对应页 → 指向句与修订记录
README 中英文、待发行说明                         → 同步
```

## 行为合同

### 写法与校验

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --timeout <秒> [其他参数] -- "<任务>"
```

- 可用于普通 run、`--resumable`、`--resume`、`--continue`。每次调用各自给，不随链继承。
- 值必须是十进制整数，范围 541～7200，否则退出 64，stderr 为 `delegate: --timeout must be an integer between 541 and 7200`。
- 不带 `--timeout` 的行为与今天完全相同。

### 期限

- 带 `--timeout` 时 `T` 取该值，忽略 `DELEGATE_TIMEOUT_SECONDS`；不带时同今天。
- 照 run-timeout 的公式：`W = min(45, T // 6)`，`M = T − W`，`S = max(M − 90, M // 2)`。例如 `T = 1800` 时 `W = 45`、`M = 1755`、`S = 1665`。常量不变。
- 时间预算段、收尾轮、兜底、结束状态与退出码都与 run-timeout 相同，只是数字变大。
- 中止时的进程清理完全使用 0.7.1 的实现，本模块不改 `run_codex.py` 的清理逻辑。主运行与收尾轮仍各自经 `run_codex.py --report <runId>.cleanup <期限>` 调用，期限参数分别是 `M` 与 `W`。
- **墙钟上限：** 一次运行最多约 `T + 30` 秒。超出 `T` 的部分来自两次中止清理（每次最多约 13 秒：列进程最多 5 秒、宽限 2 秒、回收 5 秒、查残留 1 秒），以及 wrapper 的收尾。调用方给后台任务的等待上限应不小于这个数。
- **退出 125：** 长期限下中止后回收不了，同 0.7.1：退出 125，不输出结果行，结果文件状态为 `unreaped`（见 run-result）。

### 结果

- 结果文件增加 `"timeoutSeconds": <T>`；不带 `--timeout` 时为默认算出的 `T`（今天是 540），这样所有结果都能看出期限。
- 被中止时，`cleanup` 字段按 0.7.1 的报告填写（见 run-result）。
- 元数据块不变。

### 后台调用要求（写进 `run.md`）

- `--timeout` 大于宿主前台命令的期限时（Claude Code 的 Bash 前台上限为 600 秒），必须用宿主的后台模式调用，并等宿主的完成通知，不要轮询。
- delegate 不提供后台启动、查询、取消；要停下一次运行，就停止那个宿主后台任务，delegate 会按收到信号处理（退出 143／130／129，0.7.1 负责回收进程）。
- 结束后按 `delegate: result=<路径>` 读取结果文件。

### 接口（本模块的部分）

`run` 下新增：

```json
"longRun": {"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540,
            "background": "caller"}
```

`background: "caller"` 表示后台由调用方负责。使用方按 `>=1.3,<2.0` 且 `run.longRun` 存在来判断。

## 代码风格

同 [run-result](run-result.md)。

## 测试策略

- **桩测试（`test-run-longrun.py`）：**
  - 参数校验：540、7201、非整数、负数、空值都退出 64，且不调用 Codex；
  - `T` 的选取：带 `--timeout` 时忽略环境变量，不带时同今天；
  - `W`、`M`、`S` 进入提示词和 `run_codex.py` 的期限参数（用桩记录的实际 argv，不比对源码文本）；
  - `timeoutSeconds` 写进结果文件。
- **清理不另测长期限：** 0.7.1 没有、本模块也不加期限缩放钩子。清理行为与期限长短无关，由 0.7.1 的 `test-reap-fake-endpoint.py`（真实 Codex 连本机假端点）与 `test-channel-regressions.py` 覆盖，本模块只要求它们保持通过。本模块用桩断言 `--timeout` 算出的 `M`、`W` 原样进入 `run_codex.py --report … <期限>` 的参数，不跑真实的 541 秒以上等待。
- `test-interface.py` 加 `run.longRun` 断言。先写测试并确认红，再实现。

## 开发边界

- **Always：** 不带 `--timeout` 时与今天一致；清理只用 0.7.1 的实现；中英文合同同步。
- **Ask first：** 改范围上限 7200；带 `--timeout` 时改公式或常量；delegate 自己托管后台进程；付费实测、提交、推送、发版。
- **Never：** 放宽默认 540 秒；改动 0.7.1 的清理流程或常量；自己 fork 或 detach 进程。

## 成功条件与验证映射

- **RL-01：** 范围外与非整数的 `--timeout` 都退出 64 且不调用 Codex（桩测试）。
- **RL-02：** 带 `--timeout` 时 `T` 取该值，`W`、`M`、`S` 按公式进入提示词和期限参数；不带时与今天一致（桩测试）。
- **RL-03：** 结果文件含 `timeoutSeconds`；被中止时 `cleanup` 按 0.7.1 填写（桩测试）。
- **RL-04：** `--timeout` 算出的 `M`、`W` 进入 `run_codex.py --report <runId>.cleanup <期限>`；0.7.1 的回收回归（`test-reap-fake-endpoint.py`、`test-channel-regressions.py`）保持通过（桩测试 + 现有回归）。
- **RL-05：** `interface.json` 含 `run.longRun`；已有字段不变；两项 plugin validate 通过。
- **RL-06：** run-resume 修订记录（A7 只放开期限）、run-timeout 与 channel 的指向句、`run.md`、`help.md`、中英文 README、中英文合同和待发行说明同步，含后台调用要求。
- **RL-07：** 总验证、两项 plugin validate、`git diff --check` 通过。

## 开放问题

- 已按 0.7.1（`64d7ece`）核对：清理流程、`--report` 文件、退出 125、wrapper 的 15+2 秒上限与本规格一致；0.7.1 没有期限缩放钩子，长期限下的清理靠现有回归覆盖（见测试策略）。
- 7200 秒上限是按「一个 Task」估的，没有数据；以后按试点调整（Ask first）。
- 长期限下收尾轮的上下文更大，收尾耗时可能更久（run-timeout H3 仍未验证）；收尾轮期限仍是 45 秒，失败走兜底，不影响总期限。
