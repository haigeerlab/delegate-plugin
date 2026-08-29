---
description: "把已经决策完毕的任务委托给 Codex（默认只读，--write 才可改文件）"
argument-hint: "[--write] [--model <slug>] [--effort <level>] <任务>"
allowed-tools: Bash
---

把用户已经明确决策完毕的任务交给 Codex。只原样委托用户在本轮明确交代的任务；不要补充、扩展或推断范围。

调用方式：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/codex-exec.sh" [选项] "<任务>"
```

`<任务>` 必须作为一个完整参数传入，必须加引号。调用 Bash 时把 timeout 设为 `600000`；默认的 120 秒对 Codex 经常不够，超时会白烧一次调用。

默认是只读。只有用户在**该轮**明确要求写文件时才可以加 `--write`；不得自行升级为写模式。

`--write` 返回后，必须查看输出中的 git 验收块：基线 HEAD、`git status --short` 和 `git diff --stat`。不能只相信 Codex 的自述。

wrapper 只返回最终答复；过程日志保存在 `${TMPDIR}/delegate/`。需要证据时，按输出给出的路径用 `sed -n` 取所需几行；不要 `cat` 整个日志，否则会把节省下来的上下文重新灌回来。
