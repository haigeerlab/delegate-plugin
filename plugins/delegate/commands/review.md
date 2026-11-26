---
description: "通过 Codex 或 Claude Code 对明确范围执行只读审查"
argument-hint: "[--backend codex|claude-code|auto] [--author-host codex|claude-code] (--paths <路径>|--base <提交>|--changes <模式>|--context <JSON>) [--previous-report <上一轮报告>] [--profile design] [--dry-run] [任务]"
allowed-tools: Bash
---

用户直接输入本命令授权其明确的审查；模型主动提议后须等待肯定答复。不要扩展用户范围，也不要再次索取同一范围已有的授权。付费执行和项目规则仍按会话中实际授权判断。

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" review [选项] -- "<任务>"
```

原样传递明确参数，任务作为完整参数并安全引用；Bash timeout 设为 600000。`--backend` 默认 codex，与主会话宿主无关。显式 `--backend claude-code` 实际调用 Claude；不能混用模型/专属参数或在失败时换后端。两个后端都只读，`--write` 明确拒绝，不自动转换为修复。

常用范围：`--paths <仓库根相对路径>` 可重复，`--exclude`、`--spec`、`--plan`、`--criterion` 可重复；模块加 `--module <名称>`。纯路径/模块默认读取 HEAD，排除未提交内容并展示工作区改动；需要工作区版本必须明确 `--changes staged|unstaged|working-tree`。只有 working-tree 可加 `--include-untracked`。`--repo` 可指定目标 Git 工作区。

固定 diff 用 `--base <提交> [--head <提交>]`，head 默认 HEAD；不能与 changes 混用。没指定 paths 的 diff 只选该比较的变更文件，不扩大为全项目；空比较不启动模型。缺范围先报告，不自行添加 `.`、整个项目或未跟踪文件。

高级 `--context <JSON>` 复用严格的范围合同，与所有快捷范围参数互斥。`--dry-run` 只做无模型输入预览：列出解析后的基准、文件摘要、排除/未审范围、未提交改动策略、权限和停止条件；不检查后端认证、不写审查产物，不代表审查通过。

复审用 `--previous-report <上一轮报告 JSON>`：只接受 delegate 自己产出、已有结论、范围相同（`commits` 下 `from` 也相同）的报告，读不到、结构不对或范围对不上都报固定码、退出 127、不启动模型。报告的 `recheck.items` 逐条给出上一轮阻断发现的 `resolved`／`unresolved`，`findings` 只放新问题；轮次计数和是否交给人由调用方判断。

模型用 `--model`（缺省见 README）；推理/限制参数按后端验证：Codex 支持 effort；Claude 首版拒绝 effort，支持 max-turns（默认 12）/max-budget-usd（客户端估算，非账单硬上限）。参数错误先失败，不重试。无可靠模型或宿主证据时输出 unknown。

Claude 当前仅 Mac 本机 CLI ≥2.1.295、Node ≥22.12.0、srt 0.0.79 和可用 GUI launchd 域；沿用原有认证。不安装、升级、登录或改全局配置。工具权限、上下文限制及包围整个 CLI 的 OS 隔离落实只读；allowedTools/Plan/提示词不是文件系统沙箱。递归 delegate 被拒绝。Codex 保留原进程组清理，detached 子进程限制仍存在。

Codex review 直接接收已校验的有限文件内容（逐行带行号）和摘要，不依赖命令读取文件；序列化输入上限 1 MiB，超限明确报告 codex_inline_input_limit，不截断或自动分批。启动前核实 shell/apps/plugins/multi_agent 关闭，禁用网络搜索并清空 MCP 配置；无法核实则停止。该核验不替代只读沙箱，也不证明模型全部行为。dry-run 显示输入方式、字节数和上限。

返回共同报告；退出 0 不等于无缺陷。权限拒绝、空/坏输出、部分覆盖、达限与失败不能当作通过；核对发现的触发条件、行号与证据。结论不授权修改、合并或交付。报告取 stdout；私有副本只认本次 stderr 的 `artifacts=` 路径，不按时间取最新。产物只按需用 `sed -n` 读片段。帮助用 `/delegate:help`，条件检查用 `/delegate:doctor --backend claude-code`。
