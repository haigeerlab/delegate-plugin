# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.5.0 之后的修复与文档维护已归入 [v0.5.1 版本说明](v0.5.1.md)。v0.5.1 之后的未发布变更如下。历史验收记录保留其发生时的版本和状态，不追认历史批准。

## 修复

- Codex 审查附带的文件内容改为逐行带行号，并在提示里说明 `findings.line` 填对应文件的 1 起始行号。此前内容不带行号，真实审查中模型返回 `line=null`，发现无法定位，整次审查被判 `failed`（`review_incomplete`）。快照、SHA-256 和“任一发现未定位即不算完成”的判定不变；行号前缀计入 1 MiB 输入上限。真实模型复验尚未进行。

## 文档

- README 前置条件与快速开始修正（来自一次真实 Codex 后端审查，已对照代码核实）：`/delegate:review` 要求仓库已有提交，尚无提交的仓库只能用 `/delegate:run`；安装 Codex 和 ChatGPT 登录注明为 Codex 后端专属步骤，只用 Claude 审查后端时可跳过。中英文同步。
- README 故障排查修正（来自一次真实 Claude 后端审查，已对照代码核实）：`native_authentication_environment_unverified` 的核对命令改为只列变量名，避免把密钥值打到终端；“登录后仍不提议”改为说明 v0.5.0 起提议只在明确请求委托时出现；新增 Claude 后端在非 macOS、缺少 GUI launchd 域或内核接口检查失败时的诊断码与处理；写清 Codex 0.160.0、0.162.1 与 `@latest` 安装各自的含义。中英文同步。
