# 规格：run-rules（`--rules-file` 本次委托专用的规则片段）

<!-- spec-guard: review approved ea56d01837d0 -->

简体中文 | [English](../docs/en/SPEC-run-rules.md)

2026-10-27 起草；用户 2026-10-27 批准，原话：「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」对应生态方案 S38 第 9 项（全文与用户原话见 [run-result](run-result.md)）。方案原文：「`--rules-file`：片段原样放在 delegate 前言之后，冲突时以片段为准（安全边界除外）。worktree 下 Codex 会不会读 AGENTS.md，要实测。」

## 前提（2026-10-27 用户确认，本模块用到的几条）

- **S13** `--rules-file <文件>`：
  - 内容原样放在 delegate 前言之后、任务之前，前面加【项目规则（本次委托专用）】，并注明冲突时以本节为准，但沙箱、不提交不推送、首行标记这几条安全边界除外。
  - UTF-8，最多 16 KiB，否则退出 64。
  - AGENTS.md 由 Codex 自己读，delegate 不读也不拼；片段只放 AGENTS.md 以外、这一次委托专用的规则。
  - 路径和 sha256 写进结果文件。
  - `--continue`、`--resume` 可以再传，传了就在那一轮的提示词里再放一次。

依赖：[run-result](run-result.md)（结果文件；`--strict` 的结束标记段）。

## 实测依据

[S38 前置实测](../docs/verification/2026-10-27-delegate-s38-probe.md) T3、T4：在 git worktree 下，Codex 自动读取该 worktree 根目录的 AGENTS.md 并照做，而且这份 AGENTS.md 能改动 delegate 任务要求的答复格式（任务要求两行，答复多出第三行暗号）。由此：

- 项目已有 AGENTS.md 的规则，Codex 本来就会读，`--rules-file` 不用重复放；
- AGENTS.md 若要求「首行写某某」，可能挤掉 `NEED_USER:`／`TIME_UP:`／`DONE:`。这由 run-result 的 `--strict`（缺标记判 `unmarked`）兜住，本模块在规则段里再强调一次首行标记不可改变。

## 影响面

- **提示词（只增）：** 只有带 `--rules-file` 时提示词多一段，不带时完全不变。
- **interface：** 新增 `run.rules`。本模块是五个模块里的最后一个，写完后 1.3 的能力标记齐全，见文末汇总。

## 技术栈与命令

同 [run-result](run-result.md)；新增测试文件：

```bash
python3 -B plugins/delegate/tests/test-run-rules.py
```

## 项目结构

```text
plugins/delegate/scripts/codex-exec.sh          → 读取并校验规则文件，拼进提示词
plugins/delegate/scripts/delegate_backend.py    → 解析并转发 --rules-file
plugins/delegate/scripts/delegate_capabilities.py → codex 增加 rules 能力事实
plugins/delegate/interface.json                 → run.rules
plugins/delegate/commands/run.md / help.md      → 用法与定位
plugins/delegate/tests/test-run-rules.py        → 新增：桩测试
plugins/delegate/tests/test-interface.py        → 加 run.rules 断言与 1.3 汇总断言
spec/run-rules.md / docs/en/SPEC-run-rules.md   → 本合同
README 中英文、待发行说明                         → 同步
```

## 行为合同

### 写法与校验

`run … --rules-file <文件> -- "<任务>"`，可用于普通 run、`--resumable`、`--resume`、`--continue`，最多给一次。调用 Codex 之前校验，不通过退出 64，stderr 为 `delegate: rules file not usable`，另起一行写具体原因：

- 路径不存在、是软链接（按 `lstat`）或不是普通文件；
- 读不了；
- 为空，或去掉空白后为空；
- 超过 16 KiB；
- 不是合法 UTF-8；
- 含 NUL 字符。

### 放在哪里

普通 run 与可续跑 run 的提示词顺序为：前言（非交互委托或可续跑委托）→ **规则段** → 任务正文 → 结束标记段（`--strict`）→ 时间预算段。

`--resume`、`--continue` 的顺序为：**规则段** →【用户答复】或【下一个任务】→ 结束标记段 → 时间预算段。

收尾轮的提示词固定，不放规则段。

规则段的写法：

> 【项目规则（本次委托专用）】以下规则由调用方提供，只对本次委托有效；与上文冲突时以本节为准。但下面几条不能被本节改变：沙箱限制；不提交、不推送；最终答复第一行的标记（`NEED_USER:`、`TIME_UP:`，以及要求时的 `DONE:`）。
>
> <文件原文>
>
> 【项目规则结束】

文件原文原样放入，不转义、不截断。末尾若缺换行就补一个。

### 与 AGENTS.md 的关系（写进 `run.md`）

- Codex 会自己读取工作目录所在 worktree 根的 AGENTS.md（实测 T3），delegate 不读、不拼、不检查 AGENTS.md。
- `--rules-file` 只放 AGENTS.md 以外、这一次委托专用的规则，例如这个 Task 的验收口径、这个模块的临时约定。项目长期规则应写进 AGENTS.md。
- 两者冲突时，Codex 实际听谁的，没有机制保证；规则段的措辞只能提高优先级。需要可靠的结束标记，就同时用 `--strict`。

### 结果

结果文件增加 `"rules": {"path": "<绝对路径>", "sha256": "…", "bytes": N}`，不带时不出现。不在结果文件里写规则原文。

### 接口（本模块的部分）

`run` 下新增：

```json
"rules": {"option": "--rules-file", "maxBytes": 16384, "placement": "after-preamble",
          "projectInstructions": "codex-reads-agents-md"}
```

### 1.3 完整形状（五个模块完成后）

```json
{
  "interface": "1.3",
  "review": {
    "command": "/delegate:review",
    "backends": ["codex", "claude-code"],
    "readOnly": true,
    "report": {"schemaVersion": 1}
  },
  "run": {
    "command": "/delegate:run", "backends": ["codex"], "write": "explicit",
    "resume": {"optIn": "--resumable", "option": "--resume", "backends": ["codex"],
               "statuses": ["done", "needs-input", "timeout"]},
    "timeout": {"status": "timeout", "exitCode": 124},
    "result": {"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict",
               "statuses": ["done", "needs-input", "timeout", "unmarked", "failed", "interrupted", "unreaped", "empty"]},
    "usage": {"in": "result.usage", "cumulative": "session", "perRun": "run"},
    "continue": {"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable",
                 "stateRetentionDays": 14},
    "longRun": {"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540,
                "background": "caller"},
    "check": {"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600,
              "operators": ["&&", "||", ";", "|", ">", "<", "`", "$("], "match": "token-prefix-or-suffix"},
    "writeAuthorization": {"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization",
                           "verifies": ["file-sha256-across-chain", "repository"]},
    "rules": {"option": "--rules-file", "maxBytes": 16384, "placement": "after-preamble",
              "projectInstructions": "codex-reads-agents-md"}
  },
  "doctor": {"command": "/delegate:doctor"}
}
```

方案里的能力标记与字段的对应：`run.result` → `run.result`；`run.usage` → `run.usage`；`run.continue` → `run.continue`；`run.longRun` → `run.longRun`；`run.check`（`shell: false`）→ `run.check.shell`；`run.writeAuthorization` → `run.writeAuthorization`；`run.rules` → `run.rules`。1.4 的 `run.restore`、`run.concurrent`、`doctor.quota` 不在 1.3。

## 1.3 合并实测（付费，gate，单独授权）

五个模块都完成后，统一做一次付费实测，不在单个模块里分别跑。在家目录的临时仓库里，用真实模型走一条完整链：

1. `--resumable --strict --rules-file` 起头；
2. `--continue --write --authorized-by --check` 接一轮；
3. 一轮 `--timeout`（后台模式）。

确认的事项：

- 结果文件各字段与真实事件一致；
- `usage.run` 取差值正确；
- 规则段与 AGENTS.md 同时存在时首行标记是否保住；
- `--check` 在真实工作区执行。

次数与上限届时单独提，授权后再跑。

## 代码风格

同 [run-result](run-result.md)。

## 测试策略

`test-run-rules.py`（`unittest`，自带假 codex）覆盖：

- 拒绝表每一项都退出 64，且不调用 Codex；
- 四种调用（普通、可续跑、续跑、接续）里规则段的位置与原文逐字节一致；
- 收尾轮没有规则段；
- 不带 `--rules-file` 时提示词与改动前相同；
- 结果文件里有 `rules` 字段，不含规则原文。

`test-interface.py` 加 `run.rules` 断言，并断言 1.3 的完整字段集合（上面的汇总）。先写测试并确认红，再实现。

## 开发边界

- **Always：** 不带 `--rules-file` 时提示词不变；规则段写明不可改变的安全边界；中英文合同同步。
- **Ask first：** 读取或拼接 AGENTS.md；放宽 16 KiB；让规则段能改变安全边界；付费实测、提交、推送、发版。
- **Never：** 修改、转义或截断规则原文；在结果文件里写规则原文；在收尾轮里放规则段。

## 成功条件与验证映射

- **RU-01：** 拒绝表每一项退出 64，不调用 Codex（桩测试）。
- **RU-02：** 四种调用的规则段位置和原文逐字节正确，收尾轮没有规则段，不带时提示词不变（桩测试）。
- **RU-03：** 结果文件有 `rules`（路径、sha256、字节数），没有原文（桩测试）。
- **RU-04：** `interface.json` 为完整的 1.3，字段与汇总一致；已有字段不变；两项 plugin validate 通过。
- **RU-05：** `run.md`（与 AGENTS.md 的关系）、`help.md`、中英文 README、中英文合同、待发行说明同步。
- **RU-06：** 总验证、两项 plugin validate、`git diff --check` 通过。
- **RU-07（付费，gate，单独授权）：** 1.3 合并实测，结果记入验证记录；有不成立的，回到对应模块的规格。

## 开放问题

- 规则段与 AGENTS.md 冲突时 Codex 听谁的，只能靠实测观察（RU-07），无法保证。
- 16 KiB 上限是估计值；超出时建议写进 AGENTS.md。
