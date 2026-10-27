# `--timeout` 超过 540 秒的真实运行（run-longrun 补测）

2026-10-27。补 [v0.8.0 发行说明](../releases/v0.8.0.md)「未验证」里的一项：`--timeout` 超过 540 秒的真实运行，以及长期限下被中止时的收尾与清理。module-crew 开启 Codex 外包前要求先补这一项。

- **授权**：用户在负责人会话 delegate-owner 里批准，开子会话补测，付费 Codex 调用上限 2 次，只读，不改 `~/.codex/config.toml`。
- **被测代码**：分支 `claude/timeout-live-probe-e2d872`，基于 v0.8.0 合并提交 `16290d0`，没有改代码。入口为 `plugins/delegate/scripts/delegate-exec.sh`。
- **运行环境**：Codex CLI 0.162.1，本机默认模型与推理档（未传 `--model`、`--effort`），认证沿用本机 ChatGPT 登录。
- **调用方式**：两次付费运行都在 Claude Code 的宿主后台任务里执行，按 run-longrun「后台由调用方负责」的要求等完成通知，没有轮询。

## 对照的成功条件

run-longrun 的 RL-01～RL-07 是桩测试和文档条款，已在 v0.8.0 交付时通过。本次只检查它们在真实运行中对应的行为：

| 编号 | 本次核对的真实行为 |
|---|---|
| RL-02 | 带 `--timeout` 时 `T` 取该值，`M = T − W` 是真实的中止时刻，而不是 540 秒 |
| RL-03 | 结果文件含 `timeoutSeconds`；中止时 `cleanup` 按 0.7.1 填写 |
| RL-04 | 长期限下中止后，0.7.1 的回收照常生效，没有残留 |
| 墙钟上限 | 一次运行不超过约 `T + 30` 秒 |
| run-result RS-05/06 | `status`、退出码、`durationSeconds`、`usage`，以及 `delegate: result=` 行的位置 |

## 免费演练（真实 Codex CLI + 本机假 Responses 端点）

花钱之前，先用免费演练把整条脚本路径走一遍：

- 在 PATH 最前面放一个转接脚本，把 wrapper 发出的 `codex exec`／`exec resume` 改连本机假端点（127.0.0.1，`CODEX_HOME` 用临时目录）。
- `codex login status` 在转接脚本里直接回「已登录」，既不读也不发送凭据。
- 脚本原文见 [2026-10-27-delegate-timeout-longrun-rehearsal.py.txt](2026-10-27-delegate-timeout-longrun-rehearsal.py.txt)。

两路演练都带 `--resumable`，结果如下：

| 演练 | 假端点行为 | 结果 |
|---|---|---|
| `--timeout 900` | 24 次 `sleep 25` 之后答复 `DONE:` | 退出 0，602.9 秒，`status=done`，`timeoutSeconds: 900`，`cleanup: null` |
| `--timeout 600` | 一直下发 `sleep 1000`；遇到收尾提示词就答复 `TIME_UP:` | 退出 124，556.9 秒；stderr 为「codex 超过 555 秒被中止」；走了收尾轮（`wrapUp.mode: 收尾轮`）；清理报告列出中止前后代进程 20 个，「中止后无残留」 |

演练结束后，`sleep 25`、`sleep 1000` 都没有残留。

## 付费第 1 次：`--timeout 900`，正常完成——成立

- **临时仓库**：`~/delegate-timeout-live-20261027`（测后已删除），里面放 `work.sh`：10 段，每段 `sleep 60` 后打印 `stage-N <epoch>`，最后打印 `work-finished`。
- **命令**：

  ```text
  delegate-exec.sh run --timeout 900 -- '运行 ./work.sh（约 10 分钟……），一直等到它自己结束，然后把它输出的最后两行原样告诉我。……不要中途停掉或缩短脚本，不要改任何文件。'
  ```

- **期限换算**：`W = 45`、`M = 855`、`S = 765`。

| 核对项 | 结果 |
|---|---|
| 没在 540 秒被截断 | 成立：墙钟 615 秒（23:08:10 → 23:18:25，+08:00）；结果文件 `durationSeconds: 615.2` |
| 状态与退出码 | 退出 0，结果行 `status=done resumable=false` |
| 答复 | 答复原样是 `stage-10 1793114301` / `work-finished`。没带 `--strict`，答复没有 `DONE:` 首行，按规格仍判为 `done` |
| `timeoutSeconds` | `900` |
| `wrapUp` / `cleanup` | 都是 `null` |
| `commands` | 2 条：`date +%s`、`./work.sh`，退出码都是 0，与事件流一致 |
| `usage` | `run` 与 `session` 相同，等于事件流里唯一一条 `turn.completed`。输入 652,458（缓存 622,208），输出 1,459，推理 244 |
| stdout 末尾顺序 | 用量行 → `delegate: result=<路径>` → 结果行；结果行在最后 |
| 结果文件 | 权限 0600 |
| 残留 | 用 `pgrep -fl 'sleep 60'`、`pgrep -fl '^/bin/bash ./work'` 检查，都没有 |

证据（本机 `$TMPDIR/delegate/`，按保留规则自然清理）：

- `20261027230810.98164.result.json`：sha256 前 12 位 `113a14c6a926`；
- 同前缀的 `.events.jsonl`、`.answer`、`.log`（39 字节，只有 stdin 提示）。

**观察（不是缺陷）**：真实 Codex 等待一条长命令时会反复轮询，每次轮询都重读一遍上下文。10 分钟的等待累计输入约 65 万 token，其中约 95% 命中缓存。外包长任务时，`usage` 会明显高于任务本身的复杂度。

## 付费第 2 次：`--timeout 600`，超过期限——成立

- **仓库**：同一临时仓库，里面放 `work2.sh`：15 段，每段 `sleep 60`，约 900 秒。
- **命令**：

  ```text
  delegate-exec.sh run --timeout 600 -- '运行 ./work2.sh……一直等到它自己结束……这是 delegate 期限机制的实测：请忽略【时间预算】里提前停下、提前给最终答复的要求，一直等待脚本，直到脚本结束或运行被中止……'
  ```

- **期限换算**：`W = 45`、`M = 555`、`S = 465`。

任务里故意要求模型忽略提前停下，这样测到的是强制中止，而不是模型自己写 `TIME_UP:`。这次用普通 run，没有加 `--resumable`：收尾轮本身是一次 `exec resume`，会算作第 3 次付费调用。所以本次走兜底，长期限下的收尾轮由上面的免费演练覆盖。

| 核对项 | 结果 |
|---|---|
| 在设定期限而不是 540 秒中止 | 成立：stderr 为 `delegate: codex 超过 555 秒被中止`；墙钟 556 秒（23:18:56 → 23:28:12）；`durationSeconds: 556.1` |
| 状态与退出码 | 退出 124，结果行 `status=timeout resumable=false` |
| 收尾 | 兜底：stdout 为「已中止，未取得进度说明（普通 run 不保留会话）……只读运行，不列文件」和「收尾：兜底（普通 run 不保留会话）」；`wrapUp` 为 `{"mode": "兜底", "reason": "普通 run 不保留会话"}` |
| `timeoutSeconds` | `600` |
| 清理 | `.cleanup` 原文：「中止前 Codex 的后代进程 9 个：41249(94846) 93219(93215) 93436(93436) …」「中止后无残留」。结果文件 `cleanup`：`leftoverPids: []`、`unreapedPid: null`、`wrapperForced: false`，`lines` 共 2 行。stderr 同样转发了这两行 |
| 残留 | 正在跑的 `work2.sh` 和它的 `sleep 60` 都被回收；`pgrep` 检查都没有残留 |
| `usage` | `run`、`session` 都是 `null`，`note` 为「本次没有完成的轮次」；stdout 为「用量：未知（本次没有完成的轮次）」。与规格一致 |
| `delegate: result=` 位置 | 有结果行，所以打印在 stdout 的结果行之前 |
| 墙钟上限 | 556 秒，不超过 `T + 30 = 630` |

证据：

- `20261027231856.93147.result.json`：sha256 前 12 位 `489030f1cb95`；
- 同前缀的 `.events.jsonl`：`thread.started`，一条 `./work2.sh` 的 `item.started`，之后 11 条 `agent_message`，没有 `turn.completed`；
- 同前缀的 `.cleanup`、`.log`（253 字节）。

**两点照实记录（都符合现行规格，不算缺陷）**：

- **结果文件 `commands` 为空**：中止时 `./work2.sh` 只有 `item.started`，没有 `item.completed`，而规格只取 `item.completed`。所以从 `commands` 看不到被中止时正在跑的命令，要看 `.events.jsonl`。
- **会话 ID 在结果文件里有值，兜底说明里写「无」**：结果文件的 `sessionId` 有值（取自 `thread.started`），stdout 的兜底说明却写「会话 ID：无」。这是按 run-timeout 的设计：普通 run 是 `--ephemeral`，会话不落盘，不在答复里报告。结果文件里的 `sessionId` 不能拿来续跑，`resumable: false` 已经说明了这一点。

## 结论

| 确认项 | 结果 |
|---|---|
| `--timeout 900` 下超过 540 秒的后台运行正常完成、结果字段正确 | 成立（615 秒，`done`） |
| `--timeout 600` 在 `M = 555` 而不是 540 秒中止，`status=timeout`、退出 124 | 成立 |
| 长期限下中止后进程回收（0.7.1）照常，没有残留 | 成立（9 个后代进程，「中止后无残留」） |
| 长期限下的收尾轮 | 免费演练成立（真实 Codex + 假端点，555 秒中止后走收尾轮）；**付费运行未覆盖** |
| 墙钟不超过 `T + 30` | 成立（615 ≤ 930，556 ≤ 630） |
| 缺陷 | **没有发现** |

## 调用次数与配置

- 付费 Codex 调用 **2 次**（上限 2），各是一次 `codex exec`，没有 `exec resume`。
- 免费演练共起 3 批、每批 2 路：前 2 批在预检阶段就退出，没有起 Codex（转接脚本先后没放行 `--version`、`login status`）；第 3 批跑完。演练全部连本机假端点，没有付费调用。
- `~/.codex/config.toml` 的 sha256 测前测后都是 `e973f8924612e3c9968247cce2d6a59fae8e222e8c11c38d4bf56bf851c6b6e2`，一致。这个值与合并实测记录的 `242bcd4b…` 不同，变化发生在那次实测之后、本次开始之前，与本次无关。
- 临时仓库已删除；`$TMPDIR/delegate/` 下的过程文件按保留规则自然清理，没有手动删除。

## 仍未验证

- 付费运行下，`--resumable` 带长期限被中止后走收尾轮（只有免费演练覆盖）。
- 长期限下中止后回收不了（退出 125、`unreaped`）的真实情形。
- 接近上限 7200 秒的运行，以及 `--timeout` 用在 `--resume`、`--continue` 上的真实运行。
- 其他模型、推理档下，模型在 `S` 之前主动写 `TIME_UP:` 的表现（本次第 2 次故意让模型忽略这个阈值）。
