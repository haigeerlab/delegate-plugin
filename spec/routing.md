# 规格：routing（提议式执行器路由）

简体中文 | [English](../docs/en/SPEC-routing.md)

当前合同：2026-10-08。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。当前 `tasks/routing/` 只跟踪维护核对，不追认历史验收，也不覆盖本规格。


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
plugins/delegate/hooks/prompt.sh            → warm 后 route 的串行 handler
plugins/delegate/hooks/route.sh             → 有效缓存的单行 JSON 指针
plugins/delegate/hooks/hooks.json           → 事件注册
plugins/delegate/skills/delegate-routing/SKILL.md → 六类分流及确认纪律
plugins/delegate/commands/                  → delegate / doctor / help
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

```python
    cache = read_cache()
    if cache and cache['available']:
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'UserPromptSubmit',
                'additionalContext': 'delegate: Codex 基础条件可用（未验证远端连接或额度）。若这一步的决策已经定完、只剩执行与查证，先说明要委托什么、等用户确认后再调；判据见 delegate-routing skill。',
            },
        }, ensure_ascii=False))
```

## 开发边界

- **Always：** 修改前阅读合同；行为修复先复现再复验；保持 Bash 3.2 和双语合同同步；检查实际 diff 和相关测试。
- **Ask first：** 新后端/依赖/flag、沙箱默认或认证方法变更、超出现有模块的能力；付费 live、委托、提交和远端写入取得各自授权。
- **Never：** 暴露凭据/完整私密日志；削弱失败断言；自动回滚用户修改；追认历史审批或擅改归档；把桩结果当作完整宿主行为保证。

## 测试策略

Shell 产品套使用 `stub-codex` 和临时夹具；Python 回归使用标准库 `unittest`。测试位置见项目结构，原合同保留精确命令和断言范围。未设行覆盖率百分比，不虚构阈值。
验证按条款和风险判断，包含正反场景；源码中的保证若没有独立断言，映射明确标“部分覆盖”。真实模型、权限与交互验证单列，未经授权不运行付费样本。

## 目标

在任务决策已定时让模型考虑委托，由用户决定是否执行。模型只提议，等明确肯定；写模式须当前轮明确授权。用户直接输入明确委托命令是当前任务授权。

这是命令与 skill 的行为指令，不是 wrapper 不可绕过的授权锁。hook 不做任务分类，不按关键词判断，不发起 Codex。

## 实现

UserPromptSubmit 仅注册一个 `prompt.sh` handler：先 `detect.sh --warm`，再 `route.sh`。宿主可并行同事件 handler，所以不依赖两个独立 handler 的顺序。

`route.sh` 读取 detection 共用的有效缓存合同；可用时输出单行合法 JSON：本地基础条件、等待确认要求、delegate-routing skill 指针。缺失、过期、身份变化、损坏或不可用缓存时零输出/退出 0，不重新探测。

`skills/delegate-routing/SKILL.md` 提供六类分流与返回后的纪律。主命令 `/delegate:delegate` 执行，`/delegate:doctor` 刷新，`/delegate:help` 静态帮助；宿主支持时 skill 自身可见为 `/delegate:delegate-routing`。

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

9 条原有断言覆盖不可用/缺失/过期/损坏缓存、单行 JSON、不重探、确认措辞与 skill 判据。新增 backend 测试验证冷缓存同一轮输出、仅一个串行 handler。

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

- **RT-01：** 只注册一个 prompt handler，先 warm 再 route；有效缓存才输出单行合法 JSON，route 不重探。
- **RT-02：** hook/skill 保持提议与明确确认纪律，不自动执行；文本和桩测试不能证明宿主始终遵守。
- **RT-03：** 六类分流、范围限制及返回后的答复/Git 复核要求可读、与通道参数一致。
- **RT-04：** eval 判决器区分 PASS/FAIL/NORUN，拒绝假阳性；单轮样本不代表完整交互提议行为。

精确测试、实现位置和覆盖缺口见 [条款到证据映射](../docs/verification/2026-10-08-contract-matrix.md)。当前维护计划 Task 5 负责核对该映射，不宣告全部产品条款已经充分验收。

## 开放问题

历史任务逐项验收、旧审批/插件版本及完整交互宿主行为仍未核实。当前已知覆盖缺口列在映射中；此处不新增能力或更强保证。
