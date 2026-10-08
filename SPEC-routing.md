# 规格：routing（提议式执行器路由）

简体中文 | [English](docs/en/SPEC-routing.md)

当前合同：2026-10-08。依赖 detection 与 channel；历史 `tasks/routing/` 不替代本合同。

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

v0.4.0 的真实行为 eval 样本结果见 [验收记录](docs/releases/v0.4.0.md)。成功标准是确定性合同全绿、免费判决器拒绝假阳性、加载路径明确；“该提议时总会提议”仍未自动化验证。
