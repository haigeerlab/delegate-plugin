# 能力图：delegate

简体中文 | [English](../docs/en/capability-map.md)

## 目标

当前实现将已定方案的执行与查证交给 Codex CLI，隔离过程日志，并返回最终答复与写模式 Git 证据。独立 marketplace；产品运行不依赖 Spec Guard 或 agent-skills。

2026-10-09 已确认可选 Claude Code 只读审查后端，见 [claude-review](claude-review.md)。review/run、快捷范围与无模型预览已随 v0.5.0 发布，两宿主安装已核对。两方向真实审查已有成功记录，模块已按分层标准完成验收；主动模型越界和完整异常场景仍未验证，详见[版本说明](../docs/releases/v0.5.0.md)。

2026-10-08 按已确认的项目接入范围规范化文件布局。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。本次确认不追认早期模块的人工审批。

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| channel | 调用参数、只读/写沙箱、进程组期限与清理、日志隔离、Git 证据 | — |
| detection | CLI 基础检查、身份绑定缓存、原子写入、静默降级、doctor | — |
| routing | 显式委托请求的可选判据与确认纪律，不自动注入提醒 | channel, detection |
| claude-review | 为 delegate 增加显式后端选择、Claude Code 只读审查和统一审查结果，保持现有 Codex 行为兼容 | channel, detection, routing |
| integration-interface | 发布静态 interface.json 声明对外能力与接口版本，并把审查报告 schema_version 1 写成对外兼容合同 | claude-review |
| run-resume | 为 run 增加显式开启的可续跑模式：返回 runId 与结束状态 done/needs-input，并以 --resume 带用户答复续跑原 Codex 会话；接口升 1.1 只增字段 | channel, integration-interface |
| run-timeout | run 超时保留进度：所有 run 加提示词时间预算，可续跑 run 被中止后再续跑一轮只读收尾，取不到进度时走不靠模型的兜底；结束状态新增 timeout（退出 124），可续跑 run 超时后可 --resume；修 killpg EPERM；接口升 1.2 只增字段 | channel, integration-interface, run-resume |
| write-trust | --write 运行不再让 Codex 往用户 ~/.codex/config.toml 写项目信任：用户配置里没有本仓库信任条目时用 -c 内联表临时覆盖为 trusted，已有条目（含 untrusted）不动，读不准时不覆盖并提示 | channel, run-resume |
| run-result | run 改用 --json 调 Codex，每次写 JSON 结果文件（状态、命令与退出码、改动文件、标记原文、本次与整链 token、耗时），加 --strict 缺首行标记判 unmarked；会话 ID 改从 thread_id 取；接口升 1.3 只增字段 | channel, run-timeout |
| run-continue | --continue <runId> 在 done 之后接着派下一个 Task，只接受 --resumable 起头的链，沿用续跑的仓库、写模式、占位校验；链上状态与结果文件改按 14 天保留，不受 50 组日志清理挤掉 | run-resume, run-result |
| run-longrun | --timeout <秒> 只放大期限（541～7200），调用方用宿主后台模式调用，delegate 不托管后台进程；主运行、收尾轮与阈值沿用 run-timeout 公式，中止清理沿用 0.7.1 的后代进程组回收 | run-timeout, run-result |
| run-check | --check 在运行以 done 结束后按参数列表、不经 shell 执行使用方给的检查命令（运算符规则照抄 module-crew S30），结果写进结果文件；--authorized-by 记录事先写入授权的来源文件与 sha256，整链一致 | run-result |
| run-rules | --rules-file 把本次委托专用的规则片段原样放在 delegate 前言之后，冲突时以片段为准（安全边界除外），路径与 sha256 写进结果文件；不读也不拼 AGENTS.md | run-result |

Build order: channel → detection → routing → claude-review → integration-interface → run-resume → run-timeout → write-trust → run-result → run-continue → run-longrun → run-check → run-rules

channel 与 detection 共用 `backend.py`，该共享代码不是独立模块依赖。routing 按显式请求结合 detection 体检，授权后使用 channel；构建顺序保留既有实施顺序，不新增运行职责。

```text
backend.py → codex-exec.sh → run_codex.py → codex exec
     ↓
detect.py ← detect.sh / doctor.sh
     ↓ detection.json → doctor
explicit request → delegate-routing skill → review/run
```

- channel 不决定“什么任务该派”，且每次实时复查基础认证。
- detection 不发模型请求；只检查本地条件，不保证远端/额度。
- routing 不调用 Codex，不做关键词分类；决策交给模型解释，授权交给用户。
- 移除 routing 后，channel 仍能手动调用；共用 backend 不依赖 hook 缓存。
- doctor 属于 detection，按需刷新与检查中文全局规则，临时缓存写入不触及业务项目。
- 写模式不要求干净工作区；原有修改数量和 staged/unstaged 统计必须可见，不能自动回滚。
- 默认只读、写入须当前轮明确授权；命令指令的确认纪律不能被当作不可绕过技术锁。

既有合同与验证详见 [channel](channel.md)、[detection](detection.md)、[routing](routing.md)；新增模块按 [claude-review](claude-review.md) 单独追踪。不新增非 Git 支持、后台编排、提交/推送/发布或自动升级安装缓存。
