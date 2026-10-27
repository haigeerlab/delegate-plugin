# 实施计划：run-check

<!-- spec-guard: review approved -->

日期：2026-10-27。规格：[spec/run-check.md](../../spec/run-check.md)（用户 2026-10-27 批准，指纹 845bd3397b4f）。任务：[todo.md](todo.md)。前提：run-result、run-continue、run-longrun 已完成。

**修订 R1（2026-10-27，用户原话：「选 A：新增 plugins/delegate/references/run.md 放 1.3 用法和授权纪律，run.md 只加一句必须先读的指示；四个模块的文档任务按此修订，继续做。」）：** 命令说明渲染后不得超过 4000 字节（`test-command-migration.py`；超出时 Codex 跳过该 skill），`run.md` 已无余量。所以下文文档任务里「`run.md` 写……」的用法与纪律，一律改写进 `plugins/delegate/references/run.md`；`run.md` 只更新 frontmatter 的 argument-hint，并保留那一句「必须先读」的指示。对应成功条件里的命令说明部分，按写进参考文件验收。代码任务不变。

## 架构决定

- **新增 `run_check.py`，校验与执行放在一起。** 运算符常量与判定逐字照抄 module-crew `merge.py:24` 与 `_check_config`（POSIX `shlex.split`，按首尾匹配），注释写明来源和「要改先发 mc-coord」。三条拒绝文案作为常量，测试逐字比对 #11736 原文。
- **执行器复用 0.7.1 的 `run_codex.py`。** 检查命令以 `run_codex.py --report <runId>.check.cleanup 600 <argv…>` 执行：参数列表、不经 shell、到期回收、退出 124、125 都是现成的，不另写进程管理。
- **授权核对放在 `run_state.py`。** 链上授权文件的 sha256 记进状态文件，`check` 时与本次参数比对。
- **执行顺序。** Codex 结束 → 判定 → 执行检查（只在 `done` 时）→ Git 验收块 → 写结果文件 → 结果行。
- **执行方式。** 串行，在主会话做；每个行为任务都先红后绿。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Checkpoint 1 → Task 5 → Checkpoint 2
```

## Task 1：检查命令校验（照抄 S30）

**描述：**

- `run_check.py` 实现 `validate(command)`，返回参数列表或拒绝文案；
- `delegate_backend.py` 解析 `--check`（最多给一次），调用校验；拒绝时 stderr 只输出文案（前面不加 `delegate: `），退出 64；

新建 `test-run-check.py`。

**验收条件：**
- 先红后绿；
- CK-01：三条文案逐字等于 #11736 原文，退出 64，且不调用 Codex；
- CK-02：`foo&&bar`、`/bin/sh -c 'a && b'`、`2>&1`、单个 `&`、`$VAR` 放行；`>file`，以及每个运算符分别出现在 token 开头和结尾的情况，都拦截。

**验证：** `python3 -B plugins/delegate/tests/test-run-check.py`、`python3 -B plugins/delegate/tests/test-backend.py`

**依赖：** run-longrun 完成。**文件：** `plugins/delegate/scripts/run_check.py`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/tests/test-run-check.py`。**规模：** S。

## Task 2：检查命令执行与结果

**描述：**

- `run_check.py` 实现 `run(argv, repo, run_id, directory)`：经 `run_codex.py` 执行，输出写到 `<runId>.check.log`，取末尾 40 行、最多 16 KiB，映射成六种 `check.status`；
- `codex-exec.sh` 在 Git 验收块之前、只在 `done` 时调用它，其余状态记为 `skipped`；
- 元数据块加一行「检查：…」；结果文件加 `check` 字段；`.check.log`、`.check.cleanup` 归入日志类后缀表。

**验收条件：**
- 先红后绿；
- CK-03：参数列表执行、不经 shell（`*` 不展开）、工作目录为仓库根、stdin 为空、在 Git 验收块之前；
- CK-04：`passed`、`failed`、`timeout`（测试里缩短期限）、`cannot-run`（不存在的程序、126、127）、`unreaped`（替身执行器退出 125）、`skipped` 都正确，截断规则生效；运行的退出码与结果行不受影响。

**验证：** `python3 -B plugins/delegate/tests/test-run-check.py`、`python3 -B plugins/delegate/tests/test-run-result.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/run_check.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-check.py`。**规模：** M。

## Task 3：`--authorized-by`

**描述：**

- `delegate_backend.py` 解析 `--authorized-by`，没有 `--write` 时拒绝；
- `codex-exec.sh` 用 `lstat` 校验文件（普通文件、不是软链接、可读、非空、不超过 64 KiB），计算 sha256；
- `run_state.py` 在状态文件里记录 `authorization`，续跑与接续时核对，不一致时拒绝 `authorization mismatch`；
- 结果文件加 `authorization` 字段（`file`、`in-turn` 或 `null`）；元数据块加一行「写入授权：…」。

**验收条件：**
- 先红后绿；
- CK-05：拒绝表每一行都退出 64，且不调用 Codex；三种取值都正确；
- CK-06：sha256 相同时通过；不同或缺失时拒绝；链中途加上授权文件后，从那一轮起按它核对。

**验证：** `python3 -B plugins/delegate/tests/test-run-check.py`、`python3 -B plugins/delegate/tests/test-run-continue.py`

**依赖：** Task 2。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、`plugins/delegate/tests/test-run-check.py`。**规模：** M。

## Task 4：接口与能力事实

**描述：** `interface.json` 加 `run.check`、`run.writeAuthorization`；`delegate_capabilities.py` 给 codex 加对应的能力事实；`test-interface.py` 加断言，并断言 `run.write` 仍是 `"explicit"`、`run.check.operators` 与 `run_check.py` 的常量相同。

**验收条件：** CK-07；已有字段与断言不变；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 3。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/scripts/delegate_capabilities.py`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

跑本模块和前三个模块涉及的全部测试，以及 `git diff --check`，结果记入 todo 后继续。

## Task 5：授权纪律、命令说明、README 与待发行说明

**描述：**

- `run.md` 写 `--check`、`--authorized-by` 用法，以及两条纪律：写入授权的四个条件；检查命令只能取自项目配置里用户批过的 checkCommand 或 quickCheckCommand。
- `delegate-routing` 的 SKILL.md 加一句：满足四个条件并带 `--authorized-by` 时，例外地视为本轮已授权，其余照原规则。
- `help.md`、中英文 README、中英文待发行说明同步。

routing 规格的指向句在 run-rules 的汇总任务里写。

**验收条件：** CK-08 的命令、skill、README、待发行说明部分，中英文内容对应；`test-routing.sh` 通过。

**验证：** `/bin/bash plugins/delegate/tests/test-routing.sh`、`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`git diff --check`

**依赖：** Task 4。**文件：** `plugins/delegate/commands/run.md`、`plugins/delegate/commands/help.md`、`plugins/delegate/skills/delegate-routing/SKILL.md`、`plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** M（只改文档，文件多）。

## Checkpoint 2（report）：模块收尾与本地提交

跑总验证、两项 plugin validate、`git diff --check`，结果记入 todo；勾完本模块，把 `activeModule` 切到 `run-rules`；本地提交一次，不推送。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 照抄的运算符规则与 module-crew 不一致 | 高（`--check` 会拒掉 module-crew 已批的命令，或放行它拒的命令） | 常量与文案逐字照抄，测试用 #11736 原文和 module-crew 的边界例子比对 |
| 检查命令在沙箱外执行 | 高 | 只按参数列表执行，不经 shell；来源靠纪律限定；结果文件记录实际执行的参数 |
| routing skill 改动影响现有路由行为 | 中 | 只增一句例外，不改原规则，由 `test-routing.sh` 守住 |

## 开放问题

无。（拒绝文案的主语问题已在规格的开放问题里记录，按要求照抄。）
