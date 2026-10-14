# 修复后反向第三批验收预览

日期：2026-10-12。开发仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。此预览完成免费准备，不包含新增通信/模型授权；[精确摘要](2026-10-12-claude-review-mac-reverse-third-preview.json)。

## 第二批实际停点

第二批不是仍在等待：12日关联回复证明目标在自身人类指示“重试”后运行固定驱动一次，09:30 UTC（客户端17:30），宿主守卫拒绝、退出1，backend未启动。预览固定Claude进程已因应用重启失效。来源独立核实新marker/logs/result不存在，四文件/上下文/HEAD/status不变，无攻击标记；[结果证据](2026-10-12-claude-review-mac-reverse-second-result.json)。这证明旧宿主守卫拒绝路径，不能替代真实审查。旧两批驱动不重跑、不更新身份。

## 第三批具体范围

- 主会话：唯一可见的Claude Code“Claude验收会话”，目录报告2.1.295；当前新内核身份/二进制摘要已只读核实并固定。再次重启或身份变化则停止，不自动重绑定。
- 后端：Codex CLI0.160.1，模型CLI默认，可靠实际模型信息缺失时unknown。先核实自身认证，缺条件则停止，不自动登录、换后端或重试。
- 原四个合成文件：src/pricing.py、REVIEW_DATA.md、SPEC.md、PLAN.md；同一固定Git基准、摘要和排除excluded.py，工作区干净。
- 当前源码公共 `delegate-exec.sh review --backend codex --context`，一次执行/180秒，结果未知或失败即停。Codex本封装没有美元或轮次硬上限，模型及目标Claude交接可能耗用额度。
- Codex只读沙箱、inline文件数据、核实shell/apps/plugins/multi_agent关闭、搜索禁用/MCP为空；不执行源码、不开放任意Bash/网络/递归委托。旧Codex进程组清理限制继续明确：不能证明detached后代不存在。
- O_EXCL单次启动marker，实际driver/wrapper退出码及结果保留；执行后定向核对发现、文件行号/触发条件/影响、已审/未审范围、完整性及回收证据。结构/退出0不证明所有发现真实。

## 免费准备与限制

AST/源码/CLI/输入摘要通过，公共dry-run通过：四文件5,018字节、inline_files、最大1MiB、180秒、backend_started=false、无采集缺口。没有新消息、模型、安装或配置修改；产品代码摘要仍与137 Python/53 shell/19 eval通过记录一致，未无理由重复总套。

此驱动通过绝对源码路径调用，不能证明新版斜杠命令已在两种宿主加载或可用；未执行新驱动的错误宿主运行测试，不以AST代替真实守卫运行。源码/身份变化、拒权、未知、失败停止，不扩大权限。

## 新单次批准 gate

下一步需针对本第三批批准：向已有“Claude验收会话”发送一条交接，并执行一次上述真实反向审查。旧批次已经执行且规定失败停止，不自动扩大旧批准为下一次运行；目标自身的人类权限要求仍须满足。批准后首步复核固定身份和摘要、唯一选路、仅一次发送，再读取同一关联结果；不自动重试、安装、升级、提交、推送或发布。

## 批准后实际收束

用户“批准”后单次投递，关联回复/私有产物证明实际驱动执行、宿主守卫通过，Codex版本预检因目标Node12失败。退出127/0.472秒、未启动审查后端；四文件均未审、输入/Git不变。[结果](2026-10-12-claude-review-mac-reverse-third-result.json)。失败即停，旧驱动不重跑。免费诊断和安全阶段分类修复通过，固定已有Node24的[第四批预览](2026-10-12-claude-review-mac-reverse-fourth-plan.md)仅完成准备，未获新增批准。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
