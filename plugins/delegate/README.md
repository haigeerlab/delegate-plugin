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
- Claude Code 审查后端（可选）：macOS、原版 Claude Code ≥2.1.295 且已登录、Node.js ≥22.12.0、已安装的 srt 0.0.79（npm 包 `@anthropic-ai/sandbox-runtime`，`srt --version` 须为 `0.0.79`）、可用的用户 GUI launchd 域。

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

## 检查与事先写入授权

- `/delegate:run --check "<命令>"`（接口 1.3 起）：运行以 `done` 结束后，由 delegate 在仓库根按参数列表执行检查命令（不经 shell，期限 600 秒），结果写进结果文件的 `check`，不改变运行本身的状态。命令里有 shell 运算符时拒绝，规则与 module-crew 相同。检查在沙箱外以你的权限执行，所以命令只能来自项目配置里你批过的检查命令。
- `/delegate:run --write --authorized-by <文件>`（接口 1.3 起）：使用方（module-crew）把你打开外包开关时的原话记录成文件，在 Spec 和 Plan 已批、Task 在已批 Plan 内、同一模块同一 worktree 时，可以不必每个 Task 都等你点头。delegate 只记录文件的路径和 sha256，并要求整条链用同一个文件；它核实不了文件内容。

## 规则片段

`/delegate:run --rules-file <文件>`（接口 1.3 起）把本次委托专用的规则原样放进提示词（前言之后、任务之前，最多 16 KiB），冲突时以它为准，但沙箱、不提交不推送和首行标记不能被它改变。Codex 会自己读 worktree 根的 AGENTS.md，delegate 不读也不拼；项目长期规则写进 AGENTS.md，这个片段只放这一次委托专用的规则。

## 长任务

默认期限 540 秒。`/delegate:run --timeout <秒>` 可以放大到 541～7200 秒（接口 1.3 起），期限的分配、时间预算、收尾和退出码与默认期限相同。带 `--timeout` 就必须用宿主的后台模式调用（超过 540 秒即须后台，不按 Claude Code 的 Bash 前台上限 600 秒自行判断）；delegate 不托管后台进程，要停下就停止那个后台任务，中止时会回收 Codex 起的全部后代进程。一次运行最多约 `T + 30` 秒结束。

## 结果文件

每次启动过 Codex 的 run 都写一份 JSON 结果文件 `${TMPDIR:-/tmp}/delegate/<runId>.result.json`（0600），供使用方机器读取，不用解析过程日志。

- 有结果行时，结果行的前一行是 `delegate: result=<路径>`；失败、中断、未能回收（退出 125）、空答复时这一行在 stderr。
- 内容：`status`、`exitCode`、`runId`／`parent`／`chainRoot`、会话 ID、Codex 跑过的命令与退出码、写模式改动的文件、`NEED_USER:`／`TIME_UP:`／`DONE:` 之后的原文、收尾方式、中止清理结果、耗时，以及 token。
- token 来自 Codex 的 `turn.completed`，是**整个会话的累计值**：`usage.session` 是会话总量，`usage.run` 是本次用量（续跑时取与上一轮的差值）。整条链的总量就是最后一次的 `usage.session`，不要把各轮相加。
- `--strict`：最终答复首行必须是 `DONE:`、`NEED_USER:`（仅可续跑）或 `TIME_UP:`。缺标记判 `status=unmarked`，退出 1，不能续跑。项目 AGENTS.md 若要求别的首行格式，可能挤掉标记，`--strict` 用来兜住这种情况。
- 不读取 Codex 自己的会话文件，所以上下文占用、压缩和额度不在结果文件里。
- 过程日志拆成两个文件：`<runId>.events.jsonl`（Codex 的 JSON 事件流）和 `<runId>.log`（stderr）。

## 默认模型配置

不想每次点名模型时，在 `~/.config/delegate/config.json` 按后端写好默认值（设了绝对路径的 `XDG_CONFIG_HOME` 就放在 `$XDG_CONFIG_HOME/delegate/config.json`）。delegate 只读这个文件，不创建、不修改它，也不改 Codex／Claude 的全局配置。

```json
{
  "schema": "delegate.config/v1",
  "defaults": {
    "codex": {"model": "gpt-6.2-sol", "effort": "high"},
    "claude-code": {"model": "claude-opus-5-5"}
  }
}
```

- 优先级：这次点名的 `--model`／`--effort` > 本文件 > 宿主默认（什么都不传，跟随 Codex／Claude 自己的配置）。模型和推理档分别取值。
- `--backend auto` 选中哪家就用哪家的默认值；`--resume`、`--continue` 沿用原会话记下的模型和推理档，不取本文件里的值，但仍会校验本文件：文件有错时续跑同样退出 64。
- 每个后端和字段都可以省略；`claude-code` 不支持 `effort`。多出来的键、拼错的名字、不合法的模型名或推理档都算配置错误：**文件存在但有错时，所有 review／run 退出 64**，stderr 只有一行 `delegate: invalid config <路径>: <原因码>[ at <字段>]`，不回显内容。改正或删掉文件即恢复；文件不存在不算错误。
- 实际用的模型和来源：审查报告的 `requested_model`、`model_source`，结果文件的 `model`、`modelSource`、`effort`、`effortSource`，run 输出的「模型：… / 推理档：…」一行；`/delegate:doctor` 最前面列出当前生效的默认值。来源取值 `explicit`（点名）、`config`（本文件）、`host_default`（宿主默认）、`resumed`（沿用原会话）。
- 只有 `/delegate:review`、`/delegate:run`（`delegate-exec.sh review|run`）读本文件；直接调用旧入口 `codex-exec.sh` 不读。从 Codex 里调 Claude Code 审查读的是同一份文件。合同见[规格](../../spec/default-model.md)。

## 对外接口

供其他插件按版本对接，不读本插件内部文件。

- **`interface.json`**：位于插件根目录。`interface` 是接口版本；`review.backends`、`run.backends` 是本版本**支持**的后端，不代表本机已安装、已登录或有额度，能否运行仍以 `/delegate:doctor` 为准。只增加可选字段升次版本，删除、改名或改变含义升主版本；使用方按主版本范围检查，如 `>=1.0,<2.0`。
- **续跑（接口 1.1 起）**：`run.resume` 为 `{"optIn": "--resumable", "option": "--resume", "backends": ["codex"], "statuses": [...]}`。使用方按 `>=1.1,<2.0` 判断能否续跑；读到 1.0 或没有该字段时按原做法处理，不续跑。
- **超时（接口 1.2 起）**：`run.resume.statuses` 为 `["done", "needs-input", "timeout"]`，另有 `run.timeout` 为 `{"status": "timeout", "exitCode": 124}`。使用方按 `>=1.2,<2.0` 才使用 `timeout`；读到 1.1 时超时仍是退出 124，按失败处理。
- **结果文件（接口 1.3 起）**：`run.result` 为 `{"schemaVersion": 1, "line": "delegate: result=<path>", "strict": "--strict", "statuses": [...]}`，`run.usage` 说明 token 的累计口径。使用方按 `>=1.3,<2.0` 且字段存在时读取结果文件。
- **接着派任务（接口 1.3 起）**：`run.continue` 为 `{"option": "--continue", "backends": ["codex"], "accepts": ["done"], "chain": "--resumable", "stateRetentionDays": 14}`。
- **长任务（接口 1.3 起）**：`run.longRun` 为 `{"option": "--timeout", "minSeconds": 541, "maxSeconds": 7200, "defaultSeconds": 540, "background": "caller"}`，`background: "caller"` 表示后台由调用方负责。
- **检查与写入授权（接口 1.3 起）**：`run.check` 为 `{"option": "--check", "shell": false, "when": "done", "timeoutSeconds": 600, "operators": [...], "match": "token-prefix-or-suffix"}`，运算符规则与 module-crew S30 一致；`run.writeAuthorization` 为 `{"option": "--authorized-by", "requires": "--write", "recorded": "result.authorization", "verifies": [...]}`。`run.write` 仍是 `"explicit"`。
- **规则片段（接口 1.3 起）**：`run.rules` 为 `{"option": "--rules-file", "maxBytes": 16384, "placement": "after-preamble", "projectInstructions": "codex-reads-agents-md"}`。
- **补丁指纹（接口 1.4 起）**：`review.report.fingerprint` 为 `{"field": "scope.fingerprint", "algorithm": "blob-pairs-v1", "baselineModes": ["commits"]}`，算法见[规格](../../spec/review-fingerprint.md)。只用两个提交树里每个被审文件的权限和对象编号算 sha256，与 git 配置、git 版本无关，可以在别的机器（如 GitHub Actions）复算；Actions 上浅克隆时要能取到 `from` 提交。
- **发现的严重程度（接口 1.5 起）**：`review.report.severity` 为 `{"field": "findings[].severity", "values": ["blocking", "suggestion"], "criteria": "severity-v1", "missing": "blocking"}`。审查模型按固定判据 `severity-v1`（见[规格](../../spec/review-severity.md)）给每条发现标 `blocking`（阻断）或 `suggestion`（建议），`--task` 不能改判据；以后改判据只换新名字。
- **复审对照上一轮（接口 1.5 起）**：`review.recheck` 为 `{"option": "--previous-report", "field": "recheck", "statuses": ["resolved", "unresolved"]}`，合同见[规格](../../spec/review-recheck.md)。把上一轮 delegate 报告交进来，上一轮的阻断发现逐条进 `recheck.items` 标已解决或未解决，本轮 `findings` 只放新问题；上一轮报告必须已有结论、范围相同。
- **快照审查的复审（接口 1.6 起）**：`review.recheck.snapshot` 为 `true`，合同见[规格](../../spec/review-snapshot-recheck.md)。Plan 这类快照审查（`--paths` 不带 `--base`，基准 `from == to`）返工后也能带 `--previous-report`：两轮都是快照时只比 `paths` 与 `mode`，本轮提交须是上一轮提交本身或其后代（换了分支、提交不存在或是标签对象都报 `previous_report_scope_mismatch`）；一轮快照一轮区间也报这个码。`--spec`／`--plan` 带进来的参考文件，提示词会说明只用来核实引用、不对它们本身提发现。不在审查范围里的参考文件不要求审查者报告覆盖，没提到它们不算漏审（0.12.1 起）。
- **技术方案审查（接口 1.7 起）**：`review.profiles.design` 为 `{"option": "--profile design", "criteria": "design-v1", "downgraded": ["no_code_evidence", "second_round"]}`，合同见[规格](../../spec/design-review-criteria.md)。`--profile design` 用判据 `design-v1` 审技术方案：阻断必须指向一个**参考文件**（用 `--spec`／`--plan` 带进来、不在审查范围里的文件）里存在的行，否则 delegate 把它改记为建议并标 `downgraded: "no_code_evidence"`，原文不改；带 `--previous-report` 的第二轮只核对上一轮，新发现一律记为建议并标 `downgraded: "second_round"`；design 档里行号核不上的发现不让整轮失败。报告顶层新增 `criteria`（`severity-v1` 或 `design-v1`），复审时两轮必须相同（老报告缺字段按 `severity-v1`）。审技术方案时务必把要对照的已有代码、需求文档用 `--spec` 带上，否则所有阻断都会降为建议。不带 `--profile` 时行为与判据不变。
- **第二审查者的选择（接口 1.7 起）**：`review.reviewer` 声明 `--backend auto` 与 `--author-host codex|claude-code`，合同见[规格](../../spec/reviewer-selection.md)。`auto` 必须说明主开发是谁；delegate 用无模型检查优先选另一家厂商，否则用同厂商的全新会话，都不可用时出「未审」报告：`execution_status=conditions_missing`、`review_outcome=inconclusive`、诊断首项 `no_reviewer_available`、顶层 `backend` 为 `null`、退出 127。`auto` 不能和 `--model`、`--effort`、`--max-turns`、`--max-budget-usd` 同用。报告顶层新增 `reviewer: {vendor, backend, same_vendor, selection}`，`vendor` 为 `openai`／`anthropic`，`selection` 为 `cross_vendor`／`same_vendor_fallback`／`explicit`／`none`；显式指定后端又没给主开发时 `same_vendor` 为 `null`。审查总是新起会话，写代码的会话不会审自己的东西。`/delegate:doctor --reviewers [--json]` 列出本机可用的审查者（JSON 为 `delegate.reviewers/v1`），只有一家时建议再开通一家，不阻止任何操作。
- **`statuses` 是开放集合**：以后的次版本可能追加新值。遇到不认识的值必须停下或当失败处理，不能当成完成；判断成功先看退出码为 0，再看 `status=done`。
- **审查报告（`review.report.schemaVersion: 1`）**：`/delegate:review` 的标准输出是一份 JSON 报告（`--dry-run` 输出的是预览，不是报告）。标准错误中的私有副本路径不属于接口。稳定字段：

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定 `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`、`scope.baseline`、`scope.diff_sha256`、`scope.files` | 审查对象与指纹；`diff_sha256` 是 diff 文字的 sha256，受本机 git 配置与版本影响，只在本机有效 |
| `scope.fingerprint`（接口 1.4 起） | `{algorithm, sha256, paths}`；只在基准为 `commits` 时有值，其他基准为 `null` |
| `reviewed`、`unreviewed[]`（`{path, reason}`） | 已审与未审文件 |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified, severity}`，`line` 可为 `null`；`severity`（接口 1.5 起）为 `blocking` 或 `suggestion` |
| `recheck`（接口 1.5 起） | 不带 `--previous-report` 时为 `null`；带时为 `{previous_report_sha256, previous_fingerprint, items}`，`items[]` 为 `{index, status, evidence, finding}`，`status` 为 `resolved` 或 `unresolved` |
| `limitations` | 限制说明 |

其他字段属于诊断信息，可能变化。只有 `execution_status=completed` 且 `review_outcome` 为 `findings` 或 `no_findings_in_scope` 才算有结论；`no_findings_in_scope` 不等于没有缺陷。报告是第三方参考意见，不是用户批准；引用时注明 delegate、后端与指纹。复算 `scope.fingerprint` 时：只证明审查看到的补丁就是 `paths` 从 `from` 到 `to` 的这些变化，PR 里有没有审查没看到的文件要自己对比 `paths`；指纹一致不等于有结论，更不等于可以合并；遇到不认识的 `algorithm` 按无法复算处理。读 `severity` 时：缺这个字段（0.9.0 及以前的报告）或值不认识，一律按 `blocking`；只在有结论时才看；`unverified` 非空的阻断发现是审查者拿不准、按判据从严标的；严重程度是模型的判断，没有阻断发现也不等于可以合并。复审时本轮的阻断集合 = `recheck.items` 里 `unresolved` 的 + `findings` 里按 `blocking` 处理的，只在有结论时才看；要核对复审的是修正后的补丁，比较 `recheck.previous_fingerprint` 和本轮 `scope.fingerprint`；快照复审没有补丁、指纹每轮相同，改为比较两轮报告 `scope.files` 里的 sha256。
- **默认模型（接口 1.8 起）**：顶层 `defaults` 声明配置文件位置、`delegate.config/v1` 和来源取值；审查报告新增稳定字段 `model_source`，结果文件新增 `modelSource`、`effortSource`。`requested_model` 现在是 delegate 实际传给后端的模型（点名或配置；宿主默认时为 `null`）。见上文「默认模型配置」与[规格](../../spec/default-model.md)。

## 反馈与许可

问题和建议请提交到 [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues)；安全问题请通过[私密漏洞报告](https://github.com/haigeerlab/delegate-plugin/security/advisories/new)提交。本插件采用 [MIT 许可证](LICENSE)。
