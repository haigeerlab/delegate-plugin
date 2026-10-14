# 双后端命令接口调整与验证

日期：2026-10-10。开发仓库 delegate-plugin，分支 codex/spec-guard-conventions-public；用户在审阅设计后回复“继续”，确认本批实施。计划见 [claude-review plan](../../tasks/claude-review/plan.md)，精确合同见 [spec](../../spec/claude-review.md)，摘要/源码哈希见 [JSON 证据](2026-10-10-delegate-interface.json)。未提交、安装或发布。

## 结果与迁移

- 源斜杠命令整理为 review/run/doctor/help，原 delegate 命令移除。Codex 宿主从同一来源定义使用公共入口，具体显示名称仍以加载的命令/技能列表为准；没有修改生成缓存。
- review 两后端都只读；run 保留旧 Codex 通用任务和显式 write，Claude run 拒绝。默认后端仍 codex，模型另选，无 fallback。
- 常用路径/模块/diff/排除/Spec/Plan/验收参数生成原严格上下文；高级 context JSON 保留。无 paths 的 diff 只选该比较的变更文件，不扫描全项目。
- paths/module 默认读取 HEAD，未提交内容须显式 changes；include-untracked 仅 working-tree。空主范围不能被 Spec/Plan 掩盖，部分路径缺失列入采集缺口，不当作全部审完。
- dry-run 输出 kind=review_preview，仅范围、摘要、缺口、权限和请求限制；不输出源码/diff正文，不调用后端/模型、不检查认证、不创建审查产物。
- 共享双后端能力用于帮助、doctor 和选项验证，未引入注册框架或第三后端。清单和中英文使用/合同/迁移说明同步。

```text
/delegate:review --backend claude-code --paths src/payments --model sonnet
/delegate:review --backend codex --base main --head HEAD
/delegate:review --paths src/payments --module payments --spec spec/payments.md --plan tasks/payments/plan.md --dry-run
/delegate:run --write 按已确认方案修复并测试
```

上例是未发布源命令；安装 v0.4.0 仍是旧命令。旧 codex-exec.sh 和 delegate-exec.sh 无子命令调用继续有效；终端新入口为 delegate-exec.sh review|run。run/review 成为保留子命令名，原任务仅为这两个单词时用 `run -- run` / `run -- review` 或旧脚本 `--` 明确任务。建议下一发行 0.5.0，版本与发行须在实际交付步骤处理。

## 已运行验证

1. 新命令/能力测试先红后绿；CLI 13 项覆盖兼容 run、禁用 Claude run、参数混用、明确范围、固定/工作区 diff、HEAD 默认、排除、上下文等价、预览隐私、空主范围及部分缺失路径。新快捷参数实际经过公共 Codex wrapper→固定假 Codex，得到严格共同报告。
2. Claude 新 review 快捷入口→适配器→固定假 Claude 的端到端测试通过，确认不启动 Codex；该适配器测试使用假原生边界，不冒称 OS 验收。
3. 实际 macOS 公共 review --context→srt→固定假 Claude 批次：6 项/8 场景，31.619 秒，退出0；覆盖拒写、长 TMPDIR、空/坏结果、拒权、未知工具、超时、取消和本次进程回收。无真实模型。
4. 免费总入口 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：退出0，53 shell、137 Python、19 eval。最初工具沙箱限制 /bin/ps，未修改测试/跳过断言；在允许精确检查测试 helper 的环境中通过。
5. 两项原生 plugin validate 退出0。当前启用 Spec Guard 动态定位后 phase-guard/verify-artifacts 退出0，BUILDING、5 未勾，产物3/0/0。文档和 diff 检查单独记录，不冒充真实宿主验收。

输入条件异常捕获限制在后端启动之前，避免后端未知异常被包装成“未启动/条件不足”。反向输入、禁用功能核验、stderr 摘要及假报告合同修复后，再完整运行免费总套：137 Python 全部通过。43 Python AST、612 个本地链接及 git diff --check 通过。未修改原生权限或清理逻辑。

## 未验证与下一步

新版源斜杠命令未实际加载到两种宿主，修复后的真实反向成功审查和主动模型越界仍未完成。此前正向真实成功属于先前源码，不能替新版接口作证；只读审查不保证模型全部观点正确。

本批修改使旧反向临时夹具的源码摘要失效；不能自动追认旧预览或从当前 Codex 发起替代反向测试。下一步先准备与当前接口一致的固定预览，再分别处理源码加载和有限真实宿主验收的具体授权。输入/宿主变化、权限不足、失败或结果未知即停，不重试或扩大范围。发布、安装、提交、推送仍未执行。

## 真实反向首批失败与输入修复

收束时发现原反向夹具 marker/result 已生成，精确关联回复证明目标取得人类直接批准后，从真实 Claude 主会话单次启动 Codex；该运行发生在本批接口源码修改前。退出1、16.988秒、failed/inconclusive，四文件全部未审：Codex 无获准的 Read 工具且遵守禁止命令的要求。用量已报告、实际模型未知。输入与 Git 未变，进程组回收确认；这不是“未运行”，也不是“没有问题”。详见[实际反向证据](2026-10-10-claude-review-mac-reverse-first.json)。

已免费修复：Codex 直接接收校验后的文件内容、路径及摘要，作为不可信 JSON 数据，序列化输入限制1MiB；超限不调用 CLI 或模型。启动前核实四项工具功能关闭，禁用搜索/清空 MCP，保留原只读沙箱。新增两个真实 wrapper 假 CLI 回归覆盖输入上限及功能禁用核验，原成功回归断言文件正文确实传入。共同 stderr 摘要现在区分实际启动、覆盖和用量是否已报告。原生路由测试的固定假报告补齐现有合同字段；未削弱权限或清理断言。

旧预览/marker/报告保持一次运行历史，不能重跑或自动更新批准。修复后的真实反向成功结果尚未取得，新版斜杠命令也尚未加载；下一步准备当前源码的无模型预览，新增付费调用和加载仍按具体授权处理。

当前源码无模型反向预览已生成：[预览 JSON](2026-10-10-claude-review-mac-reverse-current-preview.json)。仍为原四个合成文件，共4,821字节，inline_files、backend_started=false，上限1,048,576字节；不启动后端、不检查认证、不产生新执行报告。尚未创建新单次驱动，也没有取得新增模型调用授权；旧驱动已消费，不可使用。
