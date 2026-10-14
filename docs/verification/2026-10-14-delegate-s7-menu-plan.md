# S7：Claude菜单选择后的实际命令执行

日期：2026-10-14。位置：`/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，模块claude-review，Task8的菜单子验收。没有新的后端审查模型或权限取舍；这是新增的宿主指令提交gate，不能复用S6授权。

**当前执行状态：** 用户批准后，两条实际公共脚本调用已观察；[完整输出只读读回](2026-10-14-delegate-s7-output-readback-result.md)已确认help匹配、review实际argv与预览全部字段匹配、退出0/backend_started=false、四文件摘要一致。菜单到脚本功能证据补齐；原UI输入缺字/重复参数、并发提交和宿主纠正保留，精确无差错输入验收不通过，S7不整体通过、不重发。固定对象/被观察设置未变，完整Task2/6/8保留。[原有限结果](2026-10-14-delegate-s7-menu-result.md)保留为历史；下文是执行前方案。

## 已备齐对象与验证

AI在已有Claude会话“Claude验收会话”实际选中了review菜单，参数提示正确，未发送、输入恢复为空；不需要安装或reload。两正常缓存仍匹配62源码，Codex四迁移skill另行固定。正常Claude缓存公共帮助及同一四文件context的codex dry-run免费预览均退出0；dry-run明确backend_started=false，四文件范围，实际主会话尚未执行。

私有固定候选`.agent/acceptance/remaining-feasibility-20261014/s7-menu-plan.json`摘要 `4742f5507c2bd2be5f6f5a133174bb223562e235815cd80d4de6f8e62d5adf64`，上下文仍为S6四文件输入摘要 `7e807061edc6a4d57f811dc1a6345ada507e35f5403e738467276223335ac09b`。未创建新的授权记录、未发消息。

## 获批后仅提交两条指令

1. 在“Claude验收会话”从菜单选择`/delegate:help`，提交一次。要求只读帮助与迁移说明，不执行doctor、安装、审查、任务或其他委托。
2. 第一条明确完成且四入口/默认codex/Claude只读语义匹配后，菜单选择`/delegate:review`，补充下列固定参数并提交一次：

```text
--backend codex --context /path/to/delegate-plugin/.agent/acceptance/s6-read-boundary/context.json --dry-run -- 只预览固定范围，不执行审查。
```

只操作已有指定会话，不创建会话、不使用Agent-Relay投递、不改宿主权限/认证/设置、不安装或重载、不提交/推送/发布。目标会话自身规则、授权或工具条件不足时停止，不替目标点击审批。输入有草稿、目标正在处理其他任务、缓存/固定输入变化时停止。

委托后端模型调用为0；Claude主会话解释两条插件指令可能消耗额度，无法给该已有宿主承诺美元/轮次硬上限。每条观察最多180秒；超时只取消本批刚启动的目标处理并记录已知/未知结果，不接管无关任务，不自动重发。失败、未知、权限/授权不足或dry-run被移除/后端误启动均停止本批，第二条不在第一条失败后执行。

## 验收与停止

记录实际菜单条目、提交指令、宿主回复与可核实底层调用的安全片段，核实help内容和公共review dry-run范围。必须有实际脚本输出/命令记录，不能只凭Claude说“已完成”；dry-run须backend=codex、backend_started=false、四文件/基准摘要与预览等价。主会话/CLI/模型字段仅保留可核实信息，未知不猜；不保存完整会话、凭据、原始日志或无关项目内容。

源码、两缓存、固定合成输入/Git及被观察设置前后核对；发生变化记录并停止，不自动回滚并发会话状态。结果仅关闭Claude菜单实际命令执行子项，不冒充真实Claude→Codex审查（S2另有真实记录）、Write/递归事件、异常稳定性或Codex菜单AI自验。Task2/6/8不整体勾选。

人工批准只覆盖上述两条宿主指令，不包含追加模型审查或独立Write可见夹具。[AGENTS.md](../../AGENTS.md)明确要求付费live验证和委托另获授权；本次还需要明确授权向已有Claude会话提交指令。回复“批准S7”或“批准”即可，未获批不提交。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
