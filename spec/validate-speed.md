# 规格：validate-speed（免费总验证提速）

<!-- spec-guard: review approved 21ffcebc031f -->

简体中文 | [English](../docs/en/SPEC-validate-speed.md)

2026-11-25 起草。来源：ecosystem-lead #22978（「delegate 测试提速」，称用户原话「对，按这个发」）与 #22983（规范 v1.7.3 的 C2：快检查与全量耗时上限）。用户 2026-11-25 在本会话说「先升钉再提速」，升钉（PR #53）合并后说「写提速 Spec」。同日批准本规格，原话「批准；Q1 A；Q2 A」；验收与审查后的修订（A8 改动集与依赖展开、规则 1 与 3、A9 等待做法）同日经用户复审，原话「批准修订，本地提交」。

## 起因

每做一个需求，会话都要等 `scripts/validate.sh` 全量跑完。ecosystem-lead 在 main 941304c 上实测：37 个套件串行合计约 505 秒；最慢的 `test-run-timeout.py` 约 90 秒（真等超时），`test-channel-regressions.py` 约 61 秒（多处真 `sleep(3.2)`）。CI 两行耗时：`macos-system` 12 分 3 秒，`3.13` 8 分 48 秒（PR #53，运行 45593474833）。也没有只跑改动相关测试的快检查。

本机基线（本会话在 main 1575e4e 上量，8 核）：见「基线」一节。

## 前提（用户 2026-11-25 已确认）

- **A1 只改测试设施和测试，不改产品。** 改 `scripts/validate.sh`、新增 `scripts/run_suites.py`（并行执行器与 `--quick` 选择逻辑）、改 `plugins/delegate/tests/` 里有真等待的测试。`plugins/delegate/scripts/` 下的产品代码一行不动；测试要的短时限只靠现有环境变量（如 `DELEGATE_TIMEOUT_SECONDS`）和测试桩自己的参数。
- **A2 不改 CI 文件。** `.github/workflows/ci.yml` 已经调用 `validate.sh`，并行自动生效，所以本模块不碰 T4 文件。CI 前后耗时照样回报。
- **A3 静态检查留在前面、照旧串行。** JSON、shell、清单、共享段、Python 语法、本机路径、各脚本自检这些不进并行池，顺序与失败文字不变。
- **A4 回归套件并行跑。** 3 个 `.sh` 套件、31 个 `.py` 套件、`test-claude-isolation.py --policy-only`，合计 35 项进同一个并行池。并发数默认取 `os.cpu_count()`，`--jobs N` 指定，`--jobs 1` 就是串行。只用 Python 标准库。
- **A5 套件互相隔离。** 每个套件进程拿到自己新建的 `TMPDIR`（跑完删除）。原因：产品把日志写在 `${TMPDIR}/delegate/`，还会按 50 组清理旧日志；共用 `TMPDIR` 并行时，一个套件可能删掉另一个套件正在用的文件。`HOME` 不统一改，各测试自己设的照旧。
- **A6 输出与退出码不变形。** 每个套件的标准输出和标准错误各自缓存，跑完后按清单顺序整段打印，不交错。失败文字照旧是「`<套件>` 回归测试未通过」等原句，任一失败时总退出码为 1。`release_prepare.py` 靠 `Ran N tests in` 行数测试数、靠 `for SUITE in …; do … test-${SUITE}.py … done` 数循环套件，这两处都保持可解析，发版脚本不用改。
- **A7 末尾列最慢套件。** 全量跑完后，往标准错误打印耗时最长的 5 个套件和秒数，以及并行池的总墙钟。
- **A8 `--quick` 只跑改动涉及的套件。**
  - 改动集：`git merge-base HEAD origin/main` 到工作区（含暂存区和未跟踪文件；重命名按旧名、新名各算一个，删除的文件也算）。取不到 `origin/main` 或合并基点时退回全量。
  - 先展开产品脚本的间接依赖：`plugins/*/scripts/` 下的文件被改或被删时，其他引用了它文件名的产品脚本也算改动，传递到不再增加为止（2026-11-25 验收时补：只按直接文件名，改 `review_init.py` 选不到经 `review_result` 用到它的套件）。
  - 对应规则：
    1. 改的是套件文件本身，就跑这个套件；其他套件加载了它的（例如 `spec_from_file_location` 加载、直接运行），也照第 3 条选上。
    2. 只改 `docs/`、`spec/`、`tasks/`、`*.md` 根文档（插件内的 `commands/`、`skills/` 除外），不跑回归套件，只跑静态检查。
    3. 其他文件，用文件名在套件源码里搜，命中哪些就跑哪些；套件源码里有 `.glob('*<后缀>')` 并出现被改文件所在目录名的（整目录读取），也算命中。
    4. 一个都没命中，或者改了 `scripts/validate.sh`、`scripts/run_suites.py`、`.github/`，就退回全量。
  - 打印选了哪些套件、为什么选；退回全量时写明原因。静态检查在快检查里也照跑。
- **A9 去掉真等待，不放松断言。**
  - `test-run-timeout.py`：在现有期限公式允许的范围内调小 `DELEGATE_TIMEOUT_SECONDS` 和桩的睡眠时间。
  - `test-channel-regressions.py`：「子进程 3 秒后写标记，测试等 3.2 秒确认没写」改为子进程延迟可配置并记下启动时刻，测试只等到「启动时刻 + 延迟 + 0.5 秒」再检查；另断言检查时清理已在子进程本该写之前完成，并检查子进程已不存活。语义不变，仍要证明子进程在写之前已被回收。（原写的「0.5 秒后写、等 0.8 秒」不可行：清理本身要一两秒。）
  - 每处改动都对照原断言，不删、不放宽判定条件。
- **A10 文档。**
  - `AGENTS.md` 的检查入口写成 C2 v1.7.3：全量 `validate.sh`，快检查 `validate.sh --quick`；会话日常做 task 跑快检查，全量留给合并前和 CI。
  - `docs/development-workflow.md` 中英两页同步。
  - `CLAUDE.md` 本身没有这条，靠导入工作流文档，不另写；改动后共享段检查仍须一致。
- **A11 一个模块，不写用法草案。** 能力图末尾新增 `validate-speed`，依赖 `release-prepare`（发版脚本解析 `validate.sh`）。`review-snapshot-recheck` 只剩 R4（等 M1 实跑），先插队暂停，本模块合并后再回去。

## 基线

2026-11-25 本会话在 main 1575e4e 上量（8 核 Mac，`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`，单次）：退出 0，墙钟 407 秒（6 分 47 秒）。VS-2 的 2 分钟目标对照这个数。

## 命令

```text
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh [--quick] [--jobs N]
```

- 不带参数：静态检查加全部回归套件，并发数为核数。
- 参数错误时报用法，退出 64。

## 验收标准

- **VS-1 数量不少。** 全量跑完，测试项数（`Ran N tests` 合计）和套件数与改前相同：改前 512 项、31 个 Python 循环套件。去掉真等待时不删测试。
- **VS-2 本机全量变快。** 默认并发下本机全量墙钟不超过 2 分钟；回报改前改后的数字。
- **VS-3 并行与串行等价。** `--jobs 1` 与默认并发都退出 0；人为让一个套件失败时，两种方式都退出 1，且失败文字相同。用 `run_suites.py` 自己的离线测试证明，不靠递归跑 `validate.sh`。
- **VS-4 隔离。** 测试证明并行时每个套件的 `TMPDIR` 互不相同，跑完删除。
- **VS-5 输出不交错。** 测试证明两个套件同时输出时，打印结果按清单顺序整段出现。
- **VS-6 快检查选得对。** 对规则 1～4 各有离线用例：临时 git 仓库加假套件，断言选中的套件和退回全量的原因。
- **VS-7 慢套件榜。** 全量结束时标准错误里有最慢 5 个套件的名字和秒数。
- **VS-8 发版脚本不受影响。** `scripts/tests/test-release-prepare.py` 和 `test-validation-discovery.py` 通过；`release_prepare.loop_suites` 对新 `validate.sh` 数出的仍是 31。
- **VS-9 真等待去掉了。** `test-run-timeout.py` 和 `test-channel-regressions.py` 单独计时，比改前明显缩短，数字写进 todo。断言条数不少。
- **VS-10 CI 不变且回报。** `ci.yml` 不改；PR 的两行测试照样通过，回报两行耗时并和改前对比。
- **VS-11 文档同步。** A10 列的文件已更新，共享段检查通过。

## 边界

- **总是做：** 只用标准库；Bash 保持 3.2 兼容，测试用 `/bin/bash`，Python 用 `-B`；每次改动后跑全量；改测试前先记下原断言。
- **先问：** 要动产品代码才能缩短等待的；要改 `.github/workflows/` 的；`--quick` 规则要比 A8 更激进的（比如不跑文件名没命中的套件）。
- **不做：** 删测试、跳过测试、放宽断言、砍 CI 矩阵；把需要另备 guest 的实机套件（OS、SSH、live）放进离线检查；顺手删 `scripts/check-frontmatter.py`（另议）。

## 已定问题（原为未决）

- **Q1 只改文档时 `--quick` 是否完全不跑回归套件？** 定为 A「是」（A8 第 2 条）：这类文件没有测试读，静态检查已覆盖链接、本机路径和共享段。保守的做法是文档改动也退回全量，但这样快检查在文档 PR 上就没有用了。
- **Q2 并发数默认取核数，还是封顶？** 定为 A：取核数、不封顶：8 核机器上最慢的单个套件决定墙钟。CI 的 macOS 机器核数少，自动跟着变少。
