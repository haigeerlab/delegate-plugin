---
description: Codex 委托接入体检
allowed-tools: Bash
---

直接运行：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/doctor.sh"
```

每次强制刷新本地基础探测，并写临时缓存，不修改业务文件。退出 0 表示诊断完成，以文本的问题数量为准。它不验证远端连接、额度、模型权限或所有规则；全局 AGENTS.md 检查仅为中文启发式。
