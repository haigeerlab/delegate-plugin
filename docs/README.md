# 文档索引

简体中文 | [English](en/README.md)

delegate 的默认文档语言为简体中文。英文对应页覆盖当前维护的使用、设计、技术规格、贡献与版本说明；同一插件共用相同命令和实现，运行时提示仍以中文为主。

## 按阅读目标选择

- 首次使用：阅读 [README](../README.md) 的前置条件与快速开始，再用 `/delegate:doctor` 检查本地基础条件。
- 日常使用与排障：查 README 的命令、输出验收和故障排查；会话内可用 `/delegate:help`。
- 理解设计：先读 [设计与边界](../DESIGN.md)，再看 [能力图](../spec/CAPABILITY-MAP.md)。
- 开发与审查：阅读三份当前规格和 [贡献指南](../CONTRIBUTING.md)，从仓库根目录运行离线验证。
- 升级：读 [v0.4.0 版本说明](releases/v0.4.0.md)；后续变化看 [未发布记录](releases/unreleased.md)。

## 当前维护的双语文档

| 内容 | 简体中文 | English |
|---|---|---|
| 安装、使用与排障 | [README](../README.md) | [README](../README.en.md) |
| 文档索引 | 本页 | [Documentation index](en/README.md) |
| 贡献与验证 | [贡献指南](../CONTRIBUTING.md) | [Contributing](../CONTRIBUTING.en.md) |
| 设计与边界 | [设计](../DESIGN.md) | [Design](en/DESIGN.md) |
| 模块职责 | [能力图](../spec/CAPABILITY-MAP.md) | [Capability map](en/capability-map.md) |
| 执行合同 | [通道规格](../spec/channel.md) | [Channel specification](en/SPEC-channel.md) |
| 探测与缓存 | [探测规格](../spec/detection.md) | [Detection specification](en/SPEC-detection.md) |
| 路由与行为评估 | [路由规格](../spec/routing.md) | [Routing specification](en/SPEC-routing.md) |
| 当前发行 | [v0.4.0](releases/v0.4.0.md) | [v0.4.0](en/releases/v0.4.0.md) |
| 后续变化 | [未发布记录](releases/unreleased.md) | [Unreleased](en/releases/unreleased.md) |
| 旧版发行记录 | [v0.3.1（历史）](releases/v0.3.1.md) | [v0.3.1 (historical)](en/releases/v0.3.1.md) |

安装和日常使用以 README 为入口；精确的实现与测试合同以当前 `spec/<id>.md` 为准。英文版与中文版应同步维护；发现差异时请提交问题，以当前实现和验证结果核对后同时修正。

项目源码和随附文档采用 [MIT 许可证](../LICENSE)。中文摘要见 [README 的许可章节](../README.md#许可)，英文标准全文以 LICENSE 为准。

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

## 当前开发流程

[开发流程与 AI 约定](development-workflow.md)（[English](en/development-workflow.md)）说明两种宿主规则、标准路径、阶段确认及验证边界。当前模块维护清单：[channel](../tasks/channel/todo.md)、[detection](../tasks/detection/todo.md)、[routing](../tasks/routing/todo.md)，只记录接入核对，不追认历史验收。

[合同条款与验证证据](verification/2026-10-08-contract-matrix.md) 把 13 条当前规格条件映射到源码、测试和缺口；当前维护完成不代表这些产品条件都得到充分验收。

## 历史与实施记录

这些资料保留当时的方案、检查清单和取舍，不是当前安装或行为合同。旧参数、认证判据、性能数字和未完成勾选不能直接用于判断当前版本。

- 早期模块计划、任务及双语修订记录：[按字节归档的原始资料](archive/pre-spec-guard/README.md)，保留原路径、勾选和 SHA-256。
- 2026-08-30 文档设计：[公开定位](superpowers/specs/2026-08-30-public-positioning-design.md)、[中文 marketplace 定位](superpowers/specs/2026-08-30-chinese-marketplace-positioning-design.md)、[v0.3.0 发布说明草案](superpowers/specs/2026-08-30-v030-release-notes-design.md)。
- 对应实施记录：[公开定位](superpowers/plans/2026-08-30-public-positioning-docs.md)、[中文 marketplace 定位](superpowers/plans/2026-08-30-chinese-marketplace-positioning.md)、[v0.3.0 发布说明草案](superpowers/plans/2026-08-30-v030-release-notes.md)。
- 本轮 Spec Guard 接入：[计划](process/2026-10-08-adoption/plan.md) / [任务与验收](process/2026-10-08-adoption/todo.md) / [检查结果](process/2026-10-08-adoption/report.md)。
- 既有修复与真实验证：[脱敏摘要及原始本地证据索引](verification/2026-10-08-history.md)。

历史和实施记录保留原有语言，不逐篇翻译；当前维护文档通过上表提供双语阅读路径。

119 个历史未勾项的[逐项裁决](verification/2026-10-08-historical-reconciliation.md)及 26 项[免费定向补验](verification/2026-10-08-supplemental.md)保留当前证据与历史未知的边界。

[变异与业务目录零足迹核验](verification/2026-10-08-mutation.md)记录本批反向证据、工具声明来源和 F8 测试隔离缺项。

当前工具声明取舍：[ADR-001](decisions/ADR-001-command-tool-scope.md)（[English](en/decisions/ADR-001-command-tool-scope.md)）。七项集中处理的最新[整批结果](verification/2026-10-08-bulk.md)含实际宿主证据及唯一未完成条件。

[最后原生交互样本](verification/2026-10-08-proposal.md)及免费收束：119条当前裁决106/13/0，历史完成/批准未知及产品覆盖缺口继续保留。
