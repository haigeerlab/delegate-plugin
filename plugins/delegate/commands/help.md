---
description: "delegate 的审查、执行、后端能力与迁移帮助"
allowed-tools: Bash
---

先读取当前源码的无模型帮助，依据共享能力定义说明参数，不启动执行器或诊断：

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" --help
```

回答时按下列小标题分节、每条一行列出，不合并成长段；用户只问某项时只答那一节。

```text
/delegate:review --backend claude-code --paths src/login --model sonnet
/delegate:review --backend codex --base main --head HEAD
/delegate:review --paths src/payments --module payments --spec spec/payments.md --dry-run
/delegate:review --changes working-tree --paths src/login --include-untracked
/delegate:review --context /path/review.json
/delegate:run --write 按已确认方案修复空指针并运行相关测试
/delegate:run --resume 20261024183015.12345 --write 用户答复：选 A
/delegate:doctor --backend claude-code
```

**入口**
- `/delegate:review`：两个后端只读审查，拒绝 write；`/delegate:run`：仅 Codex 通用执行，Claude run 拒绝；`/delegate:doctor`：指定后端无模型体检；`/delegate:help`。
- 后端默认 codex，与主会话宿主无关；模型用 --model；不自动换宿主或 fallback，参数不混传。

**review 范围**
- 路径以仓库根为准，--repo 指定工作区；paths/module 默认读 HEAD，工作区须明确 changes，只有 working-tree 可含 untracked。
- base/head 与 changes 互斥；无 paths 时只选变更文件，不全项目扫描；context 与快捷参数互斥，旧 CLI review-context 保留；exclude/spec/plan/criterion 可重复。
- 仓库须已有提交，否则报 repository_has_no_commits（127）。
- dry-run 只预览，不调用模型、不查认证、不给结论。

**run**
- 末行 run_id/status/resumable：先看退出码 0 再看 status=done；超时退出 124。
- `--resumable` 才能停下问用户；`--resume <runId>` 只带用户原话。
- 1.3 参数仅 codex run：--continue、--timeout 541～7200（带它就用宿主后台模式）、--strict、--check、--authorized-by、--rules-file；用前读 references/run.md。
- --write 不提交，提交由调用方做。

**Claude 后端**
- 仅 Mac 本机 CLI ≥2.1.295、Node ≥22.12.0、srt 0.0.79（npm 包 @anthropic-ai/sandbox-runtime）、GUI launchd；可用 DELEGATE_CLAUDE_BIN、DELEGATE_NODE_BIN、DELEGATE_SRT_BIN 指定已有路径。
- 拒绝 effort；max-turns 默认 12，max-budget-usd 是估算不是账单上限；Codex 不支持这两项。实际模型／用量未知时不猜、不填零。不安装、登录或改全局配置。
- 模型主动越界及无差错自动 UI 输入仍未验证。

**结果与退出码**
- 退出 0、JSON 有效、无输出都不等于无问题；核对证据，列未审范围，不授权修改、合并或交付。
- 产物在私有 delegate-review／delegate 目录，按需读片段，要留证据须自行复制。
- 64 参数错误、127 条件不足、124 超时、130/143/129 中断；doctor 退出 0 只表示诊断完成。
- 预检失败核对 diagnostics 与实际 PATH；版本探测失败不等于未登录，不输出原始认证诊断；重新执行须符合已有授权。

**迁移**
- 旧 `/delegate:delegate`：通用任务改 run，审查改 review；不自动更新已安装缓存；安装、付费验收和发布分别按授权处理。
- 详细合同见源码 spec/claude-review.md，历史证据在源码 docs/verification/。
