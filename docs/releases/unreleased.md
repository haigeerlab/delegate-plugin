# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.6.0 之后的 run 超时保留进度（接口 1.2）与写模式不再写入 Codex 项目信任已归入 [v0.7.0 版本说明](v0.7.0.md)；v0.7.0 之后的中止时回收 Codex 起的命令已归入 [v0.7.1 版本说明](v0.7.1.md)；v0.7.1 之后的接口 1.3（结果文件、接着派任务、长任务、检查与写入授权、规则片段）已归入 [v0.8.0 版本说明](v0.8.0.md)；v0.8.0 之后的文档补齐已归入 [v0.8.1 版本说明](v0.8.1.md)；v0.8.1 之后的 run 命令说明修正已归入 [v0.8.2 版本说明](v0.8.2.md)。v0.8.2 之后的使用者文档补齐已归入 [v0.8.3 版本说明](v0.8.3.md)。v0.8.3 之后的无提交仓库专用诊断码已归入 [v0.8.4 版本说明](v0.8.4.md)。v0.8.4 之后的 Codex 审查 schema 修复与失败原因诊断已归入 [v0.8.5 版本说明](v0.8.5.md)。v0.8.5 之后的沙箱证书信任已归入 [v0.8.6 版本说明](v0.8.6.md)。v0.8.6 之后的审查报告补丁指纹（接口 1.4）已归入 [v0.9.0 版本说明](v0.9.0.md)。v0.9.0 之后的未发布变更见下。

## 审查发现新增严重程度（接口 1.5）

- 审查报告每条发现新增必填字段 `severity`：`blocking`（阻断）或 `suggestion`（建议）。审查模型按固定判据 `severity-v1` 标注，判据见 [review-severity 规格](../../spec/review-severity.md)，`--task` 不能改判据。
- 模型漏标或取值不对时，整次审查判 `failed`（诊断 `finding_invalid`），delegate 不替模型补。
- 读报告的一方遇到缺字段（0.9.0 及以前的报告）或不认识的值，一律按 `blocking`；没有阻断发现不等于可以合并。
- `interface.json` 升到 1.5，`review.report` 下新增 `severity` 说明；报告 `schema_version` 仍为 `1`，只增字段。

## 复审对照上一轮（接口 1.5）

- `/delegate:review` 新增 `--previous-report <上一轮报告>`：上一轮的阻断发现逐条进报告新字段 `recheck.items`，标 `resolved` 或 `unresolved` 并给证据；本轮 `findings` 只放新问题。合同见 [review-recheck 规格](../../spec/review-recheck.md)。
- 上一轮报告必须是 delegate 产出、已有结论、范围相同（`commits` 下 `from` 也相同），否则报 `previous_report_unreadable`、`previous_report_invalid` 或 `previous_report_scope_mismatch`，退出 127、不启动模型；模型的逐条回答不完整报 `recheck_invalid`、整次审查 `failed`。
- 可以连着复审：第三轮把第二轮报告交进来即可。轮次计数和是否交给人由调用方判断。
- 不带该参数时 `recheck` 为 `null`，其余行为不变。

历史验收记录保留其发生时的版本和状态，不追认历史批准。
