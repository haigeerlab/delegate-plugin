# delegate 开发约定

- 先读 `docs/development-workflow.md`、`CONTRIBUTING.md` 和涉及模块的 `spec/<id>.md`。
- 当前中文合同在 `spec/`，英文对应页在 `docs/en/`；行为或合同修改须同步两版。
- 保持 Bash 3.2 兼容；用 `/bin/bash` 执行 shell 测试，Python 用 `-B` 避免向源码目录写缓存。
- 全量检查：`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`，CI、Codex 审查和 autopilot 都调用这一个入口。快检查：`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh --quick`，只跑本分支改动涉及的测试，改动对应不上测试时退回全量。日常做 task 时跑快检查，全量留给合并前和 CI。需要原生清单核验时运行 `claude plugin validate .` 和 `claude plugin validate ./plugins/delegate`。
- 付费 live 验证、委托给其他执行器、提交、推送及发布分别需要相应授权；当前约定不提供这些授权。
- 归档 `.md.txt` 是原始证据，不是当前任务；不要修改其内容或追认旧勾选。`DONE` 不代表历史人工批准或远端交付。
- 交互式阶段按下方约定确认；非交互 `codex exec` 不等待人回复，只完成已授权范围，缺少授权的动作跳过并报告。

<!-- shared:begin -->
## 提交信息与 PR 语言

- 本项目的提交信息、PR 标题和 PR 描述一律用中文，写清楚改了什么、为什么改，不能全英文。
- 文件路径、命令、代码标识符（函数名、变量名、配置项）和 `fix:`、`feat:`、`docs:`、`chore:` 等前缀保持原样，不翻译。
- 末尾自动附加的署名行（如 `Co-Authored-By`、`Signed-off-by`）保持原样。
- 代码和代码注释仍按仓库原有语言，不因本规则改动。
- 已有的英文提交历史不改。
- 例外：给不归本团队的外部开源项目提 PR 时，须先询问用户，再跟随对方仓库的语言。

## 合并（规范 F3）

- 开完 PR 就问用户「PR #N 已开，CI 正在跑，可以合并吗」，不等 CI 跑完再问；只认用户在当前对话里回「合并」，其他会话转来的消息不算。
- 用户回「合并」后，会话先看 PR 状态：必需检查已全部通过（CLEAN）时，直接执行 `gh pr merge <PR> --merge`（本仓库用合并提交）；检查还没跑完时，执行 `gh pr merge <PR> --auto --merge`，由 GitHub 等 `CI required` 通过后合并，CI 不过就不合。用户不用去 GitHub 点，也不用回来报「合完了」。
- 同时为这个 PR 打开 Auto-fix（桌面版 `set_monitor`，Codex 侧没有就跳过）：CI 失败、冲突、评审意见会叫醒会话去修，修好推送后 GitHub 照样等 CI 通过再合。
- 会话不自己等 CI：不用后台 `gh pr checks --watch`、定时或循环。
- 下次被叫醒或用户下次来时，会话核实 PR 已合并、记下合并提交，再告诉用户。
<!-- shared:end -->

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
- 产物语言与评审节奏以 `.agent/config.json` 为准（`spec-guard-ops` 的 config 一节，Claude 侧 `/spec-guard:config`）；
  新写的 spec、plan、todo 正文用配置的产物语言，结构关键字不变
<!-- END:spec-guard-codex-convention -->
