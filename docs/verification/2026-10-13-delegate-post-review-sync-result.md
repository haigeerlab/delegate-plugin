# S3真实同步结果：失败停止，窄暂存修正待批准

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，模块claude-review。用户“批准S3仅同步delegate”授权[原方案](2026-10-13-delegate-post-review-sync-plan.md)，本批已执行并停止，没有自动重试。

## 实际结果与副作用

- 固定63文件及CLI/Node/Python/原生Codex摘要核对通过；两宿主仅delegate缓存、选定字段和模式已备份，不复制凭据。
- 假HOME原安装限写探针：Codex11个、Claude15个写路径断言通过；两边网络拒绝及凭据拒读通过。
- 仅Codex add一次实际启动，退出1、failed，内核coalition清理confirmed；没有可解析stdout。Claude卸载/安装均0次，整个批次模型0次、会话重载/通信0次。
- Codex当前65缓存文件与备份逐字节一致（61旧源码+4迁移skill），Claude61源码与备份一致；选定及无关配置事实/模式均不变，源码和原版工具摘要未变。没有部分安装效果，无需自动回滚。

控制器原先在失败时也删除stderr，具体CLI错误没有保留下来，这是本次诊断缺口；不能猜成认证缺失或某个确定产品缺陷。已补固定类别和已知位置标签的脱敏诊断，在5个合成错误输入中验证凭据canary不入日志；不保留原始stderr或任意外部错误文本。此次已丢失的原错误不能补造。

## 有限诊断与候选修正

独立只读launchd探针能读取仓库和临时副本的公开marketplace清单，摘要一致、回收confirmed；没有安装/模型/全局写入。这不证明所有原版CLI拥有相同TCC访问事实。

只读查询原尝试两秒时间窗及codex/.codex路径的系统日志，出现同PID83746的三项拒绝：

| 操作 | 路径 | 判断 |
|---|---|---|
| file-write-mode | `.codex/tmp/arg0` | 元数据写入未放行；不自动增加权限 |
| file-read-data | `.codex/auth.json` | 既定凭据拒读边界生效；不开放认证 |
| file-write-create | `.codex/plugins/cache/delegate-marketplace/plugin-install-D9z7XE` | 原规则未允许同级安装临时目录，存在具体限写缺口 |

原安装命令PID未单独保留，日志只有时间/路径关联；不能把它冒充恢复的CLI错误或唯一根因证明。候选修正仅开放delegate-marketplace下plugin-install-字母数字临时目录树，其他marketplace/前缀/路径穿越仍拒绝。假HOME旧规则4项全拒、新规则仅目标通过，共8项实际OS断言通过；凭据和arg0权限保持原样。修正后真实安装尚未执行，不提前声称解决退出1。

## 准备好的修正接续（未授权，未执行）

位置和固定源码沿用原S3。复用原备份，先核对当前源/工具/配置/两缓存与失败后记录完全一致；不重新安装依赖、不重新跑已通过产品总套。新增一批仅：

1. Codex add再一次（这是新批的一次尝试，最多30秒），仅上述窄暂存规则修正；新的授权文件、started标记和result-resume.json，不覆盖第一批结果。
2. 只有明确成功、62源码/四迁移skill/Hook/无关配置/清理全部核对，才执行原未开始的Claude uninstall --keep-data一次及install一次，每条30秒。
3. 两边通过后安装文件help、两后端同四文件dry-run、跨模型参数拒绝；零模型、禁网、不重载/通信，不修改其他插件/认证/依赖或Git交付。任一错误/未知即停，不再重试，不自动回滚或放宽权限。

接续控制器和候选探针位于项目私有 `.agent/acceptance/post-review-sync/`；authorization-resume.json尚未创建。需要用户回复“批准S3修正接续”后才执行。这不是重复源码设计/开发接受；原S3明确失败即停，新的安装尝试必须单独授权。Task9k未完成，Task2/6/8完整安全条件未关闭。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
