# S2恢复：依赖和边界通过，安装控制器失败后停止

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`；模块claude-review，BUILDING。人类回复“批准恢复并继续原S2”。本批没有模型调用、交接、reload或Git交付。

## 已完成与证据

材料保存在 `.agent/acceptance/s2-recovery/`，目录0700、记录0600，由新增项目 `.gitignore` 仅排除 `.agent/acceptance/`。以下均为本地验收材料，不是新增产品功能。

1. 一次安装固定 SRT 0.0.79 成功。使用Node24.18.0，官方npm registry、禁安装脚本/审计/基金请求；包lock的所有resolved来源和sha512 integrity均已检查。入口SHA-256 `3f5544de20b8a4bf9937b1ceaa59e18ca05758f0d6a18ee76e8273585e78817a` 与历史已使用文件相同。没有修改全局npm/登录/其他插件。npm零安装配置预检发现同一 `/dev/null` 不能同时作为user/global配置；实际安装改用两个独立的私有空文件，保持不加载用户配置的语义。记录：`dependency-install-result.json`、`dependency-integrity.json` 和锁文件。
2. 新合成夹具 `s2-recovery-1-not-original-bytes` 固定。新Git基准 `dcb56fcd2f1c16f675657dc274ccfc7f6cbf2d36`；只提交合成仓库基准，未提交delegate开发仓库。纳入审查仍为pricing.py/SPEC/PLAN/REVIEW_DATA四文件，excluded.py排除；新输入、上下文和61文件源码摘要见 `manifest.json`。不冒充遗失原字节或原基准。
3. 新SRT下实际Mac零模型权限/生命周期套14项通过（12.606秒），完整日志 `macos-boundary.log`。上下文capture核对确为四文件，无排除文件或扩大范围。这些结果不能代替真实模型验收。

## 本次安装效果与停止

先保存delegate缓存、原文件权限和仅该插件的登记/启用/marketplace字段；其他配置只保存去除delegate后的语义摘要，没有保存凭据或整个用户设置。

- `update` 一次：退出0、outcome=ok、updateOutcome=up_to_date、回收confirmed；仍差 `review_macos.py` 和两项对应测试，共3文件。没有将“最新版本”视为内容同步。
- 条件满足后 `uninstall --keep-data` 一次：退出1、outcome=failed、回收confirmed。官方CLI报告 `.claude/.cc-writes/settings.json.tmp.<pid>.<suffix>` 打开EPERM；delegate仍安装、启用，61个缓存内容仍旧。其他配置语义摘要、marketplace字段及登记/设置文件权限未变。
- `install` 未执行。没有再次尝试update/uninstall，没有自动回滚、手改缓存或跳过OS权限。

过滤结果 `refresh-result.json`、原执行控制器 `refresh.executed.py` 保留。错误是本次重建的**安装验收控制器**错误，不是审查产品隔离失效：把Seatbelt regex字面量当JSON字符串编码，反斜杠被重复转义，规则未匹配预期原子临时文件。

`installer-regex-probe.py` 在假HOME、OS禁网下实际复现：旧转义拒绝预期临时文件；正确Seatbelt regex字面量允许该类型，另一无关文件仍被拒写。证据 `installer-regex-proof.json`。没有用真实用户设置做写入复现。

## 已准备的具体接续（待新批批准）

修正控制器 `refresh-next.py` SHA-256 `feac25fb02d4775df721dc2239be2b5845e0de556d82f9189e37cb1136959f7a`；仅修正regex字面量编码，其他OS禁网/限写/凭据拒读范围不扩大。原执行代码和失败结果不覆盖。

1. 不重复SRT安装或update。重新核对固定61文件/新夹具/运行时/登记及配置语义，另备份仅delegate；差异或未知即停。
2. 原版Desktop2.1.295执行 `uninstall --keep-data` **一次**，明确成功且登记/启用消失，才 `install` **一次**；各30秒，OS禁网，范围仍限本插件缓存、官方local暂存、必要登记/设置的原子写入。错误/未知即停，不重试、不手改缓存、不自动回滚。
3. 安装后61文件逐一匹配才能普通reload既有“Claude验收会话”一次并直接查四入口。
4. 再继续原S2未启动的正向一次，成功且清理/输入/配置检查通过后，才一次指定交接和反向一次。正向sonnet/Read/8轮/180秒/CLI估算预算1美元，反向Codex默认模型/只读/180秒且无美元/轮次硬上限；不增加模型次数。目标仍需自身人类授权。

当前批次按[S2计划](2026-10-13-delegate-s2-plan.md)“任一失败/未知……即停止本批”停止。新的一次真实安装接续必须由人类授权，不能把修正后的复验追认为尚未消费的原卸载尝试。回复“批准修正接续”仅批准本节，不批准最终Checkpoint3、提交、推送或发布。

Task2/6/8完整安全验收、最新源码真实双向验收和Checkpoint3仍未完成。运行时及诊断保存方式已经改善；本次成功恢复不证明历史临时原始证据可以重新打开。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
