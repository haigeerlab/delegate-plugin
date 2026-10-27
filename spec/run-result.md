# 规格：run-result（结构化结果文件、`--strict` 与成本数据）

<!-- spec-guard: review approved 43d83f5ab434 -->

简体中文 | [English](../docs/en/SPEC-run-result.md)

2026-10-27 起草；用户 2026-10-27 批准，原话：「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」起因是生态方案 S38（模块整体外包给 Codex），用户 2026-10-27 批准，原话：「S38 接口方案：假设全部确认，五个决定点按推荐批准——done 后可续跑（只限 --resumable 链）；A7 只放开期限、用 --timeout 轻方案；写入授权按有条件折中；1.3 一次到齐必须五项，1.4 做回滚与并发额度，第 10 项暂缓；授权 delegate-owner 先做 T1～T5 付费实测再写 Spec。」本模块对应方案第 3 项（结构化结果）与第 8 项（成本数据），是 1.3 五个模块里的第一个：其余四个（[run-continue](run-continue.md)、[run-longrun](run-longrun.md)、[run-check](run-check.md)、[run-rules](run-rules.md)）都往本模块的结果文件里加字段。

做法依据 [S38 前置实测](../docs/verification/2026-10-27-delegate-s38-probe.md)（T1：`--json` 事件字段；T2：token 是会话累计值）。

## 前提（2026-10-27 用户确认 S1～S15，本模块用到的几条）

用户原话：「D2 确认：孤儿清理先由 0.7.1 单独修，1.3 以它为前提。5 个模块拆分和 S1～S15 假设（S10 按 0.7.1 改）全部确认，开始插能力图并写 Spec。」

- **S1** 1.3 只增不改：`run.write: "explicit"`、普通 run 保留 `--ephemeral`、540 秒默认期限、已有退出码、现有结果行都不变；结果行仍是 stdout 最后一行。新能力要显式加参数才生效，只有 S3、S4 两处对所有 run 生效。
- **S2** 本模块把 `interface` 升到 `1.3`，其余四个模块各自加能力标记；五个模块全部完成前不发版。
- **S3** 所有 run 路径调用 Codex 时都加 `--json`。
- **S4** 所有 run 都写结果文件，stdout 在结果行之前多一行 `delegate: result=<路径>`。
- **S5** 结果文件的字段见下文；token 记「本次」与「整个会话」两项，本次 = 本次累计 − 父 run 累计，不沿 parent 链累加。
- **S6** `--strict`：首行必须是结束标记，缺了判 `unmarked`、退出 1。
- **S14** 验证分三层：桩测试；本机假 Responses 端点驱动真实 Codex 的免费测试；一次付费实测（gate，单独授权）。
- **S15** 写 Spec、Plan 这一轮只改 `spec/`、`tasks/`、`docs/`，不改产品代码，不调用模型，不提交。

## 已定的决定点

### D1：1.3 不读 Codex 自己的会话文件（已定）

用户 2026-10-27 在本会话选定，原话：「D1 选 A：1.3 不读 Codex 会话文件，额度读取留给 1.4 的 doctor.quota。」

实测（T1、T2）表明：上下文占用（`last_token_usage.input_tokens` 与 `model_context_window`）、上下文压缩（`type: "compacted"` 记录）、额度与限流（`rate_limits`）只在 Codex 的会话文件里，`--json` 事件流里没有。按 D1：

- 结果文件只用 `--json` 事件流和 delegate 自己的计时；上下文占用、压缩、额度一律不出现。
- run-resume 的 Never 规则「读取或删除 Codex 会话文件」不变。
- 额度读取留给 1.4 的 `doctor.quota` 一并设计；module-crew 在 1.3 里看不到上下文快满或快限流的信号。

当时的另一个选项（只读、只取列明字段，并修订 run-resume 的 Never 规则）没有采用。

### D2：孤儿进程清理放在哪（已定）

用户 2026-10-27 在本会话确认（原话见上「前提」）：孤儿清理先由 delegate 0.7.1 单独修，1.3 以 0.7.1 为前提。0.7.1 已合入 main 并发版（`64d7ece`，标签 `v0.7.1`，channel 规格修订 S41）。本模块以它的实际实现为准：

- 中止（到期或 TERM/INT/HUP）时，`run_codex.py` 冻结 Codex、快照后代、按进程组回收，直接子进程最多等 5 秒；回收不了时报告 `delegate: 执行进程未能回收，PID=<pid>` 并**退出 125**，wrapper 按普通执行失败处理，不输出结果行。
- 清理报告写进 `<runId>.cleanup`，并由 wrapper 转发到 stderr；`.cleanup` 已在 50 组保留规则里。
- `codex-exec.sh` 被中断时对执行进程 TERM，最多等 15 秒，再 KILL 并最多等 2 秒，强制结束时另报一行。

本模块把这些写进结果文件（`status: "unreaped"`、`cleanup` 字段），不改清理流程本身。

## 影响面

- **过程日志变成两个文件：** 今天 Codex 的 stdout 和 stderr 都写进 `<runId>.log`。改用 `--json` 后，事件流写到 `<runId>.events.jsonl`，stderr 仍写 `<runId>.log`。失败时打印的「过程日志末尾」现在来自 stderr 文件，下面再追加最多 10 条渲染过的事件（见「失败诊断」）。升级说明要写明这一点：读日志文本的人和脚本会看到不同内容。日志不是对外合同，接口不受影响。
- **会话 ID 的来源：** 开 `--json` 后，日志里不再有 `session id: <uuid>` 这一行，改从事件流第一条 `thread.started` 的 `thread_id` 取。run-resume「会话 ID 取自过程日志里第一行 `session id: <uuid>`」与 run-timeout 收尾轮「沿用 `session_id_from_log`」由本模块取代，各加一句指向本模块。
- **stdout 多一行：** 成功、`needs-input`、`timeout`、`unmarked` 时，结果行之前多一行 `delegate: result=<路径>`。结果行格式和位置不变。
- **新状态 `unmarked`：** 只在显式 `--strict` 时出现。1.2 已写明状态是开放集合，旧使用方遇到不认识的状态要当失败处理；它的退出码也是 1。
- **收尾轮：** 也加 `--json`，事件写到 `<runId>.wrapup.events.jsonl`。
- **`run_codex.py` 的输出：** 0.7.1 起它把清理报告写到自己的 stderr 和 `--report` 文件。拆分后，它的 stderr 与 Codex 的 stderr 一起进 `<runId>.log`；事件文件只接 Codex 的 stdout。
- **review 不在范围内**：Codex 后端 review 不加 `--json`、不写结果文件。

## 技术栈与命令

Bash 3.2 wrapper、Python 3 标准库、Git、Codex CLI 0.162.1（实测版本）。不新增依赖、hook 或命令入口。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-run-result.py
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-run-timeout.py
python3 -B plugins/delegate/tests/test-interface.py
/bin/bash plugins/delegate/tests/test-channel.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/codex-exec.sh          → 加 --json 与 --strict，分开事件流与 stderr，写结果文件，多打印 result 行
plugins/delegate/scripts/run_events.py          → 新增：解析事件流（thread_id、命令与退出码、turn.completed 用量、最后一条答复）
plugins/delegate/scripts/run_state.py           → 会话 ID 改从事件流取；状态文件加 usageTotal；判定加 DONE: 与 unmarked；结果文件写入
plugins/delegate/scripts/delegate_backend.py    → 解析并转发 --strict
plugins/delegate/scripts/delegate_capabilities.py → codex 增加 result 能力事实
plugins/delegate/interface.json                 → interface 1.3，run.result、run.usage
plugins/delegate/commands/run.md / help.md      → 结果文件、--strict、升级提示
plugins/delegate/tests/test-run-result.py       → 新增：桩测试
plugins/delegate/tests/fake-responses.py        → 新增：从 test-reap-fake-endpoint.py 抽出的本机假 Responses 端点，加「回答复」模式
plugins/delegate/tests/test-reap-fake-endpoint.py → 改为引用共用假端点，断言不变
plugins/delegate/tests/test-interface.py        → 加 1.3 断言
plugins/delegate/README.md / README.en.md       → 结果文件一节，对外接口补 1.3
spec/run-result.md / docs/en/SPEC-run-result.md → 本合同
spec/run-resume.md、spec/run-timeout.md、spec/channel.md 及英文对应页 → 各加一句指向本模块
docs/releases/unreleased.md 及英文对应页        → 待发行说明
```

## 行为合同

### Codex 调用

普通 run、可续跑 run、续跑、收尾轮，在现有参数之后、`-o` 之前都多一项 `--json`。其余参数不变（含普通 run 的 `--ephemeral`、`approval_policy="never"`、信任覆盖、stdin=/dev/null）。重定向改为：

```bash
python3 -B run_codex.py --report "${CLEANUP}" "${MAIN_SECONDS}" env … codex "${CODEX_ARGS[@]}" \
  >"${TMP_ROOT}/${RUN_ID}.events.jsonl" 2>"${LOG}" </dev/null
```

最终答复仍以 `-o` 文件为准（实测 T1：与最后一条 `agent_message.text` 逐字一致）。

### 事件解析（`run_events.py`）

逐行读事件文件，非 JSON 行跳过，不报错：

| 取什么 | 从哪个事件 | 说明 |
|---|---|---|
| 会话 ID | 第一条 `{"type":"thread.started"}` 的 `thread_id` | 取不到时 `resumable=false`，同今天的降级 |
| 命令 | `type == "item.completed"` 且 `item.type == "command_execution"` | 取 `item.command`、`item.exit_code`、`item.status`；不取 `aggregated_output` |
| 用量 | 最后一条 `{"type":"turn.completed"}` 的 `usage` | 五个字段：`input_tokens`、`cached_input_tokens`、`cache_write_input_tokens`、`output_tokens`、`reasoning_output_tokens`；是**整个会话的累计值** |

`item.id` 每轮从 `item_0` 重新编号，不作唯一键。命令最多记 200 条，每条 `command` 最多 1000 个字符；超出部分丢弃，并把 `commandsTruncated` 置为 `true`。

### 判定

去掉开头空白（含 BOM）后看首行：

| 首行开头 | 状态 | 适用 |
|---|---|---|
| `TIME_UP:` | `timeout` | 所有 run |
| `NEED_USER:` | `needs-input` | 可续跑 run、续跑 |
| `DONE:` | `done` | 只在 `--strict` 时识别 |
| 其他 | 不带 `--strict`：`done`（同今天）；带 `--strict`：`unmarked` | — |

被强制中止（收尾轮或兜底）的状态仍是 `timeout`，不受 `--strict` 影响。执行进程未能回收（退出 125）时没有答复判定，状态为 `unreaped`，同样不受 `--strict` 影响。

### `--strict`

- 可用于普通 run、`--resumable`、`--resume`，以及 1.3 新增的 `--continue`。每次调用各自决定，不随链继承。
- 提示词在时间预算段之前多一段：

  > 【结束标记】最终答复的第一行必须以下列标记之一开头：做完了写 `DONE:`，后面接一句总结；<需要用户拍板时写 `NEED_USER:`；>到了时间预算写 `TIME_UP:`。这一要求优先于项目 AGENTS.md 或其他文件里的格式要求。

  尖括号那一句只在可续跑 run 和续跑里出现。
- `unmarked`：退出码 1。stdout 照常输出答复、元数据、`delegate: result=` 行和结果行（`status=unmarked`）。可续跑 run 照常写状态文件，状态为 `unmarked`；`--resume` 按「not waiting for input」拒绝，`--continue` 也拒绝。

### 结果文件

- **位置：** `${TMPDIR:-/tmp}/delegate/<runId>.result.json`，权限 0600，目录要求同状态文件（0700、拒绝软链接），原子写入（临时文件后 `rename`）。
- **何时写：** 只要已经启动过 Codex（今天 `EXEC_STARTED=1` 的那一刻之后）就写，含失败、被信号中断、空答复。参数错误、拒绝（退出 64）不写。
- **何时打印路径：** 有结果行的情形（`done`、`needs-input`、`timeout`、`unmarked`），在结果行之前打印 `delegate: result=<路径>` 到 stdout；没有结果行的情形（失败、中断、未能回收、空答复），打印到 stderr。
- **在哪写：** 在 `finish` 里、`stop_runner` 之后写，这样被中断和未能回收的情形也能写进清理结果。
- **字段（schema 1）：**

```json
{
  "schema": 1,
  "runId": "20261027133326.79650",
  "kind": "run",
  "parent": null,
  "chainRoot": "20261027133326.79650",
  "backend": "codex",
  "repository": "/abs/path/to/repo",
  "write": false,
  "strict": false,
  "model": null,
  "effort": null,
  "status": "done",
  "exitCode": 0,
  "resumable": true,
  "startedAt": "2026-10-27T05:33:26Z",
  "endedAt": "2026-10-27T05:33:52Z",
  "durationSeconds": 26.3,
  "sessionId": "01a17bd9-66cd-7b22-8b09-b1414082a390",
  "answer": {"path": "/…/20261027133326.79650.answer", "bytes": 39},
  "markers": {"needUser": null, "timeUp": null, "done": null},
  "wrapUp": null,
  "commands": [{"command": "/bin/zsh -lc 'cat marker.txt'", "exitCode": 0, "status": "completed"}],
  "commandsTruncated": false,
  "changedFiles": null,
  "usage": {
    "run": {"inputTokens": 124735, "cachedInputTokens": 112256, "cacheWriteInputTokens": 0,
            "outputTokens": 391, "reasoningOutputTokens": 0},
    "session": {"inputTokens": 124735, "cachedInputTokens": 112256, "cacheWriteInputTokens": 0,
                "outputTokens": 391, "reasoningOutputTokens": 0},
    "note": null
  },
  "cleanup": null,
  "logs": {"events": "/…/<runId>.events.jsonl", "stderr": "/…/<runId>.log"}
}
```

字段说明：

- `kind`：`run`（普通或可续跑起头）、`resume`；run-continue 加 `continue`。
- `chainRoot`：链首 runId。普通 run 与可续跑起头的 run 等于自己；续跑沿用父 run 状态文件里的值。
- `status`：有结果行时与结果行一致；没有结果行时为 `failed`（Codex 非零退出）、`interrupted`（信号 129/130/143）、`unreaped`（退出 125，执行进程未能回收）或 `empty`（空答复）。退出码以 `exitCode` 为准：例如到期中止后又回收不了，退出码是 125 而不是 124，状态是 `unreaped`。这是开放集合，使用方遇到不认识的值要当失败处理。
- `markers`：对应标记之后的原文，没有就是 `null`。`done` 只在 `--strict` 时填写。
- `wrapUp`：被强制中止时为 `{"mode": "收尾轮"|"兜底", "reason": <兜底原因或 null>}`；模型主动写 `TIME_UP:` 时为 `{"mode": "主动停", "reason": null}`；其余为 `null`。
- `changedFiles`：写模式下为与运行前基线相比新出现或内容不同的 porcelain 行（同 run-timeout 兜底的算法，所以写模式在每次运行前都记录基线快照，不再只在超时时使用）；只读为 `null`。
- `usage.session`：本次最后一条 `turn.completed` 的累计值；收尾轮也在同一会话里，取主运行和收尾轮中较晚的那一条。没有任何 `turn.completed`（例如中途被杀）时为 `null`。
- `usage.run`：本次用量。普通 run 与可续跑起头的 run 等于 `usage.session`；续跑为 `usage.session` 减去父 run 状态文件里的 `usageTotal`。父 run 的值缺失，或本次 `session` 为 `null` 时为 `null`，`note` 写明原因（「父轮用量未知」或「本次没有完成的轮次」）。**整条链的总用量就是链上最后一次的 `usage.session`；不要把各轮的 `session` 相加。**
- `cleanup`：没有发生中止、且 wrapper 也没有强制结束执行进程时为 `null`。否则为：

  ```json
  {"file": "/…/<runId>.cleanup", "lines": ["delegate: 清理：中止前 Codex 的后代进程 2 个：…", "delegate: 清理：中止后无残留"],
   "leftoverPids": [], "unreapedPid": null, "wrapperForced": false}
  ```

  `lines` 是 `.cleanup` 文件的原文行（主运行与收尾轮各自的报告都在里面），再加上 wrapper 在 `stop_runner` 里打印的行。`leftoverPids` 取自「中止后仍有残留，PID=…」行，`unreapedPid` 取自「执行进程未能回收，PID=…」行，`wrapperForced` 表示出现了「执行进程超时未退出，已强制结束」行。解析不到时字段为空或 `null`，`lines` 原样保留。KILL 后仍有残留只报告、不改退出码，这一点照 0.7.1。
- 其他模块追加的字段：`authorization`、`check`（run-check），`rules`（run-rules），`timeoutSeconds`（run-longrun）。没有用到的模块字段不出现。

### 状态文件

可续跑 run、续跑的状态文件（`schema` 仍为 1，私有文件）增加 `usageTotal`（本次 `usage.session`，可为 `null`）、`chainRoot` 和 `strict`。读旧状态文件时缺这些字段按 `null` 处理，`--resume` 照常可用。

### 失败诊断

Codex 非零退出时，stderr 仍先打印「过程日志末尾（最后最多 40 行 / 16KiB）」，内容来自 `<runId>.log`（stderr）。之后追加「最近的事件：」，最多 10 条，从事件流倒数选取，只选 `type == "error"`、`item.type == "error"` 和 `command_execution`，每条渲染成一行（例如 `命令 /bin/zsh -lc '…' 退出 1`）。最后一行仍是完整日志路径，并加上事件流路径。

### 元数据块

不变，只在成功路径末尾（结果行与 `result=` 行之前）多一行：

```text
用量：本次输入 124,735（缓存 112,256）/ 输出 391；整个会话输入 124,735
```

用量为 `null` 时写「用量：未知（<note>）」。

### 保留与清理

50 组规则删除一组时，一并删除 `.events.jsonl`、`.wrapup.events.jsonl` 与 `.result.json`。（run-continue 会把状态文件和结果文件改为按时间保留，见该模块。）

### 接口 1.3（本模块的部分）

`interface` 改为 `"1.3"`，`run` 下新增：

```json
"result": {"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict",
           "statuses": ["done", "needs-input", "timeout", "unmarked", "failed", "interrupted", "unreaped", "empty"]},
"usage": {"in": "result.usage", "cumulative": "session", "perRun": "run"}
```

其余已有字段不删不改。使用方按 `>=1.3,<2.0` 并检查 `run.result` 存在来判断能否读结果文件。五个模块完成后的完整 1.3 见 [run-rules](run-rules.md) 末尾汇总。

## 代码风格

同 run-resume：Bash 兼容 3.2，`${VAR}`，空数组展开沿用现有守卫；Python 标准库、4 空格缩进、snake_case；JSON 一律用序列化器生成，shell 里不解析 JSON。现有写法示例（`run_state.py`）：

```python
def classify(answer, resumable=True):
    text = answer.lstrip().lstrip('﻿').lstrip()
    if text.startswith(TIME_UP):
        return 'timeout', text[len(TIME_UP):].strip()
```

## 测试策略

- **桩测试（`test-run-result.py`，`unittest`）：** 用自带的假 codex（同 test-run-timeout 的写法）按参数写出预设的 JSONL 与 `-o` 文件。覆盖：
  - 所有 run 路径的 argv 含 `--json`，普通 run 其余参数与改动前逐项相同；
  - 事件流与 stderr 分开落盘；
  - 会话 ID 从 `thread_id` 取，缺失时降级；
  - 命令、退出码、用量的提取，非 JSON 行跳过，200 条与 1000 字符截断；
  - 判定表每一行，含 `--strict` 的 `unmarked` 退出 1；
  - 每种结束情形的结果文件字段、0600 权限、原子写入，以及 `result=` 行的去向，含退出 125 的 `unreaped` 与 `cleanup` 字段的解析（用 0.7.1 的报告原文做夹具）；
  - 续跑的 `usage.run` 取差值，父轮缺失时为 `null`；
  - 失败诊断的渲染；
  - 清理覆盖新文件。
- **免费真机测试：** 沿用 0.7.1 的 `test-reap-fake-endpoint.py` 的做法（本机假 Responses 端点、临时 `CODEX_HOME`、不发送也不读取凭据，没有 `codex` 时跳过），把假端点抽成测试共用的 `fake-responses.py`，加上「回一条答复」的模式，驱动真实 Codex 走一遍普通 run 与可续跑 run，确认事件字段与上表一致，并确认 0.7.1 的回收回归仍然通过。
- **`test-interface.py`：** `interface == "1.3"`，`run.result`、`run.usage` 存在；已有断言不改。
- 先写测试并确认红，再实现。

**付费实测（gate，单独授权）：** 五个模块都完成后，统一用真实模型跑一次（见 run-rules「1.3 合并实测」），不在本模块单独跑。

## 开发边界

- **Always：** 普通 run 除 `--json` 与结果文件外参数和提示词不变，由测试守住；结果行仍是 stdout 最后一行；中英文合同同步；`interface.json`、能力事实和测试一起改。
- **Ask first：** 把命令输出写进结果文件；改结果行格式；付费实测、提交、推送、发版。
- **Never：** 改 `review.command`、`doctor.command` 或升主版本；在结果文件里写账号信息、凭据或完整对话；读取或删除 Codex 会话文件（D1）；把结果文件、状态文件写进业务仓库。

## 成功条件与验证映射

- **RS-01：** 所有 run 路径的 Codex 参数含 `--json`；普通 run 其余参数与 `--ephemeral` 不变（桩测试）。
- **RS-02：** 事件流写 `.events.jsonl`，stderr 写 `.log`；会话 ID 取自 `thread_id`，取不到时 `resumable=false`（桩测试）。
- **RS-03：** 命令、退出码、用量按上表提取，非 JSON 行跳过，截断规则生效（桩测试）。
- **RS-04：** 判定表每一行；`--strict` 缺标记时 `unmarked`、退出 1、结果行照常（桩测试）。
- **RS-05：** 结果文件在每种结束情形下写出（含退出 125 的 `unreaped` 与 `cleanup`），字段与示例一致，0600、原子写入；拒绝时不写（桩测试）。
- **RS-06：** `delegate: result=` 行在结果行之前，结果行仍是最后一行；没有结果行时路径打印到 stderr（桩测试）。
- **RS-07：** `usage.run` 取差值，父轮缺失或本次无完成轮次时为 `null` 且有 `note`（桩测试）。
- **RS-08：** 失败诊断包含 stderr 末尾和最多 10 条渲染事件（桩测试）。
- **RS-09：** 清理覆盖新增文件（桩测试）。
- **RS-10：** 假端点驱动真实 Codex，事件字段与实现一致；0.7.1 的回收回归仍通过（免费真机测试）。
- **RS-11：** `interface.json` 为 1.3，含 `run.result`、`run.usage`；已有字段不变；两项 plugin validate 通过。
- **RS-12：** `run.md`、`help.md`、中英文 README、中英文合同、指向句和待发行说明同步，含「日志变成两个文件」「result 行」「`unmarked`」的升级提示。
- **RS-13：** 总验证、两项 plugin validate、`git diff --check` 全部通过；现有测试断言不改（参数断言因 `--json` 需要更新的，逐条在 Plan 里列出并说明）。

## 开放问题

- 已按 0.7.1（`64d7ece`）核对：`cleanup` 字段直接取 `.cleanup` 原文与 wrapper 的报告行，不另起格式；退出 125 记为 `unreaped`。
- 现有测试里断言 Codex 参数逐项相等的用例，会因为多了 `--json` 失败。这属于有意的参数变化，Plan 里逐条列出要更新的断言，不算「削弱断言」。
