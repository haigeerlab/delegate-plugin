# 规格：run-continue（done 之后接着派下一个 Task）

<!-- spec-guard: review approved 339bdbf978f2 -->

简体中文 | [English](../docs/en/SPEC-run-continue.md)

2026-10-27 起草；用户 2026-10-27 批准，原话：「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」对应生态方案 S38 第 1 项与决定点 1，用户 2026-10-27 批准原话：「……done 后可续跑（只限 --resumable 链）……」（全文见 [run-result](run-result.md)）。用途：module-crew 的模块会话用同一个 Codex 会话依次做完一个模块的多个 Task，Task 之间由 Claude 核对、提交，不必每个 Task 都重新起会话、重新读一遍项目。

## 前提（2026-10-27 用户确认，本模块用到的几条）

- **S1** 只增不改；普通 run、`--resumable`、`--resume` 的现有行为不变。
- **S7** 写法 `--continue <runId> [--write] -- "<下一个 Task>"`：
  - 只接受 `--resumable` 起头的链上、状态为 `done` 的 runId；`needs-input`、`timeout` 仍走 `--resume`。
  - 其余同 `--resume`：同一仓库根目录，`--write` 与原运行一致，模型和推理档沿用，`.resumed` 占位保证一个 runId 只被接一次，每轮新 runId，`parent` 指向上一轮。
  - 提示词以【下一个任务】开头。
- **S8** 日志与答复仍保留最近 50 组；`.state.json`、`.resumed`、`.result.json` 改为最后一次写入后 14 天才删。

依赖：[run-resume](run-resume.md)（状态文件、占位、拒绝表）、[run-result](run-result.md)（结果文件、`kind`、`chainRoot`、用量差值）。

## 影响面

- **run-resume 合同（只增）：** 新增一条续跑入口。`--resume` 的语义、拒绝表、答复纪律都不变。run-resume 的 A7「续跑超时或失败的运行」不在本模块范围，`--continue` 只接 `done`。run-resume 规格加一句指向本模块。
- **一个 runId 只有一个后继：** `--resume` 与 `--continue` 共用 `<runId>.resumed` 占位，谁先占谁生效，链不会分叉。
- **清理规则：** 50 组规则不再删除状态文件、占位文件和结果文件，它们改按时间清理。run-resume「保留与清理」、run-timeout「保留与清理」、run-result「保留与清理」中「随日志一并删除状态文件」的部分由本模块取代，各加一句指向本模块。旧版本留下的状态文件照常可读。
- **interface：** 新增 `run.continue`，不改已有字段。

## 技术栈与命令

同 [run-result](run-result.md)；新增测试文件：

```bash
python3 -B plugins/delegate/tests/test-run-continue.py
```

## 项目结构

```text
plugins/delegate/scripts/codex-exec.sh          → --continue 分支（复用 --resume 的执行路径，换提示词与校验）
plugins/delegate/scripts/run_state.py           → check 增加 continue 模式；按时间清理的常量与实现
plugins/delegate/scripts/delegate_backend.py    → 解析并转发 --continue，校验组合
plugins/delegate/scripts/delegate_capabilities.py → codex 增加 continue 能力事实
plugins/delegate/interface.json                 → run.continue
plugins/delegate/commands/run.md / help.md      → 用法与纪律
plugins/delegate/tests/test-run-continue.py     → 新增：桩测试
plugins/delegate/tests/test-interface.py        → 加 run.continue 断言
spec/run-continue.md / docs/en/SPEC-run-continue.md → 本合同
spec/run-resume.md、spec/run-timeout.md、spec/run-result.md 及英文对应页 → 各加一句指向本模块
README 中英文、待发行说明                         → 同步
```

## 行为合同

### 写法

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --continue <runId> [--write] [--strict] -- "<下一个 Task>"
```

- 可以与其他 1.3 参数同用：`--strict`（run-result）、`--timeout`（run-longrun）、`--check`、`--authorized-by`（run-check）、`--rules-file`（run-rules）。
- 不能与 `--resumable`、`--resume`、`--model`、`--effort`、`--review-context`、`--backend claude-code` 同用；任务正文不能为空。违反时退出 64。

### 校验（不调用 Codex，退出 64，stderr 为 `delegate: <原因>`）

顺序与 `--resume` 相同，只把状态条件换掉：

| 原因 | 情形 |
|---|---|
| `invalid run id` | runId 格式不对 |
| `run not found` | 状态文件不存在（普通 run 没有状态文件，所以「只限 `--resumable` 起头的链」由这一条自然保证） |
| `run not resumable` | 状态文件里没有会话 ID |
| `run not done` | 状态不是 `done`（`needs-input`、`timeout` 请用 `--resume`；`unmarked` 不能接）。失败、中断、未能回收（125）的运行不写状态文件，按 `run not found` 拒绝 |
| `run already resumed` | 该 runId 已被 `--resume` 或 `--continue` 接过 |
| `repository mismatch` | 当前 Git 根目录与状态文件不同 |
| `write mode mismatch` | `--write` 有无与原运行不同 |

`--resume` 遇到状态为 `done` 的 runId，仍按 `run not waiting for input` 拒绝，文字不变；`--help` 和 `run.md` 提示改用 `--continue`。

### 执行

与续跑完全相同：`codex exec resume <会话ID>`，`-c sandbox_mode=…`，固定 `approval_policy="never"`，写模式加信任覆盖，`--json`（run-result），模型与推理档沿用状态文件，不传 `--ephemeral`；先排他创建 `<runId>.resumed` 再调 Codex。

发给 Codex 的内容（之后接时间预算段；带 `--strict` 时在时间预算段前加结束标记段；带 `--rules-file` 时规则段放在最前，见 run-rules）：

> 【下一个任务】<任务原文>
>
> 上一个任务已经结束。请在本会话里接着做这个新任务，沿用之前的约定：先做不受待定决策影响的部分；需要用户拍板时，最终答复第一行以 `NEED_USER:` 开头。

### 结果

- 新 runId，状态文件的 `parent` 指向被接的 runId，`chainRoot` 沿用，`kind` 为 `continue`。
- 结束判定与可续跑 run 相同（`done`／`needs-input`／`timeout`，`--strict` 时另有 `unmarked`），可以再被 `--continue` 或 `--resume` 接下去。
- 结果文件 `kind: "continue"`；`usage.run` 按 run-result 取与父轮的差值。
- 写模式照常输出 Git 验收块，基线在本轮启动前重新记录。

### 保留与清理

- 日志类文件（`.log`、`.answer`、`.events.jsonl`、`.wrapup`、`.wrapup.answer`、`.wrapup.events.jsonl`、`.baseline`、0.7.1 的 `.cleanup`，以及 run-check 的 `.check.log`、`.check.cleanup`）仍按「最近 50 组」删除。`.cleanup` 的清理结果已经抄进结果文件的 `cleanup` 字段，所以它随日志删掉不影响链。
- 状态类文件（`.state.json`、`.resumed`、`.result.json`）不随 50 组删除，改为修改时间早于 14 天时删除。14 天写成集中定义的常量，测试从同一处读取。
- 今天的清理代码在 `codex-exec.sh` 里内联（0.7.1 刚往后缀表里加了 `.cleanup`）；本模块把后缀表与 14 天常量挪进 `run_state.py` 集中定义，两类各一张表。
- 清理仍在每次运行结束时进行，失败不改变执行状态。
- **已知限制：** 被 50 组规则删掉日志的链，仍可以 `--continue`（只需要状态文件），但旧轮的过程日志查不到了。

### 接口（本模块的部分）

`run` 下新增：

```json
"continue": {"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable",
             "stateRetentionDays": 14}
```

使用方按 `>=1.3,<2.0` 且 `run.continue` 存在来判断。`accepts` 是开放集合，使用方只用自己认识的值。

## 答复与授权纪律（写进 `run.md`）

- `--continue` 的任务正文必须来自已批准的 Plan 里的 Task，或用户本人的要求；delegate 无法核实，这是命令指令层面的纪律。
- `--continue --write` 的前提与 `--resume --write` 相同：原运行已获得写入授权，且没有被收回。事先给好的写入授权见 [run-check](run-check.md) 的 `--authorized-by`。
- 上一轮的 `done` 不代表上一个 Task 已验收；核对、提交仍由调用方做，之后再派下一个 Task。

## 代码风格

同 [run-result](run-result.md)。

## 测试策略

`test-run-continue.py`（`unittest`，自带假 codex，临时 Git 夹具）覆盖：

- `--continue` 的 argv（`exec resume`、沙箱、`approval_policy`、`--json`、沿用模型与推理档、会话 ID）与提示词；
- 新 runId、`parent`、`chainRoot`、`kind`；
- 校验表每一行都退出 64 且不调 Codex，含 `run not done`；
- `--resume` 与 `--continue` 抢同一个 runId 时只有一个成功；
- 写模式的 Git 验收块；
- 清理：日志类（含 `.cleanup`）按 50 组删除，状态类按 14 天删除（用 `os.utime` 构造时间），超过 50 组后仍能 `--continue`。

`test-interface.py` 加 `run.continue` 断言。先写测试并确认红，再实现。

## 开发边界

- **Always：** `--resume` 的行为与文字不变；`--continue` 与 `--resume` 共用占位；中英文合同同步。
- **Ask first：** 接 `unmarked` 或失败的运行；允许 `--continue` 换模型或推理档；改 14 天保留期；付费实测、提交、推送、发版。
- **Never：** 接普通 run；让一条链分叉；替用户编写 Task 或回答问题；读取或删除 Codex 会话文件。

## 成功条件与验证映射

- **RC-01：** `--continue` 对 `done` 的 runId 调用 `codex exec resume`，参数与续跑一致，提示词为【下一个任务】版本（桩测试）。
- **RC-02：** 新 runId、`parent`、`chainRoot`、`kind: "continue"` 正确，结果文件 `usage.run` 为差值（桩测试）。
- **RC-03：** 校验表每一行退出 64 且不调用 Codex（桩测试）。
- **RC-04：** `--resume` 与 `--continue` 共用占位，同一 runId 只能被接一次（桩测试）。
- **RC-05：** 写模式输出 Git 验收块（桩测试）。
- **RC-06：** 状态类文件按 14 天清理，日志类按 50 组清理；日志被清理后仍能 `--continue`（桩测试）。
- **RC-07：** `interface.json` 含 `run.continue`；已有字段不变；两项 plugin validate 通过。
- **RC-08：** `run.md`、`help.md`、中英文 README、中英文合同、指向句和待发行说明同步，含纪律三条。
- **RC-09：** 总验证、两项 plugin validate、`git diff --check` 通过。

## 开放问题

- 长链的上下文压缩：实测 T2 表明 Codex 约在窗口 94% 时自动压缩、对调用方透明，本模块不管上下文；按 D1（见 run-result），1.3 不读会话文件，压缩在 1.3 里观测不到。
- 14 天是否够用：按一个模块的典型周期估计，没有数据；以后按 module-crew 试点调整（Ask first）。
