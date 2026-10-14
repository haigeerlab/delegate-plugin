# Claude 审查隔离闸门：2026-10-09

计划：[claude-review](../../tasks/claude-review/plan.md)。结论：**Checkpoint 1 未通过，Task 2 部分验证，新后端不可用。** 本文件是无模型权限/生命周期证据，不是 Claude 审查或双向宿主验收。

## 环境、授权与变更

源码仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，基准 `823c42383cf055ea8af99256618daf6212d10735`。平台 macOS 15.7.3（24G419）、arm64；Python 3.10、Node 22.22.0、npm 10.9.4。Claude 2.1.295/Codex 0.160.1 沿用前一阶段核实的版本，本轮没有调用它们执行模型任务。
用户对上一轮具体临时安装请求回复“继续”，授权固定 srt 与依赖和无模型测试，不包含新 VM/容器运行时安装、登录、付费调用或交付。
安装目录 `/path/to/private-evidence`；运行时 `node_modules/.bin/srt`，实际 `--version` 为 0.0.79。依赖：socks5-server 1.0.10、commander 12.1.0、node-forge 1.4.0、zod 3.25.76。禁 npm 安装脚本，前缀/cache/两份空 npmrc 均在该目录。
首次命令因 user/global 同用 `/dev/null` 被 npm 拒绝，未安装；后续改为临时目录内独立 user.npmrc/global.npmrc 后安装成功。首次 shell 尾部 printf 返回 0 不代表 npm 成功，依据实际错误和后续依赖树区分。没有执行 npm 提示的升级命令。
仅新增候选 `review_isolation.py` 及两个守门测试，未接入命令、技能或产品总测试入口，未改旧 Codex runner。文档更新记录当前条件；源实现不是已发布后端。

## 权限与网络结果

先添加策略测试，缺 `review_isolation.py` 时退出 1；实现候选生成器后 5 项单元测试通过。策略不读取/合并用户配置，全部路径以 literal 标记；denyRead `/` 后只重开快照、本次可写区和固定 OS/Python 运行文件，写区与保护区重叠或软链接根拒绝。srt 默认额外可写路径显式 deny，网络 exact host:port，无外部代理豁免或弱隔离。
实际 OS 探针在工具外层沙箱之外运行，否则嵌套 sandbox-exec 会被外层权限拒绝。业务对象都是 `/private/tmp` 下合成源码、`.git`、home/config 和快照；合成配置没有真实凭据。共享 `/path/to/private-evidence` 只验证本次唯一子路径，必要时创建/删除空 fixture 根，不读或改其他内容。

```bash
python3 -B plugins/delegate/tests/test-claude-isolation.py --srt /path/to/private-evidence
```

最终退出 0：**13 项通过 = 5 项策略单元 + 8 项实际 OS 场景**。

| 实际场景 | 证据 |
|---|---|
| 快照可读、专用 temp 可写 | 子进程实际读取 fixture，并写出预期 marker |
| 源码、Git index、配置、快照写入拒绝 | EPERM/EACCES；所有 baseline 内容不变 |
| 可写区软链接指向源码 | 解析后的源码写入仍拒绝 |
| 删除、重命名及硬链接逃逸 | 真实 syscall 被拒，原文件在、别名不存在 |
| 范围外直接及软链接读取 | EPERM/EACCES，无内容输出 |
| srt 默认额外可写路径 | 合成 home 的 npm/debug 与本次共享 temp 子路径写入拒绝 |
| 网络未列 endpoint | 代理 403；外部于沙箱的本地 fixture server 未收到请求 |
| exact host:port 与其他端口 | 许可 server 返回 200/固定内容；另一 server 未收到请求且代理 403 |
| 直连与本地监听 | 即使 proxy 许可 endpoint，直接 connect/bind 仍 EPERM/EACCES |

网络 3 个测试中，许可/其他端口同属一个测试。所有 server 都是本次 loopback fixture，不访问外部服务。
初版两项代理场景因 localhost 解析失败而失败，不能算过滤通过。增加只读 `/etc/hosts` 未解决，已撤回该额外 grant。最终夹具显式把 **测试客户端** 的代理 URL 从 localhost 改为 127.0.0.1，并移除该客户端 NO_PROXY；不改 OS 策略，也不修改 srt/Claude。最终通过只证明代理过滤和直接 socket 边界，**不证明原版 Claude 的 DNS/TLS/认证/服务兼容性**。这些保留未验证。

## 生命周期：红色守门测试

```bash
python3 -B plugins/delegate/tests/test-review-lifecycle.py --srt /path/to/private-evidence
```

使用原有 `run_codex.py`（实际是通用进程组 runner）包围 srt。最终退出 1：**8 项中 5 通过、3 失败**。不改为 expectedFailure、不删断言、不接入产品入口掩盖缺口。

| 场景 | 实际结果 |
|---|---|
| 正常退出 | 通过，退出 0 保留 |
| 同组辅助进程忽略 TERM，超时 | 通过，wrapper 124；KILL 后无活进程 |
| 同组取消 | 通过，INT/TERM/HUP 分别 130/143/129，wrapper 原因保留 |
| 父先退出、同组子进程持有 pipe | 通过，主答复 pipe 关闭且子进程已终止 |
| 无关独立会话保护 | 通过，本次清理未杀独立 sentinel |
| 独立会话辅助进程，超时 | **失败**，wrapper 124 但 setsid 子进程仍活 |
| 独立会话辅助进程，取消 | **失败**，wrapper 143 但 setsid 子进程仍活 |
| 父先退出、独立会话辅助进程 | **失败**，wrapper 0 但子进程仍活 |

存活通过 OS ps 状态检查，僵尸不当作活进程；不是仅检查父 PID 或迟到 marker。测试 teardown 对记录的本次 helper 发送 KILL 并验证已终止，另清理记录的本次组；没有 teardown 失败或遗留夹具。测试能准确回收自己已知 PID，**不意味着产品能获取任意被调用 CLI 的全部后代 PID**。
已证实 macOS srt 文件/网络限制会被 detached helper 继承，但限制资源权限不等于限制进程寿命。不能从相同 sandbox 或 srt 退出 0 推导树已回收。

## 监督方式的只读核对与待决方向

本机 SDK `sys/event.h:356` 和 [Apple 官方头文件](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/event.h) 明示 NOTE_TRACK/NOTE_CHILD 不支持；NOTE_FORK 的实际事件不携带 child PID。仅对探针自身 PID 的内核注册核对：NOTE_FORK 接受，NOTE_TRACK 返回 errno 45 / ENOTSUP。因此不能将 Python kqueue 自动追踪 fork 当作现成替代。
按 PPID 定期 ps、进程名/环境标签或退出后扫描只能覆盖已观察到的后代；父快速退出、双重 fork/重新归属可能让观察缺失。这是机制边界的推断，不能用提高轮询频率或几条成功用例证明完整归属。未实现这些启发式监督，未声称不可能存在其他 macOS 方案。
候选更强边界是 Linux PID namespace：其 init 退出后，内核杀死命名空间进程（[Linux man-pages](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html)）。本次安装的 srt Linux 源码实际包含 `--new-session`、`--die-with-parent`、`--unshare-pid`（[官方对应源码](https://github.com/anthropics/sandbox-runtime/blob/main/src/sandbox/linux-sandbox-utils.ts)）。这是候选设计依据，**没有运行 Linux/bwrap 测试，不能宣布支持**。
本机 command 查找未发现 docker、podman、bwrap；未安装、启动或配置新容器/VM。本轮不自行扩大平台或添加后台服务。

建议重新评审的方向（尚未批准）：保持 CR-03/06，先评估具备可收束进程边界的 Linux 环境/受控 VM，确认 snapshot/日志映射、原版 CLI 和用户自行认证、网络/子进程回收，再形成最小实现计划。macOS 原生直接运行在该闸门通过前不可宣称支持。仅这一步的只读设计调研无需 VM 安装；新增依赖/运行环境、认证动作和实际验收分别另授权。两个执行后端与显式选择的范围不变。

## 旧产品回归及未验证项

本轮 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0：24 channel、19 detection、9 routing，Python 10 backend + 7 channel regressions，eval 自检 7+12，通过。xcodebuild 外层沙箱 cache/FSEvents 警告存在，未影响结果。这个旧入口目前没有调用新增 OS/生命周期守门测试；不能据此说全部测试通过。
收束时 `git diff --check` 退出 0，11 份 Markdown 的 160 个本地链接、双语条款/参数和下表三份源码哈希检查通过；旧产品已跟踪文件未修改。当前启用 Spec Guard 的产物核验 3 通过/0 警告/0 失败，阶段 BUILDING，claude-review 仍有 17 个未勾项。未改清单或运行原生清单 validator。
真实 Claude 进程权限、隔离内认证/网络/配置加载、辅助程序可信归属、快速双 fork、子进程改变身份、其他平台和双向宿主审查未验证。任何无模型结果都不验证模型发现真实性或提高准确率。未调用付费模型、委托、提交、推送、发布或真实事项。

## 可核对的文件 SHA-256

| 文件 | SHA-256 |
|---|---|
| `plugins/delegate/scripts/review_isolation.py` | `60549f2de584a539a3e8a2297372dd5d3037d2ac8c5ebe29ea8750e94017448a` |
| `plugins/delegate/tests/test-claude-isolation.py` | `e7d405cd9ae33411503fb6bf264248e35b15254381ca579f53dc72b2b3999257` |
| `plugins/delegate/tests/test-review-lifecycle.py` | `3a91abc4530d4c2decc818998b41a990c3f664e5c0c2adc2f7dccd468390ec24` |
| 临时官方包 `dist/cli.js` | `3f5544de20b8a4bf9937b1ceaa59e18ca05758f0d6a18ee76e8273585e78817a` |
| 临时官方包 `dist/sandbox/macos-sandbox-utils.js` | `0270e6c93a2be8261c85cdbbe3241434d88f19365201ca2eb1d52a0527c89885` |
| 临时官方包 `dist/sandbox/linux-sandbox-utils.js` | `cbb123ca899675ee45e9cb39746db3474a7ab8fe63d9f502000bfd0edcd7c8a4` |


## 后续阶段引用（不改变上述历史结果）

用户后续已接受 ADR-003 的专用 Linux VM 修订及免费实现测试。R1 合同同步完成，service 14 项与 guest 11 项离线测试通过，公共入口仍未接入；此前 macOS 生命周期 5 通过/3 失败保持原始结果，未重新执行。具体代码、未完成部分、固定运行环境安装预览与本轮收束证据见[VM 前置记录](2026-10-09-claude-review-vm-preflight.md)。实际 VM/Linux 清理、guest 认证、模型与双向宿主均未验证。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
