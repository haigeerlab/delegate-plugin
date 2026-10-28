# 规格：claude-review（可选 Claude Code 审查后端）

简体中文 | [English](../docs/en/SPEC-claude-review.md)

**审批方式（2026-10-25）：** Codex 后端审查调用固定 `-c approval_policy="never"`，见 [run-resume](run-resume.md) 修订记录 R2；其余审查合同不变。

**当前发行（2026-10-28）：** v0.8.2 是补丁版，只改 `/delegate:run` 的命令说明、行为不变，接口仍为 1.3；本模块的审查合同、参数与报告格式不变，见[版本说明](../docs/releases/v0.8.2.md)；免费验证 328 Python / 53 shell / 19 eval。

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

本批接口设计经用户“继续”确认；新源斜杠入口为 `/delegate:review`、`/delegate:run`、`/delegate:doctor`、`/delegate:help`。review 两后端都只读；run 保留既有 Codex 自由文本及显式 write，Claude run 拒绝。旧 `/delegate:delegate` 源命令移除；旧 codex-exec.sh 和 delegate-exec.sh 无子命令调用继续有效。两宿主从同一源命令使用公共入口，宿主生成缓存不随源码自动更新，四入口显示与 S7 菜单实际公共脚本/dry-run 已验收；无差错自动 UI 输入仍未验证。

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
Claude错误终态先保留非空permission_denials列表的固定permission_denied事实，不回显工具输入；同时保留已知四类错误subtype的claude_error_*码和错误终态中已知assistant.error枚举的claude_api_*码，继续保留backend_result_error。未知/畸形字段不拼入诊断，errors/message原文不保存；不能从通用error_during_execution推断认证、额度或服务原因。成功终态不被先前已恢复的assistant错误改判失败；未新增重试或后端切换。
两后端均按本次快照文件清单生成输出 schema：reviewed、unreviewed.path 和 findings.file 的枚举仅含原路径，不含 data/ 前缀、排除项或运行时路径。空快照不生成非法空枚举，并保持未完成。模型不得重复覆盖路径或同时声明已审/未审；采集阶段遗漏由 wrapper 合并，语义校验仍强制执行，schema 不证明审查真实。范围失败只保留固定细分类别，不回显任意路径或原文。已校验的唯一终结事件提供的模型/用量先于答案语义解析保存；错误、达限或坏覆盖仍失败，缺失元数据仍未知，不凭失败推断费用为零。

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

`module` 需要在 scope 添加 `module` 字符串并给文件边界；`paths` 直接给有限包含/排除路径。`commits` 固定两端 SHA，三种未提交标志都 false；快照取目标提交 blob，不用当前工作文件代替。`staged` 比较 HEAD→index，标志 true/false/false，快照取 index；`unstaged` 比较 index→工作区，标志 false/true/false，index 中既有变更仅是比较基准，不在 diff 中审查；`working-tree` 比较 HEAD→工作区，staged/unstaged 都 true，untracked 显式 true/false。三种非提交 baseline 只含 `mode`。所有模式记录实际 dirty 状态；不因省略选项纳入未跟踪文件。共同模式要求已有 HEAD，旧 Codex 自由文本仍支持未提交的初始仓库。

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

共同审查保留 codex_preflight_failed，并增加可信阶段诊断：codex_cli_missing、codex_version_probe_failed、codex_version_probe_timeout/unavailable、codex_login_probe_timeout/unavailable、codex_login_status_failed 或 codex_login_method_unsupported。这些分类来自受控检查分支，不复制CLI原始stdout/stderr、凭据、路径或环境；backend_started=false、conditions_missing/inconclusive且保留未审范围。backend.check 的原两值返回、退出码及旧CLI文案兼容。版本无法运行不等同于用户未登录，也不能自动安装/升级或登录。

第三批真实Claude宿主祖先核验通过，但Node12作为其Bash环境的优先运行时令Codex版本探针失败，退出127、四文件未审、实际后端未启动；来源免费重现Node12失败及现有Node24.18.0成功，见[第三批结果](../docs/verification/2026-10-12-claude-review-mac-reverse-third-result.json)。新验收驱动只对本次子进程固定已有Node路径/版本/摘要，不修改用户PATH或配置，不在已批准失败批次中变更运行时或重跑。真正修复后反向仍未验收。

### 2026-10-13：本地安装目录与监督代码启动

launchd的解释器不一定能重新打开Documents中的插件安装文件。主会话仅将review_macos.py、review_result.py、claude_review.py三个受信监督/解析代码文件复制到既有私有control子目录（目录0700、文件0600），临时任务从该处启动。源码快照、凭据与其他用户数据不在这一步复制；reviewer仍被OS禁止读写整个control树，工具、网络、身份证明、期限与清理规则不变。不修改系统权限、全局配置或认证，不换后端。实际路径拒绝及零模型修复证据另记；不能由启动探针推导真实模型审查通过。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。

## 附录：历史接续记录（保留当时状态，不覆盖当前结论）

**2026-10-14 S5/S6批次：** Task9l诊断修复已由S5同步两宿主，16项读回/48项安装结果回归通过；Task9n标准工作区免费157/53/19通过。S6诊断接续取得指定快照外Read工具拒权及精确目标归属，回收confirmed；审查1/4、failed/inconclusive，Task2/6/8完整条件仍未完成。S4及原S6认证失败根因未知，不追认修复。见[接续结果](../docs/verification/2026-10-14-delegate-s6-diagnostic-followup-result.md)。

**2026-10-13修复批次：** S2固定源码普通双向审查及四入口显示已通过；随后CMD-001/CMD-002/DOC-001三批修复免费总148/53/19通过，已同步两宿主正常安装并通过16项无模型读回，尚未真实模型复验或本批会话重载，完整安全条件仍未完成。见[最新修复结果](../docs/verification/2026-10-13-delegate-command-fixes-result.md)。下方早期日期状态保留当时证据，不代表新增修复已live验证。

日期：2026-10-13。状态：当前Mac功能代码和免费验证已完成；两方向普通真实四文件审查各有成功记录。最新Claude主会话→Codex0.162.1/Node24.18.0完成4/4，核心缺陷核对通过、输入/Git/源码未变，见[收束证据](../docs/verification/2026-10-12-claude-review-mac-reverse-fourth-success.md)。先前Codex→Claude2.1.296仅覆盖其固定历史源码/版本。新斜杠宿主体验、主动模型写入/递归企图、认证刷新和异常helper仍未验收；完整验收未完成。最新严格边界认证通过，此前失败原因未定。目标仅当前Mac；VM为历史证据。安装、新增模型调用、提交、推送、发布继续分别授权。 2026-10-12临时Codex源码安装成功，但原生命令迁移仅生成review/run/doctor，help缺失；已修正4000字节超限并由单次原生CLI安装核对四入口转换产物通过；桌面/Claude新命令体验仍待验，见[复验结果](../docs/verification/2026-10-13-delegate-source-load-fixed-result.md)。

2026-10-13本机已按独立批准切换正常Codex到本地源码并重装，4skill/61文件匹配、仅SessionStart；Claude2.1.296实际按现有user配置原地加载4命令，无本批安装/设置变更；安装的预检函数核实已有CLI/claude.ai认证及回收（收紧为禁网）。SRT仍须按次指定临时绝对路径，既有主会话UI和模型/额度未验。[本批证据](../docs/verification/2026-10-13-delegate-local-activation-result.md)不追认完整Task2/6/8。
