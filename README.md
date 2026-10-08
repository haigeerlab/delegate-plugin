# delegate

简体中文 | [English](README.en.md)

Claude Code 插件。把范围、方案和验收目标已经明确的执行与查证交给 **Codex CLI**，主会话收到最终答复，过程日志留在本机。

主会话负责需求澄清、方案判断与最终验收。插件只接受 ChatGPT 登录的 Codex，目的是减少主会话携带的过程上下文；实际使用哪个账号的额度取决于 Codex 登录账号，不保证节省总费用或总 token。

仓库：[haigeerlab/delegate-plugin](https://github.com/haigeerlab/delegate-plugin) · 当前发行：[v0.4.0](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.4.0) · [文档索引](docs/README.md)

## 目录

- [使用场景与边界](#使用场景与边界)
- [前置条件](#前置条件)
- [快速开始](#快速开始)
- [命令与参数](#命令与参数)
- [输出与验收](#输出与验收)
- [更新与卸载](#更新与卸载)
- [故障排查](#故障排查)
- [架构与文档导航](#架构与文档导航)
- [开发贡献与反馈](#开发贡献与反馈)
- [报告 Bug](#报告-bug)
- [许可](#许可)

## 使用场景与边界

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

用户直接输入明确的委托命令也构成该任务的执行授权。命令和 skill 要求确认，这是模型指令约束；wrapper（调用脚本）本身没有不可绕过的授权令牌。

支持单次、非交互、同步委托，选择模型与推理档、默认只读、授权后可写、日志隔离、失败诊断和 Git 变更概览。当前两种模式都**只接受 Git 工作区**。

插件不提供后台任务、排队、断点续跑、自动重试、多后端或团队配额管理；不负责自动提交、推送或发布，也不保证结果正确或模型遵守全部指令。

## 前置条件

| 依赖 | 要求 |
|---|---|
| Claude Code | 支持插件，且可在终端运行 `claude` |
| Codex CLI | 可在同一环境的 PATH 中运行 `codex`，使用 ChatGPT 登录 |
| Python 3、Git、Bash | 运行脚本所需；兼容 macOS 自带 Bash 3.2 |
| 业务项目 | Git 工作区；允许已有未提交修改，也允许尚无提交的仓库 |
| Node.js、npm | 使用下方 npm 安装 Codex 的方式时需要 |

v0.4.0 的验证环境为 Claude Code 2.1.291、Codex CLI 0.160.0、Python 3.10、Bash 3.2。这是已验证环境，未声明更早版本的最低兼容线，也未验证 Windows。

认证状态通过 CLI 检查，不以 `auth.json` 是否存在为依据。API key 登录和未知认证状态会被拒绝；执行时清除 `OPENAI_API_KEY`、`CODEX_API_KEY`，并指定 ChatGPT 认证和 OpenAI provider。凭据存储由 Codex CLI 管理，可能使用 `CODEX_HOME` 下的文件或系统钥匙串。[Codex 认证说明](https://learn.chatgpt.com/docs/auth)

## 快速开始

### 1. 安装 Codex 并登录

在终端运行：

```bash
npm install -g @openai/codex@latest
codex --version
codex login
codex login status
```

`codex login status` 应显示 `Logged in using ChatGPT`。插件检测到这类明确状态才允许执行。

### 2. 安装插件

在终端运行：

```bash
claude plugin marketplace add haigeerlab/delegate-plugin
claude plugin install delegate@delegate-marketplace
```

本仓库是一个 marketplace，内部插件名为 `delegate`；安装标识是 `delegate@delegate-marketplace`。

### 3. 进入业务项目并诊断

把下面路径替换成你的业务 Git 项目，在终端启动新的 Claude Code 会话：

```bash
cd /path/to/your-project
claude
```

在 **Claude Code 会话**中输入：

```text
/delegate:doctor
```

doctor 会刷新本地安装与登录状态，检查部分中文全局 AGENTS.md 规则。它不发起模型任务；退出 0 表示诊断完成，应阅读问题数量和文字原因。基础条件可用不等于远端、额度或模型权限已验证。

### 4. 执行首次只读委托

在 Claude Code 会话中输入：

```text
/delegate:delegate 读取当前项目的 git status --short，解释工作区状态；不要修改文件
```

这个命令会发起真实 Codex 模型请求并消耗登录账号的额度。正常结束后，应看到最终答复、模型/推理档提示、过程日志路径和字节数。未指定模型时显示“配置默认”，不代表 wrapper 已读取到实际模型名称。

有写入需求时，明确授权当前任务后使用 `--write`，并按[输出与验收](#输出与验收)检查真实 diff 和测试结果。

## 命令与参数

终端中的 `claude plugin ...` 是安装管理命令；下表 `/delegate:...` 是 Claude Code 会话入口。插件使用完整命名空间，以当前宿主加载的命令列表为准。[官方组件说明](https://code.claude.com/docs/en/plugins/components)

| 入口 | 作用 | 是否执行 Codex 任务 |
|---|---|---|
| `/delegate:delegate [选项] <任务>` | 委托一个明确任务 | 是 |
| `/delegate:doctor` | 刷新基础探测，检查部分全局中文规则 | 否，仅 CLI 状态探测 |
| `/delegate:help` | 参数、示例、限制和故障帮助 | 否 |
| `/delegate:delegate-routing` | 宿主支持时可调用的分流判据 skill | 自身只提供判据，仍需确认 |

```text
/delegate:delegate 审查 src/payments 的错误处理；只报告有代码证据的问题
/delegate:delegate --write 按已确认的方案修复空指针；运行相关测试并报告结果
/delegate:delegate --model <模型 slug> --effort high 梳理登录链路
```

| 参数 | 约定 |
|---|---|
| 无模式开关 | `read-only` 沙箱 |
| `--write` | `workspace-write` 沙箱；须用户当前轮明确授权 |
| `--model <slug>` | 透传模型名称；省略则采用 Codex 配置，非法值由 CLI 报错 |
| `--effort <level>` | 透传推理档；合法值取决于模型和 CLI 版本 |
| `--` | 终止选项解析，允许任务以 `-` 开头 |
| `--help` / `-h` | wrapper 的本地参数帮助，不依赖 Codex；不是新增会话命令 |

需要直接运行源码脚本时，在**业务 Git 项目目录**执行；任务必须是一个完整、正确引用的参数：

```bash
bash /path/to/delegate-plugin/plugins/delegate/scripts/codex-exec.sh --write "按已确认方案修复并测试"
```

Claude 的 Bash 工具 timeout 设为 `600000` 毫秒。wrapper 的 Codex 执行期限默认和上限为 **540 秒**；`DELEGATE_TIMEOUT_SECONDS` 可设置更短的正整数，超过 540 会被截断，非法或非正值回落 540。认证探测每项最多 5 秒，进程组清理最多等待 2 秒后强制终止。执行期限不包括前置探测与后置 Git 检查；自行脱离进程组的进程不保证被回收。

## 输出与验收

成功时返回 Codex 最终答复、模型/推理档提示、日志路径与字节数。写模式额外返回：

- 基线 HEAD（含尚无提交的仓库）和原有未提交变更数量；
- `git status --short`；
- `git diff --stat` 与 `git diff --cached --stat`。

执行失败、超时、空答复或中断后，**已经开始的写模式任务仍输出 Git 验收块到 stderr**。失败不会自动回滚。统计可能混有用户原有修改，不能区分修改归属；必须查看真实 diff 和测试结果。Git 检查本身失败时按错误输出处理，不能把概览当作完整验收。

过程日志与答复位于 `${TMPDIR:-/tmp}/delegate/`，目录 0700、新文件 0600。完成或失败后尽力保留最近 **50 组** `.log/.answer`；清理失败不改变任务退出码。数量限制不限制单个文件体积。失败回显日志尾部最多 40 行 / 16KiB，并给出完整路径；按需读取少量行，避免把整个日志带回会话。

默认只读与可写权限由 Codex 沙箱及宿主配置实现。`workspace-write` 的可写范围可能包括临时目录和额外根目录；“不提交、不推送、不发布、不越范围访问网络”等是行为指令，不能替代 OS 沙箱或宿主权限配置。

## 更新与卸载

### 从远程 marketplace 安装

手动更新后启动新会话，使更新后的插件生效：

```bash
claude plugin update delegate@delegate-marketplace
```

修改你本机另一个源码目录不会改变远程安装的缓存副本；远程安装的插件更新还取决于插件版本是否变化。第三方 marketplace 的宿主后台自动更新默认关闭，用户或管理员可以开启。delegate 自身没有自动升级功能；不能把这一点理解为宿主永远不会自动更新。[官方更新说明](https://code.claude.com/docs/en/plugins/host-marketplace)

### 本地源码与开发加载

先克隆仓库，再从**仓库根目录**注册本地 marketplace：

```bash
git clone https://github.com/haigeerlab/delegate-plugin.git
cd delegate-plugin
claude plugin marketplace add "$PWD"
claude plugin install delegate@delegate-marketplace
```

当前 Claude Code 对本地路径 marketplace 中的相对路径插件可直接加载源码；修改后在新会话或 `/reload-plugins` 中生效。此行为与远程安装缓存不同，具体支持取决于宿主版本。[官方本地加载说明](https://code.claude.com/docs/en/plugin-marketplaces)

开发和评估时，也可在业务 Git 项目中显式加载源码插件目录：

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

已注册同名 marketplace 时，应先检查现有来源；本地加载与远程安装是替代方式，不需要同时安装两份。发行源码由 `v0.4.0` 标签固定，`main` 会继续变化。

### 卸载

在终端运行，然后启动新会话：

```bash
claude plugin uninstall delegate@delegate-marketplace
```

如果也不再使用 marketplace，可继续移除：

```bash
claude plugin marketplace remove delegate-marketplace
```

卸载不会回滚此前的业务文件修改。临时日志和探测缓存位于上文的临时目录中，由本插件的运行清理和系统临时目录策略处理。

## 故障排查

| 症状 | 检查与下一步 |
|---|---|
| 命令找不到 | 检查已加载插件、命名空间和安装来源；更新后启动新会话，开发时可用 `--plugin-dir` |
| Codex 缺失或版本命令失败 | `codex --version`；修复安装与 PATH |
| 未登录、API key 登录或未知认证 | `codex login status`；执行 `codex login` 选择 ChatGPT 登录 |
| 登录后仍不提议 | `/delegate:doctor` 强制刷新缓存；是否提议还取决于任务与模型规则 |
| 不是 Git 工作区（64） | 进入业务 Git 仓库；没有非 Git 绕过开关 |
| 参数错误（64） | 查 `/delegate:help` 或脚本 `--help`；直接运行脚本时把任务作为一个参数 |
| 超时（124） | 看日志尾部和 Git 状态，核实任务规模；人工决定是否重试 |
| 失败或空答复 | 查错误、日志路径和真实 diff；失败修改不会自动撤销 |
| 停在等待确认 | 检查实际生效的全局/项目 AGENTS.md，给仅用于交互的流程章节注明非交互豁免 |

wrapper 退出状态：64=参数/非 Git 工作区；127=CLI/Python 基础条件失败；124=执行超时；129/130/143=HUP/INT/TERM 中断；空答复为 1，其他执行失败保留其非零状态。doctor 始终退出 0，按文字中的问题数量判断。

doctor 会刷新临时缓存，不修改业务文件。它只做部分中文全局规则的启发式检查，不覆盖英文或全部项目级规则，也不验证远端连接、额度、模型权限或 token 是否仍有效。当前运行时诊断和 skill 指令以中文为主；双语文档不改变这些输出。

## 架构与文档导航

| 模块 | 职责 | 实现 |
|---|---|---|
| channel（通道） | 调用、沙箱、进程组期限/清理、答复与日志、Git 证据 | `codex-exec.sh` + `run_codex.py` |
| detection（探测） | 共享基础检查、身份绑定缓存、原子写入、doctor | `backend.py` + `detect.py` + shell 入口 |
| routing（路由） | 按有效缓存注入确认要求与 skill 指针 | `prompt.sh` → `detect.sh --warm` → `route.sh` + skill |

UserPromptSubmit 使用一个串行入口。缓存有效期 8 小时，绑定 CLI 路径、Codex home、插件根目录与版本；未来时间、旧格式、身份变化和坏文件都会失效。缓存不保证当前认证有效，真正执行前总会重新检查登录。

阅读顺序和两种语言的对应页见[文档索引](docs/README.md)。设计见 [DESIGN.md](DESIGN.md)，模块职责见[能力图](spec/CAPABILITY-MAP.md)，精确合同见[通道](spec/channel.md)、[探测](spec/detection.md)和[路由](spec/routing.md)规格。发行变化见 [v0.4.0](docs/releases/v0.4.0.md)，后续修改见[未发布记录](docs/releases/unreleased.md)。

## 开发、贡献与反馈

开发流程与两类 AI 项目约定见 [开发流程](docs/development-workflow.md)；当前中文规格使用 `spec/<id>.md`，历史记录与当前维护任务分开。

从**本仓库根目录**运行免费离线验证：

```bash
/bin/bash scripts/validate.sh
```

总入口包含语法、清单必填字段、判决器自检、3 个 shell 产品套及 2 个 Python 回归套。基线为 channel 24 条、detection 19 条、routing 9 条断言和 17 个 Python 回归测试。免费总验证不发起模型请求；doctor 规则测试已自行配置 CLI 桩、合成登录状态和临时日志，不再依赖外层 Codex 的安装或登录。[F8 实际修复验证](docs/verification/2026-10-08-f8-applied.md)包含无外层 CLI 和外层拒绝登录的结果。

开发约定、单独测试入口、付费 live 验证和双语维护规则见 [贡献指南](CONTRIBUTING.md)。问题和建议统一通过 [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues) 反馈，Bug 提交步骤见下节。

## 报告 Bug

遇到插件异常时，请在本仓库的 GitHub Issues 中报告：

1. 先[搜索已有问题](https://github.com/haigeerlab/delegate-plugin/issues)，看是否有相同现象或解决方法；已有相同问题时，可补充你的复现信息。
2. 登录 GitHub，打开[新建 Issue](https://github.com/haigeerlab/delegate-plugin/issues/new)，用一句话概括故障作为标题。
3. 复制下方清单，填写能复现问题的信息后提交。中文或英文均可。

```text
环境：操作系统、插件、Claude Code、Codex CLI、Python 和 Bash 版本
安装方式：远程 marketplace / 本地路径 / --plugin-dir
运行的命令：注明只读或 --write，移除任务中的私密内容
复现步骤：从什么状态开始，依次执行了什么
预期结果：应该发生什么
实际结果：发生了什么，是否每次都能复现
退出状态与错误：保留关键错误原文
/delegate:doctor：相关诊断片段
若涉及写入：Git 状态、是否有原有修改，以及失败后留下了哪些修改
```

版本可通过 `claude --version`、`codex --version` 等命令查看。提交前移除凭据、个人路径和业务源码；不要上传 `auth.json`、API key 或完整过程日志。更多说明见[贡献指南的报告问题章节](CONTRIBUTING.md#报告问题与提出建议)。

## 许可

本项目源码及随附文档采用 [MIT 许可证](LICENSE)，版权声明为 `Copyright (c) 2026 haigeerlab and contributors`。允许商业使用、修改和分发，分发时须保留版权声明与许可声明；软件按原样提供，不作担保。此处为中文摘要，以 LICENSE 中的英文标准全文为准。

插件目录内附有同文 [LICENSE](plugins/delegate/LICENSE)，确保单独分发或安装插件时也携带许可。
