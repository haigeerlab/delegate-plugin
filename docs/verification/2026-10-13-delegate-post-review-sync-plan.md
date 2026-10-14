# S3：仅同步本机两宿主的delegate（待安装授权）

**实际结果：** 用户已批准原S3；Codex add一次退出1，清理确认、源码/配置/两缓存不变，Claude未开始。本批按失败即停收束，原“待批准”是准备时状态。窄暂存修正已通过假HOME8项断言；[结果与新批接续](2026-10-13-delegate-post-review-sync-result.md)尚待单独批准。

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，模块claude-review。用户在具体Checkpoint3接受请求后回复“继续”，按上下文记录为接受当前源码及已展示的未验证清单；这不是完整Task2/6/8验收，不含安装、模型或Git授权。当前仅准备本批方案，未执行安装。

## 已准备的对象

当前插件62文件，加marketplace共63文件，已冻结到项目私有忽略目录 `.agent/acceptance/post-review-sync/source/`；完整摘要、工具路径及指纹见同目录上级preview.json。bundle摘要：`7b4dd67c8814d94f41da1d37850205d9ad171c0a6cf29314661485a24f5b6a07`。本轮源代码已通过148 Python/53 shell/19 eval；不重复总套。

两宿主delegate已启用，marketplace均指向本仓库；历史实际缓存路径与当前源码比较，Codex有10文件不同，Claude有7文件不同。Codex差异还包括此前S1监督修复，不能仅同步Claude。版本字符串仍0.4.0，不能作为内容一致的判据。

原版管理CLI：Codex0.162.1/Node24.18.0、Claude Desktop2.1.295；二进制摘要已冻结。三项管理命令帮助已在OS禁网、拒绝全部文件写入时核对。默认沙箱不能启动嵌套sandbox-exec，转到外层后相同拒写帮助成功；不是安装失败。默认Python3.10.7没有tomllib；选用现有Codex内置Python3.12.14及标准库，不安装Python或解析依赖。

## 请求的一次执行范围

1. 重核源码62文件、marketplace、CLI/Node/Python摘要、两宿主仅delegate的来源/登记/启用字段及现有缓存。运行安装权限路径的零模型合成探针，允许官方原子暂存路径、拒绝无关插件和配置；通过才继续。任何前提变化/失败即停，不自动修正全局状态。
2. 备份仅两宿主delegate缓存、必要登记/启用/来源字段及文件模式到本批0700/0600目录。配置只保存选定字段和无关语义摘要；不复制auth.json、钥匙串、凭据文件、整个用户配置或持久业务数据。
3. Codex：现有本地marketplace不变，只执行官方plugin add一次，最多30秒。根据本次JSON的installedPath读回，逐个核对62源文件，以及4个自动迁移技能、只有SessionStart、旧delegate命令不在；不是直接修改缓存。无关配置语义及其他插件保持。若输出无效、未知或不匹配即停，不继续Claude。
4. Claude：已确认同版本update曾明确无操作，本批不重复update。先官方uninstall --keep-data一次，明确成功后install一次，每条最多30秒；user scope、仅delegate、本地已登记来源不变。读回启用/登记、62文件全部摘要及四条源命令；出错/未知/无关变化即停，不重试、不自行回滚。
5. 两边全部成功后只执行安装文件的help和两后端review dry-run，用既有S2四文件合成输入、原基准和明确Read范围核对等价信息及新模型校验失败分支。不运行版本/认证/模型探针，不运行codex exec或claude -p。记录清理事实和已审/未审范围；dry-run不冒充真实审查。

具体安装命令（均未执行）：

```bash
codex plugin add delegate@delegate-marketplace --json
claude plugin uninstall delegate@delegate-marketplace --scope user --keep-data --json
claude plugin install delegate@delegate-marketplace --scope user --json
```

## OS边界和停止条件

沿用现有MacBoundary监督/本次进程身份及清理机制，原版CLI的每条命令均OS禁网、默认拒写；仅开放本批控制/日志目录、选定delegate缓存及官方安装器必要原子登记/设置暂存。Codex可创建必要临时安装/路径元数据，但不可改其他插件内容或无关配置语义；所有实际写入根在执行前固定并用合成目录探针验证。Claude复用已通过的settings原子暂存、.cc-writes及temp_local规则，不再次使用历史错误双转义。禁止读凭据文件和钥匙串；源码根拒写。

每条修改命令本批一次、30秒，无自动重试/后端切换。非零、空/坏JSON、超时、取消、清理未知、源码或无关配置变化立即停止后续动作，报告部分安装状态；不把卸载/安装当原子事务，不自动覆盖并发配置。任何必须扩大限写范围的情况另形成具体修正范围，不自行放宽。

**不包含：** 两宿主UI重载/重启或发送会话消息、模型调用、认证检查/刷新/登录、srt/Node/CLI升级、其他插件更新、marketplace切换、全局环境修改、Git提交/推送/发布。没有UI重载的本批结果只证明安装文件一致，不证明现有会话已采用新内容。S2模型/交接授权已消费，不延伸到本批；Task2/6/8完整安全缺口不勾完成。

## 授权原因和下一步

AGENTS.md明确“付费live验证、委托给其他执行器、提交、推送及发布分别需要相应授权”，既有模块计划还明确“未经单独批准不运行真实模型，不自行安装/更新插件或写全局配置”。前一个Checkpoint3接受请求明确排除了安装，因此本批安装需要新的具体确认，不重复设计/源码成果确认。

批准“S3仅同步delegate”后，先重核固定输入并跑合成限写探针，再按上述最多三条正常安装命令执行；任何失败即停。通过后仅保存本批安装/无模型结果，下一步现有会话加载及真实模型验收另按具体授权处理。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
