# 验证记录索引

简体中文 | [English](../en/verification/README.md)

本目录保存各轮验收、真实验证、修复复核和审查记录。文件按日期平铺、原位保留，不移动也不改写：其他记录、计划和 JSON 证据以原路径和 SHA-256 引用它们。本页只做导航。

- **结果/记录**：一轮验收、修复或审查的结论。
- **方案/预览**：执行前的方案、批次预览或交接（`*-plan.md`、`*-preview.md`）；同名 `*-preview.json`、`*-handoff.json` 是对应的机器可读草案。
- **配套数据**：同一前缀的 `*.json`（结果或预览）与 `*.py.txt`（当时使用的检查脚本原文，不作为当前可执行脚本）。

记录保留发生时的版本、授权和状态，不是当前安装或行为合同。当前状态从[合同条款与验证证据](2026-10-08-contract-matrix.md)和 [delegate 双后端当前交付状态](2026-10-13-delegate-delivery-status.md)读起；历史证据边界见[历史验证证据索引](2026-10-08-history.md)。

## 2026-10-08 接入批次与历史核对

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [剩余七项的集中验收方案](2026-10-08-batch-plan.md) | 方案/预览 | — |
| [七项整批验收结果](2026-10-08-bulk.md) | 结果/记录 | [2026-10-08-bulk-closeout.py.txt](2026-10-08-bulk-closeout.py.txt)、[2026-10-08-bulk-results.json](2026-10-08-bulk-results.json) |
| [当前合同条款与验证证据](2026-10-08-contract-matrix.md) | 结果/记录 | — |
| [F8 测试隔离修复与实际验证](2026-10-08-f8-applied.md) | 结果/记录 | [2026-10-08-f8-applied-results.json](2026-10-08-f8-applied-results.json) |
| [119 个历史未勾项逐项裁决](2026-10-08-historical-reconciliation.md) | 结果/记录 | [2026-10-08-historical-reconciliation.json](2026-10-08-historical-reconciliation.json) |
| [2026-10-08 历史验证证据索引](2026-10-08-history.md) | 结果/记录 | — |
| [当前快照有限 live 验证](2026-10-08-live.md) | 结果/记录 | [2026-10-08-live-results.json](2026-10-08-live-results.json) |
| [免费变异与业务目录零足迹核验](2026-10-08-mutation.md) | 结果/记录 | [2026-10-08-mutation-results.json](2026-10-08-mutation-results.json) |
| [唯一剩余交互条件的单会话验收方案](2026-10-08-proposal-plan.md) | 方案/预览 | — |
| [最后一项的原生交互验收结果](2026-10-08-proposal.md) | 结果/记录 | [2026-10-08-proposal-closeout.py.txt](2026-10-08-proposal-closeout.py.txt)、[2026-10-08-proposal-preparation.json](2026-10-08-proposal-preparation.json)、[2026-10-08-proposal-results.json](2026-10-08-proposal-results.json) |
| [Redaction of public evidence](2026-10-08-public-redaction.en.md) | 结果/记录 | — |
| [公开材料的脱敏说明](2026-10-08-public-redaction.md) | 结果/记录 | [2026-10-08-public-redaction.json](2026-10-08-public-redaction.json) |
| [免费离线定向补验](2026-10-08-supplemental.md) | 结果/记录 | [2026-10-08-supplemental-results.json](2026-10-08-supplemental-results.json) |

未对应单独说明页的数据：[2026-10-08-batch-preparation.json](2026-10-08-batch-preparation.json)、[doctor-isolation-proposal-results.json](doctor-isolation-proposal-results.json)、[doctor-isolation-proposal.patch.txt](doctor-isolation-proposal.patch.txt)、[doctor-isolation-proposal.py.txt](doctor-isolation-proposal.py.txt)、[f8-applied-check.py.txt](f8-applied-check.py.txt)、[historical-evidence.json](historical-evidence.json)、[live-batch-check.py.txt](live-batch-check.py.txt)、[mutation-check.py.txt](mutation-check.py.txt)、[supplemental-check.py.txt](supplemental-check.py.txt)。

## Claude 审查后端：隔离闸门与 Mac 验收（2026-10-09 至 10-12）

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [Claude 审查：专用 Linux VM 的实际无模型验证](2026-10-09-claude-review-linux.md) | 结果/记录 | — |
| [专用临时 VM 验证预览](2026-10-09-claude-review-vm-preflight.md) | 方案/预览 | — |
| [Claude 审查隔离闸门：2026-10-09](2026-10-09-claude-review.md) | 结果/记录 | — |
| [当前 guest 整合与原版 CLI 无模型验收](2026-10-10-claude-review-guest-cli.md) | 结果/记录 | [2026-10-10-claude-review-guest-cli.json](2026-10-10-claude-review-guest-cli.json) |
| [Claude 审查候选调用链：本轮集成与验证](2026-10-10-claude-review-integration.md) | 结果/记录 | — |
| [Mac 真实审查：首个有限批次预览](2026-10-10-claude-review-mac-live-plan.md) | 方案/预览 | — |
| [Claude 审查后端：当前 Mac 原生实现与验收记录](2026-10-10-claude-review-mac-native.md) | 结果/记录 | — |
| [当前 Mac 本机路线核对](2026-10-10-claude-review-mac-preflight.md) | 结果/记录 | — |
| [真实反向审查预览：Claude Code → Codex](2026-10-10-claude-review-mac-reverse-plan.md) | 方案/预览 | — |
| [修复后反向第二批验收预览](2026-10-10-claude-review-mac-reverse-second-plan.md) | 方案/预览 | — |
| [反向第四批当前预览：重启后宿主与实际CLI入口](2026-10-12-claude-review-mac-reverse-fourth-current-plan.md) | 方案/预览 | — |
| [当前第四批驱动纠错交接](2026-10-12-claude-review-mac-reverse-fourth-fixed-plan.md) | 方案/预览 | — |
| [反向第四批：固定 Node 运行时后的验收预览](2026-10-12-claude-review-mac-reverse-fourth-plan.md) | 方案/预览 | — |
| [当前 Mac 双向普通审查收束](2026-10-12-claude-review-mac-reverse-fourth-success.md) | 结果/记录 | [2026-10-12-claude-review-mac-reverse-fourth-success.json](2026-10-12-claude-review-mac-reverse-fourth-success.json) |
| [修复后反向第三批验收预览](2026-10-12-claude-review-mac-reverse-third-plan.md) | 方案/预览 | — |

未对应单独说明页的数据：[2026-10-10-claude-review-mac-live-first.json](2026-10-10-claude-review-mac-live-first.json)、[2026-10-10-claude-review-mac-live-followup-preview.json](2026-10-10-claude-review-mac-live-followup-preview.json)、[2026-10-10-claude-review-mac-live-fourth-preview.json](2026-10-10-claude-review-mac-live-fourth-preview.json)、[2026-10-10-claude-review-mac-live-fourth.json](2026-10-10-claude-review-mac-live-fourth.json)、[2026-10-10-claude-review-mac-live-second.json](2026-10-10-claude-review-mac-live-second.json)、[2026-10-10-claude-review-mac-live-third-preview.json](2026-10-10-claude-review-mac-live-third-preview.json)、[2026-10-10-claude-review-mac-live-third.json](2026-10-10-claude-review-mac-live-third.json)、[2026-10-10-claude-review-mac-reverse-current-preview.json](2026-10-10-claude-review-mac-reverse-current-preview.json)、[2026-10-10-claude-review-mac-reverse-first.json](2026-10-10-claude-review-mac-reverse-first.json)、[2026-10-10-claude-review-mac-reverse-handoff.json](2026-10-10-claude-review-mac-reverse-handoff.json)、[2026-10-10-claude-review-mac-reverse-preview.json](2026-10-10-claude-review-mac-reverse-preview.json)、[2026-10-10-claude-review-mac-reverse-second-handoff.json](2026-10-10-claude-review-mac-reverse-second-handoff.json)、[2026-10-10-claude-review-mac-reverse-second-preview.json](2026-10-10-claude-review-mac-reverse-second-preview.json)、[2026-10-10-claude-review-mac-startup.json](2026-10-10-claude-review-mac-startup.json)、[2026-10-12-claude-review-mac-reverse-fourth-current-preview.json](2026-10-12-claude-review-mac-reverse-fourth-current-preview.json)、[2026-10-12-claude-review-mac-reverse-fourth-driver-result.json](2026-10-12-claude-review-mac-reverse-fourth-driver-result.json)、[2026-10-12-claude-review-mac-reverse-fourth-fixed-preview.json](2026-10-12-claude-review-mac-reverse-fourth-fixed-preview.json)、[2026-10-12-claude-review-mac-reverse-fourth-preview.json](2026-10-12-claude-review-mac-reverse-fourth-preview.json)、[2026-10-12-claude-review-mac-reverse-second-result.json](2026-10-12-claude-review-mac-reverse-second-result.json)、[2026-10-12-claude-review-mac-reverse-third-handoff.json](2026-10-12-claude-review-mac-reverse-third-handoff.json)、[2026-10-12-claude-review-mac-reverse-third-preview.json](2026-10-12-claude-review-mac-reverse-third-preview.json)、[2026-10-12-claude-review-mac-reverse-third-result.json](2026-10-12-claude-review-mac-reverse-third-result.json)。

## 双后端接口与 Codex 源码加载（2026-10-10 至 10-12）

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [双后端命令接口调整与验证](2026-10-10-delegate-interface.md) | 结果/记录 | [2026-10-10-delegate-interface.json](2026-10-10-delegate-interface.json) |
| [双后端实现的最终定向复核](2026-10-12-delegate-final-review.md) | 结果/记录 | [2026-10-12-delegate-final-review.json](2026-10-12-delegate-final-review.json) |
| [下一批：Codex源码插件隔离加载（待批准）](2026-10-12-delegate-source-load-plan.md) | 方案/预览 | — |
| [临时Codex源码加载：安装成功，完整命令迁移未通过](2026-10-12-delegate-source-load-result.md) | 结果/记录 | [2026-10-12-delegate-source-load-result.json](2026-10-12-delegate-source-load-result.json) |

未对应单独说明页的数据：[2026-10-12-delegate-preflight-fix.json](2026-10-12-delegate-preflight-fix.json)、[2026-10-12-delegate-source-load-preview.json](2026-10-12-delegate-source-load-preview.json)、[2026-10-12-node-environment-repair.json](2026-10-12-node-environment-repair.json)。

## 命令迁移、安装同步与 S1–S3（2026-10-13）

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [Checkpoint3：当前diff与验收限制待人工审阅](2026-10-13-delegate-checkpoint3-review.md) | 结果/记录 | [2026-10-13-delegate-checkpoint3-review.json](2026-10-13-delegate-checkpoint3-review.json) |
| [UI-001：Claude重载后仍显示旧delegate入口](2026-10-13-delegate-claude-desktop-entry-mismatch.md) | 结果/记录 | [2026-10-13-delegate-claude-desktop-entry-mismatch.json](2026-10-13-delegate-claude-desktop-entry-mismatch.json) |
| [Claude delegate 安装及四入口显示验收通过](2026-10-13-delegate-claude-install-staged-result.md) | 结果/记录 | [2026-10-13-delegate-claude-install-staged-result.json](2026-10-13-delegate-claude-install-staged-result.json) |
| [Claude delegate 刷新修正批次：卸载成功、安装失败停止](2026-10-13-delegate-claude-refresh-fixed-result.md) | 结果/记录 | [2026-10-13-delegate-claude-refresh-fixed-result.json](2026-10-13-delegate-claude-refresh-fixed-result.json) |
| [Claude delegate 正常安装刷新：已批准批次失败停止](2026-10-13-delegate-claude-refresh-result.md) | 结果/记录 | [2026-10-13-delegate-claude-refresh-result.json](2026-10-13-delegate-claude-refresh-result.json) |
| [delegate 命令审查问题：三批修复结果](2026-10-13-delegate-command-fixes-result.md) | 结果/记录 | [2026-10-13-delegate-command-fixes-result.json](2026-10-13-delegate-command-fixes-result.json) |
| [help命令漏迁移：根因与修正](2026-10-13-delegate-command-migration-fix.md) | 结果/记录 | [2026-10-13-delegate-command-migration-fix.json](2026-10-13-delegate-command-migration-fix.json) |
| [delegate 命令与功能多维审查](2026-10-13-delegate-command-multiaxis-review.md) | 结果/记录 | [2026-10-13-delegate-command-multiaxis-review.json](2026-10-13-delegate-command-multiaxis-review.json) |
| [delegate 双后端当前交付状态](2026-10-13-delegate-delivery-status.md) | 结果/记录 | — |
| [两宿主新入口：CLI 加载核验](2026-10-13-delegate-host-command-loading.md) | 结果/记录 | [2026-10-13-delegate-host-command-loading.json](2026-10-13-delegate-host-command-loading.json) |
| [本机源码启用方案（待批准，未执行）](2026-10-13-delegate-local-activation-plan.md) | 方案/预览 | — |
| [本机启用已完成：Codex新源码与Claude本地加载核验](2026-10-13-delegate-local-activation-result.md) | 结果/记录 | [2026-10-13-delegate-local-activation-result.json](2026-10-13-delegate-local-activation-result.json) |
| [S3完整替换接续通过：两宿主delegate已同步](2026-10-13-delegate-post-review-sync-complete-result.md) | 结果/记录 | [2026-10-13-delegate-post-review-sync-complete-result.json](2026-10-13-delegate-post-review-sync-complete-result.json) |
| [S3：仅同步本机两宿主的delegate（待安装授权）](2026-10-13-delegate-post-review-sync-plan.md) | 方案/预览 | — |
| [S3真实同步结果：失败停止，窄暂存修正待批准](2026-10-13-delegate-post-review-sync-result.md) | 结果/记录 | [2026-10-13-delegate-post-review-sync-result.json](2026-10-13-delegate-post-review-sync-result.json) |
| [S3修正接续：第二批失败，完整替换流程候选已准备](2026-10-13-delegate-post-review-sync-resume-result.md) | 结果/记录 | [2026-10-13-delegate-post-review-sync-resume-result.json](2026-10-13-delegate-post-review-sync-resume-result.json) |
| [剩余双向验收批次：双向普通审查完成，Claude入口待核验](2026-10-13-delegate-remaining-acceptance-plan.md) | 方案/预览 | — |
| [已批准剩余验收：双向有限审查完成，Claude入口待重载](2026-10-13-delegate-remaining-acceptance-result.md) | 结果/记录 | [2026-10-13-delegate-remaining-acceptance-result.json](2026-10-13-delegate-remaining-acceptance-result.json) |
| [剩余验收差距与下一最小批次预览](2026-10-13-delegate-remaining-gap-plan.md) | 方案/预览 | — |
| [路由修复：普通继续不再成为委托前置](2026-10-13-delegate-routing-host-fix.md) | 结果/记录 | [2026-10-13-delegate-routing-host-fix.json](2026-10-13-delegate-routing-host-fix.json) |
| [S1入口验收：正向未启动模型，停止；监督脚本路径缺陷已修复源码](2026-10-13-delegate-s1-result.md) | 结果/记录 | [2026-10-13-delegate-s1-result.json](2026-10-13-delegate-s1-result.json) |
| [S2预览：同步监督启动修复并补新入口双向验收](2026-10-13-delegate-s2-plan.md) | 方案/预览 | — |
| [S2恢复：依赖和边界通过，安装控制器失败后停止](2026-10-13-delegate-s2-recovery-result.md) | 结果/记录 | [2026-10-13-delegate-s2-recovery-result.json](2026-10-13-delegate-s2-recovery-result.json) |
| [S2：批准后前置核对未通过](2026-10-13-delegate-s2-result.md) | 结果/记录 | [2026-10-13-delegate-s2-result.json](2026-10-13-delegate-s2-result.json) |
| [S2修正接续：安装、新入口和正向真实审查通过](2026-10-13-delegate-s2-resume-result.md) | 结果/记录 | [2026-10-13-delegate-s2-resume-result.json](2026-10-13-delegate-s2-resume-result.json) |
| [修正后单次临时源码加载（待批准）](2026-10-13-delegate-source-load-fixed-plan.md) | 方案/预览 | — |
| [修正后临时源码加载：四入口转换产物通过](2026-10-13-delegate-source-load-fixed-result.md) | 结果/记录 | [2026-10-13-delegate-source-load-fixed-result.json](2026-10-13-delegate-source-load-fixed-result.json) |
| [Spec Guard 初始化与当前任务核对](2026-10-13-spec-guard-workflow-check.md) | 结果/记录 | [2026-10-13-spec-guard-workflow-check.json](2026-10-13-spec-guard-workflow-check.json) |

未对应单独说明页的数据：[2026-10-13-delegate-installed-preview-result.json](2026-10-13-delegate-installed-preview-result.json)、[2026-10-13-delegate-local-activation-preview.json](2026-10-13-delegate-local-activation-preview.json)、[2026-10-13-delegate-post-review-sync-preview.json](2026-10-13-delegate-post-review-sync-preview.json)、[2026-10-13-delegate-source-load-fixed-preview.json](2026-10-13-delegate-source-load-fixed-preview.json)。

## 分层验收与 S4–S7（2026-10-14）

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [剩余验收的分层取舍：已明确批准](2026-10-14-delegate-acceptance-decision.md) | 结果/记录 | — |
| [Task9l：Claude 错误终态安全诊断修复](2026-10-14-delegate-error-diagnostics-result.md) | 结果/记录 | [2026-10-14-delegate-error-diagnostics-result.json](2026-10-14-delegate-error-diagnostics-result.json) |
| [最终分层验收供审](2026-10-14-delegate-final-layered-review.md) | 结果/记录 | [2026-10-14-delegate-final-layered-review.json](2026-10-14-delegate-final-layered-review.json) |
| [分层验收修订执行结果](2026-10-14-delegate-layered-acceptance-result.md) | 结果/记录 | [2026-10-14-delegate-layered-acceptance-result.json](2026-10-14-delegate-layered-acceptance-result.json) |
| [剩余验收对齐与免费补证](2026-10-14-delegate-remaining-acceptance-feasibility.md) | 结果/记录 | [2026-10-14-delegate-remaining-acceptance-feasibility.json](2026-10-14-delegate-remaining-acceptance-feasibility.json) |
| [S4：单次真实读取拒权验收](2026-10-14-delegate-s4-read-boundary-plan.md) | 方案/预览 | — |
| [S4 单次真实读取拒权验收结果](2026-10-14-delegate-s4-read-boundary-result.md) | 结果/记录 | [2026-10-14-delegate-s4-read-boundary-result.json](2026-10-14-delegate-s4-read-boundary-result.json) |
| [S5：仅同步错误诊断修复](2026-10-14-delegate-s5-sync-plan.md) | 方案/预览 | — |
| [S5：诊断修复已同步两宿主](2026-10-14-delegate-s5-sync-result.md) | 结果/记录 | [2026-10-14-delegate-s5-sync-result.json](2026-10-14-delegate-s5-sync-result.json) |
| [S6 后续：零模型认证路径核对](2026-10-14-delegate-s6-auth-diagnosis.md) | 结果/记录 | [2026-10-14-delegate-s6-auth-diagnosis.json](2026-10-14-delegate-s6-auth-diagnosis.json) |
| [S6 诊断接续：一次真实读取边界调用](2026-10-14-delegate-s6-diagnostic-followup-plan.md) | 方案/预览 | [2026-10-14-delegate-s6-diagnostic-followup-plan.json](2026-10-14-delegate-s6-diagnostic-followup-plan.json) |
| [S6诊断接续结果：指定Read拒权子验收通过](2026-10-14-delegate-s6-diagnostic-followup-result.md) | 结果/记录 | [2026-10-14-delegate-s6-diagnostic-followup-result.json](2026-10-14-delegate-s6-diagnostic-followup-result.json) |
| [S6：诊断修复后的单次读取边界补证](2026-10-14-delegate-s6-read-boundary-plan.md) | 方案/预览 | — |
| [S6：一次真实读取边界验收未完成](2026-10-14-delegate-s6-read-boundary-result.md) | 结果/记录 | [2026-10-14-delegate-s6-read-boundary-result.json](2026-10-14-delegate-s6-read-boundary-result.json) |
| [S7：Claude菜单选择后的实际命令执行](2026-10-14-delegate-s7-menu-plan.md) | 方案/预览 | — |
| [S7：菜单实际执行的有限证据](2026-10-14-delegate-s7-menu-result.md) | 结果/记录 | [2026-10-14-delegate-s7-menu-result.json](2026-10-14-delegate-s7-menu-result.json) |
| [S7已有完整输出读回](2026-10-14-delegate-s7-output-readback-result.md) | 结果/记录 | [2026-10-14-delegate-s7-output-readback-result.json](2026-10-14-delegate-s7-output-readback-result.json) |
| [Task6：有限运行时启动诊断](2026-10-14-delegate-task6-runtime-timing-result.md) | 结果/记录 | [2026-10-14-delegate-task6-runtime-timing-result.json](2026-10-14-delegate-task6-runtime-timing-result.json) |
| [当前入口与 S4 前置核对](2026-10-14-delegate-ui-and-s4-preview.md) | 方案/预览 | — |
| [Task9n：标准工作区总验证恢复通过](2026-10-14-delegate-validator-discovery-result.md) | 结果/记录 | [2026-10-14-delegate-validator-discovery-result.json](2026-10-14-delegate-validator-discovery-result.json) |

## run 超时与写模式信任：S35–S36（2026-10-26）

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [run-timeout Checkpoint 3：付费实测 H1–H5](2026-10-26-delegate-run-timeout-cp3.md) | 结果/记录 | — |
| [S35 前置实测：中止后续跑与到期前收尾](2026-10-26-delegate-s35-timeout-probe.md) | 结果/记录 | [2026-10-26-delegate-s35-timeout-probe.py.txt](2026-10-26-delegate-s35-timeout-probe.py.txt) |
| [S36 补测：内联表覆盖的合并方式与 worktree 的信任键](2026-10-26-delegate-s36-trust-followup-probe.md) | 结果/记录 | [2026-10-26-delegate-s36-trust-followup-probe.py.txt](2026-10-26-delegate-s36-trust-followup-probe.py.txt) |
| [S36 调研：`--write` 运行能否不写入项目信任](2026-10-26-delegate-s36-trust-probe.md) | 结果/记录 | — |
| [S36 免费真机核验：write-trust 生成的覆盖能阻止写入](2026-10-26-delegate-s36-write-trust-check.md) | 结果/记录 | [2026-10-26-delegate-s36-write-trust-check.py.txt](2026-10-26-delegate-s36-write-trust-check.py.txt) |
| [S36 付费实测：真实 `--write` 不再改用户配置](2026-10-26-delegate-s36-write-trust-live.md) | 结果/记录 | — |

## 中止回收与接口 1.3：S38、S41（2026-10-27）

| 记录 | 类型 | 配套数据 |
|---|---|---|
| [S38 前置实测：`--json` 事件、续跑压缩、worktree 与长运行](2026-10-27-delegate-s38-probe.md) | 结果/记录 | [2026-10-27-delegate-s38-probe.py.txt](2026-10-27-delegate-s38-probe.py.txt)、[2026-10-27-delegate-s38-fake-responses.py.txt](2026-10-27-delegate-s38-fake-responses.py.txt)、[2026-10-27-delegate-s38-term-repro.sh.txt](2026-10-27-delegate-s38-term-repro.sh.txt) |
| [接口 1.3 合并实测（RU-07）](2026-10-27-delegate-1.3-merged-live.md) | 结果/记录 | — |
| [`--timeout` 超过 540 秒的真实运行（run-longrun 补测）](2026-10-27-delegate-timeout-longrun-live.md) | 结果/记录 | [2026-10-27-delegate-timeout-longrun-rehearsal.py.txt](2026-10-27-delegate-timeout-longrun-rehearsal.py.txt) |
