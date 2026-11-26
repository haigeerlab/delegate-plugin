# Usage draft: auto-takeover-review

<!-- 2026-11-21 补写：S101 一次拆出 review-severity、review-recheck 两个模块，按 spec-guard「用法草案」规则应在第一个模块的 Spec 之前审完，当时漏写；
     ecosystem-lead #21941 指出后补写，随 review-recheck 的 Checkpoint 2 一并交用户审。两个模块的已批准 Spec 不因本草案改动。 -->

来源：生态总账 S101「自动接管」合并方案（plugin-ecosystem 仓 `research/2026-11-21-自动接管合并方案.md`，第 2 节 delegate 行）。调用方是 autopilot 的编排：用 Codex 审查一个 PR 的补丁，按阻断／建议处理意见，阻断返工后复审，两轮仍未解决交给人。

## Entry points

| Entry | Does | Module |
|---|---|---|
| `/delegate:review` 报告的 `findings[].severity` | 每条发现标 `blocking` 或 `suggestion`（判据 `severity-v1`，`--task` 改不了） | review-severity |
| `interface.json` 的 `review.report.severity` | 声明字段、取值、判据名，以及缺失按 `blocking` | review-severity |
| `/delegate:review --previous-report <上一轮报告>` | 复审：上一轮的阻断逐条标 `resolved`／`unresolved`，进报告 `recheck.items`；`findings` 只放新问题 | review-recheck |
| `interface.json` 的 `review.recheck` | 声明参数名、报告字段名和两种状态 | review-recheck |
| 快照审查（`--paths`／`--spec`／`--plan`）带 `--previous-report` | 返工后复审 Plan 这类快照审查；`interface.json` 的 `review.recheck.snapshot` 为 `true` 表示支持 | review-snapshot-recheck |

## Typical usage

### U1: 审查报告带严重程度，调用方据此分流

编排对一个 PR 的补丁发起审查：

```text
/delegate:review --backend codex --base <PR 基准提交> --head <PR 头提交> "<任务与验收标准>"
```

标准输出是一份 JSON 报告，保存为 `round1.report.json`。只有 `execution_status=completed` 且 `review_outcome` 为 `findings` 或 `no_findings_in_scope` 时才往下看；否则当作「Codex 不可用或没有结论」，停下等人，不改用 Claude 后端自审。有结论时逐条看 `findings[].severity`：`blocking`（以及缺失或不认识的值）进入返工；`suggestion` 由 Claude 决定改不改，写一句理由留档。`unverified` 非空的阻断表示审查者拿不准、按判据从严标的。没有阻断发现也不等于可以合并。

### U2: 返工后带上一轮报告复审

返工提交后，用同样的范围参数（同一个 `--base`，`--head` 换成新的提交）复审，并把上一轮报告交进来：

```text
/delegate:review --backend codex --base <PR 基准提交> --head <新的头提交> --previous-report round1.report.json "<任务与验收标准>"
```

报告的 `recheck.items` 对上一轮每条阻断给出 `resolved` 或 `unresolved` 和证据，`findings` 只放这次新发现的问题。本轮阻断集合 = `unresolved` 的旧项 + `findings` 里按 `blocking` 处理的；为空就进入后续流程，不为空再返工。第三轮把第二轮报告交进来即可连着复审。「两轮仍未解决交给人」由编排自己数轮次。要核对复审的是修正后的补丁，比较 `recheck.previous_fingerprint` 与本轮 `scope.fingerprint`。上一轮报告读不到、没有结论或范围对不上时，报 `previous_report_*`、退出 127、模型不启动。

### U3: Plan 审查返工后复审（快照审查）

编排审一份 Plan，用快照审查（不带 `--base`），Spec 作为参考文件带上：

```text
/delegate:review --backend codex --paths tasks/<模块>/plan.md --spec spec/<模块>.md "<任务与验收标准>"
```

报告保存为 `round1.report.json`，按 U1 分流。有阻断就返工 Plan 并提交，然后用同样的 `--paths` 复审：

```text
/delegate:review --backend codex --paths tasks/<模块>/plan.md --spec spec/<模块>.md --previous-report round1.report.json "<任务与验收标准>"
```

两轮都是快照、`paths` 相同、新提交在上一轮提交之后时可以复审，`recheck` 的读法与 U2 相同；`--spec` 带进来的文件只用来核实引用，不会对它本身提发现。要核对复审的是改过的 Plan，比较两轮报告 `scope.files` 里 Plan 的 sha256（快照没有补丁，指纹每轮相同）。新提交不在上一轮提交之后（例如换了分支）时，报 `previous_report_scope_mismatch`、退出 127。

## Milestones

| Milestone | Usage | Modules |
|---|---|---|
| M1 | U1, U2 | review-severity, review-recheck |
| M2 | U1, U2, U3 | review-snapshot-recheck |

<!-- spec-guard: milestone M1 confirmed review-severity, review-recheck -->
<!-- spec-guard: milestone M2 confirmed review-snapshot-recheck -->

M1 实跑（2026-11-21，用户判定原话「M1 通过」）：本机两侧升到 0.10.0 后，用安装版 `delegate-exec.sh` 在临时仓库实跑。U1：Codex 审 `--base/--head` 补丁，`completed`、`findings`，故意留的 `add` 减法缺陷标为 `blocking`。U2：修正后带 `--previous-report` 复审，`completed`、`no_findings_in_scope`，上一轮阻断标为 `resolved` 并给证据，`previous_report_sha256` 与上一轮文件一致，`previous_fingerprint` 与上一轮指纹一致且与本轮不同。另验范围不同时退出 127、`previous_report_scope_mismatch`、不启动模型。只跑了 Codex 后端；Claude 后端、访客路径与 `unresolved` 路径未实跑。
