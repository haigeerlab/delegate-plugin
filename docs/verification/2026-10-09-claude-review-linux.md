# Claude 审查：专用 Linux VM 的实际无模型验证

日期：2026-10-09。工作区 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，基准 `823c42383cf055ea8af99256618daf6212d10735`。
English readers: this is an administrative evidence record; see the [English contract](../en/SPEC-claude-review.md).

## 批准与当前产品进度

用户在阅读[固定安装预览](2026-10-09-claude-review-vm-preflight.md)和进度解释后回复“继续 快速推进啊”，据此执行该唯一临时 VM 的安装、无模型测试与收尾。未安装 delegate 或 Claude/Codex CLI，未登录、读取/复制主机凭据、调用模型、委托、提交、推送或发布。

五阶段进度：调研完成；设计/计划完成；第三阶段安全基础的 Linux/SSH 实测完成本批次；第四阶段公共后端接入尚未开始；第五阶段真实双向审查尚未开始。候选代码存在，**新增 Claude 后端仍不可用**。Checkpoint 1 等待本次结果和限制评审，不能从测试通过推导产品完成或交付授权。产品化 VM/SSH 控制接口、CLI 预检、原版 CLI 配置/认证兼容仍待后续实现/验收。

## 实际环境与初始化

本机 arm64，16 GiB RAM、8 逻辑 CPU；可用磁盘约 258 GiB。默认工具沙箱 sysctl 被拒后，沙箱外只读核实资源。唯一 `/path/to/private-evidence` 为 0700，Lima/下载/SSH/host HOME/TMPDIR 均在其中；命令使用 env -i，无用户全局环境和配置继承。

| 项目 | 实际结果 |
| --- | --- |
| Lima | 2.2.1，官方 Darwin arm64 包，38,328,082 字节，SHA-256 与预览匹配 |
| Debian 镜像 | 固定 20261001-2618 arm64，337,510,400 字节，SHA-512 与预览匹配 |
| VM | VZ，2 vCPU、4 GiB RAM、16 GiB 虚拟盘，plain，无 host 挂载/static forwarding/provision；agent/X11/user SSH 公钥转发关闭，containerd/Rosetta 关闭 |
| kernel / systemd | `6.12.111+deb13-cloud-arm64`；257.13-1~deb13u1；cgroup2fs；user manager running |
| Node / npm / srt | 22.22.0 / 10.9.4 / 0.0.79，Node 下载摘要匹配，npm srt integrity 匹配官方固定值 |
| guest OS 依赖 | apt 先模拟后固定安装 bubblewrap 0.12.0-1~deb13u1、ripgrep 14.1.1-1+b4、dbus-user-session 1.16.2-2；0 升级、3 新增；已有 socat 1.8.0.3-1+deb13u1、python3 3.13.5-1、ca-certificates 20250419 |

Lima validate 通过；启动时顶层 rosetta deprecated 警告，实际 effective config 仍 false。只用已校验本地镜像，VZ 原生转换，未安装 QEMU 或写全局缓存。guest 包索引实际读取 Debian 签名仓库，无 host 修改。新安装 dbus-user-session 后，已有 user manager 的 bus socket 尚未启动：首次 systemd-run 报无法连接；仅在专用 guest daemon-reload/start dbus.socket 并显式 XDG_RUNTIME_DIR/DBUS_SESSION_BUS_ADDRESS 后恢复，不修改 linger 或主机设置。

npm 安装使用独立空 user/global npmrc、专用 prefix/cache、ignore-scripts/no-audit/no-fund，未执行 npm 的升级提示。实际依赖：sandbox-runtime 0.0.79、socks5-server 1.0.10、commander 12.1.0、node-forge 1.4.0、zod 3.25.76；package-lock SHA-256 `756dcc412a9dcf95fe15c125177bc286964b314a27a1a56c626d26eed45a8db7`。

## 代码与失败修复

`review_service.py` 增加实际单次服务启动、环境清空、INT/TERM/HUP 处理、有限输出、独立停止及结果分类。systemd-run 固定 Type=exec、RuntimeMaxSec、KillMode=control-group、SendSIGKILL、TimeoutStopSec、禁止变量展开/restart/delegate/remain-after-exit。可信 ExecStopPost 在隔离外的私有 control 根保存 unit/cgroup/结束原因；CLI 返回后 unit 已回收时依据这份事实和内核 cgroup 空状态核实，不把缺元数据猜作成功。reviewer 实测不能读写 control 根。

首个 Linux 测试在没有 run 方法时退出 1。实际全套最初 7 通过/2 失败：srt 的根 denyRead 特意保留 `/sys`，Linux allowLocalBinding=false 也不禁止私有网络命名空间内 bind。没有删除断言；`build_linux_policy` 显式掩蔽 `/sys` 和 `/run`，新增只支持已验证 arm64 的 `review_network.py`，在 srt 内叠加不可移除的 no_new_privs/seccomp bind/listen 禁止。过滤器启动失败停止，不回退。固定过滤器需显式只读路径；首次漏配时全部相关启动失败，补固定文件后通过，不扩大目录授权。

过滤器依据 [Linux seccomp](https://docs.kernel.org/userspace-api/seccomp_filter.html) 和 [v6.12 syscall UAPI](https://raw.githubusercontent.com/torvalds/linux/v6.12/include/uapi/asm-generic/unistd.h)；先检查 ABI，再匹配 bind/listen。它只增加两个 syscall 禁止，不替代 srt 网络命名空间、端点代理和 Unix socket 过滤。其他架构未支持。

代理测试先因空域列表没有代理，以及 loopback NO_PROXY 绕过代理而失败。夹具改为两台真实回环 HTTP server，固定允许其中一个精确端口；仅夹具删除 NO_PROXY 并将代理 localhost 改数字地址。最终证明另一个端口 403/零命中、允许端口 200/一次命中；**不证明原版 Claude 的 DNS/TLS/认证兼容**。

## 已执行结果

| 验证 | 命令与结果 |
| --- | --- |
| 实际 Linux | guest `python3 -B /tmp/delegate-tests/tests/test-review-linux.py --srt /tmp/delegate-tools/srt/node_modules/.bin/srt`，退出 0，**15 项通过** |
| 实际 SSH | host `python3 -B plugins/delegate/tests/test-review-ssh.py --root /path/to/private-evidence`，退出 0，**2 项通过** |
| 假 manager/控制面夹具 | `python3 -B plugins/delegate/tests/test-review-service.py`，沙箱外仅本次临时夹具，退出 0，14 项通过 |
| 快照/lease 基础 | `python3 -B plugins/delegate/tests/test-review-guest.py`，退出 0，11 项通过 |
| 既有策略基础 | `python3 -B plugins/delegate/tests/test-claude-isolation.py --policy-only`，退出 0，5 项通过 |

15 项 Linux 实测覆盖：正常与非零、源码/Git/配置/快照/control/链接拒写、纳入范围读取和专用 temp 写入、范围外/管理路径不可读、删除/重命名/hardlink 拒绝、默认额外写目录拒绝、直接网络/bind/Unix socket 拒绝、精确代理端点、输出上限、超时、INT/TERM/HUP 取消、父先退、八个快速 double-fork、客户端死亡期限、无关 sentinel 存活。不是只检查父 PID；先证明 helper 确实启动，再核对整个已观察 unit 的 cgroup populated=0 或该路径已消失，包含外围 Node/proxy/socat。

2 项 SSH 实测覆盖：独立 SSH 客户端被 SIGKILL 后，另一独立通道确认 guest cgroup 限期收束；最终结果丢失仍标未知，不推导完成。普通文件快照通过实际 SSH 后路径/哈希一致、排除项未传输；路径穿越请求被 guest 在写入前拒绝，目标保持空。传输代码是测试夹具，不冒充已接入产品的 VM 控制 API。

此前 macOS 5 通过/3 失败保持历史证据；未重跑、改绿、跳过或 expectedFailure。旧免费总入口尚未纳入候选 suite，沿用此前真实通过记录，不称“所有测试都通过”。真实 Claude tool/Hook/MCP/上下文、原版 CLI 在此策略内的启动与认证、额度/模型/结果质量、双向宿主审查、其他平台均未验证。没有付费/live。

## 对应源码 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `plugins/delegate/scripts/review_isolation.py` | `16cee5ab304b40c85299a7e8e7340d8fdfe8902d6472bcad1968ea7336c923b1` |
| `plugins/delegate/scripts/review_service.py` | `fd435e04a0513ada73cccccd34396ac1eac6b02e7b95fe7bfcff90bf1026b26d` |
| `plugins/delegate/scripts/review_guest.py` | `9014b34c9c027a6b3706e413c2b9d767b7969e8de7f2fcad6920defa7a785aa1` |
| `plugins/delegate/scripts/review_network.py` | `b835bc9aa4ba1019895a1eefe667ae7d74a57b6da51c9e1ce10a8477c4ed5d44` |
| `plugins/delegate/tests/test-review-linux.py` | `ace401d85bc479621822db87b5ca525f99764ad7a74531fcff134254d3db58f5` |
| `plugins/delegate/tests/test-review-ssh.py` | `8363341dfc5a0404e142d4e696f0783712679c3050ea42f8b553d276d52eb7d2` |

## 收尾

`limactl stop --yes delegate-review` 与 `delete --yes delegate-review` 均退出 0；VZ/hostagent 已停止，记录的 PID 19961 的 ps 结果为空（退出 1）。仅本次目录的 lsof -t +D 无持有进程（退出 1）。确认 instance 目录已删除后，移除唯一专用临时根，存在检查为 false。未删除其他 Lima_HOME 或前次 macOS srt 目录。下载、工具、临时 SSH 私钥及 VM 磁盘已随本次根删除，仓库保留脱敏事实/摘要/命令。

本批次收束：`git diff --check` 退出 0，6 个候选 Python AST 通过，15 份文档的 185 个本地文件链接有效，双语 CR/选项和当前源码摘要一致。动态解析已启用 Spec Guard 的产物检查 3 通过/0 警告/0 失败，阶段 BUILDING，4 模块/规格/计划、17 个未勾项。临时 VM 根不存在。核验是文档/候选阶段检查，不是产品接入或真实双向审查完成。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
