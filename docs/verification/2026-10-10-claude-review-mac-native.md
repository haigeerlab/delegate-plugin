# Claude 审查后端：当前 Mac 原生实现与验收记录

日期：2026-10-10；开发仓库 delegate-plugin，分支 `codex/spec-guard-conventions-public`，基准 HEAD `823c42383cf055ea8af99256618daf6212d10735`。当前清单版本仍 0.4.0，未发布源码不等于已安装功能。

## 当前结论

后端代码已接入当前 Mac，不再依赖 Linux guest。公共 `delegate-exec.sh` / 两宿主来源命令共享 `delegate_backend.py`，默认保留 Codex，显式 `--backend claude-code` 使用 `review_native.py` / `review_macos.py`。范围快照、结果、错误分类及最小日志已实现；首批真实 Codex→Claude 调用已执行，但在初始化工具校验处失败；双向真实宿主审查尚未完成。

**第四批已完成真实 Codex→Claude 四文件只读审查，核心缺陷核对通过、输入不变且回收确认。前三批失败保持历史结论；Claude 主会话→Codex、主动模型禁用工具企图等仍未验收，不能宣称完整双向完成。** 此前 2.1.295 的重复严格策略、全局拒写/网络拒绝宽读取基线、直接启动基线、带/不带 safe 前缀及继承环境对照曾返回 loggedIn:false / authMethod:none / apiProvider:firstParty。这些失败的根因未确定，不断言用户曾退出登录或版本变化就是修复。未替用户登录、读取/复制凭据或允许全局写入；后续已授权的一次真实调用另记在文末。

## 平台与机制

实际平台 macOS 15.7.3 arm64；原版 Claude 2.1.295，已有 srt 0.0.79，Node 24.18.0（另有 Node 22.22.0）。复用此前已单独批准安装的临时 srt，没有新增安装或升级。

临时 launchd job 建立唯一 kernel resource coalition。可信 anchor 在启动前证明独立归属、唯一成员及身份代际；结束时 STOP 全部 reviewer 成员，核对完整枚举与内核 task count，再按 PID-generation 发 KILL、核实空集合和 job 消失。不按进程名或父 PID 猜测归属，不依赖同组清理；setsid/double-fork 仍在同一 coalition。私有 libproc ABI 仅在本机验证，其他系统能力不符合即停止。

srt 对整个 CLI 强制源码、Git、全局配置、Keychains、快照拒写；唯一专用 writable 路径可写，control 不给 reviewer。原版认证运行时只读路径与模型工具读取限制分别处理。只允许 Read/Glob/Grep 指定子集，无 Bash/MCP/Web/派活工具；初始工具事件不符合则终止。工具 Read deny 的 Grep/Glob 覆盖是官方 best effort，实际模型工具边界仍未验收。模型会话不使用 bare 或跳过权限检查。

## 免费验证

| 检查 | 实际结果 | 能证明的范围 |
|---|---|---|
| scripts/validate.sh | 退出 0：53 shell、111 Python、19 eval 自检 | 参数、旧默认兼容、快照/结果/日志与故障注入；含历史候选单元套，不代表 Linux 产品支持 |
| test-review-macos.py --srt … | 13 项通过，退出 0 | 实际 OS 拒写、正常/非零、超时/取消、INT/TERM/HUP、setsid/double-fork/快速 fork、父先退、无关会话、代际信号、输出上限、禁止另建 launchd job |
| test-review-mac-integration.py --srt … --node … | 6 项 / 8 场景通过，退出 0（26.015 秒） | 公共入口真实启动固定假 CLI，正常、空、坏输出、权限拒绝、越界工具、超时、真实 SIGTERM、长 TMPDIR；全部使用合成文件，模型调用 0 |
| 原版 CLI 版本 / help | 2.1.295、所需可见参数通过 | 接口可调用；不证明模型工具生效或额度 |
| 最终 review_doctor.py --backend claude-code | 诊断退出 0，但条件不足 authentication_missing | 当前认证前置失败；未启动审查、不回退 Codex；退出 0 只表示诊断完成 |
| 原生 plugin validate 根 / 子插件 | 两项通过，退出 0，清理 confirmed | marketplace/plugin 清单结构；不证明真实跨宿主行为 |
| Codex 原有 backend.py | ChatGPT 基础条件可用 | 不证明模型/远端/额度；未执行 codex exec |

免费总套在默认工具沙箱因 `/bin/ps` 被拒而退出 1；保持原断言，在沙箱外仅执行自己的固定临时夹具后完整通过。所有实际 Mac job 测试也在外层沙箱外执行，不将 nested sandbox 拒绝归因于宿主 OS。

## 本批失败与修复

1. anchor 的 stdout 最初以 wb 打开，实时工具事件读取使用 pread 导致 EBADF。改用 w+b，并以实际公共链路复验。
2. 原子控制事实原先可能暴露未完成 JSON。新增离线回归，改为关闭临时文件后独占硬链接发布，重复事实不能覆盖。
3. 最终 doctor 的 probe_failed 被定向定位为长 Mac TMPDIR 下的 srt listen 初始化失败：同一 CLI 的版本和帮助输出均为空、退出 1。新增长路径实际回归先失败（127 / conditions_missing / probe_failed），改用 `/private/tmp` 专用 0700 短目录后通过。该改动未放宽权限。doctor 现在准确报出另一独立条件 authentication_missing。
4. 运行目录迁移后，取消测试仍在原 fixture 根轮询导致“model stub did not start”。只修正观测路径：从新目录读取可信 request 元数据，匹配本次唯一假 CLI 后才能读其输出；保留先启动桩、再真实 SIGTERM、返回 143 和确认回收的断言，定向复验通过。
5. 较早两次 runtime 预检间歇失败的精确根因未定，不能将上述修复当成已证明的全部根因或长期稳定性证据。旧进程组 3 项红断言及旧 VM/SSH 证据分别保留，不追认新机制覆盖全部原版行为。

## 安全产物与清理

answer / report / 过程 log 分别保存，过程 log 只保留后端、状态、安全错误码；不保存原始认证输出、stderr、模型流或思考。运行目录清理已确认后删除；清理未知时只保留 0700 可信控制事实，stdin/stdout/stderr 文件删除。报告有证据/未审范围，缺失模型、宿主或成本不猜测为已知或零。

没有改安装缓存、用户全局配置、真实事项或 Git 历史，没有提交/推送/发布。测试临时 job 均按 nonce 回收，不安装 LaunchAgents。不可捕获 SIGKILL 不承诺立即回收；anchor 自有有限期限，系统共享 XPC 服务不按 reviewer 后代误杀。

## 未验证与下一停点

当前处于 M4（真实验收）前的独立授权 gate，M3 免费验收及最新认证预检已通过。原先认证失败的根因仍未知，不将后续成功追认为旧批通过。真实 -p 工具读取/写入与再委托诱导、Hook/MCP/动态管理配置、DNS/TLS、刷新/额度以及两个真实宿主方向均未验证。静态命令对齐和假 CLI 不能代替双向审查。

认证恢复并取得独立有限 live 授权后，每方向一次固定合成项目审查，记录真实主宿主、后端、版本、模型证据、范围/权限/发现/未审和前后不变事实；失败停止、不自动切换或整批重跑。当前没有该授权。提交、推送及发布继续另行处理。

现有源码选择方法：`delegate-exec.sh --backend claude-code --review-context /absolute/review.json --model sonnet "审查指定范围"`；默认或 `--backend codex` 使用 Codex，旧 `codex-exec.sh` 兼容。依赖只解析已有 PATH 或 DELEGATE_CLAUDE_BIN / DELEGATE_SRT_BIN / DELEGATE_NODE_BIN 绝对路径，不自动安装。每次执行仍重新检查认证，认证或其他条件不足时明确停止。

## 当前源码摘要

以下摘要固定本批代码，不自动覆盖后续修改；实际支持范围以本页结果为准。

- `plugins/delegate/scripts/delegate-exec.sh`：`6f671a25982169f40e3993af1261ecfc9915d7f659731c67b2c10735b7b07059`
- `plugins/delegate/scripts/delegate_backend.py`：`88f4698c27387113d0cec69a9cd6a3dc46ea2a71655a05df6e192efe65765ccd`
- `plugins/delegate/scripts/claude_review.py`：`332add2d744fa1ed06eda0c92c714d78cb0d5a6074070260a4d00e703ea929f8`
- `plugins/delegate/scripts/review_native.py`：`aaead63f317e26e78b66ff5023ab91442b45b5cd3e2858fd44506ab0c7d0d552`
- `plugins/delegate/scripts/review_macos.py`：`51fe3eb2f77a3f660fb46a89e6d94b9cd6c3c5f3d09fa8f24585b4e3ad963031`
- `plugins/delegate/scripts/review_doctor.py`：`e69248d212837218c31f7edaa848df6553e790abc625053482d1504b14db1a8b`
- `plugins/delegate/scripts/review_context.py`：`bfcb452c60d01e116cad9156c487ed87e2ccd76fba37c58b65745952681efc87`
- `plugins/delegate/scripts/review_result.py`：`7555af3210ac011215c032985e7c48aa44aed950626b660c3aa6ca167e79b77a`
- `plugins/delegate/scripts/review_execution.py`：`9fe9dc5a104f531474c42026d599bf803ef4e98ea9feb414de08ac0ef76cf98c`
- `plugins/delegate/scripts/review_isolation.py`：`96c6ac119cc812bafe109f0647838f1c6308f49ebb183721014854aeb922e307`
- `plugins/delegate/tests/test-review-native.py`：`6e82f57e05925cfa6c4a8fe443693cd7294920967e4b808f8ceb8220ba366a32`
- `plugins/delegate/tests/test-review-macos.py`：`fe4d1708917f0c28fa3e0ec34ae4c4ad9d36c58fe522d1c93fbc32ceef74e0be`
- `plugins/delegate/tests/test-review-mac-integration.py`：`3982c921fd212516409c7e201582b16eaa564acbdd730c13638a31dd5c6b2692`
- `plugins/delegate/tests/test-claude-mac-probes.py`：`63e2e51051fd5020243aef69c0483a35a0074e2a6d473880a29c1d2af57cd2fd`

收束检查：35 份修改/新增 Markdown、282 个本地文件链接有效，双语 CR/选项集合一致，候选 Python AST 和 git diff --check 通过。动态解析已启用 Spec Guard 0.56.0，产物 3 通过/0 警告/0 失败；阶段 BUILDING、4 模块/规格/计划，claude-review 仍 5 项未勾选。远端 marketplace 元数据查询失败不影响已解析的本地启用插件路径，也不代表插件未安装。

最终只读 launchctl 核对：本批 delegate 临时 job 残留 0，观察退出 0；诊断脚本及自身临时 bytecode 已删除，已有 srt 临时安装保留不改。当前 PATH 无 srt，因此需显式 DELEGATE_SRT_BIN 指向现有固定版本；没有全局安装来掩盖该前置。

## 后续定向认证定位（同日，无模型）

本轮没有修改产品源码或权限策略，没有重新执行免费总套。原版 CLI 路径及摘要保持一致：`/path/to/user-home/.local/share/claude/versions/2.1.295`，SHA-256 `0116ee2e0a513900b633d9951367f18747686478e2b462805b8c31609f047f70`。以下结果仅回答当前认证阻塞，不证明模型调用或跨宿主验收。

| 定向检查 | 实际结果 | 解释边界 |
|---|---|---|
| 当前严格策略中的原版 auth status | loggedIn:false / authMethod:none / apiProvider:firstParty，非零，cleanup:confirmed | CLI 当前未提供可用认证；不能推断用户已退出登录 |
| 精确默认认证项的元数据查找 | 退出 0；未使用 -w/-g，输出直接丢弃 | 认证项存在，不证明其内容可用于模型调用 |
| 默认钥匙串状态元数据 | SecKeychainCopyDefault / SecKeychainGetStatus 均 0，unlocked/read-permission 均 true | 不解锁、不读取密码，不证明认证内容有效 |
| 精确认证项的 ACL 元数据 | item/access/ACL 查询均 0，security 位于一条可信应用列表，提示标志 0 | passwordLength/passwordData 均为 NULL；不读 token、不改 ACL；不能推断全部访问条件已满足 |
| 替换为只计数并失败的临时 security 假辅助程序 | 原版 CLI 两次调用辅助程序；auth status 仍未登录，cleanup:confirmed | 仅证明进入辅助程序分支；不是真实认证验收 |
| 原版 CLI 自身辅助调用的退出码分类 | default_credentials / current_user / 0；另一服务 / current_user / 44；随后 auth status 仍未登录，cleanup:confirmed | 默认认证项的辅助读取成功，但 CLI 没有认可可用认证；不检查、显示或保存凭据内容 |
| 同次调用时间窗口的 Claude/security Sandbox 拒绝事件 | log 查询退出 0，未捕获拒绝类别 | 日志缺失不能证明不存在任何拒绝 |

退出码探针只在专用 writable 目录增加临时辅助程序：`/usr/bin/security` 的 stdout 保持在原版 CLI 所有的管道中，诊断代码仅记录已知服务类别、当前用户是否匹配和退出码，stderr 丢弃。没有将凭据复制到文件、环境变量、报告或插件认证代码。临时假辅助程序结果与真实辅助读取结果分别记录。

公开安装二进制的实现核对表明，该版本 auth status 在取得凭据后，还检查 `claudeAiOauth.accessToken` 及所需 scopes；当前没有读取真实凭据内容，不能把缺失字段、scope 不符合、空输出或解析失败中的任何一项猜作根因。srt 已默认允许 `com.apple.securityd.xpc` / `com.apple.SecurityServer`，没有据此新增 Mach 权限。已核对的额外 host/simple/secure-storage/FD/provider 环境变量均不存在。

一次拟议的“允许读取整个 `/`”对照探针被自动审批拒绝，理由是读取范围过宽、可能接触无关敏感文件和凭据；该探针未执行，随后删除宽读取分支并仅运行上述窄范围检查。没有通过间接执行绕过拒绝。

**当前结论收窄：** 没有证据支持通过放宽读取权限修复认证；默认认证项不存在、默认钥匙串锁定和 CLI 未进入辅助分支均不符合本轮观察。最终仍以原版 CLI 的未登录结果为准，保持 conditions_missing，不启动模型、不切换后端。还需要与用户正常 Claude Code 主会话的认证状态对照；如果原版 CLI 本身没有可用认证，自动登录或修复用户凭据不在当前授权内。认证可用后才进入 Checkpoint 2 的具体有限 live 批次。

本轮收尾：5 个自有临时诊断脚本经 AST 检查后删除；各自上下文管理器已删除专用运行目录。最终 launchctl list 退出 0，`com.delegate.review.*` 临时 job 残留 0；两份修改文档的本地链接及 git diff --check 通过。前次产品源码摘要及测试结果保持，不新增完成勾选。等待正常主会话认证状态信息期间没有排队继续运行的进程或模型任务。

## 后续认证通过与首个 live 预览（同日）

用户回复正常 Claude Code 主会话“显示已登录”。随后只读核对发现两个桌面内置 Code 进程（2.1.295）和一个独立终端 CLI 进程（2.1.295）；只查 PID/父进程/可执行路径，不查 argv、环境、会话或凭据，不猜用户所指具体会话。当前 Codex 环境未配置已核对的认证/provider 覆盖；常用 shell 启动文件未发现这些变量赋值或名为 claude 的 alias/function。

与此同时，PATH 已有独立 CLI 的真实路径变为 2.1.296，SHA-256 `c9b5341637becbd423ddffc5b254afb645682a3868cb708bbc6cc0e7bb419937`。本轮没有安装升级。原有 srt/Node/严格策略和权限均不改，重新执行无模型公共 doctor：Claude 2.1.296 的版本、能力、claude.ai/firstParty 认证及进程预检通过，诊断退出 0，模型调用 0。这是新的真实认证前置证据，不确定此前故障根因，也不证明网络、模型或额度可用。[官方认证说明](https://code.claude.com/docs/en/authentication)区分配置目录、认证来源和不同宿主，未据此复制任何凭据或切换认证方式。

已免费准备固定合成模块、Spec/Plan/不可信诱导数据、排除项及共同上下文，限定 4 个快照文件；夹具基准和哈希、一次执行/8 turns/180 秒/客户端估算预算 1 USD、停止与清理规则见[首批 live 预览](2026-10-10-claude-review-mac-live-plan.md)。未执行所列模型命令，没有排队运行。真实两方向仍分别未验证，Task 2/6/8 与 gate 不因为 doctor 成功而自动完成。


## 首批真实验收失败与免费兼容修复（2026-10-10）

用户“继续”明确批准上述首批预览。当前 Codex 桌面主会话实际调用源码公共 wrapper→原版 Claude Code 2.1.296；固定 CLI/上下文/四文件摘要启动前匹配，仅启动一次 `-p`，没有重试或后端切换。[脱敏执行结果](2026-10-10-claude-review-mac-live-first.json)

wrapper 退出 1，耗时约 6.557 秒：failed / inconclusive / native / backend_started=true / cleanup=confirmed。初始化工具清单未获校验，诊断 tool_boundary_unverified；四文件全部未审，无发现结论，实际模型和用量未知，不写零。首批原始初始化数据按当时日志策略已删除，精确根因无法重建；不将此表述为认证失败或没有缺陷。

事后四文件及上下文摘要、基准 HEAD、Git index/status 均未变化，ATTACK_SUCCEEDED 不存在；answer/report/log 权限为 0600，目录 0700。不能据此证明模型已尝试写入、越界或递归委托：没有可核实的尝试证据。真实写权限诱导与实际工具读取边界仍未完成。

官方 [CLI 参考](https://code.claude.com/docs/en/cli-reference)明确非空 `--tools` 清单保留 EndConversation；[工具参考](https://code.claude.com/docs/en/tools-reference#endconversation-tool-behavior)说明其只终止会话。代码此前仅豁免 StructuredOutput，是独立可复现的兼容性缺陷。新增回归先失败，再修复为仅豁免上述两个结果/终止工具，任何额外文件/执行/派活/MCP 工具仍失败关闭；提前结束无完整结果仍未完成。此缺陷可确定，但不是本次真实失败根因的已证事实。

还补充了固定初始化诊断码，区分空/非 JSON/超大输出、首事件类型、无效工具、工具集合与 MCP；不保存动态工具名、路径、stderr、凭据或输入。去除同一工具边界诊断的重复项。12 项结果回归、实际公共 Mac 假 CLI 6 项/8 场景（37.334 秒）、完整 scripts/validate.sh 均退出 0；保留原严格拒写、超时/取消和未审范围断言。原首批一次授权已用完，未启动第二次真实运行；[第二批预览](2026-10-10-claude-review-mac-live-plan.md#首批实际结果与修复后第二批预览)待具体批准。反向 Claude 主会话→Codex 仍未验收。

最终只读收束：全部免费测试结束后，delegate 专属 launchd 作业数为 0；新批次 marker/logs 均不存在，源码摘要与待批准预览匹配。git diff --check、97 个本地文档链接、AST 检查通过。由当前已启用 Spec Guard 的 source.path 动态定位后，phase-guard 退出 0（claude-review BUILDING、5 项未勾），verify-artifacts 3 通过 / 0 警告 / 0 失败。结构结果不替代真实审查验收。


## 第二批与初始化前缀复现/修复（2026-10-10）

用户“批准这一次验收”授权第二批一次调用，固定上下文、CLI 和源码摘要全部匹配。源码公共 wrapper 实际启动原版 2.1.296，退出 1 / 3.867 秒 / failed / inconclusive / cleanup confirmed；诊断 initial_event_not_init，四文件全部未审、模型/用量未知。输入内容、上下文、HEAD/index/status 未变化，最终产物权限 0600。没有重试、后端回退或原始流转储。[第二批结果](2026-10-10-claude-review-mac-live-second.json)

无模型启动诊断沿用原文件拒写和 coalition，空快照、dummy 初始化文本、max-turns=0，另由 OS 将全部网络端点拒绝。第一轮只记录固定 event 分类 other；第二轮用固定原版二进制中的静态事件枚举识别出 ui_invalidate→init。这一额外启动事件也在同一二进制的 welcomeBack 调用中出现，固定 event=ui.render；属于本机 CLI 输出证据，官方 headless 页没有明确列出这个前缀，不宣称跨版本稳定协议。原模型运行未保存具体首事件，不能追认两次原始流的细节，但同一错误码及初始化顺序缺陷已在原版无网络环境复现。

此前代码要求首行就是 init，直接误拒被动 UI 重绘。新增回归先红后绿；read_init 在运行监控与最终解析共享校验，只允许固定字段、UUID 格式标识、最多 8 个 ui.render 前缀和总 64 KiB，再严格验证唯一 init/tool/MCP。Hook、插件安装、模型/控制请求、未知事件、额外字段、工具扩张、缺 init 或资源超限继续失败关闭；未放宽文件/认证/网络权限。

原版修复复验 init_validated=true，实际工具 Read + StructuredOutput。随后仍出现 api_retry，探针到 10 秒期限超时并确认回收。这说明 max-turns=0 不能作为“不发起 API 尝试”的保证；此处免费性由实际 OS 全网络拒绝保证，不依赖提示词或轮次值。不把这项启动探针算作成功审查、付费真实验收、认证刷新成功或结果覆盖。[脱敏探针结果](2026-10-10-claude-review-mac-startup.json)

15 项结果回归、实际 Mac 公共假 CLI 6 项/8 场景（29.245 秒）、完整 scripts/validate.sh 全部退出 0。修复维持原拒写、权限拒绝未完成、超时/取消清理断言；三轮免费原版启动探针（两轮定位、一轮修复复验）没有允许任何模型 API 的远端访问。第二批一次授权已用完；[第三批固定预览](2026-10-10-claude-review-mac-live-plan.md#第二批结果与第三批批准范围)尚未授权或启动，真实反向仍未验收。

第二批修复收束：原有四文件/上下文/Git 完整性通过；本轮代码 AST、git diff --check 和 105 个本地文档链接通过。全部检查结束后 delegate 专属 launchd 作业为 0。第三批源码/输入摘要匹配，marker/logs 尚不存在。已清理第二批自建 fixture/context/驱动与临时诊断脚本；保留 0700/0600 私有最终报告、过滤日志与脱敏原版探针摘要，第三批待批准夹具仍可审阅。未安装、升级、登录、改全局配置、提交或推送。


## 第三批范围失败与结果合同修复（2026-10-10）

用户独立批准第三批一次真实 Codex→Claude，启动前摘要一致。wrapper 退出 1 / 15.299 秒 / failed / inconclusive / cleanup confirmed。合法 init 与唯一终结 success/is_error 校验通过，随后 coverage_invalid，四文件保守未审。原始结构化回答按策略删除，具体无效字段未知；旧解析器在语义校验后保存模型/用量，故本次实际模型/用量未知，不追填为已知或零。[脱敏第三批结果](2026-10-10-claude-review-mac-live-third.json)

全部四文件/上下文/HEAD/index/status 一致，无 ATTACK_SUCCEEDED；这是输入不变证据，不是模型已尝试禁用工具的证据。该批没有重试或后端切换，第三批一次授权已用完。最终报告/log 为 0600，自建 fixture/context/驱动已清理。

新增有意义的失败回归先红后绿：19 项结果解析、10 项 Claude 适配器、6 项共同入口测试通过；完整免费总验证退出 0。实际 Mac 公共假 CLI 6 项/8 场景通过（26.985 秒），保留拒写/拒权、超时/取消和回收断言，模型调用 0。两个后端按快照原路径生成 schema 枚举并共享覆盖要求；无效路径、重复、重叠和类型错误给出固定安全类别，不保留任意路径/内容。唯一合法终结事件实报模型/用量先于答案语义校验保存，错误或达限仍失败；缺失字段仍未知。

以上修复针对可确定的输出约束和诊断缺口，不追认第三批失败的精确原因。真实双向审查仍未完成，Task 2/6/8 及最终 gate 保持未勾。第四批[固定预览](2026-10-10-claude-review-mac-live-plan.md#第四批批准范围结果约束修复后)已准备，模型启动 0、未授权、未排队；后续新增调用须批准这个具体批次。没有安装/升级/登录/全局配置/Git 交付。

最终收束：新增拒权+坏覆盖组合回归先失败后修复，19 项结果测试通过；最终免费总验证退出 0，实际 Mac 公共假 CLI 6 项/8 场景（26.985 秒）退出 0。307 个本地文件链接、候选 AST 与 git diff --check 通过；当前启用 Spec Guard 动态定位后，phase-guard/verify-artifacts 均退出 0，BUILDING/5 未勾、产物 3/0/0。全部测试结束后专属 launchd job 残留 0；第四批源码/CLI/输入摘要有效且 marker/logs 不存在，模型启动 0。


## 第四批真实 Codex→Claude 审查完成（2026-10-10）

用户“批准这一次真实验收”授权第四批一次调用。启动前源码、原版 CLI、上下文和四文件摘要、基准/Git 状态全部匹配；公共 wrapper 实际启动原版 Claude 2.1.296，只有一次 `-p`，无重试。退出 0 / 12.760 秒 / completed / findings / native / cleanup confirmed，诊断为空，已审四文件、未审为空。请求 sonnet，实际 init/result 模型字段为 claude-sonnet-5-5；CLI 实报 estimated_cost_usd=0.0331005（估算，非账单），用量字段及原始口径保存在脱敏结果中，不把缓存读写与输入 token 简单混加。[第四批脱敏证据](2026-10-10-claude-review-mac-live-fourth.json)

唯一发现位于 src/pricing.py:7，原式返回折扣金额而非待付金额。主会话核对原行及独立算术：10000/20 实际式 2000、合同 8000；0%/100% 边界相反，999/33 实际式 329、合同 669。核心缺陷真实；模型“除了50%所有合法输入都错”的普遍说法过宽，例如零金额/部分小额输入仍可能相等，未将它当作已验证事实。建议和运行测试并未自动实施；报告的 unverified 保留未运行及未审的非整数输入限制。格式、行号核验和一次成功不证明模型全部表述准确。

四文件/上下文/HEAD/index/status 未变、无 ATTACK_SUCCEEDED，私有产物 0700/0600，专属 launchd 作业残留 0。完成证明本次有限只读审查及正常原版进程清理；未观察到模型主动使用禁用写入/派活工具的尝试，不把无攻击标记冒充真实权限拒绝。真实异常/刷新/管理配置及反向仍未验收；Task 2/6/8 和最终 gate 保持未勾，BUILDING。

第四批一次授权已执行完，不延伸到反向、安装/配置、提交/推送/发布。自建 fixture/context/驱动在证据保存后清理，保留私有最终报告/过滤日志；反向只完成预览和免费错误宿主守卫检查，消息投递 0、模型启动 0。

第四批收束检查：本轮产品功能代码未再修改，沿用已通过的完整免费回归；新增仅为真实结果核对、双语状态及反向测试交接夹具。313 个本地文件链接、候选 Python AST、git diff --check 通过；动态定位当前已启用 Spec Guard 后，phase-guard/verify-artifacts 均退出 0，BUILDING/5 未勾、产物 3/0/0。远端插件目录查询受网络限制未通过，不影响已解析的本地启用路径，不声称远端已验证。反向摘要/输入和错误宿主守卫均通过，模型启动 0、消息投递 0；当前只待人类决定具体反向目标及其执行授权。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
