# 实施计划：validate-speed

<!-- spec-guard: review approved -->

日期：2026-11-25。规格：[spec/validate-speed.md](../../spec/validate-speed.md)（用户 2026-11-25 批准，原话「批准；Q1 A；Q2 A」）。任务：[todo.md](todo.md)。来源：ecosystem-lead #22978、#22983。

## 架构决定

- **执行器是一个标准库 Python 文件。** 新建 `scripts/run_suites.py`：
  - 输入：套件清单（每项是一条完整命令和显示名）、`--jobs N`、`--quick`。
  - 用 `concurrent.futures.ThreadPoolExecutor` 管 `subprocess.run`。每个套件进程拿到自己的 `tempfile.mkdtemp()` 作为 `TMPDIR`，跑完删除。
  - 每个套件的 stdout、stderr 各自缓存，按清单顺序整段写回本进程的 stdout、stderr。
  - 失败时写原句「`<名>` 回归测试未通过」等到 stderr。
  - 结束时往 stderr 写最慢 5 个套件和总墙钟。
  - 退出码：有失败为 1，参数错为 64。
  - 选择逻辑（`--quick`）写成纯函数（输入改动文件列表和套件源码文本，输出选中集合与原因），可以离线测试。
- **`validate.sh` 的形状。** 静态检查段原样不动，放在前面。
  - 原来的三个循环改为把命令收集进数组。循环体仍写 `test-${SUITE}.py`，`release_prepare.loop_suites` 照旧能数出 31；`--policy-only` 那一项也进数组。
  - 最后把数组交给 `run_suites.py` 执行。
  - `validate.sh` 自己只解析 `--quick`、`--jobs N`，其他参数退出 64。
- **改前计时。** 并行改造之前，先用 `--jobs 1` 形态（或直接逐个跑）记下 `test-run-timeout`、`test-channel-regressions` 的单独耗时和测试项数，写进 todo，作为 VS-9 的对照。
- **执行方式。** 按临时规则，Task 1～4 用 `/delegate:run --write` 派给 Codex，一次一个 Task。每个 Task 回来后，本会话看验收块和真实 diff，重跑该 Task 的验证命令。Task 5 是文档，本会话自己写。每个行为任务先红后绿。
- **审查。** Checkpoint 2 用 Claude 子代理（code-reviewer，只读）审全部 diff 加本规格。

## 顺序与依赖

```text
Task 0（本会话，记录改前计时）→ Task 1 → Task 2 → Task 3 → Task 4 → Checkpoint 1（report）
→ Task 5 → Checkpoint 2（gate：审查与提交）→ Checkpoint 3（gate：PR、合并与回报）
```

Task 3、4 只改各自的测试文件，和 Task 1、2 不冲突。但 Codex 在同一个工作区写，所以仍按顺序派。

## Task 0：改前计时

**描述：** 本会话在当前分支（未改代码）上逐个单独跑 `test-run-timeout.py`、`test-channel-regressions.py`，记下秒数和 `Ran N tests`；再记全部套件各自的 `Ran N` 合计（应为 512）。

**验收条件：** todo 里有这几个数。**验证：** 命令和输出写进 todo。**依赖：** 无。**文件：** `tasks/validate-speed/todo.md`。**规模：** XS。

## Task 1：并行执行器

**描述：** 新建 `scripts/run_suites.py`，覆盖并行池、隔离 `TMPDIR`、按序输出、失败原句、退出码和慢套件榜；`validate.sh` 改为收集数组后调用它，加 `--jobs` 解析；新建 `scripts/tests/test-run-suites.py`（用假套件：会睡、会失败、会打印 `TMPDIR`、会同时大量输出），登记进 `validate.sh` 和发现测试的桩清单。

**验收条件：**
- 先红后绿。
- VS-3：`--jobs 1` 和 `--jobs 4` 结果一致；有一个假套件失败时，两种方式都退出 1，失败文字相同。
- VS-4：并行时每个套件拿到的 `TMPDIR` 不同，跑完删除。
- VS-5：两个同时大量输出的假套件，打印结果按清单顺序整段出现。
- VS-7：慢套件榜出现在 stderr。
- VS-8：`test-release-prepare.py`、`test-validation-discovery.py` 通过，`loop_suites` 对新 `validate.sh` 数出 31。
- 全量 `validate.sh` 退出 0。

**验证：** `python3 -B scripts/tests/test-run-suites.py`、`python3 -B scripts/tests/test-release-prepare.py`、`python3 -B scripts/tests/test-validation-discovery.py`、`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`

**依赖：** Task 0。**文件：** `scripts/run_suites.py`、`scripts/tests/test-run-suites.py`、`scripts/validate.sh`、`scripts/tests/test-validation-discovery.py`。**规模：** M。

## Task 2：`--quick`

**描述：** 在 `run_suites.py` 里加改动集读取（`git merge-base HEAD origin/main`，加工作区、暂存区、未跟踪文件）和 A8 的四条规则；打印选中的套件和原因；`validate.sh` 透传 `--quick`。

**验收条件：**
- 先红后绿。
- VS-6：四条规则各至少一个离线用例，用临时 git 仓库加假套件，断言选中集合和退回全量的原因。
- 取不到 `origin/main` 时退回全量。
- 参数错退出 64。

**验证：** `python3 -B scripts/tests/test-run-suites.py`，并在本分支实跑一次 `validate.sh --quick`，看选择说明。

**依赖：** Task 1。**文件：** `scripts/run_suites.py`、`scripts/tests/test-run-suites.py`、`scripts/validate.sh`。**规模：** M。

## Task 3：`test-run-timeout` 去掉真等待

**描述：** 在现有期限公式（`run_state.deadlines`）允许的最小值内，调小 `DELEGATE_TIMEOUT_SECONDS` 和 `STUB_SLEEP`；不改产品代码。

**验收条件：**
- 测试项数不变。
- 逐条对照原断言，不删、不放宽。
- 单独耗时比 Task 0 记的数明显缩短，新数写进 todo。
- 如果确实要改产品代码才能再缩短，停下来问用户（Spec「先问」）。

**验证：** `python3 -B plugins/delegate/tests/test-run-timeout.py`（单独计时），以及全量。

**依赖：** Task 0。**文件：** `plugins/delegate/tests/test-run-timeout.py`，可能还有它用的测试桩。**规模：** S。

## Task 4：`test-channel-regressions` 去掉真等待

**描述：** 把「子进程 3 秒后写标记、测试等 3.2 秒」改成测试桩可配置的短延迟（例如 0.5 秒后写、等 0.8 秒），三处 `sleep(3.2)` 和桩里对应的 `sleep(3)` 一起改；仍要证明子进程在写之前已被回收。

**验收条件：** 同 Task 3。另外，故意让清理失效（例如临时不杀子进程）时，测试应当失败。这个用一次性的本地实验验证，不提交。

**验证：** `python3 -B plugins/delegate/tests/test-channel-regressions.py`（单独计时），以及全量。

**依赖：** Task 0。**文件：** `plugins/delegate/tests/test-channel-regressions.py`，可能还有对应的测试桩。**规模：** S。

## Checkpoint 1（report）：全量达标

- 默认并发跑全量 3 次，记墙钟（VS-2：不超过 2 分钟）和 `Ran N` 合计（VS-1：512）。
- 再用 `--jobs 1` 跑一次，确认也退出 0。
- 记进 todo 后继续。

## Task 5：文档

**描述：**
- `AGENTS.md` 的检查入口按 C2 v1.7.3 改写。
- `docs/development-workflow.md` 和 `docs/en/development-workflow.md` 写明 `--quick`、`--jobs`、慢套件榜，以及日常跑快检查、合并前跑全量。
- 补英文规格页 `docs/en/SPEC-validate-speed.md`，中文规格页顶部链接改成指向它。
- 能力图英文页 `docs/en/capability-map.md` 加上新模块。

**验收条件：** VS-11：共享段检查和全量通过，`git diff --check` 干净。**依赖：** Task 2。**文件：** 上面列的五六个文档。**规模：** S。

## Checkpoint 2（gate）：审查与提交

- Claude 子代理审全部 diff 加规格。
- 阻断项先修，建议项逐条写处理结果进 todo。
- 用户确认后，在本分支本地提交（中文提交信息）。

## Checkpoint 3（gate）：PR、合并与回报

- 推送和开 PR 要用户确认，合并按 F3。
- CI 两行耗时和改前（`macos-system` 12 分 3 秒，`3.13` 8 分 48 秒）对比写进 todo（VS-10）。
- 合并后起草给 ecosystem-lead 的答复（正式答复 #22978，并说明 #22983 的 C2 已同步），附改前改后的本机和 CI 耗时，经用户同意再发。
- 之后把 `activeModule` 切回 `review-snapshot-recheck`。

## 风险与缓解

- **并行暴露隐藏的共享状态**（端口、固定路径、`HOME` 下的文件）。缓解：Task 1 后连跑 3 次全量；出现偶发失败就查是哪个套件，对它单独隔离，不靠重跑掩盖。
- **CI 机器核数少，提速有限。** 缓解：如实回报；不为 CI 另改工作流（Spec A2）。
- **缩短等待后在慢机器上偶发失败。** 缓解：留出与原来相同比例的余量（原来是 3 秒对 3.2 秒，改后的写入延迟和等待时间之间要有更宽的差距）；CI 的 `macos-system` 行是检验。
- **Codex 到时限中途停下（E2 出现过）。** 缓解：每个 Task 范围小；回来一律看 diff，本会话补完。

## 未决问题

无。
