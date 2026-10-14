# 当前 Mac 本机路线核对

日期：2026-10-10；仓库 delegate-plugin，分支 `codex/spec-guard-conventions-public`。用户补充：“只要当前mac 环境可用就可以了 我插件目前只要mac 可以用就可以了”。本批按当前 Mac 本机使用收敛，不要求用户准备 Linux guest，不扩展其他平台。已有候选实际仍连接 guest，**不能据其开发完成宣称 Mac 原生版本完成**。历史 VM 测试和批准分别保留，不追认为原生证据。

## 已核实

- 平台 Darwin arm64，本机原版 Claude 可执行文件规范路径 `/path/to/user-home/.local/share/claude/versions/2.1.295`；固定安全参数的 version 返回 2.1.295，退出 0。
- 原版 CLI 的 `auth status --json` 在原有认证环境返回退出 0、loggedIn:true、authMethod:claude.ai、apiProvider:firstParty。只保存这些安全字段，未保存邮箱、账号、凭据或完整输出，未直接读取/复制认证文件。
- sandbox-exec 存在，先前单独批准的临时 srt 0.0.79 仍存在；没有安装升级新依赖，未创建/启动 VM，未登录或调用模型。认证预检不能证明模型权限、额度或服务可用。

## 当前认证与进程限制实验

每次仅调用原版 auth status，单次 6 秒截止、单独进程组及专用临时目录，结束清理本次对象。OS 规则拒绝全局文件写入和网络；下面的 allow-default 读取规则仅用于认证可行性对照，**不是产品快照文件读取白名单**，也不证明完整审查边界。

| 无模型探针 | 退出 | loggedIn | 结论 |
|---|---|---|---|
| 拒绝文件写入、仅开放本次临时目录 | 1 | false | 缺少标准输出辅助路径权限，不能据此说用户未登录 |
| 上项加 deny process-fork | 1 | false | 不能据此证明只读调用可用 |
| 拒绝全局文件写入、允许临时目录及 `/dev/null` | 0 | true | 当前本机认证能在该只读文件边界下使用 |
| 上项再加 deny process-fork | 1 | false | 全部禁止派生进程与当前认证不兼容，不能作为已验证生产方案 |

原版状态探针未传任务或 `-p`，模型调用 0；无安装、登录、委托或交付操作。每项临时目录由本次 context manager 清理。拒绝派生进程导致认证失败的更细粒度内部调用尚未验证，不猜测具体凭据读取实现。

## 进程机制结论及未完成项

以前 Mac 原生生命周期 5 通过/3 失败保持原始结果：setsid helper 在超时、取消和父先退情况下逃出进程组。原版 CLI 认证成功不修复这些失败。Apple 的 [launchd plist 定义](https://raw.githubusercontent.com/apple-oss-distributions/launchd/main/man/launchd.plist.5)只给出同进程组剩余进程的终止行为，不能当作 Linux cgroup 的替代；[XNU setsid/setpgid 实现](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_prot.c)也不能据此假设 sandbox 的 process-info-setcontrol 阻止脱离。

官方 [CLI 参考](https://code.claude.com/docs/en/cli-reference)核对：safe-mode 保留认证但管理设置仍适用；restricted 限制普通设置和工具，并不等于整个进程的 OS 文件隔离。不能因两选项或只读提示词省略权限机制。

当前下一步是计划中的 Mac 原生免费切片：先证明与当前认证兼容的进程边界，再接本机 Claude 入口及固定快照/结果/日志。原版模型启动后的工具、权限、网络/刷新、清理及两向真实宿主仍未验收。保留原只读与进程清理标准，不静默改成尽力清理、不把 VM 实测算作 Mac 原生通过。需要放宽合同或新增系统权限时，展示具体证据和取舍再请用户决定。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
