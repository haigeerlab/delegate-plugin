# ADR-004：Claude 审查使用当前 Mac 本机运行边界

[English](../en/decisions/ADR-004-native-mac-review.md)

日期：2026-10-10。当前源码采用本决定；真实模型验收未完成。用户已明确只需要当前 Mac 本机可用并要求继续实现；本决定替代 ADR-003 的 guest 部署要求，不追认旧失败为通过，不授权新安装、模型调用或 Git 交付。

## 问题与选择

旧进程组 runner 在 setsid helper 的正常退出、超时、取消三个场景失败。Linux guest/cgroup 虽已取得无模型证据，却增加环境和独立认证准备，用户已收敛为 Mac 本机。完全禁止 fork 也已证实与原版本机认证不兼容。

使用临时 launchd job 建立唯一 resource coalition；不是依赖 launchd 的同组清理。可信 anchor 执行前证明独立归属及自身为唯一成员；srt/CLI/代理和 fork、setsid、double-fork 后代由内核保留归属。STOP 所有 reviewer 成员后，核对枚举与内核任务数一致、全员停止，再发送绑定 PID generation 的 KILL。最后移除唯一 job、核对计数为零，失败关闭。命名、环境标签、PPID 轮询不用于推断完整归属。

依据是 Apple [libproc 封装](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/libsyscall/wrappers/libproc/libproc.c)、[进程身份/coalition ABI](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/sys/proc_info_private.h)、[coalition 计数定义](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/osfmk/mach/coalition.h)，以及[本机实际证据](../verification/2026-10-10-claude-review-mac-native.md)。私有 ABI 不是稳定公开接口；仅核实当前 macOS 15.7.3 arm64 的布局、能力、计数、代际信号。其他版本遇到不匹配即条件不足，不能按进程名补杀。

## 权限与认证

- 工具：Read/Glob/Grep 指定子集、dontAsk、无 Bash/写入/MCP/Web/派活；初始化事件工具清单不合规立即停止。仅另外容许 StructuredOutput/schema 和官方保留的 EndConversation/会话终止控制，不扩张 IO；缺少完整结果仍未完成。初始化失败仅保留固定原因码。原版探针复现的被动 ui_invalidate/ui.render 前缀按固定字段、最多 8 个/64 KiB 兼容，随后仍强制合法 init；不跳过 Hook、插件安装或未知事件。它是能力控制，不是文件系统隔离。
- OS：srt 0.0.79 的明确读取和只写本次 writable 策略；源码、Git、配置、快照和 Keychains 不可写；control 不给 reviewer。网络只允许三个 first-party 443 端点。临时 job 不写 LaunchAgents 或全局配置。
- 上下文：固定范围快照，safe/restricted 关闭普通项目/插件/Hook 定制；数据不当作指令，不扩大扫描。
- 认证：原版 CLI 自行使用本机现有认证，不读/复制凭据；实测 Keychains 的运行时只读访问必需。工具层对运行时授权路径加 Read deny 与 blockReadsOutsideWorkingDirectories。官方对 Grep/Glob 的 Read 规则是 best effort，实际模型工具行为仍未验收。自定义认证/provider 环境、本地管理配置与旧 guest 配置明确拒绝，不静默换认证。

## 实施与验收

`review_macos.py` 管进程归属/期限/控制事实，`review_native.py` 接入本机依赖、策略、快照与 Claude 适配器。公共分派、doctor、两宿主来源命令/技能及双语合同统一本机路径；Codex 默认与旧写行为保留。依赖只发现已有 PATH 或显式绝对路径，不安装、不升级、不登录。后台 anchor 有自己的有限期限；不可捕获终止不保证立即清理。系统共享 XPC 服务不被当作本次派生进程终止。

免费测试分别证明参数/状态、实际 OS 拒写/生命周期、固定假 CLI 公共链路。原版 2.1.295 曾返回 authentication_missing，最新原版 2.1.296 的严格边界认证已通过；此前根因尚未确定，不能推断用户曾退出登录、将版本变化认定为修复或宣称真实审查可用。正常、空/坏输出、权限拒绝、工具越界、超时、INT/TERM/HUP、快速 fork、父先退、无关会话、PID 复用和控制 JSON 原子发布均独立检查。原 Mac 红测试保持原旧 runner 结果，新运行器用同类实断言复验，不删红或跳过冒充修复。

真实 `-p`、认证刷新、动态管理配置、网络/TLS、工具读取边界、写入/递归诱导和双向真实宿主仍需有限 live 批次。CLI 状态成功和假结果均不能宣称审查通过、模型更准确或交付授权。安装缓存、提交、推送、发布均未变。

本次修复：srt 代理在 Mac 默认长 TMPDIR 下启动失败。新增实际长路径回归先红后绿；运行/doctor 改用 `/private/tmp` 下专用短目录，权限不放宽。原认证失败与此启动缺陷分开记录。

### 2026-10-13：本地安装目录与监督代码启动

launchd的解释器不一定能重新打开Documents中的插件安装文件。主会话仅将review_macos.py、review_result.py、claude_review.py三个受信监督/解析代码文件复制到既有私有control子目录（目录0700、文件0600），临时任务从该处启动。源码快照、凭据与其他用户数据不在这一步复制；reviewer仍被OS禁止读写整个control树，工具、网络、身份证明、期限与清理规则不变。不修改系统权限、全局配置或认证，不换后端。实际路径拒绝及零模型修复证据另记；不能由启动探针推导真实模型审查通过。
