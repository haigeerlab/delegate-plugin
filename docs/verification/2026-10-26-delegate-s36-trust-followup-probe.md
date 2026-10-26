# S36 补测：内联表覆盖的合并方式与 worktree 的信任键

2026-10-26。接 S35 子会话的调研（分支 `claude/lucid-yalow-625ffc` 里尚未提交的 `docs/verification/2026-10-26-delegate-s36-trust-probe.md`），补测其中两项没验证的问题。本轮没有付费调用。

## 做法

与原调研相同：codex-cli 0.162.1；每个用例新建隔离的 `CODEX_HOME`，`config.toml` 只有 `model = "gpt-6.1-sol"` 加用例需要的 `projects` 条目，不放登录凭据，环境变量里去掉 `OPENAI*`／`CODEX*`。命令为
`codex exec -c approval_policy="never" --ephemeral --sandbox workspace-write --color never [覆盖] -- hi`，stdin 接 `/dev/null`。
信任写入发生在启动线程时、请求模型之前；之后每个用例都因无凭据被 `401` 拒掉（全部 13 个用例退出码 1，输出含 401）。
判断依据是运行后隔离 `config.toml` 是否多出 `[projects."…"]` 段：Codex 只在合并配置里查不到该项目的 `trust_level` 时才写入，所以「没写入」表示当时生效的配置里已有这个项目的信任级别。

脚本见 [同名 .py.txt](2026-10-26-delegate-s36-trust-followup-probe.py.txt)。仓库都建在会话 scratchpad 下：`repoA`、`repoB`、主仓库 `main` 及其 worktree `main-wt`（`git worktree add`），`main-wt/sub` 是子目录。
真实 `~/.codex/config.toml` 未参与，sha256 测前测后都是 `c84d6a4b…3c8b`。

## ① `-c 'projects={…}'` 是整表替换还是按键合并

| 编号 | 隔离配置里的条目 | 覆盖 | 启动目录 | 写入 |
|---|---|---|---|---|
| R0 | `repoB = untrusted` | 无 | repoB | 否（对照：已有条目就不写） |
| R1 | 无 | 无 | repoB | 是，键 repoB（对照） |
| R2 | `repoB = untrusted` | `projects={"repoA"={trust_level="trusted"}}` | repoB | **否** |
| R3 | `repoB = untrusted` | 同 R2 | repoA | 否 |

R2 是关键：覆盖里只有 repoA。若整表替换，repoB 的条目会被丢掉，Codex 会像 R1 一样写入 repoB；实际没写，说明 repoB 的 `untrusted` 仍在合并后的配置里。

**结论：按键合并，不是整表替换。** 覆盖只加（或改）给出的那个键，用户已有的其他 `projects` 条目照常生效，修复时不需要把它们带上。
（同一个键上 `-c` 与用户配置谁优先没有测：两者都让该项目有信任级别，从写入与否看不出来。按 Codex 配置分层，`-c` 在用户配置之上；这正是「用户标了 `untrusted` 就绝不覆盖」要防的情形。）

## ② git worktree 里用哪条路径作键

| 编号 | 隔离配置里的条目 | 覆盖键 | 启动目录 | 写入 |
|---|---|---|---|---|
| W3 | 无 | 无 | main | 是，键 **main** |
| W0 | 无 | 无 | main-wt | 是，键 **main**（不是 main-wt） |
| W6 | 无 | 无 | main-wt/sub | 是，键 **main** |
| W1 | 无 | main-wt | main-wt | 否 |
| W2 | 无 | main | main-wt | 否 |
| W4 | 无 | main-wt | main-wt/sub | **是，键 main** |
| W5 | 无 | main | main-wt/sub | 否 |
| W7 | `main-wt = untrusted` | 无 | main-wt | 否 |
| W8 | `main = untrusted` | 无 | main-wt | 否 |

在 `main-wt` 里 `git rev-parse --show-toplevel` 返回 `main-wt`，`--git-common-dir` 是 `main/.git`。

**结论：**

- **写入用的键是主仓库路径**（Git 公共目录 `.git` 的上一级），不是 worktree 路径，也不是 `git rev-parse --show-toplevel`。从 worktree 运行 `--write` 会给主仓库加信任记录。
- 查找时先看启动目录本身的键，再看主仓库路径的键（与原调研读到的源码一致）。所以 worktree 路径作键只在恰好从 worktree 根目录启动时有效（W1），从子目录启动就失效并照样写入（W4）；**主仓库路径作键在根目录和子目录都有效**（W2、W5）。
- 用户配置里不论是 worktree 路径还是主仓库路径的条目，从 worktree 根目录启动时都算「已有条目」（W7、W8）。

## 对修复的含义

1. 覆盖不用带上用户已有的其他条目；只加当前仓库一个键。
2. 覆盖键要用 Codex 的信任根：主仓库路径 = `git rev-parse --path-format=absolute --git-common-dir` 的上一级（普通仓库里与 `--show-toplevel` 相同）。wrapper 现有的 `REPO_ROOT`（`--show-toplevel`）在 worktree 子目录里会失效。
3. 判断「用户配置里有没有这个仓库的条目」要按 Codex 的查找顺序：先启动目录的键，再信任根的键；任一个有 `trust_level` 就不加覆盖（包括 `untrusted`）。

## 仍未验证

- 同一个键上 `-c` 覆盖与用户配置的优先级（见 ①），以及项目级 `.codex/config.toml` 里的 `projects` 条目。
- 路径规范化：符号链接、大小写不敏感文件系统（本次路径都在 `/private/tmp` 下，已是真实路径）；Windows／WSL；bare 仓库与 `--separate-git-dir` 之类的非常规布局。
- 嵌套 Git 仓库、子模块。
