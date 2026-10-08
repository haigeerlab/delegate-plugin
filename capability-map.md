# 能力图：delegate

简体中文 | [English](docs/en/capability-map.md)

2026-10-08 修复合同，依据用户确认的范围；早期任务记录保留为历史证据。
独立 marketplace，只支持 Codex CLI，不依赖 spec-guard 或 agent-skills。

| 模块 | 职责 | 依赖 |
|---|---|---|
| channel | 调用参数、只读/写沙箱、进程组期限与清理、日志隔离、Git 证据 | 共用 backend 基础检查 |
| detection | CLI 基础检查、身份绑定缓存、原子写入、静默降级、doctor | 共用 backend 基础检查 |
| routing | 注入事实与确认要求，skill 提供任务判据 | detection 缓存；确认后通过 channel 执行 |

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

合同与验证详见 [channel](SPEC-channel.md)、[detection](SPEC-detection.md)、[routing](SPEC-routing.md)。没有新增后端、非 Git 支持、后台任务、提交/推送/发布或自动升级安装缓存。
