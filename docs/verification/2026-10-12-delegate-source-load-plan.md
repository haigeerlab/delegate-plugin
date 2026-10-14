# 下一批：Codex源码插件隔离加载（待批准）

日期2026-10-12。目标仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。源码已开发、两方向普通真实审查成功；本批补原生加载前置，不重做模型审查。

## 可审阅对象与授权原因

固定源码副本61文件已准备：[摘要和边界](2026-10-12-delegate-source-load-preview.json)。目录 `/path/to/private-evidence`。尚未运行安装/加载，也没有新增模型、登录、全局配置或日常插件状态变化。只在临时子进程设置CODEX_HOME，不改变当前会话的环境或真实 `~/.codex`。

[AGENTS.md](../../AGENTS.md)要求“付费 live 验证、委托给其他执行器、提交、推送及发布分别需要相应授权”；计划Checkpoint2进一步明确“未经单独批准……不自行安装/更新插件或写全局配置”。本批含安装到专用临时目录，故先取得该具体范围授权；本次不申请付费、委托通信、正常安装覆盖、提交、推送或发布。

官方[Codex高级配置](https://developers.openai.com/codex/config-advanced/)说明本地状态位于CODEX_HOME。本机Codex0.162.1 CLI help已核实实际子命令是 `plugin marketplace add` / `plugin add`，不是 `plugin install`。CLI原生安装/迁移要实际执行后才能确认；不使用未完成的app-server plugin协议。Claude官方[插件说明](https://code.claude.com/docs/en/plugins)支持--plugin-dir临时开发加载，但本批不启动Claude会话；后续真实slash行为另外明确，不把本批冒充它。

## 一批有限操作

1. 复核源码/Node24.18.0/Codex0.162.1固定摘要，创建私有writable、独立codex-home和无真实业务的工作目录；不读/复制认证文件、不运行认证或login探针。
2. 使用macOS sandbox-exec把子进程网络全部禁用，可写仅writable与/dev/null；原项目、源码副本、真实配置目录无可写授权。先用专用临时sentinel实际核对允许写和边界外拒写；无法建立边界即停止，不进入安装。
3. 用相同限制运行以下两条本机CLI命令，各仅一次、至多30秒。子进程PATH固定Node24和Codex目录，CODEX_HOME指向专用临时writable/codex-home，TMPDIR亦在writable；环境仅必要系统字段，不含API key/token。

```text
codex plugin marketplace add /path/to/private-evidence --json
codex plugin add delegate@delegate-marketplace --json
```

4. 在同一临时配置运行plugin list，核对安装路径确实在本批专用目录、delegate唯一、新review/run/doctor/help命令迁移产物存在且指向固定来源、旧source-command-delegate不存在；检查产物与权限/来源哈希。不调用命令内的执行器，不运行Codex exec或Claude -p。网络禁用导致远端目录不可读不等于本地加载失败，以本地条目与迁移产物核实。
5. 保存脱敏结果、固定错误阶段和必要文件摘要，检查原源码及可核对的设置文件未变。只清理本批自己创建的运行/安装状态，保留小型证据；不移除日常插件或修改源码缓存。

## 成功与停止条件

成功仅表示现有Codex CLI接受该源码插件，生成新命令迁移产物；不证明桌面UI展示、模型遵循命令、双向审查或完整安全验收。任一步身份/摘要变化、拒权、超时、不支持、结果未知或意外路径即停止，不重试安装、不升级CLI、不借用宿主凭据或自动降级。未批准不执行第1–5步；准备副本不是安装。


## 2026-10-12 已批准执行收束

用户“批准这批临时加载”后实际执行一次：禁网/拒写与固定版本前置通过，marketplace/add/list均退出0，但仅生成review/run/doctor，help缺失，完整迁移验收失败。已停止且清理临时安装状态，没有重试或模型调用。见[实际结果](2026-10-12-delegate-source-load-result.md)。前文待批准/未执行是原预览状态，本批批准已消费。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
