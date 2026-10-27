# /delegate:run 参考（接口 1.3）

`/delegate:run` 的命令说明受体积限制，1.3 各参数的用法和授权纪律写在这里。使用下面任何一项之前先读完对应一节；没读到的纪律不能当作已获授权。

## 结果文件与 `--strict`

- 每次启动过 Codex 的运行都写一份 JSON 结果文件 `${TMPDIR:-/tmp}/delegate/<runId>.result.json`（0600）。有结果行时，结果行前一行是 `delegate: result=<路径>`；失败、中断、未能回收（退出 125）、空答复时这一行在 stderr，`status` 分别为 `failed`、`interrupted`、`unreaped`、`empty`。
- 机器读取运行结果用这个文件，不解析过程日志。过程日志是两个文件：`<runId>.events.jsonl`（Codex 的 JSON 事件流）和 `<runId>.log`（stderr）；只按需用 `sed -n` 读片段。
- token 是 Codex 的会话累计值：`usage.session` 是整个会话的总量，`usage.run` 是本次用量（续跑取与上一轮的差值）。不要把各轮的 `session` 相加。
- `--strict`：提示词要求最终答复首行必须是 `DONE:`、`NEED_USER:`（仅可续跑）或 `TIME_UP:`，并声明它优先于项目 AGENTS.md 的格式要求。缺标记判 `status=unmarked`、退出 1，不算完成，也不能续跑。
- 判断成功仍先看退出码为 0，再看 `status=done`；`status` 是开放集合，不认识的值当失败。

## `--continue`：done 之后接着派下一个任务

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" run --continue <runId> [--write] [--strict] -- "<下一个任务>"
```

- 只接受 `--resumable` 起头的链上、状态为 `done` 的 runId；`needs-input`、`timeout` 仍用 `--resume`，`unmarked` 和失败的运行不能接。
- 同一仓库根目录，`--write` 有无须与原运行一致，模型和推理档沿用原运行，不接受 `--model`、`--effort`、`--resumable`、`--resume`。一个 runId 只能被 `--resume` 或 `--continue` 接一次；每轮返回新 runId，`parent` 指向上一轮，可以一直接下去。拒绝时退出 64，不启动 Codex，`run not done` 表示状态不是 done。
- 纪律：任务正文必须来自已批准 Plan 里的 Task 或用户本人的要求，不得自行编写；`--continue --write` 的前提与 `--resume --write` 相同（原运行已获写入授权且没有收回）；上一轮的 `done` 不代表上一个 Task 已验收，核对、提交仍由调用方做完再派下一个。
- 链上的状态文件和结果文件保留 14 天，过程日志仍只保留最近 50 组；日志被清掉后仍可以接着跑，只是旧轮的日志查不到。
