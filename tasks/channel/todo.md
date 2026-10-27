# 当前维护核对：channel

- [x] Task 9：执行已授权的当前通道 live 样本，记录成功、失败或环境不可运行及证据。

Task 9 结果：既有 --live 入口退出 0，25 通过/0 失败，真实只读答复非空（3 字节）；产品快照不变，无自动重试。channel:8-A1/8-V1 取得当前样本依据，历史完成/批准仍未知。见[本批 live 证据](../../docs/verification/2026-10-08-live.md)。

日期：2026-10-08。计划：[plan.md](plan.md)。只跟踪本次接入，不替代历史产品验收。

- [x] 当前规格、模块映射及中英文链接核对通过。
- [x] 接入前 plan/todo 已按字节归档，SHA-256 与 `56c3ba7` 一致。
- [x] 本轮插件结构、阶段及相关确定性验证通过，结果已记录。

## 实际记录

归档：运行本轮归档核验，逐字节比较基准提交与存档，并验证 manifest 中 SHA-256；本模块两份原文均一致。
本轮核对：Spec Guard 0.52.3 严格能力图解析成功，产物检查为 3 通过、0 警告、0 失败；完成项写入前阶段为 BUILDING。
`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0；本模块 24 条 shell 断言通过；统一 backend 10 与 channel-regressions 7 个 Python 测试通过，eval 自检 7 + 12 通过。
迁移规格正文与命令围栏核对一致（仅导航链接调整）；Markdown 文件链接和锚点核对通过。当前清单完成后的阶段另在最终报告核验。
两项原生 `claude plugin validate` 通过。完整本轮记录见 [接入任务](../../docs/process/2026-10-08-adoption/todo.md)。

## 未验证项

历史人工批准、旧清单各项当时的验收、真实交互行为及远端交付未核实。
这些事实不因本轮归档、桩验证或阶段 `DONE` 被改成完成。

## 内容补全任务（2026-10-08）

- [x] Task 4：双语规格的开发约束齐备，原行为合同保留。
  - 描述：按增补计划补齐中英文规格的开发约束，不改变原功能合同。
  - 验收：六个核心领域完整；双语编号/命令/代码示例一致。
  - 验证：标题、源代码片段、原正文保留核对。
  - 依赖：初轮维护 1–3；涉及文件：本模块中英文 Spec；规模 S（2 文件）。
  - 结果：文档内容检查退出 0；六领域/三级边界存在；两版新命令及源代码片段一致；原中英文行为正文完整保留。
- [x] Task 5：条款到已有测试与缺口的映射齐备。
  - 描述：把现有产品条款对应到测试和源码，明确尚未充分覆盖的条件。
  - 验收：全部条款有映射行，测试引用存在，覆盖限制明确，plan 含逐任务字段。
  - 验证：条款编号、源码与测试断言定向核对。
  - 依赖：Task 4；涉及文件：本模块 plan、共享验证映射；规模 S（2 文件）。
  - 结果：5 个 CH 条款与映射逐项对应；全表 13 行，16 个明确 Python 用例引用存在；缺口保持部分覆盖。plan Task 4–6 的六字段已核对。
- [x] Task 6：本轮内容验收及实际证据已记录。
  - 描述：核验本次文档及其证据，完成维护记录而不关闭历史未知。
  - 验收：本轮完成项有证据，历史未知及产品覆盖缺口保持开放。
  - 验证：文档链接/字段、插件结构/阶段、归档哈希、产品范围比较。
  - 依赖：Task 5；涉及文件：本模块 todo；规模 S（1 文件）。
  - 结果：文件链接/锚点、8 份归档和 30 份证据哈希均通过；verify-artifacts 为 3 通过/0 警告/0 失败；diff 空白及产品范围检查通过。新增 task 完成前阶段为 BUILDING；完成后的阶段由最终报告记入。既有产品测试沿用首轮真实离线结果，本次未重复运行。

- [x] Task 7：本模块历史裁决及免费补验记录齐备。
  - 描述：逐条区分当前证据、合同替代和未验证，不回填历史勾选。
  - 验收：全部原条目有来源/理由/证据；历史批准保持未知；样本限制明确。
  - 验证：行号/文本/哈希、定向结果和产品范围核对。
  - 依赖：Task 4–6；涉及文件：本模块 todo；规模 S（1 文件）。
  - 结果：52 条：39 项当前证据支持、7 项合同替代、6 项仍待验证，逐项记录见[裁决](../../docs/verification/2026-10-08-historical-reconciliation.md)；SUP-01–06 的同组清理、日志权限/软链接及无 HEAD 样本通过，详见[定向补验](../../docs/verification/2026-10-08-supplemental.md)。历史完成/批准均未知；临时夹具不等于永久回归或完整宿主验收。

- [x] Task 8：免费反向条件证据与当前裁决更新。
  - 描述：临时副本变异/还原与定向记录，不改产品。
  - 验收：指定断言抓住故意错误、还原通过；历史未知保留。
  - 验证：本批正常/变异/还原、归档哈希和产品范围。
  - 依赖：Task 7；涉及文件：本模块 todo；规模 S（1 文件）。
  - 结果：MUT-01 抓住变量多字节错误，覆盖 2 条原条件；无变异和还原总套通过。工具范围取舍追到引入提交，但人工批准未知。见[本批证据](../../docs/verification/2026-10-08-mutation.md)。历史完成/批准保持未知，产品未改。

- [x] Task 10：当前 Bash 决定及已安装斜杠命令验收。
  - 结果：当前用户批准以 ADR 记录，channel:7-A1 归为合同替代；原生 user-scope /delegate:delegate 实际解析，Bash timeout 600000，真实 read-only Codex 一次答复“批次验收通过”，18 字节 answer/5924 字节过程日志；夹具前后文件哈希相同。仅当前一次样本，历史批准仍未知。见[整批证据](../../docs/verification/2026-10-08-bulk.md)。

## S41：中止时回收后代进程组（v0.7.1，2026-10-27）

计划见 [plan.md](plan.md) 的 S41 一节。

- [x] Task 11：回归测试先红（setsid 后代、有界 wait、wrapper finish、真实 Codex 连假端点）。
  - 红灯（Checkpoint 7，report，2026-10-27，实现前）：`python3 -B plugins/delegate/tests/test-channel-regressions.py` 13 项中 6 项失败，旧 8 项仍绿。到期与 TERM/INT/HUP 四次都是「new-session descendant survived cleanup」；finish 测试 25 秒内不退出（「wrapper hung waiting for a runner that ignores TERM」）；有界 wait 测试返回 124 而非 125（原代码在最终 `wait()` 上等到子进程自然结束）。
  - 更正：finish 用例第一次的红灯是测试自身的错误（`backend.py` 会 `from run_codex import stop_group`，替身脚本在导入时就挂住了）。改成只在作为主程序运行时才忽略 TERM 后，对 `origin/main` 的原版代码重跑（`--root` 指向 `git archive origin/main` 解出的副本）仍然是红灯，但原因是：原版 wrapper 约 4.6 秒就退出，把忽略 TERM 的执行进程留成孤儿，也没有报告。也就是说，原版 `finish` 的 `wait` 在这种情形下并不挂住。
  - `python3 -B plugins/delegate/tests/test-reap-fake-endpoint.py`（真实 Codex 0.162.1，假端点，临时 `CODEX_HOME`）：到期、TERM、INT、HUP 四次都失败，`run_codex.py` 均及时退出，但 `/bin/zsh -lc … sleep 40` 与 `sleep 40` 残留。红灯残留已手工清掉；测试善后改为累计所有见到的 PID。
- [x] Task 12：`run_codex.py` 回收后代、5 秒上限、125 与清理报告。
- [x] Task 13：`codex-exec.sh` 转发 `.cleanup`、`finish` 有界、保留清理加后缀。
  - 绿灯（2026-10-27）：`test-channel-regressions.py` 13 项全过（67.8 秒）；`test-reap-fake-endpoint.py` 2 项（含 4 个场景）全过（21.5 秒）；`test-run-timeout.py` 26 项、`test-run-resume.py` 20 项、`test-backend.py` 12 项全过；`test-channel.sh` 24 通过 / 0 失败（live 跳过）。之后没有残留的 `sleep`。
- [x] Task 14：中英文文档同步。
  - `DESIGN.md`、`docs/en/DESIGN.md`、`README.md`、`README.en.md`（清理描述、退出码 125、20 个回归套）、`plugins/delegate/commands/run.md`、`docs/releases/unreleased.md` 及英文页。旧的「脱离进程组不保证」说法只在 review 命令里还有（与本次无关）。
- [x] Task 15：全量免费验证与配置指纹对照。
  - 第一轮总验证失败 3 项：发现回归缺新套件登记；`test_timeout_ignoring_sigterm_is_bounded_and_returns_124` 外层 8 秒超时（原版代码单跑同样要 5.1–7.9 秒，预算本来就紧），并且在冻结窗口里被外层 KILL，留下一个停止状态（`Ts`）的假 codex 孤儿；finish 用例与两个信号子用例在负载下超时。
  - 修订 R1：冻结只持续到发完 TERM，后代组与 Codex 的 2 秒宽限期并行；`finish` 改按 `$SECONDS` 真实秒数轮询；新信号用例的启动等待放宽到 20 秒；发现回归登记 `reap-fake-endpoint`。规格中英文与文档同步。R1 待用户在 Checkpoint 8 确认。
  - 第二轮（2026-10-27）：`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 输出 `validate: ok`（7 分 37 秒，Python 回归合计 253 项，shell 套 7/12/24/19/10 全过）；`claude plugin validate .` 与 `claude plugin validate ./plugins/delegate` 都通过；`git diff --check` 无输出。`~/.codex/config.toml` 的 sha256 前后都是 `84bbafa4…5538`。测试后没有残留的 `sleep 40`、假 codex 或夹具进程。
- Checkpoint 8（gate）：2026-10-27 用户在本会话回复「修订 R1 和 diff 审查通过。」
