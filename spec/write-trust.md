# 规格：write-trust（写模式不落盘项目信任）

<!-- spec-guard: review approved 6e8ad64dfdd8 -->

简体中文 | [English](../docs/en/SPEC-write-trust.md)

2026-10-26 起草。起因：S35 实测发现 `/delegate:run --write` 第一次在某个仓库运行时，Codex 会往用户的 `~/.codex/config.toml` 追加 `[projects."<路径>"] trust_level = "trusted"`，与插件「不修改全局配置」的说法冲突。用户经生态总负责人 ecosystem-lead 转述的方向（原话）：「S36 修行为：只在用户配置里没有这个仓库的信任条目时，才用 -c 内联表临时覆盖，不再写入 ~/.codex/config.toml；补测那两项没验证的；在修好之前，先在 README 里照实写明现在的行为。」补测与 README 两步已在本会话经用户认可、批准。

依据：
- S35 子会话调研（openai/codex `rust-v0.162.1` 源码 + 免费实测，分支 `claude/lucid-yalow-625ffc` 中未提交的 `docs/verification/2026-10-26-delegate-s36-trust-probe.md`）：写入只发生在启动新线程、合并配置里该项目没有 `trust_level`、生效权限可写 cwd 时；`-c 'projects={"<根>"={trust_level="trusted"}}'` 内联表能阻止写入，点号写法和 `--ignore-user-config` 不行。
- 本会话补测 [2026-10-26-delegate-s36-trust-followup-probe.md](../docs/verification/2026-10-26-delegate-s36-trust-followup-probe.md)：内联表覆盖**按键合并**，不替换用户其他条目；worktree 里 Codex 的信任键是**主仓库路径**，从 worktree 子目录启动时只有主仓库路径作键的覆盖有效。

## 前提（待用户确认 A1–A9）

- **A1** 新模块 `write-trust`，依赖 channel 与 run-resume（改的是两者共用的 `codex-exec.sh` 写模式参数）。两者原有条款不改，各加一句指向本模块。
- **A2** 只作用于让 Codex 以 `workspace-write` 执行的调用：`--write` 普通 run、`--write --resumable`、`--resume … --write`。只读 run、只读续跑、Codex 后端 review 一个参数都不加（它们本来就不写信任）。
- **A3** 续跑（`exec resume`）按源码本身不写信任，但写模式续跑仍加同样的覆盖：今天首次运行已把信任落盘，续跑读到的是「受信任」；不落盘之后，续跑若不加覆盖，信任会从「受信任」变成「未设置」，行为与今天不一致。
- **A4** 判断「用户配置里有没有这个仓库的条目」只读一个文件：`${CODEX_HOME:-$HOME/.codex}/config.toml`。文件不存在算「没有条目」。不读系统级、托管配置和仓库内项目级 `.codex/config.toml`（见开放问题）。
- **A5** 不引入 TOML 解析器（本机 Python 3.10 没有 `tomllib`，插件不装依赖）。改用保守的文本判定：候选键中任何一个**带引号整串**（`"<键>"` 或 `'<键>'`）出现在文件里，就当作已有条目、不加覆盖。TOML 里含 `/` 的键必须加引号，所以真实条目一定会被看到；误判只会偏向「不覆盖」，也就是退回今天的行为（Codex 可能写入），不会放宽信任。
- **A6** 候选键与 Codex 的查找顺序对齐：启动目录（物理路径，以及与之同一目录的 `$PWD` 逻辑路径），加上信任根。信任根 = `git rev-parse --path-format=absolute --git-common-dir` 的上一级，前提是该目录名为 `.git`；否则（子模块、`--separate-git-dir`、bare 等）视为「读不准」。覆盖用的键就是这个信任根。
- **A7** 「读不准」时不加覆盖、照常运行，stderr 提示一行，退出码不变。读不准包括：配置文件存在但读不了或不是 UTF-8；任一候选键含 `"`、`\` 或控制字符；取不到信任根。
- **A8** 已经写进用户配置的旧信任条目不清理，也不提示；接口版本、`interface.json`、退出码都不变。
- **A9** 验证分三层：桩测试（参数与判定）；免费真机核验（真实 Codex、隔离 `CODEX_HOME`、无凭据被 401 拒，确认生成的覆盖确实阻止写入）；一次付费真实 `--write` 运行，确认真实 `~/.codex/config.toml` 的 sha256 不变（gate，单独授权）。

## 技术栈与命令

Bash 3.2 wrapper、Python 3 标准库、Git ≥2.31（`--path-format`）、Codex CLI 0.162.1（本机实测版本）。不新增依赖、hook 或命令入口。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
python3 -B plugins/delegate/tests/test-write-trust.py
python3 -B plugins/delegate/tests/test-run-resume.py
/bin/bash plugins/delegate/tests/test-channel.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/codex_trust.py      → 新增：候选键、信任根、文本判定，输出 -c 参数值或提示（标准库）
plugins/delegate/scripts/codex-exec.sh       → 写模式 run 与写模式续跑在 APPROVAL 之后加覆盖参数
plugins/delegate/tests/test-write-trust.py   → 新增：单元测试 + 桩集成测试
plugins/delegate/README.md / README.en.md    → 第 26 行改回「不写全局配置」并说明例外（读不准时）
README.md / README.en.md                     → 改写 S36 第 2 步加的那段：从「现在会写」改为新行为
spec/write-trust.md / docs/en/SPEC-write-trust.md → 本合同
spec/channel.md、spec/run-resume.md 及英文对应页 → 各加一句指向本模块
spec/CAPABILITY-MAP.md / docs/en/capability-map.md → 新行（英文页同步）
docs/releases/unreleased.md 及英文对应页     → 待发行说明
docs/verification/2026-10-26-delegate-s36-*  → 免费真机核验与付费实测记录
```

## 行为合同

### 何时加覆盖

写模式调用在启动 Codex 前运行 `codex_trust.py`：

| 情形 | 结果 |
|---|---|
| 配置文件不存在 | 加覆盖 |
| 配置文件里找不到任何候选键的带引号整串 | 加覆盖 |
| 找到了（不论值是 `trusted`、`untrusted` 还是别处出现的同一路径） | 不加，不提示 |
| 读不准（A7） | 不加，stderr 提示 |

加的参数（键为信任根，放在 `-c approval_policy="never"` 之后）：

```text
-c projects={"<信任根>"={trust_level="trusted"}}
```

信任根已排除 `"`、`\` 和控制字符，直接加双引号即为合法 TOML 键。

### 提示文案（stderr，一行）

```text
delegate: 未能确认 Codex 用户配置里有没有本仓库的信任条目（<原因>），本次不加临时信任；Codex 可能会往 <配置文件路径> 写入一条信任记录。
```

`<原因>` 取其一：`配置文件无法读取`、`配置文件不是 UTF-8`、`仓库路径含引号、反斜杠或控制字符`、`无法确定 Git 信任根`。

### 不变的部分

- 运行时的信任与今天一致：今天第一次 `--write` 也是先在内存里信任再落盘；之后的运行读到落盘的 `trusted`。现在改成每次临时给，不落盘。
- 用户已有条目（含 `untrusted`）时，参数与今天逐项相同。
- 只读 run、只读续跑、Codex review 的参数与今天逐项相同。
- `codex_trust.py` 只读配置文件，不写、不改权限、不建目录。

## 代码风格

沿用现有写法：Bash 兼容 3.2、变量写 `${VAR}`、空数组用已有守卫展开；Python 标准库、4 空格缩进、snake_case，纯函数与命令行入口分开（同 `run_state.py`）。现有示例（`codex-exec.sh`）：

```bash
# Never let a configured approver let a delegated run leave its sandbox.
APPROVAL=(-c 'approval_policy="never"')
```

## 测试策略

`test-write-trust.py`（`unittest`，临时 Git 夹具，`CODEX_HOME` 指向临时目录，PATH 指向现有 `stub-codex` 记录 argv）。先写测试并确认它红，再实现。

- 单元：无配置文件；配置里有 `trusted`／`untrusted` 条目（表头、点号、内联表三种写法）；只有单引号键；相近路径（`<根>-sub`、`<根>/sub`）不算命中；路径含 `"`；非 UTF-8；不可读；信任根目录名不是 `.git`。
- 集成：普通仓库根目录与子目录、worktree 根目录与子目录的 `--write` run，覆盖键都是主仓库路径；`--write --resumable` 与 `--resume … --write` 带覆盖；只读 run、只读续跑不带；读不准时有提示、退出码不变、不带覆盖；运行前后配置文件字节不变。
- 现有 `test-channel.sh`、`test-run-resume.py`、`test-review-backends.py` 的断言不改。

**免费真机核验（report）：** 用 `codex_trust.py` 生成的参数，在隔离 `CODEX_HOME`、无凭据下跑真实 `codex exec --sandbox workspace-write`（被 401 拒），覆盖普通仓库根目录与子目录、worktree 子目录、已有 `untrusted` 条目四种，确认都不写入；真实 `~/.codex/config.toml` 测前测后 sha256 一致。

**付费实测（gate，单独授权）：** 在家目录下新建一个从未用过 Codex 的临时 Git 仓库，用当前源码跑一次真实 `--write`（最小任务：写一个文件），确认文件写出、真实 `~/.codex/config.toml` sha256 不变。

## 开发边界

- **Always：** 只读配置；读不准时退回今天的行为并提示；用户已有条目一律不覆盖；中英文合同同步。
- **Ask first：** 清理或改写用户已有的信任条目；读取系统级或托管配置；引入 TOML 解析依赖；改动只读路径的参数；付费实测、提交、推送、发版。
- **Never：** 写 `~/.codex/config.toml` 或 `CODEX_HOME` 下任何文件；把用户标成 `untrusted` 的仓库抬成 `trusted`；用 `--ignore-user-config` 或点号写法；改接口版本或 `interface.json`。

## 成功条件与验证映射

- **WT-01：** 写模式 run 在无条目时带覆盖，键为信任根（普通仓库、worktree，根目录与子目录）（桩测试）。
- **WT-02：** 有任一候选键的带引号条目时不带覆盖，参数与改动前相同（桩测试）。
- **WT-03：** 读不准的四种原因各自提示一行、不带覆盖、退出码不变（桩测试）。
- **WT-04：** 写模式可续跑 run 与写模式续跑带覆盖；只读 run、只读续跑、Codex review 参数不变（桩测试）。
- **WT-05：** 运行前后配置文件字节不变（桩测试）。
- **WT-06：** 免费真机核验四种情形都不写入，真实配置 sha256 不变（report）。
- **WT-07：** 付费实测真实配置 sha256 不变（gate；未授权就标「未验证」）。
- **WT-08：** 中英文 README、合同、指向句和待发行说明同步，README 不再写「`--write` 现在会改动 Codex 的用户配置」。
- **WT-09：** 总验证、两项 plugin validate、`git diff --check` 通过；现有测试断言不改。

## 开放问题

- 同一个键上 `-c` 与用户配置谁优先未实测；本模块不在用户已有条目的键上加覆盖，所以不依赖它。
- Codex 的系统级（如 `/etc/codex/config.toml`）、托管配置和项目级配置里若有 `projects` 条目，本模块看不到，可能把那里标成 `untrusted` 的仓库临时抬成 `trusted`。是否要扫这些文件，待定（扫了只会更保守）。
- 符号链接路径：候选键已含物理路径与 `$PWD` 逻辑路径，但 Codex 自己是否规范化未实测。
- 是否要在 `/delegate:doctor` 里列出用户配置里已有的、可能由旧版 delegate 留下的信任条目，不在本模块。
- 与 S35（run-timeout）同改 `codex-exec.sh`、README 和能力图同一处；进入实现前由负责人 delegate-owner 协调先后。
