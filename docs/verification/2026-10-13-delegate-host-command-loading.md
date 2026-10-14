# 两宿主新入口：CLI 加载核验

日期2026-10-13；仓库 delegate-plugin，分支 codex/spec-guard-conventions-public。本轮继续已预告的免费入口检查；没有安装、登录、通信、模型调用或全局配置修改。

## 已通过的范围

| 宿主加载链 | 实际证据 | 限制 |
|---|---|---|
| Codex0.162.1 | 上一批原生CLI安装生成source-command-review/run/doctor/help，四份真实产物与固定源码逐字节匹配 | 临时安装已清理；不是桌面界面验收 |
| Claude Code2.1.296 | 一次--init-only/--plugin-dir加载固定源码，原版CLI日志明确Loaded 4 commands from plugin delegate default directory及Total plugin commands loaded: 4；退出0，coalition回收confirmed | 日志只有总数；名称由对应的固定四文件集合核对，不声称CLI逐项列出了名称 |

[本轮JSON](2026-10-13-delegate-host-command-loading.json)保存CLI摘要、固定源码、实际argv、原版日志中的最小加载观察、隔离探针、非致命诊断和清理。Codex的原始安装驱动路径误报与独立产物核对仍见[上一批证据](2026-10-13-delegate-source-load-fixed-result.md)，没有再安装或重跑驱动。

Claude采用独立临时CLAUDE_CONFIG_DIR和空工作目录，无认证复制；源码只读、仅本批临时目录可写，OS禁网及认证/日常配置读取拒绝。相同策略的实际探针在初始化后核对：源副本拒写、专用目录可写、回环网络拒绝，源marker不存在。CLI和源码摘要不变。禁用Hook、严格空MCP，日志观察到跳过插件Hook；未用会关闭插件加载的safe-mode、restricted或disable-slash-commands，也未用bare。CLI仍枚举内置插件/技能，不把此检查说成移除了一切内置上下文。

原版CLI记录临时空配置锁ENOENT后成功原子写入、ps启动EPERM、本地UDS监听失败以及其他进程持有版本锁等非致命诊断。它们不影响观察到的四命令加载，但不能据此宣称整个日常启动环境无问题；未干预其他进程或版本锁。本批完整debug和匿名临时配置已删除，仅保留必要的过滤事实、摘要及固定夹具。没有独立快照核对所有全局文件，边界依据是OS写策略和实际探针。

## 用户如何选择入口

Claude Code源码入口为`/delegate:review/run/doctor/help`。Codex对应的是`source-command-review/run/doctor/help`迁移skill，通过宿主skill选择器选择delegate条目，再提供相同参数；显示名以已加载列表为准。Codex内置`/review`不是delegate的review入口。两个宿主复用相同脚本和参数，不保证斜杠显示完全相同。

选择Claude审查后端：review加`--backend claude-code`；选择Codex：`--backend codex`，未指定仍为codex。模型另加`--model`。安装v0.4.0不会随本轮源码自动变化。help/doctor/dry-run不调用执行后端模型；通过宿主解释这些指令仍可能使用主会话模型及额度。

依据官方[CLI参考](https://code.claude.com/docs/en/cli-reference)，--plugin-dir只为本次会话加载，--init-only运行初始化Hook后退出而不开始对话；本批Hook关闭、无prompt并禁网。Codex CLI的[skill选择器](https://learn.chatgpt.com/docs/developer-commands#use-skills-with-skills)通过/skills使用。CLI加载记录不等于真实审查验收。

## 剩余范围与下一步

当前代码和免费回归已完成；两方向普通真实四文件审查及两宿主CLI入口加载有通过证据。仍未验收交互显示/调用、真实模型主动写入/再委托企图、认证刷新和异常原版helper；Task2/6/8保持未勾，模块保持BUILDING，不自动提交发布。

本批不需要为了确认命令总数重复加载或安装。下一步先收束面向用户的最终变更说明和未验收矩阵，展示具体交互/主动越权验收方案；涉及模型、其他会话通信、日常安装或配置时分别取得相应授权。没有第三后端或Spec Guard执行器扩展。
