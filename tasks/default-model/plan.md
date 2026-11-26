# 实施计划：default-model

<!-- spec-guard: review approved -->

日期：2026-11-26。规格：[spec/default-model.md](../../spec/default-model.md)（用户 2026-11-26 批准，原话「批准」）。任务：[todo.md](todo.md)。来源 ecosystem-lead #23280；接口影响已由 ecosystem-lead #23282 判断为无下游读者，不另行通知。依赖已完成的 reviewer-selection、run-result、detection。

## 架构决定

- **取值是纯函数。** 新建 `plugins/delegate/scripts/delegate_defaults.py`：`config_path(environ)` 按 P1 算路径；`load(path)` 按 E2 校验，成功返回 `{backend: {'model', 'effort'}}`，失败抛 `ConfigError(code, key_path)`；`resolve(backend, model, effort, config)` 按 E1 返回 `(model, model_source, effort, effort_source)`。校验复用 `delegate_model.model_error()` 与 `delegate_backend` 的 `--effort` 取值表（抽成同一个常量，不复制）。
- **一处读、一处报错。** `delegate_cli.main()` 分派 review／run 之前调 `load()`；出错按 E3 打一行、退出 64。读到的配置挂在参数对象上往下传，下游不再读文件。
- **最终后端定了再取值。** 显式后端在参数校验后取；`auto` 在 `reviewer_select.choose()` 之后取（P2）；续跑与接续不取值，来源记 `resumed`（P3）。
- **来源传给 Bash。** `delegate_backend.main()` 转发 run 时加内部参数 `--model-source`／`--effort-source`（Checkpoint 2 审查后由环境变量改来，见 todo）；`codex-exec.sh` 只接受 `explicit`／`config`／`host_default`，未给时按今天规则推断（E8 兼容入口因此不变）；`run_state.py` 把两项写进结果文件。
- **测试不碰真实配置。** `scripts/run_suites.py` 给每个套件设独立的空 `XDG_CONFIG_HOME`（和现有每套独立 `TMPDIR` 同一处），`test-run-suites.py` 断言这一点；需要「未设 XDG」的用例在套件里自己去掉变量并指向临时 `HOME`。
- **执行方式。** 串行，在主会话写（用户 2026-11-23 定：实现类 task 由本会话自己写）；每个行为任务先写测试并确认红，再实现。

## 顺序与依赖

```text
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Checkpoint 1（report）→ Task 6
→ Checkpoint 2（gate：Codex 只读审查与复审；本地提交须你另行明确同意）→ Checkpoint 3（gate：交付验收，含推送与开 PR 的授权请求）
```

## Task 1：配置读取与取值

**描述：** 新建 `test-default-model.py` 并确认红，再实现 `delegate_defaults.py`；套件登记进 `scripts/validate.sh` 与 `scripts/tests/test-validation-discovery.py`；`run_suites.py` 给每个套件设空 `XDG_CONFIG_HOME`，`test-run-suites.py` 加断言。

**验收条件：** DM-01（取值穷举）；DM-02（三种路径情形）；DM-03 的函数层（十个原因码各一例、字段类带字段路径、错误信息不含值、文件不存在返回空配置）。

**验证：** `python3 -B plugins/delegate/tests/test-default-model.py`、`python3 -B scripts/tests/test-validation-discovery.py`、`python3 -B scripts/tests/test-run-suites.py`

**依赖：** 无。**文件：** `plugins/delegate/scripts/delegate_defaults.py`、`plugins/delegate/scripts/delegate_backend.py`（只抽出 `--effort` 取值常量）、`plugins/delegate/tests/test-default-model.py`、`scripts/validate.sh`、`scripts/run_suites.py`、`scripts/tests/test-validation-discovery.py`、`scripts/tests/test-run-suites.py`。**规模：** M。

## Task 2：入口与审查

**描述：** 先在 `test-review-cli.py`、`test-review-result.py` 写用例确认红，再改 `delegate_cli.py`（读配置、报错、`auto` 后取值、`--dry-run` 预览）、`delegate_backend.py`（显式后端取值）、`review_result.base_report()`／`context_failure()`（`model_source`）。

**验收条件：** DM-03、DM-04 的审查端到端（退出 64、一行、`delegate: invalid config` 开头）；DM-08（显式 codex、显式 claude-code、auto 选中两家各一次；无配置时 `host_default`／`null`）；DM-09；DM-15（Codex 宿主环境调 `--backend claude-code`，桩 Claude 收到 `--model claude-opus-5-5`）。

**验证：** `python3 -B plugins/delegate/tests/test-review-cli.py`、`test-review-result.py`、`test-reviewer-select.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/delegate_cli.py`、`plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/review_result.py`、`plugins/delegate/scripts/review_execution.py`（若 Codex 审查要接推理强度）、`plugins/delegate/tests/test-review-cli.py`、`plugins/delegate/tests/test-review-result.py`。**规模：** M。

## Task 3：执行与续跑

**描述：** 先在 `test-run-result.py`、`test-run-resume.py`、`test-run-continue.py`、`test-default-model.py` 写用例确认红，再改 `delegate_backend.main()` 转发、`codex-exec.sh`（读来源变量、打印行注明来源）、`run_state.py`（结果文件两项）。

**验收条件：** DM-03、DM-04 的 run 端到端（含 `--resume` 时配置有错也退出 64）；DM-05；DM-06；DM-07；DM-10（直接调 `codex-exec.sh` 不读配置）。

**验证：** `python3 -B plugins/delegate/tests/test-run-result.py`、`test-run-resume.py`、`test-run-continue.py`、`test-default-model.py`

**依赖：** Task 2（入口读配置）。**文件：** `plugins/delegate/scripts/delegate_backend.py`、`plugins/delegate/scripts/codex-exec.sh`、`plugins/delegate/scripts/run_state.py`、上述四个测试文件。**规模：** M。

## Task 4：体检

**描述：** 先写用例确认红（无配置、有效配置、配置错误三种；`--reviewers` 不变），再改 `review_doctor.py` 加「默认模型」一段。

**验收条件：** DM-11（错误时其余检查照常跑完、退出 1；无配置或有效时退出码与今天相同）。

**验证：** `python3 -B plugins/delegate/tests/test-default-model.py`、`test-review-backends.py`

**依赖：** Task 1。**文件：** `plugins/delegate/scripts/review_doctor.py`、`plugins/delegate/tests/test-default-model.py`。**规模：** S。

## Task 5：接口 1.8

**描述：** 先改 `test-interface.py` 期待 1.8、顶层 `defaults`、报告稳定字段 `model_source` 并确认红，再改 `interface.json`；断言 `defaults.sources` 与 `delegate_defaults` 里的来源常量一致。

**验收条件：** DM-12；两项 plugin validate 通过。

**验证：** `python3 -B plugins/delegate/tests/test-interface.py`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`

**依赖：** Task 2、Task 3。**文件：** `plugins/delegate/interface.json`、`plugins/delegate/tests/test-interface.py`。**规模：** XS。

## Checkpoint 1（report）：免费验证全绿

全量 `validate.sh` 退出 0（含 DM-13：没有配置文件时现有套件不改断言通过）、两项 plugin validate、`git diff --check`、产物校验；把命令与结果记入 todo 后继续。

## Task 6：文档同步

**描述：** 插件中英文 README 加「默认模型配置」一节（路径、格式示例、优先级、报错读法）；`commands/review.md`、`commands/run.md`、`commands/doctor.md` 加一句指向（注意 `review.md` 渲染上限 4000 字节）；`spec/integration-interface.md` 及英文页补 1.8 一条并把 `model_source` 列入稳定字段；`spec/run-result.md` 及英文页字段表加两项；中英文待发行说明加本项。

**验收条件：** DM-14 逐项核对，位置记入 todo。

**验证：** `verify-artifacts`、`git diff --check`、逐项核对记录。

**依赖：** Checkpoint 1。**文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`plugins/delegate/commands/review.md`、`plugins/delegate/commands/run.md`、`plugins/delegate/commands/doctor.md`、`spec/integration-interface.md`、`docs/en/SPEC-integration-interface.md`、`spec/run-result.md`、`docs/en/SPEC-run-result.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。**规模：** S（只改文档）。

## Checkpoint 2（gate）：审查与复审

对当前树跑一遍全量验证，再用 `/delegate:review --backend codex` 只读审全部改动（用 Codex 额度，发起前问你），阻断先修；之后交你复审实际 diff，重点是优先级、报错格式和续跑路径。改到的 `integration-interface`、`run-result` 合同随复审重新记录批准。**本地提交是独立授权项**，只有你在这一步明确同意才提交。

## Checkpoint 3（gate）：交付验收

在最终交付树上重跑全量验证、两项 plugin validate、`git diff --check`；按最终验收格式报告 DM-01～DM-15，列实际改动文件与越界检查。推送与开 PR 在这里请你授权；合并按项目规则（你回「合并」）；发版与告诉 ecosystem-lead 另行授权。

## 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 测试读到你真实的 `~/.config/delegate` | 中 | 运行器给每个套件设空 `XDG_CONFIG_HOME`，有用例断言；路径类用例用临时 `HOME` |
| 给所有套件设 `XDG_CONFIG_HOME` 影响其他工具 | 低 | 套件里的 Codex／Claude 都是桩；真实 Claude 预检用例读的是 `~/.claude`，不看 XDG；全量跑一遍确认 |
| 续跑漏判，误用配置覆盖原会话模型 | 中 | 续跑路径不调 `resolve()`；DM-07 断言桩收到的是原会话模型 |
| `commands/review.md` 超过渲染上限 | 低 | 只加一句指向 README，改完量字节数 |
| `--effort` 取值表抽常量时改动现有参数解析 | 低 | 只移动不改值；现有参数用例不改断言通过 |

## 开放问题

- 无。
