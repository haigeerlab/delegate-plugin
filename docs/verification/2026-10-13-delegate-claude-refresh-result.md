# Claude delegate 正常安装刷新：已批准批次失败停止

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`；claude-review / Checkpoint2b / UI-001。用户批准原话：**“批准仅刷新 Claude delegate”**。

本批没有完成安装刷新。旧delegate缓存、仅该插件的登记/启用字段及权限已备份到专用私有目录。Desktop原版CLI2.1.295受OS禁网和限写边界控制，update执行一次，退出0、清理confirmed，明确返回“delegate is already at the latest version (0.4.0).”；只读核对仍是旧缓存，因此进入已批准的有限重装分支。辅助驱动初始只识别success/status键，误将CLI的已是最新结果标为未知；依据已经保存的退出状态和明确消息更正为成功无操作，保留初始分类，**没有再次执行update**。

uninstall `--scope user --keep-data --json`只执行一次，退出1、清理confirmed。原版CLI明确报告仍安装：更新settings需要先打开 `.claude/.cc-writes/settings.json.tmp.<pid>.<suffix>`，本批OS权限规则遗漏了这个原子写入暂存路径，因EPERM失败。该失败来自安装批次限写策略，不能归因于delegate后端代码或认证。按已批准方案的“失败/未知即停”，未执行install、重试、回滚或普通重载。

失败后精确核对：delegate登记/启用字段、marketplace、其他配置语义以及旧缓存20个非运行标记文件均未变。源插件61文件和原版CLI摘要仍匹配固定预览。专用电脑工具在既有“Claude验收会话”再次直接观察菜单：仍有help/doctor/delegate/routing，仍无review/run；没有发送命令，输入框恢复为空。未调用模型、访问认证、更新其他插件、改源码版本、提交或发布。逐项机器证据见[JSON](2026-10-13-delegate-claude-refresh-result.json)。

## 修正后的待批准批次

准备目录 `/path/to/private-evidence`。不重复update；重核固定源码/CLI和安装状态，重新备份仅delegate，执行user scope uninstall `--keep-data`一次，只有明确成功且登记消失后install一次，随后普通重载“Claude验收会话”并直接查看review/run/doctor/help。任何错误、未知、其他配置变化即停；不手改缓存，不自动回滚其他用户变化，不执行审查。

相对于已批准方案，只增加原版CLI必要的原子settings暂存写入规则：允许 `.claude/.cc-writes`目录的必要条目操作以及**仅** `settings.json.tmp.<pid>.<suffix>`文件；不允许任意该目录内容、认证、其他插件或持久数据写入。已在临时假HOME做实际sandbox-exec验证：原子settings替换通过、其他文件拒写、退出0/内核回收confirmed。该免费探针没有写真实HOME，不代替实际安装验收。

本批一次授权已执行至失败停止，修正后的重复卸载/安装须重新批准。依据[plan.md Checkpoint2](../../tasks/claude-review/plan.md)“未经单独批准不运行真实模型，不自行安装/更新插件或写全局配置”和本批明确停止条件。已有实施与电脑查看授权仍有效，不重复请求代码设计或普通只读查看授权。

模块仍BUILDING：功能代码和普通双向审查的成功证据保留；UI-001、主动工具越权/认证刷新/自然helper及最终人工diff检查点仍未关闭。下一步首先修复这次有限安装批次，不重新泛扫项目。

免费收束检查：当前启用Spec Guard阶段为BUILDING、5项未勾；产物3通过/0警告/0失败；本批涉及文档96个本地链接及JSON有效，`git diff --check`通过。产品实现未变，没有重复总套或模型验收。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
