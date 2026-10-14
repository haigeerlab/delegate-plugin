# delegate 双后端当前交付状态

更新：2026-10-14。模块 `claude-review`，阶段 **DONE：当前Mac功能与分层验收已收束，v0.5.0已发布并完成两宿主本机安装核对**。功能代码和必要修复已完成、同步两宿主；Task2/6/8按明确批准的分层标准完成。用户接续具体最终供审清单回复“继续”，233受审文件与固定条件未变后关闭Checkpoint5。所有未验证项和历史未知保留，不代表所有安全行为已证明。

本页只列当前状态。历史批次按下方链接保留，不把旧失败写成通过，也不把安装与菜单显示写成真实审查。

**本地工作已完成。** 用户已明确批准分层标准并接续[最终供审清单](2026-10-14-delegate-final-layered-review.md)回复“继续”；233文件逐项摘要/集合及分支/HEAD/固定条件再次核对未变，实际原话与供审摘要保存后关闭最后人工gate。原供审文件保留当时pending状态，不覆盖历史；当前接受由本页和todo记录。见[分层结果](2026-10-14-delegate-layered-acceptance-result.md)。Git交付、安装和新模型调用均不在此次接受范围。

| 阶段 | 当前结果 | 证据 |
|---|---|---|
| 官方接口、设计与计划 | 已完成并按会话确认实施；CLI 优先、两个后端、Mac 范围 | [规格](../../spec/claude-review.md)、[计划](../../tasks/claude-review/plan.md) |
| 功能开发与审查修复 | 三个Required问题及Task9l诊断丢失已修复；Task9n恢复标准原工作区总验证157 Python / 53 shell / 19 eval通过，私有备份执行位限制已解决 | [最新验证维护](2026-10-14-delegate-validator-discovery-result.md) |
| 普通双向真实审查 | S2 固定源码：Codex→Claude 与 Claude→Codex 各一次，均审 4/4 合成文件，输入/配置/Git/清理核对通过 | [S2 结果](2026-10-13-delegate-s2-resume-result.md) |
| 本机安装同步 | 发布后两宿主已安装并启用0.5.0，62源码匹配两缓存，Codex另有4迁移技能；16项入口检查、48项结果回归通过。未新增模型或宣称旧会话热加载 | [v0.5.0](../releases/v0.5.0.md)；私有发布回执已核对 |
| 宿主入口显示 | Codex 四入口由用户确认；Claude 四入口由 AI 直接观察，2026-10-14 再次可见。未执行本轮重载或新审查 | [本轮 UI 核对](2026-10-14-delegate-ui-and-s4-preview.md) |
| 人工接受 | Checkpoint3源码部分接受保留历史范围；Checkpoint5接受当前Mac功能、分层证据及未验证限制，不含Git交付 | [最终供审对象](2026-10-14-delegate-final-layered-review.md) |
| 分层工程验收 | 按明确批准的CR-03/06/09判据分别关闭Task2/6/8；非安全行为穷举，历史未知保留 | [分层结果](2026-10-14-delegate-layered-acceptance-result.md) |
| 提交、推送、发布 | 用户另行明确授权后已完成：提交c59b370，main与开发分支及v0.5.0标签目标一致，正式非预发布版本已创建 | [发行页](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.5.0)、[提交](https://github.com/haigeerlab/delegate-plugin/commit/c59b370b7e64c9a0f88024ecdfda8a371174ea89) |

## 已实现与使用方式

`review` 支持显式 `codex` 或 `claude-code`，默认 Codex，宿主与执行后端独立；`run` 保留 Codex 通用任务，默认只读，显式 write 才能写。模型、推理及限制参数按后端验证，不混传、不失败切换。Claude 首版只读，拒绝 write、effort 和 run。

Claude 主会话使用 `/delegate:review --backend codex --paths src/login -- 审查这个范围的回归风险`。Codex 主会话选择 delegate 的 `source-command-review`，提供 `--backend claude-code --paths src/login --model sonnet -- 审查这个范围的回归风险`。先加 `--dry-run` 核对范围；`doctor` 检查所选后端；`help` 解释能力和迁移。旧 `delegate` 源斜杠命令已退役，原脚本兼容保留。

审查输入区分固定 diff、模块与指定路径，带基准、工作区策略、Spec/Plan、验收条件、排除项和停止条件。执行状态与审查结论分开；空/坏结果、拒权、达限、超时和部分覆盖不能当作“没有问题”。报告核对行号和证据，未知宿主/模型/费用标未知；最终答复、报告与过滤日志分开保存。审查不授权修改、合并或交付。

Claude 采用 Read/Glob/Grep 的工具限制、项目上下文隔离、包围整个 CLI 的 OS 文件系统/网络边界与 Mac coalition 清理；不开 Bash、MCP、派活或写入工具，递归入口受 depth 限制。Codex 保留原进程组实现及 detached 子进程限制。Spec Guard 辅助合同、任务与验收，Agent-Relay 仅用于已授权的宿主间交接，两者不成为 delegate 执行依赖。

Claude 当前要求 Mac、原版 CLI ≥2.1.295、Node ≥22.12.0、SRT 0.0.79 和可用 GUI launchd 域。依赖仍按次提供已有绝对路径，不改全局 PATH、不自动安装或登录。版本号相同不能证明缓存内容相同；发布后已核实0.5.0安装内容与源码一致。

## 真实结果及未验证项

S2 正向 21.418 秒，实际模型 `claude-sonnet-5-5`，CLI 估算 0.0331589 美元；反向 22.326 秒，模型名称和美元口径未知。两方向均定位 `pricing.py` 第 7 行返回折扣额而非应付额。Claude 对“所有合法输入都错”的概括有反例，已校准说明，原报告保留。有限样本不证明所有发现真实或另一模型更准确。三批后续修复已有免费回归及安装读回；其后S4有一次真实受限补证但失败，普通双向成功记录仍为S2。S5诊断修复已用于原S6一次认证失败和新批准的一次诊断接续；后者指定Read拒权及目标归属通过、审查1/4未完成，进程回收确认。此前认证失败根因仍未知，不能从此次可用追认修复。

| 已完成的分层任务 | 已有证据 | 仍未验证的限制 |
|---|---|---|
| Task2 安全边界 | Mac 实际拒写/生命周期探针、公共假 CLI 故障场景、原版普通只读运行 | 真实模型主动写入/递归企图并被拒的事件、认证刷新；S6接续已取得指定快照外Read工具拒权；仍缺真实主动写入/递归及认证刷新事件 |
| Task6 异常运行 | 合成 detached/双重 fork、取消/超时与内核回收；原版异常分类/回收有直接事实；当前两种Python监督器12项Node/SRT启动采样通过 | 原版异常整批设置摘要曾变化且归属未知；自然异常 helper、间歇启动失败根因及长期稳定性；本轮未复现不追认修复 |
| Task8 宿主与真实权限 | 普通双向四文件审查、四入口显示；S7 help/review实际脚本及完整dry-run输出已核对 | 真实主动写入/递归工具事件、无差错的UI输入/提交体验；指定快照外Read拒权已补齐，原并发输入失败保留 |

不为完成清单强制刷新认证或放宽权限。真实模型不尝试越权时记录“未观察”，不能凭提示词承诺、工具不存在或普通审查成功补齐现行合同。三项 Optional 体验建议及一项结构建议未自动扩大实施。

## 下一步与历史导航

[S4 一次真实 Read 边界验收](2026-10-14-delegate-s4-read-boundary-result.md)已获批准并执行：6.751 秒，后端实际启动，返回 backend_result_error / failed / inconclusive，0/4 未完成；回收确认、输入/源码/缓存/被观察设置未变。未取得直接拒权证据，本批未通过，授权已消费，未重试。后续免费诊断复现/源码修复已完成，见[Task9l结果](2026-10-14-delegate-error-diagnostics-result.md)。[S5仅delegate安装同步](2026-10-14-delegate-s5-sync-result.md)已获批准并完成，Task9m关闭，授权已消费。随后[Task9n验证入口修复](2026-10-14-delegate-validator-discovery-result.md)完成，标准工作区157/53/19通过，未再次安装。[S6单次读取补证](2026-10-14-delegate-s6-read-boundary-result.md)已按用户对具体范围的“继续”执行一次：6.043秒、failed/inconclusive、认证错误，0/4未审；未取得拒权证据，清理confirmed、固定对象/被观察设置不变，次数已消费、不重试。截图中另一个“查看命令说明失败”已核实是读取退役的delegate.md，与认证失败分开；不干预该独立会话。随后[S6免费认证诊断](2026-10-14-delegate-s6-auth-diagnosis.md)确认同一原版CLI在禁网/只读边界下仍本地登录、默认目录正确、观察设置不变；用户已反馈终端Login有效，根因仍未定；[新批准的诊断接续](2026-10-14-delegate-s6-diagnostic-followup-result.md)一次11.974秒，指定Read拒权和精确目标归属通过、cleanup confirmed，固定对象/被观察设置不变；模型报告审查1/4，failed/inconclusive，估算约0.030152美元。没有认证错误，历史根因仍未知；原失败保留、两次各自授权均消费，不自动重跑。随后[剩余证据对齐](2026-10-14-delegate-remaining-acceptance-feasibility.md)取得10项安装递归入口拒绝及Claude菜单Tab选中review的直接记录，未提交。下一gate为[S7两条菜单宿主指令](2026-10-14-delegate-s7-menu-plan.md)，后端模型0、宿主可能耗额度；用户已“批准S7”并反馈空闲；[S7实际有限结果](2026-10-14-delegate-s7-menu-result.md)确认help脚本完成及review公共dry-run一次，输入在并发提交中含重复参数、宿主纠正后执行，AI发送点击0次、提交者未知。随后[已有完整输出读回](2026-10-14-delegate-s7-output-readback-result.md)免费确认实际argv与预览全字段相等、四摘要一致、退出0/backend_started=false，菜单到公共脚本功能证据补齐。原交互输入失败保留，S7不整体通过、不重发；真实Write/递归、异常/稳定性等限制保留，不改变工具集合或重复Read探针。新增模型、通信或Git交付分别授权，不复用旧批次。

历史证据：[最初普通双向](2026-10-13-delegate-remaining-acceptance-result.md)、[Claude 缓存刷新与显示](2026-10-13-delegate-claude-install-staged-result.md)、[流程核对](2026-10-13-spec-guard-workflow-check.md)、[命令多维审查](2026-10-13-delegate-command-multiaxis-review.md)、[S3 第一批失败](2026-10-13-delegate-post-review-sync-result.md)、[S3 第二批失败及完整替换方案](2026-10-13-delegate-post-review-sync-resume-result.md)。历史失败、次数、当时限制和未消费范围分别保留。
