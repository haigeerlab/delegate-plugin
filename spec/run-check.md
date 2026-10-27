# 规格：run-check（`--check` 跑完检查与 `--authorized-by` 事先写入授权）

<!-- spec-guard: review approved 845bd3397b4f -->

简体中文 | [English](../docs/en/SPEC-run-check.md)

2026-10-27 起草；用户 2026-10-27 批准，原话：「批准 run-result、run-continue、run-longrun、run-check、run-rules 五份 Spec，开始写英文页和 Plan。」对应生态方案 S38 第 4、5 项与决定点 3，用户 2026-10-27 批准原话：「……写入授权按有条件折中……」（全文见 [run-result](run-result.md)）。方案的守门条款：「`--check` 在沙箱外以你的权限执行，所以命令只能来自项目配置里你批过的 checkCommand 或 quickCheckCommand，不能由 Codex 或模块会话临时拼。」

## 前提（2026-10-27 用户确认，本模块用到的几条）

- **S11** `--check "<命令>"`：
  - 校验照抄 module-crew S30：POSIX `shlex.split`，按首尾匹配 `_SHELL_OPS`，三条拒绝文案一字不差（文案里写的是 module-crew，按要求照抄）。拒绝时退出 64，不调用 Codex。
  - 只在运行以 `done` 结束时，在仓库根目录按参数列表执行；其他状态记为「跳过」。
  - 检查有自己的期限，默认 600 秒，不计入 `--timeout`。
  - 退出码和输出末尾 40 行写进结果文件；检查失败不改变运行的状态。
- **S12** `--authorized-by <文件>`：
  - 文件须是可读的普通文件、不是软链接、不为空；delegate 只记录路径、sha256、大小，核实不了内容。
  - `--write` 仍须显式传。条件折中的四条写进 `run.md` 的授权纪律，由使用方负责；delegate 只核对同一 worktree（仓库根）和整条链用同一个授权文件（sha256）。
  - 检查命令只能来自项目配置里用户批过的 checkCommand 或 quickCheckCommand，也写进纪律。

依赖：[run-result](run-result.md)（结果文件）。运算符规则来源：module-crew `module_crew/merge.py:24` 的 `_SHELL_OPS` 与 `_check_config`，mc-coord 经 agent-relay 消息 #11736 给出的原文。

## 影响面

- **授权纪律（只增）：** 今天 `run.md` 与 routing 的规矩是「只有用户在当轮明确要求才能加 `--write`；说『继续』不会自动升级写权限」。现在加一条例外：满足下文四个条件、并带 `--authorized-by` 时，视为本轮已授权。原规则其余部分不变，`run.write: "explicit"` 不变。routing 规格与 `delegate-routing` skill 各加一句指向本模块。
- **沙箱外执行：** `--check` 的命令由 delegate 在 Codex 沙箱之外、以用户权限执行。这是 delegate 第一次在沙箱外执行调用方给的命令，所以只接受参数列表，不经 shell，并且来源由纪律限定。
- **与 module-crew 的一致性：** 运算符规则与 module-crew 共用。delegate 不得比它更严或更松；要改，先发 mc-coord，两边同步改并交用户批。
- **interface：** 新增 `run.check`、`run.writeAuthorization`。

## 技术栈与命令

同 [run-result](run-result.md)；新增测试文件：

```bash
python3 -B plugins/delegate/tests/test-run-check.py
```

## 项目结构

```text
plugins/delegate/scripts/run_check.py           → 新增：检查命令校验（照抄 S30）、经 run_codex.py 执行、取末尾 40 行
plugins/delegate/scripts/run_state.py           → 状态文件记录 authorization；续跑时核对授权文件
plugins/delegate/scripts/codex-exec.sh          → --check 在 Codex 结束后、Git 验收块之前执行；--authorized-by 校验与记录
plugins/delegate/scripts/delegate_backend.py    → 解析并转发两个参数，校验组合
plugins/delegate/scripts/delegate_capabilities.py → codex 增加 check、writeAuthorization 能力事实
plugins/delegate/interface.json                 → run.check、run.writeAuthorization
plugins/delegate/commands/run.md / help.md      → 用法与授权纪律
plugins/delegate/skills/delegate-routing/SKILL.md → 写入授权例外一句
plugins/delegate/tests/test-run-check.py        → 新增：桩测试
plugins/delegate/tests/test-interface.py        → 加两项断言
spec/run-check.md / docs/en/SPEC-run-check.md   → 本合同
spec/routing.md 及英文对应页                     → 指向句
README 中英文、待发行说明                         → 同步
```

## 行为合同

### `--check`

**写法：** `run … --check "<命令>" -- "<任务>"`，可用于普通 run、`--resumable`、`--resume`、`--continue`，最多给一次。

**校验（解析参数时，调用 Codex 之前）：** 与 module-crew S30 完全相同：

```python
_SHELL_OPS = ("&&", "||", ";", "|", ">", "<", "`", "$(")
argv = shlex.split(command)          # POSIX 模式
bad = next((t for t in argv if t.startswith(_SHELL_OPS) or t.endswith(_SHELL_OPS)), None)
```

拒绝时退出 64、不调用 Codex，stderr 只有下面一行，**一字不差**，前面不加 `delegate: `：

| 情形 | 文案 |
|---|---|
| 拆不开（`ValueError`） | `检查命令拆不开：{异常信息}` |
| 拆出空列表 | `检查命令不能为空` |
| 有 token 以运算符开头或结尾 | `检查命令里有 shell 运算符（「{token}」）：module-crew 不经 shell 执行检查命令，运算符会被当成普通参数。改用两种写法之一：把这些步骤写进项目脚本，检查命令写这个脚本；或写成 /bin/sh -c '<原命令>'` |

由此而来的边界照抄、不另定：夹在 token 中间的不拦（`foo&&bar`、`a|b`）；引号里的整段算一个 token，所以 `/bin/sh -c 'make test && make lint'` 放行；单个 `&`、`$VAR`、`2>&1` 不拦；`>file` 拦。`run_check.py` 里的常量带注释，写明来源与「改动先发 mc-coord」。

**执行时机：** Codex 结束、判定完成后，Git 验收块之前。只有本次状态为 `done`（退出码 0）时执行；其余状态（`needs-input`、`timeout`、`unmarked`、失败、中断、空答复）不执行，记为 `skipped`。

**怎么执行：**

- 复用 0.7.1 的 `run_codex.py` 作为执行器：`python3 -B run_codex.py --report <runId>.check.cleanup 600 <argv…>`。它按参数列表 `Popen`、不经 shell、放进新会话，到期或被中断时按 S41 回收后代，直接子进程回收不了时退出 125。
- 工作目录为仓库根（`git rev-parse --show-toplevel`）；stdin 为 `/dev/null`；环境变量与 delegate 自身相同，不加 Codex 的环境（`DELEGATE_REVIEW_DEPTH` 等）。
- stdout 与 stderr 合并写到 `<runId>.check.log`；取末尾 40 行，最多 16 KiB。`.check.log`、`.check.cleanup` 归入日志类文件，按 50 组清理。
- 期限 600 秒，集中定义为常量。

**结果文件** 增加：

```json
"check": {"command": "<原文>", "argv": ["…"], "status": "passed", "exitCode": 0,
          "durationSeconds": 12.4, "tail": "…"}
```

`status` 取以下之一，是开放集合：

- `passed`：退出码 0；
- `failed`：其他退出码；
- `timeout`：超过期限（`run_codex.py` 退出 124）；
- `cannot-run`：启动失败（`run_codex.py` 报「无法启动」并退出 127），或检查命令自己退出 126、127；
- `unreaped`：`run_codex.py` 退出 125，检查进程未能回收，`check.cleanup` 带上 `.check.cleanup` 的原文行；
- `skipped`：运行没有以 `done` 结束，此时只有 `command`、`argv`、`status` 三个字段。

**输出：** 元数据块里加一行 `检查：<通过|失败（退出 N）|超时|跑不起来|未能回收|跳过>`。运行本身的状态和退出码**不受检查结果影响**，结果行不变。使用方要看 `check.status` 自己判断。

### `--authorized-by`

**写法：** `run --write --authorized-by <文件> …`，可用于 `--write` 的普通 run、`--resumable`、`--resume`、`--continue`。

**校验（调用 Codex 之前，退出 64，stderr 为 `delegate: <原因>`）：**

| 原因 | 情形 |
|---|---|
| `--authorized-by requires --write` | 没有 `--write` |
| `authorization file not usable` | 路径不存在，或是软链接（按 `lstat`），或不是普通文件，或读不了，或大小为 0，或超过 64 KiB |
| `authorization mismatch` | 续跑或接续时，链上状态文件已记录授权文件，而本次没给，或本次给的文件 sha256 与记录的不同 |

**记录：**

- 结果文件增加 `"authorization": {"source": "file", "path": "<绝对路径>", "sha256": "…", "bytes": N}`。
- 写模式但没带 `--authorized-by` 时，记为 `{"source": "in-turn"}`，表示调用方声称用户当轮明确要求写入。
- 只读运行为 `null`。
- 可续跑链的状态文件记录 `authorization`（`path`、`sha256`），供后续轮核对。链上第一次没有授权文件、之后某一轮加上的，从那一轮起按它核对。
- 元数据块加一行 `写入授权：文件 <路径>（sha256 <前 12 位>）` 或 `写入授权：当轮`。

delegate 不读也不解释授权文件的内容，只计算 sha256。核对「同一 worktree」靠现有的仓库根比对（`repository mismatch`）。

### 授权纪律（写进 `run.md`，routing skill 加一句指向）

下面四条同时满足时，调用方可以不等用户在当轮开口，就带 `--write --authorized-by <文件>`：

1. 用户打开外包开关时的原话，已经由使用方（module-crew）记录成这个文件；
2. 这个模块的 Spec 和 Plan 已批准，派出的 Task 在已批 Plan 之内；
3. 同一个模块、同一个 worktree；
4. 授权来源由 delegate 写进每次的结果，即上面的 `authorization` 字段，调用方不得删除或改写。

任何一条不满足，就回到原规则：只有用户当轮明确要求才加 `--write`。delegate 只能核对第 3 条的仓库部分和文件是否一致，其余由调用方负责，这是命令指令层面的纪律，不是技术锁。

`--check` 的命令只能取自项目配置里用户批过的 checkCommand 或 quickCheckCommand，不能由 Codex、调用方模型或模块会话临时拼写。delegate 无法核实来源，同样是纪律。

### 接口（本模块的部分）

`run` 下新增：

```json
"check": {"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600,
          "operators": ["&&", "||", ";", "|", ">", "<", "`", "$("], "match": "token-prefix-or-suffix"},
"writeAuthorization": {"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization",
                       "verifies": ["file-sha256-across-chain", "repository"]}
```

`run.write` 仍是 `"explicit"`。使用方按 `>=1.3,<2.0` 且字段存在来判断。

## 代码风格

同 [run-result](run-result.md)。运算符常量与判定照抄 module-crew 的写法：

```python
_SHELL_OPS = ("&&", "||", ";", "|", ">", "<", "`", "$(")   # S38, copied from module-crew S30 (merge.py:24); change via mc-coord
```

## 测试策略

`test-run-check.py`（`unittest`，自带假 codex，临时 Git 夹具）覆盖：

- **校验：** 拆不开、空、每个运算符分别出现在 token 开头和结尾，这些情况的拒绝文案逐字比对（与 #11736 原文一致）、退出 64、不调用 Codex；边界放行：`foo&&bar`、`/bin/sh -c 'a && b'`、`2>&1`、单个 `&`、`$VAR`。
- **执行：** 经 `run_codex.py` 执行、参数列表、不经 shell（命令里的 `*` 等不被展开）、工作目录为仓库根、stdin 为空；`passed`、`failed`、`timeout`（缩短期限）、`cannot-run`（不存在的程序、126、127）、`unreaped`（桩执行器退出 125）、`skipped`（`needs-input`、`timeout`、失败）；末尾 40 行与 16 KiB 截断；运行退出码与结果行不受检查结果影响；在 Git 验收块之前执行。
- **授权：** 拒绝表每一行；`source: file`、`in-turn`、只读为 `null`；链上 sha256 核对（相同通过、不同或缺失拒绝、中途加上后按新的核对）。
- `test-interface.py` 加两项断言。先写测试并确认红，再实现。

## 开发边界

- **Always：** 运算符规则与 module-crew 一字不差，由测试守住；检查不经 shell；`run.write` 仍是 `"explicit"`；中英文合同同步。
- **Ask first：** 改运算符清单或判定方式（先发 mc-coord）；检查结果影响运行状态；在非 `done` 状态下执行检查；读取授权文件内容；付费实测、提交、推送、发版。
- **Never：** 经 shell 执行检查命令；接受 Codex 产出的检查命令；不带 `--write` 时接受 `--authorized-by`；在结果文件里写授权文件的内容。

## 成功条件与验证映射

- **CK-01：** 三条拒绝文案逐字一致，退出 64，不调用 Codex（桩测试）。
- **CK-02：** 照抄的边界逐条放行或拦截（桩测试）。
- **CK-03：** 检查只在 `done` 时执行，按参数列表、不经 shell、在仓库根、stdin 为空，在 Git 验收块之前（桩测试）。
- **CK-04：** 六种 `check.status` 与截断规则正确；运行状态和退出码不受影响（桩测试）。
- **CK-05：** `--authorized-by` 拒绝表每一行退出 64；`authorization` 字段三种取值正确（桩测试）。
- **CK-06：** 链上授权文件 sha256 核对（桩测试）。
- **CK-07：** `interface.json` 含 `run.check`、`run.writeAuthorization`，`run.write` 仍为 `"explicit"`；两项 plugin validate 通过。
- **CK-08：** `run.md` 授权纪律四条、检查命令来源纪律、routing 规格与 skill 的指向句、`help.md`、中英文 README、中英文合同、待发行说明同步。
- **CK-09：** 总验证、两项 plugin validate、`git diff --check` 通过。

## 开放问题

- 拒绝文案里写的是「module-crew 不经 shell 执行检查命令」，在 delegate 里读起来主语不对。按要求一字不差照抄；要改，须 module-crew 同步改并交用户批。
- 检查期限 600 秒对全量测试是否够用，没有数据；module-crew 的默认是 1800 秒。是否加 `--check-timeout`，留到试点后再议（Ask first）。
