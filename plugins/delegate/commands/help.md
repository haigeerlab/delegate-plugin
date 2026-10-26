---
description: "delegate 的审查、执行、后端能力与迁移帮助"
allowed-tools: Bash
---

先读取当前源码的无模型帮助，依据共享能力定义说明参数，不启动执行器或诊断：

```bash
/bin/bash "${CLAUDE_PLUGIN_ROOT}/scripts/delegate-exec.sh" --help
```

四个入口：`/delegate:review`（两个后端只读审查）、`/delegate:run`（既有 Codex 通用执行）、`/delegate:doctor`（指定后端无模型体检）、`/delegate:help`。主会话宿主与执行后端独立，默认 codex；模型另用 --model，不自动选相反宿主或 fallback。

```text
/delegate:review --backend claude-code --paths src/login --model sonnet
/delegate:review --backend codex --base main --head HEAD
/delegate:review --paths src/payments --module payments --spec spec/payments.md --plan tasks/payments/plan.md --dry-run
/delegate:review --changes working-tree --paths src/login --include-untracked
/delegate:review --context /path/review.json
/delegate:run --write 按已确认方案修复空指针并运行相关测试
/delegate:run --resume 20261024183015.12345 --write 用户答复：选 A
/delegate:doctor --backend claude-code
```

所有路径以目标仓库根为基准，可用 --repo 指定 Git 工作区。paths/module 默认读取 HEAD；工作区改动须明确 changes，只有 working-tree 可含 untracked。base/head 固定提交 diff，与 changes 互斥；无 paths 时仅选比较中的变更文件，不全项目扫描。exclude/spec/plan/criterion 可重复。高级 context 与快捷范围参数互斥；旧 CLI review-context 保留。dry-run 只是输入预览，不调用模型、检查认证或给出通过结论。

review 永远只读，拒绝 write；run 当前仅 codex，Claude run 拒绝。run 成功末行给出 run_id/status/resumable；`--resumable` 才可停下问用户，`--resume <runId>` 只带用户原话续跑，细则见 run 命令。Claude 首版拒绝 effort，提供 max-turns（默认12）及 max-budget-usd（估算，非账单硬上限）；Codex 不支持这两个限制参数。参数不混传，未知实际模型/用量不猜、不填零。

Claude 当前仅 Mac 本机 CLI ≥2.1.295、Node ≥22.12.0、srt 0.0.79、GUI launchd；已有绝对路径可通过 DELEGATE_CLAUDE_BIN、DELEGATE_NODE_BIN、DELEGATE_SRT_BIN 指定。沿用原认证，不安装/升级/登录/改全局配置。两方向普通四文件真实审查已有成功记录，各自仅证明固定源码/版本及有限范围；真实模型主动越界及无差错自动UI输入仍未验证；菜单到公共脚本的功能证据已核对，不以安装/假 CLI 通过替代。

报告区分执行状态与审查结论；退出0、JSON有效、无输出都不等于代码无问题。发现须核对证据，部分完成列未审范围，不授权修改、合并或交付。answer/report/log 分开保存在私有 delegate-review 目录，旧 Codex 自由文本日志在 delegate 目录；只按需读取片段。参数错误64、条件不足127、超时124、INT/TERM/HUP 130/143/129；doctor 退出0表示诊断完成，以问题和未验证项为准。

迁移：旧 `/delegate:delegate` 通用任务改用 `/delegate:run`；结构化只读审查改用 `/delegate:review`。源命令替换不自动更新已安装缓存；v0.5.0已采用新入口；安装、付费验收和发布分别按授权处理。详细合同见源码 spec/claude-review.md。

预检失败时核对 diagnostics 和宿主实际 PATH/运行时；CLI 版本探测失败不等于未登录。只报告可信分类，不输出原始认证诊断；重新执行须符合已有授权和停止条件。历史验收与详细故障证据留在源码仓库 docs/verification/，不要求安装副本包含这些开发记录。
