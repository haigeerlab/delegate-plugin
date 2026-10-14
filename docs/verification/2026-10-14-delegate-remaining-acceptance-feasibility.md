# 剩余验收对齐与免费补证

日期：2026-10-14。开发位置：`/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。模块claude-review，BUILDING；用户“继续”承接S6后的剩余条件整理，本批没有新增真实模型、安装、通信或权限修改。

## 当前证据与缺口

| 任务/条件 | 已有直接证据 | 尚不能宣称 |
|---|---|---|
| Task2 / 源项目与配置拒写 | Mac实际OS拒写探针、只读快照及允许临时写范围；真实S6指定快照外Read工具拒权且目标精确归属 | CR-03另要求真实Claude Write企图；当前默认工具集合移除了Write，没有真实Write工具事件 |
| Task2/8 / 防递归 | Bash/Agent/Skill/MCP移除、项目上下文隔离；本批10项正常安装副本入口均在认证/运行时/模型启动前拒绝depth=1 | 不是模型实际调用delegate事件；depth环境标记是合作式入口防护，不能独立作为恶意进程的OS隔离 |
| Task6 / 回收与异常 | Mac真实fork/setsid/double-fork等探针；原版普通结束与S6拒权结束coalition清理确认；原版禁网超时/取消曾有分类和清理直接事实 | 旧异常整批设置变化归属、自然helper全部模式、间歇启动原因及长期稳定性未知；不能用一次正常成功覆盖 |
| Task8 / 双向功能 | S2两方向普通审查各4/4、固定输入/真实宿主、核心缺陷与清理核对 | 新诊断源码不借旧成功证明全部安全，部分输出需校准 |
| Task8 / 菜单显示和选择 | 两宿主四入口显示；本批AI在Claude菜单通过Tab选中review，显示参数提示，未发送且恢复空输入 | 尚未证明菜单提交后的命令实际执行；Codex界面仍按用户确认范围，不用电脑工具冒充直接观察 |

三个任务不自动勾选；没有将全安全验收改为默认已通过。

## 为什么不能反复运行以取得Write/递归事件

源码claude_review.py明确仅声明上下文中的Read/Glob/Grep，并以裸工具名移除Bash、Edit、Write、Agent、Skill和MCP；review_macos.py/read_init又在启动时检查允许集合。官方[CLI参考](https://code.claude.com/docs/en/cli-reference#cli-flags)确认裸工具名的disallowedTools会从模型上下文移除工具，scoped rule才是在保留工具的同时拒绝匹配调用。

所以当前生产路径通常不会提供Write或执行delegate所需工具的正常调用机会；普通运行没有企图只能记未观察。为取证而在测试中声明Write，或提供执行delegate的工具，会改变测试工具集合/初始化验证对象，须先设计并单独审阅；不能混作当前默认后端验收，不自行修改生产参数或降低CR-03。

保留当前权限可以继续验收菜单实际执行。若之后要求主动Write事件，应另行审阅独立合成夹具：只让工具可见、所有写动作仍拒绝、源项目/配置仍由OS拒写，初始化集合差异单独记录；本批没有实现或授权这种夹具。递归事件不通过开放任意Bash、真实事项或网络取得。认证刷新不靠手动编辑/撤销凭据制造事件；现有认证及历史未知原因保持。

## 本批安装副本递归入口验证

对Codex和Claude两个正常安装缓存分别执行review/run×codex/claude-code四种组合及旧codex-exec.sh，共10项。实际调用者全是当前Codex，不冒充第二轮Claude宿主。使用独立临时HOME，depth=1，后端和srt在PATH中替换为只写本批启动标记就退出的无模型哨兵；真实后端二进制、认证及网络未调用。

10项全部退出64、stdout为空、stderr精确为固定递归拒绝文字；哨兵均未启动。冻结源码、两缓存、输入/运行时、合成Git及四项被观察设置未变，临时夹具已清理。源码断言或执行逻辑没有修改。

首个探针的精确stderr断言失败且未保留首个详细返回。相同首场景定向复现得到正确64/递归拒绝和Xcode Python shim警告、无哨兵启动；记录保留。随后用已有内置Python3.12固定解释器避开shim，原精确断言不变，10项通过，不把这项环境噪音算作插件递归失效。

机器结果见[JSON](2026-10-14-delegate-remaining-acceptance-feasibility.json)，私有证据位于`.agent/acceptance/remaining-feasibility-20261014/`，0600文件/0700目录。

## 本批Claude真实菜单选择

在用户此前授权电脑查看的范围内，AI切到已有“Claude验收会话”；输入原为空、发送禁用。输入斜杠并筛选delegate，实际菜单含run/help/doctor/review/routing。用方向键和Tab补全review（不按Return、不点发送），输入呈现review命令节点及完整backend/paths/base/changes/context/dry-run参数提示。

随后清空输入并Escape，完整AX确认无残留参数提示、发送禁用，恢复原先可见会话。没有提交、重载、目标消息或本批触发的模型请求，不保存完整会话或截图。当前会话CLI版本本轮未独立核实，标未知。

## 下一批

[S7仅菜单实际执行方案](2026-10-14-delegate-s7-menu-plan.md)已备齐：已有Claude“Claude验收会话”两条指令，help一次及review/codex/dry-run一次，委托模型0次，主会话解释可能消耗额度。固定公共脚本帮助和dry-run的免费预览均退出0、四文件、backend_started=false。涉及向另一会话提交指令及宿主额度的具体授权尚未取得，不自行发送。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
