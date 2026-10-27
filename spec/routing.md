# 规格：routing（提议式执行器路由）

简体中文 | [English](../docs/en/SPEC-routing.md)


取消每轮 UserPromptSubmit 自动路由提醒；Codex 基础可用缓存不代表宿主、委托意图或 Claude 可用。用户明确请求委托时，命令/skill 区分宿主与后端：默认 Codex，显式 Claude 仅固定范围只读审查；不自动选相反宿主、不混模型/参数、不 fallback，详情见 [claude-review](claude-review.md)。显式委托和写权限确认纪律保留，同一范围已有授权不重复确认。

接口 1.3 起，写入授权有一个例外：满足 [run-check](run-check.md) 所列四个条件、并带 `--authorized-by <文件>` 时，视为本轮已授权；纪律写在插件的 `references/run.md`，`delegate-routing` skill 有一句指向。其余写入规则不变。

当前合同：2026-10-13（路由提醒修复）；2026-10-08条款与样本保留历史适用范围。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。当前 `tasks/routing/` 跟踪维护核对和本次修复，不追认历史验收，也不覆盖本规格。


## 技术栈与命令

Bash 3.2、Python 3 标准库、Claude Code hook/skill；检测及通道分别提供事实与执行。判决器的付费样本需要 Claude CLI；免费自检使用桩。
本产品为脚本插件，无独立编译构建或 dev server。下方原合同列出模块测试；仓库统一验证/开发加载如下，加载命令只启动宿主，不自行委托。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
claude --plugin-dir "$PWD/plugins/delegate"
```

## 项目结构

路径均相对仓库根；插件内相对路径在原合同中说明。

```text
plugins/delegate/hooks/prompt.sh            → 退役 Hook 的静默兼容入口
plugins/delegate/hooks/route.sh             → 退役自动路由提示的静默兼容入口
plugins/delegate/hooks/hooks.json           → 事件注册
plugins/delegate/skills/delegate-routing/SKILL.md → 六类分流及确认纪律
plugins/delegate/commands/                  → review / run / doctor / help
plugins/delegate/tests/test-routing.sh      → Shell 桩断言
plugins/delegate/tests/test-backend.py      → Python unittest 冷缓存/handler 回归
evals/                                    → 判决器自检与按需付费样本
spec/routing.md                            → 当前中文合同
docs/en/SPEC-routing.md                    → 当前英文合同
tasks/routing/plan.md / todo.md            → 当前维护步骤与记录
```

## 代码风格

保持已有风格，不做格式重构。Bash 兼容 3.2，变量用 `${VAR}`、数组展开按已有空数组守卫，不使用 `cmd | grep -q`；Python 使用标准库、4 空格缩进、snake_case 函数名，JSON 通过序列化器生成，不手工拼转义。
以下为 `plugins/delegate/hooks/route.sh` 的现有片段，展示实际写法（上下文片段，不是新命令）：

```bash
# Compatibility no-op for callers of the retired per-prompt routing hook.
# Commands and delegate-routing handle explicit requests without guessing a host.
exit 0
```

## 开发边界

- **Always：** 修改前阅读合同；行为修复先复现再复验；保持 Bash 3.2 和双语合同同步；检查实际 diff 和相关测试。
- **Ask first：** 新后端/依赖/flag、沙箱默认或认证方法变更、超出现有模块的能力；付费 live、委托、提交和远端写入取得各自授权。
- **Never：** 暴露凭据/完整私密日志；削弱失败断言；自动回滚用户修改；追认历史审批或擅改归档；把桩结果当作完整宿主行为保证。

## 测试策略

Shell 产品套使用 `stub-codex` 和临时夹具；Python 回归使用标准库 `unittest`。测试位置见项目结构，原合同保留精确命令和断言范围。未设行覆盖率百分比，不虚构阈值。
验证按条款和风险判断，包含正反场景；源码中的保证若没有独立断言，映射明确标“部分覆盖”。真实模型、权限与交互验证单列，未经授权不运行付费样本。

## 目标

仅在用户明确请求委托、分流、独立审查或执行器选择时使用路由判据。决策已定不等于必须委托；普通“继续”推进已授权工作，不先要求额外委托确认。模型提出新委托时等待明确肯定；直接委托命令和同一范围已有批准可直接执行，写权限仍须用户明确授予。

这是命令与 skill 的行为指令，不是 wrapper 不可绕过的授权锁。宿主仅按主会话可靠上下文判断，不能由 Codex 可用缓存或可继承的环境猜测；未知不作自动方向提示。Claude→Codex、Codex→Claude按显式目标选择，后端基础条件由对应doctor报告，不自动换后端。显式要求同宿主独立Codex审查仍允许。

## 实现

hooks.json不再注册UserPromptSubmit；SessionStart继续静默刷新Codex基础缓存。prompt.sh与route.sh保留为无探测、无注入、退出0的兼容入口，防止旧注册引用新源码时恢复每轮提醒。无需关键词分类、宿主猜测、session去重状态或新配置；基础事实与委托决策分开。

`skills/delegate-routing/SKILL.md` 提供六类分流与返回后的纪律。`/delegate:review` 执行两个后端的只读审查，`/delegate:run` 执行既有 Codex 任务，`/delegate:doctor` 按后端体检，`/delegate:help` 读取无模型本地帮助；宿主支持时 skill 自身可见为 `/delegate:delegate-routing`。

## 分流与验收

代码审查、跨文件结构、复现定位可只读；单个明确 task 与批量机械修改需授权写模式；需求澄清、架构取舍、结果验收和微小修改留主会话。只读沙箱会限制需要写缓存/文件的测试，必要时用户另行授权写入。

任务不扩展范围。成功后看最终答复，写模式看实际 Git diff 与测试；失败后仍看 Git 证据，不能假定没有修改。日志按路径读取相关少量行，避免全文重新灌入上下文。Bash timeout=600000，与 channel 540 秒执行期限协调。

## 确定性验证

以下验证与评估命令从本仓库根目录运行：

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-routing.sh
python3 -B plugins/delegate/tests/test-backend.py
```

10条shell断言覆盖所有缓存状态零注入、不重探、显式确认措辞与skill/命令判据。backend回归覆盖冷缓存无探测/输出、无UserPromptSubmit注册，Claude/Codex/未知/冲突环境×5种提示×2个兼容入口×2次重复共80次调用均静默；显式Codex run在两种环境桩中仍各启动一次Codex。环境夹具不是原生宿主验收。

## 行为评估与限制

```bash
/bin/bash evals/propose-not-auto.sh --scaffold-only
/bin/bash evals/routing-fitness.sh --scaffold-only
# 以下会消耗模型额度
/bin/bash evals/propose-not-auto.sh
/bin/bash evals/routing-fitness.sh
```

_preflight 检查 CLI 可运行、当前插件源目录原生清单校验；eval 用 `claude --plugin-dir <当前源目录>`，不以已安装版本号代替内容加载验证。脚手架给临时桩 CLI、Git 项目和符合当前 identity 的缓存。

退出 0=PASS，1=FAIL，2=NORUN。无有效产出/工具故障不记产品失败。

- propose-not-auto 的硬判据是没有自动调用 exec；是否主动提议仅为观察项。`claude -p` 单轮无法证明互动时的提议行为。
- routing-fitness 比较决策已定的批量任务与尚需架构选择的任务，只解析第一个非空行的完整“判断：委托/自己做”。条件句、前缀或正文示例不算判决，返回 NORUN。
- 用户全局规则与已安装环境可能仍影响模型；显式加载源码不等于完全隔离评估。

v0.4.0 的真实行为 eval 样本结果见 [验收记录](../docs/releases/v0.4.0.md)。成功标准是确定性合同全绿、免费判决器拒绝假阳性、加载路径明确；“该提议时总会提议”仍未自动化验证。

## 成功条件与验证映射

以下编号于 2026-10-08 为既有合同添加检索标识，不是历史编号或批准记录。

- **RT-01：** 不注册UserPromptSubmit；退役prompt/route所有宿主、输入、缓存及重复调用均无探测/无输出；SessionStart仍静默刷新基础条件。
- **RT-02：** skill只对显式委托请求使用提议与确认纪律，不自动执行；已批准范围不重复确认，不由基础可用/决策已定强制委托；写权限不升级。文本和桩不证明完整宿主行为。
- **RT-03：** 六类分流、范围限制及返回后的答复/Git 复核要求可读、与通道参数一致。
- **RT-04：** eval 判决器区分 PASS/FAIL/NORUN，拒绝假阳性；单轮样本不代表完整交互提议行为。

精确测试、实现位置和覆盖缺口见 [条款到证据映射](../docs/verification/2026-10-08-contract-matrix.md)。当前维护计划 Task 5 负责核对该映射，不宣告全部产品条款已经充分验收。

## 开放问题

历史任务逐项验收、旧审批/插件版本及完整交互宿主行为仍未核实。当前已知覆盖缺口列在映射中；此处不新增能力或更强保证。
