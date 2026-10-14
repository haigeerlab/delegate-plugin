# 反向第四批当前预览：重启后宿主与实际CLI入口

日期2026-10-12。仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。用户“已重启 claude”只推进重启后的只读验证/准备，不当作本新批次付费或通信批准。旧第四批0.160.1预览保持历史，不执行。[当前固定摘要](2026-10-12-claude-review-mac-reverse-fourth-current-preview.json)。

## 已确认前置条件

“Claude验收会话”在受支持目录中唯一可见，重启后的新Claude内核身份和原版2.1.295可执行摘要已固定。该真实会话的SessionStart环境文件已经写入Node24.18.0的PATH/NVM_BIN/NVM_INC；只读检查文件仅含修复helper的三项导出，用这个实际文件覆盖旧Node12 PATH后，免费Node/Codex版本检查成功。未从当前Codex冒充Claude实际Bash工具调用，也未启动审查模型。[Node修复及重启证据](2026-10-12-node-environment-repair.json)。

本机有两份CLI：pnpm入口仍为0.160.1；Node24目录中的入口为0.162.1，修复环境实际选择后者。上次所说“当前CLI0.162.1”是PATH选择变化，不能推断旧安装已经升级或被覆盖。当前预览固定实际选择的0.162.1入口/摘要，驱动在marker前验证实际PATH选择及CLI版本一致，防止摘要校验旧入口却执行新入口。

原版0.162.1 --version、所需exec选项、指定四项关闭功能的features list均免费通过；未验证远端、认证或额度。未自动安装、切换插件、登录、发送消息或再次运行旧驱动。

## 一次真实验收范围

- 主会话：Claude Code“Claude验收会话”，2.1.295，固定重启后身份/祖先；身份变化停止，不自动更新。
- 后端：实际PATH选择的Codex CLI0.162.1；现有Node24.18.0路径/版本/摘要固定，只前置本次子进程PATH。模型CLI默认，可靠实际模型证据缺失则unknown，不猜测。
- 同样四个合成文件：src/pricing.py、REVIEW_DATA.md、SPEC.md、PLAN.md；固定原Git基准、各文件/上下文摘要，排除excluded.py，须干净，不扩为其他项目扫描。
- 当前源码公共 `delegate-exec.sh review --backend codex --context`；只读沙箱和有界inline输入，关闭shell/apps/plugins/multi_agent，搜索禁用、MCP为空；不执行源码、改文件或再次委托。
- 一次运行/180秒，Codex本封装无美元或轮次硬上限，目标Claude交接与模型可能耗用额度。失败、未知、拒权或任何固定事实不符停止，不重试或fallback。
- O_EXCL单次marker标明wrapper尝试，非API计数；独立核对报告、定位证据、触发条件/影响、覆盖/未审范围及输入/Git和清理限制。Codex保留进程组清理，不证明detached后代全无。

## 免费准备结果与限制

新目录/驱动、AST/源码/CLI/Node/输入摘要、同等任务的public dry-run通过：四文件5,036字节、180秒、backend_started=false、采集缺口为空。所需参数/四关闭feature值已用实际0.162.1核对。新marker/logs/result/dispatch均不存在，未发新消息或运行模型。

真实Claude Bash直接工具版本查询尚未观察，此证据只确认真实SessionStart环境生成和官方加载语义下的本机版本执行；真正反向审查仍未通过。新斜杠命令未实际加载/安装，本批直接绝对源码调用，不能冒称斜杠UI验收。仅更新验收夹具，不修改产品代码；沿用138 Python/53 shell/19 eval免费结果。

## 新批批准 gate

需人类批准本当前第四批：向已有“Claude验收会话”发送一次交接并执行上述一次真实审查。目标仍须满足自身的人类授权和权限要求。批准后首步复核当前固定身份/源码/CLI/Node/输入与实际CLI选择，再单次唯一选路/发送并只读核对匹配回执及本次产物。身份/输入变化或结果未知/失败停止，不安装、提交、推送、发布或自动重试。

## 单次交接后发现驱动顺序错误，未执行

用户“可以”后单次联系，目标关联回复指出logs先引用后赋值，未执行、未消耗一次审查。来源无模型实际复现并修正，见[纠错预览](2026-10-12-claude-review-mac-reverse-fourth-fixed-plan.md)。旧驱动不再使用；补充消息未发，原一次审查批准仍保留，不重新索取模型授权。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
