# S38 前置实测：`--json` 事件、续跑压缩、worktree 与长运行

2026-10-27。起因是生态方案 S38（模块整体外包给 Codex，interface 1.3），用户已批准方案并授权写 Spec 前的 T1～T5 付费实测（计划约 18 次，上限 25 次）。本记录只做实测，不写 Spec、不改产品代码。

- 基准：main `4f87049`（v0.7.0 之后，含 PR #18）。Codex CLI `0.162.1`；模型 `gpt-6.1-sol`（本机默认），推理档未指定时为配置默认 `high`；T2 用 `low`（对应 delegate `--effort low`，只为缩短每轮耗时，与压缩机制无关）。
- 认证沿用本机 ChatGPT 登录；每次调用都和产品一样传 `-c forced_login_method="chatgpt" -c model_provider="openai" -c approval_policy="never"`，并去掉 `OPENAI_API_KEY`／`CODEX_API_KEY`，`stdin=/dev/null`，只读沙箱。
- 临时目录（家目录下新建，测后删除）：`~/delegate-s38-probe-20261027133055`（`step01..12.txt` 各含一个随机 token；`big/big01..60.txt` 各约 65KB 随机数字、第一行是 `SECRET-NN-…`）、`~/delegate-s38-wt-20261027133247` 及其三个 worktree `-a`／`-b`／`-c`。
- 驱动脚本原文：[2026-10-27-delegate-s38-probe.py.txt](2026-10-27-delegate-s38-probe.py.txt)。它按 `codex-exec.sh` 的参数直接调 `codex exec`／`codex exec resume`，另加 `--json`，stdout（JSONL）、stderr、`-o` 答复分别落盘；`runcodex` 模式经产品 `run_codex.py` 调用。T2 的循环与 T5 的包装脚本见文末附录。

## T1：`--json` 事件流的字段形状（2 次）

做法：一次只读 run（4 条命令，第 3 条 `cat does-not-exist.txt` 故意失败），再对同一会话 `exec resume --json` 一次（2 条命令，第 2 条 `ls no-such-dir` 故意失败）。两次都同时带 `-o`。

| 编号 | 命令 | 耗时 | 退出 | 事件行数 |
|---|---|---|---|---|
| T1a | `codex exec … --sandbox read-only --color never --json -o <answer> -- <prompt>` | 26.3 s | 0 | 13 |
| T1b | `codex exec resume … -c sandbox_mode="read-only" --json -o <answer> -- <会话ID> <prompt>` | 21.3 s | 0 | 10 |

### stdout 事件（两次形状一致）

```text
{"type":"thread.started","thread_id":"01a17bd7-5818-71b2-971d-dfe40eefa843"}
{"type":"turn.started"}
{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"我会按顺序逐条执行…"}}
{"type":"item.started","item":{"id":"item_3","type":"command_execution","command":"/bin/zsh -lc 'cat does-not-exist.txt'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
{"type":"item.completed","item":{"id":"item_3","type":"command_execution","command":"/bin/zsh -lc 'cat does-not-exist.txt'","aggregated_output":"cat: does-not-exist.txt: No such file or directory\n","exit_code":1,"status":"failed"}}
{"type":"item.completed","item":{"id":"item_5","type":"agent_message","text":"已按顺序执行…"}}
{"type":"turn.completed","usage":{"input_tokens":124735,"cached_input_tokens":112256,"cache_write_input_tokens":0,"output_tokens":391,"reasoning_output_tokens":0}}
```

- **会话 ID**：`thread.started.thread_id`，resume 时与原会话相同。开 `--json` 后 stdout 里**没有**文本日志那行 `session id: <uuid>`（stderr 只有一行 `Reading additional input from stdin...`，resume 时 stderr 为空）。`run_state.session_id_from_log` 现在靠这行取会话 ID，改用 `--json` 后必须改从 `thread.started` 取。
- **命令与退出码**：`item.completed` 且 `item.type == "command_execution"`：`command`（外面包了一层 `/bin/zsh -lc '…'`）、`exit_code`（整数）、`status`（`completed`／`failed`，失败与非零退出码一致）、`aggregated_output`（**完整输出**，不受模型侧截断影响，T2 里单条 65KB 原样在里面）。`item.started` 同 id 先出现一次，`exit_code` 为 `null`。
- **item id 每轮从 `item_0` 重新编号**，resume 那一轮也从 `item_0` 开始，跨轮不能当唯一键。
- **最终答复**：最后一个 `agent_message` 的 `text` 与 `-o` 文件内容逐字一致（两次都是）。`--json` 与 `-o` 同用正常，互不影响。
- **token**：只有 `turn.completed.usage`，字段为 `input_tokens`、`cached_input_tokens`、`cache_write_input_tokens`、`output_tokens`、`reasoning_output_tokens`。**它是整个会话的累计值，不是本轮的**：T1b 的 `input_tokens` 是 201,493 = T1a 的 124,735 + 本轮 3 次请求约 76,758，与会话文件里 `total_token_usage` 完全相同。
- **上下文窗口、限流**：stdout 事件里**都没有**。两者只在 Codex 自己的会话文件（`~/.codex/sessions/YYYY/MM/DD/rollout-…-<id>.jsonl`，只读查看）的 `event_msg` / `token_count` 里，每次模型请求后写一条：

```text
{"type":"event_msg","payload":{"type":"token_count","info":{
  "total_token_usage":{"input_tokens":124735,"cached_input_tokens":112256,…,"total_tokens":125126},
  "last_token_usage":{"input_tokens":25210,"cached_input_tokens":24960,…,"total_tokens":25343},
  "model_context_window":475000},
 "rate_limits":{"limit_id":"codex","primary":{"used_percent":<百分比>,"window_minutes":<分钟>,"resets_at":<epoch秒>},
  "secondary":null,"credits":{…},"plan_type":"<套餐>","rate_limit_reached_type":null}}}
```

  `last_token_usage.input_tokens` 是最近一次请求送进模型的上下文大小（T1a 五次请求 24,663 → 25,210），`model_context_window` 本机为 475,000。`task_started`／`task_complete` 也在会话文件里，带 `duration_ms`、`time_to_first_token_ms`。会话文件 `session_meta` 里还有账号标识与额度余额，结果文件不应照抄。
- **`--ephemeral` 的 run 不写会话文件**，所以普通 run 拿不到上下文窗口和限流，只有 stdout 的累计 token。
- 本机 hook（SessionStart、UserPromptSubmit）在文本日志里有 `hook:` 行，`--json` 流里没有对应事件。

## T3：git worktree 下 Codex 是否读 AGENTS.md（1 次）—— **读，而且照做**

做法：临时仓库根目录提交一份 `AGENTS.md`（「每次最终答复最后单独一行必须原样写 `暗号：青柠-7351`」），`git worktree add` 出 `-c`，在 `-c` 里跑一次只读 run，任务只说「`cat marker.txt`，一句话告诉我内容」，不提 AGENTS.md。

- 答复：「`marker.txt` 的内容是 `main-checkout`。」下一行「暗号：青柠-7351」。16.3 s。
- 会话文件里注入的是 `# AGENTS.md instructions for /Users/vilin/delegate-s38-wt-20261027133247-c`，即 **worktree 自己的路径**（worktree 的 `.git` 是指向主仓库的文件，Codex 仍以 worktree 根为项目根）。
- 同一份 AGENTS.md 在 T4 的两次 delegate run 里也生效：任务要求「用两行写出」，答复仍多了第三行暗号——**项目 AGENTS.md 能改动 delegate 任务要求的答复格式**。本机另有全局 `~/.codex/AGENTS.md`，未单独区分它与项目文件的合并顺序。

## T4：两个 worktree 同时跑 delegate run（2 次）—— **不串**

做法：用本仓库的 `plugins/delegate/scripts/codex-exec.sh --resumable`（真实产品脚本，只读）在 worktree `-a`、`-b` 里同时后台启动，各自的 `marker.txt` 是不同随机值（已提交到各自分支）。任务：`cat marker.txt` 与 `git branch --show-current`。

| | runId | 会话 ID | `.state.json` 的 repository | 答复 | 退出 |
|---|---|---|---|---|---|
| a | `20261027133326.79650` | `01a17bd9-66cd-…a390` | `…-wt-20261027133247-a` | `WT-A-889f0d8e` / `wt-a` | 0 |
| b | `20261027133326.79651` | `01a17bd9-66d2-…31c9` | `…-wt-20261027133247-b` | `WT-B-b8581d31` / `wt-b` | 0 |

- 两路在**同一秒**启动，runId 时间戳部分相同，只靠 `$$`（PID）区分；同一台机器上同时存活的进程 PID 不会相同，所以不会撞。
- 两路共用 `$TMPDIR/delegate/`（本机 `/var/folders/…/T/delegate`，测时共 64 个文件），各自的 `.log`／`.answer`／`.state.json` 齐全、内容各归各；`repository` 记的是各自 worktree 根，所以拿 a 的 runId 在 b 里续跑会被现有的 `repository mismatch` 挡住。
- 总耗时约 31 s，两路几乎同时结束（日志 mtime 差 2 s）。
- 只测了只读、`--resumable`、各跑一轮；同时续跑同一条链、写模式并发、清理规则在并发下删到对方文件没测。

## T2：done 之后连续续跑，会不会自动压缩、能否观测（11 次）—— **会，第 8 轮触发；`--json` 流里看不到**

做法：T2r00 新起一个**不带 `--ephemeral`** 的只读会话读 4 个大文件；之后 T2r01～T2r10 每轮 `codex exec resume --json` 同一会话（每轮都是在上一轮 done 之后续跑，正是 `--continue` 要放开的场景），每轮读 3 个新大文件，并凭记忆列出至今读过的全部 SECRET。推理档 `low`。

校准：T2r00 里模型自己给 `exec_command` 传了 `max_output_tokens:1000`，单个 65KB 文件（原始 16,261 token）进上下文后只剩约 4.4KB，照此 10 轮撑不满窗口。所以 T2r01 起在提示词里要求「把 `max_output_tokens` 设为 20000」（只改提示词，不改配置），每轮约增加 5.6 万 token。**JSONL 的 `aggregated_output` 不受这个截断影响**，始终是完整 65KB。

| 轮 | 耗时 s | 本轮结束时上下文（会话文件 `last_token_usage.input_tokens`） | `turn.completed.usage.input_tokens`（累计） |
|---|---|---|---|
| 00 | 37.5 | 31,445 | 140,349 |
| 01 | 51.4 | 84,748 | 370,107 |
| 02 | 39.9 | 141,175 | 822,521 |
| 03 | 76.7 | 197,613 | 1,499,740 |
| 04 | 69.7 | 254,096 | 2,402,857 |
| 05 | 44.4 | 310,538 | 3,531,868 |
| 06 | 32.7 | 367,054 | 4,887,762 |
| 07 | 28.8 | 423,586 | 6,469,810 |
| 08 | 49.1 | **42,916**（轮内压缩） | 7,415,629 |
| 09 | 34.3 | 108,202 | 7,736,129 |
| 10 | 34.4 | 164,831 | 8,283,100 |

- **触发点**：第 8 轮读完第 2 个文件后上下文 448,712（窗口 475,000 的 94.5%），下一次请求前 Codex 自动压缩，会话文件写入一条 `{"type":"compacted","payload":{"replacement_history":[…14 条],"window_number":1,"retained_context":{…},…}}`（约 62KB），随后 `token_count` 归零再从 24,198 起算。压缩发生在**轮中**，本轮照常读完第 3 个文件、正常结束，退出 0。
- **`--json` stdout 里没有任何压缩事件**：第 8 轮的事件流与其他轮形状一样（`thread.started`、`turn.started`、命令项、`agent_message`、`turn.completed`），没有新的 item 类型。`turn.completed.usage` 是累计值，压缩后也不会下降。唯一的间接迹象是累计值的轮间增量变小（第 7 轮 +1,582,048，第 9 轮 +320,500），不足以可靠判断。
- **能观测的地方只有会话文件**：`type == "compacted"` 记录，以及 `token_count.info.last_token_usage.input_tokens` 骤降。`--ephemeral` 的 run 没有会话文件，观测不到。
- **压缩后的记忆**：第 8～10 轮凭记忆列出的 SECRET 全对（第 10 轮 34 个按集合核对一致）。但前几轮的答复里已经逐轮列过这些值，压缩保留的历史消息里就有，所以这只说明「答复里写过的结论能跨压缩保留」，不说明工具输出原文能保留。
- 11 轮合计累计输入 828 万 token（其中缓存 744 万），说明长链续跑每轮都要重送全部上下文，越往后单轮越贵，直到压缩。

## T5：超过 540 秒的运行（2 次）

做法：包装脚本经产品 `run_codex.py 700` 调驱动（即把期限放到 700 秒，不改 delegate 源码），整条命令放在 Claude Code 的后台任务里跑（宿主后台模式）。任务：12 步，第 N 步单独 `sleep 47 && cat stepNN.txt`。运行中抓一次进程树，结束后查残留。

### T5a：约 11 分钟正常跑完 —— **成立**

- 656.4 s 正常结束，`run_codex.py` 退出 0（会话文件 `duration_ms` 647,765）。12 条命令退出码全为 0；答复 12 个 token 与文件逐个一致；最后一个 `agent_message` 与 `-o` 文件逐字一致。结束后无残留 `sleep 47`、无残留 codex 进程。
- 每步实际约 54 s（47 s sleep + 约 7 s 模型往返）；单条命令 47 s 期间事件流没有输出，`item.started` 到 `item.completed` 之间是空白。
- **进程树（第 150 秒快照）**：

```text
  PID  PPID  PGID  command
86878 86862 86878  python3 -B run_codex.py 700 …
86911 86878 86911  node …/bin/codex exec …                 ← run_codex 用 start_new_session 起的组
86928 86911 86911  …/codex-darwin-arm64/…/codex exec …
91230 86928 91230  /bin/zsh -lc sleep 47 && cat step03.txt  ← Codex 的命令在【自己的新进程组】
91275 91230 91230  sleep 47
```

  Codex 执行的每条 shell 命令都在**另一个进程组**里（T5b 快照同样如此：codex 组 10607，命令组 12214）。`run_codex.py` 的 `stop_group` 只对 Codex 的组 `killpg`，**打不到正在执行的命令**；能否清掉它们完全取决于 Codex 自己收到 SIGTERM 后是否回收子进程，Codex 被 SIGKILL 时则一定留下孤儿。

### T5b：运行到 150 秒时向 `run_codex.py` 发 SIGTERM —— **没有在 60 秒内退出**

- 驱动在第 150.1 s 对 `run_codex.py` 发 SIGTERM（模拟宿主停止 delegate；`codex-exec.sh` 的 `finish` 也是这样对 `RUNNER_PID` 发 TERM），然后等 60 s：`run_codex.py` **始终没有退出**，第 210.1 s 被驱动兜底 SIGKILL（退出 -9）。`-o` 答复文件没有写（符合预期）。
- 事件流停在第 2 步的 `item.started`（`sleep 46 && cat step02.txt`），没有 `item.completed`；会话文件最后一次写入在 SIGTERM 前约 48 s（第 2 步命令发起时）。
- 事后（约 70 s 后）没有残留 `sleep 46`，也没有残留 codex 进程。但第 2 步的 `sleep 46` 本来就会在约第 149 s 自己结束，**这次「无残留」是时间凑巧，不能证明清理有效**。
- 免费排查（不调用模型）：
  - 假 Codex（Python，子进程放进新进程组跑 `sleep 33`）：无论是否忽略 SIGTERM，`run_codex.py` 都在 1.1～2.1 s 退出 143，但**新进程组里的 `sleep 33` 两次都残留**——与上面的进程树结论一致。
  - 真实 Codex 指向本机一个只收不答的假端点（`-c model_providers.bh=…`，不带凭据、`--ephemeral`）挂在模型请求上：`run_codex.py` 收到 SIGTERM 后 1.1 s 退出 143，无残留。
  - 「进程组里有僵尸时 macOS `killpg` 报 EPERM、信号没送到」：构造后 SIGTERM／SIGKILL 都正常送达，排除。
  - 所以挂住只出现在「真实 Codex 正在执行 shell 命令时被 TERM」这一种情形，**根因没定位**（候选：Codex 收到 TERM 后等在途命令、`run_codex.py` 在 `stop_group` 某一步卡住）；按授权不再加付费调用复测。

## 对 1.3 设计的直接结论

1. **结果文件各字段取自哪里**（都以开 `--json` 为前提）：
   - 会话 ID：`thread.started.thread_id`（开 `--json` 后文本行 `session id:` 不再出现，`run_state.session_id_from_log` 要改）。
   - 命令与退出码：`item.completed` 中 `item.type == "command_execution"` 的 `command`、`exit_code`、`status`；`aggregated_output` 是完整输出，结果文件只应截尾保存。item id 每轮从 `item_0` 重编，不能跨轮当键。
   - 最终答复：继续用 `-o` 文件（与最后一个 `agent_message.text` 一致）；`--json` 与 `-o` 可同用。
   - token：`turn.completed.usage`，但它是**整条会话的累计值**。单次 run 的用量 = 本次累计 − 父 run 的累计；方案里「沿 parent 链累加」会重复计数，应改为「链上最后一次的值就是整条链的总量，单次取差值」。普通 `--ephemeral` run 只有一轮，累计值即本次。
   - 耗时：事件里没有时间戳，由 delegate 自己计时。
   - 限流／额度：stdout 事件里**没有**。只有 Codex 会话文件 `token_count.rate_limits`（`primary.used_percent`、`window_minutes`、`resets_at`、`rate_limit_reached_type` 等）。要做 `doctor.quota` 只能读会话文件，而普通 run 带 `--ephemeral` 不写会话文件；读会话文件也与 run_state 现在「不读 Codex 会话文件」的约定冲突，需要在 Spec 里单独决定。
2. **上下文用量能否观测**：`--json` 流里不能；会话文件里能（`model_context_window` 本机 475,000、`last_token_usage.input_tokens`、`type: compacted`）。Codex 在约 94% 时自动压缩，压缩对调用方透明、本轮正常结束。`--continue` 长链不必由 delegate 管上下文；若结果文件要报上下文占用或「发生过压缩」，同样只能读会话文件。
3. **`--rules-file` 与 AGENTS.md**：worktree 下 Codex 会自动读该 worktree 根的 AGENTS.md 并照做，且能改动 delegate 任务要求的答复格式。所以 `--rules-file` 不是「让 Codex 看到项目规则」的唯一途径：项目已有 AGENTS.md 的部分 Codex 本来就会读，`--rules-file` 适合放 AGENTS.md 之外、本次委托专用的片段；两者冲突时谁优先，Codex 端没有机制保证，只能靠前言措辞。还要防 AGENTS.md 要求「首行写某某」时挤掉 `NEED_USER:`／`TIME_UP:` 首行标记，`--strict` 判定时要考虑。
4. **并发**：两个 worktree 同时跑不串（runId 靠 PID 区分，状态按 worktree 根记录）。除了方案里已列的「50 组清理规则会删掉链上状态」之外，本次没发现别的必须改的地方。没测的有同一链并发续跑（已有 `.resumed` 原子占位保护）、写模式并发。
5. **`--timeout` 放开后的清理是否可靠**：**不能认为可靠**。
   - 正常跑完（656 s）没问题，答复文件正确、无残留。
   - Codex 的 shell 命令跑在独立进程组，`run_codex.py` 的组清理覆盖不到；期限越长，单条长命令（测试、构建）恰好在中止时运行的概率越大。若要 delegate 保证不留孤儿，需要另找办法（例如按会话／父子关系找出 Codex 的后代进程组一并清理），这是 1.3 新增的实现工作，不只是放开数字。
   - 真实 Codex 执行命令时收到 SIGTERM，`run_codex.py` 一次挂住 ≥60 s，根因未定位。现有 540 秒路径同样经过这段代码，所以这不是 `--timeout` 独有的问题，但长运行更容易碰到「停在命令中途」。建议 Spec 前先免费复现定位（例如构造一个会返回工具调用的本机假端点），再决定是否需要付费复测。

## 调用次数与配置

- 付费 Codex 调用 **18 次**（上限 25）：T1 2 次（T1a、T1b）、T3 1 次、T4 2 次、T2 11 次（T2r00～T2r10）、T5 2 次（T5a、T5b）。没有重试、没有加跑。另有 1 次真实 Codex 指向本机假端点的免费调用（没有访问模型、未带凭据）。
- 额度：会话文件里 `rate_limits.primary.used_percent` 在实测期间小幅上升，`rate_limit_reached_type` 始终为 `null`（具体值属账号信息，不记录）。
- `~/.codex/config.toml` sha256：测前 `84bbafa44e5745c37c741b02a1b84aa85f7fa81ac974a0dbb240345baf285538`，测后 `84bbafa44e5745c37c741b02a1b84aa85f7fa81ac974a0dbb240345baf285538`，**一致**。临时仓库、三个 worktree、输出目录和 T4 在 `$TMPDIR/delegate/` 留下的 6 个文件已删除；测后无残留 `sleep`／codex 进程。

## 仍未验证

- T5b 挂住的根因；SIGINT、SIGHUP 停止；写模式下长运行中止。
- 「Codex 收到 SIGTERM 会不会主动回收它在独立进程组里起的命令」：T5b 里命令恰好自然结束，没有观测到。
- 压缩只测了 1 次、只读、推理档 `low`、模型 `gpt-6.1-sol`；压缩阈值是否固定在约 94%、压缩本身耗时（第 8 轮比相邻轮多约 15～20 s）没有多样本。
- 压缩后工具输出原文的保留情况（本测试的记忆核对被前几轮答复污染，见 T2）。
- `rate_limits` 在接近限额或触发限流时的字段取值（本次 `rate_limit_reached_type` 一直是 `null`）。
- `--json` 与 delegate 现有文本日志并存的做法（stdout 已被 JSONL 占用，hook 行只在文本日志里有）。
- 同一链并发续跑、写模式并发、50 组清理在并发下的行为。
- Codex 自己的会话文件（本次所有非 ephemeral 调用都写了）按约定只读，未删除。

## 附录：辅助脚本

T2 循环（每轮 `resume` 同一会话，`n` 从 1 到 14；第 10 轮后若已见压缩即停）：每轮提示词为「第 n 轮：分别单独运行 `cat big/big{3n+2,3n+3,3n+4}.txt` …把 `max_output_tokens` 设为 20000…最终答复两行：本轮 3 个 SECRET；凭记忆列出至今全部 SECRET」，加上 delegate 续跑提示的结尾；调用 `PROBE_EFFORT=low python3 -B 2026-10-27-delegate-s38-probe.py.txt t2rNN <out> none 500 <prompt> <会话ID>`。压缩判定只看会话文件每行的 `type` 或 `payload.type` 是否含 `compact`（基础指令文本里本来就有 compact 字样，不能用全文 grep）。

T5 包装：`t5.sh <name> <sleep秒> <快照秒> [SIGTERM秒]`，生成 12 步 `sleep N && cat stepNN.txt` 的只读提示词，后台调 `python3 -B 2026-10-27-delegate-s38-probe.py.txt <name> <out> runcodex 700 <prompt>`（T5b 另设 `PROBE_TERM_AT=150`），到点用 `ps -axo pid,ppid,pgid,sess,etime,command` 抓进程树，结束 3 s 后再查 `sleep N` 与带答复路径的 codex 进程。

## T5b 根因排查（免费）

同日，负责人会话验收上文后转来用户原话：「同时让子会话不花钱地复现 T5b 挂住的根因」。本节**没有调用真实模型**，没有付费调用；`~/.codex/config.toml` 测前测后 sha256 都是 `84bbafa4…5538`。临时目录 `~/delegate-s38-rootcause-20261027141314` 测后已删除。

### 怎么复现

- 假模型端点：[2026-10-27-delegate-s38-fake-responses.py.txt](2026-10-27-delegate-s38-fake-responses.py.txt)，本机 `127.0.0.1` 上的极简 Responses SSE 服务，不验证也不接收凭据。每次请求都回一个工具调用，让真实 Codex 一直在执行 `sleep N && echo slept`：
  - `call:` 回普通 `function_call` → `exec_command`（假模型名 `fake-model` 时 Codex 给的工具表）；
  - `js:` 回 `custom_tool_call` → `exec`，内容 `text(await tools.exec_command({cmd:…,yield_time_ms:30000}))`。这是 T2／T5 里真实模型实际用的 code-mode 调用；用 `-m gpt-6.1-sol` 指向假端点时，Codex 给的就是这一套工具。
- 真实 Codex 0.162.1 经 `-c model_providers.fk={…base_url="http://127.0.0.1:<port>/v1"…} -c model_provider="fk"` 连假端点，其余参数同 delegate（只读沙箱、`approval_policy="never"`、`--json`、`-o`、`stdin=/dev/null`），可选 `--ephemeral`。
- 复现脚本：[2026-10-27-delegate-s38-term-repro.sh.txt](2026-10-27-delegate-s38-term-repro.sh.txt)。用产品 `run_codex.py 700`，或它的打点副本（临时目录里，不改源码）。打点副本只加了 `faulthandler.register(SIGUSR1)`，并在 `Interrupted`、`stop_group` 进入、TERM 后 2 秒内是否退出、发 SIGKILL、最终 `wait()` 返回这几处写时间戳到 stderr。脚本等 `sleep N` 进程出现后再过若干秒给 `run_codex.py` 发信号，然后打印信号前的进程树、信号后 3 秒仍存活的进程、打点；40 秒内不退出就 `kill -USR1` 抓 Python 栈并对 codex 用 `sample` 抓原生栈。

### 结果（共 20 次）

| 组 | 次数 | 条件 | `run_codex.py` | 残留 |
|---|---|---|---|---|
| 启动期 | 1 | TERM 落在 Codex 启动阶段（插件同步的 `git clone`、登录 shell 快照，尚未请求模型） | 1.2 s 退出 143 | — |
| 长命令 + TERM | 2 | `exec_command`，`sleep 45` 运行中，打点副本 | 1.1、1.3 s 退出 143 | **`zsh -lc` 与 `sleep 45` 都残留** |
| 长命令 + INT | 1 | 同上 | 1.1 s 退出 130 | 同上 |
| 长命令 + HUP | 1 | 同上 | 1.3 s 退出 129 | 同上 |
| 短命令随机时刻 | 6 | 非 ephemeral、产品原版、`sleep 3`，信号落在命令中或命令间 | 1.1～2.0 s 退出 143 | 无（命令已自然结束） |
| code-mode 长命令 | 1 | `exec` 自定义工具、`sleep 45` | 1.1 s 退出 143 | `zsh -lc` 与 `sleep 45` 残留 |
| code-mode 短命令加压 | 8 | 非 ephemeral、产品原版、`sleep 1`，0～4 s 随机打断 | 1.0～1.1 s 退出 143 | 无 |

打点（长命令 + TERM，有代表性）：

```text
[probe …44.145] Interrupted signum=15
[probe …44.193] stop_group enter pid=59967
[probe …44.811] after TERM: exited          ← Codex 收到 TERM 后 0.6 s 自己退出（退出码 0）
[probe …44.818] SIGKILL sent; final wait
[probe …44.818] final wait returned rc=0
```

信号后 3 秒仍存活：

```text
  PID  PPID  PGID STAT command
60866     1 60866 Ss   /bin/zsh -lc sleep 45 && echo slept   ← 过继给 launchd
60876 60866 60866 S    sleep 45
```

### 结论

1. **T5b 的「60 秒不退出」在免费条件下没有复现**。20 次都在 2 秒内正常退出：涵盖 TERM／INT／HUP、`exec_command` 与 code-mode `exec` 两种工具、ephemeral 与否、产品原版与打点副本、打断落在启动期／长命令中／短命令之间。与 T5b 仍有的差别是真实 OpenAI provider（ChatGPT 登录、可能走不同的传输）和真实模型的推理流；这部分不带凭据就测不了，按授权不再测。
2. **能排除的**：
   - 不是 Codex 收到 TERM 后等在途命令。Codex 0.1～0.8 s 内就退出，不等命令结束（退出码 0，与 S35 相同）。
   - 不是 `stop_group` 前两步的问题：TERM 送达、2 秒等待、SIGKILL 都按预期走完。
   - 不是「进程组含僵尸时 killpg 报 EPERM」（上文已排除）。
   - Codex 起的 MCP 服务（agent-relay、spec-guard 账本、node_repl 等，各自在独立进程组）随 Codex 退出自行结束，没有残留。
3. **最接近的结论**：`run_codex.py` 里所有等待都有上限，唯独 `stop_group` 最后那个 `process.wait()` 没有超时。信号处理在 Python 主线程上一定会跑（`time.sleep` 被信号打断时先执行处理函数），所以 T5b 那次最可能卡在 SIGKILL 之后的这个 `wait()`。也就是直接子进程（`env`→`node` 包装）在 SIGKILL 后没有被回收：可能信号没送到，也可能进程处在不可中断等待（复现 1 的进程树里，原生 codex 与命令 shell 的 STAT 都出现过 `U`）。这一点**没有直接证据**，因为 T5b 当时用的是不打点的产品原版，也没有抓栈。
4. **已确认的清理缺陷（与挂住无关，但更要紧）**：无论 TERM、INT、HUP，Codex 都**不回收**正在执行的命令。命令的 `zsh -lc` 用 `setsid` 起在新会话、新进程组（STAT `Ss`），Codex 退出后它和子进程被过继给 launchd 继续跑完。`run_codex.py` 的 `killpg(Codex 组)` 打不到它们。现有 540 秒路径同样有这个缺陷；`--timeout` 放开后，长测试、长构建在中止时正在运行的概率更大，写模式下孤儿命令还可能在 delegate 报告结束后继续改工作区。

### 对 1.3 `--timeout`／清理设计的影响

- **需要按后代进程组清理**。命令既换了进程组也换了会话，按 pgid、sid 都圈不住。Codex 一退出，ppid 链就断了（变成 1），所以必须在 Codex 还活着时取快照。建议 `stop_group` 改成：
  1. `killpg(Codex 组, SIGSTOP)` 冻结 Codex，防止快照期间再起新命令；
  2. 沿 ppid 链列出 Codex 的全部后代，收集它们的 pgid（排除 Codex 自己的组）；
  3. 对每个后代组 `killpg` TERM → 短等待 → KILL；
  4. 对 Codex 组 KILL（再补一个 `SIGCONT`，防止停止状态的进程收不到后续信号）。
  
  macOS 上列后代可用 `ps -axo pid,ppid,pgid` 或 `sysctl`。代价是放弃 Codex 自己的优雅退出：当前的优雅退出也只是 Codex 自己 0.1～0.8 s 退出，并不回收命令，所以没有损失。也可以保留先 TERM 的做法，但快照必须在 TERM 之前做。
- **最后的 `process.wait()` 要有上限**（例如 5～10 s），超时后报告「执行进程未能回收，PID=…」并按失败返回，不能无限期挂住宿主；`codex-exec.sh` 的 `finish` 里 `wait "${RUNNER_PID}"` 同理。
- **结果文件**应记录清理结果：信号前后的后代清单、是否有残留、残留 PID。这样 1.3 的 `--strict`／结果文件能如实反映「中止后工作区可能仍在被改」。
- 这三条都可以用本节的假端点做成免费的确定性回归测试（长 `sleep` 中途打断 → 断言无残留、`run_codex.py` 在上限内退出），不依赖付费调用。

### 仍未验证

- T5b 挂住的真正根因：真实 OpenAI provider 的传输、真实模型推理流下的退出行为，以及挂住时 `run_codex.py` 和 `node` 的栈。下一次付费长运行建议直接用打点副本并在超时时抓栈，以便一次定位。
- 写模式（`workspace-write` 沙箱）下的残留命令行为。
- 建议的「SIGSTOP + 后代快照」方案还没实现、没测，例如快照与新进程创建的竞态、`sandbox-exec` 包装下的父子关系。
- `codex-exec.sh` 的 `finish` 在宿主再次发信号时的行为。

### 后续：0.7.1 修复后的状态（2026-10-27 补记）

本节结论交给 delegate 0.7.1 处理。0.7.1 已合入 main 并发版（`64d7ece`，标签 `v0.7.1`，见 channel 规格修订 S41），此后：

- **孤儿命令：已修。** 中止（到期或 TERM/INT/HUP）时，`run_codex.py` 先冻结 Codex，再沿 ppid 链快照后代，按进程组回收，换了会话、换了进程组的命令也在回收范围内。清理结果写进 `<runId>.cleanup` 并转发到 stderr。回归测试是 `plugins/delegate/tests/test-reap-fake-endpoint.py`：真实 Codex 连本机假端点。
- **不会再无限挂住：** 最后的 `wait()` 已加上限（5 秒）。回收不了时报告 `delegate: 执行进程未能回收，PID=<pid>` 并退出 125。`codex-exec.sh` 被中断时最多等 15+2 秒，并如实报告。
- **「60 秒不退出」的真实根因仍未定位。** 上文结论 3 的推断（卡在没有上限的最后一个 `wait()`）仍是推断。现在即使再遇到同样情形，也会在上限内退出 125 并报告 PID，但为什么直接子进程在 SIGKILL 后回收不了，没有直接证据。下一次付费长运行时若出现 125，应保留 `.cleanup` 与当时的进程状态。

本节上面的文字保持当时的原貌，不按 0.7.1 改写。

