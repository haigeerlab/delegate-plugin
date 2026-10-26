# S36 调研：`--write` 运行能否不写入项目信任

2026-10-26。起因：S35 补测发现 delegate 的 `--write` 运行会让 Codex 往 `~/.codex/config.toml` 追加 `[projects."<路径>"] trust_level = "trusted"`（见 [S35 实测记录](2026-10-26-delegate-s35-timeout-probe.md)）。负责人 delegate-owner 要求调研能否不写入，不改代码、默认不花钱。本轮没有付费调用。

## 官方源码（openai/codex，标签 `rust-v0.162.1`，提交 `7a078f6b`）

- 唯一的写入点在 `codex-rs/app-server/src/request_processors/thread_processor.rs` 的 `thread_start_task`（约 1351–1411 行），调用 `codex_core::config::set_project_trust_level(codex_home, trust_target, Trusted)`。四个条件同时满足才写：
  1. 请求带了 cwd——`codex exec` 启动线程时总是传 `cwd: Some(config.cwd)`（`codex-rs/exec/src/lib.rs` 约 1452 行）；
  2. `config.active_project.trust_level.is_none()`，即合并后的配置里这个项目还没有信任级别；
  3. `!config.config_layer_stack.is_projectless()`；
  4. 生效权限允许写 cwd（`workspace-write` 或更宽；`read-only` 不满足）。
- 写入的键是 `resolve_root_git_project_for_trust(cwd)`，即 Git 根目录，不是 cwd。
- 写盘失败时只记警告，改用内存里的信任继续。也就是说，信任本身在运行时总会生效，持久化只是副作用。
- `active_project` 从**合并后的** `projects` 表里查（`codex-rs/config/src/project_trust.rs`），查找顺序是 cwd 键优先、Git 根目录键次之；`-c` 覆盖也是合并的一层。
- 只有启动新线程会写；`exec resume` 走的是续跑线程，源码里没有这条写入。

## 免费实测

做法：在隔离的 `CODEX_HOME`（scratchpad 里的临时目录，`config.toml` 只有一行 `model = "gpt-6.1-sol"`，不放登录凭据）下运行 `codex exec -c approval_policy="never" … -- "hi"`。写入发生在启动线程时、请求模型之前；之后请求因为没有凭据被 `401 Unauthorized` 拒掉，不产生费用。仓库是家目录下新建的空 Git 仓库 `~/delegate-s36-probe-20261026203551`。真实 `~/.codex/config.toml` 全程未参与，sha256 测前测后都是 `c84d6a4b…3c8b`。

| 编号 | 参数 | 写入信任 |
|---|---|---|
| T0 | `--sandbox read-only` | 否 |
| T1 | `--sandbox workspace-write` | **是**（键为仓库根目录） |
| T1s | 同 T1，从子目录 `sub/` 启动 | **是**（键仍是仓库根目录） |
| T2 | `workspace-write` + `-c 'projects."<根目录>".trust_level="trusted"'`（点号路径写法） | **是**——此写法没被识别 |
| T2c | 同 T2，值为 `"untrusted"` | **是**——同上，证明点号写法根本没生效 |
| T2b | `workspace-write` + `-c 'projects={"<根目录>"={trust_level="trusted"}}'`（内联表写法） | **否** |
| T2d | 同 T2b，值为 `"untrusted"` | 否 |
| T2e | 同 T2b，从子目录 `sub/` 启动 | **否** |
| T3 | `workspace-write` + `--ignore-user-config` | **是**——不读用户配置，但照样往 `CODEX_HOME` 写 |

## 结论

- **能做到不写入。** `--write` 运行加一个内联表覆盖 `-c 'projects={"<Git 根目录>"={trust_level="trusted"}}'` 就不会持久化。运行时的信任与今天相同（今天也是先信任再写盘），只是不落盘。
- 点号路径写法 `projects."<路径>".trust_level=…` 无效，不能用。
- `--ignore-user-config` 无效（照样写入），还会丢掉用户的全部配置（模型、MCP、hook 等），不采用。
- 只读运行、续跑（`exec resume`）本来就不写。

## 风险与待定

- 用户如果在自己的配置里把这个仓库明确标成 `untrusted`，今天 Codex 不会改它，也不会信任它。无条件加 `trusted` 覆盖会把它抬成受信任，从而加载仓库里的项目级配置和 hook，这是放宽。稳妥做法是只在用户配置里没有该仓库条目时才加覆盖；要做到这一点，delegate 得读取用户的 `config.toml`。标准库 `tomllib` 要 Python 3.11+，本机是 3.10.7，读取方式要另行设计。
- 内联表覆盖 `projects=` 是替换整个 `projects` 表还是逐键合并，没有验证；对本次运行只有当前仓库的条目有意义，影响应该不大，但未证实。
- 没验证：Git worktree 里写入的键是 worktree 路径还是主仓库路径（源码用 `resolve_root_git_project_for_trust`，可能解析到主仓库）；Windows、WSL 的路径写法。
- 信任已经写进用户配置的旧条目（例如 S35 实测之前的 delegate 运行留下的），本方案不清理。
