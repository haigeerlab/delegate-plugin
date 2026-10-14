# UI-001：Claude重载后仍显示旧delegate入口

2026-10-13，位置 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，claude-review / BUILDING。本批是用户明确授权的电脑只读查看，不是安装或新审查。

## 直接观察

用户先回答“四个入口都已出现”，随后澄清“我没注意到入口，我给你操作电脑的权限，你来自己查看吧”。此前Claude显示通过不能成立；Codex的独立确认保留。按用户对该操作的明确授权覆盖skill的默认人工显示规则，使用专用电脑工具查看Claude应用，未换用其他UI技术。

定位既有“Claude验收会话”，其对话确有`/reload-plugins`和`Reloaded: 7 plugins · 95 skills · 29 agents · 6 hooks · 0 plugin LSP servers`。输入框原本为空，只键入斜杠筛选菜单、未发送命令，查看后恢复为空。

| 层次 | 实际内容 |
|---|---|
| 斜杠菜单 | delegate:help、delegate:doctor、delegate:delegate、delegate:delegate-routing；没有review/run |
| 插件详情 | delegate-marketplace / 0.4.0 / 命令3 / Hook2，更新按钮禁用 |
| 命令详情页 | delegate、doctor、help三条旧命令，旧描述 |
| 已安装登记/缓存 | user scope，旧Git摘要38172b7e；缓存三旧命令和SessionStart/UserPromptSubmit |
| 本地源码 | doctor/help/review/run四命令；仅SessionStart |
| 当前marketplace登记 | 本地directory来源指向delegate真实源码仓库 |

确认的是**安装内容与源码不一致，而且会话重载未更新安装内容**。不能仅从按钮禁用或相同0.4.0号断言桌面内部完整解析算法；本机Claude CLI2.1.296源码初始化的四命令加载证据，也不能替代Desktop主会话2.1.295的实际菜单。

这是Required缺口UI-001，归入现有Task8。双向脚本审查成功仍有效，但Claude新入口显示验收未过，不能标完整完成。机器证据见[JSON](2026-10-13-delegate-claude-desktop-entry-mismatch.json)。查看期间没有启停插件、安装、全局配置修改、新审查、发送交接或Git交付。

## 官方接口与修复候选

使用Desktop自身原版Claude2.1.295，只在OS禁网/禁止HOME写入的边界执行update/install/uninstall各一次`--help`。三项退出0、回收confirmed，插件登记及settings摘要未变；不使用`--help`结果冒充实际安装通过。

[官方插件管理文档](https://code.claude.com/docs/en/discover-plugins#update-plugins-now)区分更新磁盘插件与重载会话，提供`claude plugin update <plugin>@<marketplace>`。本机help核实update/install的`--scope`及`--json`，uninstall还支持`--keep-data`；不使用默认scope、`--prune`或未审阅命令的`--yes`。

推荐下批**仅刷新Claude user scope的delegate**：

1. 复核已固定源码61文件、marketplace、原版CLI及旧安装摘要；备份旧delegate缓存和仅delegate的登记/启用字段及原权限到专用0700/0600目录，不复制认证、整个settings或其他插件。
2. OS禁网，只用已有本地directory来源。执行一次：

   ```bash
   claude plugin update delegate@delegate-marketplace --scope user --json
   ```

3. 若明确成功且实际加载路径/文件为新源码，跳过重装。若成功但只读核验确认仍旧内容，在同批预先获准的范围内用官方uninstall（保留持久数据）及install各一次；不手改缓存、不换marketplace、不更新所有插件：

   ```bash
   claude plugin uninstall delegate@delegate-marketplace --scope user --keep-data --json
   claude plugin install delegate@delegate-marketplace --scope user --json
   ```

4. 只接受安装登记指向/内容匹配新源码的事实；核对其他插件及非delegate配置语义未变。错误、权限拒绝、网络需求、并发配置变化或未知即停止，不盲目重试；报告可能部分效果。持久数据保留，不自动回滚用户其他改动。
5. 在既有“Claude验收会话”普通`/reload-plugins`后，直接查看菜单应有review/run/doctor/help；不执行新后端审查，不强制重载、不重启应用、不升级CLI/Node/SRT，不改源版本或发布。

本次电脑权限只授权查看，以上刷新会写Claude正常安装登记/必要启用项和delegate缓存，尚未执行。依据当前[计划Checkpoint2](../../tasks/claude-review/plan.md)的“未经单独批准不运行真实模型，不自行安装/更新插件或写全局配置”，须针对这次正常Claude刷新批准一次；此前正常Codex启用明确不含Claude重装，不能复用。

## 后续实际授权与结果

上节“尚未执行/待批准”保留为预览时事实。用户随后批准“批准仅刷新 Claude delegate”。本批update成功无操作，uninstall因遗漏settings原子写暂存路径被OS拒绝，失败即停，未install或重载；安装/启用/旧缓存未变。修正后的有限重装待新批批准，见[实际结果与修正方案](2026-10-13-delegate-claude-refresh-result.md)。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
