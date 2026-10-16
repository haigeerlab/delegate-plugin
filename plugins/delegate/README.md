# delegate 插件

简体中文 | [English](README.en.md)

本目录是 delegate 插件本体，也是安装后缓存里的内容。完整的安装、参数、验收与故障排查说明见仓库 [README](https://github.com/haigeerlab/delegate-plugin#readme)。

delegate 把范围明确的只读审查交给 Codex 或 Claude Code，把已定方案的通用任务交给 Codex。后端用 `--backend` 显式选择，默认 Codex；插件只在用户明确请求或确认后执行，不自动派活。

## 命令

| 命令 | 作用 | 是否调用后端模型 |
|---|---|---|
| `/delegate:review` | 对 `--paths`、`--base`、`--changes` 或 `--context` 指定的范围做只读审查，后端 codex 或 claude-code | 是；`--dry-run` 除外 |
| `/delegate:run` | 把已确认的任务交给 Codex；默认只读，用户明确授权后加 `--write` 才写文件 | 是 |
| `/delegate:doctor [--backend codex\|claude-code]` | 检查所选后端的本地条件 | 否 |
| `/delegate:help` | 显示参数、退出码与迁移说明 | 否 |

Codex 中对应的 skill 为 `source-command-review`、`source-command-run`、`source-command-doctor`、`source-command-help`。旧 `/delegate:delegate` 已在 v0.5.0 移除，通用任务改用 run，结构化审查改用 review。

## 依赖

- 所有用法：Git 工作区、Python 3、Bash（兼容 3.2）。
- Codex 后端：PATH 中可运行的 `codex`，使用 ChatGPT 登录。
- Claude Code 审查后端（可选）：macOS、原版 Claude Code ≥2.1.295 且已登录、Node.js ≥22.12.0、已安装的 srt 0.0.79、可用的用户 GUI launchd 域。

插件不安装依赖、不登录、不修改全局配置。首次使用前运行 `/delegate:doctor`，使用 Claude 后端前运行 `/delegate:doctor --backend claude-code`。

## 目录

```text
.claude-plugin/plugin.json   插件清单
commands/                    review、run、doctor、help 会话入口
skills/delegate-routing/     显式委托请求的分流判据
hooks/                       SessionStart 基础探测、缓存与 doctor 入口
scripts/                     后端调用（Codex / Claude Code）与进程管理
tests/                       离线桩测试与回归
```

## 反馈与许可

问题和建议请提交到 [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues)；安全问题请通过[私密漏洞报告](https://github.com/haigeerlab/delegate-plugin/security/advisories/new)提交。本插件采用 [MIT 许可证](LICENSE)。
