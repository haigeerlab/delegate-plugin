# S36 免费真机核验：write-trust 生成的覆盖能阻止写入

2026-10-26，write-trust 模块 Checkpoint 2（WT-06）。本轮没有付费调用。

## 做法

codex-cli 0.162.1。每个用例新建隔离的 `CODEX_HOME`，`config.toml` 只有 `model = "gpt-6.1-sol"` 加用例需要的条目，不放登录凭据，环境变量去掉 `OPENAI*`／`CODEX*`。
先在启动目录运行 `plugins/delegate/scripts/codex_trust.py`（与 `codex-exec.sh` 写模式的调用方式相同），把它输出的值作为 `-c` 传给真实
`codex exec -c approval_policy="never" [-c <覆盖>] --ephemeral --sandbox workspace-write --color never -- hi`，stdin 接 `/dev/null`。
信任写入发生在请求模型之前；之后请求因无凭据被 `401` 拒掉。仓库 `main` 及其 worktree `main-wt` 建在会话 scratchpad 下。脚本见 [同名 .py.txt](2026-10-26-delegate-s36-write-trust-check.py.txt)。

真实 `~/.codex/config.toml` 未参与，sha256 测前测后都是 `c84d6a4b…3c8b`。

## 结果

| 用例 | 启动目录 | `codex_trust.py` 给出的覆盖 | 退出 | 401 | 写入 |
|---|---|---|---|---|---|
| C0 对照（不调用 `codex_trust.py`） | main | 无 | 1 | 是 | **是**，`[projects."main"]` |
| C1 普通仓库根目录 | main | `projects={"main"={trust_level="trusted"}}` | 1 | 是 | 否 |
| C2 普通仓库子目录 | main/sub | 同上 | 1 | 是 | 否 |
| C3 worktree 子目录 | main-wt/sub | 同上（键为主仓库路径） | 1 | 是 | 否 |
| C4 已有 `main = untrusted` | main-wt/sub | 无（已有条目，不覆盖） | 1 | 是 | 否 |

表中路径省略了 scratchpad 前缀，实际都是绝对路径。

第一次运行时 C0 超过 120 秒没有退出，脚本因超时中断（之后的用例没跑）；改为超时 60 秒即终止并照样检查配置后重跑，五个用例都在超时前以 401 结束，结果如上。超时原因没查，推测是当时的网络重试；它不影响结论，因为写入发生在请求模型之前。

## 结论

- 对照组仍会写入，说明这个环境能复现原问题。
- `codex_trust.py` 生成的覆盖在普通仓库根目录、子目录和 worktree 子目录都阻止了写入。
- 用户配置里已有 `untrusted` 条目时不给覆盖，Codex 也不写入，信任保持 `untrusted`。

## 未覆盖

- 读不准的四种情形由桩测试覆盖，不需要真实 Codex（它们不加参数，与改动前相同）。
- 真实登录状态下的完整 `--write` 运行由 Checkpoint 3 付费实测验证（单独授权）。
