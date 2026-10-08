# 贡献指南

简体中文 | [English](CONTRIBUTING.en.md)

感谢你帮助改进 delegate。先阅读 [README](README.md)、[设计与边界](DESIGN.md)和涉及模块的[当前规格](docs/README.md)。历史任务记录用于理解背景，不覆盖当前合同。

## 报告问题与提出建议

先搜索 [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues) 中已有的问题。新问题请包含：

- Claude Code、Codex CLI、Python、Bash、操作系统和插件版本；
- 安装方式（远程 marketplace、本地路径或 `--plugin-dir`）；
- 最小复现步骤、预期行为、实际行为和退出状态；
- `/delegate:doctor` 的相关诊断及必要的日志片段；
- 写模式问题的 Git 状态，说明是否有原有未提交修改。

只提供复现所需的信息。提交前移除凭据、个人路径、业务源码和其他无关私密内容；不要上传 `auth.json`、API key、完整过程日志或缓存中的本机身份路径。

## 开发准备

安装依赖见 [README 前置条件](README.md#前置条件)。从本仓库根目录检查清单：

```bash
claude plugin validate .
claude plugin validate ./plugins/delegate
```

开发加载要在业务 Git 项目中显式使用源码插件目录：

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

不要以安装版本号相同推断源码内容已加载。远程缓存、本地路径和重载方式见 [更新与卸载](README.md#更新与卸载)。

## 项目 AI 与流程约定

开发前阅读 [开发流程与 AI 约定](docs/development-workflow.md)。Codex 使用项目 `AGENTS.md`，Claude Code 使用项目 `CLAUDE.md`；当前中文规格统一放在 `spec/`，模块计划/任务放在 `tasks/<id>/`。历史原文见 [归档索引](docs/archive/pre-spec-guard/README.md)，不能重新作为活动任务执行。

## 修改与验证

保持修改聚焦。行为变更先增加能够复现故障的回归，再修复实现；不要通过削弱断言让测试变绿。修改相关规格与帮助说明，避免文档和实际行为分离。

从**本仓库根目录**运行免费离线总验证：

```bash
/bin/bash scripts/validate.sh
```

总入口检查 JSON/Python/Bash 语法、可执行位、清单必填字段、判决器自检、全部 3 个 shell 产品套和 2 个 Python 回归套。基线为 52 条产品断言和 17 个 Python 回归；免费总入口不调用模型；doctor 的四个规则检查通过 run_doctor 显式使用本套受控 CLI、合成登录状态和临时日志，不继承外层安装/认证判据。[本轮实际验证](docs/verification/2026-10-08-f8-applied.md)在无外层 Codex 环境通过整个总套，且无 CLI/外层拒绝登录两种场景的探测套各 19 条通过。

需要定位失败时可单独运行：

```bash
/bin/bash plugins/delegate/tests/test-channel.sh
/bin/bash plugins/delegate/tests/test-detection.sh
/bin/bash plugins/delegate/tests/test-routing.sh
python3 -B plugins/delegate/tests/test-backend.py
python3 -B plugins/delegate/tests/test-channel-regressions.py
/bin/bash evals/propose-not-auto.sh --scaffold-only
/bin/bash evals/routing-fitness.sh --scaffold-only
```

免费桩只能验证确定性调用和进程合同，不能证明真实 CLI 沙箱或模型行为。以下命令**会调用模型并消耗额度**，不进入总验证，按明确的验证目的主动执行：

```bash
/bin/bash plugins/delegate/tests/test-channel.sh --live
/bin/bash evals/propose-not-auto.sh
/bin/bash evals/routing-fitness.sh
```

eval 显式用 `--plugin-dir` 加载源码；退出 0=PASS、1=FAIL、2=NORUN。routing-fitness 只接受首个非空行的完整“判断：委托”或“判断：自己做”。`claude -p` 单轮不能证明交互式“该提议时总会提议”，全局规则仍可能影响结果。更多细节见 [路由规格](spec/routing.md)。

保持 Bash 3.2 兼容：变量用 `${VAR}`，空数组用 `${ARR[@]+"${ARR[@]}"}` 守卫，不使用 `cmd | grep -q`。测试入口用 `/bin/bash`，避免 zsh 重定向行为影响结果。

## 双语文档维护

- `README.md` 和根目录设计/规格保持中文；`README.en.md`、`CONTRIBUTING.en.md` 和 `docs/en/` 提供英文对应页。
- 先修正中文事实和阅读路径，再同步英文。两版表达可以适应读者，但参数、默认值、退出状态、权限、失败语义和验证范围必须一致。
- 当前维护文档保留双向语言切换；英文导航默认链接英文对应页。源码和历史资料若只有中文或原始语言，应明确说明。
- 文档中的任务示例可以翻译，命令名、选项、环境变量、路径和需要精确匹配的诊断/判决字符串保持原样。
- 历史资料保留原事实和勾选状态，用归档说明指向当前合同；不要把旧设计重写成已经实现的新行为。

修改文档后检查文件链接、章节锚点和代码块，执行 `git diff --check`。双语覆盖表在 [文档索引](docs/README.md)。

## 提交 Pull Request

使用独立分支提交范围清晰的 PR。说明具体问题、修改后的行为或阅读路径，以及运行过的验证和限制。行为修改、文档同步与必要测试可以一起审查；避免混入无关重构。

提交前确认清单和相关验证通过，检查真实 diff。写模式委托无论成功或失败都可能留下修改，不能仅凭模型自述认定结果正确。

本项目采用 [MIT 许可证](LICENSE)。贡献时请确保所提交内容与该许可兼容，并保留第三方材料必要的版权及许可声明。
