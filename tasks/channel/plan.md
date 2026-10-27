# 当前维护计划：channel

日期：2026-10-08。范围：既有合同的项目约定接入与维护核对；没有新增产品实现任务。
规格：[spec/channel.md](../../spec/channel.md)。任务：[todo.md](todo.md)。
本轮接入方案经用户确认；这不是对早期模块 Spec/Plan 或检查点的追认。

## 核对顺序

1. 核对当前规格、能力图中的职责/依赖和双语路径；不修改产品合同。
2. 验证接入前本模块 plan/todo 的归档 SHA-256 与基准 Git 内容一致。
3. 运行本轮统一验证；本模块的确定性验证结果与证据记录在 todo。

## Checkpoint 1（report）：当前维护基线

核对通过后只勾选本轮实际完成项，记录命令、结果和未验证项，并在授权范围内继续。
当前清单 `DONE` 只表示本轮核对没有剩余 task，不表示历史验收、人工批准或远端交付已完成。

## 历史记录与未知事实

[归档索引](../../docs/archive/pre-spec-guard/README.md) 保留原始计划和任务，勾选与内容不变。
本模块历史批准原话、当时插件版本和 gate 确认仍未核实。没有重新执行付费模型或完整交互验收。
新需求或修复应另写明确任务及前置计划，不能重新执行归档清单。

## 内容补全计划（2026-10-08）

本轮授权来源：用户对已列明前三项修复回复“继续推进”。该授权覆盖文档补全，不代表历史 Spec/Plan 审批。旧维护核对 1–3 已完成，新增 4–6 单独追踪。

### 工具与实施顺序

Python 3、Git、rg 和启用的 Spec Guard 0.52.3 hooks 已可用。只编辑文档；不新增产品能力或 UI，不运行付费验证。
模块顺序：channel → detection → routing。模块内 Task 4 → 5 → 6 串行；引用既有离线结果时标明是沿用，不伪造新运行。

### Task 4：补全双语规格的开发约束

**描述：** 补技术栈、目录职责、真实代码风格示例、三级边界和明确成功条件，保留原行为合同。
**验收条件：** 六个核心领域可定位；中英文命令/示例/编号一致；新内容不改变参数、退出状态或授权语义。
**验证：** 定向检查两版标题和命令，逐字比对代码片段与引用源文件，确认原合同正文仍在。
**依赖：** 首轮维护核对 1–3。
**涉及文件：** `spec/channel.md`、`docs/en/SPEC-channel.md`。
**预计规模：** S，2 文件。

### Task 5：建立条款与验证映射

**描述：** 将本模块 CH 条款逐条映射到已有源码、测试和当前验证边界，明确部分覆盖。
**验收条件：** 所有条款编号有对应行；测试路径/用例存在；桩覆盖与真实行为、历史审批分开；本计划任务字段完整。
**验证：** 阅读对应测试断言和源代码，核对 [合同验证映射](../../docs/verification/2026-10-08-contract-matrix.md) 中本模块行与 Spec 编号一致。
**依赖：** Task 4。
**涉及文件：** 本 `plan.md`、`docs/verification/2026-10-08-contract-matrix.md`。
**预计规模：** S，2 文件。

### Checkpoint 2（report）：规格和映射完成

Task 4–5 完成后，在 todo 各项下记录实际文档检查和仍未验证的条款，已有授权内继续。

### Task 6：维护任务验收与证据归位

**描述：** 核对本模块规格、计划、任务字段及验证引用，记录本次内容核对结果。
**验收条件：** 每项有独立验收/验证/依赖/文件字段；Spec 的产品成功条件可追踪到映射；只有实际完成的本轮事项被勾选。
**验证：** 文档字段和链接检查、Spec Guard 产物/阶段核验；源码与基准比较，归档哈希不变。测试结果引用首轮接入实际运行，不重复宣称执行。
**依赖：** Task 5。
**涉及文件：** 本模块 `todo.md`；统一结果在行政报告 Task 7 汇总。
**预计规模：** S，1 文件。

### Checkpoint 3（report）：本模块内容核对

记录结果和缺口后进入已授权的下一个模块文档切片。产品验收的未测条件不是本次文档 task，不因 phase DONE 被关闭。三个模块最终 diff 由行政计划的 gate 交给用户审阅。

### 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 补格式时改变既有合同 | 行为说明失真 | 旧正文完整保留，只加开发约束和条款索引 |
| 总测试通过被当成每条充分覆盖 | 假阳性验收 | 映射写清部分覆盖/源码依据/待验证 |
| 当前记录被误当历史审批 | 流程证据失真 | 保留历史原文，增补日期和授权对象明确 |

### 开放事项

本模块旧任务逐项状态、旧审批、真实交互及远端交付仍未核实。此计划只补齐文档及验证追踪，不重写早期实施历史。

## Task 7：本模块历史裁决与免费定向补验（2026-10-08）

**描述：** 将本模块归档未勾项逐项归类到当前证据/合同替代/待验证，并引用本批免费离线定向结果；不修改历史原文或产品实现。
**验收条件：** 本模块原条目全部有精确来源和依据；未知历史完成/批准保留；临时夹具结果与永久回归分开。
**验证：** 归档文本及行号逐项匹配，证据路径/哈希检查；免费定向脚本结果和当前产品范围比较；共享汇总见行政 Task 8–9。
**依赖：** 内容补全 Task 4–6。
**涉及文件：** 本模块 todo；共享裁决及定向验证文件由行政 Task 8–9 隔离为各最多 3 文件的切片。
**预计规模：** S，本模块 1 文件。

### Checkpoint 4（report）：本模块证据收束

实际证据明确后记录并继续已授权范围；遇到产品缺陷/旧批准证据缺失只分类，不擅改实现或填批准。

## Task 8：免费反向证据及本模块裁决更新（2026-10-08）

**描述：** 对本模块待验证的反向条件在临时产品副本执行受控变异；探测另核对业务目录零足迹；引用实际结果更新文档，不修改产品或历史档案。
**验收条件：** 无变异与还原通过，故意错误由指定断言抓住；失败或未知如实保留，历史批准不升级。
**验证：** 行号/完整原文/证据哈希、定向正常/变异/还原日志及产品范围核对；汇总由行政 Task 10–11 保存。
**依赖：** 本模块 Task 7。
**涉及文件：** 本模块 todo（1 份）；共享证据与裁决按行政切片处理，每片最多 3 文件。
**预计规模：** S。

### Checkpoint 5（report）：反向证据分类

结果明确后记录本模块实际覆盖与限制；当前目录为文档维护，真实宿主及历史人工批准保持未验证。

## Task 9：当前通道 live 样本（2026-10-08）

**描述：** 按行政 Task 15 的具体批准运行既有 --live 入口，仅一次真实只读 Codex 调用，使用临时 Git 夹具。
**验收条件：** 入口退出 0、真实答复非空；跳过、环境失败或执行失败分别记录，不补造历史批准。
**验证：** 本地基础条件与源码哈希；/bin/bash plugins/delegate/tests/test-channel.sh --live 的脱敏输出、状态及哈希；产品源码不变。
**依赖：** F8 验证完成及用户对具体三次 CLI 有限批次的“继续推进”。
**涉及文件：** 本模块 todo；共享 live 证据由行政 Task 15 保存。
**预计规模：** S，无实现修改。

### Checkpoint 6（report）：通道 live 分类

结果明确后记入 todo；不自动重试或升级到写模式，失败先报告分类。

## Task 10：当前 Bash 决定及已安装斜杠命令验收（2026-10-08）

**描述：** 记录当前已批准工具取舍，在原生 user-scope 会话执行一次真实只读委托。
**验收条件：** 旧窄范围不冒充满足；当前决定有独立 ADR；命令实际解析、wrapper 成功、真实答复非空且业务文件快照不变。
**验证：** 原生 TTY/JSONL/trace、唯一 read-only exec 日志、answer/log 哈希和夹具快照。
**依赖：** Task 9；行政 Checkpoint 11 一次批准。
**涉及文件：** 本模块 plan/todo；共享批次 JSON/Markdown；channel 另引用双语 ADR。
**预计规模：** S/M，仅临时验收与文档，不改运行时。

### Checkpoint 6（report）：整批证据收束

遵守整批四个 Claude 会话/最多一个 Codex exec 上限；结果缺证不自动追加调用。完成记录不回填历史批准。

## S41：中止时回收后代进程组（v0.7.1 补丁，2026-10-27）

**来源：** ecosystem-lead 处的 S41，用户原话：「S41 先单独出 delegate 0.7.1：只修中止时回收后代进程组、最后的 wait 加上限、清理结果如实报告，用假端点做回归测试；1.3 在它之上做。」本会话中用户确认假设 A1–A10 与合同条款清单，A5 用 125。合同见 [spec/channel.md](../../spec/channel.md) 修订 S41、CH-03、CH-06、CH-07。
**批准：** 2026-10-27 用户在本会话回复「Spec 修订和 Plan 批准，开始 Task 11。」
**范围：** 只改 `run_codex.py`、`codex-exec.sh`、测试与文档。接口 1.2、`--timeout`、540 秒期限、结果行、stdout、状态文件、review 进程管理都不动。

### 实施顺序与检查点

Task 11 → Checkpoint 7（report）→ Task 12 → Task 13 → Task 14 → Task 15 → Checkpoint 8（gate）。

### Task 11：回归测试（先红）

**描述：** `test-channel-regressions.py` 新增：
- 假 codex 的 `setsid_child` 模式：用 `start_new_session=True` 起子进程，3 秒后写标记；测到期（124）和 wrapper 收到 TERM/INT/HUP 各一次。断言子进程不在、标记没写出、stderr 含清理报告（后代 PID、`无残留`）。
- `stop_group` 单元测试：注入 `wait` 永远超时的进程，断言有界返回、输出 `执行进程未能回收，PID=…`、`main` 返回 125。
- wrapper `finish` 有界：把脚本复制到临时目录，换成忽略 TERM 的 `run_codex.py`，断言 wrapper 在约 17 秒内非零退出，stderr 报告强制结束与 PID。

新增 `test-reap-fake-endpoint.py`：本机假 Responses 端点（取自 S38 实测记录附件，不收凭据）、临时 `CODEX_HOME`，真实 Codex 执行长 `sleep` 时对 `run_codex.py` 分别触发到期、TERM、INT、HUP。断言 `sleep` 和 `zsh -lc` 都不在、`run_codex.py` 在上限内退出。找不到 `codex` 时跳过。注册进 `scripts/validate.sh`。
**验收条件：** 实现前新断言全部红，失败原因与缺陷一致（残留、挂住或无报告）；旧断言不改。
**验证：** `python3 -B plugins/delegate/tests/test-channel-regressions.py`、`python3 -B plugins/delegate/tests/test-reap-fake-endpoint.py`。
**依赖：** 无。**涉及文件：** 两个测试文件、`scripts/validate.sh`。**规模：** M（3 文件）。

### Checkpoint 7（report）：红灯记录

把红灯的命令、失败断言和原因记入 todo 后继续。

### Task 12：`run_codex.py` 回收后代、有界等待与报告

**描述：** 按合同五步重写 `stop_group` 的中止路径；新增可选 `--report <路径>`，中止时追加写清理报告；最终 `wait` 5 秒上限，超时输出未能回收行并让 `main` 返回 125。所有 `killpg` 继续容忍 `ProcessLookupError` 与 `PermissionError`。正常退出路径保持原有行为。
**验收条件：** Task 11 中 `run_codex.py` 相关的断言转绿；EPERM 两条旧回归仍绿。
**验证：** 同 Task 11 两条命令。
**依赖：** Task 11。**涉及文件：** `plugins/delegate/scripts/run_codex.py`。**规模：** S（1 文件）。

### Task 13：`codex-exec.sh` 转发报告与 `finish` 有界

**描述：** 两处 `run_codex.py` 调用都传 `--report <runId>.cleanup`；`finish` 对执行进程 TERM，轮询 15 秒，KILL，再轮询 2 秒，如实报告并非零退出；`finish` 把非空的 `.cleanup` 转发到 stderr；保留清理列表加 `.cleanup` 后缀。
**验收条件：** Task 11 全部转绿；现有 channel、run-resume、run-timeout 套件不变绿。
**验证：** `/bin/bash plugins/delegate/tests/test-channel.sh`、`python3 -B plugins/delegate/tests/test-channel-regressions.py`、`python3 -B plugins/delegate/tests/test-run-timeout.py`、`python3 -B plugins/delegate/tests/test-run-resume.py`。
**依赖：** Task 12。**涉及文件：** `plugins/delegate/scripts/codex-exec.sh`。**规模：** S（1 文件）。

### Task 14：文档同步

**描述：** `DESIGN.md` 与 `docs/en/DESIGN.md` 的清理描述；`README.md`／`README.en.md` 的清理描述、退出码表加 125、回归套件数；`plugins/delegate/commands/run.md` 的清理句；`docs/releases/unreleased.md` 与英文页写影响面；`CONTRIBUTING*.md` 若列套件数则同步。
**验收条件：** 中英文一致，没有残留「detached 后代不在保证」类的旧说法（Codex 正常结束后留下的进程除外）。
**验证：** `rg -n 'detach|脱离' README* DESIGN.md docs/en/DESIGN.md plugins/delegate/commands spec/channel.md docs/en/SPEC-channel.md`。
**依赖：** Task 13。**涉及文件：** 约 8 个文档。**规模：** M。

### Task 15：全量免费验证

**描述：** 跑总验证与两项 plugin validate、`git diff --check`；`~/.codex/config.toml` 前后 sha256 对照；确认测试后无残留 `sleep`／假端点进程。
**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`、`git diff --check`。
**依赖：** Task 14。**涉及文件：** 本模块 todo。**规模：** S。

### Checkpoint 8（gate）：交审

把实际 diff、红绿记录和未验证项交用户审。版本号 0.7.1、`v0.7.1` 版本说明、提交、推送和 PR 分别单独询问。

### 风险与缓解

- **冻结后 Codex 的会话没写完，收尾轮续跑不了：** 仍先给 Codex TERM、再 CONT，保留它原来的优雅退出（修订 R1 后 TERM 紧跟在后代组 TERM 之后）；run-timeout 套件守住收尾轮流程。
- **PID 复用误杀：** 只对快照里 pgid 不变、仍在世的后代组发信号，排除自身组和 pgid≤1；窗口只有几秒，写进合同的保证范围之外。
- **Linux 无 `ps`：** 优先读 `/proc`。Linux 上未实测，列为未验证项。
- **真实 Codex 测试依赖本机版本与启动耗时：** 无 codex 时跳过，等待以进程出现为准，不靠固定延时。

### 未验证项（预先列明）

- Linux 实机；写模式（`workspace-write`）下的回收；T5b 那次 60 秒挂住的真实根因（真实 provider 与推理流，需要付费调用）；`sandbox-exec` 包装下的父子关系以本机实测为准。
