---
description: "把已明确任务交给 Codex 执行，默认只读，显式 write 才可改文件"
argument-hint: "[--backend codex] [--write] [--model <slug>] [--effort <level>] <任务>"
allowed-tools: Bash
---

用户直接输入本命令授权其明确任务；模型主动提议后须等待肯定答复。只委托已决策且用户明确交代的范围，不补充任务、不重复索取已有的同范围授权。

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run [选项] -- "<任务>"
```

任务作为一个完整参数安全引用；Bash timeout 设为 600000。在业务 Git 工作区执行。run 当前只支持 codex，默认只读；`--backend claude-code` 明确拒绝，Claude 仅通过 `/delegate:review` 提供只读审查。需要共同结构化审查时也使用 review；run 不接受 review-context 或范围快捷参数。

只有用户在该轮明确要求写文件才能加 `--write`，不自行升级权限。写入返回后无论成功、失败、超时或空答复，都核对 Git 验收块和真实 diff；失败不自动回滚，不能只相信执行器自述。沿用 Codex 原有认证、沙箱、期限和日志合同，不自动重试、切后端或切模型，不提交、推送或发布。

默认/上限 540 秒；Codex 保留原进程组清理，不证明 detached 后代已回收。旧过程日志位于 `${TMPDIR:-/tmp}/delegate/`，最终答复分开返回；只按需用 `sed -n` 读取必要片段，不 `cat` 整个日志。递归调用 delegate 被拒绝。实际宿主/模型无法核实时标 unknown。

原 `/delegate:delegate` 源命令已替换为 run/review；旧 codex-exec.sh 和 delegate-exec.sh 无子命令调用继续有效。安装缓存不会随源码更新，加载/安装另行处理。帮助见 `/delegate:help`。
