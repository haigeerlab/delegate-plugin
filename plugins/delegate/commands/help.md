---
description: "delegate 命令、使用场景、限制与故障帮助"
---

直接向用户说明以下帮助；不发起 Codex 任务，不运行诊断。结合用户问题可以精简，但不能省略相关权限与失败边界。

# delegate 使用帮助

把范围、方案和验收已明确的执行与查证委托给 Codex CLI；默认只读，返回最终答复，过程日志留在本机。

| 命令 | 作用 |
|---|---|
| `/delegate:delegate [选项] <任务>` | 执行一次委托 |
| `/delegate:doctor` | 刷新本地安装与 ChatGPT 登录检查，检查部分全局中文 AGENTS.md 规则 |
| `/delegate:help` | 显示帮助 |
| `/delegate:delegate-routing` | 宿主支持时调用分流判据 skill，不自行执行 |

参数：`--write` 可写；`--model <slug>` 指定模型；`--effort <level>` 指定推理档；`--` 终止选项解析；脚本 `--help` / `-h` 显示本地用法。模型和档位省略时遵循 Codex 配置，非法值由 CLI 报错。

```text
/delegate:delegate 审查 src/login 的错误处理，只报告有证据的问题
/delegate:delegate --write 按已确认方案修复空指针，运行相关测试
/delegate:delegate --model <模型 slug> --effort high 梳理登录链路
```

适合：代码审查、跨文件探索、定位问题、明确方案后的实现与批量机械修改。需求澄清、架构取舍和最终验收留在主会话。

要求：Claude Code 插件宿主、Codex CLI、Python 3、Git、Bash；在业务 Git 工作区调用。使用 `codex login` 登录 ChatGPT；`codex login status` 核实状态。API key 登录或未知认证会被拒绝。直接输入委托命令表示授权当前任务；模型主动提议时须等待明确肯定答复。用户须在当前轮明确授权写入，模型不得自行添加 `--write`。

Claude Bash timeout 设 600000；Codex 执行默认最多 540 秒，`DELEGATE_TIMEOUT_SECONDS` 可缩短，上限 540，非法值回落默认。超时与中断会停止执行进程组，不能保证回收自行脱离进程组的进程。

成功返回答复与日志路径。写模式在成功、执行失败、超时、空答复和中断后均提供 Git 概览；失败不会回滚已发生的修改。查看实际 diff 与测试，不能只相信模型自述；已有用户改动可能混在统计里。

日志在 `${TMPDIR:-/tmp}/delegate/`，尽力保留最近 50 组。失败日志回显最多 40 行 / 16KiB；按需读取少量行。最终答复和单个日志没有体积上限。

错误：64=参数或非 Git 工作区；127=基础 CLI / Python 条件失败；124=执行超时；其他非零=认证或任务失败。先看错误、日志路径、Git 状态；接入问题运行 `/delegate:doctor`。doctor 退出 0 表示诊断完成，看文本的问题数量。

doctor 不验证远端、额度、模型权限或所有规则；只检查部分中文全局规则并刷新临时缓存。安装缓存不会随源目录自动更新，用户主动更新插件或开发时用 `claude --plugin-dir <插件目录>` 加载当前源码。

权限由 Codex 沙箱及宿主配置决定，可写范围可能含临时目录/额外根目录。确认、不提交/推送/发布、网络范围等要求是行为指令，没有不可绕过的 wrapper 授权机制。插件不提供后台编排、自动重试、多后端、团队配额管理，也不保证结果正确。
