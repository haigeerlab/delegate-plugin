# delegate 开发约定

- 先读 `docs/development-workflow.md`、`CONTRIBUTING.md` 和涉及模块的 `spec/<id>.md`。
- 当前中文合同在 `spec/`，英文对应页在 `docs/en/`；行为或合同修改须同步两版。
- 保持 Bash 3.2 兼容；用 `/bin/bash` 执行 shell 测试，Python 用 `-B` 避免向源码目录写缓存。
- 免费总验证：`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`。需要原生清单核验时运行 `claude plugin validate .` 和 `claude plugin validate ./plugins/delegate`。
- 付费 live 验证、委托给其他执行器、提交、推送及发布分别需要相应授权；当前约定不提供这些授权。
- 归档 `.md.txt` 是原始证据，不是当前任务；不要修改其内容或追认旧勾选。`DONE` 不代表历史人工批准或远端交付。
- 交互式阶段按下方约定确认；非交互 `codex exec` 不等待人回复，只完成已授权范围，缺少授权的动作跳过并报告。

## 提交信息与 PR 语言

- 本项目的提交信息、PR 标题和 PR 描述一律用中文，写清楚改了什么、为什么改，不能全英文。
- 文件路径、命令、代码标识符（函数名、变量名、配置项）和 `fix:`、`feat:`、`docs:`、`chore:` 等前缀保持原样，不翻译。
- 末尾自动附加的署名行（如 `Co-Authored-By`、`Signed-off-by`）保持原样。
- 代码和代码注释仍按仓库原有语言，不因本规则改动。
- 已有的英文提交历史不改。
- 例外：给不归本团队的外部开源项目提 PR 时，须先询问用户，再跟随对方仓库的语言。

<!-- BEGIN:spec-guard-codex-convention -->
## Spec Guard 项目约定

> 由 `setup-convention local --host=codex` 生成。

- 能力图：`spec/CAPABILITY-MAP.md`；模块 spec：`spec/<module-id>.md`
- 每个模块隔离使用 `tasks/<module-id>/plan.md` 和 `tasks/<module-id>/todo.md`
- 活跃模块在 `.agent/state.json` 的 `activeModule`；不要共用 `tasks/plan.md`
- 若项目已启用 Local 事项账本，确认要实现的需求或修复在动代码前先用 `spec-guard:ticket`
  查重并取得事项 ID；探索和无需追踪的小操作例外
- 项目级审查按 `spec-guard:spec-guard-ops` 的共享检查点规则限定批次、收束发现并交接缺陷；
  审查完成后的“继续”推进已预告的问题处理步骤，不重新泛扫
- 明确选用 GitHub/GitLab 普通 Issue 时，用 `spec-guard:hosted-ticket-workflow` 逐项查重、授权写入与交付对账；
  Local 事项仍走 `spec-guard:ticket`，不凭 Git remote 改目标
- 阶段交接或停止时，加载 `spec-guard:spec-guard-ops` 的共享检查点规则，预告已授权下一步。
- Plan 的检查点标 `gate`（停下等确认）或 `report`（记入 todo 后继续），未标注按 `gate`；按需求批量前置审与
  UI 自验按 `spec-guard:spec-guard-ops` 的共享检查点规则
<!-- END:spec-guard-codex-convention -->
