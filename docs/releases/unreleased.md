# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

v0.6.0 之后的 run 超时保留进度（接口 1.2）与写模式不再写入 Codex 项目信任已归入 [v0.7.0 版本说明](v0.7.0.md)；v0.7.0 之后的中止时回收 Codex 起的命令已归入 [v0.7.1 版本说明](v0.7.1.md)。历史验收记录保留其发生时的版本和状态，不追认历史批准。

v0.7.1 之后（接口 1.3，五个模块全部完成前不发版）：

- **结果文件（run-result）**：每次启动过 Codex 的 run 写一份 JSON 结果文件；结果行前多一行 `delegate: result=<路径>`。新增 `--strict`，缺首行结束标记判 `unmarked`、退出 1。接口新增 `run.result`、`run.usage`。
- **接着派任务（run-continue）**：新增 `--continue <runId>`，在 `--resumable` 链上状态为 `done` 的一轮之后，于同一 Codex 会话里接着做下一个任务。状态文件、占位文件和结果文件改为保留 14 天，不再随最近 50 组日志一起删除。接口新增 `run.continue`。
- **长任务（run-longrun）**：新增 `--timeout <秒>`，把期限放大到 541～7200 秒；默认仍是 540 秒，超过宿主前台期限时须由调用方用后台模式调用，delegate 不托管后台进程。中止清理沿用 v0.7.1。结果文件记 `timeoutSeconds`。接口新增 `run.longRun`。
- **检查与写入授权（run-check）**：新增 `--check "<命令>"`，运行以 `done` 结束后按参数列表、不经 shell 执行检查命令（运算符规则与 module-crew S30 一致），结果写进结果文件；新增 `--authorized-by <文件>`，记录事先写入授权的来源文件与 sha256，整条链须为同一文件。`run.write` 仍是 `"explicit"`。接口新增 `run.check`、`run.writeAuthorization`；`delegate-routing` 的写入规则加了带 `--authorized-by` 的例外。
- **规则片段（run-rules）**：新增 `--rules-file <文件>`，把本次委托专用的规则原样放在前言之后；AGENTS.md 仍由 Codex 自己读取。接口新增 `run.rules`。

1.3 汇总：`interface` 为 `"1.3"`，`run` 下新增 `result`、`usage`、`continue`、`longRun`、`check`、`writeAuthorization`、`rules` 七个能力标记，已有字段不删不改。使用方按 `>=1.3,<2.0` 且对应字段存在来启用；`/delegate:run` 的 1.3 用法与授权纪律在插件的 `references/run.md`。

升级提示：
- 过程日志变成两个文件：`<runId>.events.jsonl`（Codex 以 `--json` 运行的事件流）和 `<runId>.log`（stderr）；失败时 stderr 打印的日志末尾随之变化，并附最近的事件。读日志文本的脚本需要调整；日志不是接口。
- 结果行仍是 stdout 最后一行，但它前面多了 `delegate: result=` 一行。
- 结果文件的 `status` 多了 `unmarked`（仅 `--strict`）以及没有结果行时的 `failed`、`interrupted`、`unreaped`、`empty`。判断成功仍先看退出码为 0，再看 `status=done`。
