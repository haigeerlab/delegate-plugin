# delegate 插件

简体中文 | [English](README.en.md)

本目录是 delegate 插件本体，也是安装后缓存里的内容。完整的安装、参数、验收与故障排查说明见仓库 [README](https://github.com/haigeerlab/delegate-plugin#readme)。

delegate 把范围明确的只读审查交给 Codex 或 Claude Code，把已定方案的通用任务交给 Codex。后端用 `--backend` 显式选择，默认 Codex；插件只在用户明确请求或确认后执行，不自动派活。

## 安装

在终端运行：

```bash
claude plugin marketplace add haigeerlab/delegate-plugin
claude plugin install delegate@delegate-marketplace
```

安装后打开新会话或执行 `/reload-plugins`。更新用 `claude plugin update delegate@delegate-marketplace`。

## 命令

| 命令 | 作用 | 是否调用后端模型 |
|---|---|---|
| `/delegate:review` | 对 `--paths`、`--base`、`--changes` 或 `--context` 指定的范围做只读审查，后端 codex 或 claude-code | 是；`--dry-run` 除外 |
| `/delegate:run` | 把已确认的任务交给 Codex；默认只读，用户明确授权后加 `--write` 才写文件 | 是 |
| `/delegate:doctor [--backend codex\|claude-code]` | 检查所选后端的本地条件 | 否 |
| `/delegate:help` | 显示参数、退出码与迁移说明 | 否 |

Codex 中对应的 skill 为 `source-command-review`、`source-command-run`、`source-command-doctor`、`source-command-help`。旧 `/delegate:delegate` 已在 v0.5.0 移除，通用任务改用 run，结构化审查改用 review。

## 依赖

- 所有用法：Git 工作区、Python 3、Bash（兼容 3.2）。
- Codex 后端：PATH 中可运行的 `codex`，使用 ChatGPT 登录。
- Claude Code 审查后端（可选）：macOS、原版 Claude Code ≥2.1.295 且已登录、Node.js ≥22.12.0、已安装的 srt 0.0.79、可用的用户 GUI launchd 域。

插件不安装依赖、不登录、不修改全局配置：`--write` 运行用 `-c` 只对本次运行临时信任当前仓库，不让 Codex 往 `~/.codex/config.toml` 写信任记录（读不准时除外，会在 stderr 提示），详见[根 README](../../README.md#输出与验收)。所有 run 与 Codex 审查固定 `approval_policy="never"`，不用本机配置的审批方式：越出沙箱的命令（如 worktree 里 `git commit`、网络访问）直接被拒，提交靠前缀放行规则或由调用方完成。首次使用前运行 `/delegate:doctor`，使用 Claude 后端前运行 `/delegate:doctor --backend claude-code`。

## 目录

```text
.claude-plugin/plugin.json   插件清单
interface.json               对外接口版本与能力声明
commands/                    review、run、doctor、help 会话入口
skills/delegate-routing/     显式委托请求的分流判据
hooks/                       SessionStart 基础探测、缓存与 doctor 入口
scripts/                     后端调用（Codex / Claude Code）与进程管理
tests/                       离线桩测试与回归
```

## 可续跑委托

`/delegate:run --resumable` 让 Codex 先做不受待定决策影响的任务，碰到需要用户拍板的事再停下。默认不开启；开启后 Codex 会话保存在它自己的会话目录。

- 每次成功返回和超时时的最后一行：`delegate: run_id=<id> status=<done|needs-input|timeout> resumable=<true|false>`。**判断成功先看退出码为 0，再看 `status=done`；有结果行不等于成功。**
- `needs-input` 退出码为 0，答复以 `NEED_USER:` 开头，标记之后是要问用户的问题原文。
- 用户答复后：`/delegate:run --resume <runId> [--write] -- "<用户答复>"`。答复须是用户原话或其同意的转述；只续跑最近一轮 needs-input，同一仓库、写模式一致，沿用原模型与推理档；每轮新 runId。
- 超时（`status=timeout`，退出 124）：提示词里有时间预算，模型应在到期前主动停下并写进度（答复首行 `TIME_UP:`）；被强制中止时再以只读沙箱续跑一轮只写进度的收尾，收尾也失败就输出不靠模型的兜底文字（会话 ID、可否续跑，写模式附改动文件）。超时后可用 `--resume` 续跑，由用户决定。
- 普通 run（不带 `--resumable`）同样有时间预算和兜底，超时也是 `status=timeout`、退出 124，但会话不保留，不能续跑。
- 已知限制：模型漏写标记会判为 done；失败的运行不能续跑。
- **done 之后接着派下一个任务（接口 1.3 起）**：`/delegate:run --continue <runId> [--write] -- "<下一个任务>"`，只接 `--resumable` 起头的链上状态为 `done` 的一轮，在同一个 Codex 会话里接着做，不必重新起会话、重读项目。一个 runId 只能被接一次；任务须来自已批准的 Plan 或用户本人。
- 链上的状态文件和结果文件保留 14 天，过程日志只保留最近 50 组。

## 结果文件

每次启动过 Codex 的 run 都写一份 JSON 结果文件 `${TMPDIR:-/tmp}/delegate/<runId>.result.json`（0600），供使用方机器读取，不用解析过程日志。

- 有结果行时，结果行的前一行是 `delegate: result=<路径>`；失败、中断、未能回收（退出 125）、空答复时这一行在 stderr。
- 内容：`status`、`exitCode`、`runId`／`parent`／`chainRoot`、会话 ID、Codex 跑过的命令与退出码、写模式改动的文件、`NEED_USER:`／`TIME_UP:`／`DONE:` 之后的原文、收尾方式、中止清理结果、耗时，以及 token。
- token 来自 Codex 的 `turn.completed`，是**整个会话的累计值**：`usage.session` 是会话总量，`usage.run` 是本次用量（续跑时取与上一轮的差值）。整条链的总量就是最后一次的 `usage.session`，不要把各轮相加。
- `--strict`：最终答复首行必须是 `DONE:`、`NEED_USER:`（仅可续跑）或 `TIME_UP:`。缺标记判 `status=unmarked`，退出 1，不能续跑。项目 AGENTS.md 若要求别的首行格式，可能挤掉标记，`--strict` 用来兜住这种情况。
- 不读取 Codex 自己的会话文件，所以上下文占用、压缩和额度不在结果文件里。
- 过程日志拆成两个文件：`<runId>.events.jsonl`（Codex 的 JSON 事件流）和 `<runId>.log`（stderr）。

## 对外接口

供其他插件按版本对接，不读本插件内部文件。

- **`interface.json`**：位于插件根目录。`interface` 是接口版本；`review.backends`、`run.backends` 是本版本**支持**的后端，不代表本机已安装、已登录或有额度，能否运行仍以 `/delegate:doctor` 为准。只增加可选字段升次版本，删除、改名或改变含义升主版本；使用方按主版本范围检查，如 `>=1.0,<2.0`。
- **续跑（接口 1.1 起）**：`run.resume` 为 `{"optIn": "--resumable", "option": "--resume", "backends": ["codex"], "statuses": [...]}`。使用方按 `>=1.1,<2.0` 判断能否续跑；读到 1.0 或没有该字段时按原做法处理，不续跑。
- **超时（接口 1.2 起）**：`run.resume.statuses` 为 `["done", "needs-input", "timeout"]`，另有 `run.timeout` 为 `{"status": "timeout", "exitCode": 124}`。使用方按 `>=1.2,<2.0` 才使用 `timeout`；读到 1.1 时超时仍是退出 124，按失败处理。
- **结果文件（接口 1.3 起）**：`run.result` 为 `{"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict", "statuses": [...]}`，`run.usage` 说明 token 的累计口径。使用方按 `>=1.3,<2.0` 且字段存在时读取结果文件。
- **接着派任务（接口 1.3 起）**：`run.continue` 为 `{"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable", "stateRetentionDays": 14}`。
- **`statuses` 是开放集合**：以后的次版本可能追加新值。遇到不认识的值必须停下或当失败处理，不能当成完成；判断成功先看退出码为 0，再看 `status=done`。
- **审查报告（`review.report.schemaVersion: 1`）**：`/delegate:review` 的标准输出是一份 JSON 报告（`--dry-run` 输出的是预览，不是报告）。标准错误中的私有副本路径不属于接口。稳定字段：

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定 `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`、`scope.baseline`、`scope.diff_sha256`、`scope.files` | 审查对象与指纹 |
| `reviewed`、`unreviewed[]`（`{path, reason}`） | 已审与未审文件 |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified}`，`line` 可为 `null` |
| `limitations` | 限制说明 |

其他字段属于诊断信息，可能变化。只有 `execution_status=completed` 且 `review_outcome` 为 `findings` 或 `no_findings_in_scope` 才算有结论；`no_findings_in_scope` 不等于没有缺陷。报告是第三方参考意见，不是用户批准；引用时注明 delegate、后端与指纹。

## 反馈与许可

问题和建议请提交到 [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues)；安全问题请通过[私密漏洞报告](https://github.com/haigeerlab/delegate-plugin/security/advisories/new)提交。本插件采用 [MIT 许可证](LICENSE)。
