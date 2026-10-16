# delegate plugin

[简体中文](README.md) | English

This directory is the delegate plugin itself and is what the installation cache contains. See the repository [README](https://github.com/haigeerlab/delegate-plugin/blob/main/README.en.md) for complete installation, option, verification, and troubleshooting guidance.

delegate sends scoped read-only reviews to Codex or Claude Code and sends general tasks with a settled plan to Codex. Choose the backend explicitly with `--backend`; Codex is the default. The plugin runs only on an explicit user request or confirmation and never delegates automatically.

## Commands

| Command | Purpose | Calls a backend model |
|---|---|---|
| `/delegate:review` | Read-only review of the scope given by `--paths`, `--base`, `--changes`, or `--context`, on the codex or claude-code backend | Yes, except with `--dry-run` |
| `/delegate:run` | Sends a confirmed task to Codex; read-only by default, writes files only with `--write` after explicit user authorization | Yes |
| `/delegate:doctor [--backend codex\|claude-code]` | Checks local prerequisites for the chosen backend | No |
| `/delegate:help` | Shows options, exit statuses, and migration notes | No |

In Codex the corresponding skills are `source-command-review`, `source-command-run`, `source-command-doctor`, and `source-command-help`. The old `/delegate:delegate` was removed in v0.5.0: use run for general tasks and review for structured reviews.

## Requirements

- All uses: a Git working tree, Python 3, and Bash (compatible with 3.2).
- Codex backend: a working `codex` on PATH, signed in through ChatGPT.
- Claude Code review backend (optional): macOS, the official Claude Code ≥2.1.295 already signed in, Node.js ≥22.12.0, an installed srt 0.0.79, and an available user GUI launchd domain.

The plugin installs no dependencies, signs in to nothing, and changes no global configuration. Run `/delegate:doctor` before first use, and `/delegate:doctor --backend claude-code` before using the Claude backend.

## Layout

```text
.claude-plugin/plugin.json   Plugin manifest
commands/                    review, run, doctor, help session entries
skills/delegate-routing/     Routing criteria for explicit delegation requests
hooks/                       SessionStart readiness checks, cache, doctor entry
scripts/                     Backend invocation (Codex / Claude Code) and process management
tests/                       Offline stub tests and regressions
```

## Feedback and license

Report problems and suggestions through [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues); report security problems through [private vulnerability reporting](https://github.com/haigeerlab/delegate-plugin/security/advisories/new). This plugin is released under the [MIT License](LICENSE).
