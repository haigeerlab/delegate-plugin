# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.5.3 之后的可续跑委托与审批方式变化已归入 [v0.6.0 版本说明](v0.6.0.md)。历史验收记录保留其发生时的版本和状态，不追认历史批准。

## run 超时保留进度（run-timeout，接口 1.2）

合同见 [spec/run-timeout.md](../../spec/run-timeout.md)。

- **所有 run 的提示词末尾多一段时间预算**：Codex 主运行最多跑总期限减去收尾预留（540 秒时为 495 秒），到阈值（540 秒时为 405 秒）后应主动停下，答复首行写 `TIME_UP:` 并写进度。普通 run 的参数（含 `--ephemeral`）不变。
- **超时有结果行**：超时现在输出答复、元数据与 `delegate: run_id=<id> status=timeout resumable=<true|false>`，退出码仍为 124。
- **两道收尾与兜底**：可续跑 run 被强制中止后，再以只读沙箱续跑一轮只写进度的收尾（最多 45 秒）；普通 run，以及收尾超时、失败、答复为空或没有会话 ID 时，输出不靠模型的兜底文字，写模式附运行中改动的文件。
- **超时后可续跑**：`--resume` 接受 `status=timeout` 的可续跑 runId；普通 run 超时不能续跑。
- **接口 1.2，只增不改**：`run.resume.statuses` 追加 `"timeout"`，新增 `run.timeout: {"status": "timeout", "exitCode": 124}`。
- **修复**：`run_codex.py` 在 macOS 上清理进程组时偶发的 `PermissionError`（EPERM）不再中断清理。

### 升级提示

- **判断成功先看退出码为 0，再看 `status=done`。** 超时现在也有结果行，有结果行不等于成功。
- **`statuses` 是开放集合**：遇到不认识的值要停下或当失败处理，不能当成完成。
- 读 1.1 的使用方不受影响：超时仍是退出 124，可继续按失败处理。

未验证：真实 540 秒期限下的守时余量、收尾轮的长尾频率、大上下文下的收尾、其他模型，以及写模式续跑是否重复写入，留待付费实测。
