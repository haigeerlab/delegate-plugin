# 修正后单次临时源码加载（待批准）

日期2026-10-13。仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。[根因与免费修正](2026-10-13-delegate-command-migration-fix.md)已完成；上一批失败即停且已清理，原安装授权已消费。

新固定目录：`/path/to/private-evidence`。[62文件摘要、Node/CLI/原生二进制及驱动摘要](2026-10-13-delegate-source-load-fixed-preview.json)已落盘。没有运行preflight或install；CLI版本仍为0.162.1、Node24.18.0，原生二进制摘要与上一批一致。不升级运行时或修改日常缓存，源码清单仍为未发布0.4.0。

批准范围只包含这一个新批次，沿用[上一批边界](2026-10-12-delegate-source-load-plan.md)：sandbox-exec禁网、只有新writable与/dev/null可写，源码/真实设置只读；CODEX_HOME仅在子进程指向新writable/codex-home。没有登录、复制凭据、模型调用、委托消息、日常插件变更或Git交付。

1. 先复核固定输入/CLI/Node/原生二进制摘要，再以原限额做一次实际允许写/边界外拒写/禁网探针和版本检查。失败即停。
2. 同一边界添加本地固定marketplace、安装delegate各一次（每条最多30秒），随后读一次临时plugin list；不重试。

```text
codex plugin marketplace add /path/to/private-evidence --json
codex plugin add delegate@delegate-marketplace --json
```

3. 必须生成source-command-review/run/doctor/help全部四个迁移skill，旧source-command-delegate不存在；路径必须在本批目录、来源和内容匹配固定源码、产物大小与预期一致。新驱动在命令集合不符时保存固定观察字段，明确migration_commands_mismatch，不再用无定位AssertionError作唯一诊断。
4. 独立核对原源码与已记录设置未变，保存小型脱敏证据并清理仅本批安装/运行状态。任何拒权、输入变化、失败、超时或未知即停止，不切换CLI、放宽边界、升级或再次安装。

成功只关闭当前CLI安装/转换的四入口前置；不声称桌面UI命令调用、模型遵守提示词或完整安全验收通过。[模块计划](../../tasks/claude-review/plan.md) Checkpoint2要求安装另行授权，故未批准不执行此批。批准不扩展到实际日常加载、新模型调用或发布。


## 2026-10-13 已批准执行收束

用户“继续”及随后“批准这一次临时复验”对应同一个已执行批次。三条CLI命令各一次全部成功；驱动误把source.path当缓存而退出1，原错误保留。通过只读真实缓存核对，四个迁移skill及大小/内容全部匹配固定来源，见[结果](2026-10-13-delegate-source-load-fixed-result.md)。未重试安装或执行修正驱动；本批临时安装已清理，授权已消费。前文待批准是历史预览状态，不再要求同一批确认。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
