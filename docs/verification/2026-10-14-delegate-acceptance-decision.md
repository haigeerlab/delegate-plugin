# 剩余验收的分层取舍：已明确批准

日期：2026-10-14。审阅位置：`/path/to/delegate-plugin`，分支`codex/spec-guard-conventions-public`。这是验收标准修订建议，不是旧验收通过的证明；没有修改spec或勾选Task2/6/8。源码部分成果已在Checkpoint3接受，不重复请求那份接受。

**当前记录：** 用户明确“批准分层验收修订”，已按下列原供审文本同步双语合同并逐项核对；见[执行结果](2026-10-14-delegate-layered-acceptance-result.md)。下文“未经批准”及旧标准未勾状态保留为供审时文本，不代表本次仍在等待修订批准。

## 已有事实与问题

功能代码、参数/失败分支、Mac权限/生命周期探针及免费157/53/19已完成，S2普通双向真实审查成功；S5最新缓存同步，S6真实Read拒权，S7菜单实际help和完整dry-run读回已有证据。Task6新增12项版本启动采样通过，但历史根因及长期稳定性仍未知。

当前CR-03额外要求真实Claude主动写入工具事件；生产后端移除Write/Bash/Agent/Skill/MCP。没有Write调用事件不能当作成功，也不能靠反复付费保证出现。为取得事件而声明Write或执行工具会改变测试对象，独立夹具结果也不能冒充原生产路径。CR-09需区分入口递归保护、工具不可用与真实模型递归事件；历史自然helper和长期稳定性没有有限完成判据。

## 现行合同的证据对账（不等待修订也可核对）

这张表只整理现有证据，不改变成功标准或任务勾选。免费总套结果仅覆盖测试合同；真实结果按记录的版本/输入分别判断。

| 当前条款 | 已有证据 | 当前判定与缺口 |
|---|---|---|
| CR-01 默认/旧Codex兼容 | test-review-backends、test-backend及既有shell回归在157/53/19总套中通过 | 已验证回归覆盖的调用；不新增真实write任务 |
| CR-02 显式后端与参数 | 公共CLI、模型归属回归、S2正向实际Claude；没有fallback | 已验证覆盖参数/执行路径，不证明任意未来CLI版本 |
| CR-03 实际拒写及模型事件 | Mac实际OS拒写与公共假CLI真实拒写；S6实际指定Read拒权 | **部分**：真实模型主动Write事件未观察，现行双重要求未满足 |
| CR-04 固定范围/上下文 | test-review-context、两后端等价输入，S2/S7固定四文件摘要核对 | 已验证所测范围与边界案例，不泛化为全项目 |
| CR-05 状态分类 | test-claude-review、test-review-result，S2正常与S6真实failed/inconclusive/拒权 | 已验证所测类别；空/坏/达限等故障注入仍是合成证据 |
| CR-06 生命周期 | Mac真实内核归属、超时/信号/detached/double-fork等合成进程；原版异常分类/清理记录；新增12版本采样 | **部分**：原版异常整批设置断言未过且归属未知，自然helper与长期稳定性不由合成进程证明 |
| CR-07 定位/覆盖/未知 | S2第7行核心缺陷独立核对及反例校准，S6报告1/4及三未审范围，缺失字段保留未知 | 已验证这些报告字段与样本；格式不证明所有模型发现真实 |
| CR-08 日志/凭据/权限 | sentinel回归、0600/0700产物、过滤日志及无原始流保存、S5安装副本结果回归 | 已验证保留策略和所测敏感哨兵，不声称穷举所有凭据形式 |
| CR-09 防递归 | 两缓存10项公共/兼容入口在depth=1下实际拒绝，无后端/认证启动；原版受限运行及初始化校验 | **部分**：真实模型递归事件未观察；环境标记是合作式入口防护，不是恶意进程OS证明 |
| CR-10 两真实宿主 | S2当前Codex→Claude与ClaudeClaude验收会话→Codex各4/4；版本、范围、权限、结果与限制分别记录 | S2固定源码批次的普通双向已验证；最新诊断修复不追认为已重跑完整双向。S7只是无模型菜单功能证据 |

依据：[最新免费总验证](2026-10-14-delegate-validator-discovery-result.json)、[S2真实双向](2026-10-13-delegate-s2-resume-result.json)、[S5安装结果回归](2026-10-14-delegate-s5-sync-result.md)、[S6真实拒权](2026-10-14-delegate-s6-diagnostic-followup-result.json)、[S7完整读回](2026-10-14-delegate-s7-output-readback-result.json)、[Task6有限采样](2026-10-14-delegate-task6-runtime-timing-result.json)、[递归入口证据与边界](2026-10-14-delegate-remaining-acceptance-feasibility.md)。

当前完整Task2/6/8仍三项未勾。单纯“继续”只承接证据对账，不登记为本修订的明确批准。

## 推荐取舍：权限不变，明确分层成功条件

以下是**拟替换文本**，未经批准不成为合同。原始失败/未观察/未知都保留；测试断言、源码及生产工具/文件/网络权限不变。

### spec中文与英文对照

- CR-03拟改为：“同一生产文件系统策略下，受控审查进程实际尝试写入源码、Git、配置和快照均被拒，指定临时目录可写；原版Claude初始化工具清单只含允许的只读及结果/结束工具；真实指定范围外Read拒权单列证据。模型主动Write事件未观察时明确标未验证，不以其不存在证明OS拒写。”
  English: “Under the production filesystem policy, controlled reviewer processes actually attempt and are denied writes to source, Git, configuration and snapshot files; only designated temporary paths are writable. Original Claude initialization exposes only allowed read and result/end tools. A real out-of-scope Read denial is recorded separately. Unobserved model Write attempts remain explicitly unverified and are not evidence of OS enforcement.”
- CR-06保留原超时/取消/辅助进程回收要求，补充：“以Mac内核归属、实际超时/信号、detached/double-fork/父先退与无关进程存活证据验收；原版CLI异常记录按对应版本和不变性检查逐批报告。未观察的自然helper类型、历史未定根因及长期稳定性列为限制，不宣称已证明。失败或清理未知仍失败关闭。”
  English: “Validate kernel ownership, real deadlines/signals, detached/double-fork/parent-exit helpers and survival of unrelated processes. Report original CLI abnormal runs per version and state-invariance checks. Unobserved natural helper variants, unresolved historical causes and long-term stability remain limitations. Failures and unknown cleanup remain fail-closed.”
- CR-09拟改为：“全部delegate公共与兼容入口在嵌套标记下于认证/运行时/模型启动前拒绝；原版Claude初始化不开放执行、派活或MCP工具，项目上下文隔离。入口标记是合作式防护，不能替代OS限制；真实模型递归企图未观察时明确标未验证。”
  English: “Every public and compatibility delegate entry rejects a nested marker before auth/runtime/model startup. Original Claude initialization exposes no execution, delegation or MCP tools, with project context isolated. The marker is cooperative protection, not an OS boundary. Unobserved model recursion attempts remain explicitly unverified.”
- CR-10和两真实宿主要求保持不变。两方向证据按实际固定源码/CLI版本记录，不把S7无模型预览替代S2真实审查或声称最新源码已重跑双向。

### plan/todo拟调整及验证

1. Task2按OS实际权限、原版工具初始化、真实Read拒权三层逐项映射；Write/递归模型事件和认证刷新保持独立“未验证”，不转成已通过。
2. Task6按现有明确的生命周期/日志合同验收，历史设置变化、自然helper、间歇根因和长期稳定性继续列限制；不能从本轮采样证明稳定或修改超时。
3. Task8将S2版本固定的普通双向与S7菜单到公共脚本证据分开。保留UI自动输入缺字/替换失败和并发提交，不能标为无差错自动UI验收，也不归因为插件功能失败。
4. 批准后才同步中文spec、英文对应页、plan和todo，并按修订后的逐项证据判定；有未满足条件继续未勾，不承诺批准即可关闭3项。保留157/53/19所有产品测试与断言；文档/合同对应检查及Spec Guard验证通过后交最终验收清单。

本次批准最多授权上述合同/文档修订与免费验证，不授权安装、升级、登录/刷新认证、新模型调用、跨会话消息、提交/推送或发布。生产权限与工具集不得扩大。若要补独立攻击夹具，先单独设计、审查其与生产对象的差异，再按具体次数授权执行。

## 可选决定与下一停点

- **批准分层验收修订（建议）**：按上面精确范围同步合同和任务，逐项核对，保留不可证明的限制；不是追认旧标准通过。
- **保持原验收**：三个完整任务保持未完成，停止重复普通审查；若还要取得主动Write/递归事件，另行设计受控夹具，不自动启用工具或新增模型调用。

需要人工决定的原因：spec的Ask first明确要求“隔离闸门不通过或改变已确认取舍时停下”；Spec Guard共享检查点规则（本机私有证据，原路径未公开）也要求“Spec没覆盖的决策”停下。当前建议改变的是成功判据，不能从“继续”或源码已完成推导批准。回复“批准分层验收修订”或“保持原验收”即可。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
