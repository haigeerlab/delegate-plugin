---
description: "把已明确任务交给 Codex 执行，默认只读，显式 write 才可改文件"
argument-hint: "[--backend codex] [--write] [--model <slug>] [--effort <level>] [--resumable] [--strict] <任务> | --resume <runId> [--write] [--strict] <用户答复> | --continue <runId> [--write] [--strict] <下一个任务>"
allowed-tools: Bash
---

用户直接输入本命令授权其明确任务；模型主动提议后须等待肯定答复。只委托已决策且用户明确交代的范围，不补充任务、不重复索取已有的同范围授权。

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run [选项] -- "<任务>"
```

任务作为一个完整参数安全引用；Bash timeout 设为 600000。在业务 Git 工作区执行。run 当前只支持 codex，默认只读；`--backend claude-code` 明确拒绝，Claude 仅通过 `/delegate:review` 提供只读审查。需要共同结构化审查时也使用 review；run 不接受 review-context 或范围快捷参数。

只有用户在该轮明确要求写文件才能加 `--write`，不自行升级权限。写入返回后无论成功、失败、超时或空答复，都核对 Git 验收块和真实 diff；失败不自动回滚，不能只相信执行器自述。所有 run 固定 `approval_policy="never"`，不用本机配置的审批方式：越出沙箱的命令（如 worktree 里 `git commit`、网络访问）直接被拒，提交靠前缀放行规则或由调用方完成。沿用 Codex 原有认证、沙箱、期限和日志合同，不自动重试、切后端或切模型，不提交、推送或发布。

默认/上限 540 秒；中止时冻结 Codex 并回收它的全部后代进程组（含换组、换会话的命令），清理结果与残留 PID 输出到 stderr；执行进程未能回收时退出 125。旧过程日志位于 `${TMPDIR:-/tmp}/delegate/`，最终答复分开返回；只按需用 `sed -n` 读取必要片段，不 `cat` 整个日志。递归调用 delegate 被拒绝。实际宿主/模型无法核实时标 unknown。

成功和超时时 stdout 末行是 `delegate: run_id=<id> status=<done|needs-input|timeout> resumable=<true|false>`；失败、信号中断、空答复不输出。判断成功先看退出码 0 再看 `status=done`；status 是开放集合，不认识的值当失败。

读结果文件或用 `--strict`、`--continue` 等 1.3 参数前，必须先读 `${CLAUDE_PLUGIN_ROOT}/references/run.md` 对应一节。

超时 `status=timeout` 一律退出 124：提示词附时间预算，模型应到期前主动停下、首行 `TIME_UP:` 写进度；被强制中止时可续跑 run 再只读收尾一轮，否则输出不靠模型的兜底（写模式附改动文件）。超时不等于完成，进度交用户，续跑由用户决定。

可续跑模式只在用户或使用方开关明确要求时加 `--resumable`：Codex 会话会保存在它自己的会话目录，可以停下来问用户。`status=needs-input` 退出码仍为 0，答复以 `NEED_USER:` 开头，标记之后的全部内容就是要问用户的问题，要原样转给用户；它不是失败，也不是批准。模型漏写标记时会判为 done，仍须读答复全文。用户答复后续跑：

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --resume <runId> [--write] -- "<用户答复>"
```

答复必须是用户本人的原话，或用户明确同意的转述；不得替用户回答问题。只能续跑最近一轮且状态为 needs-input 或 timeout 的 runId，同一仓库，`--write` 有无须与原运行一致（原运行须已获写入授权且用户答复未收回）；不接受 `--model`、`--effort`、`--resumable`，沿用原设置。每轮返回新 runId，可接着续跑。拒绝时退出 64，不启动 Codex。失败或普通 run 超时须重新发起。

原 `/delegate:delegate` 源命令已替换为 run/review；旧 codex-exec.sh 和 delegate-exec.sh 无子命令调用继续有效。安装缓存不会随源码更新，加载/安装另行处理。帮助见 `/delegate:help`。
