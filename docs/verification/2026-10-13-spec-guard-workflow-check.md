# Spec Guard 初始化与当前任务核对

日期：2026-10-13。位置：`/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。用户要求核对初始化，随后要求在非人工检查点连续推进。本轮只同步仓库约定、任务导航和证据；无安装升级、全局配置写入、付费审查、跨会话通信或 Git 交付。

## 初始化

通过 `codex plugin list --available --json` 解析实际已启用的 Spec Guard 0.56.0，使用其官方脚本，不猜缓存版本。

- `setup-convention.sh local --host=codex --replace --dry-run` 和 Claude 默认宿主的相同预览均只有新增两行配置规则，无删除；随后按本轮继续授权实际执行，两项退出 0。
- [AGENTS.md](../../AGENTS.md) 和 [CLAUDE.md](../../CLAUDE.md) 的声明块均与当前模板同步。Claude 的 `agent-skills-convention` 是正式识别标记。
- `.agent/state.json` 仍为 `{"activeModule":"claude-review"}`；未改能力图或勾选验收。
- 项目配置不存在：`artifactLanguage=unset`，沿用项目中文要求；`reviewCadence=separate` 默认；两宿主 dispatch=off，trackerDefault=absent。可选账本缺失不等于初始化失败，也不由此补建事项。
- 状态目录为 `~/.spec-guard`；插件仍读取旧 `~/.local/state/spec-guard/hosted-ticket-intents` 回退目录。本轮未删除或迁移它们。

## 当前接续

当前模块 `claude-review`，BUILDING。最新完成 Task9g，接续 Task2 剩余安全证据 → Task6 原版异常/helper → Task8 新入口交互/主动越权 → Checkpoint3 人工审阅。保留四个未勾项；Task9g 移入当前清单，历史停点单独说明，不重写历史批准。

源码功能已实现；完整模块验收尚未完成。已核实反向真实审查固定的 18 个 Python 执行文件和 2 个 shell 执行文件摘要仍匹配；当前 61 个插件文件与正常 Codex 缓存逐字节一致。142 Python/53 shell/19 eval 的既有通过结果继续有效，本轮没有重复总套，也不把摘要一致追认为旧证据覆盖新交互行为。

## 原版 CLI 免费异常补证

固定 Claude2.1.296、现有 Node24.18.0/SRT0.0.79。仅专用临时 Git 仓库的一份合成 `a.py`，Read 和结构化输出；原产品工具限制、Hook/MCP/会话持久化限制不放宽。原生进程边界使用当前 `NativeRunner` 和 `MacBoundary`；SRT `allowedDomains=[]`，禁止所有外部模型请求送达，不能用轮次值保证免费。

| 场景 | 实际结果 | 清理 |
|---|---|---|
| 一次12秒期限 | timed_out，原版 init 校验通过，12.776秒 | confirmed；job不存在，内核coalition为空 |
| 一次init后SIGTERM取消 | cancelled，cancel_signal=15，原版 init 校验通过，9.161秒 | confirmed；job不存在，内核coalition为空 |

合成文件摘要未变，未生成模型答案。两场景不重复，不作成功真实审查、认证刷新或自然 helper 拓扑证明。原始 stdout/stderr/stdin 已删除，只保存长度、摘要、安全状态和控制事实。

**整批驱动退出1，不能宣称整批通过。** 最后的设置摘要不变断言失败：`settings_unchanged=false`。观察到 `.claude.json` 的mtime在运行区间内变化，其他三个被观察文件的mtime早于本批；原驱动未落盘逐文件的前置摘要，无法可靠确定变更内容或归属。本次 OS 策略拒绝 HOME 写入，但不能仅据策略或其他会话存在就断言变更由谁造成。后续只做相同策略的无字节写入诊断，不重跑原批次，不回滚用户设置，不读取认证内容。

同一 SRT 策略的定向诊断实际拒绝以追加写方式打开已存在的 `.claude.json`，未截断或写入任何字节；诊断退出0并回收confirmed。文件摘要在这段诊断期间也变化，仍不能从此确定写入者，不把该诊断退出0当作配置不变证明。

直接证据与诊断摘要见[JSON](2026-10-13-spec-guard-workflow-check.json)；私有批次位于 `/path/to/private-evidence`。两个原版异常分类和清理事实可作为有限证据，配置完整性未知仍保留，Task6不勾完整完成。

## 后续检查点

用户继续后只读核对三个本批job均不存在，并完成20.13秒无Claude/SRT启动的被动观察；未见配置变化。这只描述该窗口，不能归属之前的写入，失败记录不变。Agent Relay只读目录核实既有“Claude验收会话”的当前候选与注册映射，未发送或注册；其进程身份/可执行摘要固定在私有包中。

免费准备收束为[剩余真实验收gate](2026-10-13-delegate-remaining-acceptance-plan.md)：两后端dry-run及两方向preflight通过，61个固定插件文件、4个审查文件和1个排除文件；新增模型调用/交接尚未批准或排队。不再重复同样的观察或安装，不因目前条件不足自称全部验收完成。

本轮最终核验：两份声明块与实际模板逐字匹配；98个本地文件链接有效，JSON可解析，activeModule未变、Task9g仅出现一次、仍4项未勾。`git diff --check`退出0；Spec Guard产物3通过/0警告/0失败，阶段BUILDING。这里只验证本轮文档/导航，不重新运行产品总套或追认真实验收。

本轮免费整理与诊断是 report，继续运行文档、阶段和产物核验。新增模型/宿主交互批次须给出明确范围、次数、预算及停点，未获批准不执行；既有已消费的 live/安装授权不重复使用。最终 diff 和完整验收限制仍由 Checkpoint3 人工审阅，不能从结构检查、安装或普通审查成功直接勾 DONE。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
