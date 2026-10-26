# 实施计划：write-trust

<!-- spec-guard: review approved -->

日期：2026-10-26。规格：[spec/write-trust.md](../../spec/write-trust.md)（用户 2026-10-26 批准，指纹 86f0e0150a17）。任务：[todo.md](todo.md)。
本计划覆盖免费的本地实现与验证，外加一次需单独授权的付费实测（Checkpoint 3）。提交、推送、PR、版本号与发版另行授权；动 `codex-exec.sh` 前先告知负责人 delegate-owner，由其与 S35（run-timeout）协调先后。

## 架构决定

- 判定逻辑全部放进新增的 `codex_trust.py`（标准库）：纯函数 `candidate_keys`、`trust_root`、`decide(config_text, keys)`，加一个命令行入口。入口在有覆盖时向 stdout 打印 `-c` 的值，读不准时向 stderr 打印提示、stdout 为空，退出码恒为 0（判定失败不能让运行失败）。
- `codex-exec.sh` 只在 `WRITE_MODE=1` 时调用它，新增 `TRUST=()` 数组，放在 `APPROVAL` 之后，普通 run 与续跑两条 `CODEX_ARGS` 都展开它。只读路径不调用，参数逐项不变。
- 不改 `run_codex.py`、`delegate_backend.py`、`interface.json`：不新增用户参数，接口不变。

## 顺序与依赖

Task 1 → Task 2 → Checkpoint 1 → Checkpoint 2 → Task 3 → Task 4 → Checkpoint 3 → Checkpoint 4。

串行，在主会话做，不派子代理（每个 task 都小）。每个行为 task 先写测试并确认它红，再实现转绿。

## Task 1：`codex_trust.py` 纯函数与单元测试（WT-02、WT-03 的判定部分）

**描述：** 新增 `codex_trust.py` 与 `test-write-trust.py` 的单元部分：候选键（物理 cwd、同目录的 `$PWD`、信任根及其真实路径）、信任根（`--git-common-dir` 上一级，目录名须为 `.git`）、文本判定（任一候选键的 `"<键>"` 或 `'<键>'` 整串出现即命中）、读不准的四种原因与提示文案。

**验收条件：**
- 先红：模块不存在时测试报缺模块失败；
- 再绿：表头、点号、内联表三种写法与单引号键都命中；`<根>-sub`、`<根>/sub` 不命中；含 `"` 的路径、非 UTF-8、不可读、目录名不是 `.git` 各给出对应原因；无配置文件时给出覆盖值。

**验证：** `python3 -B plugins/delegate/tests/test-write-trust.py`
**依赖：** Spec 批准。
**涉及文件：** `plugins/delegate/scripts/codex_trust.py`、`plugins/delegate/tests/test-write-trust.py`。
**规模：** S，2 文件。

## Task 2：接入 `codex-exec.sh`（WT-01、WT-03、WT-04、WT-05）

**描述：** 先在 `test-write-trust.py` 加桩集成测试（临时 Git 夹具含 worktree，`CODEX_HOME` 指向临时目录，PATH 指向 `stub-codex`），再改 `codex-exec.sh`。

**验收条件：**
- 普通仓库与 worktree、根目录与子目录的 `--write` run，argv 含覆盖且键为主仓库路径；
- `--write --resumable` 与 `--resume … --write` 含覆盖；只读 run、只读续跑不含；
- 已有条目时不含；读不准时 stderr 有提示、退出码与无覆盖时相同；
- 运行前后隔离配置文件字节不变；
- `test-channel.sh`、`test-run-resume.py`、`test-review-backends.py` 原断言不改仍通过。

**验证：** `python3 -B plugins/delegate/tests/test-write-trust.py`、`/bin/bash plugins/delegate/tests/test-channel.sh`、`python3 -B plugins/delegate/tests/test-run-resume.py`、`python3 -B plugins/delegate/tests/test-review-backends.py`
**依赖：** Task 1；负责人确认与 S35 的先后。
**涉及文件：** `plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/tests/test-write-trust.py`。
**规模：** S，2 文件。

## Checkpoint 1（report）：桩测试全绿

运行 Task 2 的四条验证命令和 `scripts/validate.sh`，把命令与结果记入 todo 后继续。

## Checkpoint 2（report）：免费真机核验（WT-06）

记录真实 `~/.codex/config.toml` sha256；用 `codex_trust.py` 生成的参数在隔离 `CODEX_HOME`、无凭据下跑真实 `codex exec --sandbox workspace-write`，覆盖普通仓库根目录、子目录、worktree 子目录、已有 `untrusted` 条目四种，确认都不写入、都被 401 拒；测后再核 sha256。记录写进 `docs/verification/2026-10-26-delegate-s36-write-trust-check.md`。不花钱。

## Task 3：文档（WT-08）

**描述：** 中英文同步：
- 根 README 改写第 2 步加的那段，描述新行为与「读不准时可能写入」的例外；
- 插件 README 第 26 行；
- `docs/en/SPEC-write-trust.md`；
- `spec/channel.md`、`spec/run-resume.md` 及英文页各加一句指向；
- `docs/en/capability-map.md` 新行；
- 待发行说明。

**验收条件：** 中英文逐条对应；README 不再写「现在会改动 Codex 的用户配置」；链接锚点可达。
**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`
**依赖：** Task 2。
**涉及文件：** 约 11 个文档文件（只改文字，不动代码）。
**规模：** M。

## Task 4：总验证与记录（WT-09）

**描述：** 跑完整验证，把命令、结果、未验证项记入 todo。
**验证：** 规格「技术栈与命令」中的全部命令。
**依赖：** Task 3。
**涉及文件：** `tasks/write-trust/todo.md`。
**规模：** XS。

## Checkpoint 3（gate）：付费实测（WT-07）

单独授权后，在家目录下新建从未用过 Codex 的临时 Git 仓库，用当前源码跑一次真实 `--write`（写一个文件），确认文件写出、真实 `~/.codex/config.toml` sha256 不变。未授权就在 todo 里标「未验证」。

## Checkpoint 4（gate）：交付前人工验收

把 diff、验证记录和未验证项交用户审。提交、PR、发版另行授权。

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| 文本判定误命中（同一路径出现在别的配置项里） | 只会退回今天的行为（不覆盖），不会放宽信任；规格写明 |
| 系统级／托管配置里的 `untrusted` 被临时抬成 `trusted` | 列为开放问题；需要时再扩大扫描范围（只会更保守） |
| Codex 规范化路径的方式与 git 不同（符号链接） | 候选键含物理与逻辑路径；覆盖键未命中时 Codex 只会照旧写入，由免费真机核验观察 |
| 与 S35 同改 `codex-exec.sh`、README、能力图 | Task 2 前由负责人协调；后合入的一方 rebase 解决 |
| Codex 升级后写入条件或键规则变化 | 真机核验脚本留存，升级后可零成本重跑 |
