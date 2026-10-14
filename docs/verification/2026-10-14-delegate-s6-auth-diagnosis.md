# S6 后续：零模型认证路径核对

日期：2026-10-14。位置：`/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，模块 `claude-review`，阶段 BUILDING。用户“继续s6”承接[S6失败收束](2026-10-14-delegate-s6-read-boundary-result.md)的免费只读认证诊断，不重用已消费的模型次数。

## 已执行的核对

1. 复核源码调用链：`claude_review.preflight` 运行 version/help/auth status；审查才运行 `-p`。二者复用 NativeRunner 的 HOME、环境、文件系统边界和 SAFE_PREFIX。S6 报告含 CLI 版本和 claude.ai/firstParty，说明其本地预检通过；终态的 `claude_api_authentication_failed` 发生在实际审查调用后。没有保留 HTTP 状态码或原始错误，不能据类别推断为某个具体 401、过期或服务故障。
2. 新增一次无模型 `auth status --json`，使用 S6 固定的原版 CLI 2.1.296、Node 24.18.0、SRT 0.0.79，并核实二进制摘要。复用 NativeRunner/MacBoundary，网络 allowlist 收紧为空，HOME 仍只读，临时目录专用且 0700；不使用 `-p`、登录、恢复会话、更新或写配置。结果 completed、cleanup confirmed、loggedIn=true、authMethod=claude.ai、apiProvider=firstParty、configDirectory 确为默认目录。五项被观察设置摘要未变；不输出账号、凭据或原始 auth JSON/stderr。
3. 只观察认证路径存在性/模式，未读取凭据内容：默认 `.claude`、`.claude.json` 和 Keychains 存在，无 `.claude/.credentials.json` 回退文件，无 `~/.config/anthropic/active_config`。当前进程未设置已检查的自定义认证/provider/configDirectory 环境变量；NativeRunner 实际使用明确的最小环境。路径元信息仅描述当前时点，不证明 S6 时的 token 内容或有效性。
4. 对 S6 启动标记的 UTC 时间 `08:53:54.963716`，只读查询 `08:53:50–08:54:10` 的 sandboxd 拒权事件，并过滤 CLI 版本名/专用运行目录。默认工具沙箱明确禁止 `log`，退出64；随后通过只读权限执行同一查询，退出0，没有匹配记录。原始系统日志不留存。缺少匹配日志不证明没有拒权，更不证明认证刷新成功。

机器摘要见[JSON](2026-10-14-delegate-s6-auth-diagnosis.json)。私有探针及安全结果位于 `.agent/acceptance/s6-auth-diagnosis/`，0600 文件、0700 目录；本轮模型调用为 0，产品源码和安装缓存未改。

## 官方依据及结论边界

[CLI 参考](https://code.claude.com/docs/en/cli-reference)说明 auth status 的登录状态、退出码和 configDirectory 字段。本次禁网仍取得 loggedIn=true，直接说明这项成功不能当作远端认证有效的证据。

[认证文档](https://code.claude.com/docs/en/authentication#credential-management)说明 macOS 钥匙串、文件回退以及不同配置目录使用不同登录；[续期说明](https://code.claude.com/docs/en/authentication#renew-an-expiring-login)说明可在 `/status` 的 Login 行观察过期状态，登录过期且无法刷新会令模型请求失败。[官方登录故障说明](https://code.claude.com/docs/en/troubleshoot-install#not-logged-in-or-token-expired)还说明并行会话共享已保存登录并协调刷新。这些是候选机制，不是本次根因的证明。

目前已核实：实际后端/固定 CLI 正确、默认认证目录可读、本地 claude.ai 登录存在、已观察设置不变、进程回收确认。仍未知：服务是否接受 S6 当时的凭据、token 是否过期/撤销、是否需要刷新、刷新与隔离是否存在冲突。没有证据就不修改权限、不要求退出所有会话、不自动登录或复制凭据。

## 下一步

已请求用户仅反馈其平常终端 Claude Code `/status` 中 Login 的有效/Expired/缺失状态，区别于先前 Claude Desktop“显示已登录”的事实，不索取凭据或要求重新登录。若显示过期，可先明确需要用户处理的原版 CLI 登录条件；若有效，也不直接判定隔离故障。新增服务验证或付费审查必须先准备具体范围与诊断目标，不能在条件未变时重复 S6、删除原失败或消费另一个模型掩盖认证失败。

本轮只完成免费诊断，不宣称修复认证或通过读取边界验收。Task2/6/8 保持三个未勾项，没有安装、全局配置、会话消息或 Git 交付。

## 用户反馈与具体接续（2026-10-14）

用户直接回复“Login 有效”，终端状态问题已回答，不重复要求重新登录。它描述当前用户会话，不恢复S6原始流或证明其历史凭据。原版固定二进制静态错误映射证实多个原因共用authentication_failed，不能据类别修改权限。已准备[一次诊断接续](2026-10-14-delegate-s6-diagnostic-followup-plan.md)：私有观察器只输出固定提示类别和精确canary归属布尔值，7个隔离用例/最终dry-run通过，0真实模型。新增一次调用须明确授权；反馈Login有效不当作批准。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
