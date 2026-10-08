# 开发流程与 AI 约定

简体中文 | [English](en/development-workflow.md)

本仓库于 2026-10-08 按确认范围接入 Spec Guard 本地多模块约定。产品运行不新增该插件依赖。
接入计划与任务见 [本轮记录](process/2026-10-08-adoption/plan.md)。历史批准不能由这次接入补证。

## 开发入口

- 中文能力图是 [`spec/CAPABILITY-MAP.md`](../spec/CAPABILITY-MAP.md)，模块合同在 `spec/<id>.md`。
- 当前计划与任务分别是 `tasks/<id>/plan.md`、`tasks/<id>/todo.md`。每个模块使用自己的文件，不建根目录 `SPEC-*.md` 或共享 `tasks/plan.md`。
- `.agent/state.json` 的 `activeModule` 是本地指针；空值按能力图构建顺序选下一项，不表示历史已批准。
- [AGENTS.md](../AGENTS.md) 提供 Codex 项目约定；[CLAUDE.md](../CLAUDE.md) 提供 Claude Code 项目约定并导入本页。本机全局配置不是仓库交付的一部分。
- 修改实现前阅读 [贡献指南](../CONTRIBUTING.md) 和相关规格；中文合同修改时同步英文对应页。Bash 保持 3.2 兼容，测试用 `/bin/bash`；Python 用 `-B`。

## 从需求到验收

1. 明确问题、范围、排除项、成功标准；新能力先评审能力图和模块规格。已有模块修复按现有范围处理。
2. 规格确认后写模块计划、任务和验证方法。计划的检查点标 `gate` 或 `report`；未标注按 `gate`。
3. `gate` 在交互会话中等待明确确认；`report` 把命令、结果和限制记入 todo 后继续。不能把文件存在当作批准。
4. 行为修复先证明回归测试能复现，再修复和复验；不削弱断言，不混入无关重构。
5. 验证后记录具体命令、结果、未验证项和证据位置；用户审阅实际 diff。远端交付另按已取得的具体授权执行。

Spec 覆盖目标、完整命令、目录职责、代码风格（真实示例）、测试策略和 Always/Ask first/Never 三级边界；成功条件与开放问题明确。标题可以中文表达，不能只迁移路径。
每个 task 写明描述、验收条件、验证步骤/命令、依赖、涉及文件和规模；通常拆到 1–5 个文件。Plan 说明顺序、风险与缓解、检查点及开放问题。维护任务验收和产品条款验收分别记录。
当前三模块的 [合同验证映射](verification/2026-10-08-contract-matrix.md) 将 CH/DET/RT 编号对应到实际测试和未验证项；这些编号是当前检索标识，不是历史批准证据。

非交互 `codex exec` 不等待人回复，只执行已经授权的范围；缺少授权的写入、付费或远端动作跳过并说明。
阶段确认以当前对话为准。记录可保存批准原话、日期、评审对象及基准，不能事后虚构旧批准。

## 验证

从仓库根目录运行免费验证：

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

Spec Guard 使用当前启用安装解析出的根目录运行 `phase-guard.sh` 和 `verify-artifacts.sh`，不硬编码缓存版本。
结构通过、阶段 `DONE`、桩测试通过分别描述文件布局、当前清单和确定性合同；都不证明历史批准、远端发布或真实模型的全部行为。
付费 live 验证、委托给其他执行器、Git 提交、推送和发布分别需要相应授权。本约定不提供这些授权。

## 历史与当前清单

八份接入前计划和任务按字节保存在 [历史索引](archive/pre-spec-guard/README.md)，带原路径、基准提交和 SHA-256。
`.md.txt` 保留原勾选和当时相对路径，不能直接当作当前导航或任务。历史文档设计仍保留原貌。
当前模块清单记录接入及内容补全的维护核对；历史未勾项、gate 批准和当时插件版本仍按证据分别判断，不一键转成完成。
[历史验证摘要](verification/2026-10-08-history.md) 区分原始本地证据与可随仓库阅读的摘要。

## 可选功能与事项

项目没有启用文档基线、Local 事项账本或能力历史账本。缺少这些可选文件不算违规，本轮不创建事项或迁移 tracker。
以后选择其中一项时，先按对应插件入口预览并确认；不能由 Git remote 或当前 `DONE` 推断事项后端及关闭状态。
