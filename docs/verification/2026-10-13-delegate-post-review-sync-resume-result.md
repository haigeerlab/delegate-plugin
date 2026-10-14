# S3修正接续：第二批失败，完整替换流程候选已准备

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，claude-review。用户“批准S3修正接续”批准仅增加plugin-install临时目录规则，实际Codex add新批一次仍退出1/failed，清理confirmed。本批已停止，不进行第三次安装；Claude卸载/安装仍各0次。

## 实际状态

脱敏stderr602字节，固定类别permission_denied/installation_failed、位置codex_cache；没有可解析stdout。Codex65文件、Claude61文件均与最初备份逐字节一致；选定/无关配置事实及模式未变，源码与二进制摘要未变。累计两次Codex add，零模型、重载、通信、依赖安装或Git交付。

只读系统日志查询本批时间窗显示PID60218拒绝file-write-create `.codex/plugins/cache/delegate-marketplace/plugin-backup-i65YEg`，另有arg0写模式/auth.json拒读。PID仅由时间/路径关联，不冒充保留的原命令身份；stderr类别和后续官方源码与安装备份目录缺口相符。凭据仍禁止读取，arg0权限未放宽。第一批[原结果](2026-10-13-delegate-post-review-sync-result.md)保留，不覆盖或追认。

## 对应版本官方源码核对

[store.rs](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/store.rs#L515)的同版本替换完整路径：在选定marketplace根创建plugin-install暂存树，复制源码、生成迁移技能；创建plugin-backup树，将旧插件根移入其中；激活新根，失败时尝试恢复旧根；清理临时树。远端身份元数据删除位于选定插件根，原规则已包含。不使用Git/远端路径的安装流程。

[CLI本地分支](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/cli/src/plugin_cmd.rs#L173)及[manager](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/manager.rs#L2128)在安装后设置选定plugin enabled；[loader本地分支](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/loader.rs#L1655)直接使用本地来源，不需要Git源暂存权限。配置编辑器子源码抓取不可用，本轮不扩配置限写范围；原配置原子路径通过合成测试，实际CLI写入仍待验证。此调研仅读取公开官方源码；正常安装子进程保持OS禁网，未以安装器联网。

此前只补暂存目录，对替换流程核对不完整，造成第二次仍失败。现在候选规则同时限定plugin-install和plugin-backup两种临时名（仅delegate-marketplace，字母数字随机后缀），不开放整个缓存根、其他marketplace、凭据或arg0。

## 新免费证明

假HOME在候选OS策略下完成两场景：成功替换（暂存/复制/模拟迁移/旧根备份/新根激活/临时树清理/配置原子替换）；模拟激活故障后旧根恢复及临时树清理。两场景均验证其他插件和TOML无关字段保持、非法临时前缀/其他marketplace/源码实际EPERM或EACCES拒写、凭据拒读。

强化探针首轮误把预置非法前缀目录也当清理目标，断言失败；纠正为仅核验真实临时命名并要求非法目录保留后，两场景通过。不是删减产品断言或把真实安装改为通过。该探针没有执行官方安装CLI，不能替代实际安装成功。产品源码62文件未修改，不重复148/53/19总套。

## 准备好的下一具体批次：完整替换接续（待批准）

复用原固定源码/工具和备份，先核对源码、配置与两缓存仍与失败后状态相同。仅增加已核对的plugin-backup临时目录规则，其他S3权限和行为保持；新授权文件authorization-complete.json、各动作-complete-started和result-complete.json，不覆盖前两批。

- Codex add第三批一次，最多30秒；实际输出、62源文件、四迁移技能、Hook、配置语义、清理均明确通过才进入Claude。
- 原尚未执行的Claude卸载保留数据一次、安装一次，每条30秒；限写规则不变。
- 完成后安装文件help、两后端同四文件dry-run和跨后端模型拒绝，零真实模型，禁网，不重载或发送消息；不修改其他插件、依赖、认证、环境或Git。

任一错误/未知即停，不重试、不自动放宽权限或人工回写整个配置。官方CLI本身的缓存替换失败恢复由其原流程负责，控制器不自行全局回滚。仍不能承诺一次关闭所有权限/CLI缺口；新的实际安装尚未执行。需要人类批准“S3完整替换接续”后才启动。Task9k未完成，原源码Checkpoint3接受不重问，Task2/6/8完整安全条款不降低。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
