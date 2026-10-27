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

## `--timeout`：放大期限

- `--timeout <秒>` 只能把期限放大到 541～7200 秒（十进制整数），其他值退出 64、不启动 Codex。不带时仍是默认 540 秒，`DELEGATE_TIMEOUT_SECONDS` 仍只能缩短默认值；带 `--timeout` 时忽略这个环境变量。可用于普通 run、`--resumable`、`--resume`、`--continue`，每次调用各自给，不随链继承。
- 期限的分配与默认期限相同：收尾轮 `W = min(45, T // 6)`、主运行 `M = T − W`，提示词里的阈值 `S = max(M − 90, M // 2)`；例如 `T = 1800` 时 `M = 1755`、`S = 1665`。时间预算段、收尾轮、兜底和退出码都不变，结果文件记 `timeoutSeconds`。
- 后台调用要求：
  1. `--timeout` 超过宿主前台命令的期限时（Claude Code 的 Bash 前台上限为 600 秒），必须用宿主的后台模式调用，并等宿主的完成通知，不要轮询。
  2. delegate 不提供后台启动、查询、取消；要停下一次运行，就停止那个宿主后台任务，delegate 按收到信号处理（退出 143／130／129），并回收 Codex 起的全部后代进程。
  3. 一次运行最多约 `T + 30` 秒才结束（中止清理与收尾的余量），给后台任务的等待上限不要小于这个数。

## `--check`：做完后跑检查

- `--check "<命令>"` 在运行以 `done` 结束后，由 delegate 在仓库根按参数列表执行（不经 shell，stdin 为空，期限 600 秒），结果写进结果文件的 `check`（`passed`、`failed`、`timeout`、`cannot-run`、`unreaped`、`skipped`），元数据里有一行「检查：…」。其他状态不执行，记为 `skipped`。检查结果不改变运行本身的状态和退出码，要看 `check.status` 自己判断。
- 命令按 module-crew S30 的规则校验：先 POSIX `shlex.split`，任何 token 以 `&&`、`||`、`;`、`|`、`>`、`<`、`` ` ``、`$(` 开头或结尾就拒绝（退出 64，不启动 Codex），拒绝文案与 module-crew 一字不差。要组合多步，写进项目脚本，或写成 `/bin/sh -c '<原命令>'`。
- **纪律：检查命令在沙箱外以用户的权限执行，只能取自项目配置里用户批过的 checkCommand 或 quickCheckCommand，不能由 Codex、调用方模型或模块会话临时拼写。** delegate 无法核实来源。

## `--authorized-by`：事先给好的写入授权

- 写法：`run --write --authorized-by <文件> …`，可用于 `--write` 的普通 run、`--resumable`、`--resume`、`--continue`。没有 `--write` 时拒绝；文件须是普通文件、不是软链接、可读、非空、不超过 64 KiB，否则 `authorization file not usable`。
- delegate 只记录文件的路径、sha256、大小（结果文件的 `authorization`，元数据「写入授权：…」），不读也不解释内容。一条链上一旦记录了授权文件，后面每一轮的 `--write` 都必须给同一个文件（sha256 相同），缺了或不同就拒绝 `authorization mismatch`。写模式没带它时记为「当轮」授权。
- **纪律：只有下面四条同时满足，才可以不等用户在当轮开口，就带 `--write --authorized-by <文件>`：**
  1. 用户打开外包开关时的原话，已经由使用方（module-crew）记录成这个文件；
  2. 这个模块的 Spec 和 Plan 已批准，派出的 Task 在已批 Plan 之内；
  3. 同一个模块、同一个 worktree；
  4. 授权来源由 delegate 写进每次的结果（`authorization` 字段），调用方不得删除或改写。
- 任何一条不满足，就回到原规则：只有用户当轮明确要求才加 `--write`。delegate 只能核对第 3 条的仓库部分与文件是否一致，其余由调用方负责；这是命令指令层面的纪律，不是技术锁。
