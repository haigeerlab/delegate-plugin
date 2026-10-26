# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.5.2 之后的对外接口说明已归入 [v0.5.3 版本说明](v0.5.3.md)。v0.5.3 之后：

- 新增可续跑委托（[run-resume](../../spec/run-resume.md)）：`/delegate:run --resumable` 可停下问用户并返回 `needs-input`，`--resume <runId>` 带用户答复续跑原 Codex 会话；每次成功返回末行给出 run_id 与结束状态。接口说明升到 1.1，只新增 `run.resume`。所有 run 与 Codex 审查改为固定 `approval_policy="never"`，不再沿用本机配置的审批方式；写模式下越出沙箱的命令会被拒。真实 Codex 续跑实测见本模块验收记录。

历史验收记录保留其发生时的版本和状态，不追认历史批准。
