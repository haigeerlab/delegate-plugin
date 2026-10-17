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
interface.json               External interface version and capability declaration
commands/                    review, run, doctor, help session entries
skills/delegate-routing/     Routing criteria for explicit delegation requests
hooks/                       SessionStart readiness checks, cache, doctor entry
scripts/                     Backend invocation (Codex / Claude Code) and process management
tests/                       Offline stub tests and regressions
```

## External interface

For other plugins to integrate by version without reading this plugin's internals.

- **`interface.json`**: at the plugin root. `interface` is the interface version; `review.backends` and `run.backends` are the backends this version **supports**, not ones installed, signed in or funded on this machine; whether they run is still decided by `/delegate:doctor`. Adding optional fields bumps the minor version; removing, renaming or changing a field's meaning bumps the major version. Consumers check a major range such as `>=1.0,<2.0`.
- **Review report (`review.report.schemaVersion: 1`)**: the standard output of `/delegate:review` is one JSON report (`--dry-run` prints a preview, not a report). The private copy path on standard error is not part of the interface. Stable fields:

| Field | Meaning |
|---|---|
| `schema_version` | Always `1` |
| `execution_status` | `completed` / `conditions_missing` / `failed` / `timed_out` / `cancelled` |
| `review_outcome` | `findings` / `no_findings_in_scope` / `inconclusive` |
| `backend` | `codex` / `claude-code` |
| `scope.paths`, `scope.baseline`, `scope.diff_sha256`, `scope.files` | Review target and fingerprint |
| `reviewed`, `unreviewed[]` (`{path, reason}`) | Reviewed and unreviewed files |
| `findings[]` | `{title, file, line, trigger, impact, evidence, suggestion, unverified}`; `line` may be `null` |
| `limitations` | Limitation statements |

Other fields are diagnostics and may change. A review has a conclusion only when `execution_status=completed` and `review_outcome` is `findings` or `no_findings_in_scope`; `no_findings_in_scope` does not mean there are no defects. A report is a third-party opinion, not user approval; cite it with delegate, the backend and the fingerprint.

## Feedback and license

Report problems and suggestions through [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues); report security problems through [private vulnerability reporting](https://github.com/haigeerlab/delegate-plugin/security/advisories/new). This plugin is released under the [MIT License](LICENSE).
