# 任务清单：run-result

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-result.md)。
授权：用户 2026-10-27 对 Plan 原话「批准」。范围：改本仓库文件、跑测试与构建、在本分支本地提交（每个模块收尾一次）；做到 run-rules 的 Checkpoint 2（gate）停下。付费调用、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：事件流解析 `run_events.py`
- [x] Task 2：`run_state.py` 的判定、用量差值、结果文件与清理报告解析
- [x] Task 3：所有 run 路径加 `--json`，拆开事件流与 stderr
- [x] Task 4：写结果文件、`result=` 行、用量行与失败诊断
- [x] Task 5：`--strict`
- [x] Task 6：接口 1.3、能力事实与清理后缀
- [x] Checkpoint 1（report）：免费桩测试全绿
- [x] Task 7：共用假端点与免费真机测试
- [x] Task 8：命令说明、README 与待发行说明
- [x] Checkpoint 2（report）：模块收尾与本地提交

## 记录

**Task 1（2026-10-27）：** `test-run-result.py` 的 `RunEventsTests` 5 项先红（模块不存在），实现 `run_events.py` 后通过。

**Task 2（2026-10-27）：** `RunStateResultTests` 6 项中 5 项先红（旧状态文件兼容一项本就成立），实现后 11 项通过；`test-run-timeout.py` 不改通过。偏离 Plan 一处：`test-run-resume.py` 第 209 行对状态文件整体相等的断言，按规格补上新增的 `chainRoot`、`strict`、`usageTotal` 三个字段；比对方式仍是整体相等，没有放宽。`record` 新增可选的 `--events`、`--strict` 尾随参数，旧的 11、12 参数调用不变。

**Task 3（2026-10-27）：** `codex-exec.sh` 所有 run 路径加 `--json`，Codex 的 stdout 写 `.events.jsonl`、stderr 写 `.log`（收尾轮写 `.wrapup.events.jsonl` 与 `.wrapup`），会话 ID 改用 `run_events.py session`，`record` 传 `--events`。现有测试按 Plan 更新：`test-run-resume.py` 与 `test-run-timeout.py` 的假 codex 带 `--json` 时改为输出 `thread.started` 事件，三处参数逐项比对加上 `--json`；`test-write-trust.py` 的假 codex 同样改为输出事件；`test-review-backends.py` 不用改（它不比对 run 的参数）。偏离 Plan 两处：
- `test-channel.sh` 第 5 项（Plan 未列出）：桩原来往 stdout 打一行纯文本、断言它出现在 stderr；改用 `--json` 后 stdout 是事件流，于是把桩的输入改成一条 `{"type":"error","message":"可识别的过程文本"}` 事件，断言（退出 3、stderr 含该文本与「过程日志：」）一字不改。
- 失败诊断里「最近的事件」原排在 Task 4，为让第 5 项保持绿提前到本任务实现；路径行改为「完整过程日志：<log>；事件流：<events>」，`test-channel-regressions.py` 第 336 行的正则不改仍通过。

先红证据：新增的 `JsonEventsFlowTests` 4 项是在实现之后写的，补做了验证——临时换回改动前的 `codex-exec.sh` 时 4 项全部失败，恢复后通过。验证：`test-run-result.py` 15 项、`test-run-resume.py`、`test-run-timeout.py`、`test-write-trust.py`、`test-backend.py`、`test-review-backends.py`、`test-channel-regressions.py` 全部 OK；`test-channel.sh` 24 通过 / 0 失败。

**Task 4（2026-10-27）：** `ResultFileFlowTests` 10 项中 9 项先红（拒绝时不写一项本就成立）。实现：`run_state.py` 新增 `result`、`usage-line` 子命令与 `build_result`；`codex-exec.sh` 在 `finish` 里、`stop_runner` 之后写结果文件，有结果行时 `delegate: result=` 打印到 stdout 的结果行之前，否则打印到 stderr；元数据块加用量行；超时路径记录收尾方式。另两处：
- wrapper 的 `stop_runner` 两条报告行（0.7.1）改为追加进 `.cleanup` 文件，由 `finish` 已有的 `cat` 转发到 stderr，这样结果文件的 `cleanup.lines` 能收到它们；行文不变，只是在 stderr 里的位置挪到 Git 验收块之后。`test-channel-regressions.py` 不改仍通过。
- 两项新测试第一次失败是测试输入写错（续跑的假 codex 读 `STUB_RESUME_EVENTS`），改正输入，断言不变。

验证：`test-run-result.py` 25 项、`test-run-resume.py`、`test-run-timeout.py`、`test-write-trust.py`、`test-backend.py`、`test-channel-regressions.py` OK；`test-channel.sh` 24 通过 / 0 失败。

**Task 5（2026-10-27）：** `StrictFlowTests` 4 项中 3 项先红（与 `--review-context` 同用本就因参数不认识退出 64）。`delegate_backend.py` 解析并转发 `--strict`，与 `--review-context` 同用时拒绝；`codex-exec.sh` 在时间预算段之前插入结束标记段（普通版与可续跑版），`record` 与结果文件带上 strict，`unmarked` 时输出照常、退出 1。

**Task 6（2026-10-27）：** `test-interface.py` 新增 1.3 断言、`RetentionTests` 1 项，先红后绿。偏离 Plan 一处：`test-interface.py` 的 `test_resume_is_an_additive_minor_version` 原来断言 `interface == '1.2'`，按规格改为 `'1.3'`，同测试里 `review.command`、`doctor.command`、`run.resume` 的断言不变。

**Checkpoint 1（report，2026-10-27）：**
- `test-run-result.py`（30 项）、`test-run-resume.py`、`test-run-timeout.py`、`test-write-trust.py`、`test-backend.py`、`test-review-backends.py`、`test-channel-regressions.py`、`test-interface.py`、`test-reap-fake-endpoint.py`：全部 OK
- `/bin/bash plugins/delegate/tests/test-channel.sh`：24 通过 / 0 失败（LIVE 跳过）
- `claude plugin validate .`、`claude plugin validate ./plugins/delegate`：通过
- `git diff --check`：通过

**Task 7（2026-10-27）：** 把 0.7.1 `test-reap-fake-endpoint.py` 里的假端点抽成 `tests/fake-responses.py`（`start(script)`、`provider_args(server)`，按步骤回工具调用或答复）；回收测试改为引用它，断言不变，仍通过（顺带删掉因此不再使用的 `import threading`）。偏离 Plan 一处：delegate 的 wrapper 固定 `model_provider="openai"`，无法连到假端点，所以真机用例 `RealCodexEventsTests` 不经 wrapper，而是直接用真实 Codex 0.162.1 跑 `exec --json` 与 `exec resume --json`（临时 `CODEX_HOME`、不带凭据），再用 `run_events`、`run_state.run_usage` 解析产出的事件，核对会话 ID、命令与退出码（含失败命令）、累计用量递增与差值。本机有 `codex`，该用例实际执行并通过（9.1 秒），不是跳过。

**Task 8（2026-10-27）：** 中英文 README 新增「结果文件」一节，对外接口补 1.3 的 `run.result`、`run.usage`；中英文待发行说明写入 1.3 的第一条与三条升级提示。偏离 Plan：总验证里的 `test-command-migration.py` 要求命令说明渲染后不超过 4000 字节（超出时 Codex 会跳过该 skill）。改动前 `run.md` 渲染 3813 字节、`help.md` 3971 字节，几乎没有余量。因此 `run.md` 只加 `--strict` 到 argument-hint 和一句指向 README「结果文件」的话（渲染后 3996 字节）；`help.md` 不改。RS-12 的命令说明部分以「指向 README」的形式满足。其余四个模块的命令说明怎么放，属于规格没覆盖的决定，在本模块收尾后交用户定。

**Checkpoint 2（report，2026-10-27）：**
- `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：`validate: ok`（退出 0）
- `claude plugin validate .`、`claude plugin validate ./plugins/delegate`：通过
- `git diff --check`：通过；spec-guard `verify-artifacts`：4 通过 / 0 警告 / 0 失败
- 本地提交两次（实测与 1.3 规格计划、run-result 实现），未推送
