# 专用临时 VM 验证预览

日期：2026-10-09。阶段：R2/R3 的真实环境前置，**尚未安装或启动**。
English readers: this is a Chinese administrative evidence/authorization preview; the behavior contract is in [ADR-003](../en/decisions/ADR-003-review-process-boundary.md).

## 已完成与缺口

用户对 ADR-003 的专用 VM 推荐回复“继续”，批准设计、合同同步及免费实现测试，不含安装、guest 登录、模型或 Git/外部交付。
R1 双语合同已同步。候选 service 与 guest 基础实现和测试位于 `plugins/delegate/`，尚未接产品入口：

- `python3 -B plugins/delegate/tests/test-review-service.py`：最终 14 项通过；假 manager、模拟 cgroup 文件，临时真实 manager helper 的 PID/无关 sentinel 检查。默认工具沙箱禁止 ps，因此该 suite 最终在沙箱外使用本次夹具运行；不接真实 systemd。
- `python3 -B plugins/delegate/tests/test-review-guest.py`：11 项通过；真实临时文件读写/链接拒绝、编码/哈希/范围、guest 配置和 lease，未使用 SSH/VM。
- 新文件缺失时两套各退出 1；增强用例分别复现非相邻文件/目录冲突与字符串 argv 接受，修复后转绿；运行中 unit 与清理状态矛盾也先复现再修复。ps 被外层沙箱拒绝记为测试环境错误，未算通过。
- 旧 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：退出 0，52 shell + 17 Python，eval 7+12 通过；该入口尚不包含上述新 suite，也不包含新 OS gate。原生 Mac 上轮 3 项失败仍保留。

真实 service 启动、权威结束事实保留、unit 回收竞态、namespace/seccomp/代理、VM/SSH 控制、断线取消均未实现或实际验收；当前检查点未通过。service 元数据缺失时失败关闭。systemd-run 的变量展开默认开启，候选固定 `--expand-environment=no`；官方标注该参数自 254 提供，因此实际版本/能力预检必须拒绝不支持者。

## 下一次请求的安装范围

只安装一个用于**无模型隔离测试**的临时环境；不安装 delegate 插件、Claude/Codex CLI，不读/复制本机 Claude 凭据，不登录、不调用模型。

| 项目 | 固定来源与校验 | 目的 |
| --- | --- | --- |
| Lima 2.2.1 Darwin arm64 | [官方 release](https://github.com/lima-vm/lima/releases/tag/v2.2.1)，`lima-2.2.1-Darwin-arm64.tar.gz`，38,328,082 字节，SHA-256 `9e9eacce88f37e185c346bad73aa6136f738d8cdf8c3bb23cd42b071824bc66e` | 临时解包，用 macOS VZ，无 Homebrew/global 安装、QEMU、vmnet 服务或自动启动 |
| Debian 13 arm64 固定镜像 | [官方镜像](https://cloud.debian.org/images/cloud/trixie/20261001-2618/debian-13-genericcloud-arm64-20261001-2618.qcow2)，337,510,400 字节，SHA-512 `d8470b8c6c38fead046c794b5800a5a7b96672d5bcf543cc230ceb0c4b8ace05ed341a0c8928045422243fde26b2f1f2f58e99244c65709ffda2e3d4b674dd5a` | 只用该镜像，不使用 daily/latest/fallback 模板 |
| Node 22.22.0 Linux arm64 | [官方分发目录](https://nodejs.org/dist/v22.22.0/)，`node-v22.22.0-linux-arm64.tar.xz`，SHA-256 `1bf1eb9ee63ffc4e5d324c0b9b62cf4a289f44332dfef9607cea1a0d9596ba6f` | guest 专用工具目录解包，无系统 Node 切换 |
| srt 0.0.79 | 官方 npm 包，原记录中的 sha512 integrity；guest 专用 prefix/cache、不同空 user/global npmrc、ignore-scripts/no-audit/no-fund | 固定隔离 runtime，记录完整依赖树；无 npm global 安装 |
| guest OS 工具 | Debian 签名仓库中的 [bubblewrap 0.12.0-1~deb13u1](https://packages.debian.org/trixie/bubblewrap)、[socat 1.8.0.3-1+deb13u1](https://packages.debian.org/trixie/socat)，必要的 python3/rg/ca-certificates/dbus-user-session | 仅写本次 VM 磁盘。安装前模拟 apt 事务、固定所有实际包版本并记录；目标包缺失或事务超范围即停，不切版本 |

2026-10-09 实际只读核实：GitHub release API 给出上述 Lima digest/大小；固定 tag 的 [Debian template](https://raw.githubusercontent.com/lima-vm/lima/v2.2.1/templates/_images/debian-13.yaml)给出镜像摘要。HEAD 最初 302，跟随官方 Debian 镜像分发到 `laotzu.ftp.acc.umu.se` 后为 200 和上述大小。Node 官方 SHASUMS 用系统 curl 验证 TLS 读取；Python 本机证书缺失失败，未关闭证书检查。尚未下载安装包/镜像，摘要未对实际下载字节验证，镜像内 kernel/systemd 版本未知；[Debian 当前 systemd](https://packages.debian.org/trixie/systemd)页面是 257.13-1~deb13u1，不能据此猜镜像已安装版本。

## 路径、资源与配置

创建唯一 `/path/to/private-evidence`（0700），工具/下载/本次 Lima 配置/SSH 控制键/日志全部放在里面；只对这些命令显式传入 `LIMA_HOME=<该目录>/lima`，不使用或修改 `~/.lima`、全局 PATH、shell rc、SSH config、钥匙串、sudoers、sysctl、AppArmor、linger 或自启动项。
一台 VZ arm64 VM，**2 vCPU、4 GiB guest 内存、16 GiB 虚拟盘**；启动前核对本机资源，下载合计预算 1 GiB、专用目录实际占用预算 20 GiB，达到上限停止扩大动作。虚拟盘可稀疏分配，不能把 16 GiB 当作实际占用或承诺 host 总内存仅 4 GiB。

待创建的最小配置（先交 Lima 自身 validate；未经安装不可称验证过）：

```yaml
vmType: vz
arch: aarch64
cpus: 2
memory: 4GiB
disk: 16GiB
plain: true
images:
  - location: <已逐字节校验后位于专用临时目录的本地 qcow2>
    arch: aarch64
    digest: sha512:d8470b8c6c38fead046c794b5800a5a7b96672d5bcf543cc230ceb0c4b8ace05ed341a0c8928045422243fde26b2f1f2f58e99244c65709ffda2e3d4b674dd5a
mounts: []
portForwards: []
provision: []
ssh:
  forwardAgent: false
  forwardX11: false
  forwardX11Trusted: false
  loadDotSSHPubKeys: false
containerd:
  system: false
  user: false
rosetta:
  enabled: false
```

不继承模板/base/global override，不提供 host 文件共享，不导入用户 SSH 公钥，不用 preserve-env、不传 host API/provider 变量。不使用模板附带的 guest resolved 修改脚本；若原默认 SSH/DNS 不兼容，先报告具体失败。初始 SSH 密钥和基础 cloud-init 属于本次 VM 的正常初始化，不代表 Claude 登录。
LIMA_HOME 管理配置/实例但不重定向所有缓存：[v2.2.1 downloader](https://raw.githubusercontent.com/lima-vm/lima/v2.2.1/pkg/downloader/downloader.go)的 WithCache 使用 os.UserCacheDir，**本地镜像不缓存**。因此先在专用目录下载并校验，再以本地路径建 VM；关闭 containerd，避免其他 runtime 下载。若仍出现临时目录外写入条件，不扩大权限或借用用户全局缓存。

## 执行与收尾标准

批准后第一步下载并校验指定字节，再临时解包、读该版本帮助/校验配置；不直接运行远程安装脚本。只创建一个本次专用 guest，启动/初始化有界，读取实际版本与 capabilities，镜像/kernel/manager 不满足严格边界即停。guest apt/npm 初始化可写其专用磁盘；审查夹具运行阶段仍仅开放 run/temp，认证夹具只用合成数据。
然后继续 R2/R3 的实际启动/状态保存/传输代码和测试，覆盖正常/失败/超时/取消、setsid/double-fork、proxy/socat、无关 sentinel、断线期限和取消结果未知；同步拒写、范围外读、无任意网络与递归执行能力。未通过项不关闭 gate，不接 Claude 调用通道。
测试结束停止并删除**该 LIMA_HOME 中本次唯一** VM，确认相关进程结束，保留脱敏证据后删除拥有的临时目录。停止/删除失败时保留定位信息并报告，不删除运行中的磁盘或其他实例。摘要错误、权限拒绝、包版本不可得、额外配置需求、资源超限或未知结果均停止，不无限重试。安装批准不授权模型、用户登录、插件安装/升级、提交、推送或发布。


## 本轮收束核验

`git diff --check` 退出 0；4 个候选 Python 文件 AST 解析通过；14 份 Markdown 的 176 个本地文件链接有效，双语 CR 编号和命令选项集合一致。启用的 Spec Guard 来源通过 `codex plugin list --available --json` 的 installed/enabled 项动态解析，产物核验 3 通过/0 警告/0 失败；阶段 BUILDING，4 modules/specs/plans，claude-review 仍 17 个未勾项。远端插件目录查询在默认沙箱失败，不影响已启用本地来源读取，未重试安装或切换插件。

本轮没有改动任何旧产品已跟踪的命令、技能、脚本、测试或清单。新 suite 尚未加入免费总入口，因此旧总套通过与新候选测试通过分别报告；原生清单未改，本轮不把重复清单验证作为审查证据。以下摘要对应最终通过 14+11 基础测试的候选文件：

| 文件 | SHA-256 |
| --- | --- |
| `plugins/delegate/scripts/review_service.py` | `0693dceec4597e9afe7d3c0d4f7427c15f7ef0aa93d9ff2028eed7ea3ab65ad6` |
| `plugins/delegate/scripts/review_guest.py` | `9014b34c9c027a6b3706e413c2b9d767b7969e8de7f2fcad6920defa7a785aa1` |
| `plugins/delegate/tests/test-review-service.py` | `ba300a5b8f905d71fade3a270067728c097f7912475f51d03c153a256eccb012` |
| `plugins/delegate/tests/test-review-guest.py` | `44a349f7a5fa75260f2686ea3d134b0062848a47aeb3e6c3e94ffeb372caddc9` |


## 后续执行引用

上述是安装前的预览。用户后续“继续 快速推进啊”批准后已按范围执行；实际 Linux 15 项和 SSH 2 项通过，唯一临时 VM 与下载/控制目录均已清理。失败修复、版本/摘要及仍未知的原版 CLI 条件见[实际记录](2026-10-09-claude-review-linux.md)，不从安装或无模型通过推导后端完成。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
