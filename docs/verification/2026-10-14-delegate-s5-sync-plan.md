# S5：仅同步错误诊断修复

位置：`/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，模块 `claude-review`，Task9m 安装 gate。

Task9l 的源码修复与免费验证已经完成，见 [13文件结果](2026-10-14-delegate-error-diagnostics-result.md)。当前两宿主安装仍为 S3 固定源码，和最新插件仅相差 `scripts/review_result.py`、`tests/test-review-result.py` 两文件；命令和权限未变。此批只同步这份源码修复，不验证 S4 的实际后端原因或新增模型。

## 固定对象与执行顺序

专用目录 `.agent/acceptance/s5-diagnostics-sync/` 已备齐固定源码、候选控制器、验证驱动和假 HOME 探针结果。62 插件文件加 marketplace 共 63 文件，摘要 `62ba98f725163674720a62482211914d25c90ba1feb94b34ce8c157ffa715c5f`。旧 S3/S4 控制器、结果、备份及启动标记不改、不重跑。

1. 再核对源码/固定副本/已有二进制摘要及 delegate 当前登记，备份仅该插件缓存、必要登记/启用字段和原权限；配置中其他内容仅比较语义摘要，不复制完整配置或凭据。
2. Codex 0.162.1 使用现有本地 marketplace 执行 `plugin add delegate@delegate-marketplace --json` 一次，明确成功及内核回收确认后核对 62 源码及 4 迁移 skill。
3. Desktop 原版 Claude 2.1.295 执行 user scope `plugin uninstall delegate@delegate-marketplace --keep-data --json` 一次；明确成功后 `plugin install delegate@delegate-marketplace --scope user --json` 一次，核对 62 源码和登记/启用状态。
4. 两安装副本各核对 help/review/run 帮助、两后端 dry-run、跨模型及旧入口非法模型拒绝，共 16 项；结果解析回归各 24 项，共 48 项。dry-run 沿用四个合成文件，只核对范围与摘要，不启动后端或检查认证。

每条安装命令最多 30 秒，OS 禁网、零模型。任一失败、未知、清理不明或无关配置语义变化立即停止，不重试，不自动扩大写入或恢复其他会话的更改。卸载成功而重装失败时如实报告，保留备份供后续明确恢复，不隐瞒为成功。

## 实际边界与前置核验

复用 S3 成功批的限写策略，只开放该插件缓存、delegate-marketplace 同级 plugin-install/plugin-backup 的字母数字临时目录、必要原子登记写入及专用控制目录。凭据读取、钥匙串、网络和其他插件写入仍拒绝；Mac coalition 回收只处理本次启动进程。

既有 Node 24.18.0、Codex 0.162.1、Desktop Claude 2.1.295、控制器 Python 3.12.14 的摘要均核对未变。不安装依赖/升级 CLI，不修改全局环境、认证、其他插件；不重载会话、不跨会话通信、不调用模型、不提交/推送/发布。受控 PATH/HOME 仅用于本次进程和验证夹具，不写用户全局设置。

实际免费前置：假 HOME 两宿主 26 个写入边界案例通过，并核对凭据拒读和禁网；完整替换/故障回滚/清理两场景通过。初版替换探针随机生成了含下划线的 Python 临时名称，被字母数字规则正确拒绝；探针已改用匹配已核实官方路径形状的字母数字后缀，未扩大权限，原初版保留。未授权控制器在读取授权文件时停止，未创建真实备份/启动标记、未执行安装；源码和二进制摘要检查通过。

## 检查点

本批候选使用默认单次模式；不存在 S3 旧批接续授权。批准来源是当前人类回复“批准S5仅同步诊断修复”，执行前记录具体范围及预览摘要，再按独占标记运行；缺少授权或授权摘要不符均在任何安装前停止。S3 的单次安装和 S4 的模型授权均已消费。

新增安装必须确认的依据是模块 [plan.md](../../tasks/claude-review/plan.md) 的既有约束：“未经单独批准不运行真实模型，不自行安装/更新插件或写全局配置”。本次批准只覆盖上述同步；Task2/6/8 完整安全验收不因安装或假测试自动完成。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
