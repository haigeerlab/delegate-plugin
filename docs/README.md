# 文档索引

简体中文 | [English](en/README.md)

delegate 的默认文档语言为简体中文。英文对应页覆盖当前维护的使用、设计、技术规格、贡献与版本说明；同一插件共用相同命令和实现，运行时提示仍以中文为主。

## 按阅读目标选择

- 首次使用：阅读 [README](../README.md) 的前置条件与快速开始，再用 `/delegate:doctor` 检查本地基础条件。
- 日常使用与排障：查 README 的命令、输出验收和故障排查；会话内可用 `/delegate:help`。
- 理解设计：先读 [设计与边界](../DESIGN.md)，再看 [能力图](../capability-map.md)。
- 开发与审查：阅读三份当前规格和 [贡献指南](../CONTRIBUTING.md)，从仓库根目录运行离线验证。
- 升级：读 [v0.4.0 版本说明](releases/v0.4.0.md)；后续变化看 [未发布记录](releases/unreleased.md)。

## 当前维护的双语文档

| 内容 | 简体中文 | English |
|---|---|---|
| 安装、使用与排障 | [README](../README.md) | [README](../README.en.md) |
| 文档索引 | 本页 | [Documentation index](en/README.md) |
| 贡献与验证 | [贡献指南](../CONTRIBUTING.md) | [Contributing](../CONTRIBUTING.en.md) |
| 设计与边界 | [设计](../DESIGN.md) | [Design](en/DESIGN.md) |
| 模块职责 | [能力图](../capability-map.md) | [Capability map](en/capability-map.md) |
| 执行合同 | [通道规格](../SPEC-channel.md) | [Channel specification](en/SPEC-channel.md) |
| 探测与缓存 | [探测规格](../SPEC-detection.md) | [Detection specification](en/SPEC-detection.md) |
| 路由与行为评估 | [路由规格](../SPEC-routing.md) | [Routing specification](en/SPEC-routing.md) |
| 当前发行 | [v0.4.0](releases/v0.4.0.md) | [v0.4.0](en/releases/v0.4.0.md) |
| 后续变化 | [未发布记录](releases/unreleased.md) | [Unreleased](en/releases/unreleased.md) |
| 旧版发行记录 | [v0.3.1（历史）](releases/v0.3.1.md) | [v0.3.1 (historical)](en/releases/v0.3.1.md) |

安装和日常使用以 README 为入口；精确的实现与测试合同以当前 `SPEC-*.md` 为准。英文版与中文版应同步维护；发现差异时请提交问题，以当前实现和验证结果核对后同时修正。

## 源码入口

本仓库同时包含 marketplace 和插件源码：

```text
.claude-plugin/marketplace.json       marketplace 清单
plugins/delegate/
  .claude-plugin/plugin.json         插件清单
  commands/                         delegate、doctor、help 会话入口
  skills/delegate-routing/          分流判据
  hooks/                            基础探测、缓存和上下文注入
  scripts/                          Codex 调用与进程管理
  tests/                            离线桩测试与回归
scripts/                            仓库验证
evals/                              行为判决器和按需模型评估
```

命令文件和 skill 是宿主执行的指令，当前以中文编写；本页链接的英文文档解释其完整使用合同，不会注册第二套插件命令。

## 历史与实施记录

这些资料保留当时的方案、检查清单和取舍，不是当前安装或行为合同。旧参数、认证判据、性能数字和未完成勾选不能直接用于判断当前版本。

- 早期模块记录：[channel 计划](../tasks/channel/plan.md) / [任务](../tasks/channel/todo.md)、[detection 计划](../tasks/detection/plan.md) / [任务](../tasks/detection/todo.md)、[routing 计划](../tasks/routing/plan.md) / [任务](../tasks/routing/todo.md)。
- 2026-08-30 文档设计：[公开定位](superpowers/specs/2026-08-30-public-positioning-design.md)、[中文 marketplace 定位](superpowers/specs/2026-08-30-chinese-marketplace-positioning-design.md)、[v0.3.0 发布说明草案](superpowers/specs/2026-08-30-v030-release-notes-design.md)。
- 对应实施记录：[公开定位](superpowers/plans/2026-08-30-public-positioning-docs.md)、[中文 marketplace 定位](superpowers/plans/2026-08-30-chinese-marketplace-positioning.md)、[v0.3.0 发布说明草案](superpowers/plans/2026-08-30-v030-release-notes.md)。
- 本次双语修订：[计划](../tasks/plan.md) / [任务与验收](../tasks/todo.md)。

历史和实施记录保留原有语言，不逐篇翻译；当前维护文档通过上表提供双语阅读路径。
