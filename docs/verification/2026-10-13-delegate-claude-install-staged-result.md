# Claude delegate 安装及四入口显示验收通过

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`；claude-review / Checkpoint2b / UI-001。

用户对具体“仅安装一次，再普通重载检查四入口”方案回复“继续”，本批已完成。Desktop原版CLI2.1.295离线执行user scope install一次，返回`outcome: ok`、退出0、内核coalition清理confirmed。实际安装缓存的61个非运行标记文件与固定源码逐一匹配，含review/run/doctor/help。delegate登记和启用恢复，其他配置语义不变。使用先前备份；不重复update/uninstall、不手改缓存、不访问认证、不更新其他插件或CLI、不改全局环境。

专用电脑工具定位既有“Claude验收会话”，普通`/reload-plugins`实际执行一次，收到`Reloaded: 7 plugins · 96 skills · 29 agents · 5 hooks · 0 plugin LSP servers`。操作期间两次工具报告用户切换页面，先读取最新界面；第一次选择会话未成功，第二次提交重载已实际成功，读到新消息28/29后没有再提交。未绕过工具保护或使用其他UI技术。

重载后直接打开斜杠菜单，AX文本和截图均可见 `/delegate:run`、`/delegate:help`、`/delegate:doctor`、`/delegate:review`，以及routing技能；旧`/delegate:delegate`已不在菜单。截图只在当前对话展示，没有声称保存本地PNG。菜单查看后取消选择并恢复空输入框，没有执行审查或模型任务。[完整机器记录](2026-10-13-delegate-claude-install-staged-result.json)。

UI-001仅针对安装内容与入口显示的Required缺陷现已关闭；此前两个失败批次的证据保持原样，不能重写成当时通过。实际依靠重新安装同步同版本源码，不能从0.4.0号推断内容一致，也不据此声明所有官方更新算法已证明。本地仍为未发布源码，未提交、推送或发布。

该批是零模型安装和显示验证，不能替代真实审查或主动工具越权验收。两向普通真实审查另有[同包成功记录](2026-10-13-delegate-remaining-acceptance-result.md)；真实模型主动写入/递归尝试、认证刷新、异常自然helper等仍未验证。模块保持BUILDING，下一步进入Checkpoint3的实际diff与限制人工审阅，不追加未授权模型批次。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
