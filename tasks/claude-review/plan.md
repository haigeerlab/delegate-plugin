# 实现计划：claude-review

日期：2026-10-09。规格：[claude-review](../../spec/claude-review.md)；结果：[todo](todo.md)；决定：[ADR-002](../../docs/decisions/ADR-002-claude-review-isolation.md)。

## 当前接续：流程核对修订（2026-10-13）

位置：`/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。activeModule 为 claude-review，阶段 BUILDING；最新完成 Task9h/9i/9j 三批Required修复，免费总148/53/19通过；Checkpoint3当前源码部分成果已接受；剩余 Task2、Task6、Task8完整安全条件，Task9k两宿主安装同步已通过，后续修复未真实模型复验或本批重载；剩余完整安全补证按具体授权推进。本节是当前导航，其余日期段落保留历史批准、失败和当时停点，不重新生效。

1. **Task2 剩余补证：** 整理实际 OS 边界、原版认证和模型工具事件的证据层次。已有无模型/普通模型结果直接引用；未验证的刷新/主动工具行为保持未完。模型相关安全项交 Task8 的同一具体批次验收，不重复启动。
2. **Task6 补证：** 核对真实 CLI 异常/helper 的直接证据。免费合成生命周期套与普通原版正常回收已通过；缺少原版异常或自然 helper 时明确未验证，不把合成故障注入冒充自然行为，也不强制认证失效或改凭据。
3. **Task8 补证：** 新命令的宿主交互显示/实际调用与主动越权尝试，按两方向分别记录。新增付费或跨会话步骤使用具体批次 gate；先完成免费准备再请求一次对应授权。没有尝试事件则未观察，不无限重试。
4. **Checkpoint3（gate）：** 用户审阅最终 diff 和未验证限制。若前述验收仍有缺口，只能审阅部分成果和遗留条件，不勾完整完成，不自动 Git 交付。

本轮免费整理为 report：同步已预览的两宿主约定、任务导航、当前交付事实，运行 Spec Guard 阶段/产物、链接和 diff 检查后直接继续；不安装更新插件、不改全局设置、不新建事项、不调用模型。已通过且实现未变的产品测试不重复运行。验证与限制记入[流程核对记录](../../docs/verification/2026-10-13-spec-guard-workflow-check.md)。

### 剩余真实验收检查点（gate，2026-10-13，已批准）

免费核对已收束；不再围绕相同配置摘要无期限扫描。上一批三个job均不存在；无CLI被动观察20.13秒无变化，先前写入归属仍未知。已准备[集中双向批次](../../docs/verification/2026-10-13-delegate-remaining-acceptance-plan.md)：固定61文件和4文件合成范围、已有CLI/内核宿主身份、一方向一次的执行保护，两后端dry-run及驱动preflight通过。拟新增正向一次、通过后向既有“Claude验收会话”交接一次并反向一次；付费和委托授权尚未取得，不执行或发送。实际事件缺失仍未验证，不能保证一次调用补齐主动越权/刷新/helper。批次参数、费用口径和停止条件均以该具体方案为准；这不是设计或安装的再次确认。

实际批准：用户“批准这批双向验收”。正向一次已完成，唯一反向交接291已被读取，待对账；上段未批准是准备时状态，已有本批授权不重复索取。若反向自身授权不足或结果未知，保留未执行/未知，不重新发送或从Codex代跑。

最新结果：两向均一次完成相同4文件审查，正向10.930秒、反向19.641秒；输入/Git/被观察配置不变、各自清理confirmed。Codex四入口显示已由用户确认。Claude目标报告旧加载清单缺review/run，下一步按官方普通`/reload-plugins`由用户重载并确认显示，不自动安装、强制重载或追加后端模型。完整主动工具/刷新/helper验收和Checkpoint3保持未完；本批模型额度已消费。

### Checkpoint 2b（gate）：仅刷新Claude正常delegate安装（UI-001，后续批次完成）

用户执行普通重载后澄清未实际注意到四入口，并明确授权电脑查看。已用专用工具直接观察“Claude验收会话”：仍是旧delegate/doctor/help及routing，插件详情3命令/2Hook；旧安装缓存与新4命令/1Hook源码不一致。不能保留此前Claude显示通过；Codex独立确认不变。

已完成免费只读帮助/安装登记核对，准备[修复范围](../../docs/verification/2026-10-13-delegate-claude-desktop-entry-mismatch.md)：固定CLI2.1.295、本地61文件，备份仅delegate；官方user scope update一次，成功却明确仍旧内容时才按预先批准分支uninstall --keep-data/install各一次；OS禁网，不更新其他插件或CLI，不手改缓存、不改认证/env，不调用模型、不提交发布。错误/未知停止，保留可能部分状态；之后普通重载并直接核对入口。此正常Claude刷新没有被此前Codex安装或模型批次授权，尚未执行。UI-001是既有Task8的Required缺口，不是扩展后端或重新设计。

## 本批双后端接口整理（2026-10-10）

用户在审阅 review/run、范围快捷参数、dry-run、共享能力说明与统一结果的建议后回复“继续”，确认本批设计与实现范围。开发位置 delegate-plugin / codex/spec-guard-conventions-public；不包含真实模型、依赖安装、插件安装、提交、推送或发布。按以下切片执行并记录，不重新申请已有实施授权。

1. Task 9a：单一双后端能力定义和 review/run CLI 分派；run 保留旧 Codex 行为，拒绝 Claude run。涉及 capabilities、CLI、公共 shell、backend 和 CLI 测试；验证非法参数/跨后端/run 写入与旧调用兼容。
2. Task 9b：范围快捷参数→既有上下文采集；review --dry-run 不启动执行器、不写产物。涉及 CLI、context、backend 和 CLI/上下文测试；验证固定 diff、paths/module、排除、Spec/Plan、未提交改动、空范围/非法组合和不泄漏文件内容。
3. Task 9c：斜杠命令改为 review/run/doctor/help，更新路由、清单、双语规格/帮助和迁移说明。只有源命令替换，不修改宿主生成缓存。验证命令一致性、能力说明和两项原生清单。
4. Task 9d：完整免费验证、文档链接与 diff 检查，记录结果及限制。行为变更先红后绿；不将新入口桩测试追认成真实宿主使用体验。

检查点（report）：每片测试通过后继续下一片。最终检查点（gate）：展示实际变更与免费证据；真实双向/越权验收、安装与发布仍须各自授权。旧反向夹具固定源码摘要在本批修改后失效；不自动更新其已批准预览或发起模型。

输入规则：新 review 默认 codex、永远只读；--paths 可重复且以仓库根为基准，--module 需 paths。--base/--head 固定提交 diff（head 默认 HEAD），--changes staged|unstaged|working-tree 明确工作区 diff；两种 diff 互斥。无 paths 的 diff 仅采集该比较的变更文件，不扩展全项目；空比较不启动模型。纯 paths/module 默认读取 HEAD 的指定范围，排除未提交内容并展示存在的改动；--changes 显式选择工作区版本时保留 paths/module 类型。只有 working-tree 可加 --include-untracked。--exclude/--spec/--plan/--criterion 可重复；高级 --context 与快捷范围参数互斥。--dry-run 输出 JSON 预览（类型明确，非审查结论），仅含范围/摘要/缺口/权限及模型请求，不含源码/diff正文，不创建快照/日志/报告。

不建立通用调度/后端注册框架，不扩认证方式、不自动选择相反宿主、不静默 fallback。旧 codex-exec.sh 和旧 delegate-exec.sh 无子命令调用继续有效；删除重复命名的源斜杠 delegate 命令，迁移到 run/review。

## 当前分层验收执行约定（2026-10-14）

用户明确“批准分层验收修订”，仅授权已展示的CR-03/06/09和Task2/6/8证据分层、双语文档与免费检查；生产权限/工具/测试断言不改，不补历史整份Spec/Plan批准标记。原初task描述保留，当前成功判据按如下批准切片解释：

1. Task2按同一生产OS策略实际拒写/专用临时可写、原版只读工具初始化、真实范围外Read拒权分别核对；模型主动Write/递归及认证刷新独立标未验证。
2. Task6按Mac内核归属、实际超时/信号、detached/double-fork/父先退和无关进程存活、原日志/失败状态合同验收；历史设置变化与根因、自然helper及长期稳定性保留限制，不由合成进程或短采样证明。
3. Task8分开接受S2版本固定的真实双向普通审查和S7菜单到公共脚本/预览证据；不称最新诊断源码已重新双向live，原自动输入失败/并发提交不改写为无差错UI通过。
4. 逐项证据满足才勾任务，未满足仍保留；下一gate为Checkpoint5最终实际diff及限制人工审阅，不包含新的模型、安装、认证、通信或Git交付。

## 批准、基准与执行顺序

用户审阅源码核对、官方接口调研、设计、实现计划及推荐取舍后回复“继续”。本计划据此实施 CLI、显式后端、受控快照、整个进程隔离、Claude 首版拒绝 effort、macOS 首验。批准不包含依赖安装、付费 live、其他执行器委托、提交、推送、发布或外部写入；遇到这些条件单独取得具体授权。
基准：分支 `codex/spec-guard-conventions-public`，HEAD `823c42383cf055ea8af99256618daf6212d10735`。只做本能力所需修改；旧模块 todo 和归档不重写。未启用 Local 事项账本。
顺序：Task 1a–1c 文档 → Task 2 实际隔离 → **Checkpoint 1** → Task 3a–3b 分派/预检 → Task 4a–4b 上下文 → Task 5a–5b 结果/执行 → Task 6 生命周期/日志 → Task 7a–7d 入口/双语/验证 → **Checkpoint 2** → 经独立授权 Task 8 两宿主 live → **Checkpoint 3**。
每片先写失败测试，再实现和复验；不通过时保留证据并修复，不降低合同。列出的产品文件均位于 `plugins/delegate/`，仓库行政文件写全路径。新增脚本名称可按实际最小实现调整职责，不引入第三后端或通用调度层。

## 工具与可用性

已有 Bash、Python 3、Git、rg、Node 22.22.0、npm 10.9.4、Claude 2.1.295、Codex 0.160.1，以及当前启用 Spec Guard 的只读产物/阶段工具。Python 用 `-B`，shell 测试用 `/bin/bash`。不要用安装缓存实施产品修改。
设计阶段 srt 未安装。官方注册表已只读核实 0.0.79 发布且要求 Node >=22.12.0；不等于运行可用。用户随后对具体安装请求回复“继续”，当前已在专用 `/private/tmp` 安装该版本；实际证据见 todo。默认工具沙箱内 `sandbox-exec` 最小探针报 `Operation not permitted`，不能据此判定宿主 OS 无法隔离。实际 OS 夹具通过工具审批在外层沙箱之外运行，仅使用临时合成资源。
安装命令的有效形式如下；user/global 必须使用不同文件，不能同指 /dev/null。实际依赖树和路径已记录：

```bash
review_tools_dir="$(mktemp -d /path/to/private-evidence)" || exit 1
cd "$review_tools_dir" || exit 1
: > "$review_tools_dir/user.npmrc"
: > "$review_tools_dir/global.npmrc"
npm install --prefix "$review_tools_dir" --cache "$review_tools_dir/npm-cache" --userconfig "$review_tools_dir/user.npmrc" --globalconfig "$review_tools_dir/global.npmrc" --registry https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --package-lock=false @anthropic-ai/sandbox-runtime@0.0.79 || exit 1
```

UI 无新增页面。原生命令/技能入口通过免费静态对齐检查；真实原生主会话另经 live 授权，记录宿主和启动证据，不能用 CLI 桩或 Hook smoke 代替。主会话可信标识不可得时报告未知。

## 任务切片

### Task 1a：双语规格与架构决定

**描述：** 将已确认设计落为未来实施合同，明确当前尚未实现。
**验收：** 参数、权限、状态、范围、CR-01–10 和未验证条件双语一致；批准范围与历史事实分开。
**验证：** 逐项比较选项/字段/编号/命令；检查引用；所有官方判断有来源。
**依赖：** 用户“继续”。**文件：** `spec/claude-review.md`、`docs/en/SPEC-claude-review.md`、中英文 ADR-002（4 文件）。**规模：** M。

### Task 1b：能力图与导航

**描述：** 登记新模块及依赖，激活本模块，保持原三模块行为说明。
**验收：** 两版能力图顺序 channel→detection→routing→claude-review；索引标为未实施；无根目录 spec 漂移。
**验证：** 严格能力图、链接、state JSON 检查。
**依赖：** Task 1a。**文件：** `spec/CAPABILITY-MAP.md`、`docs/en/capability-map.md`、`docs/README.md`、`docs/en/README.md`、`.agent/state.json`（5 文件）。**规模：** S。

### Task 1c：计划、实际证据与隔离前置条件

**描述：** 保存本计划/清单及当前源码、接口、工具和免费结果，留下未完任务。
**验收：** 逐任务字段齐备；批准、未验证和阻塞分开；不将候选方案记为实现。
**验证：** diff 空白、文档链接/双语合同、Spec Guard 产物和阶段核验。
**依赖：** Task 1a–1b。**文件：** 本模块 plan/todo（2 文件）。**规模：** S。

### Task 2：无模型的实际隔离可行性

**描述：** 在临时 Git/配置/日志夹具验证候选 srt，先证明权限边界和进程清理，不接真实认证或模型。
**验收：** 源码/Git/config/快照写入、链接逃逸及默认额外可写路径均实际被拒；专用 temp 可写；范围外读与网络按策略被拒；仅许可端点可用；正常/超时/取消以及 detached helpers 可核实回收。确认 CLI 自身需要写入的路径可重定向；凭据内容无需读取。失败不得回退无隔离。
**验证：** `python3 -B plugins/delegate/tests/test-claude-isolation.py`，测试自身创建和删除临时资源；每个拒绝同时检查进程状态及目标内容；生命周期测 PID/归属/最终存活而非仅检查父退出。先验证实际 srt 版本/策略，不依赖 main 分支印象。
**依赖：** Task 1、用户提供 srt 或单独批准专用临时安装。**文件：** `scripts/review_isolation.py`、`tests/test-claude-isolation.py`、`tests/test-review-lifecycle.py`（最多 3 文件）。**规模：** M。

### Checkpoint 1（gate）：隔离与运行前置

缺 srt 时在 Task 1 后停下，先请用户批准具体临时依赖安装或提供现有路径；不重复请求设计批准。Task 2 通过后报告 OS/runtime 版本、权限/网络/清理证据和认证兼容限制，确认后才进入调用通道实现。无法满足 CR-03/06 时呈现具体替代设计，不能自行减少边界。此 gate 不授权真实模型。

2026-10-09 当前状态：临时安装与文件/本地代理边界已验证，独立会话子进程的正常/超时/取消清理三项失败；未通过 gate，Task 3 不启动。详见[实际证据](../../docs/verification/2026-10-09-claude-review.md)。Task 2 的行政收束分为证据/todo（2 文件）和双语 spec/ADR 状态/本计划（5 文件），只记事实，不修改已批准的参数或削弱条款。
用户先对只读评估、随后对专用 VM 修订分别回复“继续”，当前 [ADR-003](../../docs/decisions/ADR-003-review-process-boundary.md) 已接受设计与免费实施范围：Mac 主会话使用专用 Linux guest，原版 Claude CLI+srt 的外围进程纳入单次 transient service/cgroup，guest 独立认证、无 host 文件共享。该修订替代原生 Mac 首验，未授权新运行时安装、登录或模型。R1 合同同步完成；R2/R3 的离线基础实现已验证，真实 Linux/VM 与传输控制尚未完成，不进入 Task 3。ps 仅用于本次夹具存活证据，不作为发现全部后代的归属机制。

### Task 2 修订切片（继承 ADR-003 的批准）

- **R1：** 双语 claude-review spec、ADR-002 两版及本计划（5 文件）；同步平台/认证/结果/进程边界，保留原批准和失败历史。验收为链接、参数/状态对齐和 diff 检查；本轮完成。
- **R2：** `scripts/review_service.py` 与 `tests/test-review-service.py`（2 文件，M）；固定 service 参数、不扩展 argv 变量，校验 unit/cgroup 归属，有界 manager 探针，正常/失败/超时/取消的清理分类。假 manager 与实际 cgroup 验证分开。当前 14 项通过，尚无真实 manager/namespace/seccomp 验收，也未实现实际 unit 启动/权威结束事实保留；unit 已回收缺元数据时失败关闭。
- **R3：** `scripts/review_guest.py` 与 `tests/test-review-guest.py`（2 文件，M）；有限普通文件快照、哈希/编码校验、无链接/路径穿越/文件目录冲突、guest 配置拒绝与专用 lease。当前 11 项通过；VM 启动、配置实际生效、SSH/独立取消/断线期限控制尚未实现或验证。
- **R4（gate）：** 明确批准具体临时依赖后，在专用 VM 继续 R2/R3 的真实运行部分与实际 OS 故障套；source/Git/config 拒写、脱离组 helper/快速 fork、外围 proxy、正常/超时/取消/断线清理全部通过，记录版本和限制，再交 Checkpoint 1 评审。第一步是校验下载摘要和仅本次 LIMA_HOME，再创建一个 VM；缺依赖、摘要不符、权限不够、运行未知或任何边界失败即停，不降级。具体预览见[临时 VM 范围](../../docs/verification/2026-10-09-claude-review-vm-preflight.md)。当前未获安装授权。

### Task 3a：公共入口与兼容分派

**描述：** 增加默认 Codex 的显式后端入口及递归标记，不改旧 read/write 意义。
**验收：** 默认/显式只启动目标后端；未知/混用选项、Claude write/effort 在启动前失败；help 无模型；所有相关入口拒绝嵌套。
**验证：** 先以可记录 argv 的假 CLI 证明失败，再实现；`test-review-backends.py` 及现有 channel 回归。
**依赖：** Checkpoint 1。**文件：** `scripts/delegate-exec.sh`、`scripts/codex-exec.sh`、`tests/test-review-backends.py`、`tests/stub-claude`（4 文件）。**规模：** M。

### Task 3b：Claude 能力和认证预检

**描述：** 校验 CLI/版本/参数/认证安全字段，与 Codex 原检查分开。
**验收：** 缺失、不支持、超时、坏 JSON、未认证准确分类；原 Codex ChatGPT 检查保留；不打印凭据、不自动登录或切认证。
**验证：** 假 CLI 故障注入，测试 sentinel 凭据不出现在任何产物；原 backend 测试全部通过。
**依赖：** Task 3a。**文件：** `scripts/claude_review.py`、`scripts/backend.py`（仅必要兼容）、`tests/test-claude-review.py`（3 文件）。**规模：** M。

### Task 4a：共同上下文与只读 Git 采集

**描述：** 校验版本化输入，固定 diff/module/paths 和未提交改动，不扩大扫描。
**验收：** 非法/未知字段提前拒绝；HEAD/两端 SHA/范围/哈希记录；采集禁用外部程序和 Git 状态写入。
**验证：** 临时 Git 仓库装入恶意 diff/textconv/fsmonitor/hook sentinel，运行后 sentinel 不出现；覆盖 staged/unstaged/untracked/排除及输入变化。
**依赖：** Task 3。**文件：** `scripts/review_context.py`、`tests/test-review-context.py`（2 文件）。**规模：** M。

### Task 4b：快照与两后端等价任务

**描述：** 复制普通文件至受控目录并映射证据，接入 Codex 的可选共同审查模式。
**验收：** 无源链接/真实 .git；资源限制、子模块/二进制/读取失败列未审；变更输入停止；两后端获得同任务和范围；旧 Codex 自由文本不变。
**验证：** 正常与链接逃逸/竞争修改夹具，假 CLI 比较任务上下文而非逐字比对各自 CLI argv。
**依赖：** Task 4a。**文件：** `scripts/review_context.py`、`scripts/delegate-exec.sh`、`scripts/codex-exec.sh`、`tests/test-review-context.py`（4 文件）。**规模：** M。

### Task 5a：结果契约与安全渲染

**描述：** wrapper 独立持有执行身份/状态，校验模型结果、定位/覆盖/用量，分开 answer/report/log。
**验收：** 完成/缺条件/失败/超时/取消与三审查结论准确区分；空/坏/拒权/部分/达限不报无问题；行号核验、身份缺失未知；成本口径不猜测。
**验证：** 受控 terminal result/init/structured_output/permission_denials 夹具；格式正确但定位错误亦不能被证明为真实发现。
**依赖：** Task 4。**文件：** `scripts/review_result.py`、`tests/test-claude-review.py`、`tests/test-review-backends.py`（3 文件）。**规模：** M。

### Task 5b：受限 Claude 调用与 Codex 审查结果

**描述：** 连接隔离、快照、CLI 设置/工具清单验证、流解析和共同报告。
**验收：** Claude 实际 argv 含合同限制，拒绝写入/派活/MCP/网络工具；无裸模式/跳权/恢复/fallback；拒权、预算/轮次耗尽、不完整 stream 明确失败或未完成；Codex 共同模式输出同契约。
**验证：** `test-claude-review.py` 故障注入；首个 result 前系统信息异常时终止；不能把桩通过称为真实 Claude 权限证明。
**依赖：** Task 5a。**文件：** `scripts/claude_review.py`、`scripts/review_isolation.py`、`scripts/codex-exec.sh`、`tests/test-claude-review.py`（4 文件）。**规模：** M。

### Task 6：生命周期、日志和错误

**描述：** 有界清理本次进程/辅助进程，保留原因，限制日志和落盘数据。
**验收：** srt 信号退出 0 仍分类取消；无挂住 pipe/孤儿/跨会话误杀；日志路径/权限/最近 50 组与体积上限通过；凭据和原始敏感 stderr 不落盘。
**验证：** `test-review-lifecycle.py` 注入忽略 TERM、父先退、setsid helpers、持有 pipe、中断启动及超时；同时运行无关 sentinel 进程确保存活；日志/目录回归。
**依赖：** Task 5b。**文件：** `scripts/run_codex.py`、`scripts/claude_review.py`、`scripts/review_result.py`、`tests/test-review-lifecycle.py`、`tests/test-channel-regressions.py`（5 文件）。**规模：** M。

### Checkpoint 2a（report）：实现与故障证据

Task 3–6 完成后把实际命令、失败复现/修复/复验、代码差异和未验证项写入 todo；已授权范围内继续文档入口。需要改变批准的参数或边界时改为 gate。

### Task 7a：宿主命令与路由

**描述：** Claude 命令与 Codex 技能共享入口，路由文案区分主宿主和执行者。
**验收：** 默认 Codex、显式 Claude、限制/未知身份一致；doctor 不安装/登录，不把 Codex 认证失败阻挡显式 Claude；不扩展 Spec Guard 执行器。
**验证：** 命令到脚本调用链与迁移技能来源对齐；静态参数/递归/日志合同检查。
**依赖：** Task 6。**文件：** `commands/delegate.md`、`commands/doctor.md`、`commands/help.md`、`skills/delegate-routing/SKILL.md`、`tests/test-routing.sh`（5 文件）。**规模：** M。

### Task 7b：用户用法与双语同步

**描述：** 记录真实最低版本、可选运行依赖、范围 JSON、错误及权限限制。
**验收：** 中英文安装/使用/配置说明一致；不引导全局配置写入、不声称提高准确率；清楚说明不支持平台与未验收能力。
**验证：** 文档命令与 parser help 对齐；代码示例离线解析；链接检查。
**依赖：** Task 7a。**文件：** 切片 7b-1 为根 `README.md`、`README.en.md`、`DESIGN.md` 和 `docs/en/DESIGN.md`（4 文件）；切片 7b-2 为 `docs/README.md`、`docs/en/README.md`（2 文件）。**规模：** 每片 S/M。

### Task 7c：关联模块合同同步

**描述：** 必要时同步 channel/detection/routing 的受影响合同，不重写历史 todo。
**验收：** 新行为与老默认兼容，语言版本同步；现有检测缓存仍有清晰 Codex 范围。
**验证：** 相关规格条款映射与现有测试定向比对；每个模块分别两文件切片，遇到超范围先停止。
**依赖：** Task 7a。**文件：** 每片 `spec/<module>.md` 与 `docs/en/SPEC-<module>.md`（2 文件）。**规模：** 每片 S。

### Task 7d：离线总验证与记录

**描述：** 将新测试纳入免费入口，更新真实实现状态与验证证据。
**验收：** 免费总套和两项原生清单检查通过；已实现状态只对应已完成项；旧 Codex 模式未破坏。
**验证：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`、`git diff --check`、Spec Guard 产物/阶段；实际权限测试单独列环境，失败/跳过不算通过。
**依赖：** Task 7a–7c。**文件：** `scripts/validate.sh`、本模块 todo、两版 claude-review spec、`docs/verification/2026-10-09-claude-review.md`（5 文件）。**规模：** S/M。

### Checkpoint 2（gate）：真实验收前

展示可审阅实现、免费测试及明确限制，再提议固定 fixture、次数/预算/权限的双向 live 批次。缺认证、隔离或宿主条件保持未验证。未经单独批准不运行真实模型，不自行安装/更新插件或写全局配置。

### Task 8：真实双向宿主验收

**描述：** 获准后分别运行 Codex 主会话→Claude 审查、Claude 主会话→Codex 审查；包括写入诱导和再委托诱导的有限只读审查夹具。
**验收：** 每方向记录宿主/CLI/plugin/runtime 版本、加载源码、实际后端、范围、权限、结果/未审、状态/模型证据；源码/Git/config 前后不变；不将静态/桩/安装 smoke 充当真实验收。
**验证：** 固定夹具哈希、实际启动 argv 的安全字段、原生宿主/终端事件、answer/report/过滤日志及权限拒绝；每个方向独立状态。不无限重试或自动修复。
**依赖：** Checkpoint 2 的具体 live 授权。**文件：** 专用临时夹具、本模块 todo、上项验证报告（仓库 2 文件）。**规模：** M，调用额度单独约定。

### Checkpoint 3（gate）：最终 diff 与交付

整理改动/原因/真实已测与未测/限制/选择后端的用法，展示 diff 等用户审阅。未测能力不勾选；提交、推送、发布各自另授权，不能由本需求推导。

## 风险与缓解、开放问题

| 风险 | 缓解与停止条件 |
|---|---|
| srt 默认可写路径、代理或管理 Hook 破坏边界 | 实际 OS 夹具先证；不能严格限制时 gate，绝不降级 |
| 配置/认证刷新需要全局写入 | 在单次 temp 中验证可行方式，保持源/全局只读；不兼容报告条件不足 |
| 快照缺文件或采集期间变化 | 固定哈希、排除/未审原因；不扩大范围 |
| stream/result 或 CLI 参数随版本改变 | 固定支持基线、能力检查、错误夹具；无最终结果即未完成 |
| detached helper 越出进程组 | 验证本次进程归属和清理；无法保证时 gate，不误杀 |
| 官方登录/订阅政策口径不同 | 原版 CLI 自行认证、不复制凭据；不承诺权益，SDK 留后续 |
| 宿主/模型无法核实 | 明确未知，实际启动后端单独取证 |

开放问题：srt 可验证的网络/auth/provider 策略、管理员配置兼容性及 detached cleanup；这些必须由 Task 2/后续有授权验收回答。第一版不追加 SDK、自动路由或其他平台支持。最终日志体积/快照资源上限等实现常量在测试可证明条件下确定并写入两版文档。


## 2026-10-09 Linux 实测阶段记录

用户批准具体临时 VM 后，R2 已增加真实服务启动及隔离外可信 ExecStopPost 结束事实保留；R3 实际快照传输与独立 SSH 客户端死亡探针完成，产品化控制接口尚未接入；R4 本批次 Linux 15 与 SSH 2 项通过，停止/删除 VM 成功。Linux 需要显式 `/sys`/`/run` 掩蔽与已验证 arm64 的额外 bind/listen 过滤器，新 `review_network.py`、Linux/SSH 守门测试均直接对应原边界要求，不引入额外执行后端。具体失败与修复见[实际记录](../../docs/verification/2026-10-09-claude-review-linux.md)。

上述为上一轮停点。2026-10-10 用户回复“继续快速推进”，接受 Checkpoint 1 的 Linux/SSH 实测结果及所列限制，批准进入 Task 3–7 免费实现。原版 CLI 的启动/写路径/认证条件仍未验证，移交 Task 3/5 的预检与后续单独授权的真实验收，不据此宣称完整后端支持。不重做已确认设计、不重复请求同一安装批准，本阶段不安装或调用模型。公共入口增加薄 Python 参数分派文件，脚本名称按本计划的最小实现调整规则确定。


## 2026-10-10 候选调用链收束

Task 3–7 的已授权免费代码与离线故障验证已接入源码，文件按职责分为公共分派、Claude 适配、共同上下文/结果、Codex 共同审查、Lima 传输、guest 控制与专属 doctor。原 `backend.py` / `run_codex.py` 未重构，旧 Codex 默认保持；没有安装或升级插件。

本轮新增 stdin、初始工具守门和 guest/独立取消整合改变了 service 的实际运行组合，旧 Linux/SSH 固定摘要证明不自动覆盖本轮。Task 2/6 的原版 CLI/当前整合实际条件尚未满足；免费套通过只关闭离线实现项，不能勾选完整安全或双向验收。

Checkpoint 2 的具体预览分两步：先经单独批准准备临时 guest 并安装固定原版 CLI，执行无模型当前整合复验；成功后再请求有认证前提的有限双向模型批次。此次新增安装对象/重建环境不继承已完成并删除的旧批次授权，具体来源/摘要/资源/停止条件见[集成记录](../../docs/verification/2026-10-10-claude-review-integration.md)。不改变已批准的权限或结果合同，不增加后端。


## 2026-10-10 原版 CLI 无模型批次收束

下一批预览已由用户“继续”具体批准并执行：[实际记录](../../docs/verification/2026-10-10-claude-review-guest-cli.md)。当前 guest 整合及原版接口无模型检查已完成，旧安装预览中的“尚未批准/未安装”仅是历史停点。Task 2/6 的模型启动后认证、工具、写路径与 helper 条件仍未验证；SSH 连接超时的精确根因和长期稳定性缺口保留，不降低完整验收标准。Checkpoint 2 仍需已认证专用 guest 与有限双向模型授权；不自行登录、复制宿主凭据或重建已清理环境。


## 最新修订：当前 Mac 本机目标（2026-10-10）

用户明确插件目前仅需当前 Mac 可用；以本机 Claude/Codex CLI 为验收对象，不扩展 Linux/Windows 支持，不再要求用户准备独立 guest。已有 VM 安全边界及测试仅保留历史证据，不代表原生路线通过。当前已核实本机 Claude 2.1.295 和 claude.ai 认证，详情见[无模型探针](../../docs/verification/2026-10-10-claude-review-mac-preflight.md)。

- **M1，Mac 原生边界证明：** 保持 Task 2 的源码/Git/config 拒写、范围外读取拒绝、网络限制和超时/取消/父先退 helper 回收标准。保留原 3 项生命周期红断言，验证候选机制与当前原版认证兼容；不将进程组或 launchd 同组清理说成完整进程树。免费实验文件限专用临时目录；正式证明进入 `test-review-lifecycle.py` 与新的 Mac 测试/控制文件，最多 4 文件切片。验收是所有边界实际通过；不能满足时停在具体证据/取舍，不能默默降级。当前仅完成可行性对照，可靠替代机制尚未选定；禁止所有 fork 的候选已证实不兼容。
- **M2，本机调用接入：** M1 通过后，公共 backend 直接解析本机原版 Claude，复用共同参数、范围快照、结果和脱敏日志，移除 guest 配置作为 Mac 前置。先以假 CLI 证明实际执行路径和错误分类，再接控制文件；每片最多 5 文件，旧 Codex 默认不改。验收是本机指定 Claude 确实启动、无后端混用/自动 fallback，写请求和递归拒绝。
- **M3，免费实际验收与双语同步：** 两宿主来源入口/doctor/说明同步 Mac-only 合同；运行完整免费套和 Mac 实际权限/清理套，报告先前失败的定向复验与限制，不以安装成功代替验收。需同步 spec/ADR 的机制决策时先形成具体方案供评审；没有新的已验证机制前不宣称原生可用。
- **M4，真实双向验收（gate）：** 分别取得有限调用授权，明确每方向一次固定合成范围，使用当前 Mac 的原有认证，记录真实宿主、实际后端、模型/权限/结果和前后不变证据。未授权不调用模型、不替用户登录、不安装升级插件；完成后再交 Checkpoint 3，Git 交付另授权。

此修订接受用户的 Mac-only 范围，不重复要求平台目标确认。技术边界尚未证明，M1 是当前第一步；新的权限削弱、认证方式切换或系统配置动作不由此推导授权。

## 当前阶段收束：Mac 原生代码与免费验证（2026-10-10）

M1 已以新运行器完成本机 13 项实际隔离/生命周期验证；原旧进程组红结果不重写。M2 公共入口、本机依赖、doctor、共同范围/结果及两宿主来源入口已接通，保持旧 Codex 默认。M3 的完整免费总套 53 shell / 111 Python / 19 eval、两项清单检查通过；最终公共 Mac 假 CLI 批次结果见[本机证据](../../docs/verification/2026-10-10-claude-review-mac-native.md)。新增长 TMPDIR 回归先失败后通过，运行/doctor 使用专用短临时目录，不放宽权限。

原版接口可用，但最后认证预检及只读对照返回 authentication_missing；先前认证通过仅是当时事实，不能据此宣称当前本机后端可用。当前阶段为 M3 条件不足收尾、M4 未开始；代码已落盘，真实双向审查未完成。下一步限定定位当前认证在只读边界下不可用的具体原因，不重做设计、不重建 VM、不自动登录或改全局配置；必要的新取舍先列具体证据。认证通过后，再按 Checkpoint 2 展示一次/方向的固定合成项目与预算、权限和停止条件，取得独立 live 授权。Git 提交/推送/发布继续另行处理。

## 最新前置通过与 M4 首批授权预览（2026-10-10）

正常主会话登录状态已获用户确认。当前 PATH 原有 CLI 为 2.1.296，公共 doctor 在未改变的严格策略下通过版本/能力/claude.ai 认证预检；此前 2.1.295 的失败不追认成通过，也不把版本变化猜作根因修复。M3 免费和认证前置已收束，M4 尚未启动模型。

按 Checkpoint 2 分批验证：[首批有限预览](../../docs/verification/2026-10-10-claude-review-mac-live-plan.md)已准备可审阅的 4 文件合成模块和共同上下文。批准对象为当前 Codex 主会话→原版 Claude 的一次运行，sonnet / 8 turns / 180 秒 / 客户端估算预算 1 USD，任何失败停止、不重试或切后端。前后文件/Git/哈希不变、模型和工具实际证据与执行/审查状态分别验收。未授权不执行模型命令。

第一向结果收束后，使用等价固定范围预览并独立批准真实 Claude 主会话→Codex 批次；当前 Codex 主会话中的 Codex 启动不能替它作证。此次只是确定已批准总体计划内的验收切片，不重新请求设计或实现授权；两个 gate 和 Task 2/6/8 仍需实际结果。开发仓库/分支为 delegate-plugin / codex/spec-guard-conventions-public，提交/推送/发布继续另行授权。


## M4 首批实际失败、修复与下一停点（2026-10-10）

首批 gate 已获用户“继续”批准并启动一次真实 Codex→Claude；原版 2.1.296、sonnet 请求、4 文件合成 module 范围，wrapper 退出 1 / 6.557 秒 / failed / inconclusive / cleanup confirmed / tool_boundary_unverified；全部未审，模型和用量未知。输入摘要、HEAD/index/status 保持不变，无自动重试或后端切换。原始流未保留，精确失败原因仍未知。

免费定位发现官方保留的 EndConversation 会被旧严格集合误拒绝；回归先红后绿，修复仅容许 EndConversation/StructuredOutput 控制工具，未知工具仍立即停止。新增固定初始化原因码且不保留原文；12 项结果回归、完整免费总套、实际公共 Mac 假 CLI 6 项/8 场景通过。没有以此勾选真实安全/双向验收，Task 2/6/8 仍按实际证据保留未完成项。

当前为 M4 修复后的有限 live gate：[实际结果与第二批预览](../../docs/verification/2026-10-10-claude-review-mac-live-plan.md#首批实际结果与修复后第二批预览)。具体下一步是在新根核对固定上下文、原版 CLI 和源码摘要后执行一次驱动；仍需针对这新增一次运行的批准，不重复询问设计/免费实现授权。失败即停，不重跑；第一向收束后再准备真实反向宿主批次。无需安装、修改配置、重建 VM、提交或推送。


## M4 第二批失败与原版协议修复（2026-10-10）

用户“批准这一次验收”已单独批准第二批一次真实 Codex→Claude；固定摘要匹配，退出 1 / 3.867 秒 / failed / inconclusive / cleanup confirmed，initial_event_not_init，四文件均未审、模型/用量未知，无自动重跑。全部输入和 Git 状态保持不变。

免费原版空快照/全网络拒绝探针复现 ui_invalidate→init，固定二进制源片段显示 event=ui.render；本机输出协议假设错误已定位。15 项结果回归先红后绿，运行/最终解析共享固定且有界的 read_init，未知/Hook/插件/越权工具仍拒绝。原版修复探针 init 校验通过（Read + StructuredOutput），随后网络禁令下 api_retry，按期限回收；max-turns=0 不防止请求尝试，不能代替 OS 边界。公共 Mac 假 CLI 6 项/8 场景、完整免费总验证通过。

当前检查点为修复后的第三批有限 live gate：[固定预览](../../docs/verification/2026-10-10-claude-review-mac-live-plan.md#第二批结果与第三批批准范围)。下一步核对新根输入/CLI/源码摘要后启动一次公共驱动；尚未授权或排队。仍需针对新增这一次的具体批准，免费修复不重复申请授权。失败即停；Task 2/6/8 和最终 gate 不因 init/假 CLI 通过勾选，真实 Claude 主会话→Codex 仍待独立验收。不安装、修改全局配置、提交或推送。


### M4 第三批收束与第四批 gate（2026-10-10）

第三批一次批准已执行，启动校验成功后覆盖校验失败，cleanup confirmed，未重试；实际证据见 todo。免费输出 schema/安全诊断/失败元数据保存修复及总回归已完成，无新增权限。当前只有第四批具体预览，未获新增模型授权；gate 仍遵守 AGENTS 的付费验证单独批准要求。获批后首步核对固定摘要和合成 Git，再单次公共入口调用；失败即停止，不自动续跑。真实反向宿主另预览/授权，不能用当前 Codex 内直接调用 Codex 代替。


### M4 正向完成与反向准备 gate（2026-10-10）

第四批一次授权已执行并完成有限 Codex→Claude 真实审查，核心发现/输入完整性/正常回收核对通过；前三批失败不追认为通过，主动禁用工具企图等缺口保留。反向预览位于 docs/verification/2026-10-10-claude-review-mac-reverse-plan.md，尚未授权/投递/执行。候选真实 Claude 主会话为“Claude验收会话”；是否联系这个会话和在其自身权限内执行一次 Codex 审查，须人类针对具体目标和付费范围决定。来信不授予接收端新权限；无法满足即停。独立记录真实宿主证据，不以当前 Codex 运行 Codex、目录状态或桥回执代替真实审查。

### M4 反向交接已处理，执行授权不足（2026-10-10）

用户“允许发送给Claude验收会话”批准当前来源的一次联系。单次唯一选路投递后，目标已确认并精确回复缺少本会话付费 Codex/固定驱动的人类授权，未执行且不重试；模型启动 0，输入摘要不变。证据见[反向交接](../../docs/verification/2026-10-10-claude-review-mac-reverse-handoff.json)。Task 8/Checkpoint 2/3 仍未完成。

下一步由用户在已有“Claude验收会话”直接批准已准备的一次固定审查；目标首步核对权限、宿主身份与摘要，再启动 run-once.py。当前来源不重发或替代运行。身份/输入变化、缺权限或任何执行失败即停；有实际结果后核对固定产物和完整性，不重新泛扫或扩大范围。

### Task 9 接口整理收束（report，2026-10-10）

本批 review/run、范围快捷参数、无模型预览、共享能力及入口/双语迁移同步已完成，完整免费验证和实际 Mac 新入口假 CLI 批次通过，证据见 [接口验证](../../docs/verification/2026-10-10-delegate-interface.md)。未进行安装、真实模型、全局配置或 Git 交付。新宿主斜杠体验及原 M4 实际验收缺口保留，模块继续 BUILDING。

本批修改使旧反向夹具的源码固定摘要失效，前段停点不再允许直接执行旧驱动。下一步先准备当前接口的固定加载/验收预览（只读/无模型），再就实际加载/付费验收的具体范围处理授权；不重发原消息、自动更新旧批准或从当前 Codex 冒充反向宿主。预览可评审或缺权限/身份变化时停止，发布另行处理。

### 真实反向失败补录与修复（report，2026-10-10）

后续关联回复和产物证明首批反向已在接口修改前单次运行，四文件全未审而失败；目标报告直接人类批准，一次额度已消费。此前交接时零启动记录保留其时间范围，当前以[实际结果](../../docs/verification/2026-10-10-claude-review-mac-reverse-first.json)为准。免费修复将范围内内容作为有界 JSON 输入直接交给 Codex，并核实禁用执行/派活相关功能，不增加权限。验收标准：文件正文真实传入、1MiB 超限和功能核验失败均不启动模型、旧调用和故障分类保持，完整免费总验证通过。下一步仅准备当前源码的无模型预览；真实新增一次须另行批准，旧 marker 不清除、驱动不重跑。Task 8 和最终 gate 保持未完成。

本批 report 收束：完整免费总套137 Python、53 shell、19 eval通过；当前四文件无模型预览见[JSON](../../docs/verification/2026-10-10-claude-review-mac-reverse-current-preview.json)。下步为实际源码加载与修复后真实反向有限验收的 gate；没有新付费授权，不能自动执行或重跑已消费驱动。

## 修复后反向第二批准备（2026-10-10，gate）

用户“继续”后仅推进免费准备；新驱动/目录、当前源码完整摘要、四文件5,020字节/180秒的公共dry-run及交接草稿完成。唯一目标“Claude验收会话”仍可见，进程重启后身份重新核实；原版Codex0.160.1版本/help通过，不检查额度、不发消息、不调用模型。AST/摘要通过，新marker/logs/result不存在。自动审批拒绝了驱动的错误宿主运行测试，原因是守卫若误通过会启动付费模型而无新增批准；未执行、不绕过、不记作通过。[具体预览](../../docs/verification/2026-10-10-claude-review-mac-reverse-second-plan.md)。

下一步须批准对该目标的一次交接及一次真实反向运行；首步唯一选路/固定摘要和宿主复核，目标自身授权不足即停，失败或未知不重试。源码通过绝对路径加载，不安装；此批不能证明斜杠UI加载。Task8和最终gate未完成，产品代码本轮未改变，不重复完整回归；无提交/推送/发布。

## 修复后第二批单次交接（2026-10-10）

本批已获用户直接“继续”批准，唯一目标与固定源码/驱动/输入/Git/新Claude身份复核通过。按 agent-relay session-routing 唯一桥路线仅投递一次，08:05:11 UTC入箱；两次50秒等待均pending，目标未读1、wake/receipt unknown，无匹配回复。新marker/logs/result均未生成，观察到模型启动0，不能称作真实审查通过或确定通信失败。[交接证据](../../docs/verification/2026-10-10-claude-review-mac-reverse-second-handoff.json)。

当前结果未知，不重发/换目标/改权限；已记录的本批批准不重复索取。下步只读对账同一消息和固定产物，或由人类在已有“Claude验收会话”查看联调消息并按该会话权限处理。晚到处理可能存在，不能另起重复执行。产品代码未改变，无新安装、提交、推送或发布；Task8和最终gate仍未完成。

## 2026-10-12 第二批对账与第三批准备（gate）

普通“继续”只读核对同一消息：已确认第二批关联回复、目标报告本会话人类“重试”后执行驱动一次，09:30 UTC守卫拒绝/退出1，模型启动0。固定Claude进程因重启失效；来源独立验证四文件/上下文/HEAD/status不变，新marker/logs/result不存在，无攻击标记。[实际证据](../../docs/verification/2026-10-12-claude-review-mac-reverse-second-result.json)。此前pending保留当时观察，当前已收到/处理回复；不将守卫停止当作真实审查通过。

已准备[第三批具体预览](../../docs/verification/2026-10-12-claude-review-mac-reverse-third-plan.md)：新目录/驱动、唯一同名Claude当前固定内核身份，四文件5,018字节/180秒/只读；AST、源码/CLI/输入摘要和无模型dry-run通过。产品摘要不变，沿用完整免费验证，不重跑旧驱动、不发新消息或调用模型。本次仅更新证据与计划；Task8和最终gate仍未完成。

下一步批准本新批次的一次交接/一次真实运行后，首步核对固定身份/摘要并唯一选路单次投递；目标自身权限不足、身份变化、失败或未知即停，不重试。此预览不授权安装、提交/推送/发布或斜杠UI加载。

## 第三批实际停止、免费诊断修复与第四批预览（2026-10-12，gate）

用户明确“批准”第三批后单次唯一投递/读取处理关联回复；目标报告本会话人类“同意”，驱动实际祖先/内核身份通过，Codex版本探针停止：wrapper退出127/0.472秒、conditions_missing/inconclusive、backend_started=false、4文件未审。输入/上下文/Git未变，无攻击标记。[实际结果](../../docs/verification/2026-10-12-claude-review-mac-reverse-third-result.json)。驱动marker不是模型启动；模型调用0、缺用量不写0。未重试或改变批准的固定事实。

已独立免费复现目标PATH的Node12运行Codex入口SyntaxError，以及已有Node24正常版本输出。新增版本/登录阶段诊断回归3子例先红后绿，安全分类不复制原始CLI/认证输出，旧check两值API兼容；完整免费验证138 Python/53 shell/19 eval通过，公共执行9项8.630秒。[修复证据](../../docs/verification/2026-10-12-delegate-preflight-fix.json)。

[第四批具体预览](../../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-plan.md)已固定已有Node24路径/版本/SHA，仅对子进程PATH生效；新根/驱动、4文件5,020字节/180秒无模型预览通过，未发新消息或启动。下一步须批准新批一次交接/执行后再复核当前固定身份/摘要并单次发送；目标自身缺授权、身份/摘要变化、失败或未知停止，不重试。无安装/升级/全局配置/提交/推送/发布，Task8/最终gate继续未完成。

## 单独的本机Node环境修复（2026-10-12，report）

用户当前要求“Node 12 这个版本也太低了吧，帮我解决一下这个问题，是什么原因导致的”。已定位NVM默认24.18.0，但Claude最新shell快照将Node12目录置前，Bash登录启动未初始化NVM；交互zsh本来选24。作为该新请求的本机修复，备份并补充~/.bash_profile默认NVM初始化、添加个人Claude SessionStart helper通过官方CLAUDE_ENV_FILE持久化PATH/NVM_BIN/NVM_INC；仅修复用户环境，不加入delegate产品依赖。原其他Claude设置/权限/插件/认证及旧Node版本保留，未安装或升级Node。

免费实际验证：从旧Node12 PATH启动的登录Bash和加载官方env文件的Bash/zsh均选Node24.18.0，Codex版本检查通过；保留既有env项且不保存模拟凭据，单次注册helper、无模型调用。[脱敏修复记录](../../docs/verification/2026-10-12-node-environment-repair.json)。真实已开Claude工具需用户恢复/重开使SessionStart生效，不用静态配置或模拟env验证替代实际工具激活。

实际Codex现为0.162.1，本次未升级它；第四批预览固定0.160.1已失效，禁止旧驱动。后续先在用户恢复Claude后只读验证实际Node/CLI及宿主，必要时重新准备当前预览；该请求不授权新的交接/付费审查、安装发布或Git交付。插件Task8/最终gate仍未完成。

## Claude重启后环境验证与当前第四批预览（2026-10-12，gate）

用户“已重启 claude”后只读验证同一“Claude验收会话”新进程身份；其真实SessionStart env文件仅含helper的PATH/NVM_BIN/NVM_INC导出，确实选择Node24.18.0。加载该实际文件覆盖旧Node12 PATH，Node/Codex版本执行免费通过；不是直接Claude Bash工具调用或真实审查。pnpm旧CLI0.160.1与Node24入口0.162.1并存，当前会话选后者，不推断旧安装被升级。

[当前第四批预览](../../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-current-plan.md)固定重启后宿主与实际0.162.1入口/Node24、新根/驱动/源码/输入摘要；增加marker前实际CLI选择及版本一致核验。实际help所需选项/关闭feature值/AST和dry-run通过，4文件5,036字节/180秒，无启动或新消息。只修验收夹具，产品不改、不重复未变化总套，旧第四批不能执行。

下步需针对当前新批一次交接/真实运行批准；已有第三批已失败停止，不扩大批准。首步固定事实复核、唯一选路单次发送，目标本身权限不足、变更、失败或未知停止。无安装/登录/提交/发布，模块继续BUILDING，Task8/最终gate未完成。

## 当前第四批未执行、驱动顺序纠错（2026-10-12，gate）

用户“可以”批准当前第四批一联系/一次审查后，来源固定摘要/实际CLI/宿主核验并单次发送；目标已确认并精确回复发现logs先引用后赋值，未执行驱动、未启动模型，目标自身第四批人类表态仍待。来源独立验证marker/log/result无、四文件/上下文/HEAD/status未变。[结果](../../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-driver-result.json)。此错误由来源重排验收驱动引入，AST不替代运行测试。

已增加严格--preflight-only，在任何模型/marker之前退出且明确不证明宿主祖先；安全实跑复现NameError后纠正，正常/非法参/错误CLI版本三个场景均在无模型条件下验证，新[纠错预览](../../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-fixed-plan.md)已固定。产品不改、不重复总套。原一次审查批准尚未消费，不申请增加模型次数；上一条联系已使用，需获准一条同目标纠错补充通信后才发送。目标自身直接人类权限仍须满足。

下一步仅补充消息授权后复核当前身份/摘要、单次发送修正驱动路径，继续原一条审查范围/180秒；变更/拒权/失败/未知停止，不重试或用旧驱动。无新模型、安装或Git发布，Task8/最终gate仍未完成。


## 2026-10-12 最新执行收束

用户“继续”批准一次纠错通信，目标报告直接人类“同意”后执行原批准的一次审查。当前反向已completed/findings，4/4已审、19.962秒、核心缺陷核对通过，见[结果与限制](../../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-success.md)。上述准备/未执行描述保留为当时事实；批准已消费，不追加运行或通信。两方向普通审查成功不替代主动越权/异常/新斜杠体验验收；下一停点为Checkpoint3实际diff与限制供用户审阅。


## 2026-10-13 两宿主CLI入口收束（report）

承接用户“继续”及已预告的免费入口调查，Task9f仅执行一次Claude2.1.296会话级源码初始化：--plugin-dir不安装，--init-only不开始对话。独立临时配置、空工作目录、OS禁网/拒绝全局写入和认证读取、Hook禁用/严格空MCP；不使用会关闭插件的safe-mode、restricted或disable-slash-commands。按已有MacBoundary回收本次内核coalition；同一策略后置探针核验源码拒写/临时可写/网络拒绝。成功后保存最小CLI加载事实，清理完整日志和临时配置；失败或未知不重试。本批已执行，4条命令加载、退出0、回收确认通过，非致命诊断及限制见[记录](../../docs/verification/2026-10-13-delegate-host-command-loading.md)。

同步两版README和claude-review合同中的宿主名称映射与主会话/后端模型额度区别，不修改源命令或执行逻辑，不重新安装或重复完整免费总套。交互展示/调用、真实模型主动越权、认证刷新和异常helper仍未验收。下一步按Checkpoint3展示最终实现和证据矩阵供用户审阅；日常安装、付费、通信或Git交付依旧分别授权。

本次最终审阅入口：[当前交付清单与验收矩阵](../../docs/verification/2026-10-13-delegate-delivery-status.md)。当前源码未提交、未发布；完整验收未勾。


## 2026-10-13 本机源码启用预览（gate，未执行）

源码路由修复后的“继续”用于只读核对现有安装与准备方案。Codex仍为Git来源旧三命令/每轮Hook；Claude本地来源登记与旧缓存并存，实际主会话加载根目录未知，不能仅凭缓存断定。当前PATH无srt，已有临时0.0.79可用于按次体检。已准备固定62文件和已有CLI摘要的[一次启用方案](../../docs/verification/2026-10-13-delegate-local-activation-plan.md)：隔离安装预验通过后，再将正常Codex delegate切为本地源码并重装，最后用已有srt做无模型doctor；不动Claude安装、不改全局env、不调用模型/通信、不提交发布。未经具体批准尚未执行；旧批批准不复用。完整Task2/6/8和人工gate仍未关闭。


## 本批实际收束（2026-10-13，report）

用户“继续 不要 总是停下来”承接本批具体启用范围。隔离安装一次通过后，正常Codex source切到本地并实际重装一次；4skill和61文件匹配、只SessionStart，旧注册命令直接调用无输出，非delegate配置语义/Claude设置/源码未变。Python3.12控制失败时CLI未启动、配置/cache未变，记录保留；分离解析/托管后执行首次实际CLI命令，不重复安装。已有srt按次无模型体检通过；Claude原user配置只读初始化实际从本仓库加载4命令，未安装/更新它。CLI、原认证及回收已核实，模型/额度/真实主会话UI仍未验。无凭据复制、全局env改动或Git交付。[结果与限制](../../docs/verification/2026-10-13-delegate-local-activation-result.md)。此前“待批准/未执行”是计划形成时状态，不再请求已执行批次批准。

## Checkpoint2b实际接续（2026-10-13）

用户“批准仅刷新 Claude delegate”已授权本批。update一次成功但版本0.4.0无操作；uninstall一次因本批OS遗漏settings原子暂存路径失败，按约定停止，未install/重载。旧安装及其他配置未变。临时假HOME中的修正限写探针已通过；下一步是[修正后的有限重装方案](../../docs/verification/2026-10-13-delegate-claude-refresh-result.md)，需新批批准后一次uninstall --keep-data、成功后一次install，再普通重载/UI检查。原批准不追认为成功，也不扩大为自动重试。UI-001仍Required，模块BUILDING；不重新泛扫、不追加模型或Git交付。

### Checkpoint2b第二批实际接续（2026-10-13）

用户对具体修正请求回复“继续”，已执行新批：uninstall --keep-data一次成功；install一次因官方CLI本地temp_local暂存路径未在本批OS规则内而失败，已停止。delegate登记/启用当前缺失，旧缓存20个文件未变，仅新增orphaned标记，备份保留。下一步[仅剩一次安装方案](../../docs/verification/2026-10-13-delegate-claude-refresh-fixed-result.md)待新批授权；新增local暂存限写规则已在临时假缓存验证、其他缓存拒写。不得重复update/uninstall，不自动回滚其他配置。

### Checkpoint2b完成与Checkpoint3接续（2026-10-13）

用户对剩余install一次/重载/UI方案回复“继续”，最后一批通过：实际缓存61文件匹配，delegate登记/启用恢复、其他配置语义未变，既有Claude普通重载一次并直接确认四入口。UI-001关闭；前两批失败/部分效果保留，[完整结果](../../docs/verification/2026-10-13-delegate-claude-install-staged-result.md)。下一步整理实际产品/合同diff和证据进入Checkpoint3人工审阅，不新模型、不泛扫、不Git交付。Task2/6/8完整安全未验仍未勾；本checkpoint仅代表安装和显示完成。

### 当前停点：Checkpoint3实际对象已备齐

[最终实际diff与限制](../../docs/verification/2026-10-13-delegate-checkpoint3-review.md)已准备，UI-001关闭、普通双向审查成功；Task2/6/8完整条件未验。此gate请求审阅具体成果，不表示豁免缺口或自动授权提交/发布。审阅后第一步确定剩余具体验收范围，不重新泛扫或重复已通过且产品未变的回归。

### S1已批准但失败停止后的当前接续（2026-10-13）

用户“批准S1”授权有限真实入口批次；正向runtime启动失败，模型未开始，未发送反向。现有实施授权内先红→绿修复NATIVE-START-001监督代码安装路径依赖并完成免费回归，具体[S1记录](../../docs/verification/2026-10-13-delegate-s1-result.md)。保持原批不重试；代码修复不自动授权缓存更新或新真实验收。Checkpoint3供审对象应包括该有限delta；Task2/6/8完整条件仍未关闭，旧普通成功不覆盖新修复。

### S2当前实际接续（2026-10-13，report）

人类“批准S2”“批准恢复并继续原S2”“批准修正接续”的具体批次已分别记录。SRT/新输入恢复、实际Mac14项、修正后一次卸载/安装、普通reload和四入口均通过；当前源码正向真实Claude审查21.418秒完成4/4并确认清理/输入/观察配置。唯一反向交接384已被既有Claude验收会话处理，目标需其本会话人类直接同意，尚未启动Codex。本报告后只读对账同一包；目标授权后仅执行原已预告反向一次，不追加模型、安装或消息。详见[实际结果及未完成项](../../docs/verification/2026-10-13-delegate-s2-resume-result.md)。Checkpoint3最终人工审阅和Task2/6/8完整条件保持独立。

后续结果：目标人类直接“同意，你来跑”，真实Claude应用已安装新review入口→Codex一次22.326秒完成4/4，核心发现、等价输入、主会话祖先/代际、源/配置/Git不变及回收通过。来源UI独立读到人类授权和完成提示。当前S2普通双向批次收束，两向和唯一交接额度均消费；仅整理持久实际diff及未验限制交Checkpoint3人工审阅，不再模型/安装/通信、不自动Git交付。

### 命令/功能多维审查后的修复计划（2026-10-13，制定时尚未实施，现已完成）

用户另行请求命令和功能多维审查。限定审查已完成，四入口命名/职责保留，但3项Required使当前实现不能直接通过最终审阅；见[报告](../../docs/verification/2026-10-13-delegate-command-multiaxis-review.md)。本次只报告和记录队列，未修改产品代码，不把审查请求或目录中计划存在当作新增付费/安装/交付授权。

1. Task9h（P1，S）：范围外路径不能阻断有限审查。涉及review_context.py与test-review-context.py/test-review-cli.py（3文件）；用已追踪/未跟踪范围外方括号路径先红→绿，比较两后端预览与原快照摘要，非法请求路径仍拒绝。
2. Task9i（P2，S）：统一已知模型归属校验。涉及delegate_backend.py、codex-exec.sh、test-review-backends.py与模型校验必要共用实现（至多4文件）；假CLI先红→绿验证provider前缀/旧入口大写、零启动、合法/default/custom既有合同及不fallback。不得擅自封死全部未来模型。
3. Task9j（P2，S）：同步双语当前状态。涉及README.md/README.en.md及docs/releases/unreleased.md和英文对应页（4文件）；比对S2事实、当前未发布身份、保留限制与历史链接。依赖9h/9i状态明确，不声称未来修复源码已复用旧live验收。

三个修复仍属于claude-review，不开新模块或平台、不自动实现4个Optional建议。免费回归按修改范围执行；模型/安装尝试不复用已消费S2，远端步骤不开始。当前后续第一步为9h的失败回归；修复后再带实际diff及剩余安全条件回到原Checkpoint3（gate），不提前勾最终批准。

### 三批修复接续完成（report，2026-10-13）

用户“分批次 快速处理审查出来的问题”明确授权上述9h/9i/9j源码修复；按原模块切片完成，不重复前置确认。模型校验抽成delegate_model.py供公共及旧入口复用，并同步两版spec职责/规则，未扩大模型或后端范围。具体RED/GREEN、免费总148/53/19和文档检查见[结果](../../docs/verification/2026-10-13-delegate-command-fixes-result.md)。修复队列三项均关闭，4项Optional保留；原审查报告与S2证据保持原基准。新的完整diff包独立冻结，不覆盖旧供审摘要，不宣称新源码已安装或实际模型验证。下一步原Checkpoint3（gate）：在本仓库/本分支审阅新diff与未验限制；没有新的模型/安装/Git交付授权。

### Checkpoint3部分成果接受与Task9k（gate，2026-10-13）

用户对具体最终源码/限制接受请求回复“继续”，按上下文确认当前固定源码部分成果；不推导全安全验收或安装/付费/Git权限。三项Required已修复、源文件供审快照未变。Task2/6/8保留；下一具体步骤为[已准备S3两宿主仅delegate同步](../../docs/verification/2026-10-13-delegate-post-review-sync-plan.md)，官方管理help、62文件冻结和缓存差异核对已完成。Task9k涉及安装/登记，因此进入独立安装gate；只有新批批准后最多三条30秒修改命令及无模型读回，不更新其他插件/组件、不追加真实模型或通信。

### S3失败收束与窄规则接续（gate，2026-10-13）

原S3已批准并执行Codex add一次，退出1且原stderr未保留，清理confirmed；两缓存、配置和源码与前值一致。系统拒绝事件显示具体同级plugin-install暂存目录未放行，因果仍待新批输出；候选修正8项实际假HOME通过，脱敏诊断5项通过。详见[结果与有限接续](../../docs/verification/2026-10-13-delegate-post-review-sync-result.md)。只有新批明确批准后才再Codex add一次及通过后Claude尚未执行的两条各一次；其他原S3边界、30秒和失败即停不变。无凭据开放，不追加模型、依赖安装、重载、通信或Git。

### S3完整替换接续（gate，2026-10-13，待批准）

仅暂存规则接续已批准但再次Codex add退出1，指向plugin-backup临时目录拒创建，缓存/配置/source无部分变化。复核官方同版本替换全流程后准备包含两种临时树的窄候选；假HOME替换与回滚/清理/配置原子写通过，权限不扩大到凭据、其他插件或arg0。具体边界和第三批一次范围见[最新结果](../../docs/verification/2026-10-13-delegate-post-review-sync-resume-result.md)。新批未获授权、未执行，不复用前两批started或自动retry；产品源码及原设计不重审，不重复产品总套。

### S3完整替换接续已批准并通过（report，2026-10-13）

用户“批准S3完整替换接续”后已完成本批三条30秒/条的正常安装及16项无模型读回。62源码和Codex四迁移skill逐字核对、配置及来源/源码不变、清理confirmed；两主会话未重载或通信，没有模型/认证/依赖/Git动作。详见[成功结果](../../docs/verification/2026-10-13-delegate-post-review-sync-complete-result.md)。原失败留存，Task9k关闭；Task2/6/8完整安全条件仍未整体通过，后续真实补证需具体新批，不复用本安装授权。

### S4有限补证准备（report → 新增付费执行gate，2026-10-14）

S3安装gate已完成，不重跑安装或总套。当前接续Task2/8的单次Read拒权补证：四个固定合成文件、一个快照外无敏感排除文件；沿用原权限，不启用写入或派活工具。驱动/输入/62源码摘要已固定，无模型预览和缺授权不启动后端检查通过。具体范围、限额、直接证据判据与停止条件见[S4方案](../../docs/verification/2026-10-14-delegate-s4-read-boundary-plan.md)。新增一次模型须独立授权，失败/未知即停、不重试；不包含安装、通信、反向、认证刷新或Git交付。该批不保证关闭Task2/6/8全部缺口，未观察的模型事件继续记录未验证。

本轮AI已直接确认Claude“Claude验收会话”四入口显示，未发送reload或模型消息。当前状态导航收束旧日期段落，历史证据不改；不修改产品行为或补历史评审标记。

### S4一次执行已收束（report，2026-10-14）

用户明确“批准S4单次读边界验收”后执行一次固定驱动；后端启动但返回backend_result_error，6.751秒、failed/inconclusive、0/4，回收confirmed、固定输入和被观察设置未变。本批未通过，不重试，授权已消费。错误终态权限字段未留存，不能断言没有Read企图/拒权；具体后端原因未知。Task2/6/8保持未完成，产品不改。结果见[S4收束](../../docs/verification/2026-10-14-delegate-s4-read-boundary-result.md)。后续仅做免费合成错误终态诊断复现，新增真实调用/安装/通信另授权。

### Task9l：错误终态的固定诊断补齐（report，2026-10-14）

用户承接免费故障诊断步骤回复“继续”。范围为现有CR-05/08故障分类与日志隐私：合成错误终态复现拒权字段被提前返回遮住、错误类别丢失；先RED后最小修复，覆盖错误终态、非零进程、未知/畸形字段和凭据sentinel，再完整免费回归。改review_result.py及其结果测试，同步双语规格结果条款、任务/证据；不改参数、权限或执行器。来源参考官方发布类型中的result错误subtype及assistant.error封闭枚举，仍使用CLI、不安装SDK。源码修复为report，不新增live或安装授权；S4原始证据不改、具体实际原因仍未知。规模为单个解析分支与有意义回归，预计产品文件2个。

### Task9l已完成（report，2026-10-14）

合成RED产生15个新增失败断言，最小解析修复后GREEN；再验证已恢复中间错误与重复码。完整源码副本运行原总入口153 Python/53 shell/19 eval通过；原工作区入口因私有安装备份的20个0600脚本执行位退出1，未更改其隐私模式或验证断言。副本仅排除.git/.agent/acceptance，冻结时282文件摘要一致，当前产品/双语合同再次核对一致。结果见[Task9l](../../docs/verification/2026-10-14-delegate-error-diagnostics-result.md)。共13文件、无提交；最新诊断源码未安装或真实复验，S4报告与具体原因未知保持。Task2/6/8三个未勾不变。下一步仅固定最新版并准备delegate安装同步范围，新增安装/live/通信需具体授权。

### Task9m / S5仅同步诊断修复（gate，2026-10-14）

Task9l免费修复完成后准备本次正常安装同步。固定62插件源码和marketplace，当前两缓存仅差解析器/测试两文件；旧二进制摘要未变。沿用S3成功限写规则，新控制器只接受新S5授权，假HOME26个边界案例及替换/回滚两场景通过，未授权不启动真实安装。具体三条一次/30秒/禁网安装、16项无模型读回和两安装副本各24项结果回归见[S5具体方案](../../docs/verification/2026-10-14-delegate-s5-sync-plan.md)。安装独立gate尚未执行；不重载、通信、模型、依赖、认证、全局环境或Git交付，失败/未知即停、不重试。

### Task9m / S5已批准并通过（report，2026-10-14）

用户明确“批准S5仅同步诊断修复”后，先记录预览摘要授权，再执行新控制器。Codex add一次、Claude user uninstall --keep-data/install各一次成功且回收confirmed；两安装62源码和Codex四迁移skill核对、16入口无模型检查、安装副本48结果回归通过，其他配置语义/来源/源码未变。无重试、重载、通信、模型、依赖/认证/全局环境/Git动作。Task9m关闭，S5授权已消费；Task2/6/8完整安全三项未完成。见[S5结果](../../docs/verification/2026-10-14-delegate-s5-sync-result.md)。下一步准备剩余真实安全补证范围，新增模型仍需具体批准，不追认S4。

### Task9n：总验证排除私有验收产物（report，2026-10-14）

S5已完成，接着处理Task9l发现的工作区总入口误扫：私有安装备份按0600保存，现有find将其当源码要求执行位；既有.gitignore明确排除此目录。仅让JSON/Bash/Python语法发现排除精确.git及.agent/acceptance子树，不扩大为全部.agent、所有忽略文件或产品目录。先合成夹具RED，证明私有坏文件应不影响总入口、普通源码坏JSON/语法/执行位仍失败，再最小修复、标准工作区总验证GREEN。改scripts/validate.sh与验证器回归，同步双语贡献/开发流程及任务结果；不改插件62源码/安装或真实调用。此免费验证入口修复为report，不需要新安装或模型授权；不弱化任何现有产品断言。

### Task9n已完成（report，2026-10-14）

4个隔离发现规则测试RED有1失败，最小精确排除修复后GREEN；普通产品坏JSON/Python/Bash/缺执行位及其他.agent/相似目录仍失败。原工作区直接运行标准总入口退出0，157 Python/53 shell/19 eval；未放宽备份0600、未弱化原产品断言。插件62源码与S5固定摘要未变，无新增安装/模型/用户配置/Git。Task9n关闭，11文件、无提交；见[结果](../../docs/verification/2026-10-14-delegate-validator-discovery-result.md)。Task2/6/8三个完整安全未勾项继续保留。下一步仅准备剩余真实补证范围，新增模型或通信分别授权。

### S6诊断修复后的单次读取补证（gate，2026-10-14）

S5同步和Task9n标准总验证已通过，用户“继续”推进Task2/8的下一批准备。新S6目录固定当前62源码、两缓存/Codex四迁移skill、原CLI/Node/SRT及与S4相同的四文件/合成canary；任务文字不变，仅新已安装解析器能保留已知错误类别和拒权事实。无模型dry-run及缺授权/错误摘要拒绝已通过，未创建授权或启动标记，未重跑已通过总套。具体单次sonnet/8轮/180秒/估算1美元、限权、停止条件、有限通过判据见[S6方案](../../docs/verification/2026-10-14-delegate-s6-read-boundary-plan.md)。下一gate仅新增一次付费调用；不安装、重载、通信、反向、认证刷新或Git动作；目标归属无法核实时仍unknown，Task2/6/8不自动勾。

### S6一次执行收束（report，2026-10-14）

用户在具体单次范围之后回复“继续”，记录实际原话，仅调整私有驱动授权匹配并重新绑定摘要，原供审版本保留；不写Spec/Plan评审批准标记，不改变任务/权限/限额/判据。已安装公共入口执行一次6.043秒，后端实际启动但认证错误，failed/inconclusive、0/4未审；固定诊断claude_api_authentication_failed及backend_result_error，读拒权未观察，具体认证根因未知。内核coalition清理confirmed、控制器未超时、源码/两缓存/输入/Git及被观察设置不变，0600分离产物报告一致。本批未通过、次数已消费、不重试；Task2/6/8仍未完成。见[实际结果](../../docs/verification/2026-10-14-delegate-s6-read-boundary-result.md)。同轮截图另一个帮助读取失败是访问已退役delegate.md，已经实际展开核实，和本次认证失败分开。下一步仅免费只读认证加载路径核对；新增模型/认证操作/安装另按具体范围处理，不干预截图中的独立运行任务。

### S6后续免费认证路径诊断收束（report，2026-10-14）

用户“继续s6”承接已预告的只读核对，未新增付费调用。固定原版CLI同一NativeRunner/MacBoundary文件边界、allowlist为空的一次auth status确认claude.ai/firstParty及默认目录、进程回收、设置未变；20秒sandboxd只读查询没有匹配日志，不能归因或排除刷新。默认沙箱log拒绝及外层只读成功分别记录。本地loggedIn不是服务凭据有效证明，具体认证根因仍未知，暂不改产品/权限或重跑S6。已请求终端原版/status Login状态，不要求Desktop重新证明旧事实。见[诊断结果](../../docs/verification/2026-10-14-delegate-s6-auth-diagnosis.md)。本批5文档/流程文件，无提交；Task2/6/8保留，新增live、认证操作和安装仍按具体范围处理。

### S6诊断接续准备（新增live gate，2026-10-14）

用户反馈终端Login有效已记录，不要求重复登录。固定原版二进制静态映射确认authentication_failed多分支，原因仍未定；不改产品源码或权限。私有观察器在原NativeRunner结果返回后保留固定提示/精确canary归属，原结果对象和调用参数保持；预览/真实文件冲突先RED后修复，7隔离用例/最终公共Python入口dry-run通过、0.581秒、后端未启动、固定对象/被观察设置不变。冻结的新批一次范围见[具体方案](../../docs/verification/2026-10-14-delegate-s6-diagnostic-followup-plan.md)，没有授权或启动标记。新增live必须明确批准，失败/未知/无拒权停、不重试，不包含安装/登录/通信/反向/Git交付；Task2/6/8保留。

### S6指定Read拒权子验收通过（report，2026-10-14）

用户直接“批准”绑定冻结清单后，原版Claude2.1.296实际调用一次11.974秒，模型claude-sonnet-5-5、CLI估算约0.030152美元。官方终态permission_denied，私有精确比较证实拒绝工具为Read且目标为指定排除文件；共同failed/inconclusive/退出1、1/4和三未审范围正确，内核coalition清理confirmed、固定源码/两缓存/输入/Git和被观察设置不变。Read子验收通过但完整审查未完成；本次无认证错误，旧认证失败根因不追认。第7行核心合成缺陷校准成立，50%反例收窄模型过宽触发描述，原报告保留。不将工具拒权扩大为本次OS打开拒权证据。更新12份文档/流程记录、无提交，产品源码未改；见[结果](../../docs/verification/2026-10-14-delegate-s6-diagnostic-followup-result.md)。单次授权消费完毕，不重试或重复普通双向/Read。Task2/6/8仍三项未勾，下一步按现有合同整理写入/递归、异常/稳定性及菜单调用剩余方案，新增高风险/付费/安装/认证/通信/Git操作具体授权。

### 剩余验收对齐与S7菜单子项准备（report→gate，2026-10-14）

用户“继续”后限定Task2/6/8现有缺口，不泛扫。安装副本depth=1公共review/run两后端及旧脚本共10项准确拒绝且无后端/认证/运行时启动；首轮Xcode shim警告使精确stderr断言失败，定向复现及固定已有Python后原断言通过，原失败保留。源码/两缓存/输入/Git及被观察设置未变。AI在已有ClaudeClaude验收会话Tab选中review、参数提示匹配，未发送/清空/恢复原会话；只证明菜单选择子项。详见[证据矩阵](../../docs/verification/2026-10-14-delegate-remaining-acceptance-feasibility.md)。

官方CLI和源码确认默认工具列表移除Write/Bash/Agent/Skill，不能通过重复付费调用稳定取得缺失工具的真实企图；不改CR-03或生产权限。独立Write可见但deny-all夹具属于后续需审阅的取舍，本批不实现。已备齐[S7两条宿主指令](../../docs/verification/2026-10-14-delegate-s7-menu-plan.md)：已有ClaudeClaude验收会话help一次，明确成功后review/codex/dry-run一次，后端模型0但主会话可能耗额度，每条180秒、失败/未知即停、不重试、不安装/重载/认证/权限/通信扩展或Git交付。具体目标指令提交授权尚未取得，不发送。本批6文档/流程文件、无提交，Task2/6/8仍三项未勾。

### S7已批准、界面输入等待（report，2026-10-14）

用户直接“批准S7”后，固定候选/源码/两缓存/输入与分支核对通过，授权原话及前置摘要保存。没有提交指令。Claude当前其他会话正在听写且有未发送草稿，两次间隔只读确认仍在进行；为避免干扰用户，不停止听写、不切换目标、不读取/保存草稿内容。已请求仅反馈输入结束，既有S7两条授权未消费，不重复请求批准；输入结束后先复核目标空闲/空输入，再按原顺序help一次、通过后review dry-run一次。没有安装/配置/权限/模型/消息/Git交付，不把等待当执行失败或已完成；Task2/6/8保持未勾。

用户随后反馈“输入结束”；目标help菜单已选中并记录提交前意图，未点击发送。接续复核发现界面已切到其他会话，新草稿后再次开启听写，停止界面动作。两条实际提交0，不能将意图标记视为已执行；固定源码/两缓存/输入与被观察设置未变，授权未消费，界面空闲后按原顺序接续，无需重批。私有记录`s7-ui-recheck.json`仅保存状态，不保存草稿内容。

### S7实际有限收束（report，2026-10-14）

用户继续并反馈界面空闲后，目标help消息及实际安装脚本--help完成，四入口语义吻合。review菜单Tab选择正确，但中文键入缺字，选择替换未生效后出现重复参数，准备清除时已被并发提交；AI发送点击0次，提交者未知。宿主纠正后只执行一次原定codex/context/dry-run公共脚本，报告exit0/backend_started=false；直接输出前缀确认仓库/限定范围/基准，完整原始输出截断，精确输入和全输出验收未完成，不整体通过，不重发。固定对象和被观察设置未变，产品未改，完整Task2/6/8仍三项未勾。见[有限结果](../../docs/verification/2026-10-14-delegate-s7-menu-result.md)。下一步仅收束输入与证据采集缺口，不从已观察调用推导新宿主提交授权。

### S7已有输出补证（report，2026-10-14）

只读目标当天Bash工具记录并按tool_use_id关联，help/review各一次；实际review argv与批准范围精确相等，完整预览全字段、四文件摘要及exit0/backend_started=false确认，help仅去掉末尾换行、恢复后候选摘要相等。补齐功能链路，不改写原交互失败，4项合成AX判定只验证多行解析。无CLI/UI/模型重跑，固定对象及被观察设置未变；宿主日志version2.1.295/modelclaude-opus-5-5，插件hostunknown保持，金额未知。见[读回结果](../../docs/verification/2026-10-14-delegate-s7-output-readback-result.md)。Task2/6/8完整缺口仍保留，下一步收束剩余安全与异常条件，不重复已通过功能链路。

### Task6有限启动诊断（report，2026-10-14）

同一当前MacBoundary、现有Node/SRT，各--version三次，分别用当前Python3.12.14与历史Xcode3.9.6作监督解释器，共12项全部completed/cleanup confirmed；原5秒期限保留，Claude/认证/网络/模型0次。合成HOME/临时树，固定源码/两缓存/输入/Git/运行时及4被观察设置未变。未复现历史超时，不能推定根因或稳定性；旧原始临时材料缺失，设置变化归属仍未知，产品不改，Task6保持未勾。见[实际结果](../../docs/verification/2026-10-14-delegate-task6-runtime-timing-result.md)。

### 剩余验收判据取舍（gate，2026-10-14，已明确批准）

[供审具体文本](../../docs/verification/2026-10-14-delegate-acceptance-decision.md)说明CR-03/06/09分层验收建议及Task2/6/8证据映射；中英文拟文本已列出，但spec未改、任务未勾。生产工具/OS/网络权限及全部产品断言保持不变，历史失败和未验证事件保留。用户须明确决定修订成功判据或保持原合同；不是再次接受源码。若批准，首步同步中文spec/英文对应页及plan/todo，再逐项按新合同核对；不保证直接关闭3项，不含新增模型/安装/认证/通信或Git交付。若保持原合同，则完整任务继续未完成，主动事件的独立夹具须另行设计审阅，不重复普通审查。

### 分层验收执行收束（report，2026-10-14）

明确批准已保存，双语合同按供审文本同步；19项证据映射通过，当前2项OS权限/6个内核生命周期方法通过、产品及断言不变、4被观察设置未变。原私有控制器0测试类名预检失败与1方法长socket启动失败保留，类名/短临时根修正后原断言通过，不归因为权限放行或原历史间歇根因。Task2/6/8按新标准关闭，所有未验证项保留。详见[分层结果](../../docs/verification/2026-10-14-delegate-layered-acceptance-result.md)。

### Checkpoint5：分层验收最终diff与限制（gate，已收束）

准备当前Git相对HEAD的新增/修改/删除及行数、最新检查和版本分开的真实证据、未验证条件；因未按任务提交，清单包含整个工作区既有未提交变更，不声称全属本轮。用户审阅并明确接受最终验收后才关闭本gate；此前源码部分接受不重复、历史全验收不追认。首步仅核对最终清单与当前受审文件，不安装/调用模型或修改外部对象。提交、推送、发布保持分别授权。

### 最终人工接受与本地模块收束（2026-10-14）

用户对上一轮已展示的具体最终diff/行数及限制回复“继续”，按唯一接续对象记录为接受当前Mac功能和分层验收。先核对全部233受审文件摘要/文件集合、分支/HEAD、62产品与测试、输入/Git/运行时及4被观察设置全部未变；保存实际原话和供审摘要后关闭Checkpoint5。无需新增行为或模型，本模块DONE；不添加历史Spec/Plan完整批准标记，不改变未验证项，不授权提交、推送、发布。原供审md/json保留生成时的pending字段，由当前todo及交付状态页记录后续接受，不覆盖历史证据。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。

## 发布后文档事实修订（report，2026-10-14）

针对已冻结审查DOC-101～106修正当前双语说明：发行/安装状态、退役Hook流程、版本绑定的真实与菜单证据、源码加载与缓存区别、实际验证套数量及英文漏同步。只改文档，不改CR条款、产品权限、接口或测试断言，不重跑模型、安装或修改全局配置，不自动提交/推送/发布本次文档修订。

验收：核对v0.5.0发布回执及缓存关系；逐项定位六类旧文本并复查双语；检查所有当前Markdown文件链接与锚点、代码围栏、git diff --check；确认产品62文件、历史批次证据和归档未变。完成后在todo记录结果并报告未提交状态。

### 文档交付接续（report，2026-10-14）

沿用用户此前明确的提交、推送授权，将已核对的17份文档修订形成一个中文docs提交并同步main及开发分支。先获取两分支新鲜远端状态，确认修订范围、敏感信息和链接，再提交并原子推送；远端并发冲突、权限拒绝或结果未知时停下核实，不强推。保留v0.5.0标签和发行版，不重新安装或调用模型。最终以远端提交读回和工作区状态报告交付。
