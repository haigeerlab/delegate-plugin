# 规格：claude-review（可选 Claude Code 审查后端）

<!-- spec-guard: review approved dbfa8c162069 -->

简体中文 | [English](../docs/en/SPEC-claude-review.md)

**审批方式（2026-10-25）：** Codex 后端审查调用固定 `-c approval_policy="never"`，见 [run-resume](run-resume.md) 修订记录 R2；其余审查合同不变。

**当前发行（2026-11-18）：** v0.8.6 是补丁版，实现本规格「沙箱证书信任」：Claude 后端审查自动把系统明确信任的证书以只读文件经 `NODE_EXTRA_CA_CERTS` 追加给沙箱里的 claude，失败时报非致命 `system_trust_export_unavailable`；接口仍为 1.3，网络放行范围不变，真实验收 CR-14 未做，见[版本说明](../docs/releases/v0.8.6.md)；免费验证 343 Python / 53 shell / 19 eval。

**v0.8.5 发行（2026-11-18）：** v0.8.5 是补丁版，修复审查结果 schema 缺 type 导致 Codex 审查全部失败，并新增 codex_turn_failed、codex_output_schema_rejected、claude_api_tls_untrusted 三个固定诊断码；接口仍为 1.3，沙箱边界不变，见[版本说明](../docs/releases/v0.8.5.md)；免费验证 333 Python / 53 shell / 19 eval。

**v0.8.4 发行（2026-11-04）：** v0.8.4 是补丁版，无提交仓库的审查改报 `repository_has_no_commits`（原为 `git_probe_failed`），退出码与其他报告内容不变，接口仍为 1.3，见[版本说明](../docs/releases/v0.8.4.md)；免费验证 330 Python / 53 shell / 19 eval。

**v0.8.3 发行（2026-11-04）：** v0.8.3 是补丁版，只改使用者文档与帮助文字、行为不变，接口仍为 1.3；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.8.3.md)；免费验证 328 Python / 53 shell / 19 eval。

**v0.8.2 发行（2026-10-28）：** v0.8.2 是补丁版，只改 `/delegate:run` 的命令说明、行为不变，接口仍为 1.3；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.8.2.md)；免费验证 328 Python / 53 shell / 19 eval。

**v0.8.1 发行（2026-10-28）：** v0.8.1 是补丁版，只改文档、行为不变，接口仍为 1.3；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.8.1.md)；免费验证 328 Python / 53 shell / 19 eval。

**v0.8.0 发行（2026-10-27）：** v0.8.0 是次版本，`/delegate:run` 新增结果文件、`--continue`、`--timeout`、`--check`、`--authorized-by`、`--rules-file`，接口说明升到 1.3（只增不改，见 [run-result](run-result.md) 等五份规格）；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.8.0.md)；免费验证 328 Python / 53 shell / 19 eval。

**v0.7.1 发行（2026-10-27）：** v0.7.1 是补丁版，只修 run 中止时回收 Codex 起的后代进程组（见 [channel](channel.md) 修订 S41）；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.7.1.md)；免费验证 253 Python / 53 shell / 19 eval。

**v0.7.0 发行（2026-10-26）：** v0.7.0 新增 run 超时保留进度（见 [run-timeout](run-timeout.md)，接口 1.2）并让写模式不再写入 Codex 项目信任（见 [write-trust](write-trust.md)）；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.7.0.md)；免费验证 247 Python / 53 shell / 19 eval。

**v0.6.0 发行（2026-10-26）：** v0.6.0 新增可续跑委托（见 [run-resume](run-resume.md)），本模块的 Codex 后端审查改为固定 `approval_policy="never"`，审查合同与报告格式不变，见[版本说明](../docs/releases/v0.6.0.md)；免费验证 196 Python / 53 shell / 19 eval。

**v0.5.3 发行（2026-10-17）：** v0.5.3 发布插件根目录 `interface.json`，并把本模块的统一审查报告 `schema_version: 1` 写成对外合同（见 [integration-interface](integration-interface.md)），报告生成不变，见[版本说明](../docs/releases/v0.5.3.md)；免费验证 173 Python / 53 shell / 19 eval，未新增模型调用。

**v0.5.2 发行（2026-10-16）：** v0.5.2 让 Codex 审查附带的文件内容逐行带行号，解决真实审查中发现缺少行号、整次被判失败的问题，并修正 README 说明，见[版本说明](../docs/releases/v0.5.2.md)；免费验证 166 Python / 53 shell / 19 eval，修复后用 main 源码做了一次真实 Codex 审查，6/6 完成且发现带可核实行号。

**v0.5.1 发行（2026-10-16）：** v0.5.1 修复 Claude Desktop 会话注入官方 `ANTHROPIC_BASE_URL` 时 Claude 后端被误拒的问题，见[版本说明](../docs/releases/v0.5.1.md)；免费验证 162 Python / 53 shell / 19 eval，未新增模型调用，Desktop 中 Claude 后端完整 doctor 与真实审查未验证。

**v0.5.0 发行（2026-10-14）：** v0.5.0 已发布，提交 `c59b370` 已推送 main 与开发分支，本机两宿主 0.5.0 安装内容核对一致。免费发布验证 157 Python / 53 shell / 19 eval、安装后16项入口检查与48项结果回归通过；发布未新增模型调用，S2/S6/S7仍按各自固定源码报告。详见[交付状态](../docs/verification/2026-10-13-delegate-delivery-status.md)。

**当前验收口径（2026-10-14）：** 用户明确“批准分层验收修订”，CR-03/06/09按下表分层判定。生产权限、工具集与产品测试不变；模型主动Write/递归、认证刷新、自然helper类型、历史未定根因和长期稳定性仍单独标未验证，不能追认为旧标准通过。S7菜单到脚本及完整dry-run输出已核对，原自动输入/并发提交失败保留。下方早期状态按当时版本/判据保留；当前逐项结论以本模块todo及证据对账为准。

计划：[plan.md](../tasks/claude-review/plan.md)；任务及真实结果：[todo.md](../tasks/claude-review/todo.md)；取舍：[ADR-002](../docs/decisions/ADR-002-claude-review-isolation.md)。本规格中的新命令、文件及条款是实施合同，不能当作当前安装能力或已通过测试。

## 目标与范围

- 仅有 `codex` 和 `claude-code` 两个执行后端；宿主与后端独立，用户显式选择，默认保持 Codex。
- Claude Code 第一版仅审查：代码缺陷、回归风险、规范/计划/实现一致性及指定范围证据。不自动修改、修复、提交、推送、创建/合并 PR 或修改事项。
- 保留现有 Codex 自由文本及 `--write` 行为；新增结构化审查模式供两后端接收等价上下文和结果契约。
- Spec Guard 仅跟踪本项目开发及审查上下文，不增加其执行器或运行时依赖。不实现宿主反向自动选择、第三后端、通用调度、后台排队或无限重试。
- 第一版只支持 Mac 本机 Claude 后端；当前实测 macOS 15.7.3 arm64。使用已有原版 CLI/本机认证与独立内核 coalition；不扩展 Linux/Windows，不自动准备运行依赖。旧 Linux/SSH 实测仅作历史证据。Codex 既有平台和默认行为保持不变。

## 双后端命令接口（v0.5.0）

本批接口设计经用户“继续”确认；新源斜杠入口为 `/delegate:review`、`/delegate:run`、`/delegate:doctor`、`/delegate:help`。review 两后端都只读；run 保留既有 Codex 自由文本及显式 write，Claude run 拒绝。旧 `/delegate:delegate` 源命令移除；旧 codex-exec.sh 和 delegate-exec.sh 无子命令调用继续有效。`delegate-exec.sh doctor [--backend codex|claude-code] | --reviewers [--json]` 原样转交 `review_doctor.py`，与 `/delegate:doctor` 相同、不调用模型；因此第一个参数恰好是 `doctor` 的调用不再当作旧版任务原文（2026-11-26 用户选定，原话「按 A 修」）。两宿主从同一源命令使用公共入口，宿主生成缓存不随源码自动更新，四入口显示与 S7 菜单实际公共脚本/dry-run 已验收；无差错自动 UI 输入仍未验证。

以上斜杠写法属于 Claude Code。Codex 0.162.1 对应迁移 skill 为 `source-command-review/run/doctor/help`，通过宿主 skill 选择器调用并提供相同参数；显示名以加载列表为准，不能把 Codex 内置 `/review` 当成本插件入口。统一的是参数和脚本行为，不保证两宿主斜杠别名相同。四个 Codex 转换产物与 Claude CLI 本次源码初始化加载已核验，后续菜单到公共脚本与完整 dry-run 已核对，见[S7读回](../docs/verification/2026-10-14-delegate-s7-output-readback-result.md)；原自动输入失败保留。help/doctor/dry-run 不调用执行后端模型，不代表宿主解释这些命令不消耗主会话额度。

```text
/delegate:review --backend claude-code --paths src/payments --model sonnet
/delegate:review --backend codex --base main --head HEAD
/delegate:review --paths src/payments --module payments --spec spec/payments.md --plan tasks/payments/plan.md --dry-run
/delegate:run --write 按已确认方案修复并测试
```

终端等价入口是 `delegate-exec.sh review|run`。后端默认 codex，与宿主独立；模型另选，不 fallback。backend 能力和专属选项由 delegate_capabilities.py 的两个显式条目定义，帮助、doctor 和参数校验复用，不建立动态注册/通用调度框架。

公共入口与旧 `codex-exec.sh` 共用模型归属校验：已知模型家族和别名按大小写无关规则识别，提供商命名空间不能绕过跨后端拒绝；不改写传入的模型 slug。未知自定义 slug 由选定后端 CLI 验证，失败不切换后端或模型；Claude `opusplan` 自动切模型模式继续拒绝。
Git 状态可以报告全仓库是否有改动，但只对指定范围及显式上下文中未排除的文件名执行传输路径校验；范围外或已排除的特殊文件名不阻断审查。指定范围内不支持的路径仍明确失败，Git 输出/快照限额不变。

| 审查参数 | 合同 |
|---|---|
| `--repo` | 目标 Git 工作区目录；省略用当前目录发现仓库根 |
| `--paths` | 可重复，每次一个仓库根相对文件/目录；不接受 `.`、通配符或穿越 |
| `--module` | 标明模块名，须 paths；不与固定提交 diff 混用 |
| `--base` / `--head` | 固定提交 diff；base 必填，head 默认 HEAD，解析后记录 SHA |
| `--changes` | staged、unstaged 或 working-tree；与 base/head 互斥 |
| `--include-untracked` | 仅 working-tree 可用，显式纳入未跟踪文件 |
| `--exclude` | 可重复的明确排除路径 |
| `--spec` / `--plan` | 可重复的上下文文件，使用相同基准/版本策略；须位于仓库，排除冲突拒绝 |
| `--criterion` | 可重复的验收条件；空列表表示没有额外条件 |
| `--context` | 高级原范围 JSON；与全部快捷范围参数互斥，模型/后端/限制参数仍可用 |
| `--dry-run` | 无模型输入预览；不检查认证/运行依赖，不创建审查快照、日志或报告 |

纯 paths/module 默认读取 HEAD 的指定文件，不纳入未提交内容；仓库存在改动仍在预览/共同上下文展示。显式 changes 选择工作区版本时保留 paths/module 类型。没有 paths 的 base/changes 审查仅从相应 diff 取变更路径（仅显式纳入 untracked），不会扫描整个项目；空比较报告 conditions_missing/inconclusive，不启动模型。任务说明可省略为固定只读审查要求，不推断额外路径。

快捷参数生成与高级 JSON 等价的 schema_version=1 上下文，再复用同一 validate/capture/snapshot/result 路径；快捷工具默认仅 Read，停止条件为既有完整集合。参数冲突、后端混用、无范围与非法路径先拒绝。review 始终拒绝 write；本批不改变既有认证、OS 隔离、执行器限制或期限。

预览 `kind=review_preview`、backend_started=false；只有范围、基准、文件/diff 摘要、采集缺口、改动策略、权限、请求模型和停止条件，不输出源码/diff正文或发现结论；展示请求的 effort/轮次/估算预算限制，缺失不当作实际用量。host/observed_models 无执行证据时未知；backend_preflight=not_performed，不把能力说明当作可用性。主审查范围不存在时不能由现有 Spec/Plan 文件掩盖：采集缺口列出原范围，正常执行在启动模型前停止。正常 review 仍返回共同审查报告，run 保留原 Git 验收/自由文本合同。新增测试为 test-review-cli.py，进入免费总验证；新入口的真实宿主验收单列。

## Codex 审查读取适配修复（2026-10-10）

真实 Claude→Codex 已运行一次，但审查失败：Codex 没有获准的本地 Read 工具，又遵守禁止命令的要求，四文件全部未审。宿主祖先/代际通过，backend_started=true、usage 已报告，不能再记作“未运行”；证据见 [反向首批](../docs/verification/2026-10-10-claude-review-mac-reverse-first.json)。2026-10-12修复后反向真实审查已完成4/4并核对核心缺陷，见[最新证据](../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-success.json)；首批失败仍为历史事实。

Codex 共同审查改为从已校验的有限快照直接附带原路径、SHA-256 和 UTF-8 文件内容，以 JSON 待审数据放入 stdin；内容逐行加 1 起始行号前缀（与定位核验相同的分行规则），提示要求 findings.line 填对应文件行号，SHA-256 仍对应原始字节，快照文件不变；不用 Bash/MCP 取得内容，不扩大范围、不执行项目代码。Claude 仍由受限 Read/Glob/Grep 读取相同快照，两后端接收等价的实际文件信息。Codex 最终序列化输入上限为 1 MiB（含任务、元数据、diff 和带行号的文件），超限在 CLI/模型启动前报告 codex_inline_input_limit，不截断或自动分批。dry-run 展示输入方式、实际 prompt 字节数与上限，不输出内容。

Codex 审查明确关闭 shell_tool、apps、plugins、multi_agent，禁用 web_search，MCP 配置为空；保留 read-only 沙箱。用同一配置的无模型 features list 核对四个功能开关各唯一且 false；不支持、未关闭、坏输出或失败时 codex_review_tools_unverified，模型不启动。当前 0.160.1 已只读核实开关输出；这不是实际模型工具清单验收，不声称关闭所有控制工具。旧 Codex run/free-text 行为不变。过程日志仍不保留真实输入内容。

常规 stderr 摘要明确 status/backend/started/已审与未审数量/用量是否由后端报告，stdout 保留机器可读报告；有用量但未审不会伪装成通过。产物 host=unknown 是产品无法核实的口径，验收驱动另有真实宿主证明，不能把驱动结论无条件写回产品。

## 技术栈、目录与命令

保持 Bash 3.2、Python 3 标准库、Git 和已有源码风格；Python 使用 `-B`，不做无关重构。CLI 原版由用户安装，插件不安装、升级、登录或改变插件状态。
Claude 支持基线设为 `2.1.295`，还须验证实际所需参数；不称这是参数首次引入版本。Codex 新审查选项按 CLI 实际能力检查，旧调用不新增未经确认的最低版本要求。
`srt` 仅为 Claude 后端的可选依赖，固定 0.0.79，Node >=22.12.0；当前本机原版 CLI 2.1.296 的无模型版本/参数/严格边界认证已核实，已有有限正常模型审查成功记录，完整安全验收仍未完成；兼容性最低核对基线仍为 2.1.295。要求可用的用户 GUI launchd 域和核实的私有 Darwin libproc 能力；接口/身份/计数不符合预期即停止，不降级进程组清理。当前版本矩阵仅限上述实测 Mac，不宣称私有 ABI 为稳定跨版本接口。

当前候选文件职责（测试 CLI 由临时夹具生成）：

```text
scripts/delegate-exec.sh          → 公共薄入口
scripts/delegate_cli.py           → review/run、范围快捷参数和无模型预览
scripts/delegate_capabilities.py  → 双后端能力及专属选项定义
scripts/delegate_backend.py       → 后端专属参数验证与分派
scripts/delegate_model.py         → 公共与旧入口共用模型归属校验
scripts/review_execution.py       → Codex 共同审查、最小私有产物
scripts/review_native.py          → 本机 CLI/依赖/策略接入
scripts/review_macos.py           → 临时 launchd、kernel coalition、代际信号与清理
scripts/review_doctor.py          → 专属后端体检，无模型
scripts/review_context.py         → 校验范围、只读 Git 采集、固定快照与路径映射
scripts/review_result.py          → 公共结果验证、证据定位、脱敏与渲染
scripts/claude_review.py          → Claude 预检、argv、流解析与审查执行
scripts/review_isolation.py       → 本次 srt 策略、可用性探针与隔离启动
tests/test-claude-isolation.py    → 无模型的实际 OS 权限验证
tests/test-review-backends.py     → 后端分派、兼容与参数验证
tests/test-review-cli.py          → 新命令、范围/预览、缺主范围与假 CLI 端到端
tests/test-review-context.py      → 范围、Git、快照、路径与变更回归
tests/test-claude-review.py       → 假 Claude CLI 结果与错误注入
tests/test-review-native.py       → 本机分派、清理失败与原子控制事实
tests/test-review-macos.py       → 实际 Mac 生命周期/权限，无模型
tests/test-review-mac-integration.py → 实际公共调用链与固定假 CLI，无模型
tests/test-claude-mac-probes.py   → 固定摘要原版 CLI 的本机无模型认证
tests/test-review-lifecycle.py    → 原生 Mac 候选的失败证据，保持历史边界
tests/test-review-execution.py    → 公共入口端到端假 CLI/本机边界
tests/test-review-result.py       → 结果、模型、覆盖与定位故障
tests/test-review-artifacts.py    → 脱敏产物、权限与保留
```

上述路径相对 `plugins/delegate/`；复用 `backend.py` 的 Codex 检查与旧 `run_codex.py`，Codex 默认不变。Claude 本机使用单次 launchd 任务的 resource coalition 归属；旧进程组、Linux guest 和 SSH 夹具不代表这条路径通过。

当前源码提供公共命令；旧 `scripts/codex-exec.sh` 调用继续有效：

```bash
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh "已明确的 Codex 任务"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend codex --write "已授权的 Codex 写任务"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend claude-code --review-context /path/to/review.json --model sonnet "审查指定范围"
/bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend codex --review-context /path/to/review.json "审查同一指定范围"
```

| 选项 | codex | claude-code |
|---|---|---|
| `--backend` | 默认 `codex` | 显式 `claude-code` |
| `--model` | Codex 模型配置；对应 CLI 判断可用性 | Claude 模型别名或 ID；对应 CLI 判断可用性 |
| `--effort` | 保留既有配置方式，校验 backend 专属参数 | 第一版明确拒绝，不透传、不降低档位 |
| `--write` | 保留现有行为；结构化审查模式拒绝写入 | 明确拒绝 |
| `--review-context` | 可选；有该选项进入共同只读审查模式 | 必填 |
| `--max-turns` | 拒绝 | 默认 12；显式值须为正整数 |
| `--max-budget-usd` | 拒绝 | 可选正有限数；客户端估算上限，可能超出 |
| `--` / `--help` | 保留终止解析/无模型帮助 | 相同 |

只允许已定义选项；不给用户任意 Claude CLI 参数透传入口。校验全部参数后才进行预检/执行。明显跨模型族名称必须提前拒绝；其他不支持的模型由所选 CLI 明确报错，不能删参数重试。未指定模型时将请求值标为默认，实际模型仍以输出证据为准。

## 审查输入与固定范围

上下文 JSON 使用 `schema_version: 1`，未知字段、错误类型和范围不明均拒绝。它不是可执行配置，不携带命令、凭据或放宽权限的设置。

| 字段 | 合同 |
|---|---|
| `repository` / `working_directory` | 规范化的绝对路径，必须属于同一有效 Git 工作区；仍要求业务 Git 仓库 |
| `review_type` | `diff`、`module` 或 `paths` |
| `scope` | 包含路径、排除路径、模块名（需要时）及 diff 基准；不得默认为全项目 |
| `baseline` | 可解析提交/分支，或 staged/unstaged 比较；记录解析后 SHA、HEAD 和 diff 哈希 |
| `context_files` | 明确选择的 Spec、Plan、验收等文件列表；空列表表示没有这些上下文 |
| `acceptance_criteria` | 有限的审查判断标准列表 |
| `uncommitted_changes` | 明确纳入/排除 staged、unstaged、untracked；不能静默丢失用户改动 |
| `allowed_tools` | 仅可请求固定只读工具的子集，不可添加 Bash/MCP/网络/派活工具 |
| `stop_conditions` | 范围完成、权限不足、上下文缺失、时间/轮次/预算达限及输入变化 |

固定 diff 指定比较两端；模块审查必须给出文件边界；项目范围审查必须列出路径。上下文缺失时向主会话报告，审查者不提问等待或扩大扫描。
wrapper 使用固定 argv 取得必要的只读 Git 信息；关闭 optional locks、外部 diff、textconv、fsmonitor 和 hooks 等会触发程序的采集入口。采集命令不接受用户脚本，不执行 fetch 或修改 Git 状态。
快照按纳入范围复制真实普通文件，不使用指向源码的软链接/硬链接、不携带真实 `.git`。记录文件哈希，保留原路径映射，采集期间来源变化则停止。二进制、子模块、范围外链接、文件消失、读取失败及资源上限列入未审范围，不当作零问题。
两后端接收相同的任务、快照范围、基准、验收条件、排除项和停止条件；内部 CLI 参数可以不同。Codex 旧自由文本模式继续保持其原合同，不能从旧文本自动推导结构化“无问题”。

## 权限、上下文及认证

Claude 运行在本次快照目录，拟使用 `-p --safe-mode --restricted --permission-mode dontAsk --permission-prompts none --tools Read,Glob,Grep --disable-slash-commands --strict-mcp-config --mcp-config <空配置> --no-chrome --no-session-persistence --output-format stream-json --verbose --json-schema <共同 schema>`。
会话设置关闭普通 Hook、connectors、Artifact、模型 fallback 链及内容触发的模型切换；`switchModelsOnFlag=false`、`fallbackModel=[]`。不使用 `--bare`、`plan`、跳过权限检查、恢复会话或背景模式。设置文件若被忽略或实际工具清单不满足限制，不能继续报告成功。
文件工具只给 Read/Glob/Grep 指定子集；写入、Bash/PowerShell/REPL、MCP、Web、Skill、Agent、任务/事项、工作流与监视能力不可用。初始化校验仅另外容许 StructuredOutput 和 EndConversation：前者提供 schema 输出，后者是官方说明无法通过非空 `--tools` 移除的会话终止工具，不授予文件、执行或派活能力；提前结束而缺少完整结果仍为未完成。其余工具、重复/无效工具清单或 MCP 非空仍立即停止。[CLI 参考](https://code.claude.com/docs/en/cli-reference)、[工具参考](https://code.claude.com/docs/en/tools-reference#endconversation-tool-behavior)
初始化失败只保存固定原因码，区分空输出、非 JSON、超过大小限制、首事件不是 init、工具字段无效、工具集合不符和 MCP 未核实，不保存原始字段、路径、错误原文或工具输入。
原版 2.1.296 的全网络拒绝启动探针已复现 init 前的被动 `system/ui_invalidate`（event=`ui.render`）。初始化序列只容许至多 8 个这种事件，字段限 type/subtype/event 及可选 UUID 格式的 uuid/session_id，总序列至 init 最多 64 KiB；随后必须取得唯一合法 init 并校验工具/MCP。Hook、插件安装、控制请求、模型消息、未知事件或额外载荷均不能跳过。运行时与最终解析使用同一校验；超时/取消/缺少 init 仍不能通过。
上下文层关闭自动加载的 CLAUDE.md、skills、插件、memory 和项目定制；明确提供的规则/代码/diff/Issue/网页/日志一律是待审查数据，不是执行指令。
Mac 本机原版 CLI 自行使用既有认证，不读取或复制凭据、不自动登录。srt 仅给 CLI 原生认证运行时只读访问 `.claude`、`.claude.json` 和 Keychains；工具层对全部运行时读取路径设置精确/递归 Read deny，并启用 blockReadsOutsideWorkingDirectories。官方对 Read 规则应用于 Grep/Glob 的表述为 best effort，不能当作完整 OS 白名单；真实工具行为仍需模型验收。首版拒绝自定义认证目录、API/provider 环境覆盖和本地管理配置，不静默丢弃它们或改用另一认证。唯一例外：Claude Desktop 的 Code 会话会注入 `ANTHROPIC_BASE_URL=https://api.anthropic.com`；该值规范化后（scheme 为 https、主机名不区分大小写等于 api.anthropic.com、端口为空或 443、路径为空或 `/`，且无 userinfo、query、fragment 或空白）与 CLI 默认端点相同时放行。子进程环境本就不继承该变量，放行不改变实际端点；其他任何值仍报 native_authentication_environment_unverified。
OS 层用 srt 包围本机整个 Claude 进程；源仓库/Git、用户配置、Keychains 和快照不可写，仅专用 writable 目录及必要标准输出描述符可写。控制目录不向 reviewer 开放。关闭 srt 额外可写路径；不以 chmod/执行后哈希代替权限强制。
网络只允许当前选定的三个 first-party 443 端点；普通模型请求已在第四批通过；认证刷新、各端点覆盖和异常 TLS 尚未验收，不给审查任务网络工具，不继承宽泛代理或服务器配置放宽权限。隔离初始化失败、未知提供商策略、管理员 Hook/helper 或管理配置妨碍证明边界时返回条件不足，不绕过管理员策略或扩大权限。
认证通过同一执行环境中的 CLI 状态检查，不读/复制凭据文件、不打印认证原文或凭据片段；只有登录方法、提供商和状态等安全字段可保留。API key、用户登录及其他认证方式不能相互猜测或自动切换。预检成功不保证远端、额度或模型权限，隔离阻止刷新时明确失败。
宿主信息仅来自可信宿主元数据；否则为未知。插件目录、安装了哪个 CLI 或模型自述均不是宿主证据。两种宿主共同入口使用相同合同，不根据宿主自动选后端。
增加嵌套委托拒绝标记及所有 delegate 入口检查；Claude 因无执行/派活工具和无插件加载不能启动 delegate。既有 Codex 自由文本模式的行为纪律不能表述成不可绕过的权限锁。

## 结果、失败与日志

共同审查结果使用 `schema_version: 1`；执行元数据由 wrapper 写入，不信任模型声明退出状态、身份或用量。

| 字段 | 值/含义 |
|---|---|
| `execution_status` | `completed`、`conditions_missing`、`failed`、`timed_out`、`cancelled` |
| `review_outcome` | `findings`、`no_findings_in_scope`、`inconclusive` |
| `host` / `backend` | 可信宿主或未知、实际选择且启动的执行后端；启动前失败明确尚未启动 |
| `execution_environment` | 当前 native；CLI 核实版本分别记录，不猜 OS/宿主 |
| `cleanup` | confirmed/unverified 与必要原因；未核实不能报告成功 |
| `requested_model` / `observed_models` | 请求值与 CLI 证据分开；别名不猜具体版本，无证据为未知 |
| `scope` / `reviewed` / `unreviewed` | 固定基准和覆盖范围；未审条目带原因 |
| `findings` | 标题、相对原仓库的文件、核实后的行号、触发条件、影响、证据、建议、未验证内容 |
| `diagnostics` / `limitations` | 安全错误分类和验证限制；清理统一使用 `cleanup` |
| `usage` | 仅后端实报字段和明确口径；缺失不是零，成本不是账单 |

退出 0 不等于审查通过。完成且覆盖全范围才能给出 `no_findings_in_scope`；权限拒绝、轮次/预算耗尽、部分覆盖、无输出、缺少最终 result、`is_error`、解析失败及格式不符均不能给出该结论。已有发现可以保留，但部分完成的总判断为 `inconclusive`。
Claude错误终态先保留非空permission_denials列表的固定permission_denied事实，不回显工具输入；同时保留已知四类错误subtype的claude_error_*码和错误终态中已知assistant.error枚举的claude_api_*码，继续保留backend_result_error。未知/畸形字段不拼入诊断，errors/message原文不保存；不能从通用error_during_execution推断认证、额度或服务原因。成功终态不被先前已恢复的assistant错误改判失败；未新增重试或后端切换。v0.8.5 起，已知 assistant.error 事件含 Node TLS 证书不可信错误码（如 SELF_SIGNED_CERT_IN_CHAIN、UNABLE_TO_GET_ISSUER_CERT）时，另加固定码 claude_api_tls_untrusted；只匹配固定标记，原文仍不保存，沙箱信任库与网络边界不变。
两后端均按本次快照文件清单生成输出 schema：reviewed、unreviewed.path 和 findings.file 的枚举仅含原路径，不含 data/ 前缀、排除项或运行时路径。空快照不生成非法空枚举，并保持未完成。schema 须满足 OpenAI 严格结构化输出：每个节点都声明 type，对象禁止额外字段且 required 列全所有字段（v0.8.5 起由回归测试守住）。模型不得重复覆盖路径或同时声明已审/未审；采集阶段遗漏由 wrapper 合并，语义校验仍强制执行，schema 不证明审查真实。范围失败只保留固定细分类别，不回显任意路径或原文。已校验的唯一终结事件提供的模型/用量先于答案语义解析保存；错误、达限或坏覆盖仍失败，缺失元数据仍未知，不凭失败推断费用为零。

行号必须能在指定快照或 diff 的明确一侧核验；不匹配的定位标为未验证，不虚构行号。结构化 JSON 只证明格式，主会话仍需核实发现；任何结论不自动提供合并或交付授权。
CLI 缺失/版本不支持/隔离不可用及启动前条件不符：条件不足；启动后的认证、额度、服务或非零失败：执行失败。参数错误退出 64，缺失 CLI/运行依赖 127，其他失败/不完整非零，正常完成（包括发现问题）退出 0；超时 124，INT/TERM/HUP 130/143/129。保存原始后端退出码为元数据，不强行改成“无问题”。
预检各项最多 5 秒；复用执行默认/上限 540 秒及外层 600 秒。到期或取消先记录 wrapper 原因，再有界 TERM/KILL 清理本次 Claude、隔离运行时及辅助进程；不靠 srt 的退出码推断取消，因为其信号路径可能返回 0。
本次临时 launchd 任务在执行前证明独立 resource coalition 和单个可信 anchor。reviewer 与其 fork/setsid/double-fork、srt/代理共享这一内核归属。清理先用 PID 代际信号 STOP 所有 reviewer 成员，核对全员停止且枚举数量等于内核任务数，再 KILL 并核对计数。随后移除唯一任务并确认计数为零；没有完整归属/计数证明不能成功。取消保留原信号原因；anchor 自身有有限期限。不可捕获 SIGKILL 不承诺立即回收，系统 XPC 服务不是本次派生进程，不因同名去终止。临时任务不安装进用户 LaunchAgents，不写全局配置。
验证正常退出、忽略 TERM、父先退出、持有输出的后代和独立会话辅助进程；若存在未回收或无法归属的本次进程，明确报告，不宣称全部回收，不误杀其他会话。禁止自动重跑整项任务、切换后端或降低模型参数。
保存 `.answer`、`.report.json` 和过滤后的 `.log`，目录 0700、文件 0600、拒绝可写目录软链接。常规日志仅保留必要事件/错误分类，不落盘完整输入、思考、工具返回或认证原文；错误回显不直接倾倒原始 stderr。临时快照结束后清理，只保留必要哈希、范围及诊断。复用最近 50 组的有界保留策略，并给过程日志体积上限；日志失败不能变成审查无问题。

## 验证、边界及成功条件

**Always：** 先复现失败分支；免费测试用假 CLI 与临时 Git 项目；实际 OS 权限测试与模型测试分开；两宿主/双语入口一致；只在有证据时勾选。
**Ask first：** 安装/升级运行依赖、真实模型/额度调用、委托、提交/推送/发布/外部写入；隔离闸门不通过或改变已确认取舍时停下。
**Never：** 改用户全局配置、真实事项或历史归档；以 allowedTools/提示词/Plan 代替隔离；绕过权限；自动切后端/模型；把桩、清单或 Hook smoke 记为真实双向验收。

| 条款 | 成功标准与计划验证 |
|---|---|
| CR-01 | 默认及旧 Codex read/write 调用兼容；`test-review-backends.py` 与全部既有测试 |
| CR-02 | 显式 Claude 仅启动 Claude；非法/混用参数先失败，effort/write 拒绝，无 fallback/重跑 |
| CR-03 | 同一生产文件系统策略下，受控审查进程实际尝试写入源码、Git、配置和快照均被拒，指定临时目录可写；原版Claude初始化工具清单只含允许的只读及结果/结束工具；真实指定范围外Read拒权单列证据。模型主动Write事件未观察时明确标未验证，不以其不存在证明OS拒写。 |
| CR-04 | 三种范围固定、Git 采集不执行 helper、未提交改动/排除/链接正确；`test-review-context.py` |
| CR-05 | 正常、发现、拒权、达限、空/坏输出和失败准确分类；`test-claude-review.py` |
| CR-06 | 超时/取消及辅助进程回收真实验证；`test-review-lifecycle.py`，不能只检查主 PID；以Mac内核归属、实际超时/信号、detached/double-fork/父先退与无关进程存活证据验收；原版CLI异常记录按对应版本和不变性检查逐批报告。未观察的自然helper类型、历史未定根因及长期稳定性列为限制，不宣称已证明。失败或清理未知仍失败关闭。 |
| CR-07 | 可核实定位、覆盖缺口和限制保存；身份/用量缺失标未知；`review_result.py` 回归 |
| CR-08 | 凭据不进日志/诊断、只保留必要内容、目录权限/保留/清理验证 |
| CR-09 | 全部delegate公共与兼容入口在嵌套标记下于认证/运行时/模型启动前拒绝；原版Claude初始化不开放执行、派活或MCP工具，项目上下文隔离。入口标记是合作式防护，不能替代OS限制；真实模型递归企图未观察时明确标未验证。 |
| CR-10 | Codex 主会话→Mac Claude 与 Claude 主会话→本机 Codex 分别记录版本、实际后端、范围、权限、结果及限制 |

实施后免费总入口仍为 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`，新测试必须集成且不调用模型。原生清单校验为 `claude plugin validate .` 和 `claude plugin validate ./plugins/delegate`。
真实宿主验收另经授权，明确加载源码；执行固定小夹具并检查源码、Git 和配置未变。未满足认证、运行时或宿主条件时记录未验证；不同模型视角不保证更高准确率。

## 官方依据与历史路线（不作为当前部署要求）

源码/接口调研日期为 2026-10-09，原始版本及实际免费结果见 todo。官网会更新；实现时复核所需 CLI 和运行时的确切版本，而非沿用模型/额度印象。
官方入口：[程序化调用](https://code.claude.com/docs/en/headless)、[CLI](https://code.claude.com/docs/en/cli-reference)、[权限](https://code.claude.com/docs/en/permissions)、[认证](https://code.claude.com/docs/en/authentication)、[SDK](https://code.claude.com/docs/en/agent-sdk/overview)、[Bash 沙箱](https://code.claude.com/docs/en/sandboxing)、[模型/effort/fallback](https://code.claude.com/docs/en/model-config)、[Hook](https://code.claude.com/docs/en/hooks)、[srt](https://github.com/anthropics/sandbox-runtime)。
设计阶段 srt 缺失；后续用户单独批准专用临时安装。macOS 实际策略/权限套 13 项通过（含 5 unit），但独立会话辅助进程的超时/取消/父先退清理三项失败，当时首个实施 gate 未通过；旧组 runner 不接入 Claude，后续 Linux 修订为历史路线，新 Mac 运行器见 ADR-004。数字代理夹具不证明原版 Claude DNS/TLS/认证兼容；双向 live 均未验证。见[实际证据](../docs/verification/2026-10-09-claude-review.md)。工具沙箱拒绝嵌套 sandbox-exec 不代表宿主 OS 无法隔离，实际权限探针已在外层沙箱之外执行。
[ADR-003](../docs/decisions/ADR-003-review-process-boundary.md) 的专用 Linux VM/service 修订已获设计及免费实现批准，专用临时环境的 Linux/SSH 无模型边界已有 15/2 项实际通过；原版 CLI 的启动/配置/认证和工具权限仍未验收；不将平台决定当作支持声明。SDK/订阅官方表述存在适用范围差异，见 ADR；不复制/中介凭据、不承诺权益。严格边界无法达成时重新给出具体取舍，不能削弱 CR-03/06 继续。

Linux 的 srt 根 denyRead 保留 kernel 目录，因此必须额外掩蔽 `/sys`、`/run`；allowLocalBinding=false 不证明 Linux bind 被禁止。已验证 arm64 路线在 srt 内叠加 `review_network.py` 的 no_new_privs/seccomp bind/listen 禁止，失败停止，不给其他 ABI 假设支持。单次 service 的可信 ExecStopPost 在 reviewer 不可读写的 control 目录保存结束事实，再核对内核 cgroup 空状态；元数据过早回收不再只靠查询猜测。具体证明与仍未知的原版 CLI 条件见[Linux 实际记录](../docs/verification/2026-10-09-claude-review-linux.md)。这是 2026-10-09 的停点；后续 Checkpoint 1 批准与源码进展见下文。

## 可执行 JSON 示例与配置

2026-10-10 当前公共后端和 doctor 已切为 Mac 本机 CLI+srt+coalition，不再使用 guest 配置。旧 VM/SSH 批次及当时失败见历史证据；新 Mac 边界、原版无模型认证及公共假 CLI 记录见[本机记录](../docs/verification/2026-10-10-claude-review-mac-native.md)。真实 `-p` 的正常 Codex→Claude 审查已在第四批完成；实际禁用工具企图、认证刷新、动态管理配置和修复后的反向成功审查尚未验收。未发布、未更新安装副本。

精确范围示例（替换为实际业务 Git 根和工作目录；`scope.include` 不接受 `.` 或通配符）：

```json
{
  "schema_version": 1,
  "repository": "/absolute/business-repository",
  "working_directory": "/absolute/business-repository",
  "review_type": "diff",
  "scope": {"include": ["src/login"], "exclude": ["src/login/generated"]},
  "baseline": {"mode": "commits", "from": "main", "to": "HEAD"},
  "context_files": ["spec/login.md", "tasks/login/plan.md"],
  "acceptance_criteria": ["登录失败时不得绕过权限检查"],
  "uncommitted_changes": {"staged": false, "unstaged": false, "untracked": false},
  "allowed_tools": ["Read", "Glob", "Grep"],
  "stop_conditions": ["scope_complete", "permission_denied", "context_missing", "limit_reached", "input_changed"]
}
```

`module` 需要在 scope 添加 `module` 字符串并给文件边界；`paths` 直接给有限包含/排除路径。`commits` 固定两端 SHA，三种未提交标志都 false；快照取目标提交 blob，不用当前工作文件代替。`staged` 比较 HEAD→index，标志 true/false/false，快照取 index；`unstaged` 比较 index→工作区，标志 false/true/false，index 中既有变更仅是比较基准，不在 diff 中审查；`working-tree` 比较 HEAD→工作区，staged/unstaged 都 true，untracked 显式 true/false。三种非提交 baseline 只含 `mode`。所有模式记录实际 dirty 状态；不因省略选项纳入未跟踪文件。未跟踪文件按 git 的标准忽略规则取，含仓库内 `.gitignore`、`.git/info/exclude` 和默认全局忽略文件（`$XDG_CONFIG_HOME/git/ignore`，未设置时为 `~/.config/git/ignore`）；Git 探测仍不读全局配置，全局配置里自定义的 `core.excludesFile` 不生效。共同模式要求已有 HEAD，旧 Codex 自由文本仍支持未提交的初始仓库。

快照最多 256 普通文件、单文件 2 MiB、总 8 MiB；diff 最多 1 MiB，输入 JSON 64 KiB，任务最多 65536 字符。范围超过文件上限在启动前失败；二进制、链接、删除目标、读取失败记为未审。当前定位核验只支持目标快照行，不虚构已删除文件的旧侧行号。实际文件置于 `snapshot/data/<原路径>`，schema/控制/日志不进入源项目，两后端使用相同映射。初始工具事件最多 64 KiB，执行 stdout/stderr 有界 1 MiB；实际进程输出允许监测间隔内有限超量后终止，不能承诺瞬时磁盘硬配额。

本机依赖默认从 PATH 解析，已有独立安装可显式指定，不自动安装或修改配置：

```bash
DELEGATE_SRT_BIN=/absolute/existing/srt DELEGATE_NODE_BIN=/absolute/existing/node /bin/bash /path/to/delegate-plugin/plugins/delegate/scripts/delegate-exec.sh --backend claude-code --review-context /path/review.json --model sonnet "审查指定范围"
```

`DELEGATE_CLAUDE_BIN` 可指定已有 CLI；三个路径都须为已有可执行绝对路径，规范化后调用。旧 `DELEGATE_CLAUDE_GUEST_CONFIG` 明确报 guest_configuration_no_longer_supported，不静默转成本机执行。auth status 与审查在同一文件边界运行，只保存方法/提供商等安全字段。最新 2.1.296 的 claude.ai 认证预检通过；此前 2.1.295 的 authentication_missing 原因未定，不推断用户曾退出登录，也不把版本变化认定为修复根因。刷新及其他认证方式尚未验收；明确配置的 API key/token/provider/CLAUDE_CONFIG_DIR 环境首版拒绝，不自动回退登录；仅与官方默认端点等价的 `ANTHROPIC_BASE_URL` 放行（规则见“权限、上下文及认证”）。仅允许 api.anthropic.com:443、claude.ai:443、platform.claude.com:443；不开放审查网络工具或其他端点。管理配置无法核实即条件不足，不绕过策略。

模型 slug/别名按后端分开，明确拒绝另一模型族、opusplan 自动切换模式及非法语法；未知合法 slug 由选定 CLI 报错，不删参数重跑。Claude `--effort` 拒绝；Codex 允许 none/minimal/low/medium/high/xhigh，具体模型支持情况由其 CLI 明确失败。请求模型与实际模型分开；多模型证据或全 ID 不匹配使报告未完成。没有实际模型字段则未知，不根据别名猜版本。

共同报告包含 backend_started（审查调用，不含版本/认证探针）、核实 CLI 版本/安全认证方法；宿主无可靠证据为 unknown。Codex 仍用 cleanup_scope=existing_codex_process_group 并保留 detached 限制；Claude 用 cleanup_scope=kernel_coalition，身份/计数/清理未核实不得成功。

共同 answer/report/log 使用 0700/0600、最多 50 组，log 仅后端/状态/安全错误码，不含原始 stderr、认证、思考、任务或工具返回。清理已确认后删除快照/运行目录；清理未知时保留 0700 控制目录的可信控制事实；原始 stdin/stdout/stderr 均删除，retained_control 仅出现在私有报告，不倾倒原文。报告中的审查证据可能包含获准范围的数据，不是凭据转储。真实模型调用及 Git 交付另授权。

本机运行/doctor 使用 `/private/tmp` 下专用 0700 短目录，避免 Mac 默认长 TMPDIR 导致 srt 代理监听启动失败；最终 answer/report/log 仍使用共同私有产物目录。长 TMPDIR 实际假 CLI 回归先失败后通过。

2026-10-12 反向第二批对账：目标报告单次执行固定驱动，旧Claude进程因应用重启失效，宿主守卫在模型启动前拒绝；来源独立核实四文件/上下文/Git不变，marker/logs/result均无。本次不是成功审查，修复后的真实反向仍待验收。新的第三批仅完成当前固定身份的免费预览，尚未通信或调用模型，见[第三批预览](../docs/verification/2026-10-12-claude-review-mac-reverse-third-plan.md)。

## Codex 前置诊断与调用环境（2026-10-12）

共同审查保留 codex_preflight_failed，并增加可信阶段诊断：codex_cli_missing、codex_version_probe_failed、codex_version_probe_timeout/unavailable、codex_login_probe_timeout/unavailable、codex_login_status_failed 或 codex_login_method_unsupported。这些分类来自受控检查分支，不复制CLI原始stdout/stderr、凭据、路径或环境；backend_started=false、conditions_missing/inconclusive且保留未审范围。backend.check 的原两值返回、退出码及旧CLI文案兼容。版本无法运行不等同于用户未登录，也不能自动安装/升级或登录。启动后事件流含 error 或 turn.failed 事件时，codex_result_invalid 之外另加固定码 codex_turn_failed；错误内容含 invalid_json_schema 时再加 codex_output_schema_rejected（v0.8.5 起）。只匹配固定标记，错误原文不进报告或日志。

第三批真实Claude宿主祖先核验通过，但Node12作为其Bash环境的优先运行时令Codex版本探针失败，退出127、四文件未审、实际后端未启动；来源免费重现Node12失败及现有Node24.18.0成功，见[第三批结果](../docs/verification/2026-10-12-claude-review-mac-reverse-third-result.json)。新验收驱动只对本次子进程固定已有Node路径/版本/摘要，不修改用户PATH或配置，不在已批准失败批次中变更运行时或重跑。真正修复后反向仍未验收。

### 2026-10-13：本地安装目录与监督代码启动

launchd的解释器不一定能重新打开Documents中的插件安装文件。主会话仅将review_macos.py、review_result.py、claude_review.py三个受信监督/解析代码文件复制到既有私有control子目录（目录0700、文件0600），临时任务从该处启动。源码快照、凭据与其他用户数据不在这一步复制；reviewer仍被OS禁止读写整个control树，工具、网络、身份证明、期限与清理规则不变。不修改系统权限、全局配置或认证，不换后端。实际路径拒绝及零模型修复证据另记；不能由启动探针推导真实模型审查通过。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。

## 沙箱证书信任（S88，2026-11-18，已批准）

**状态：** 用户 2026-11-18 批准（原话「批准，开始实现」），任务见 [plan](../tasks/claude-review/plan.md) 的 S88 节，计划随 v0.8.6 发布。

### 问题

本机装了会解密 TLS 的网络软件（实测为 Cloudflare WARP，11-02 起）后，访问 `api.anthropic.com` 拿到的是该软件根证书签发的证书。这张根证书只在系统钥匙串里被设为信任。沙箱外的 claude 能用系统信任，正常；srt 沙箱里的 claude 读不到它，连接失败（`assistant.error=server_error`，正文含 `SELF_SIGNED_CERT_IN_CHAIN`），v0.8.5 起报 `claude_api_tls_untrusted`。用户已表示不改网络软件的免检设置，要 delegate 解决。

### 目标

Claude 审查后端在沙箱内信任的根证书，与本机用户在沙箱外**明确设为信任**的根证书一致；不多信，不要求用户手动操作，不改网络放行范围。

### 做法（方案 C：自动导出）

每次 Claude 后端审查（以及 `doctor --backend claude-code` 的同一预检）在启动 srt 前执行：

1. **读信任设置**：用 `/usr/bin/security trust-settings-export -d <文件>` 导出管理员域、`/usr/bin/security trust-settings-export <文件>` 导出用户域，输出写在本次私有控制目录。每条命令有期限（5 秒）。只读，不改钥匙串或信任设置。
2. **选证书**：按 SHA-1 收集"明确信任"的证书。一条记录满足以下任一条件才入选：
   - `trustSettings` 为空数组（无条件信任）；
   - 含一项 `kSecTrustSettingsResult` 为 1（TrustRoot）或 2（TrustAsRoot），且策略名缺省或为 `sslServer`、`basicX509`。

   含 `kSecTrustSettingsResult` 为 3（Deny）且策略名缺省或为 `sslServer` 的记录一律排除。只限定于其他策略（如代码签名）的信任不入选。
3. **取证书本体**：导出文件只有 SHA-1，没有证书。用 `/usr/bin/security find-certificate -a -Z -p` 读取 `/Library/Keychains/System.keychain` 和当前用户的 `login.keychain-db`，对每张证书**自行重算 DER 的 SHA-1**，只保留与第 2 步集合一致的证书。找不到的哈希忽略。
4. **写文件**：入选证书写成 PEM，放在本次运行专用的只读目录（目录 0700、文件 0400，由 delegate 创建，不在 writable 目录内）。最多 64 张、文件最多 1 MiB，超限视为导出失败。
5. **交给沙箱**：把该文件加入 srt 的可读路径（不可写），在交给 claude 的固定环境中设置 `NODE_EXTRA_CA_CERTS=<该文件>`。Node 对此变量是**追加**信任，claude 自带的公共根证书照旧生效。工具层照常对该路径加 Read deny，reviewer 读不到。
6. **清理**：随本次控制目录一起删除，不缓存、不跨运行复用。

**失败处理：** 任一步失败、超时或一张都没选到时，**不设置**该环境变量，审查照常运行，与 v0.8.5 行为一致；报告加非致命诊断 `system_trust_export_unavailable`（只在导出失败时加，选到 0 张不算失败）。若随后仍遇证书问题，照旧报 `claude_api_tls_untrusted`。

**doctor：** `doctor --backend claude-code` 显示本次导出了几张证书或 `system_trust_export_unavailable`，不显示证书名称、哈希或路径；doctor 仍不联网。

### 边界

**Always：** 只信任沙箱外已被管理员或用户明确设为信任的证书；每张证书自行重算哈希核对；文件只读、私有、用后删除；Codex 后端与 run 不受影响。
**Ask first：** 扩大到系统内置根证书以外的其他来源、改网络放行域名、真实模型验收（需在 TLS 解密网络下跑一次 Claude 后端审查，用 Claude 额度）。
**Never：** 打开 srt 的 `enableWeakerNetworkIsolation`（放开 trustd，srt 官方标明有外泄风险）；读取或复制私钥；写钥匙串或信任设置；用 `SSL_CERT_FILE` 等变量**替换**信任库；继承调用方环境里的 `NODE_EXTRA_CA_CERTS`（调用方变量仍不进入沙箱，避免被任意文件扩大信任）；把证书名称、哈希或路径写进报告或日志。

### 成功条件

| 条款 | 成功标准与计划验证 |
|---|---|
| CR-11 | 选证规则：用固定信任设置夹具覆盖无条件信任、sslServer/basicX509 信任、Deny、只限其他策略、未指定结果五类，入选集合正确；哈希不符或钥匙串里找不到的证书不入选 |
| CR-12 | 文件与边界：目录 0700、文件 0400；路径在 srt 可读列表、不在可写列表；工具层 Read deny 覆盖该路径；固定环境含 `NODE_EXTRA_CA_CERTS` 且只指向该文件；调用方同名变量不被继承；运行结束后文件已删除 |
| CR-13 | 失败关闭为"不加信任"：`security` 缺失、非零退出、超时、输出非法、超过 64 张或 1 MiB 时不设变量、报 `system_trust_export_unavailable`，审查照常进行；报告和日志里没有证书名称、哈希或路径 |
| CR-14 | 真实验收（另经授权）：在 TLS 解密网络下，Claude 后端审查固定小夹具 `completed`，源码、Git、配置不变；同一网络下关闭本功能复现原失败作对照 |

免费部分全部用假 `security` 命令和临时目录测试，不读真实钥匙串、不调用模型，并入 `scripts/validate.sh`。

### 待确认

1. 入选证书不检查是否为 CA 证书（basicConstraints），以系统信任设置为准；被单独设为信任的叶子证书也会入选。我认为可以接受，因为沙箱外本来就信任它们。
2. 本机现有 3 张明确信任的证书：Cloudflare Gateway CA 和两张 mkcert 本地开发证书，都会被导入沙箱。

## 审查失败定位诊断（2026-11-25，已批准）

**状态：** 用户 2026-11-25 批准（原话「批准」），任务见 [plan](../tasks/claude-review/plan.md) 的「审查失败定位诊断」节。只加固定诊断码，不改审查行为、退出码、报告字段或沙箱边界。

### 问题

autopr-design 2026-11-24 在本机连续三次运行 `review --backend claude-code`，都失败了。三次都清理确认（`cleanup=confirmed`），但现有诊断码不足以找到原因：

- **第 1 次**：`timed_out` 加 `probe_timed_out`，`backend_started=false`。三个探测（`--version`、`--help`、`auth status`）共用这一个码，看不出是哪一个超了 5 秒时限。
- **第 2、3 次**：`failed` 加 `stream_empty_or_oversized`，`backend_started=true`，退出码 1。从代码可以推出两点：
  1. 子进程运行期间，监督进程在 stdout 里读到过合法的启动事件。否则会记 `initial_output_empty` 或 `tool_boundary_unverified`。
  2. stdout 没有超过 1 MiB。否则会记 `output_limit`。

  但控制进程最后读同一个 stdout 文件，得到的是空。另外，原版 CLI 以非零码退出了。现有报告分不清三种情况：文件不见了、文件读到的比写入的少、原版 CLI 自己报错退出。

### 目标

下次再出同样的失败时，报告里的固定诊断码能直接指出：哪个探测超时；stdout 是没找到还是读少了；原版 CLI 是不是非零退出、有没有写 stderr。

### 做法

1. **探测阶段码**：探测本身失败时（`probe_timed_out`、`probe_cancelled`、`probe_failed`、`probe_unavailable`、`probe_cleanup_unverified`、`probe_output_invalid`），在原码之后追加一个阶段码：`probe_stage_version`、`probe_stage_help` 或 `probe_stage_auth`。版本不符、能力缺失、认证类等探测成功后的判定失败不加阶段码。现有码和状态映射都不变。
2. **监督进程记录字节数**：监督进程（`review_macos.py` 的 anchor）写结束记录时，加两个整数，`stdout_bytes` 和 `stderr_bytes`，取自文件大小。这两个数只在私有控制目录内传递，不进报告，也不进日志。
3. **控制进程核对**：控制进程读 stdout 后，与监督进程记录的字节数比较：
   - stdout 文件不存在，记 `stream_file_missing`；
   - 读到的字节数少于记录值（含读到 0），记 `stream_read_short`。
4. **原版 CLI 退出情况**：监督进程已有 `launcher_exit_code`，现在不进报告。改为在审查未完成时（`execution_status` 不是 `completed`）追加：
   - 仅当 `execution_status` 为 `failed` 且退出码非零时记固定码 `backend_exit_nonzero`（超时、取消时子进程由 delegate 中止，退出码不反映原版 CLI 自身情况）；
   - `stderr_bytes` 大于 0 时记 `backend_stderr_nonempty`。

   审查完成时不加这两个码，以免原版 CLI 正常写出的警告干扰成功报告。退出码数值和 stderr 内容都不进报告或日志。

第 2～4 项的码由 `claude_review.execute` 在报告生成后追加，不经过监督进程的诊断列表，所以不会把完成的审查改判为失败。以上都是追加的诊断码。原有的 `stream_empty_or_oversized` 等码照旧保留；`execution_status`、`review_outcome`、退出码和报告字段都不变。按 integration-interface，`diagnostics` 属于诊断信息，使用方不应依赖，所以接口版本仍是 1.7。

### 边界

**Always：**
- 诊断码只用固定标识符；
- 字节数和退出码只用来判定写哪个码；
- 新增测试先写，并确认它失败；
- Codex 后端和 run 不受影响。

**Ask first：**
- 改探测时限；
- 用 Claude 额度实跑复现；
- 把字节数或退出码作为报告字段对外输出（这要升接口版本）。

**Never：**
- 把 stdout、stderr、提示词或认证内容写进报告、日志或控制目录以外的地方；
- 放宽沙箱或网络边界；
- 增加重试或后端切换。

### 成功条件

| 条款 | 成功标准与计划验证 |
|---|---|
| CR-15 | 探测阶段码：用假调用器让三个探测分别超时、失败、取消、不可用、清理未确认或输出超限，报告各带对应的 `probe_stage_*`；探测成功后的判定失败不带；原有码、`execution_status`、`backend_started=false` 不变 |
| CR-16 | 流丢失定位：用假结束记录和临时目录，分别构造 stdout 文件缺失、读到的比记录少、读到的和记录一致三种情况。前两种分别报 `stream_file_missing`、`stream_read_short`，第三种不报；原有 `stream_empty_or_oversized` 照旧 |
| CR-17 | 退出情况：MacBoundary 测试夹具跑一个写 stderr 并以非零码退出的假后端，结束记录里的 `stderr_bytes` 大于 0、`launcher_exit_code` 非零；再用假调用器验证 `failed` 时报告含 `backend_exit_nonzero` 和 `backend_stderr_nonempty`，超时、取消时只含后者；正常退出、不写 stderr 时两码都不出现；审查完成但写了 stderr 时也不出现；报告和日志里没有 stderr 原文或退出码数值 |

免费部分全部用假调用器、临时目录和现有 MacBoundary 测试夹具，不调用模型，并入 `scripts/validate.sh`。真实复现由 autopr-design 在补丁版发布后自愿再跑；本规格不要求用 Claude 额度。

### 待确认

1. 已定（2026-11-25）：探测时限保持 5 秒，看到阶段码后再决定是否调整。（2026-11-26 实跑发现 5 秒会偶发误判，修订见「Claude Code 探测期限放宽」一节。）
2. 已定（2026-11-25，代码审查建议 2、3，用户原话「2、3 都按推荐改」）：`backend_exit_nonzero` 只在 `failed` 时追加；阶段码覆盖探测本身产生的全部六个失败码。

## 监督代码暂存缺模块（2026-11-25，已批准）

**状态：** 用户 2026-11-25 批准（原话「批准」），任务见 [plan](../tasks/claude-review/plan.md) 的「监督代码暂存缺模块」节。修复 claude-code 后端在 macOS 上自 v0.10.0 起必然失败的问题；不改沙箱边界、报告字段和接口版本（仍为 1.7）。

### 问题

macOS 原生路径的监督进程（`review_macos.py` 的 anchor）不从插件目录运行，而是从私有控制目录里暂存的三个文件运行：`review_macos.py`、`review_result.py`、`claude_review.py`（见上文「2026-10-13：本地安装目录与监督代码启动」）。

监督进程第一次检查启动事件时会导入 `review_result`：
- v0.10.0 起，`review_result.py` 顶部导入了 `review_recheck`；
- v0.12.0 起，又导入了 `review_context`，后者还要导入 `review_fingerprint`、`review_guest`。

这些模块都没有暂存，导入时报 `ModuleNotFoundError`。这个异常不在监督进程捕获的类型里，于是收尾段直接清理掉刚启动的原版 CLI：
- 结果是 `execution_status=failed`，诊断里只有 `stream_empty_or_oversized`，加上 v0.12.2 起的 `backend_exit_nonzero`；
- stdout 为空，审查 0 个文件。

autopr-design 2026-11-24、25 的四次失败与此一致。只用这三个暂存文件在隔离目录里导入 `review_result`，本机复现了 `ModuleNotFoundError: No module named 'review_context'`。

访客路径（`review_transport.py` 的 `GUEST_FILES`）也一样：清单里缺 `review_fingerprint.py`、`review_recheck.py`，导入 `review_result` 时同样报错。

### 目标

1. 暂存的监督代码能独立导入并运行，不依赖未暂存的模块。
2. 以后再有人加导入，免费测试会直接失败，不会等到真实审查才暴露。
3. 监督进程遇到意料之外的异常时，留下固定诊断码，不再是空诊断。

### 做法

1. **启动检查独立成模块**：
   - 新建 `review_init.py`，只依赖标准库和已暂存的 `claude_review.unique_object`。
   - 把 `ResultError`、`init_error`、`init_valid`、`read_init` 原样移进去。
   - `review_result` 从 `review_init` 导入这四个名字，原有调用方式和异常类不变，所以 `review_result.ResultError` 仍是同一个类。
   - 监督进程改为从 `review_init` 导入。
   - 暂存清单改为 `review_macos.py`、`review_init.py`、`claude_review.py`，不再暂存 `review_result.py`。
2. **访客清单补齐**：`GUEST_FILES` 加入 `review_fingerprint.py`、`review_recheck.py`，访客入口和 `review_service` 的导入闭包完整。
3. **兜底诊断**：监督进程在启动原版 CLI 之后遇到意料之外的异常时：
   - 记固定码 `anchor_internal_error`，状态按失败；
   - 清理照常进行；
   - 异常原文不进结束记录、报告或日志。
4. **导入闭包回归测试**：
   - 新测试把每份暂存清单（Mac 监督、访客）拷到隔离临时目录；
   - 用 `python3 -I -B` 导入各自的入口模块和运行中会延迟导入的模块（Mac：`review_macos`、`review_init`；访客：`review_guest_entry`、`review_service`、`review_result`）；
   - 任一导入失败，测试就失败。并入 `scripts/validate.sh`。

### 边界

**Always：**
- 移动的函数逻辑不变，原有 `test-review-result.py` 全部通过；
- 新测试先写，并确认它在当前代码上失败；
- Codex 后端和 run 不受影响。

**Ask first：**
- 扩大暂存范围到插件目录以外；
- 用 Claude 额度做真实验收（CR-21）。

**Never：**
- 让监督进程改为从插件安装目录导入代码（launchd 解释器可能读不了 Documents，见 2026-10-13 一节）；
- 放宽 reviewer 对控制目录的读写禁止；
- 把异常原文写进报告或日志。

### 成功条件

| 条款 | 成功标准与计划验证 |
|---|---|
| CR-18 | 导入闭包：在隔离目录里只放暂存清单的文件，Mac 监督与访客两份清单的入口及延迟导入模块都能导入；在修复前的代码上同一测试失败 |
| CR-19 | 行为不变：`review_result` 仍导出 `ResultError`、`init_error`、`init_valid`、`read_init`，且与 `review_init` 中的是同一对象；原有结果与启动检查测试全部通过 |
| CR-20 | 兜底诊断：MacBoundary 测试夹具让监督进程在启动子进程后抛出意料之外的异常，结束记录含 `anchor_internal_error`、状态为 failed、清理确认；记录里没有异常原文 |
| CR-21 | 真实验收（另经授权）：发版后由 autopr-design 用安装版对同一范围复跑，`execution_status=completed` |

免费部分用临时目录、假调用器和现有 MacBoundary 夹具，不调用模型。需要 `--srt` 的真实夹具由用户在终端里运行。

### 待确认

1. 访客路径本机没有现成的 Lima 环境可以实跑，这次只做导入闭包测试。

## Claude Code 探测期限放宽（2026-11-26，已批准）

**状态：** 用户 2026-11-26 批准，原话「批准；Q1 15 秒；Q2 不重试」。来源：用户 2026-11-26 让本会话实跑 s110 用法草案 M1（原话「跑 s110 的 M1」），U2 不稳定，用户判定不通过并要求补任务（原话「不通过，补探测期限任务」）；记录见 [reviewer-selection todo](../tasks/reviewer-selection/todo.md) 的「M1 实跑未通过」节。本节修订上文「审查失败定位诊断」待确认第 1 条（探测时限保持 5 秒）。

### 问题

`--backend auto` 和 `review_doctor.py --reviewers` 判断 Claude Code 能不能用，靠的是 `reviewer_select.claude_check`：建临时目录、检查隔离运行时，再依次跑三个探测（`--version`、`--help`、`auth status`）。每个探测的期限写死为 5 秒（`claude_review._probe` 的 `deadline=5`）。

2026-11-26 用安装版 0.12.3 实跑：
- 去掉 Codex 后，同一条 `review --backend auto` 命令跑 3 次，前 2 次退出 127，诊断分别是 `probe_timed_out`、`probe_cleanup_unverified`，都被判成「两家都不可用」；第 3 次才回退到 Claude Code 跑完。
- 直接调 `claude_check` 6 次，整体耗时在 4～19 秒之间，其中 1 次 `probe_timed_out`。
- 之后分段计时 18 次都只要约 2 秒，每个探测 0.3～0.6 秒，没能复现慢的那几次。

所以平时远低于 5 秒，但 Claude CLI 启动偶尔会被卡住几秒到十几秒，一碰到探测就超时。只装了 Claude Code 的用户会因此被误判为「未审」，doctor 列表也会时好时坏。另外，auto 选择的报告只给 `probe_timed_out`，不带上文第 1 项的 `probe_stage_*`，看不出是哪个探测慢。

### 目标

Claude CLI 偶发的慢启动不再让 Claude Code 被误判为不可用；探测仍然有期限，真卡住时照旧判为不可用；下次再出问题时，auto 选择的报告能指出是哪个探测。

### 做法

1. **期限放宽**：三个探测的期限都从 5 秒改为 15 秒（三个加起来最坏 45 秒）。到期后的清理（有界 TERM/KILL）、诊断码和状态映射都不变。审查本身的 540 秒和外层 600 秒期限不变。
2. **不加重试**：维持上文边界里「增加重试」不做。探测超时一次就判为不可用。
3. **auto 选择带阶段码**：`claude_check` 因探测本身失败而判为不可用时，`--backend auto` 的「未审」报告在 `claude_cli_*`／`probe_*` 码之后同样追加 `probe_stage_version`、`probe_stage_help` 或 `probe_stage_auth`，规则同上文第 1 项。`doctor --reviewers` 的列表仍只显示主码，不改输出格式。

以上不改报告字段、退出码和接口版本（仍为 1.7）；`diagnostics` 只是追加固定码。

### 边界

**Always：**
- 期限只改这一个常量，三个探测共用；
- 新增测试先写，并确认它失败；
- Codex 后端和 run 不受影响。

**Ask first：**
- 期限取 15 秒以外的值；
- 用模型额度实跑（Task 7 发版后重跑 U2 已列为 gate）。

**Never：**
- 增加重试或后端切换；
- 去掉期限或改成不限时；
- 放宽沙箱或网络边界。

### 成功条件

| 条款 | 成功标准与计划验证 |
|---|---|
| CR-22 | 探测期限：用假调用器记录 `preflight` 传给三个探测的期限，都是 15；假调用器返回 `timed_out` 时仍报 `probe_timed_out` 加对应阶段码，`backend_started=false` |
| CR-23 | auto 选择带阶段码：用假的 `claude_check` 失败（探测超时、清理未确认）走完 `--backend auto` 的「未审」路径，报告 `diagnostics` 含 `no_reviewer_available`、原码和对应的 `probe_stage_*`；探测成功后的判定失败（如 `authentication_missing`）不带阶段码 |
| CR-24 | 真实复验：发版后用安装版去掉 Codex，同一条 `review --backend auto` 命令连续跑 3 次，都回退到 Claude Code 并完成（reviewer-selection Task 7，须用户授权额度） |

CR-22、CR-23 用假调用器，不调用模型，并入 `scripts/validate.sh`。

### 待确认

1. 已定（2026-11-26）：15 秒。理由：实测平时约 0.5 秒，慢的那几次整个检查在 9～19 秒之间，15 秒能覆盖大多数偶发卡顿，又不会让真卡住时等太久（最坏 45 秒）。备选 10 秒（最坏 30 秒，覆盖面小一些）或 30 秒（最坏 90 秒，doctor 列表可能要等一分半）。
2. 已定（2026-11-26）：不加重试，维持原边界。理由：重试会让真卡住时的等待翻倍，也会掩盖 CLI 的真实问题；放宽期限已经能覆盖偶发慢启动。

## Claude 登录令牌过期的恢复提示（2026-11-26，已批准）

**状态：** 用户 2026-11-26 批准，原话「批准；Q1 A；Q2 A」；审查后体检说明原文的修订同日经用户复审，原话「批准修订，提交开 PR」。来源：ecosystem-lead #23145，称用户原话「先让 delegate 修令牌过期的问题」；即 delegate 盘点（2026-11-26）第四节缺陷 1、第六节缺口 1。复现记录见下。

### 问题

`review --backend claude-code` 在 Claude 登录令牌过期后必然失败，失败时只给固定码，使用方不知道怎么恢复，只能退回子代理：

- autopilot-hub 11-26 两次失败（#23130），同一会话早些时候成功过 5 次。
- 本会话 11-26 02:28（UTC）用安装版 0.12.4 复现：退出 1，`failed`，诊断 `claude_api_authentication_failed`、`backend_result_error`、`backend_exit_nonzero`，`backend_started=true`（CLI 已启动，是 API 拒绝了凭据）。
- 02:30 在沙箱外运行一次 `claude -p "ok"`，02:31 同一条命令复验成功（`completed`）。

体检看不出来：
- `review_doctor.py --backend claude-code` 和 `claude auth status` 在失败前后都显示已登录（claude.ai／firstParty）。
- `claude auth status --json` 里唯一和过期有关的是 `loginExpiresAt`。实测它是整个登录的过期时间（2026-12-17），02:30 刷新后没有变，所以不代表短期访问令牌是否有效。
- 三个预检探测（`--version`、`--help`、`auth status`）都不访问 API。

原因（推断，未直接证实）：审查时沙箱只读挂载 `~/.claude`、`~/.claude.json`、`~/Library/Keychains`，用户家目录禁止写入（`review_native.py`、`review_isolation.py`）。访问令牌过期后，沙箱里的 CLI 无法把刷新结果写回，只能用旧令牌请求。delegate 不读钥匙串，所以无法从本机直接证实令牌状态。

### 目标

令牌过期时，调用方从报告和 stderr 都能拿到一句可执行、可原样转告用户的恢复提示；体检不再让人误以为「已登录」就等于审查能用。

### 做法

1. **恢复码与提示**：审查报告的 `diagnostics` 含 `claude_api_authentication_failed` 时，再追加固定码 `claude_login_refresh_required`；同时在 stderr 打一行固定的话：

   ```text
   delegate: Claude 登录令牌可能已过期：请在沙箱外的终端运行一次 `claude`（例如 claude -p "ok"）刷新登录后重试；仍失败时运行 claude /login 重新登录。
   ```

   这行只在出现这个码时打印，不含任何凭据、账号或错误原文。`--backend auto` 选中 Claude Code 后失败时同样适用。
2. **体检说明**：`review_doctor.py --backend claude-code` 在认证检查通过时，加一行固定说明（2026-11-26 审查后修订：原写「按上面的提示刷新」，体检输出里没有上文，改为写全刷新步骤，与代码、测试逐字一致）：

   ```text
   已登录只说明本机存有凭据，不代表登录令牌仍然有效；审查若报 claude_api_authentication_failed，请在沙箱外的终端运行一次 `claude`（例如 claude -p "ok"）刷新登录后重试；仍失败时运行 claude /login 重新登录。
   ```

   `doctor --reviewers` 的列表和 JSON 不改。
3. **不验证令牌**：体检不尝试验证令牌有效性。实测证据：`auth status` 给不出访问令牌状态（见上）；能证明令牌有效的办法都要调用 API（花额度）或读凭据（越界），本规格都不做。

报告字段、退出码和接口版本（1.7）不变；`diagnostics` 只是追加固定码。

### 边界

**Always：**
- 提示文字固定，测试逐字核对；
- 新增测试先写，并确认它失败；
- Codex 后端和 run 不受影响。

**Ask first：**
- 体检里加任何会花额度的真实调用；
- 改动沙箱的读写或网络边界（例如让 CLI 能写回刷新后的令牌）。

**Never：**
- 替用户刷新令牌、读写凭据文件或钥匙串、改全局配置；
- 把认证错误原文、账号、邮箱写进报告、日志或 stderr。

### 成功条件

| 条款 | 成功标准与计划验证 |
|---|---|
| CR-25 | 恢复码：用假调用器构造带 `error: authentication_failed` 的 assistant 事件，报告 `diagnostics` 依次含 `claude_api_authentication_failed`、`claude_login_refresh_required`；其他 `claude_api_*` 错误（如 `rate_limit`）不追加该码 |
| CR-26 | stderr 提示：公开入口跑上述失败时，stderr 恰好出现一次固定提示行；无该码时不出现；stdout 仍只有报告 JSON |
| CR-27 | 体检说明：`review_doctor.py --backend claude-code` 认证通过时输出固定说明行；`--reviewers` 的文字和 JSON 不变 |
| CR-28 | 真实复验：发版后在令牌确实过期时用安装版跑一次，报告与 stderr 出现提示，照提示刷新后恢复（无法按需制造过期，遇到时记录；本条不阻塞合并） |

CR-25～27 用假调用器和现有夹具，不调用模型，并入 `scripts/validate.sh`。

### 待确认

1. 已定（2026-11-26）：恢复码名用 `claude_login_refresh_required`。理由：说的是该做什么，调用方可以按码分支。备选 `claude_token_possibly_expired`（说的是可能的原因）。
2. 已定（2026-11-26）：提示只放 stderr 和固定码，不写进 `limitations`。理由：它目前是固定的能力限制说明，混进单次失败的提示会让「报告字段不变」不成立；调用方已有固定码可判。

## 附录：历史接续记录（保留当时状态，不覆盖当前结论）

**2026-10-14 S5/S6批次：** Task9l诊断修复已由S5同步两宿主，16项读回/48项安装结果回归通过；Task9n标准工作区免费157/53/19通过。S6诊断接续取得指定快照外Read工具拒权及精确目标归属，回收confirmed；审查1/4、failed/inconclusive，Task2/6/8完整条件仍未完成。S4及原S6认证失败根因未知，不追认修复。见[接续结果](../docs/verification/2026-10-14-delegate-s6-diagnostic-followup-result.md)。

**2026-10-13修复批次：** S2固定源码普通双向审查及四入口显示已通过；随后CMD-001/CMD-002/DOC-001三批修复免费总148/53/19通过，已同步两宿主正常安装并通过16项无模型读回，尚未真实模型复验或本批会话重载，完整安全条件仍未完成。见[最新修复结果](../docs/verification/2026-10-13-delegate-command-fixes-result.md)。下方早期日期状态保留当时证据，不代表新增修复已live验证。

日期：2026-10-13。状态：当前Mac功能代码和免费验证已完成；两方向普通真实四文件审查各有成功记录。最新Claude主会话→Codex0.162.1/Node24.18.0完成4/4，核心缺陷核对通过、输入/Git/源码未变，见[收束证据](../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-success.md)。先前Codex→Claude2.1.296仅覆盖其固定历史源码/版本。新斜杠宿主体验、主动模型写入/递归企图、认证刷新和异常helper仍未验收；完整验收未完成。最新严格边界认证通过，此前失败原因未定。目标仅当前Mac；VM为历史证据。安装、新增模型调用、提交、推送、发布继续分别授权。 2026-10-12临时Codex源码安装成功，但原生命令迁移仅生成review/run/doctor，help缺失；已修正4000字节超限并由单次原生CLI安装核对四入口转换产物通过；桌面/Claude新命令体验仍待验，见[复验结果](../docs/verification/2026-10-13-delegate-source-load-fixed-result.md)。

2026-10-13本机已按独立批准切换正常Codex到本地源码并重装，4skill/61文件匹配、仅SessionStart；Claude2.1.296实际按现有user配置原地加载4命令，无本批安装/设置变更；安装的预检函数核实已有CLI/claude.ai认证及回收（收紧为禁网）。SRT仍须按次指定临时绝对路径，既有主会话UI和模型/额度未验。[本批证据](../docs/verification/2026-10-13-delegate-local-activation-result.md)不追认完整Task2/6/8。
