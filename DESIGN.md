# delegate 的设计与边界

简体中文 | [English](docs/en/DESIGN.md)

将明确范围的只读审查交给 Codex 或 Claude Code CLI，将已定方案的通用执行交给 Codex；两个宿主使用同一源入口，只带回最终答复。主会话负责需求澄清、取舍、授权与验收。独立运行减少主会话携带过程日志的体量，但不保证总 token 或费用降低。

## 决策是否已定

适合委托：审查、跨文件摸结构、复现定位、明确方案的单个任务与机械修改。取舍尚未完成或范围尚不明确时，主会话继续判断。写文件需要用户当前轮明确授权。

```text
SessionStart → 刷新基础探测缓存（不输出上下文）
用户明确委托，或确认模型的具体提议 → review/run 命令 → 后端专属参数与实时认证检查
→ Git 范围/工作区检查 → 所选后端执行 → 答复 / 失败诊断
→ Codex run 写模式无论执行成功与否均输出 Git 概览 → 主会话验收
UserPromptSubmit 已退役，不按每轮输入探测、提醒或要求重复确认
```

## 职责划分

源命令按用途分为 review/run/doctor/help。delegate_cli.py 负责快捷输入与无模型预览，delegate_capabilities.py 只定义两个后端能力；公共 backend 保持旧脚本兼容。review 始终只读，run 当前仅 Codex。范围快捷参数转为既有共同上下文，不绕过采集/权限/结果验证。v0.5.0 已发布这些接口，本机两宿主安装已核对；旧命令迁移见 [模块合同](spec/claude-review.md)。

公共 `delegate-exec.sh` 分派后端与专属参数，保留 `codex-exec.sh` 兼容路径。新 `claude-review` 模块独立管理共同上下文/快照/结果、Claude 预检与本机 Mac 运行边界，不扩展 Spec Guard 执行器。detection 缓存与 Hook 仍只表明默认 Codex 基础状态，显式 Claude 不经过该认证闸门。

Claude 仅只读审查：工具限制收敛能力，safe/restricted 收敛项目/插件上下文，srt 收敛整个 CLI 的文件/网络访问；临时 launchd 任务提供独立的内核 resource coalition，STOP 屏障、PID 代际信号及成员计数负责本次 helper 清理。只使用已存在的本机 CLI/认证和运行依赖，不安装 LaunchAgent 或修改全局设置。固定快照有原路径/哈希映射；数据不是执行指令。共同报告由 wrapper 持有执行身份，权限/解析/覆盖不足不能变成无问题。两个方向的真实审查都有成功记录，菜单到公共脚本的实际执行和完整 dry-run 已核对；这些证据只对应各自当时的源码版本，发布时没有重新做双向真实验收。主动诱导模型写入或递归、认证刷新、异常的自然 helper 进程和长期稳定性仍未验证，详见 [模块合同](spec/claude-review.md)。

- `backend.py` 是 channel 与 detection 共用的基础检查：PATH、可执行版本命令、CLI 报告的 ChatGPT 登录。
- `channel` 管理调用、沙箱选择、日志、执行期限与进程组清理；不判断任务是否值得委托。
- `detection` 管理基础状态缓存与 doctor，不调用模型，不承诺远端或额度可用。
- `routing` 响应显式请求并提供判据；需要时按后端体检，不以 Codex 缓存推断 Claude 可用，不按关键词分类或自动发起执行。
- 命令和 skill 表达用户授权纪律；最终正确性由调用方根据真实 diff 和测试验收。

## Codex run 执行合同

默认 `read-only`，显式 `--write` 才用 `workspace-write`。两种模式均要求 Git 工作区；不强制工作区干净。写模式记录基线与原有变更，执行开始后所有退出路径输出验收概览，失败不会自动回滚。

执行期限默认/上限 540 秒，认证探测单项 5 秒；中止时先冻结 Codex 进程组、沿 ppid 链快照后代，对换了进程组或会话的后代组发 TERM，随即对 Codex 组发 TERM 并解冻，两边共用最多 2 秒宽限后 KILL 残余，最后最多等 5 秒回收直接子进程；回收不了时报告 PID 并退出 125，清理结果写进 `.cleanup` 并转发到 stderr（S41）。正常退出也清理组内残余进程；Codex 正常结束后自己留下的后台进程不在保证内。Bash 工具外部 timeout 为 600 秒，留下探测和清理时间。

stdin 从 `/dev/null` 输入；`-o` 最终答复和合并 stdout/stderr 过程日志分离。最近 50 组尽力清理；失败回显最多 40 行/16KiB；最终答复不作固定压缩率承诺。

认证通过 CLI 状态，兼容 CLI 自身的文件与钥匙串存储；不读取凭据文件。拒绝 API key/未知状态，执行时删除两种 API key 环境变量并设置 ChatGPT 登录与 OpenAI provider。CLI 行为变化可能导致保守拒绝。

## 控制边界

确认闸门是模型指令，不是 wrapper 的不可绕过技术锁。preamble 的不提交、不推送、不发布和网络范围要求同样是行为指令。沙箱真实边界由 Codex 与宿主配置决定，workspace-write 可以包含临时目录和额外可写根。

缓存只能说明近期本地基础条件。可用结果过期、身份变化或缓存异常会静默降级；真正执行前重新探测认证。doctor 强制刷新，但其中文规则启发式不覆盖全部项目/全局规则，也不验证网络、额度和模型权限。

## 取舍

仅支持 Codex 和可选 Claude Code 两个明确执行后端，默认 Codex，不自动识别宿主并换执行者；无后台控制面、排队、断点恢复或自动重试。两种模式统一拒绝非 Git 目录，使可执行条件与验收方式一致。用户已有修改被保留，归属需通过 diff 人工判断。

确定性合同以免费桩测试验证；真实沙箱、远端请求和交互模型行为需要用户决定进行 live 验证。eval 显式加载源码，PASS/FAIL/NORUN 分开；首行固定格式判决避免正文误报。[能力图](spec/CAPABILITY-MAP.md)和 [README](README.md)提供模块与使用入口。
