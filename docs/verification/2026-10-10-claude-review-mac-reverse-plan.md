# 真实反向审查预览：Claude Code → Codex

日期：2026-10-10。开发位置 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。正向第四批真实审查已完成；反向交接后目标取得本会话直接同意并运行一次，宿主/实际 Codex 启动通过，但四文件均未审，审查失败；本批一次授权已消耗，修复后真实审查未复验。

用户已选择真实 Claude 主会话“Claude验收会话”（目录报告 CLI 2.1.295）并批准一次联系。这是受支持会话目录和精确内核身份事实，不猜作用户常用会话，也不读取其谈话/argv/环境/凭据。目标本会话的付费运行授权仍缺少；不能自行换会话。

## 固定范围与首次动作

新专用根 `/path/to/private-evidence`，同等合成 Git 基准 `dc59b5423cfd4a2b780a4ac91f7264b6404e541e`，四文件 PLAN.md / SPEC.md / REVIEW_DATA.md / src/pricing.py，排除 excluded.py，无未提交改动。它是 module 审查，不冒称固定 diff。上下文摘要 `a01fe1364ec269d73d57c725ae4da9d86e80fcd7f790897da2c8f90b17bbc7d1`；[输入、Codex 和源码摘要](2026-10-10-claude-review-mac-reverse-preview.json)。夹具和共同输出枚举已准备；正常正向夹具缺陷不修复，以验证另一后端的实际观点。

获联系授权后的首次动作已完成：只向这个已有 Claude 会话发送一次可审阅的交接草稿（本机私有证据，原路径未公开），未创建新会话、替目标注册、安装或改配置。agent-relay 仅用于本次测试交接，不成为 delegate 产品依赖，也不扩展 Spec Guard 执行器。按 当时 agent-relay 0.6.2 的 session-routing（原读取路径 `/path/to/user-home/.codex/plugins/cache/agent-relay-marketplace/agent-relay/0.6.2/skills/session-routing/SKILL.md`，该旧缓存现已移除；前次导航路径 `/path/to/user-home/.codex/plugins/cache/agent-relay-marketplace/agent-relay/0.6.3/skills/session-routing/SKILL.md` 也已移除；前次0.6.4缓存导航也已移除；当前导航见 已启用源码的同名说明（本机私有证据，原路径未公开））唯一目录/单次选路和未知不重发规则处理；目标消息不构成扩权授权，接收端仍需直接人类授权与其现有权限。没有这些条件即报告条件不足，不绕过目标许可、不声称已经验收。

## 原版后端与边界

原版 Codex CLI 0.160.1，既有 ChatGPT 基础登录及 exec help 所需参数免费核对通过；尚未验证远端/额度。固定源码公共入口显式 --backend codex --review-context，read-only / ephemeral / ignore-user-config / ignore-rules / 禁用 multi_agent，用同一快照和结果合同。无 --write，不自动修复或执行源码/测试，不提交/推送/发布、不访问真实事项。保持 Codex 既有进程组清理，detached 后代不证明无残留的已知限制单列。

本批最多一次 codex exec，期限 180 秒（预检和有界回收另计），CLI 默认模型；实际模型和用量无后端证据时未知。Codex 适配器没有 Claude 专属轮次/美元预算参数，**不承诺 1 美元或轮次上限**；已有 Claude 主会话接收/处理交接也可能耗用其额度。不得将 Claude 预算参数混传 Codex，不使用另一个模型或后端回退。

固定驱动在模型启动前检查源码/CLI/四文件/上下文摘要与合成 Git 状态，并确认发起进程位于指定真实 Claude 的祖先链、内核 unique/generation 与执行文件摘要一致；身份变化或无法证明立即停止。它不会清除委托深度标记；嵌套 reviewer 不能靠驱动再次派活。排他 marker 避免重复启动。免费错误宿主测试已从当前 Codex 发起，得到 claude_primary_host_not_verified / model_not_started，marker/logs 未生成，不算反向真实验收。

```bash
python3 -B /path/to/private-evidence
```

## 验收与停止

固定来源目录/内核身份、真实 Claude 发起祖先及实际 Codex 执行分别留证；桥入箱/唤醒/已读/回复也分开，不以通信回执证明审查完成。不得用当前 Codex→Codex、假 CLI 或工具退出 0 替代。

结果继续核对执行状态、审查结论、四文件已审/未审、发现位置/触发证据/未验证内容、输入/Git 前后不变及清理；实际模型/费用缺失不填零。失败、超时、取消、拒权、空/坏结果、来源未知或目标权限不足即停，无重试、不改配置。正常答复只给摘要和最终产物位置；必要诊断脱敏，不倾倒原始日志或凭据。

当前状态：dispatch=enqueued，wake=admitted，receipt=acknowledged，response=received，model_runs=0；这些只证明交接被处理，不证明反向审查通过。提交、推送、发布或其他项目修改均不在此预览。

## 单次交接结果与下一步

用户在当前 Codex 对话回复“允许发送给Claude验收会话”，仅授权本次联系。受支持目录唯一匹配、已启用 agent-relay 根目录、来源加入和 selector 放行后，只投递一次，未换路或重发。目标精确关联回复明确表示本会话没有这次付费 Codex/固定驱动的人类授权，已停止且不重试。[脱敏交接证据](2026-10-10-claude-review-mac-reverse-handoff.json)记录四段通信状态和验证缺口。

回执之后核对四文件/上下文摘要不变，model-started、logs、result-summary.json 均不存在；没有 Codex 模型启动。目标不是执行失败，当前验收条件不足；不生成虚假的后端报告、模型或用量。

后续第一步由用户在已有 Claude 主会话“Claude验收会话”直接批准刚收到的固定一次审查。可表达：“批准刚收到的反向验收：仅运行已准备的 run-once.py 一次，四个合成文件、Codex 只读、180秒、默认模型；无美元或轮次硬上限，失败即停，不重试，不安装、改配置或提交发布。”目标按自己的规则核对授权及权限后执行；身份/输入变化或执行失败即停。当前 Codex 不再次发消息、不自行替代发起。结果生成后仅核对这一固定产物及输入完整性，保留原有未验证项。

用户随后明确要求再告诉目标试用 delegate，另授权一次后续通信。该消息单次投递并取得精确回复，未重新运行模型：目标只读核对驱动，确认 delegate 源码入口→Codex，已向本会话用户展示范围并等待直接同意。目标还报告用户手动输入命令被宿主祖先守卫拒绝；这个手动过程未由来源侧独立观察。来源核对固定输入摘要不变，marker/logs/result 均不存在，模型启动仍为 0。未把发送侧的转述当作目标直接授权，也未替它绕过权限或扩大范围。

## 后续实际运行与失效停点

目标在 07:06 UTC 报告用户“同意，你来跑”，通过 Claude Bash 执行一次。真实宿主祖先/代际通过，Codex 0.160.1 实际启动，16.988 秒、wrapper退出1、failed/inconclusive、cleanup confirmed（旧进程组）、review_incomplete，四文件全部未审。原版没有获准的 Read，禁止命令的共同提示使其无法读取快照。用量由 CLI 实报，模型未知，不记为零成本或审查通过。输入/上下文/HEAD/status 不变，无攻击标记。[首批真实反向证据](2026-10-10-claude-review-mac-reverse-first.json)

上方“模型0/待直接同意”是初始交接时状态，已由本段实际结果取代。源接口修改后旧预览摘要失效，且 marker 已存在；不得再执行旧驱动或消耗旧授权。免费修复采用有界 inline 文件输入及明确 Codex 功能限制，不增加 Bash/MCP 读取权限。下一步需先准备当前源码的固定新预览，真实复验另行取得一次具体授权；本批不重跑。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
