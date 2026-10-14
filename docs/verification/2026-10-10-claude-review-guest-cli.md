# 当前 guest 整合与原版 CLI 无模型验收

日期：2026-10-10；仓库 `delegate-plugin`，分支 `codex/spec-guard-conventions-public`，基准 HEAD `823c42383cf055ea8af99256618daf6212d10735`。用户“继续”承接上一轮具体临时安装/复验预览；本批不包含登录、模型请求、宿主凭据复制、插件安装升级、全局配置或 Git/外部交付。历史预览与离线证据保存在[前一记录](2026-10-10-claude-review-integration.md)，不回写其当时结论。English readers: administrative evidence in Chinese; [bilingual contract](../en/SPEC-claude-review.md).

源码候选已开发，处于第 5 阶段验收。此次完成实际 guest 无模型整合和原版 CLI 接口检查，尚未完成真实双向模型审查。**不将实际 OS + 假 CLI 或原版 help/auth smoke 计作真实审查。**

## 固定环境与安装范围

唯一临时根 `/path/to/private-evidence`，0700；独立 HOME/TMP/LIMA_HOME，专用 guest `delegate-review`，2 vCPU / 4 GiB / 16 GiB sparse disk。实际 effective config 核对 plain、VZ arm64、无 host mounts/共享、静态转发、普通 provision、agent/X11/用户公钥导入，containerd/Rosetta 关闭。仅使用本批新建 SSH key。下载总计约 520 MB，收尾前实际目录占用 2,064,380 KiB，低于批准的 20 GiB 上限。

| 对象 | 固定版本/来源 | 实际摘要 |
|---|---|---|
| Lima | 2.2.1，官方 GitHub darwin arm64 包，38,328,082 bytes | SHA-256 `9e9eacce88f37e185c346bad73aa6136f738d8cdf8c3bb23cd42b071824bc66e` |
| Debian | 13 arm64 cloud 20261001-2618，337,510,400 bytes | SHA-512 `d8470b8c6c38fead046c794b5800a5a7b96672d5bcf543cc230ceb0c4b8ace05ed341a0c8928045422243fde26b2f1f2f58e99244c65709ffda2e3d4b674dd5a` |
| Node | 22.22.0 官方 linux arm64，29,977,428 bytes | SHA-256 `1bf1eb9ee63ffc4e5d324c0b9b62cf4a289f44332dfef9607cea1a0d9596ba6f` |
| 原版 Claude CLI | 官方 `@anthropic-ai/claude-code-linux-arm64@2.1.295` glibc，114,688,246 bytes | SHA-512 `2604228026426ec4e725030b063cde229c74d358e5c3e425491d3c4ac016ee9d218d447bdc37335f83693b696affe44f9bcc38f0a84cf03c49aa152600c579f9` |
| 原版 Claude 可执行文件 | 归档内 `package/claude`，255,516,664 bytes | SHA-256 `cfb9dc1332fb6f92a683f835823e91b3179a803398ca7852cd2381a3cb1dea3b` |

先核验下载摘要及归档成员，再解包；无远程安装脚本。guest 内 signed Debian apt 先模拟，确认 0 upgraded / 3 new / 0 removed，安装 bubblewrap 0.12.0-1~deb13u1、ripgrep 14.1.1-1+b4、dbus-user-session 1.16.2-2。kernel 6.12.111+deb13-cloud-arm64、systemd 257.13-1~deb13u1、cgroup2。用户 manager 只在新 guest 内启动 dbus socket，不启用 linger，不改宿主设置。

srt 0.0.79 使用独立空 npm 配置和专用 prefix/cache，ignore-scripts/no-audit/no-fund；锁文件 SHA-256 `756dcc412a9dcf95fe15c125177bc286964b314a27a1a56c626d26eed45a8db7`，依赖版本/完整性见[机器事实](2026-10-10-claude-review-guest-cli.json)。八份 guest 受信源码 SHA-256 在结束前与当前源码一致；假 CLI 的路径和源码摘要在启动公共任务前固定核验，不允许替换成原版执行任务。

## 实际结果

| 检查 | 最终结果 | 证明范围 |
|---|---|---|
| 当前 Linux 实际 OS 套 | 15 通过，13.966 秒 | 源码/Git/config 拒写、范围外读拒绝、网络/bind 限制、快速 double-fork、独立 helper、外围代理与正常/超时/取消/断线清理 |
| 当前真实 SSH 套 | 2 通过 | 定范围快照/非法 payload 与连接死亡后 cgroup 有界回收 |
| 公共入口 → Lima → guest/service/srt → 固定假 CLI | 最终 7 通过，35.697 秒；含 10 个场景 | stdin、真实快照拒写、拒权非通过、空/坏结果、定位、初始工具守门、超时及 INT/TERM/HUP；每次核对源 Git 未变、日志 0600 和凭据 sentinel 不出现 |
| 原版 CLI 在相同 OS 边界 | 5 通过，5.306 秒 | version 2.1.295、所需可见 help 参数、未登录 JSON、适配器拒绝未登录、未知参数退出 1；每次 cleanup confirmed |
| 免费总验证 | 退出 0；53 shell + 103 Python + 19 eval 自检 | 无模型、假 CLI/manager/guest 与兼容回归；不包含上述实际套 |
| 新测试最终 AST / diff | 通过 | 仅源码/语法，无安装或模型 |

原版 CLI 只执行 `--version`、`--help`、`auth status --json` 和故意未知选项；测试禁止 `-p` / continue / resume / login。新 guest 没有认证文件，前后没有创建 `~/.claude` / `~/.claude.json`，模型请求次数为 0（这里依据实际调用列表，不是推测用量或账单金额）。

## 失败、修正与剩余风险

1. 初次公共调用拒绝 guest 源码目录的 0775 权限，返回条件不足且没有启动 service；只把本批受信目录改为 0700，未放宽产品检查，复验通过。
2. 原版未登录 `auth status` 返回非零且 `loggedIn:false`。原适配器报告通用 `probe_failed`；先新增红色回归，再按有界、无重复字段 JSON 的明确 false 分类 `authentication_missing`。非零但声称已登录仍拒绝，缺乏清理证据仍不解析认证，不启动模型。10 项适配器故障测试及完整免费套通过。
3. 公共整合首轮 7 通过；第二轮有一项 SIGHUP 后独立 SSH 核验失败，当时 wrapper 已给 cancelled/cleanup confirmed。增加不泄露 stderr 的固定失败类别后，第三轮在超时夹具就绪核验捕获 SSH 255 / connection_timed_out。未证明 cgroup 清理失败；也不能把未完成的独立核验当作通过。
4. 测试观察原先每次轮询新建 SSH 握手，改成一条独立连接内 12 秒有界轮询；失败连接仍直接报错，不增加重试、不延长产品截止、不删除反向断言。夹具异常时通过已实现取消路径收尾并关闭 pipe。最终完整 7 项通过。**连接超时的精确根因和长期稳定性仍未知**，此改动不证明生产传输在所有负载下稳定，也不授权重跑未知任务或自动切后端。

结束前，本批 13 个 failed unit 仅保留失败元数据，全部非运行且对应 cgroup 为空；guest 私有 control 无 run 残留。此核验与单个任务 wrapper 报告分别记录。

## 未验证与下一步

两向真实审查均未验证：Codex 主会话→Claude Code、Claude Code 主会话→Codex。原版 `-p` 启动后的工具清单/拒权、写路径、管理 Hook/配置、真实 DNS/TLS、登录/刷新/额度/模型权限及输出格式仍需实际审查证据。原生 Mac 清理历史 5 通过/3 失败保留，产品不启用该路线；Codex 既有进程组仍不保证 detached helpers 回收。

下一步需用户提供已独立认证且满足配置的专用 guest，并分别授权有限模型批次；不读取或复制 host 凭据，不自动登录或重建本批 VM。建议先各方向一个固定合成仓库样本，记录真实宿主、实际执行者、版本/模型证据、范围、权限、结果及限制，失败即停止、不自动重跑。guest/auth 尚无条件时保持未验证，不把候选开发完成说成已交付。

## 收尾

实际 stop/delete 均退出 0，独立 LIMA_HOME 的实例列表为空；宿主无本批进程、lsof 无文件占用，随后删除本批唯一临时根和其指针。收尾状态为 confirmed，详见机器事实中的 `cleanup`。其他临时运行环境、安装插件和全局设置不动。

最终文档/阶段收束：31 份修改或新增 Markdown 的 270 个本地链接有效，当前产品摘要与机器事实匹配，两版 CR/参数/源码测试路径集合一致；所有候选 Python AST 与 git diff --check 通过。Spec Guard 产物 3 通过/0 警告/0 失败，保持 BUILDING、claude-review 唯一进行中、5 个未勾项。原生清单沿用上一轮同清单的实际通过证据，未将其当作原版模型验收。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
