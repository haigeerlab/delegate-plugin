# S2：批准后前置核对未通过

2026-10-13，delegate-plugin / `codex/spec-guard-conventions-public`，模块 claude-review。用户明确回复“批准S2”；该授权已经取得，不再请求相同批次批准。本次仅只读核对，没有执行安装、模型审查或交接。

## 当前事实

- 批准对象中的 `/path/to/private-evidence` 不存在，无法复核原固定61文件的批准快照。
- 原合成仓库 `/path/to/private-evidence` 不存在；仓库保存了历史文件摘要和发现，但没有四个文件的完整原始字节，不能用重建内容冒充原夹具。
- 原 SRT 路径 `/path/to/private-evidence` 不存在。对本机 `.local`、Node24全局模块、`.cache` 和 Library/Caches 的候选查找没有找到可复用的已解包 sandbox-runtime 包；这不证明机器任何位置都没有副本。
- `/tmp`、`/private/tmp` 及本会话系统临时目录均未找到上述命名验收包。旧 S1 临时日志、diff包和控制器也不在记录路径。删除时间、执行者和原因未知，不能推断为重启清理。
- Claude 2.1.296、Node24.18.0、Codex0.162.1 JS入口及Desktop2.1.295安装器文件的 SHA-256 与原记录一致。没有调用认证、版本初始化或模型。
- 当前源码仍有61文件；正常Claude delegate缓存与其差异仅为 `scripts/review_macos.py`、`tests/test-review-native.py`、`tests/test-review-macos.py`。delegate安装与marketplace登记仍存在，没有修改这些记录。

## 分类与影响

这是**批次前置条件不足**，不是已启动后端的执行失败，不是模型审查通过或认证失败。本次安装0、模型审查0、交接0、重试0；没有费用或用量数据，不能写成零美元。

S2计划要求先复核固定输入、源码与运行依赖，任何错误或未知即停止。故后续update/uninstall/install、reload和两向模型调用均未开始。既往普通双向成功与免费验证的仓库摘要仍保留；失去临时原始材料降低可复查性，不能声称原始证据仍可打开。

## 下一步及需要补充的范围

原S2批准仍保留为历史授权，未消费模型尝试。继续前需要允许两个明确变化：

1. 为已不存在的四文件夹具建立**新的合成输入版本**，保留同样审查范围和折扣缺陷目标，但使用新文件摘要及新合成Git基准，明确不等同旧字节；固定源码清单、上下文、夹具生成材料和结果摘要保存到仓库内专用验收目录，运行暂存仍限私有临时目录。
2. 在项目专用 `.agent/acceptance/s2-recovery/runtime` 重新安装固定 `@anthropic-ai/sandbox-runtime@0.0.79` 及其必要依赖；缓存、锁文件和过滤后的诊断也只写同一专用目录。使用Node24.18.0，仅访问官方npm registry；`--ignore-scripts --no-audit --no-fund --save-exact`，user/global npm配置指向 `/dev/null`，不修改全局npm/认证/插件配置。增加仅排除 `.agent/acceptance/` 的项目 `.gitignore` 规则，避免将依赖和运行材料混入交付。先核对包版本、lock完整性/来源、入口摘要（与旧记录比较，不静默接受变化）及实际零模型边界，单次安装最多120秒，错误/未知即停，不自动重试。此项**不在原S2范围内**，不能自行安装。

补充范围获批并完成前置复核后，才按原S2顺序执行：仅Claude delegate同步、既有会话普通reload及四入口检查、正向一次、通过后一次指定交接和反向一次。保持原180秒、正向sonnet/Read/8轮/估算预算1美元及反向默认模型；不增加模型次数、不升级CLI或其他插件、不提交推送发布。目标会话身份与自身人类授权届时重新核对。

本次只记录实际条件；Task2/6/8完整安全条款和Checkpoint3继续未完成。依照[AGENTS.md](../../AGENTS.md)与[S2计划](2026-10-13-delegate-s2-plan.md)，新增依赖安装和已变化的批准输入需补充确认，不能靠原批次批准自动扩大。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
