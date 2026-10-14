# Claude 审查候选调用链：本轮集成与验证

日期：2026-10-10。仓库：`delegate-plugin`；分支 `codex/spec-guard-conventions-public`；基准 HEAD `823c42383cf055ea8af99256618daf6212d10735`。本记录只对应本轮未提交的源码候选，不证明发行/安装副本、真实 guest CLI 或双向宿主审查通过。English readers: Chinese administrative evidence; the bilingual behavior contract is [here](../en/SPEC-claude-review.md).

## 成果和阶段

5 阶段：源码/官方调研完成，设计/计划已批准，固定 Linux/SSH 安全基础已实测，**第 4 阶段候选功能开发与免费回归完成**；第 5 阶段当前整合版实际 guest、原版 CLI 与真实双向审查未完成。Task 2/6 的完整实际条件及 Task 8 保持未勾选，模块不标 DONE。

公共 `delegate-exec.sh` / `delegate_backend.py` 默认调用现有 Codex 包装器，显式 `--backend claude-code` 只连接显式配置的已运行专用 guest，不启动本机 Claude 或换回 Codex。保留 Codex 的默认 read/write 与原认证；backend/model/effort/turn/budget 不能混用，递归标记在新旧入口均拒绝。

共同 JSON 明确仓库、cwd、diff/module/paths、基线、未提交改动、spec/plan 上下文文件、验收、排除、允许工具和停止条件。只读 Git 禁用 external diff/textconv/fsmonitor/hooks，固化普通文件和 SHA-256，没有真实 .git、链接或自动扩大范围；采集竞争变化停止。Codex 可选共同模式和 Claude 获得同一范围快照/提示数据。

Claude 独立 guest 预检版本/能力/安全认证字段，固定 `-p` / stream-json / schema / dontAsk / Read/Glob/Grep / 空 MCP / 无会话持久化 / 禁 Hook、派活和自动模型切换。`--allowedTools`、Plan 或提示词不承担 OS 隔离。已有 Linux srt+arm64 seccomp+单次 service/cgroup 负责整个 CLI/外围 helper；源项目不共享到 VM。guest 源码摘要在导入前核对，运行配置摘要固定；插件不安装或启动 VM，不复制 host 凭据。

结果分别保存执行状态和审查结论；覆盖缺口/拒权/空或坏输出/耗尽/模型切换均不能报无问题；行号必须落在快照，未核实宿主/模型标 unknown。结构化格式不证明发现真实，不授予合并/交付。最终结果与精简过程日志分开，0700/0600、最近 50 组；不留原始 CLI 流、凭据或 stderr，实际用量缺失不写零。

## 实际免费验证

`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 最终退出 0，实际包含：

| 套件 | 通过数 | 证据性质 |
| --- | ---: | --- |
| channel / detection / routing shell | 24 / 19 / 10（53） | 原行为/静态入口及临时 CLI 桩 |
| backend / channel-regressions | 10 / 7 | 原 Codex 认证/进程组回归夹具 |
| review-backends / claude-review | 7 / 9 | 后端分派、CLI 参数和认证故障注入 |
| review-context / review-result | 8 / 9 | 临时 Git 真实文件采集；合成结果分类 |
| review-execution | 5 | 默认/共同 Codex、公共 Claude、错误和用户中断；全部假 CLI/guest |
| review-transport / review-guest-entry | 7 / 5 | 配置、来源摘要、传输协议及 guest 控制模拟 |
| review-artifacts / review-service / review-guest | 3 / 16 / 11 | 临时文件、假 manager/cgroup、进程与快照夹具 |
| claude-isolation --policy-only | 5 | 策略结构；没有实际内核沙箱 |
| Python 小计 | 102 | 本轮免费套，不包含实际 OS/SSH/live |
| eval 自检 | 7 / 12（19） | 判决器自身测试，不是跨后端验收 |

两项 `claude plugin validate .` / `claude plugin validate ./plugins/delegate` 均退出 0。Bash 3.2 语法/危险模式、JSON 和所有 Python AST 在免费入口中核验。文档/双语与 Spec Guard 最终结构检查见下方收束补记。

完整免费套之后最后收紧预检 OSError 的清理报告（未知保持 unverified），并给临时假 CLI 加 `-B`，避免专属传输环境清空环境变量后生成源码 bytecode。适配器/guest 控制/传输/公共调用链定向 9 + 5 + 7 + 5（26）项全部通过。产品数不变；未因夹具问题放宽产品截止或权限。源码 AST 在最终收束再次核验。

过程中的实际失败与处理：

- 新适配器测试先证明缺函数/不支持 stdin 等，逐片接入后转绿；不调用真实账号或模型。
- 假 CLI 用 `/usr/bin/env python3` 在本机触发慢启动导致 5 秒预检失败。测试夹具改为本次已运行的 `sys.executable`，保留产品 5 秒截止，不靠延长超时过关。
- 默认工具沙箱拒绝 ps，service 的 helper 存活断言出现环境错误。最终总套经工具批准在沙箱外执行，仅检查本次临时夹具；不将它称为实际 systemd/cgroup 通过。
- 取消发生在 init 之前时，工具清单错误覆盖 cancelled；新增测试先实际失败，再修复保持取消/超时并保留诊断。额外反转该判断，测试再次失败；finally 逐字恢复源码。
- runtime schema 将 `true` 当整数 1，新增反向断言先红后绿；测试使用独立配置副本，避免首次规范化掩盖错误。
- guest 返回不明预检错误时漏独立取消；新增测试先红，修复后只取消本次 UUID，未知仍标 unverified。
- runtime probe 被取消时继续下个探针并误报条件不足；新控制模拟先红后绿，取消后不启动下一探针或模型。

本批次有限代码复核覆盖新增公共参数/上下文/结果/传输/guest/service/日志及受影响旧入口，不重新泛扫项目。上述必须修正项已修复；真实内核和原版 CLI 未覆盖项在下节保留，不给合并授权。

## 当前未验证与已知限制

[2026-10-09 Linux/SSH 记录](2026-10-09-claude-review-linux.md)的 15 + 2 项只证明其固定源码摘要。本轮 service 的 stdin/init 守门、guest 整合、传输/独立取消组合及 `test-review-linux.py` 导入已有变化，旧报告摘要不重写，不借旧证据验证当前完整链路。原生 Mac 生命周期 5 通过/3 失败未删除、未降断言；原生 Mac 路线不启用。

原版 Linux Claude CLI 未安装；真实 startup/临时写路径、DNS/TLS/认证刷新、管理 Hook/配置、工具清单/拒权与两向真实模型尚未验证。当前认证只保守接 first-party 的已知方法，不接受外部 provider/api_key_helper 或不明字段；不扩大网络来掩盖兼容问题。

Codex 共同模式保留原进程组机制，报告明确 detached descendants 未证明不存在；Claude 的 Linux cgroup 证明不能挪给 Codex。Codex 无实际模型事件时保持 unknown。主宿主没有可靠标识时两者均 unknown，真实宿主验收还需外部宿主启动证据。

只支持有 HEAD 的 Git 工作树及有限普通 UTF-8 文件；二进制、链接、删除目标或读取失败列未审。当前定位仅目标快照行，删除旧侧行不虚构。guest 只候选支持 Linux arm64 + Lima/VZ 2.2.1 专用环境；资源/其他平台/真实原版 CLI 不能由安装或桩测试推断。输出监测为有界阈值并允许监测间隔超量，不是瞬时磁盘硬配额；CLI预算为实际返回的估算口径，不是账单保证。

## 下一批具体预览：原版 guest CLI，无模型

本节是可审阅的请求，不是已执行或已批准。旧 VM 根已删除，下一批必须重新创建，且新增原版 CLI 安装对象，不能从本轮“继续”继承。模型/guest 登录及插件安装、全局设置、Git交付均不包含。

复用[固定环境预览](2026-10-09-claude-review-vm-preflight.md)的 Lima 2.2.1 Darwin arm64、Debian 13 arm64 固定镜像、Node 22.22.0、srt 0.0.79 与摘要；不使用 latest、不升级。一个新 `/path/to/private-evidence`，0700；仅本次 LIMA_HOME、无 host mounts/端口转发/SSH agent/用户 key/Rosetta/containerd。2 vCPU、4 GiB guest 内存、16 GiB 虚拟盘；下载总预算 1.5 GiB、专用目录实际占用 20 GiB，超额即停。guest Debian签名工具安装先模拟并记录固定版本，事务不匹配停，不切版本。

新增 CLI 使用原版官方 `@anthropic-ai/claude-code-linux-arm64@2.1.295`（glibc）。2026-10-10 仅读取官方注册表，未下载或安装包：

- [固定发布元数据](https://registry.npmjs.org/@anthropic-ai%2fclaude-code-linux-arm64/2.1.295)
- tarball：`https://registry.npmjs.org/@anthropic-ai/claude-code-linux-arm64/-/claude-code-linux-arm64-2.1.295.tgz`
- integrity：`sha512-JgQigCZCbsTnJQMLBjzeIpx001jlw+QlSR08SsAW7p0hjUR73DczX4NpO2lq/+RPm8w48KhM8DxJqhUmAMV5+Q==`
- 注册表 unpackedSize：`255517258` 字节；不是实际下载大小或安装证明。

先在专用下载目录取得指定包并核验 SHA-512，再检查归档成员无绝对路径/穿越/链接，解包到本次 guest 工具目录，核对原版 `--version` 必须 2.1.295；路径不符或不支持所需 flag 即停。无需运行上层 npm 安装/自动更新，不运行远程安装脚本。八份 guest 源文件只在此专用 VM 显式准备，摘要必须等于本批次待测源。

无模型步骤：重新运行当前源码的 Linux 15 与 SSH 2 实际拒写/范围外读取/网络/setsid/helper/断线回收套；再通过公共入口和真实 Lima/guest/systemd/srt 运行临时假 Claude CLI，验证真实传输、stdin、初始工具守门、超时、取消、错误和 cgroup 清理；最后仅调用原版 CLI 的 version/help/auth status 与故意非法参数的解析探针，使用全新未认证 guest，不读/复制 host 密钥，不传任务去真实 `-p`，不登录或调用模型。原版模型启动后的 tool/写路径/认证兼容仍需后续真正的模型批次，不能由这些探针算通过。

此批次成功也只关闭当前整合无模型条件，不关闭 CR-10。任何摘要、权限、资源、CLI/manager能力、清理未知或越界即停止；不更换后端，不无限重试。收尾 stop/delete 本次唯一 VM、核对进程/占用后删除其专用根，保留脱敏证据；清理失败保留运行对象信息，不删除运行磁盘。之后才另提有 guest 独立认证前提、固定样本/次数/预算的双向真实审查请求。

## 当前候选源码摘要

以下为本轮完整免费套与随后定向复验组合对应的候选文件；不取代旧实际 OS 报告的摘要。

| 文件 | SHA-256 |
| --- | --- |
| `plugins/delegate/scripts/claude_review.py` | `85bea00c74dde195784dccdd29ed359c9530e78ef113c1c13f27b13f158a3ab7` |
| `plugins/delegate/scripts/codex-exec.sh` | `98f06790366f169f3639fe249a3634a3892ebf22b43374aff504dede12b6aad8` |
| `plugins/delegate/scripts/delegate-exec.sh` | `6f671a25982169f40e3993af1261ecfc9915d7f659731c67b2c10735b7b07059` |
| `plugins/delegate/scripts/delegate_backend.py` | `7c621a0d4f655669d96df0852a4591531a48db5014fe8eeec966c50bdd780ecb` |
| `plugins/delegate/scripts/review_context.py` | `bfcb452c60d01e116cad9156c487ed87e2ccd76fba37c58b65745952681efc87` |
| `plugins/delegate/scripts/review_doctor.py` | `748a06e06bf6dbd1c6c0e1af3943bd41b5515a6dba313d7dc37d919abfca0439` |
| `plugins/delegate/scripts/review_execution.py` | `9fe9dc5a104f531474c42026d599bf803ef4e98ea9feb414de08ac0ef76cf98c` |
| `plugins/delegate/scripts/review_guest.py` | `9014b34c9c027a6b3706e413c2b9d767b7969e8de7f2fcad6920defa7a785aa1` |
| `plugins/delegate/scripts/review_guest_entry.py` | `613f2353ae921527c8bdcadedfb756b0459b9af495775869f9f834a38b2d2da3` |
| `plugins/delegate/scripts/review_isolation.py` | `16cee5ab304b40c85299a7e8e7340d8fdfe8902d6472bcad1968ea7336c923b1` |
| `plugins/delegate/scripts/review_network.py` | `b835bc9aa4ba1019895a1eefe667ae7d74a57b6da51c9e1ce10a8477c4ed5d44` |
| `plugins/delegate/scripts/review_result.py` | `7555af3210ac011215c032985e7c48aa44aed950626b660c3aa6ca167e79b77a` |
| `plugins/delegate/scripts/review_service.py` | `8c76145c624bf6890f3ebcf115ff68b3eeb7da6b11b264d9c28549a951b6f602` |
| `plugins/delegate/scripts/review_transport.py` | `33371942d3b699b998d432d202e2800833779f4738f84277c85e549d377318a8` |


## 收束补记

30 份本轮 Markdown 的 260 个本地文件链接存在；两版 CR 编号、参数集合、三块 JSON 结构及机器字段相同，验收文字和摘要解释各按中英文表达。最初逐字比对因这两处合法翻译失败，改为显式核对翻译且逐字段比较机器数据，不改变合同。源目录的夹具 bytecode 已清除，假 CLI 加 -B 后定向回归验证不再生成。

`git diff --check` 退出 0，最终候选 Python AST 通过。动态解析已启用 Spec Guard 本地来源，`verify-artifacts.sh` 3 通过/0 警告/0 失败；`phase-guard.sh` 保持 BUILDING，4 模块/规格/计划，只有 claude-review 进行中。此为结构检查，不等价验收或发布。全局设置、安装副本、模型与远端对象本轮未改。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
