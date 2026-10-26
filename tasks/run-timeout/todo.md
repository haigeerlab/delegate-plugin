# 任务清单：run-timeout

计划：[plan.md](plan.md)；规格：[spec](../../spec/run-timeout.md)。
授权：用户 2026-10-26 对 Plan 原话“批准”。范围为 Task 1–Task 9 的本地实现与免费验证，做到 Checkpoint 3 前停下；付费实测、提交、推送、PR、版本号与发版不在此授权内。

- [x] Task 1：killpg EPERM 修复
- [x] Task 2：`run_state.py` 的期限、判定与文件清单
- [x] Task 3：时间预算段、`M` 期限与 `TIME_UP` 结束
- [x] Checkpoint 1（report）：第一道收尾到位
- [x] Task 4：收尾轮与兜底
- [x] Task 5：写模式改动文件清单与清理
- [x] Task 6：从 `timeout` 续跑
- [x] Task 7：接口 1.2
- [x] Checkpoint 2（report）：免费验证全绿
- [x] Task 8：命令说明、README 与待发行说明
- [x] Task 9：合同指向句与 Always 规则修订
- [x] Checkpoint 3（gate）：付费真实实测 H1–H5（已执行；H2 频率判断不成立、H3 未验证，见记录）
- [x] Checkpoint 4（gate）：交付验收

## 记录

**Task 1（2026-10-26）：** 新增 `RunCodexEpermTests` 两项；修复前两项都以 `PermissionError: [Errno 1] Operation not permitted` 报错，修复后 `test-channel-regressions.py` 9 项通过。

**Task 2（2026-10-26）：** `test-run-timeout.py` 单元部分 6 项先红（3 失败、3 错误），实现后通过；`test-run-resume.py` 20 项不改通过。`record` 现在总是读答复判定 `TIME_UP:`（普通 run 不判 `NEED_USER:`），新增可选第 12 参数强制状态。

**Task 3（2026-10-26）：** 集成部分 6 项先红后绿。偏离 Plan 两处，均为缩小改动：
- 没有改共用的 `stub-codex`：`test-run-timeout.py` 自带假 codex（与 `test-run-resume.py` 的做法一致），续跑时读 `STUB_RESUME_*` 变量。
- 受影响的已有断言是三处而不是 Plan 写的两处：除 `test-channel.sh` 第 16 项（改为比对到时间预算段首，因 `T0` 每次不同）和 `test-run-resume.py` 普通 run 提示词结尾（改为断言任务后紧跟时间预算段）外，`test-run-resume.py` 续跑参数断言也逐字比对了续跑提示词；按规格续跑也追加时间预算段，改为参数逐项比对、提示词比对到时间预算段首。三处的参数断言都没放宽。

**Checkpoint 1（report，2026-10-26）：**
- `python3 -B plugins/delegate/tests/test-channel-regressions.py`：9 项 OK
- `python3 -B plugins/delegate/tests/test-run-timeout.py`：12 项 OK
- `python3 -B plugins/delegate/tests/test-run-resume.py`：20 项 OK
- `/bin/bash plugins/delegate/tests/test-channel.sh`：24 通过 / 0 失败（LIVE 跳过）
- `git diff --check`：通过

**Task 4（2026-10-26）：** 9 项新测试中 8 项先红（无结果行），信号中断一项本就成立；实现后通过。普通 run 的日志里也有会话 ID（ephemeral 会话同样有 ID，只是不落盘），按规格兜底写「无」，因此普通 run 不提取会话 ID。

**Task 5（2026-10-26）：** 3 项先红后绿。写模式启动前把 porcelain 快照存为 `<runId>.baseline`；清理覆盖 `.wrapup`、`.wrapup.answer`、`.baseline`。

**Task 6（2026-10-26）：** 2 项端到端测试写好即通过：接受 `timeout` 的校验在 Task 2 实现（当时单元测试先红），续跑提示词加时间预算段在 Task 3 实现。如实记录：这两项没有单独的红阶段。

**Task 7（2026-10-26）：** `test-interface.py` 改为期望 1.2 后先红（1 失败 1 错误），升级 `interface.json` 后通过。

**Checkpoint 2（report，2026-10-26）：**
- 偏离 Plan：总验证的套件列表是写死的，没包含新测试。在 `scripts/validate.sh` 的列表与 `scripts/tests/test-validation-discovery.py` 的夹具清单各加 `run-timeout`（与 run-resume 当初的做法相同）；只加不改。
- `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：`validate: ok`，其中 `test-run-timeout.py` 26 项 OK
- `claude plugin validate .`、`claude plugin validate ./plugins/delegate`：均 Validation passed
- `git diff --check`：通过

**Task 8（2026-10-26）：** 中文、英文 README，`run.md`、`help.md`，以及中英文待发行说明都已更新，包括开放集合说明和「先看退出码 0、再看 `status=done`」的升级提示。`test-command-migration.py` 要求命令文件渲染后不超过 4000 字节：初稿 `run.md` 为 4229、`help.md` 为 4010，都超了，压缩措辞后通过。

**Task 9（2026-10-26）：** 三份合同（run-resume、channel、integration-interface）及各自的英文页都已加上指向句。run-resume 新增修订记录 R3，附用户原话，并按 R3 修订了 Always 规则、A3、RR-01 和拒绝表中 `run not waiting for input` 那一行。`verify-artifacts` 结果：4 通过、2 警告、0 失败。两条警告是 run-resume 和 integration-interface 在批准后被修订，需要用户复审，复审后重新记录批准标记。channel 没有批准标记。

**Task 1–9 之后的全量验证（2026-10-26）：**
- `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：`validate: ok`
- `claude plugin validate .`、`claude plugin validate ./plugins/delegate`：均 Validation passed
- `git diff --check`：通过
- 下一步：Checkpoint 3（gate，付费实测）需要单独授权；run-resume、integration-interface 的修订需要用户复审。

**与 S36 的文件冲突（2026-10-26，delegate-owner 转达）：** S36（`--write` 不再写入项目信任）由用户选定修改行为，另开会话实现，会改 `plugins/delegate/scripts/codex-exec.sh` 和 README。本模块已经改了这两处：
- `codex-exec.sh`：期限分配、时间预算段、超时分支里的收尾轮和兜底、写模式 `.baseline` 快照、清理后缀；
- `plugins/delegate/README.md` / `README.en.md`：可续跑委托一节和对外接口一节。

两边合并的先后顺序由 delegate-owner 协调。本会话不碰 S36。

**合同修订复审（2026-10-26）：** 用户原话「批准 run-resume 和 integration-interface 的修订。」已重新记录两份 Spec 的批准标记。

**Checkpoint 3（2026-10-26，gate，付费实测）：** 用户授权原话「授权 Checkpoint 3 按计划实测，14 次，最多 18 次付费调用；测后删掉 Codex 自动加的那条 trust 记录。」实际发起 13 次请求，其中 12 次真实模型调用，1 次因模型不可用返回 400。记录见 [docs/verification/2026-10-26-delegate-run-timeout-cp3.md](../../docs/verification/2026-10-26-delegate-run-timeout-cp3.md)。
- H1 成立：真实 540 秒期限下，模型在 412 秒主动停下，wrapper 总耗时 422.2 秒，22 个口令全部正确。
- H2 部分不成立：收尾轮 8 个样本中有 2 个超过 45 秒，「长尾不常见」的判断不成立；硬期限和兜底仍然生效。按 Plan 回到规格，交用户决定。
- H3 未验证：Codex 会截断大的命令输出，上下文停在约 3.2 万 token。另外，「强制中止 → 收尾轮」这条路径第一次在真实环境里跑通了（H3 主运行首轮约 145 秒没有响应）。
- H4 成立：`gpt-5.6-terra` 在 72.1 秒主动停下。
- H5 成立：续跑时没有提示「先看文件」，也没有重复写入。
- 新发现：长命令运行期间模型也能查看用时并停下，S35 前置实测里「单条长命令时做法 (b) 拦不住」的推断不成立。
- 善后：测试前 `~/.codex/config.toml` 的 sha256 为 `c84d6a4b…`。H5 写模式运行后 Codex 追加了一条 trust 记录，已只删这一条，sha256 恢复为测试前的值。两个临时仓库还在，删除前先问用户。

**规格修订 R1（2026-10-26）：** 用户原话「选 A：常数不变，只修订规格 H2、H3 的措辞并记录新发现。」中英文规格据此修订 H2、H3，补充新发现和各项实测结果，并按实现补正两处文字（清理列表加上 `.baseline`；测试用自带的假 codex）。

**Checkpoint 4（2026-10-26，gate，交付验收）：** 用户原话「批准」，同时批准修订后的 Spec，已重新记录 Spec 的批准标记。本次授权在本分支本地提交一次，并按交审正文里的原文回告 delegate-owner；推送、PR、版本号与发版另行授权。
<!-- spec-guard: external-review declined -->
