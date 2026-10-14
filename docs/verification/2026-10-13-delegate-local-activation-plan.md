# 本机源码启用方案（待批准，未执行）

日期2026-10-13。仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。源码开发和最新免费142 Python/53 shell/19 eval已完成，本批只准备启用方案，没有新增安装、模型或全局配置写入。

## 当前核实

| 对象 | 只读事实 | 不作的推断 |
|---|---|---|
| Codex0.162.1/Node24.18.0 | delegate已启用；来源为GitHub marketplace，旧源码commit38172b7e；缓存3条旧命令、含UserPromptSubmit；本轮仍收到旧提醒 | 不把源码修改当作当前安装已修复 |
| Claude2.1.296 CLI及登记 | marketplace指向当前本地仓库；登记缓存仍为旧0.4.0，3条旧命令/旧Hook | 缓存旧不证明真实Claude主会话加载根目录；主会话未知 |
| 新源码 | 4条命令review/run/doctor/help，仅SessionStart；prompt/route兼容入口零探测/零输出 | 不是新发行，不能由0.4.0版本字符串识别源码差异 |
| Claude审查依赖 | 当前PATH没有srt且无DELEGATE_SRT_BIN；已有临时srt0.0.79可供单次调用 | 安装delegate不自动安装/配置依赖，不等于Claude后端条件已满足 |

[固定62文件、CLI/Node/native摘要、命令及边界](2026-10-13-delegate-local-activation-preview.json)。冻结目录 `/path/to/private-evidence`；bundle SHA-256：`9a9b413d5d560dc1ba77421d585e8ba02fe5de6e8eca722e289ef582c9274147`。冻结内容为当前61个插件文件加marketplace清单；未变更源版本号，不创建tag/release。

## 一次批准包含的执行范围

1. **隔离预验，先执行且只有通过才进入正常安装。** 独立CODEX_HOME `/path/to/private-evidence`；OS禁网、禁止临时边界外写入和日常凭据读取、不复制登录状态。官方CLI marketplace add、plugin add、plugin list各一次，每条最多30秒；实际新缓存四个skill/来源文件/只有SessionStart须匹配固定源码，旧delegate skill不得存在。用install结果的installedPath核对缓存，不再把list的source.path当安装路径。通过后清理隔离安装，仅保留小型证据。
2. **正常Codex启用，仅delegate。** 先复核固定源码、二进制、旧来源/缓存和配置未发生未预告变化；备份必要delegate marketplace来源字段、插件enabled标志、旧delegate缓存和旧marketplace checkout到专用0700/0600目录。不备份auth.json、钥匙串、token或整个配置；未知配置字段/凭据URL/其他并发修改即停。使用已有Python3.12.14标准库tomllib核对配置语义，不安装解析依赖。
3. 按下列三条官方CLI命令，移除旧Git marketplace登记/checkout、添加本地仓库来源、重装同一delegate。改为本地开发来源，是为了取得未提交源码；以后远端发布后的来源切回另行处理。不要直接编辑缓存。当前marketplace只有delegate；发现其他插件或未知改动即停。
4. 独立读回：delegate仍启用、来源local→本仓库、实际61文件/四迁移skill与摘要匹配、无UserPromptSubmit、无旧delegate技能；不相关配置语义保持。安装后用已有绝对srt路径做一次无模型后端doctor，报告认证/隔离/依赖条件；不登录、不降级、不调用审查模型。

```bash
codex plugin marketplace remove delegate-marketplace --json
codex plugin marketplace add /path/to/delegate-plugin --json
codex plugin add delegate@delegate-marketplace --json
codex plugin list --available --json
```

每个修改命令最多30秒，一次，不重试；隔离/正常各安装一次。以上尚未运行。全部本地操作禁网，不刷新远端marketplace；没有Codex exec或claude -p。运行时和源码摘要不符、任何命令/校验/权限失败即停，保存脱敏状态；正常阶段部分变化须明确报告，不自动整体回写配置覆盖其他并发修改。选定备份供后续针对性恢复，不宣称三条命令组成跨步骤原子事务。

**本批不包含：** Claude安装/卸载/设置变更、自动发送另一会话消息、重启应用、Node/CLI/srt安装或升级、全局PATH/env改动、真实模型/额度测试、Git提交/推送/发布、其他插件或LIVE-SAAS修改。

源清单仍显示未发布0.4.0；成功判据是来源/文件摘要/四入口及Hook变化，不是版本号。此前临时安装授权已消费，本批需新的具体批准，但不再请求已完成设计/开发的批准。

## Claude衔接与权限说明

当前官方[加载规则](https://code.claude.com/docs/en/plugins/loading#in-place-and-copied-plugins)说明，本地marketplace相对路径插件可原地加载，在新会话或/reload-plugins生效，无需仅为此增加版本。实际Claude主会话加载哪一份仍未知，本批不贸然更新或卸载Claude，也不通过电脑操作其桌面应用。后续按真实主会话读回根目录/四入口/无每轮Hook，另列验收，不能由安装登记或本次无模型预验代替。

已有srt：`/path/to/private-evidence`（0.0.79），只按次设置DELEGATE_SRT_BIN用于本批doctor；不会写入全局环境。临时路径不是永久依赖部署，本批不保证重启/清理临时目录后仍可用，后续永久依赖方案另说明。

依据Codex0.162.1[marketplace add](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/marketplace_add.rs#L123)，同名不同来源须先remove；[remove](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/marketplace_remove.rs#L49)处理选定marketplace配置及checkout；[store.install](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core-plugins/src/store.rs#L304)会重新暂存并替换同版本缓存。因此不使用不存在的codex plugin upgrade，也不把Git marketplace升级误当工作树安装。

需要批准的依据是[现有计划Checkpoint2](../../tasks/claude-review/plan.md)： “未经单独批准不运行真实模型，不自行安装/更新插件或写全局配置。” 本批会修改日常Codex的delegate来源和缓存，普通继续不替代这项具体批准。


## 本批实际收束（2026-10-13，report）

用户“继续 不要 总是停下来”承接本批具体启用范围。隔离安装一次通过后，正常Codex source切到本地并实际重装一次；4skill和61文件匹配、只SessionStart，旧注册命令直接调用无输出，非delegate配置语义/Claude设置/源码未变。Python3.12控制失败时CLI未启动、配置/cache未变，记录保留；分离解析/托管后执行首次实际CLI命令，不重复安装。已有srt按次无模型体检通过；Claude原user配置只读初始化实际从本仓库加载4命令，未安装/更新它。CLI、原认证及回收已核实，模型/额度/真实主会话UI仍未验。无凭据复制、全局env改动或Git交付。[结果与限制](2026-10-13-delegate-local-activation-result.md)。此前“待批准/未执行”是计划形成时状态，不再请求已执行批次批准。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
