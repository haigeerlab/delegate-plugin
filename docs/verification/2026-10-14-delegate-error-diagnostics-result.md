# Task9l：Claude 错误终态安全诊断修复

2026-10-14，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。用户承接预告的免费诊断步骤回复“继续”，本批完成合成复现、最小源码修复及免费回归；没有安装、模型调用、跨会话消息或 Git 交付。

## 已确认的原因与修复

`review_result.py` 在官方错误终态直接返回 backend_result_error，尚未检查该终态的 permission_denials；同时丢失已知终态 subtype 和 assistant.error 类别。这是**诊断丢失的原因**，不是 S4 实际后端失败原因。S4 原始流没有保留，其具体原因继续未知，原报告与失败结论不改。

修复先提取非空拒权列表的固定事实，再失败关闭；对已知四种错误终态保留 claude_error_* 码，错误终态中的十种已知 assistant.error 枚举保留 claude_api_* 码。通用 backend_result_error 仍在。未知/畸形字段、错误原文、工具输入和敏感路径不进入诊断；正常最终结果不被已恢复的中间错误改判失败。模型、用量、权限、超时、重试与后端选择行为不变。

依据是 Anthropic 发布的 [SDK 类型定义](https://app.unpkg.com/@anthropic-ai/claude-agent-sdk@0.3.193/files/sdk.d.ts)中的 SDKResultError、SDKAssistantMessageError 封闭字段：只参考协议类型，仍通过 CLI 执行，没有安装或新增 SDK 后端。未知未来值保留通用失败，不凭错误文本猜认证、额度或服务原因。官方参考网页过大无法直接读取，使用发布包类型核对；这不证明当前 CLI 会产生每个枚举值。

## 实际验证

- RED：23 个测试中新增拒权及类别断言出现 15 个失败，原产品正常断言保留。
- GREEN：修复后 23 个测试通过，再增加中间错误恢复/重复码兼容案例；完整套中结果测试为 24 个。
- 工作区原总入口退出 1：153 Python、53 shell、19 eval 已通过，但安装备份目录中的 20 个 0600 脚本被文件发现逻辑要求可执行。
- 保留私有备份 0600，未改验证脚本或弱化断言。把完整源码复制到专用临时目录，仅排除 `.git` 和 `.agent/acceptance`，282 文件摘要与冻结时仓库逐项一致；在副本运行同一 `scripts/validate.sh`，退出 0，153 Python / 53 shell / 19 eval 通过。
- 当前产品摘要再次匹配验证副本；副本双语合同包含本次行为条款，验证后追加的证据状态说明及其他文档单独检查链接和 diff。原 S4 报告 SHA-256 保持 `a4fe2838e44a65c7d6246b606e05a6462873676f282f4d795ceb36f166dab0ca`。

具体安全元数据见 [JSON](2026-10-14-delegate-error-diagnostics-result.json)。私有 RED/GREEN、两次总验证日志、源码摘要与本批产品 diff 保存在 `.agent/acceptance/error-diagnostics-20261014/`。第一轮失败不追认为通过；正常开发目录仍有“总入口扫描私有备份”的限制，本批没有顺带重构发现逻辑。

## 交付范围与限制

本批共改 13 文件，无提交：产品解析器/测试 2，双语规格 2，README/未发布说明 4，模块 plan/todo 2，当前状态页 1，本页/JSON 2。斜杠命令、清单、权限配置和其他模块未改。

最新修复尚未同步安装或真实调用验证。S3 已安装的是本修复之前的固定源码，S4 失败不会因合成回归转成通过；Task2/6/8 三项仍未关闭，模块 BUILDING。下一步为固定最新源码并准备一次仅 delegate 的安装同步范围；安装与新增模型继续分别授权，不重用 S3/S4 已消费授权。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
