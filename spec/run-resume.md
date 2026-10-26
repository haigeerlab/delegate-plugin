# 规格：run-resume（可续跑委托）

<!-- spec-guard: review approved ae640dc77692 -->

简体中文 | [English](../docs/en/SPEC-run-resume.md)

2026-10-24 起草。起因是生态方案 S32（多模块并行流畅与额度外包）：用户 2026-10-24 批准接口方案（原话「按推荐批准」），其中 delegate 接口 `1.0` → `1.1`、只增不改。使用方是 module-crew 的额度外包开关 `codexOffload`：Spec、Plan 在 Claude 会话批准后，协调会话经 `/delegate:run` 把实现交给 Codex；Codex 碰到要用户拍板的事时停下，问题经协调会话转给用户，用户答复后续跑。依据是调研报告第 8 节：`codex exec resume <会话ID> "<答复>"` 三次续跑都接上了上下文；当时停得过早，需要在提示词里写明先做不受影响的任务。

## 前提（已于 2026-10-24 经用户确认 A1–A8）

- **A1** 新模块 `run-resume`，依赖 channel 与 integration-interface。channel、integration-interface 的原有条款一条不改，只各加一句指向本模块。
- **A2** 可续跑模式要显式打开：run 新增 `--resumable`。不带它的 run 行为与今天逐字节相同（提示词、`--ephemeral`、Codex 参数），唯一增加的是 A3 的结果行。（R2 起另加固定审批参数，见修订记录。）
- **A3** 每次成功返回的 run 在 stdout 末尾多一行 `delegate: run_id=<id> status=<done|needs-input> resumable=<true|false>`。`needs-input` 退出码仍为 0；超时、失败、空答复沿用现有退出码，不输出该行。
- **A4** 续跑写法 `--resume <runId> [--write] -- "<用户答复>"`。只接受最近一轮、状态为 `needs-input` 的 runId；同一仓库根目录；`--write` 与原运行一致；不接受 `--model`、`--effort`，沿用原设置；每轮新 runId；状态文件随日志保留策略清理；不删 Codex 自己的会话文件。
- **A5** `needs-input` 只靠提示词约定的 `NEED_USER:` 标记识别，不用 `--output-schema`。模型漏写标记会被判成 `done`，这是已知限制。
- **A6** `interface.json` 升到 `1.1`，`run` 下只新增可选字段 `resume`。`review.command`、`doctor.command` 及其他已有字段不动，主版本不变。
- **A7** 不做：后台守护进程（后台由调用方用 Bash 后台模式实现）；改 540 秒期限；续跑超时或失败的运行；git 提交权限（归 module-crew 的前缀放行规则）；claude-code 后端续跑。
- **A8** 验证分两层：免费桩测试，加一次付费真实实测。实测作为 Plan 里的 gate，届时单独授权。

## 修订记录

- **R1（2026-10-25，用户选定「选 A」）：** 首次付费实测（RR-10）中，只读续跑的日志头是 `sandbox: read-only`，但写文件命令仍然成功，日志里没有审批事件。推断是用户本机 Codex 配置 `approval_policy = "on-request"` 加 `approvals_reviewer = "guardian_subagent"` 代批了越出沙箱的命令，这与 S32 决定 7「不用自动审查代理代批」冲突。修订：可续跑运行和每一轮续跑都固定传 `-c approval_policy="never"`，越出沙箱的命令直接被拒，不交给任何审批方；写模式下的提交仍由使用方的前缀放行规则决定（调研 8.1 节在 `never` 下验证有效）。普通 run 不变；普通 run 是否同样受本机审批配置影响，不在本模块范围，另作后续事项。
- **R2（2026-10-25，用户经 delegate 负责人转达的原话：「让子会话把 approval_policy="never" 的修订扩大到 run、resume、review 全部调用路径，并实测现有只读路径是否会被放行。」，在本会话复审批准后生效）：** R1 扩大到 delegate 所有让 Codex 执行任务的调用：普通 run（只读与写入）、可续跑 run、续跑、Codex 后端 review，一律固定 `-c approval_policy="never"`。只做探测、不调用模型的调用（`codex --version`、`codex login status`、`codex features list`）不在此列。R1 中「普通 run 不变」由本条取代：普通 run 的参数只多这一项，提示词与其余参数不变。另加一次付费实测，用已发布 v0.5.3 的只读 run 和 review，在本机审批配置下检验会不会写出文件，结果交 delegate 负责人判断已发布接口里 `readOnly: true` 的含义。
  - 影响：写模式 run 里需要越出沙箱的命令（如在 worktree 里 `git commit`、网络访问）以前可能被本机审批方放行，现在直接被拒；需要提交的使用方继续依靠前缀放行规则，或由调用方代为提交。
  - 本模块因此改动 claude-review 管理的 `review_execution.py` 一行参数，并在 `spec/claude-review.md` 及其英文页加一句指向本条。

## 技术栈与命令

Bash 3.2 wrapper、Python 3 标准库、Git、Codex CLI（本机实测帮助的版本为 0.162.1）。不新增依赖、hook 或命令入口；仍是 `/delegate:run`。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-run-resume.py
python3 -B plugins/delegate/tests/test-interface.py
/bin/bash plugins/delegate/tests/test-channel.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/codex-exec.sh        → 增加 --resumable / --resume 分支、结果行、状态文件清理
plugins/delegate/scripts/run_state.py         → 新增：runId 校验、状态文件读写、NEED_USER 判定、会话 ID 提取（标准库）
plugins/delegate/scripts/delegate_backend.py  → 解析并转发两个新参数，校验组合
plugins/delegate/scripts/delegate_cli.py      → run 子命令放行新参数
plugins/delegate/scripts/delegate_capabilities.py → codex 增加 resume 能力事实
plugins/delegate/interface.json               → interface 1.1，run.resume
plugins/delegate/commands/run.md / help.md    → 用法与答复纪律
plugins/delegate/tests/test-run-resume.py     → 新增：桩测试
plugins/delegate/tests/test-interface.py      → 增加 1.1 断言
plugins/delegate/scripts/review_execution.py  → R2：Codex review 调用加固定审批参数（仅一项参数）
plugins/delegate/tests/test-review-backends.py → R2：断言普通 run（只读、写入）实际参数含该项
plugins/delegate/tests/test-review-execution.py → R2：断言 Codex review 实际参数含该项
spec/claude-review.md / docs/en/SPEC-claude-review.md → R2：各加一句指向本模块修订记录
plugins/delegate/README.md / README.en.md     → 可续跑一节；对外接口一节补 1.1
spec/run-resume.md / docs/en/SPEC-run-resume.md → 本合同
spec/channel.md、spec/integration-interface.md 及英文对应页 → 各加一句指向本模块
docs/releases/unreleased.md 及英文对应页      → 待发行说明
```

## 行为合同

### 普通 run（不带 `--resumable`）

提示词、`--ephemeral` 与其余参数与今天相同，只在认证配置之后多一项 `-c approval_policy="never"`（R2）。成功时在现有元数据块之后输出：

```text
delegate: run_id=20261024183015.12345 status=done resumable=false
```

`run_id` 即现有日志文件名用的 `RUN_ID`（`<14 位时间戳>.<进程号>`）。

### 可续跑 run（`--resumable`）

- 不传 `--ephemeral`，Codex 会话保存在它自己的会话目录（`~/.codex/sessions`）。另加 `-c approval_policy="never"`（R1），不使用用户配置里的审批方式。其余参数（认证配置、沙箱、模型、推理档、`-o`、stdin=/dev/null、进程组与 540 秒期限）与普通 run 相同。
- 使用可续跑提示词，替换现有的「非交互委托」开头。沙箱那一句与现有只读或写入版本相同：

  > 【可续跑委托】你的最终答复会转给用户；用户答复后，会带着答复在本会话里接着跑。先做不受待定决策影响的任务，碰到需要用户拍板的决策（规格没覆盖的取舍、测试改不红、高风险不可逆操作）再停。要停时，最终答复第一行以 `NEED_USER:` 开头，后面写要问用户的问题，再写已完成的进度和可选项；不需要用户时照常做到底，第一行不要写 `NEED_USER:`。

- 会话 ID 取自过程日志里第一行 `session id: <uuid>`。取不到时本次照常返回，但 `resumable=false`，stderr 说明原因。
- 判定：答复去掉开头空白后以 `NEED_USER:` 开头为 `needs-input`，否则为 `done`。`needs-input` 时，答复照常完整输出，**问题原文就是标记之后的全部内容**。
- 成功返回时写状态文件 `${TMPDIR:-/tmp}/delegate/<runId>.state.json`（0600，所在目录 0700，拒绝软链接），字段：`schema`（1）、`runId`、`sessionId`、`repository`（Git 根目录真实路径）、`write`、`model`、`effort`、`status`、`parent`（续跑时为上一轮 runId，否则 `null`）。

### 续跑（`--resume <runId>`）

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --resume <runId> [--write] -- "<用户答复>"
```

- 执行：`codex exec resume`。Codex 沙箱只能经 `-c sandbox_mode="read-only|workspace-write"` 传入（`resume` 不接受 `--sandbox`），模型和推理档沿用状态文件。同样固定 `-c approval_policy="never"`（R1）。认证配置、`-o`、stdin=/dev/null、进程组与期限同普通 run，不传 `--ephemeral`。
- 发给 Codex 的内容：

  > 【用户答复】<答复原文>
  >
  > 请按上次约定继续：先做不受待定决策影响的任务；还需要用户拍板时，最终答复第一行以 `NEED_USER:` 开头。

- 每轮生成新 runId 和新日志，结果行与判定规则同可续跑 run，状态文件的 `parent` 指向上一轮。可以一轮接一轮续下去。
- 写模式输出与现有写入相同的 Git 验收块，基线在本轮启动前重新记录。
- 启动前在每个 runId 上用排他创建 `<runId>.resumed` 占位，防止同一问题被续跑两次。占位后若在调起 Codex 前失败，占位保留，需要重新发起可续跑 run。

**拒绝（退出 64，不调用 Codex，stderr 为 `delegate: <原因>`）：**

| 原因 | 情形 |
|---|---|
| `invalid run id` | runId 不符合 `^[0-9]{14}\.[0-9]+$` |
| `run not found` | 状态文件不存在（未用 `--resumable`、运行失败、已被保留策略清理） |
| `run not resumable` | 状态文件里没有会话 ID |
| `run not waiting for input` | 状态不是 `needs-input` |
| `run already resumed` | 该 runId 已被续跑过 |
| `repository mismatch` | 当前 Git 根目录与状态文件不同 |
| `write mode mismatch` | `--write` 有无与原运行不同 |
| 参数组合错误 | `--resume` 与 `--resumable`、`--model`、`--effort`、`--backend claude-code` 同用；答复为空 |

### 保留与清理

现有「保留最近 50 组日志」在删除日志时一并删除同 runId 的 `.state.json` 和 `.resumed`。清理失败不改变执行状态。Codex 自己的会话文件由 Codex 管理，delegate 不读、不删。

### 接口 1.1

```json
{
  "interface": "1.1",
  "review": {
    "command": "/delegate:review",
    "backends": ["codex", "claude-code"],
    "readOnly": true,
    "report": {"schemaVersion": 1}
  },
  "run": {
    "command": "/delegate:run", "backends": ["codex"], "write": "explicit",
    "resume": {"optIn": "--resumable", "option": "--resume", "backends": ["codex"],
               "statuses": ["done", "needs-input"]}
  },
  "doctor": {"command": "/delegate:doctor"}
}
```

使用方按 `>=1.1,<2.0` 判断能否续跑；读到 `1.0` 或没有 `run.resume` 字段，就按今天的做法处理（不续跑）。`resume.backends` 与 `backends` 一样，只表示支持，不表示可用。

## 答复与授权纪律（写进 `run.md`）

- `--resume` 的答复必须是用户本人的答复原文，或用户明确同意的转述。调用方模型不得自己替用户回答 `needs-input` 问题。delegate 无法核实这一点，这是命令指令层面的纪律，不是技术锁。
- 续跑带 `--write`，前提是原运行已获得写入授权，且用户的答复没有收回授权。delegate 只校验 `--write` 与原运行一致，不替用户授权。
- `needs-input` 不是失败，也不是批准；问题要原样交给用户。

## 代码风格

保持已有风格：Bash 兼容 3.2，变量写 `${VAR}`，空数组展开沿用已有守卫；Python 用标准库、4 空格缩进、snake_case；JSON 用序列化器生成。shell 里不解析 JSON，交给 `run_state.py`。现有写法示例（`codex-exec.sh`）：

```bash
if [ -n "${MODEL}" ]; then
  EXTRA+=(-m "${MODEL}")
fi
```

## 测试策略

`test-run-resume.py` 用标准库 `unittest`，加上现有 `stub-codex`（它会记录 argv，并把 `STUB_ANSWER` 写到 `-o` 指定的文件）和临时 Git 夹具；需要时给桩加一个可选的日志头输出。覆盖：

- 普通 run 传给 Codex 的参数与改动前逐项相同，stdout 只多出结果行；
- `--resumable` 的参数、提示词、状态文件内容与权限、会话 ID 提取，以及取不到会话 ID 时降级；
- `done` 与 `needs-input` 判定，包括开头空白和标记不在第一行的情况；
- 续跑的参数（`exec resume`、`-c sandbox_mode`、沿用模型和推理档、会话 ID、答复正文）、新 runId 与 `parent`；
- 拒绝表中每一行都退出 64，且桩没有被调用；
- 写模式续跑输出 Git 验收块；
- 清理同时删除状态文件。

`test-interface.py` 增加断言：`interface == "1.1"`；`run.resume.backends` 等于 `BACKENDS` 里 `resume` 为真的后端；`review.command == "/delegate:review"`、`doctor.command == "/delegate:doctor"`。现有断言不改。

先写测试并确认它红，再实现。桩测试只能证明参数和流程，不能证明真实 Codex 的行为。

**付费实测（gate，单独授权）：** 用真实 Codex 在家目录下的临时 Git 仓库（不放 `/tmp`，避免沙箱造成假通过）跑一次 `--resumable`，让它命中一个待定决策，再 `--resume` 一次。确认三件事：

- 日志里能取到会话 ID；
- `-c sandbox_mode` 在 resume 里生效（只读续跑时写文件被拒）；
- 上下文接得上。

## 开发边界

- **Always：** 普通 run 与改动前逐字节一致，由测试守住；中英文合同同步；`interface.json`、能力事实和测试一起改。
- **Ask first：** 让所有 run 默认可续跑；续跑超时或失败的运行；用 `--output-schema` 结构化答复；改 540 秒期限；付费实测、提交、推送、发版。
- **Never：** 改 `review.command`、`doctor.command` 或升主版本；续跑时悄悄升级写权限；让任何让 Codex 执行任务的调用沿用用户配置的审批方式（含自动审查代理代批）；替用户回答 `needs-input`；读取或删除 Codex 会话文件；把状态文件或会话 ID 写进业务仓库。

## 成功条件与验证映射

- **RR-01：** 不带 `--resumable` 时提示词与其余参数不变，参数只多 `approval_policy="never"`（R2），输出只多结果行（桩测试）。
- **RR-02：** `--resumable` 不传 `--ephemeral`、固定 `approval_policy="never"`，使用含「先做不受待定决策影响的任务……再停」的提示词，写出 0600 状态文件并提取会话 ID；取不到时降级为 `resumable=false`（桩测试）。
- **RR-03：** `done` / `needs-input` 按标记判定，`needs-input` 退出 0，答复完整输出（桩测试）。
- **RR-04：** 续跑调用 `codex exec resume`，带正确的沙箱、`approval_policy="never"`、模型、推理档、会话 ID 和答复，产生新 runId 和 `parent` 链（桩测试）。
- **RR-05：** 拒绝表中每一行都退出 64，且不调用 Codex（桩测试）。
- **RR-06：** 写模式续跑输出 Git 验收块；只读续跑不输出（桩测试）。
- **RR-07：** `interface.json` 为 1.1，含 `run.resume`；两个 command 字段原值不变；一致性测试通过；两项 plugin validate 通过。
- **RR-08：** 保留策略同时清理状态文件（桩测试）。
- **RR-09：** `run.md`、`help.md`、中英文 README、中英文合同和待发行说明同步，含答复与授权纪律。
- **RR-10：** 付费实测确认会话 ID 提取、resume 沙箱生效（只读续跑写文件被拒）、上下文接续（gate，单独授权；未授权就标「未验证」）。2026-10-25 首次实测：会话 ID、`--` 分隔、上下文接续、先做不受影响的任务均成立；只读续跑写文件**未被拒**，按 R1 修订后重测这一项。
- **RR-11：** 总验证、两项 plugin validate、`git diff --check` 全部通过；现有测试断言不改。
- **RR-12（R2）：** 普通 run（只读、写入）、可续跑 run、续跑、Codex review 实际传给 Codex 的参数都含 `-c approval_policy="never"`，由桩测试断言（桩记录的实际 argv，不比对源码文本）。
- **RR-13（R2，付费，gate，单独授权）：** 用已发布 v0.5.3 的只读 run 和 Codex review 各跑一次最小提示词（要求在仓库里写一个文件），在本机 `approval_policy="on-request"`、`approvals_reviewer="guardian_subagent"` 下记录是否写出文件；改动后再用当前源码的只读 run 跑一次，确认写入被拒。结果单独报 delegate 负责人。

## 开放问题

- 已由首次实测确认：`codex exec resume` 接受 `--` 分隔，`-c sandbox_mode` 进入续跑配置。`approval_policy="never"` 能否让只读续跑拒绝写入，由 R1 后的重测确认；仍不成立就再回到本规格。
- 已发布 v0.5.3 的只读 run、review 是否会被本机审批配置放行写入，由 RR-13 实测；结论影响已发布 `interface.json` 中 `readOnly: true` 的说法，由 delegate 负责人报 ecosystem-lead 判断，本模块不改该字段。
- 大模块超过 540 秒怎么办，归 S32 落地补测（调研 9.5 节），本模块不处理。
- 是否需要续跑超时的运行，等 LIVE-SAAS 试点有数据再议。
