# 本机启用已完成：Codex新源码与Claude本地加载核验

日期2026-10-13。仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。用户“继续 不要 总是停下来”承接已展示的[固定启用方案](2026-10-13-delegate-local-activation-plan.md)及待答确认，作为本批授权；隔离预验、正常Codex启用和无模型体检按同一范围推进，不重复询问。新增模型/安装/发布不继承本批批准。

## 实际完成

| 项目 | 结果 |
|---|---|
| 隔离安装 | 一次Codex0.162.1/Node24.18.0原生安装，四skill与62文件冻结包核对通过；只SessionStart，旧回调无输出；禁网和边界拒写探针通过，安装状态已清理 |
| 正常Codex安装 | 原Git来源及v0.4.0 ref改为本地仓库来源；官方remove/add/plugin add各实际执行一次，退出0且coalition回收确认；delegate保持enabled |
| 实际缓存 | doctor/help/review/run四迁移skill逐字节匹配，全部61个插件文件与已批准源码匹配；无source-command-delegate、无UserPromptSubmit注册 |
| 旧注册兼容 | 在实际安装路径直接调用原UserPromptSubmit注册命令，退出0、stdout/stderr均空；不等同真实主会话事件trace |
| 安装脚本入口 | 已安装--help通过；review --backend claude-code对hooks指定范围的working-tree --dry-run通过、backend_started=false；不是模型审查 |
| 无模型Claude体检 | 实际安装的doctor预检函数、现有srt0.0.79/Node24.18.0/原版Claude2.1.296通过，认证claude.ai/provider firstParty；5个进程边界回收确认 |
| Claude本地来源 | 不用plugin-dir覆写、不安装；原版2.1.296读取原user配置，--init-only日志明确从本仓库读delegate hooks/skills、加载4命令/1skill；退出0，回收确认 |
| 配置/源码 | 非delegate配置语义、Claude设置/登记及源码摘要未变；未复制凭据、改全局env或升级依赖 |
| 交付 | 没有审查模型调用、会话消息、提交、推送、tag或release |

[JSON事实及限制](2026-10-13-delegate-local-activation-result.json)保留分阶段事实、固定摘要和唯一CLI调用次数。当前本机是**未发布本地源码副本**，清单仍显示0.4.0；已发布v0.4.0和本副本不能凭版本号混同。成功依据是本地来源、文件/入口摘要和Hook变化。

正常备份目录为 `/path/to/user-home/.codex/backups/delegate-local-activation-9dx12qw7`，仅包含delegate必要来源/启用项、旧checkout/cache和原权限清单；0700/0600，不包含auth.json/钥匙串/token或整个用户配置。没有整体回写配置或改动其他插件设置。CLI可能维护CODEX_HOME内的临时路径/日志等运行元数据；非delegate缓存写入及凭据访问被本批策略禁止。

## 启动控制失败与已知非致命诊断

第一次正常阶段的Python3.12托管器没有发布ready，CLI backend_started=false，cleanup=confirmed。独立核对配置字节、旧checkout/cache未变，因此实际更新命令执行次数为0，原记录保留；并非移除失败后重复整个安装。已有Python3.12直接/minimal-env/本进程内核API探针通过，具体launchd启动根因未确定，不宣称整个Python3.12不兼容。

纠正仅在本批夹具中把进程托管与只读TOML解析拆开：已通过隔离预验的Python3.10托管，3.12只做只读解析。复核已知未执行状态后，才启动各一次正常CLI操作；原失败、备份和受限范围保留。产品执行代码、后端、系统Python配置和授权预算未改变。

Claude只读加载中禁网导致本地UDS监听非致命诊断；临时空工作目录也有缺少设置/记忆目录提示。它们不否定观察到的本地四命令加载，但不将启动结果扩大为日常环境所有组件正常。完整debug/原始stdout/stderr和临时配置均删除，仅保留必要加载事实。

## 如何使用与剩余范围

Codex选择delegate的`source-command-review` skill（CLI通过/skills），提供`--backend claude-code`审查由Claude执行；默认仍codex。源命令run/doctor/help相应迁移。旧注册即使尚在会话内也引用同一路径的新静默脚本；新skill目录是否已在当前UI刷新仍未观察，必要时刷新选择器或启动新Codex会话。

Claude CLI当前的本地marketplace已能原地读取本仓库四命令，不需本批重装；真实已打开的Claude主会话是否已刷新未知。用户可在自己的主会话使用/reload-plugins或新会话核对`/delegate:review/run/doctor/help`；本批没有自动操作其桌面或发送消息。

PATH仍无srt。现有绝对路径 `/path/to/private-evidence` 仅按次供本批体检，**未写入全局环境**。后续明确授权真实审查时，调用环境需提供DELEGATE_SRT_BIN；临时路径不是永久依赖部署。下面是后续调用示例，本批未执行模型：

```bash
DELEGATE_SRT_BIN=/path/to/private-evidence \
/bin/bash /path/to/user-home/.codex/plugins/cache/delegate-marketplace/delegate/0.4.0/scripts/delegate-exec.sh \
review --backend claude-code --repo /path/to/project --paths src --changes working-tree --model sonnet
```

实际模型、额度、主动工具越权/写入/再委托、认证刷新和原版异常helper仍未验收；Task2/6/8与Checkpoint3的完整条件保持未关闭。既有普通双向真实四文件审查记录仍各对应其固定历史源码，不追认为本批新版原生UI调用通过。本批启用已收束，不再次安装；下一阶段为当前宿主入口的交互核对与剩余受限真实验收，涉及新模型、会话通信或发布另按具体授权推进。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
