# 能力图：delegate

简体中文 | [English](../docs/en/capability-map.md)

## 目标

将已定方案的执行与查证交给 Codex CLI，隔离过程日志，并返回最终答复与写模式 Git 证据。独立 marketplace，只支持 Codex CLI；产品运行不依赖 Spec Guard 或 agent-skills。

2026-10-08 按已确认的项目接入范围规范化文件布局。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。本次确认不追认早期模块的人工审批。

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| channel | 调用参数、只读/写沙箱、进程组期限与清理、日志隔离、Git 证据 | — |
| detection | CLI 基础检查、身份绑定缓存、原子写入、静默降级、doctor | — |
| routing | 注入事实与确认要求，skill 提供任务判据 | channel, detection |

Build order: channel → detection → routing

channel 与 detection 共用 `backend.py`，该共享代码不是独立模块依赖。routing 消费 detection 缓存，确认后使用 channel；构建顺序保留既有实施顺序，不新增运行职责。

```text
backend.py → codex-exec.sh → run_codex.py → codex exec
     ↓
detect.py ← detect.sh / doctor.sh
     ↓ detection.json
prompt.sh: detect.sh --warm → route.sh → delegate-routing skill
```

- channel 不决定“什么任务该派”，且每次实时复查基础认证。
- detection 不发模型请求；只检查本地条件，不保证远端/额度。
- routing 不调用 Codex，不做关键词分类；决策交给模型解释，授权交给用户。
- 移除 routing 后，channel 仍能手动调用；共用 backend 不依赖 hook 缓存。
- doctor 属于 detection，按需刷新与检查中文全局规则，临时缓存写入不触及业务项目。
- 写模式不要求干净工作区；原有修改数量和 staged/unstaged 统计必须可见，不能自动回滚。
- 默认只读、写入须当前轮明确授权；命令指令的确认纪律不能被当作不可绕过技术锁。

合同与验证详见 [channel](channel.md)、[detection](detection.md)、[routing](routing.md)。没有新增后端、非 Git 支持、后台任务、提交/推送/发布或自动升级安装缓存。
