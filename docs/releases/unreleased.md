# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.6.0 之后的 run 超时保留进度（接口 1.2）与写模式不再写入 Codex 项目信任已归入 [v0.7.0 版本说明](v0.7.0.md)；v0.7.0 之后的中止时回收 Codex 起的命令已归入 [v0.7.1 版本说明](v0.7.1.md)；v0.7.1 之后的接口 1.3（结果文件、接着派任务、长任务、检查与写入授权、规则片段）已归入 [v0.8.0 版本说明](v0.8.0.md)；v0.8.0 之后的文档补齐已归入 [v0.8.1 版本说明](v0.8.1.md)；v0.8.1 之后的 run 命令说明修正已归入 [v0.8.2 版本说明](v0.8.2.md)。v0.8.2 之后的使用者文档补齐已归入 [v0.8.3 版本说明](v0.8.3.md)。v0.8.3 之后的无提交仓库专用诊断码已归入 [v0.8.4 版本说明](v0.8.4.md)。v0.8.4 之后的 Codex 审查 schema 修复与失败原因诊断已归入 [v0.8.5 版本说明](v0.8.5.md)。v0.8.5 之后的沙箱证书信任已归入 [v0.8.6 版本说明](v0.8.6.md)。v0.8.6 之后的未发布变更见下。

## 审查报告新增可复算的补丁指纹（接口 1.4）

- 审查报告 `scope` 下新增 `fingerprint`：`{"algorithm": "blob-pairs-v1", "sha256": …, "paths": […]}`。只在基准为两个提交之间（`commits`）时有值，其他基准为 `null`。
- 指纹只用两个提交树里每个被审文件的权限和对象编号计算，与仓库配置、`.gitattributes`、git 版本都无关，可以在 GitHub Actions 等别的机器上复算，把审查结论绑定到具体补丁。算法见 [review-fingerprint 规格](../../spec/review-fingerprint.md)。
- `scope.diff_sha256` 不变，仍是 diff 文字的 sha256，只在本机有效。
- `interface.json` 升到 1.4，`review.report` 下新增 `fingerprint` 说明；报告 `schema_version` 仍为 `1`，只增字段。
- 新增固定诊断码 `fingerprint_inputs_inconsistent`：取到的文件条目和被审文件对不上时报出，不输出半截指纹。

历史验收记录保留其发生时的版本和状态，不追认历史批准。
