# delegate

Claude Code 插件。把范围、方案和验收目标已经明确的执行与查证交给 **Codex CLI**，主会话收到最终答复，过程日志留在本机。

当前仅支持 ChatGPT 登录的 Codex；目的在于分担执行过程的上下文消耗。实际消耗哪个账号的额度取决于 Codex 登录账号，不保证节省总费用或总 token。

## 目录导航

- [使用与边界](#使用与边界)、[安装](#安装)、[命令](#命令)、[故障处理](#故障处理)
- [设计](DESIGN.md)、[能力图](capability-map.md)
- [执行规格](SPEC-channel.md)、[探测规格](SPEC-detection.md)、[路由规格](SPEC-routing.md)
- [0.4.0 版本说明与升级指引](docs/releases/v0.4.0.md)、[变更摘要](docs/releases/unreleased.md)
- [开发与验证](#开发与验证)

## 使用与边界

先确认范围，再执行；需要写文件时，用户须在当前轮明确授权。

| 场景 | 用法 |
|---|---|
| 代码审查、找回归、安全审查 | 只读，指定检查范围和报告格式 |
| 跨文件摸结构、梳理调用链 | 只读，指定入口和要回答的问题 |
| 定位 bug、读日志和调用栈 | 只读；需要产生文件或运行会写缓存的测试时，应另行授权写模式 |
| 按明确方案实现单个任务、跑测试到绿 | `--write`，给出可验证的验收目标 |
| 批量重命名、迁移、机械修改 | `--write`，明确文件范围和排除项 |
| 需求澄清、架构取舍、验收结果、改一行 | 留在主会话处理 |

流程：基础探测 → Claude 提议具体任务 → 用户确认 → Codex 执行 → 查看答复与 Git 证据 → 主会话验收。
用户直接输入委托命令也构成该任务的执行授权。插件命令和 skill 要求确认，但这是模型指令约束；wrapper 本身没有不可绕过的授权令牌。

能做：单次、非交互、同步委托；选模型与推理档；默认只读；明确授权后可写；隔离过程日志；失败诊断；Git 变更概览。

不能做：替用户决定未定方案；保证代码正确；保证模型遵守所有指令；自动提交、推送或发布；持续后台任务、排队、断点续跑、自动重试、多后端或团队配额管理。当前**只接受 Git 工作区**，默认只读同样如此。

## 安装

依赖：Claude Code（支持插件）、Codex CLI、Python 3、Git、macOS 的 Bash 3.2。当前修复验证环境为 Claude Code 2.1.291、Codex CLI 0.160.0、Python 3.10、Bash 3.2；没有承诺更早版本的最低兼容线，也未验证 Windows。

```bash
npm install -g @openai/codex@latest
codex --version
codex login
codex login status
```

认证状态须显示 ChatGPT 登录。凭据可能在 `CODEX_HOME` 或系统钥匙串中，插件用 CLI 状态确认，不以 `auth.json` 存在为依据。API key 登录和未知认证状态会被拒绝；执行时还清除 `OPENAI_API_KEY`、`CODEX_API_KEY` 并指定 ChatGPT 认证与 OpenAI provider。[Codex 认证说明](https://learn.chatgpt.com/docs/auth)

从插件源码目录进行本地安装：

```bash
claude plugin marketplace add "$PWD"
claude plugin install delegate@delegate-marketplace
```

也可以向 `marketplace add` 提供本仓库的 URL。安装后在业务 Git 项目中启动 Claude Code，运行 `/delegate:doctor`。

修改源目录不会自动更新已安装缓存。用户决定更新时再运行：

```bash
claude plugin update delegate@delegate-marketplace
```

当前清单版本为 0.4.0；正式发行以对应版本标签和发布记录为准。升级由用户主动执行。开发或评估源码时，在业务 Git 项目中显式加载：

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

## 命令

插件命令使用完整命名空间；以 Claude Code 当前加载的命令列表为准。[官方命令说明](https://code.claude.com/docs/en/plugins/components)

| 入口 | 作用 | 是否执行 Codex 任务 |
|---|---|---|
| `/delegate:delegate [选项] <任务>` | 委托一个明确任务 | 是 |
| `/delegate:doctor` | 刷新本地基础探测，检查全局 AGENTS.md 的部分中文规则 | 否，仅 CLI 状态探测 |
| `/delegate:help` | 参数、示例、限制和故障帮助 | 否 |
| `/delegate:delegate-routing` | 安装宿主支持时可调用的 skill：讨论任务是否适合委托 | 自身只提供判据，仍需确认 |

```text
/delegate:delegate 审查 src/payments 的错误处理；只报告有代码证据的问题
/delegate:delegate --write 按已确认的方案修复空指针；运行相关测试并报告结果
/delegate:delegate --model <模型 slug> --effort high 梳理登录链路
```

| 参数 | 约定 |
|---|---|
| 不传参数开关 | `read-only` 沙箱 |
| `--write` | `workspace-write` 沙箱；须用户当前轮明确授权 |
| `--model <slug>` | 透传模型名称；省略则采用 Codex 配置，非法值由 CLI 报错 |
| `--effort <level>` | 透传推理档；合法值取决于模型和 CLI 版本 |
| `--` | 终止选项解析，允许任务以 `-` 开头 |
| `--help` / `-h` | wrapper 的本地参数帮助，不依赖 Codex |

脚本入口在**业务 Git 项目目录**执行；任务必须是一个完整、正确引用的参数：

```bash
bash /path/to/delegate-plugin/plugins/delegate/scripts/codex-exec.sh --write "按已确认方案修复并测试"
```

Claude 的 Bash 工具 timeout 设为 `600000`。wrapper 的 Codex 执行期限默认 **540 秒**；`DELEGATE_TIMEOUT_SECONDS` 可设置更短的正整数，超过 540 会被截断，非法或非正值回落 540。认证探测每项最多 5 秒，超时清理最多等待 2 秒后强制终止进程组。执行期限不包括前置探测与后置 Git 检查。

## 输出与验收

成功时返回 Codex 最终答复、模型/推理档提示、日志路径与字节数。写模式额外返回：基线 HEAD（含尚无提交的仓库）、原有未提交变更数量、`git status --short`、未暂存与已暂存 diff 统计。

执行失败、超时、空答复或中断后，**已经开始的写模式任务仍输出 Git 验收块到 stderr**。失败不会自动回滚。已有改动允许保留，统计不能区分用户原改动与本次改动；必须审阅实际 diff 和测试结果。Git 检查本身失败时也应按错误输出处理，不把概览当作完整验收。

过程日志与答复位于 `${TMPDIR:-/tmp}/delegate/`，目录 0700、新文件 0600。完成或失败后尽力保留最近 **50 组** `.log/.answer`；清理失败不改变任务退出码。这是数量限制，单个日志和最终答复没有体积上限。失败回显过程日志尾部最多 40 行 / 16KiB，并给出完整路径；按需读取少量行，避免把整个日志带回会话。

默认只读与可写权限由 Codex 沙箱实现。`workspace-write` 的可写范围也可能包括临时目录和宿主配置的额外根目录，不能宣称仅 cwd 可写。preamble 中“不要提交、推送、启动服务或越范围访问网络”是行为指令，不能替代 OS 沙箱或宿主权限配置。

## 故障处理

| 症状 | 检查与下一步 |
|---|---|
| 命令找不到 | 检查加载的插件、命名空间和安装缓存；源码更新后需用户主动更新或 `--plugin-dir` 加载 |
| Codex 缺失或版本命令失败 | `codex --version`；修复安装与 PATH |
| 未登录、API key 登录或未知认证 | `codex login status`；执行 `codex login` 选择 ChatGPT 登录 |
| 登录后仍不提议 | `/delegate:doctor` 强制刷新缓存；模型是否提议还取决于任务与规则 |
| 不是 Git 工作区（64） | 进入业务 Git 仓库，不提供非 Git 绕过开关 |
| 参数错误（64） | 查 `/delegate:help` 或脚本 `--help`，任务作为一个参数传入 |
| 超时（124） | 看日志尾部与 Git 状态；核实任务规模、CLI 状态；人工决定是否重试 |
| 失败或空答复 | 查错误、日志路径、真实 diff；失败修改不会自动撤销 |
| 停在等待确认 | 检查全局与项目 AGENTS.md，给仅适用于交互流程的章节注明非交互豁免 |

`doctor` 不修改业务文件，但会刷新临时缓存。它的退出 0 表示诊断已完成，问题数量以文本为准。它只做中文启发式规则检查，不覆盖英文、所有项目级规则、网络、额度、模型权限或 token 过期。

## 架构

| 模块 | 职责 | 实现 |
|---|---|---|
| channel | 调用参数、沙箱、进程组期限/中断清理、答复与日志、Git 证据 | `codex-exec.sh` + `run_codex.py` |
| detection | 共享基础探测、缓存身份与有效期、原子写入、doctor | `backend.py` + `detect.py` + shell 入口 |
| routing | 按可用缓存注入确认要求与 skill 指针，判据由模型解释 | `prompt.sh` → `detect.sh --warm` → `route.sh` + skill |

UserPromptSubmit 注册一个串行入口，避免同事件多个 hook 并行读取旧缓存。缓存有效期 8 小时，绑定 CLI 路径、Codex home、插件根目录与版本；未来时间、旧格式、身份变化和坏文件都会失效。缓存不代表当前认证必然有效；真正执行前总会重新检查登录。

## 开发与验证

```bash
/bin/bash scripts/validate.sh
```

这是免费、离线的总入口：JSON / Python / Bash 语法、清单必填字段、判决器自检、全部 3 个 shell 产品测试和 2 个 Python 回归套。原有 channel **24** 条、detection 19 条、routing 9 条断言保留；新增回归覆盖认证、缓存、进程清理、失败验收和大日志。测试使用临时 Codex 桩，不读取真实凭据或发起模型请求。

```bash
/bin/bash plugins/delegate/tests/test-channel.sh
/bin/bash plugins/delegate/tests/test-detection.sh
/bin/bash plugins/delegate/tests/test-routing.sh
python3 -B plugins/delegate/tests/test-backend.py
python3 -B plugins/delegate/tests/test-channel-regressions.py
/bin/bash evals/propose-not-auto.sh --scaffold-only
/bin/bash evals/routing-fitness.sh --scaffold-only
```

以下命令**会调用模型并消耗额度**，不进入 validate。本版本准备期间已完成真实只读/写入、行为评估与帮助命令验证，样本范围见 [版本说明](docs/releases/v0.4.0.md)：

```bash
/bin/bash plugins/delegate/tests/test-channel.sh --live
/bin/bash evals/propose-not-auto.sh
/bin/bash evals/routing-fitness.sh
```

eval 用 `--plugin-dir` 显式加载当前源码，提前做原生清单校验；退出 0=PASS、1=FAIL、2=NORUN。routing-fitness 仅接受首个非空行的完整“判断：委托”或“判断：自己做”；正文中的示例不会被判为成功。`claude -p` 无法证明交互式“该提议时会提议”，且用户全局规则仍可能影响结果。

贡献时保持 Bash 3.2 兼容：`${VAR}`、空数组守卫 `${ARR[@]+"${ARR[@]}"}`，不使用 `cmd | grep -q`。修改行为需增加能复现故障的回归，再运行总验证。仓库目前没有 LICENSE 文件，未声明开源许可。
