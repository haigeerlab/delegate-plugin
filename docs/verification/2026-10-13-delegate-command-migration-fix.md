# help命令漏迁移：根因与修正

日期2026-10-13；仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。本轮仅做源码修正和免费验证，未再次安装插件或调用模型。

## 根因已确认

对应本机版本的官方发布标签 `rust-v0.162.1` 指向commit `092d3acd6bec3e3a14bdc7e7a2810ab628ab759d`。[插件迁移代码](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/command_migration/plugin.rs#L17)把生成skill上限设为4000字节；[导入循环](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/command_migration.rs#L165)超限直接跳过，不使安装失败。计数对象是UTF-8渲染结果，不是源文件字节数或字符数。

按该发布版本[渲染格式](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/command_migration.rs#L397)计算，上一批固定help源文件3913字节，生成skill4043字节，因此未生成；doctor1038、review3528、run1843均在上限内。其余三个计算结果与上一批实际生成skill逐字节完全一致，源码规则和真实产物相互核对。没有保留字或argument-hint原因的证据，不按这些猜测改接口。

## 最小修改

- help保留CLI帮助入口、后端/模型选择、范围、权限、成本/状态、日志及迁移说明。删去重复的历史验收细节，压缩预检诊断，详细记录仍在原docs/verification中。
- 新增test-command-migration.py，按本机版本已核对的渲染格式检查所有源命令的UTF-8大小，另验证中文字符和包装开销不能按字符数忽略。纳入免费validate.sh；中英文贡献指南同步这项兼容约束。
- 不改变后端执行、认证、OS权限、清理、参数或命令名称；不依赖手改安装缓存。新help渲染3586字节，距4000上限414字节。

## 验证与限制

回归先在修正前失败：当前help为4073字节（此前状态说明更新产生了与原冻结批次4043字节的差异），只有help超限；精简后两项通过。原生三个产物的格式核对及固定官方源码摘要见[JSON证据](2026-10-13-delegate-command-migration-fix.json)。

完整免费总套140 Python/53 shell/19 eval通过。首次工具沙箱内总套退出1，唯一错误是/bin/ps被拒，影响已有假管理器helper清理测试；保留失败记录。原测试在沙箱外按原断言通过，再运行全套退出0，没有跳过/删改断言。该环境差异不作为产品修正，不把首次失败写成通过。

这证明根因与离线修正，不等于新help已在原生宿主加载。上一批安装失败结果保留；[修正后的单次临时加载预览](2026-10-13-delegate-source-load-fixed-plan.md)已准备，待独立批准后才执行。此前双向普通真实审查证据保持，完整模型主动越权/认证刷新/异常helper和新slash体验仍未完成。未提交、推送或发布。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
