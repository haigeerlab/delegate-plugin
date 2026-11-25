# 未发布变更

简体中文 | [English](../en/releases/unreleased.md)

<!-- 发版前，在下面「已归入……」那段之后按 CONTRIBUTING.md「发版」一节的格式写：标题注释行、本次变更小节、## 影响面、## 验证与已知限制；scripts/release-prepare.sh 据此生成发行说明。 -->

v0.6.0 之后的 run 超时保留进度（接口 1.2）与写模式不再写入 Codex 项目信任已归入 [v0.7.0 版本说明](v0.7.0.md)；v0.7.0 之后的中止时回收 Codex 起的命令已归入 [v0.7.1 版本说明](v0.7.1.md)；v0.7.1 之后的接口 1.3（结果文件、接着派任务、长任务、检查与写入授权、规则片段）已归入 [v0.8.0 版本说明](v0.8.0.md)；v0.8.0 之后的文档补齐已归入 [v0.8.1 版本说明](v0.8.1.md)；v0.8.1 之后的 run 命令说明修正已归入 [v0.8.2 版本说明](v0.8.2.md)。v0.8.2 之后的使用者文档补齐已归入 [v0.8.3 版本说明](v0.8.3.md)。v0.8.3 之后的无提交仓库专用诊断码已归入 [v0.8.4 版本说明](v0.8.4.md)。v0.8.4 之后的 Codex 审查 schema 修复与失败原因诊断已归入 [v0.8.5 版本说明](v0.8.5.md)。v0.8.5 之后的沙箱证书信任已归入 [v0.8.6 版本说明](v0.8.6.md)。v0.8.6 之后的审查报告补丁指纹（接口 1.4）已归入 [v0.9.0 版本说明](v0.9.0.md)。v0.9.0 之后的审查发现严重程度与复审对照上一轮（接口 1.5）已归入 [v0.10.0 版本说明](v0.10.0.md)。v0.10.0 之后的快照审查的复审（接口 1.6）已归入 [v0.11.0 版本说明](v0.11.0.md)。v0.11.0 之后的技术方案审查与第二审查者（接口 1.7）已归入 [v0.12.0 版本说明](v0.12.0.md)。v0.12.0 之后的参考文件不再要求报告覆盖已归入 [v0.12.1 版本说明](v0.12.1.md)。v0.12.1 之后的审查失败定位诊断已归入 [v0.12.2 版本说明](v0.12.2.md)。v0.12.2 之后的修复 Claude Code 后端审查在 macOS 上必然失败已归入 [v0.12.3 版本说明](v0.12.3.md)。v0.12.3 之后的未发布变更见下。历史验收记录保留其发生时的版本和状态，不追认历史批准。

<!-- release-title: doctor 子命令与 Claude Code 探测期限放宽 -->

## `delegate-exec.sh doctor` 子命令

`delegate-exec.sh` 原来只认 `review`、`run`，其余写法按旧版无子命令调用处理，所以 `delegate-exec.sh doctor` 会把「doctor」当成任务原文：不带 `--backend` 时真的派一次 Codex 只读运行，带 `--backend claude-code` 时报误导人的 `claude-code requires --review-context`。现在 `delegate-exec.sh doctor [--backend codex|claude-code] | --reviewers [--json]` 原样转交 `review_doctor.py`，与 `/delegate:doctor` 相同，不调用模型；帮助文字列出了这个子命令。

## Claude Code 探测期限放宽到 15 秒

判断 Claude Code 能不能用时，`--version`、`--help`、`auth status` 三个探测原来各只有 5 秒。Claude CLI 偶尔启动慢，探测一超时，`--backend auto` 和 `doctor --reviewers` 就会把它误判为不可用：只装了 Claude Code 的用户会拿到「未审」报告。现在每个探测 15 秒（三个最坏 45 秒），不加重试；`--backend auto` 的「未审」报告在原诊断码后追加 `probe_stage_*`，指出是哪个探测失败，`doctor --reviewers` 的输出不变。`review --backend claude-code` 的预检用同一组探测，期限同样放宽。

## 影响面

只影响第一个参数恰好是 `doctor` 的调用：以前会被当成旧版任务原文，现在改为无模型体检。写了 `-- "<任务>"` 的旧调用和 `review`、`run` 不受影响。接口版本（1.7）不变。

探测期限：只影响 Claude Code 后端的预检，以及 `--backend auto`、`doctor --reviewers` 对 Claude Code 的可用性判断。CLI 真卡住时最多多等 30 秒。报告字段、退出码与接口版本（1.7）不变。

## 验证与已知限制

新增 CLI 回归：`doctor` 加错误参数时报 `review_doctor.py` 的用法、退出 64、不启动任何执行器，帮助文字列出该子命令；修复前该测试失败。本机实跑 `delegate-exec.sh doctor --backend claude-code` 走到无模型体检。

探测期限：新增和修订的回归（修复前均失败）：三个探测拿到的期限都是 15 秒；`claude_check` 遇探测失败返回主码加阶段码、遇认证类判定失败只返回主码；`choose` 按序写入全部码；`doctor --reviewers` 只显示主码。慢启动未能稳定复现，修复后的真实效果待发版后用安装版连续重跑 3 次确认。
