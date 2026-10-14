---
description: delegate 所选后端的无模型接入体检
argument-hint: "[--backend codex|claude-code]"
allowed-tools: Bash
---

按用户选定后端运行，默认 Codex；先展示共享能力定义，再检查条件，能力说明不代表已可用：

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/review_doctor.py" [--backend codex|claude-code]
```

Codex 路径保留原 `hooks/doctor.sh`：刷新本地基础探测和临时缓存，检查部分中文全局 AGENTS.md 规则，不修改业务文件。
Claude 路径在本机 Mac 的同一只读边界检查已有 srt/Node、CLI 版本/参数及原有认证；不调用 Codex或模型、不安装、不登录、不改全局设置。仅保留安全认证方法/提供商，模型、额度、实际审查工具及双向宿主仍未验证。
退出 0 表示诊断完成，以文本的问题数量和未验证项为准；不代表远端、额度、模型权限或完整审查可用。
