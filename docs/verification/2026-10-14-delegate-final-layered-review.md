# 最终分层验收供审

日期：2026-10-14。位置：`/path/to/delegate-plugin`，分支`codex/spec-guard-conventions-public`，HEAD `823c42383cf055ea8af99256618daf6212d10735`。

**当前结果：功能代码、双语合同与分层工程验收完成，Task2/6/8关闭；仅Checkpoint5人工验收待确认。** 用户已批准成功判据修订，不等于已接受本最终diff，也不授权提交、推送、发布。

## 成果与证据

- 两执行后端codex/claude-code，宿主与后端分开选择；review两后端只读，run保留Codex默认只读及显式write，doctor/help解释接入及迁移。模型/限制参数不混用、不失败切换。
- Claude CLI优先；Mac生产工具/OS/网络边界不变，不开放写入、Bash、MCP或派活，合作式递归入口保护不替代OS边界。
- 原标准免费157 Python/53 shell/19 eval和S5安装副本16/48结果保留；本批2权限/6生命周期方法、19项证据对账通过。私有夹具基类和长socket失败保留，修正没有改变产品断言。
- S2两真实宿主各4/4、核心pricing.py第7行核对、输入/配置/Git/清理验证，仅覆盖其固定源码和CLI版本；S6指定Read拒权、S7真实菜单到公共脚本及完整无模型预览单列，不替代完整审查。

详见[分层结果](2026-10-14-delegate-layered-acceptance-result.md)。

## 仍未验证与使用限制

- 模型主动Write/递归事件、认证刷新、自然异常helper变体、历史设置变化归属/间歇根因、长期稳定性、无差错自动UI输入，以及最新诊断源码重新完整双向live。历史未知保持未知；未观察不是通过。
- 仅当前Mac Claude后端；依赖已有CLI≥2.1.295、Node≥22.12、SRT0.0.79和GUI launchd，已有srt绝对路径须按次提供，不自动安装/改配置。当前本机缓存同步不等于发布。
- Codex通用run保留既有行为，detached进程限制不扩为Claude内核回收保证。模型/费用未知字段不猜，CLI估算不是账单硬上限，审查发现不授权合并或交付。

## Git实际差异

未按任务提交，下面列的是相对当前HEAD的**全部工作区未提交变化**，包括此前配套开发与历史证据，不声称全部属于本轮。取自git diff --numstat与git diff --no-index /dev/null对未跟踪文件的统计；没有暂存或提交。

新增190、修改42、删除1，共233文件。完整逐文件行数见[机器清单](2026-10-14-delegate-final-layered-review.json)。

| 目录 | 新增/修改/删除 | 增加/删除行数 |
|---|---:|---:|
| docs/decisions | 3/0/0 | +142/−0 |
| docs/en | 4/8/0 | +500/−34 |
| docs/verification | 136/2/0 | +13713/−4 |
| plugins/delegate/commands | 2/2/1 | +73/−53 |
| plugins/delegate/hooks | 0/3/0 | +4/−33 |
| plugins/delegate/scripts | 18/2/0 | +3096/−9 |
| plugins/delegate/skills | 0/1/0 | +24/−8 |
| plugins/delegate/tests | 22/2/0 | +3863/−24 |
| scripts | 1/1/0 | +113/−5 |
| spec | 1/4/0 | +322/−30 |
| tasks/claude-review | 2/0/0 | +1027/−0 |
| tasks/routing | 0/2/0 | +24/−0 |
| 其他仓库文件 | 1/15/0 | +204/−54 |

关键文件展开：

| 文件 | 状态 | 增加/删除行数 |
|---|---|---:|
| plugins/delegate/commands/review.md | A | +27/−0 |
| plugins/delegate/commands/run.md | A | +19/−0 |
| plugins/delegate/commands/delegate.md | D | +0/−23 |
| plugins/delegate/scripts/delegate_cli.py | A | +170/−0 |
| plugins/delegate/scripts/delegate_backend.py | A | +149/−0 |
| plugins/delegate/scripts/claude_review.py | A | +134/−0 |
| plugins/delegate/scripts/review_native.py | A | +175/−0 |
| plugins/delegate/scripts/review_macos.py | A | +394/−0 |
| plugins/delegate/scripts/review_result.py | A | +258/−0 |
| spec/claude-review.md | A | +281/−0 |
| docs/en/SPEC-claude-review.md | A | +277/−0 |
| scripts/validate.sh | M | +15/−5 |
| scripts/tests/test-validation-discovery.py | A | +98/−0 |

## 初始Plan之外的配套影响

AGENTS.md/CLAUDE.md、根目录Spec Guard/多模块导航属于此前明确要求的流程核对；scripts/validate.sh和发现规则测试属于Task9n私有产物发现修复；routing/hooks/evals及tasks/routing属于已有路由提醒修复。它们都在整工作区差异中单独列出，不包装成当前合同修订新增代码。大量docs/verification为版本固定的历史/当前证据，保留失败；历史Linux/SSH代码测试不构成第三生产后端。

本批合同/状态修订只改文档、任务和私有验证夹具，插件62产品文件与测试字节不变。没有新增未经说明的产品实现影响。

## 当前用户如何选择

Claude主会话：`/delegate:review --backend codex --paths <范围> -- <审查任务>`。Codex主会话：选择delegate的source-command-review，提供`--backend claude-code --paths <范围> --model sonnet -- <审查任务>`；Claude依赖路径按README按次提供。先加--dry-run核对范围；未指定后端默认codex，未知模型/宿主不猜。run仅codex。

## Checkpoint5确认范围

请审阅这份实际差异、版本分开的证据和未验证限制，回复“接受最终验收”即可关闭本地模块人工gate。只接受当前Mac功能与分层证据，不承诺未验证能力，不追认历史全部批准，不授权安装、新模型、认证/消息或提交/推送/发布。已有源码部分接受保持原含义。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
