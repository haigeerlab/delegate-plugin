# Usage draft: s110-design-review

来源：生态总账 S110「开发流程改版」（plugin-ecosystem 仓 `research/2026-11-24-开发流程改版/需求.md`，第五节与第七节 delegate 行），由 ecosystem-lead #22330 分派。用户 2026-11-24 在本会话确认 delegate 部分的需求与 Q1～Q7，原话「说完了，按推荐定」；对接结论已发 sg-coord（#22369）。用户 2026-11-24 批准本草案，原话「批准」。调用方是 spec-guard 新流程里写技术方案的那个会话：它按阶段提示调 delegate 审 `tasks/<id>/design.md`，把报告交 spec-guard 的 review_mark 记轮次。

## Entry points

| Entry | Does | Module |
|---|---|---|
| `/delegate:review --profile design` | 用技术方案判据 `design-v1` 审查：阻断必须指向快照里非技术方案文件的真实行号，拿不出的降为建议并标 `downgraded: "no_code_evidence"`；第二轮（带 `--previous-report`）只核对上一轮，新发现一律为建议 | design-review-criteria |
| `/delegate:review --backend auto --author-host <claude-code／codex>` | 按本机无模型检查选审查者：优先异厂商，否则同厂商全新会话，都不可用时出「未审」报告；报告顶层 `reviewer` 写明厂商、是否同厂商、选择方式 | reviewer-selection |
| `/delegate:doctor` | 列出本机可用的审查者；只有一家时提示建议再开通一家，不卡住 | reviewer-selection |
| `interface.json` 的 `review.profiles`、`review.reviewer` | 声明 `design` 档与判据名、`auto` 选择与报告字段 | design-review-criteria, reviewer-selection |

## Typical usage

### U1: 普通需求的技术方案，异厂商审一轮、改一轮

主开发是 Claude Code，本机 Codex 也可用。会话写完 `tasks/<id>/design.md`，按阶段提示调：

```text
/delegate:review --profile design --backend auto --author-host claude-code --paths tasks/<id>/design.md --spec spec/<id>.md --spec <影响面里列的已有文件>… "<审查任务>"
```

报告 `reviewer` 为 `{vendor: "openai", backend: "codex", same_vendor: false, selection: "cross_vendor"}`，判据 `design-v1`。每条阻断都指向某个已有代码文件的具体行，说明按方案做会在哪里出错；指向技术方案自身或行号不存在的，在报告里是 `suggestion` 并带 `downgraded: "no_code_evidence"`。有阻断就改方案、提交，第二轮同样的参数加 `--previous-report round1.report.json`：`recheck.items` 逐条给出上一轮阻断是否已解决，`findings` 里的新问题都是 `suggestion`。阻断集合为空就往下走。

### U2: 只开通了一家，回退同厂商

主开发是 Claude Code，本机 Codex 不可用（没装或没登录），Claude Code 可用。同样的命令，报告 `reviewer` 为 `{vendor: "anthropic", backend: "claude-code", same_vendor: true, selection: "same_vendor_fallback"}`。审查在全新的 Claude Code 会话里进行，不继承调用方上下文；spec-guard 把「同厂商审查」照记进 `designApproval.sameVendor`。主开发是 Codex、只有 Codex 可用时对称。

### U3: 两家都不可用，写明「未审」

同样的命令，报告 `execution_status=conditions_missing`、`review_outcome=inconclusive`、诊断含 `no_reviewer_available`、`reviewer.selection="none"`、`backend_started=false`，退出 127。调用方按「未审」记录，交回归测试兜底，不当作审查失败重试。

### U4: 开工前体检

```text
/delegate:doctor
```

列出 Codex、Claude Code 两个审查者各自是否可用（只做无模型检查）。只有一家可用时，提示「建议再开通一家，以便异厂商审查」；不阻止任何操作。

## Milestones

| Milestone | Usage | Modules |
|---|---|---|
| M1 | U1, U2, U3, U4 | design-review-criteria, reviewer-selection |

<!-- spec-guard: milestone M1 confirmed design-review-criteria, reviewer-selection -->
