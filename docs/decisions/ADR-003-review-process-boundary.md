# ADR-003：审查进程边界修订

简体中文 | [English](../en/decisions/ADR-003-review-process-boundary.md)

2026-10-10：用户收敛为当前 Mac 本机后，当前执行环境改由 [ADR-004](ADR-004-native-mac-review.md) 定义。以下保留旧设计、批准与无模型证据；不再作为当前部署前置。

状态：Accepted（设计及免费实现测试；实际运行未验收）。日期：2026-10-09。
用户先对只读评估请求回复“继续”，后又对本提案推荐的专用 VM 路线回复“继续”，据此替代 ADR-002 的 macOS 原生首验部分，批准 R1–R4 中无需安装的实现与测试。安装新运行时、guest 登录、模型调用及交付仍需分别授权；设计批准不关闭隔离 gate。

## 问题与证据

现有 macOS 候选的权限/策略套 13 项通过；生命周期套 8 项中 5 通过、3 失败。独立会话 helper 在超时、取消和父先退时存活，不能满足 CR-06。测试收尾终止了自己的 helper，没有以 expectedFailure 隐藏失败。详见[实际记录](../verification/2026-10-09-claude-review.md)。
本次没有重跑这些测试，也没有修改候选实现。只读 PATH 清单：macOS 15.7.3 arm64 有 `/usr/bin/ssh`，未找到 limactl/docker/podman/bwrap/socat/qemu-system-aarch64；不代表磁盘上绝无其他安装。本机没有已核实可用的 Linux 执行环境。

## 官方接口核对

| 机制 | 可核实的作用 | 仍需证明的条件 |
| --- | --- | --- |
| Linux PID namespace | namespace PID 1 死亡时内核 SIGKILL 其中的全部进程 | 必须确实创建 namespace，并可靠终止其 PID 1；不能只杀外层客户端 |
| bubblewrap | `--unshare-pid` 创建边界，`--die-with-parent` 绑定父进程死亡，`--new-session` 隔离终端 | 默认 init 可等其他子进程；不能把主任务退出等同于 namespace 已空 |
| srt 0.0.79 Linux 源码 | 实际使用上述三个参数、user namespace 和严格模式 fresh `/proc`；Node 代理和 host socat 在 bwrap 之外 | 外围代理也必须纳入本次生命周期；seccomp helper 缺失时的警告不能被当作足够隔离 |
| cgroup v2 | fork 继承归属；`cgroup.kill` 对整个子树 SIGKILL，处理并发 fork；`cgroup.events` 提供 populated 状态 | 不向审查者暴露迁移/控制接口；无可用管理权限时拒绝启动 |
| systemd transient service | `KillMode=control-group` 停止整个 unit，超出 `TimeoutStopSec` 后升级 SIGKILL；`RuntimeMaxSec` 限制运行时间 | 必须用 service，不能用仅管理客户端寿命的 scope；需实际测试 user manager、状态保存和清理 |
| Lima plain mode | 关闭 host mounts、动态转发、SSH agent forwarding、containerd 和 guest agent | 静态转发、初始化脚本和基础 SSH 设置仍存在；需逐项核对最终配置，VM 本身不限制 guest 网络 |

依据：[Linux PID namespaces](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html)、[bubblewrap 参数](https://github.com/containers/bubblewrap/blob/main/bwrap.xml)、[cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)、[systemd kill](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.kill.xml)、[systemd service](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.service.xml)、[systemd-run](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd-run.xml)、[Lima plain mode](https://lima-vm.io/docs/config/plain/)。
srt 依据为临时安装的 **0.0.79** `dist/sandbox/linux-sandbox-utils.js`：2625、2766–2784 的边界参数；1072–1125 的外围桥接进程；2633–2640 的 seccomp 缺失路径。哈希已记在实际记录。官方 [main 源码](https://github.com/anthropics/sandbox-runtime/blob/main/src/sandbox/linux-sandbox-utils.ts)和 [README](https://github.com/anthropics/sandbox-runtime)仅用于交叉核对，不代表已发布版本或本机验证。严格模式不允许 `enableWeakerNestedSandbox`，不自动修改 user namespace 的系统策略。

## 方案比较与推荐

| 方案 | 优点 | 范围与代价 |
| --- | --- | --- |
| macOS 原生 srt + 现有 runner | 沿用本机原版 CLI/认证，依赖最少 | 已证实不能完整清理 detached helper；本提案不将其启用，也不宣称所有原生替代都不可行 |
| Linux 原生 CLI + srt + transient service | 无 VM 传输层，能够把外围进程纳入 cgroup | 需可用 Linux/systemd/cgroup v2；单独交付这一项不能满足当前 Mac 的双向验收 |
| macOS 专用 Linux VM + 同一执行单元 | 保留 Mac 主会话，guest 使用内核进程边界；可支持原需求的 Mac 双向验证 | 新增 VM、SSH 传输、guest 认证和资源开销，实际可用性未知，需要明确批准 |

推荐第三项作为 **Mac 验证环境和可选部署方式的下一候选**，先在 guest 验证第二项的执行单元。不引入第三执行后端：后端仍只有 codex/claude-code，VM 是 Claude 的执行环境。Codex 既有路径保持本机原行为，不自动切到 guest，也不自动选择另一后端。
若选择仅 Linux 原生，需要明确接受 Mac Claude 后端暂不支持、CR-10 在本机未完成；不能将它记为原需求完成。若继续原生 Mac，需另找并证明满足 CR-06 的边界，当前无已验证方案。

## 候选运行合同

1. 目标源码和 Git 只由 host wrapper 在明确范围内读取。普通文件快照与固定 diff 经校验后传入 guest 的专用目录，重新校验哈希。源仓库、host home、Git、钥匙串、SSH agent、Docker socket 均不共享。传输器拒绝符号链接、硬链接、绝对路径和 `..`，不执行任务内容；返回只接受有限大小的 answer/report/过滤事件。
2. 单次审查使用唯一 transient **service**，由可用的 user manager 启动可信 runner，srt/Node/proxy/socat/Claude 都在该 unit 的 cgroup。采用 `Type=exec`、`KillMode=control-group`、`SendSIGKILL=yes`、`TimeoutStopSec=2s`、有限 `RuntimeMaxSec`，不启用 restart、delegate 或 remain-after-exit。cgroup 控制路径、用户 D-Bus/SSH sockets 不向审查者开放。缺少管理能力或 namespace/seccomp 实际能力时条件不足，不修改全局 sysctl/AppArmor/linger。
3. runner 在无模型预检后启动原版 `claude -p`，工具/上下文/文件/网络权限仍按 ADR-002；仅允许实际认证方式所需的明确服务端点。guest 的整个网络不是 Claude 的工具能力。项目、配置、只读快照不能写，只开放本次 run/log/temp；内置工具仍仅 Read/Glob/Grep。
4. 正常、失败、超时和取消都执行 unit 收束，确认本次 cgroup `populated=0` 后才声明清理完成。先保存本次 unit 的 Result/ExecMainStatus 与 runner 原因，不能只解释 systemd-run 退出码；不能过早自动收集 unit 而丢失诊断。不读取 journal 原文，不保存 argv/env 中凭据。
5. host 取消通过独立控制请求停止**本次** unit；guest 有自身期限，SSH 断线不能解除它。不得将 SSH 客户端退出解读为 guest 完成。控制失败时结果为未知/失败且 inconclusive，不重新执行。专用 VM 必须独占且有归属记录；仅在确认没有其他任务时才允许停止该 VM 作为收束措施，绝不停止用户共享 VM。
6. host 的 SSH 等辅助进程仍由本次进程组清理；guest unit 和 host 两层都要检查。异常 host 消失后的 guest 最大存活期限明确记录；不可捕获终止不承诺立即清理。无法核实清理时报告该限制，不能返回审查通过。
7. 不创建通用远程执行协议、队列或后台调度器。若选择 VM 方式，只接一个显式提供、受控且专用的本机 Lima guest，固定启动/状态/取消操作，不接受任意远端或 shell 字符串。VM 缺失时不自动创建、启动或切换运行环境。

候选基线：原版 Claude **2.1.295**、srt **0.0.79**、Node **>=22.12.0**。Linux/kernel/systemd/bwrap/socat/Lima 的确切版本、镜像及摘要在下一次依赖预检中固定；当前没有可宣称验收的版本矩阵，不据官方最低平台要求猜测实际支持。参考 [Claude 平台要求](https://code.claude.com/docs/en/setup)。内核必须实际有 cgroup v2/cgroup.kill，manager 必须接受所用属性；这些能力测试优先于版本字符串。

## 认证与项目上下文

原版 guest CLI 自行使用用户在 guest 预先配置的登录或明确选择的 API/provider 认证，delegate 不读取、复制、代理或跨 SSH 传输 host 凭据。缺少 guest 认证不根据 host 登录推断可用，不自动运行 login/setup-token。首次模型验证另授权。
Linux 登录存于 `.credentials.json`，`CLAUDE_CONFIG_DIR` 会改变认证目录；因此不能随意换成空目录并称“保持登录”。预检与执行使用同一显式 guest 认证配置，只允许 CLI 读取确切需要的认证路径，普通项目/用户定制仍关闭；若刷新需写原配置，拒绝并报未完成，不复制到临时目录绕过边界。环境认证由用户在 guest 提供，wrapper 日志不保存值。API key、订阅、云 provider 的计费/政策不同，不能静默选择或替换。
依据：[官方认证](https://code.claude.com/docs/en/authentication)。能否在严格只读认证配置下正常请求仍未知；官方支持 Linux 不证明这个隔离组合可用。管理员 Hook 或 helper 不兼容时报告条件不足，不放宽权限、不使用 bare/bypass。工具权限解决动作集合；srt 解决文件与出站边界；safe/restricted 和固定快照解决上下文加载；service/cgroup 解决寿命与归属，互不替代。

## 结果合同增量

保留既有八种执行/审查状态和证据字段。只增加 `execution_environment`（native/指定 VM、OS、核实版本）与 `cleanup`（confirmed/unverified、必要原因）；主会话 `host`、实际后端、requested/observed model 仍分别记录，无法核实为未知。VM 名称、PID/cgroup 标识只进受限诊断，不常规披露个人路径。初始化失败时注明 Claude 尚未启动。结构化有效、unit 成功或退出 0 均不证明审查无问题。

## 修订实施与验证顺序

| 切片 | 文件范围/规模 | 验收与下一停点 |
| --- | --- | --- |
| R1 同步平台合同 | 中英 spec、ADR-002 两版、本 plan（5 文件，S） | 仅在修订获批后同步；保留原批准与红色历史 |
| R2 Linux 无模型单元 | 新 `review_service.py`、生命周期 Linux 测试、既有策略/权限测试（最多 4 文件，M） | 假 manager 故障分支与真实 guest suite 分开；已批准才修改候选代码 |
| R3 专用 VM 预检与传输 | 新 `review_guest.py`、夹具传输测试、权限测试（最多 3 文件，M） | 无 host 目录共享、归属/互斥、哈希、限大小、非法路径、断线/取消分类全部通过；不访问真实凭据 |
| R4 实际隔离 gate | 实际记录、todo（2 文件，S） | 固定版本后，以假 CLI 跑实际权限+生命周期；全部通过并报告限制后才进入 Task 3 |

R2 重点：setsid、double-fork、忽略 TERM、父先退、持管道、代理派生、快速 fork/exit、外层 runner 消失、INT/TERM/HUP、期限及 unrelated sentinel；检查 unit/cgroup 为空和 sockets/代理收束。R3 重点：断线但 guest 期限有效、停止请求丢回复不重跑、两任务不互相误杀、只读认证夹具拒写、无 delegate/MCP/任意 Bash 能力。不会把 Mac 的原红测试改绿或跳过来冒充原生修复。
下一具体安装请求须先列出 runtime/镜像版本与摘要、下载来源、专用临时路径、磁盘/内存/CPU 范围、初始化内容和删除方式；本提案批准不包含安装。真实认证/Claude 请求、两宿主验收和 Git/远端交付继续分别授权。原 Checkpoint 1 未通过，Task 3 尚未开始。

当前 R1 已同步，R2/R3 的候选基础实现分别通过 14/11 项免费测试；尚未实现 VM/SSH 调用及实际 unit 启动，没有 Linux 内核或 guest 验收。实际 manager 过早回收 unit 时当前实现失败关闭，不推断成功；权威结束事实保留须在真实 manager 运行片验证。候选使用的 `--expand-environment=no` 需要 systemd >=254，仍须验证实际解析/属性。具体依赖预览见[记录](../verification/2026-10-09-claude-review-vm-preflight.md)。

后续实际实施：用户“继续 快速推进啊”批准固定临时 VM 安装及无模型验证；Lima/Debian/Node/srt 摘要与实际版本已核实，Linux 15 项、实际 SSH 2 项通过，原生 Mac 失败保留。已增加实际 service 启动、可信 ExecStopPost 结束事实保留、Linux `/sys`/`/run` 掩蔽和 arm64 bind/listen seccomp 禁止；此前“没有实际 unit/VM”的段落是当时状态。公共入口与产品化 VM/SSH 控制仍未接入，原版 CLI/认证/live 均未知，gate 待评审。见[当前实际记录](../verification/2026-10-09-claude-review-linux.md)。
