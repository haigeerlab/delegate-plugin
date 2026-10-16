# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.4.0 之后的本轮变化已归入 [v0.5.0 版本说明](v0.5.0.md)。以下文档维护属于 v0.5.0 标签之后的源码提交，未创建新的插件发行版。历史验收记录保留其发生时的版本和状态，不追认历史批准。

## 发布后文档维护

修正当前发行/安装状态、已退役Hook流程、真实及菜单验收口径、本地源码与缓存加载说明、验证套数量和英文遗漏。产品版本仍为0.5.0，运行代码、权限和历史原始证据不变；不新增模型验收。

2026-10-16 文档核对：中文文档索引与英文版对齐并补 ADR-003/004、v0.4.0 链接；README 补 Claude 审查后端的前置条件、诊断和故障排查条目；移除 README、DESIGN、能力图和文档索引末尾错位的验收流水段；澄清探测规格的默认模式。新增插件目录 README、安全政策 SECURITY.md（GitHub 私密漏洞报告）、GitHub Issue 模板（Bug 报告、需求建议），README 的报告步骤改为指向模板。README 开头、DESIGN 和能力图中的内部批次流水改写为面向用户的验证状态，并更正 srt 默认从 PATH 解析；claude-review 规格开头的历史接续记录原样移到文末附录。不改运行代码。

2026-10-16 文档归档：`docs/superpowers/` 下 6 份 2026-08-30 定位设计与计划按字节移入 [`docs/archive/superpowers-2026-08-30/`](../archive/superpowers-2026-08-30/README.md)，附原路径与 SHA-256 清单；新增 [验证记录索引](../verification/README.md)（[English](../en/verification/README.md)），`docs/verification/` 下的记录不移动、不改写。不改运行代码。

## Claude 后端修复

2026-10-16：从 Claude Desktop 的 Code 会话运行 `/delegate:review --backend claude-code` 或 `/delegate:doctor --backend claude-code` 时，Desktop 注入的 `ANTHROPIC_BASE_URL=https://api.anthropic.com` 会被误判为自定义 provider，报 `native_authentication_environment_unverified`。现在该变量规范化后等于官方默认端点时放行（https、主机 api.anthropic.com 不区分大小写、端口为空或 443、路径为空或 `/`）；任何其他值、以及其他认证/provider 变量仍然拒绝。子进程环境本就不继承该变量，实际使用的端点不变。新增 `test-review-native.py` 回归用例；未发起模型调用。
