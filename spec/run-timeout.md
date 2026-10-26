# 规格：run-timeout（超时保留进度、超时可续跑）

<!-- spec-guard: review approved 9bbc7d54a239 -->

简体中文 | [English](../docs/en/SPEC-run-timeout.md)

2026-10-26 起草。起因是生态方案 S35：`/delegate:run` 单次上限 540 秒，超时退出 124 时只有 Git 验收块，没有最终答复、没有 run_id 结果行、不能续跑，改到一半的文件留在工作区。ecosystem-lead 受理原话：「S35 受理：先实测两个没验证的假设（中止后还能不能 resume、到期前能不能提示收尾），结果报你，再写 Spec 给我审；接口 1.2 只增不改。」实测结论见 [S35 实测记录](../docs/verification/2026-10-26-delegate-s35-timeout-probe.md)。ecosystem-lead 确认实测结论后，经 delegate-owner 转来本规格须写清的要求：去掉 `--ephemeral` 是行为变化，要写进影响面；两道收尾叠加；收尾轮有硬期限，并有不靠模型的兜底；接口 1.2 只增不改，写清结果行与退出码；未验证项列为假设；修 killpg EPERM；trust_level 另立 S36，不并入。

使用方是 module-crew 的 `crew-codex-offload`（项目开关 `codexOffload`），它总是带 `--resumable` 调用 run。它对三种结束状态分别处理：`done`、`needs-input` 各按原约定；`timeout` 不代提交，先把进度交给用户，续跑要用户点头；认不出的状态一律停下问用户。

## 前提（2026-10-26 用户确认）

用户对 T1–T12 答「继续」。T2、T3 列出方案 A（所有 run 都可续跑）与方案 B（折中）后，用户原话：「选方案 B：普通 run 保留 --ephemeral，只加时间预算和兜底；同意为此修订 run-resume 的 Always 规则。」ecosystem-lead 经 delegate-owner 转达，认可 T7、T8、T9、T10，并补充了要求，已写进对应条款（转达不算用户批准）。

- **T1** 新模块 `run-timeout`，依赖 channel、integration-interface、run-resume。这三者的已有条款中，被本模块取代的，逐条在各自规格里加一句指向本模块（见「影响面」），其余不改。
- **T2** 普通 run（未带 `--resumable`）照旧传 `--ephemeral`，参数不变；可续跑 run 与续跑本来就不传，也不变。review 不在范围内。
- **T3** 每次 run（普通与可续跑）与每一轮续跑，提示词都加一段时间预算，这是第一道收尾。模型按预算主动停下时，最终答复第一行以 `TIME_UP:` 开头。
- **T4** 可续跑 run 或续跑被强制中止后，若取得会话 ID，就以只读沙箱续跑一轮收尾轮，这是第二道收尾。这一轮只写进度、不执行命令，有自己的硬期限。普通 run 没有会话可续，不走收尾轮。
- **T5** 普通 run 被强制中止，或收尾轮超时、失败、答复为空，或取不到会话 ID 时，输出固定的兜底文字，不调用模型。写模式下附上改了哪些文件。
- **T6** 总期限仍是 540 秒，`DELEGATE_TIMEOUT_SECONDS` 只能缩短。期限这样分配：
  - 收尾轮期限 `W = min(45, T // 6)`；
  - 主运行期限 `M = T − W`；
  - 提示词里「不再开新步骤」的阈值 `S = max(M − 90, M // 2)`。

  T=540 时 W=45、M=495、S=405。普通 run 也按 M 中止，以便和可续跑 run 共用同一套阈值；中止后剩下的时间只用于兜底与清理。这些数字写成代码里集中定义的配置常量，提示词只填算出来的值，不写死数字；落地时在付费验证里校准（ecosystem-lead 的要求）。
- **T7** 结束状态新增 `timeout`：模型主动写 `TIME_UP:`、被强制中止，这两种情形都算，退出码一律 124。
- **T8** `status=timeout` 时，stdout 照常输出答复（进度说明或兜底文字）、元数据和结果行。升级说明须写明：判断成功要先看退出码为 0，再看 `status=done`；有结果行不等于成功。
- **T9** `--resume` 新增接受状态为 `timeout` 的 runId，其余拒绝规则不变。普通 run 不写状态文件，它的 runId 照旧按 `run not found` 拒绝。
- **T10** `interface.json` 升到 `1.2`：`run.resume.statuses` 追加 `"timeout"`，新增 `run.timeout`。任何已有字段都不删除，含义也不改，主版本不变。前提是写明 `statuses` 是开放集合：使用方遇到不认识的值，要停下或者当失败处理，不能当成完成。目前读 run 的使用方只有 module-crew；spec-guard、decision-inbox 不读 run。
- **T11** `run_codex.py` 的 killpg EPERM 竞态在本模块修复。
- **T12** 不做：
  - S36（`--write` 时 Codex 把仓库信任写进用户配置）；
  - review 超时；
  - claude-code 后端；
  - 改 540 秒总期限；
  - 自动续跑（续跑由使用方在用户同意后发起）；
  - 普通 run 超时后续跑。

### 未验证、落地时补测的假设

下面几条来自实测记录里的「未验证」项。本规格按它们成立来设计，Plan 里把它们列为付费 gate，单独授权；有不成立的，就回到本规格修订。2026-10-26 Checkpoint 3 的实测结果写在各条后面，详见 [Checkpoint 3 记录](../docs/verification/2026-10-26-delegate-run-timeout-cp3.md)。

- **H1** 真实 540 秒期限下，模型能按 T6 的阈值守时，余量与等比缩小时的实测相当。缩小实测里，余量是 1.1–3.2 秒；从越过阈值到退出约 17–19 秒。
- **H1** 实测结果：成立。真实 540 秒期限下，模型在 412 秒主动停下，总耗时 422 秒，比 M 早 73 秒。
- **H2（修订 R1）** 收尾轮多数在 10–15 秒返回，但服务端长尾不罕见：两次实测共 8 个样本，2 个超过 45 秒（185 秒、超过 45 秒被中止）。长尾时由 T4 的硬期限中止收尾轮、T5 的兜底输出固定文字，总时长不超限，只是拿不到模型写的进度。常数不变。
- **H3（修订 R1，仍未验证）** 在被强制中止、上下文较大的会话上，收尾轮耗时仍在 W 之内。Checkpoint 3 没能构造出大上下文：Codex 会截断大的命令输出，会话上下文停在约 3.2 万 token，在这个规模下收尾轮约 12–15 秒。十几万 token 的会话没有测，保留为假设。
- **H4** 本机默认模型以外的模型与推理档，同样遵守时间预算和 `TIME_UP:` 标记。实测只覆盖了 `gpt-6.1-sol` 的 `none` 与 `high` 两档。
- **H4** 实测结果：成立（1 个模型）。`gpt-5.6-terra` 在 72 秒主动停下（阈值 50 秒、期限 100 秒）。
- **H5** 写模式超时后续跑，不会重复已经完成的写入。实测在提示「先看文件确认进度」时成立；写到一半的文件没有测。Checkpoint 3 实测：续跑提示里没有「先看文件」时同样成立。
- **新发现（修订 R1）** 长命令运行期间，Codex 会先把控制权交回模型，模型能运行 `date +%s` 查看用时并按预算停下；用 `sleep 300` 刻意拖延的两次都没有触发强制中止。S35 前置实测里「单条长命令时第一道收尾拦不住」的推断不成立。强制中止主要来自服务端长尾（实测有一次主运行首轮约 145 秒无响应），这时收尾轮常常也会卡住，所以收尾轮的期限不随长尾加大。
- **修订记录 R1（2026-10-26，用户原话：「选 A：常数不变，只修订规格 H2、H3 的措辞并记录新发现。」）**：H2、H3 改为上述措辞，补上新发现与各条实测结果；同时按实现补正两处文字（保留清理列表补 `.baseline`；测试用自带假 codex、不改 `stub-codex`）。T6 常数与其余条款不变。

## 影响面

- **普通 run 的提示词多一段时间预算（修订已批准规则）：** run-resume 的 Always 规则原为「普通 run 与改动前逐字节一致」，由用户 2026-10-26 同意修订为「普通 run 除时间预算段外与改动前一致」。RR-01 中「提示词不变」一项由本模块取代；参数（含 `--ephemeral`）不变。
- **普通 run 实际只跑 `M` 秒：** channel「期限默认/上限 540 秒」不变，但 Codex 主运行最多跑 `M` 秒（总期限 540 时为 495 秒），剩下的时间留给收尾轮或兜底。
- **超时输出：** 原来的写法是超时退出 124、不输出结果行。run-resume A3「超时……不输出该行」与 channel「超时退出 124」中关于输出的部分，由本模块取代：超时现在输出答复与结果行，退出码仍是 124。
- **结果行不等于成功：** 超时现在也有结果行。使用方判断成功，要先看退出码为 0，再看 `status=done`。这一点写进 README 与待发行说明的升级提示。
- **续跑拒绝表：** run-resume 中 `run not waiting for input` 的触发条件，由「状态不是 `needs-input`」改为「状态既不是 `needs-input` 也不是 `timeout`」。
- **使用方：** 读到 `1.1` 的使用方在超时时仍会看到退出码 124，可以按失败处理，不会误当成完成。只有按 `>=1.2,<2.0` 判断的使用方，才使用 `timeout` 状态与续跑。
- **不变：** 普通 run 不在本机留会话文件，和今天一样；可续跑 run 的会话留存方式也和今天一样。

## 技术栈与命令

Bash 3.2 wrapper、Python 3 标准库、Git、Codex CLI（本机实测 0.162.1）。不新增依赖、hook 或命令入口。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-run-timeout.py
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-interface.py
/bin/bash plugins/delegate/tests/test-channel.sh
python3 -B plugins/delegate/tests/test-channel-regressions.py
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/codex-exec.sh        → 时间预算段、期限分配、收尾轮、兜底与文件清单、timeout 输出
plugins/delegate/scripts/run_codex.py         → stop_group 同时容忍 PermissionError（EPERM）
plugins/delegate/scripts/run_state.py         → TIME_UP 判定、期限常量与计算、timeout 状态写入、续跑接受 timeout
plugins/delegate/interface.json               → interface 1.2：statuses 追加 timeout，新增 run.timeout
plugins/delegate/commands/run.md / help.md    → 超时输出、续跑、判断成功的方法
plugins/delegate/tests/test-run-timeout.py    → 新增：桩测试
plugins/delegate/tests/test-run-resume.py     → 只调整影响面列出的断言
plugins/delegate/tests/test-interface.py      → 1.2 断言
plugins/delegate/tests/test-channel.sh / test-channel-regressions.py → 普通 run 提示词、EPERM 回归
spec/run-timeout.md / docs/en/SPEC-run-timeout.md → 本合同
spec/channel.md、spec/run-resume.md、spec/integration-interface.md 及英文对应页 → 指向本模块的句子；run-resume 的 Always 规则按影响面修订
spec/CAPABILITY-MAP.md / docs/en/capability-map.md → 新模块行
plugins/delegate/README.md / README.en.md、docs/releases/unreleased.md 及英文对应页 → 用法、开放集合说明与升级提示
```

## 行为合同

### 期限常量与分配

`T` 为现有逻辑得到的总期限：默认和上限都是 540，`DELEGATE_TIMEOUT_SECONDS` 只能缩短。

- **常量：** 收尾轮上限 45、除数 6、阈值余量 90、除数 2，集中定义为一处配置常量，测试从同一处读取。
- **算式：** `W = min(45, T // 6)`，`M = T − W`，`S = max(M − 90, M // 2)`。
- **用法：** 主运行交给 `run_codex.py` 的期限是 `M`；收尾轮的期限是 `W`。主运行、收尾轮加上进程清理，仍在 Bash 600 秒上限内。

### 时间预算段（第一道）

每次 run 与每一轮续跑，都在现有提示词末尾（任务正文或用户答复之后）追加下面这段。`<T0>` 为启动 Codex 前一刻的 epoch 秒，`<M>`、`<S>` 为算出的值：

> 【时间预算】本次运行开始于 epoch 秒 <T0>，<M> 秒后会被强制中止，中止时不保留未写出的答复。需要判断用时就运行 `date +%s`。已用时达到 <S> 秒后，不要再开始新的步骤，也不要启动预计会跨过期限的长命令，立即给出最终答复：第一行以 `TIME_UP:` 开头，后面写已完成的进度、做到一半的步骤（如有）、下一步应从哪里开始。

**判定：** 答复去掉开头空白后，以 `TIME_UP:` 开头的判为 `timeout`。其余情况：
- 可续跑 run 与续跑：沿用 run-resume 的 `NEED_USER:` / `done` 判定；
- 普通 run：判为 `done`。

### 收尾轮（第二道，仅可续跑 run 与续跑）

可续跑 run 或续跑的主运行退出码为 124（被强制中止）时，按下面四步处理：

1. 从过程日志取会话 ID（沿用 `session_id_from_log`）。取不到就跳到兜底。
2. 以 `codex exec resume <会话ID>` 续跑一轮，参数与续跑相同，有三处差别：
   - 沙箱**固定**为 `-c sandbox_mode="read-only"`，写模式也一样；
   - 期限为 `W`；
   - 日志写到 `<runId>.wrapup`，答复写到 `<runId>.wrapup.answer`。

   提示词：

   > 【收尾】本次运行已到期被中止。不要再执行任何命令，也不要继续做任务。只写进度：第一行以 `TIME_UP:` 开头，后面写已完成的步骤及结果、做到一半的步骤（如有）、下一步应从哪里开始。

3. 收尾轮退出 0 且答复非空：以它的答复作为本次答复。不管首行有没有 `TIME_UP:`，本次状态都是 `timeout`。
4. 其他情况一律走兜底。

普通 run 的主运行退出码为 124 时，不走收尾轮，直接走兜底。

### 兜底（不靠模型）

答复为下面的固定文字：

```text
delegate: 已中止，未取得进度说明（<原因>）。会话 ID：<uuid|无>；可续跑：<是|否>。
<文件清单>
```

`<原因>` 取以下之一：
- 「普通 run 不保留会话」
- 「收尾轮超时」
- 「收尾轮失败（退出 N）」
- 「收尾轮答复为空」
- 「未取得会话 ID」

`<文件清单>` 分两种情况：
- **写模式：** 先写一行「改动的文件（与运行前比较）：」，下面列出 `git status --porcelain` 中，与运行前基线相比新出现或内容不同的条目，每行一条；没有就写「无」。为此，写模式在运行前要多记录一份完整的 porcelain 快照（今天只记数量）。
- **只读模式：** 写「只读运行，不列文件」。

**已知限制：** 文件在运行前已经修改、运行中又被改动时，porcelain 行不变，清单列不出来。完整变化以 Git 验收块的 `git diff --stat` 为准。

### 结束状态、输出与退出码

| 情形 | status | 退出码 | stdout |
|---|---|---|---|
| 正常完成 | `done` | 0 | 同今天 |
| 首行 `NEED_USER:`（可续跑 run 与续跑） | `needs-input` | 0 | 同今天 |
| 首行 `TIME_UP:`（模型主动停） | `timeout` | 124 | 答复、元数据、结果行 |
| 可续跑 run／续跑被强制中止 | `timeout` | 124 | 收尾轮答复或兜底文字、元数据、结果行 |
| 普通 run 被强制中止 | `timeout` | 124 | 兜底文字、元数据、结果行 |
| 失败、信号中断（143/130/129）、空答复 | — | 不变 | 不变，不输出结果行 |

- **元数据块：** 同今天，另加一行 `收尾：<主动停|收尾轮|兜底（原因）>`。
- **结果行：** `delegate: run_id=<id> status=timeout resumable=<true|false>`，仍是 stdout 最后一行。`resumable=true` 当且仅当同时满足三条：是可续跑 run 或续跑、取得了会话 ID、状态文件写入成功。普通 run 一律为 `resumable=false`。
- **Git 验收块：** 写模式照常输出（退出码非 0 时按现有规则写到 stderr），工作区不回滚。
- **stderr：** 被强制中止时，另输出一行 `delegate: codex 超过 <M> 秒被中止。完整过程日志：<log>`；模型主动停时不输出这一行。

### 状态文件

只有可续跑 run 与续跑写状态文件（同今天），`status` 可取 `timeout`。收尾轮在同一个会话里进行，不改变 `sessionId`。

### 续跑

- `--resume <runId>` 接受状态为 `needs-input` 或 `timeout` 的 runId。占位、仓库、写模式一致性等其余拒绝规则不变。
- 从 `timeout` 续跑时，发给 Codex 的内容与 run-resume 的续跑相同（`【用户答复】…`），末尾加时间预算段。这一轮按 run-resume 的可续跑约定判定，也可能再次以 `timeout` 结束。
- 写模式超时后的续跑须带 `--write`，与原运行一致。delegate 不替用户决定是否续跑。

### 保留与清理

保留最近 50 组日志的规则不变。删除一组时，一并删除同 runId 的 `.answer`、`.state.json`、`.resumed`、`.wrapup`、`.wrapup.answer`、`.baseline`（写模式的运行前快照）。仍不读、不删 Codex 会话文件。

### killpg EPERM

`run_codex.py` 的 `stop_group` 对两次 `os.killpg` 都同时容忍 `ProcessLookupError` 与 `PermissionError`，之后照常 `process.wait()`；macOS 上进程组只剩僵尸进程时会返回 EPERM。退出码不受影响。

### 接口 1.2

```json
{
  "interface": "1.2",
  "review": {"command": "/delegate:review", "backends": ["codex", "claude-code"], "readOnly": true,
             "report": {"schemaVersion": 1}},
  "run": {
    "command": "/delegate:run", "backends": ["codex"], "write": "explicit",
    "resume": {"optIn": "--resumable", "option": "--resume", "backends": ["codex"],
               "statuses": ["done", "needs-input", "timeout"]},
    "timeout": {"status": "timeout", "exitCode": 124}
  },
  "doctor": {"command": "/delegate:doctor"}
}
```

使用方按 `>=1.2,<2.0` 判断后才使用 `timeout`。读到 `1.1`，或者没有 `run.timeout` 字段，就按今天处理：124 视为失败，不续跑。

`statuses` 是开放集合，以后的小版本可能追加新值。使用方遇到不认识的值，必须停下或当失败处理，不能当成完成。JSON 里不能写注释，这条说明写在三处：README 的「对外接口」一节、`spec/integration-interface.md` 的指向句，以及它们的英文对应页。

## 代码风格

保持已有风格：
- Bash 兼容 3.2，变量写 `${VAR}`，空数组展开沿用已有守卫；
- Python 用标准库、4 空格缩进、snake_case；
- shell 里不解析 JSON，也不算期限，交给 `run_state.py`。

现有写法示例（`run_codex.py`）：

```python
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
```

## 测试策略

`test-run-timeout.py` 用标准库 `unittest`、自带的假 codex（与 `test-run-resume.py` 的做法相同，不改共用的 `stub-codex`）和临时 Git 夹具，并把 `DELEGATE_TIMEOUT_SECONDS` 缩短到几秒。桩要能区分首轮与续跑（例如续跑时读 `STUB_RESUME_ANSWER`、`STUB_RESUME_SLEEP_SECONDS`），并能在日志里输出 `session id:` 行。覆盖下面这些情形：

- 普通 run 仍传 `--ephemeral`，其余参数不变；可续跑 run 与续跑仍不传；
- 所有 run 与续跑的提示词都含时间预算段，`<M>`、`<S>` 由常量和 `DELEGATE_TIMEOUT_SECONDS` 算出；
- 首行 `TIME_UP:` → `status=timeout`、退出 124、stdout 含答复与结果行，不调用收尾轮；普通 run 与可续跑 run 各测一次；
- 可续跑 run 超时 → 调用一次收尾轮，参数为 `exec resume`、只读沙箱（写模式也一样）、同一会话 ID、收尾提示词；收尾轮成功时输出它的答复，`resumable=true`；
- 收尾轮超时、失败、答复为空、取不到会话 ID → 兜底文字，原因与 `resumable` 正确；
- 普通 run 超时 → 不调用收尾轮，兜底原因为「普通 run 不保留会话」，`resumable=false`；
- 写模式超时：兜底文字附改动文件清单（基线前已有的修改不列），Git 验收块照常输出；只读模式写「只读运行，不列文件」；
- 可续跑 run 超时写状态文件；`--resume` 接受 `timeout`，仍拒绝 `done`；普通 run 超时的 runId 被拒（`run not found`）；
- 清理时同时删除 `.wrapup`、`.wrapup.answer`；
- 信号中断（143）不触发收尾轮，也不输出结果行；
- 总耗时不超过 `T` 加清理余量；
- `os.killpg` 抛 `PermissionError` 时，`run_codex.py` 不崩溃，返回原退出码（用注入或模拟的方式）。

`test-interface.py` 断言：
- `interface == "1.2"`；
- `run.resume.statuses == ["done", "needs-input", "timeout"]`；
- `run.timeout == {"status": "timeout", "exitCode": 124}`；
- 两个 command 字段不变。

现有测试只调整影响面列出的断言：普通 run 的提示词多了时间预算段、超时行为、拒绝条件。每处改动在 Plan 中逐条列明，其余断言不改。

先写测试，确认它是红的，再实现。桩测试只证明参数与流程，不能证明真实模型的行为。

**付费实测（gate，单独授权）：** H1–H5 在落地时补测，具体次数、模型与预计耗时在 Plan 的 gate 里列出。没授权就标「未验证」。

## 开发边界

- **Always：**
  - 超时时输出结果行和能拿到的进度；
  - 收尾轮固定只读，兜底不调用模型；
  - 总时长在 Bash 600 秒以内；
  - 中英文合同同步；
  - `interface.json`、能力事实和测试一起改。
- **Ask first：**
  - 改 540 秒总期限或 T6 的公式；
  - 让 delegate 自动续跑；
  - 让普通 run 也能续跑（即方案 A）；
  - 在 review 上加同样机制；
  - 付费实测、提交、推送、发版。
- **Never：**
  - 删除 `interface.json` 的已有字段、改变其含义，或升主版本；
  - 收尾轮用写沙箱，或允许它执行命令；
  - 把 `timeout` 报成 `done` 或退出 0；
  - 改变普通 run 的参数；
  - 读取或删除 Codex 会话文件；
  - 替用户决定是否续跑；
  - 在本模块处理 S36。

## 成功条件与验证映射

- **RT-01：** 普通 run 仍传 `--ephemeral`，参数不变；可续跑 run 与续跑的参数不变（桩测试）。
- **RT-02：** 所有 run 与续跑的提示词都含时间预算段，`T0`、`M`、`S` 正确，数字来自集中常量（桩测试）。
- **RT-03：** 首行 `TIME_UP:` 判为 `timeout`、退出 124，输出答复、元数据与结果行，不调用收尾轮（桩测试）。
- **RT-04：** 可续跑 run 或续跑被强制中止后，调用一次只读收尾轮，参数与提示词正确；成功时输出它的答复（桩测试）。
- **RT-05：** 普通 run 被强制中止，或收尾轮超时、失败、答复为空、取不到会话 ID 时，输出兜底文字，原因与 `resumable` 正确（桩测试）。
- **RT-06：** 写模式兜底附改动文件清单，Git 验收块照常输出，不回滚（桩测试）。
- **RT-07：** 总耗时不超过 `T` 加清理余量（桩测试，缩短期限）。
- **RT-08：** 可续跑 run 超时写状态文件；`--resume` 接受 `timeout`，拒绝 `done` 和普通 run 的 runId；清理覆盖新文件（桩测试）。
- **RT-09：** 信号中断、失败、空答复的行为不变（桩测试，用现有断言）。
- **RT-10：** `run_codex.py` 容忍 EPERM（回归测试）。
- **RT-11：** `interface.json` 为 1.2，字段如上；两项 plugin validate 通过。
- **RT-12：** `run.md`、`help.md`、中英文 README、中英文合同、指向句、run-resume 的 Always 规则修订和待发行说明同步，包含开放集合说明和「先看退出码」的升级提示。
- **RT-13：** 总验证、两项 plugin validate、`git diff --check` 全部通过。
- **RT-14（付费，gate）：** H1–H5 实测，结果记入验证记录；有不成立的，回到本规格。

## 开放问题

- T6 的几个常数（45、÷6、90、÷2）经 Checkpoint 3 实测按 R1 保持不变；H3 补测或长尾样本增多后可再评估。
- 模型漏写 `TIME_UP:`、在阈值之后仍做完全部任务并正常结束时，判为 `done`，这个结果是对的。但如果漏写标记、又只做了一部分，就会被误判为 `done`。这与 run-resume A5 是同一类已知限制。
