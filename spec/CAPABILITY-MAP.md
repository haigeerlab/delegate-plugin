# 能力图：delegate

简体中文 | [English](../docs/en/capability-map.md)

## 目标

当前实现将已定方案的执行与查证交给 Codex CLI，隔离过程日志，并返回最终答复与写模式 Git 证据。独立 marketplace；产品运行不依赖 Spec Guard 或 agent-skills。

2026-10-09 已确认可选 Claude Code 只读审查后端，见 [claude-review](claude-review.md)。当前源码已接通 Mac 本机路径与免费验证，原版 CLI 严格边界认证及有限 Codex→Claude 真实审查通过；两方向普通真实审查已有成功记录；主动模型越界和完整异常验收仍未完成。review/run、快捷范围与无模型预览已随 v0.5.0 发布；两宿主安装已核对。S7 菜单实际脚本与 dry-run 功能证据已取得；分层验收完成，未验证的安全事件与历史未知保留，详见[版本说明](../docs/releases/v0.5.0.md)。

2026-10-08 按已确认的项目接入范围规范化文件布局。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。本次确认不追认早期模块的人工审批。

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| channel | 调用参数、只读/写沙箱、进程组期限与清理、日志隔离、Git 证据 | — |
| detection | CLI 基础检查、身份绑定缓存、原子写入、静默降级、doctor | — |
| routing | 显式委托请求的可选判据与确认纪律，不自动注入提醒 | channel, detection |
| claude-review | 为 delegate 增加显式后端选择、Claude Code 只读审查和统一审查结果，保持现有 Codex 行为兼容 | channel, detection, routing |

Build order: channel → detection → routing → claude-review

channel 与 detection 共用 `backend.py`，该共享代码不是独立模块依赖。routing 按显式请求结合 detection 体检，授权后使用 channel；构建顺序保留既有实施顺序，不新增运行职责。

```text
backend.py → codex-exec.sh → run_codex.py → codex exec
     ↓
detect.py ← detect.sh / doctor.sh
     ↓ detection.json → doctor
explicit request → delegate-routing skill → review/run
```

- channel 不决定“什么任务该派”，且每次实时复查基础认证。
- detection 不发模型请求；只检查本地条件，不保证远端/额度。
- routing 不调用 Codex，不做关键词分类；决策交给模型解释，授权交给用户。
- 移除 routing 后，channel 仍能手动调用；共用 backend 不依赖 hook 缓存。
- doctor 属于 detection，按需刷新与检查中文全局规则，临时缓存写入不触及业务项目。
- 写模式不要求干净工作区；原有修改数量和 staged/unstaged 统计必须可见，不能自动回滚。
- 默认只读、写入须当前轮明确授权；命令指令的确认纪律不能被当作不可绕过技术锁。

既有合同与验证详见 [channel](channel.md)、[detection](detection.md)、[routing](routing.md)；新增模块按 [claude-review](claude-review.md) 单独追踪。不新增非 Git 支持、后台编排、提交/推送/发布或自动升级安装缓存。

真实反向首批已启动 Codex，但四文件均未审；免费修复改为有界 inline 文件输入（总输入1MiB）及核实的 shell/apps/plugins/multi_agent 禁用开关，不增加 Bash/MCP 读取权限。修复后已完成真实反向审查4/4，见[最新证据与限制](../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-success.md)；首批失败保持历史结论。
