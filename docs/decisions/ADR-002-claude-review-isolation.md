# ADR-002：Claude 只读审查使用 CLI、快照和整个进程隔离

简体中文 | [English](../en/decisions/ADR-002-claude-review-isolation.md)

当前 Mac 本机进程机制见 [ADR-004](ADR-004-native-mac-review.md)；以下保存最初设计和之后 Linux 修订的背景，不推断旧支持声明。

状态：Accepted（设计取舍；尚未实施或验收）。日期：2026-10-09。
批准来源：用户在本轮审阅设计、实现计划及三项推荐后回复“继续”。批准对象是 CLI、显式后端、快照、整个进程隔离、Claude 首版拒绝 effort、macOS 首验；不包含安装、live、委托或 Git/外部交付。

## 背景

现有 delegate 实际只调用 Codex CLI，主会话宿主不决定后端。现有期限、日志及进程组机制可复用，但 Claude Hook 可以创建独立会话，不能照搬同组清理保证。
官方 `claude -p` 可非交互调用。`--allowedTools` 不是完整白名单；Bash 沙箱不覆盖文件工具、Hook 和 MCP；`--safe-mode` 保留认证但仍可能运行管理员 Hook。`--bare` 会跳过 OAuth/钥匙串。Plan 模式和“只读”提示词不能提供所需隔离。

## 决定

使用用户安装的原版 Claude CLI，不同时引入 Agent SDK。公共入口显式接受 `codex|claude-code`，默认 Codex；旧 Codex 行为保留。Claude 只审查，拒绝写入和首版 effort，避免 CLI 对不支持档位静默降低。
审查者读取固定范围的普通文件快照，Git 信息由 wrapper 只读采集。仅 Read/Glob/Grep；禁用执行、网络、MCP、插件、子代理和再委托能力。
srt 为 Claude 后端的可选运行依赖，用于包围整个进程，源项目/Git/全局配置不可写，只允许本次临时目录写入。关闭其默认额外可写路径，验证实际边界；缺失、不兼容或隔离初始化失败则拒绝执行，不降级。
不读、复制或代理凭据；认证由原版 CLI 自行完成。严格隔离影响现有认证或管理员策略时报告条件不足，不擅自改变配置。原定先在 macOS 完成独立验收；原生候选生命周期失败后，用户批准 [ADR-003](ADR-003-review-process-boundary.md)，改用专用本机 Linux VM 中的 service/cgroup+srt。各新环境未实际验收，不宣称支持 Claude 后端。

## 备选与后果

直接在源仓库启动并仅写“只读”最简单，但不能阻止写工具、定制或辅助进程。仅内置 Bash 沙箱覆盖不足；仅 safe-mode/restricted 不能证明整个 CLI 的文件写入边界。Agent SDK 有权限回调与类型化消息，仍需进程隔离并新增依赖，因此留待后续。
快照有采集开销且缺少实时文件变化；用哈希固定输入，缺少内容列未审范围，不自动扩大扫描。srt 增加 Node/OS 依赖与认证兼容风险，必须先通过免费的隔离 gate，再实现调用通道。设计批准不证明候选运行时版本已可用。

## 官方依据及限制

[CLI](https://code.claude.com/docs/en/cli-reference)、[Bash 沙箱](https://code.claude.com/docs/en/sandboxing)、[Hook](https://code.claude.com/docs/en/hooks)、[模型配置](https://code.claude.com/docs/en/model-config)及[官方 srt](https://github.com/anthropics/sandbox-runtime)为 2026-10-09 调研依据。
[SDK 页面](https://code.claude.com/docs/en/agent-sdk/overview)限制第三方产品提供 claude.ai 登录/额度，而[帮助中心](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)说明 SDK、`claude -p` 和第三方使用仍可计入订阅限制；[凭据边界](https://code.claude.com/docs/en/legal-and-compliance)区分原版 CLI 用户自行登录与第三方凭据中介。这里不推导无限或固定额度权益，也不绕过官方认证流程。
设计阶段本机 srt 缺失；随后经用户单独批准临时安装 0.0.79。实际 macOS 权限/策略套 13 项通过，但独立会话辅助进程的超时、取消和父先退清理三项失败。默认工具沙箱的嵌套拒绝已通过沙箱外临时探针区分；严格进程寿命边界和 Claude 实际兼容性仍未验证。
首个 gate 未通过，未接入产品入口。用户随后批准 ADR-003 专用 VM 修订及免费实现测试；本 ADR 的 macOS 原生首验部分由该决定替代，CLI/快照/严格权限取舍仍有效。运行时安装、guest 认证和真实验收未获该批准或完成。见[实际证据](../verification/2026-10-09-claude-review.md)及[任务记录](../../tasks/claude-review/todo.md)，不能将 Accepted 当作验收完成。
