# Claude delegate 刷新修正批次：卸载成功、安装失败停止

2026-10-13，位置 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，claude-review / Checkpoint2b / UI-001。

用户在上批具体“修正后仅卸载、重装各一次，再重载核对”请求后直接回复“继续”，本批按该具体范围推进。新备份位于 `/path/to/private-evidence`，固定原版Desktop CLI2.1.295和插件源码61文件；OS禁网、认证/其他插件/持久数据拒写，新增仅settings原子暂存规则。

**本批部分完成，当前delegate user安装登记及启用项已移除。** uninstall `--keep-data`一次成功，退出0、内核coalition回收confirmed；原版JSON明确`outcome: ok`，登记消失。临时驱动最初未识别ok，在退出0/明确消息/登记消失的联合证据下修正分类并保存初始值，未再次卸载。

随后install一次失败：原版CLI退出1，明确报告无法mkdir `.claude/plugins/cache/temp_local_1791871293026_me7aak`（EPERM）。官方本地安装先在cache下创建`temp_local_*`暂存目录，再放入目标缓存；已核实的本批规则遗漏这个安装暂存位置。CLI调用和进程清理结束均confirmed。按“错误/未知即停”，不重复安装，不重载，不自动回滚其他配置。

失败后的精确事实：其他配置语义不变；delegate user登记/启用均不存在；旧缓存仍存在，原20个非运行标记文件均未改变或删除，新增`.orphaned_at`标记；备份仍完整；失败的temp_local目录没有创建。持久数据写入被OS拒绝，命令明确要求keep-data。无模型调用，没有源码修改、认证访问、其他插件更新、提交或发布。[机器证据](2026-10-13-delegate-claude-refresh-fixed-result.json)分别保存两次执行、分类更正和实际残留状态，不能称刷新通过。

## 仅剩安装的待批准方案

准备目录 `/path/to/private-evidence`，授权文件仍pending，未执行新批。保留已成功卸载事实，**不再update或uninstall**。重核原版CLI、61文件、marketplace和无delegate登记，使用已有备份，执行一次：

```bash
claude plugin install delegate@delegate-marketplace --scope user --json
```

只有明确成功、其他配置语义未变且实际安装61文件匹配后，才在“Claude验收会话”普通`/reload-plugins`并直接查看review/run/doctor/help；不强制重载、不调用模型。出现错误、未知、额外插件或配置变化即停止，不重复执行或自动回滚。

新增OS写例外仅为CLI本地安装暂存路径 `cache/temp_local_<数字>_<小写字母数字>`及其子文件，目标仍限delegate缓存、必要安装登记及该插件启用字段。网络、源码写入、认证、其他已安装插件及持久数据仍禁止。已在专用临时假缓存实际验证：创建暂存/写入/移动到delegate目标通过，其他marketplace及temp_remote拒写；退出0、回收confirmed。该探针不写真实HOME、不运行Claude或模型，不能冒充安装验收。

这次失败不是delegate审查后端故障，而是安装批次对官方CLI暂存写入路径核对不完整。原批一次install已消耗且明确失败即停，下一次install需新批批准；依据[模块计划](../../tasks/claude-review/plan.md)的安装独立授权和具体停止条件。功能代码与普通双向真实审查证据不变；UI-001及完整安全验收尚未完成。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
