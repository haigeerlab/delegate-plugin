---
name: Bug 报告 / Bug report
about: 插件异常、报错或行为与文档不符 / Plugin failure, error, or behavior that differs from the documentation
labels: bug
---

<!--
提交前请先搜索已有 Issue，并移除凭据、个人路径和业务源码；不要上传 auth.json、API key 或完整过程日志。
安全问题请勿在此提交，见 SECURITY.md。
Search existing issues first. Do not report security problems here; see SECURITY.md. Remove credentials, personal paths, and business source code; never upload auth.json, API keys, or full process logs.
-->

**环境 / Environment**
<!-- 操作系统、插件、Claude Code、Codex CLI、Python、Bash 版本；使用 Claude 后端时补充 Node 与 srt 版本 -->
<!-- OS, plugin, Claude Code, Codex CLI, Python, and Bash versions; add Node and srt versions for the Claude backend -->

**安装方式 / Installation**
<!-- 远程 marketplace / 本地路径 / --plugin-dir -->

**运行的命令 / Command**
<!-- 例如 /delegate:review --backend claude-code --paths src；注明只读或 --write -->

**复现步骤 / Steps to reproduce**

1.
2.

**预期结果 / Expected**

**实际结果 / Actual**
<!-- 是否每次都能复现 / Does it happen every time? -->

**退出状态与错误 / Exit status and error**

**`/delegate:doctor` 相关输出 / Relevant doctor output**
<!-- Claude 后端请用 /delegate:doctor --backend claude-code -->

**若涉及写入 / If --write was used**
<!-- Git 状态、是否有原有修改、失败后留下了哪些修改 / Git status, pre-existing changes, changes left after failure -->
