# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.5.0 之后的修复与文档维护已归入 [v0.5.1 版本说明](v0.5.1.md)。v0.5.1 之后的未发布变更如下。历史验收记录保留其发生时的版本和状态，不追认历史批准。

## 文档

- README 故障排查修正（来自一次真实 Claude 后端审查，已对照代码核实）：`native_authentication_environment_unverified` 的核对命令改为只列变量名，避免把密钥值打到终端；“登录后仍不提议”改为说明 v0.5.0 起提议只在明确请求委托时出现；新增 Claude 后端在非 macOS、缺少 GUI launchd 域或内核接口检查失败时的诊断码与处理；写清 Codex 0.160.0、0.162.1 与 `@latest` 安装各自的含义。中英文同步。
