# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Technical design review and second reviewer (interface 1.7) after v0.11.0 is recorded in [v0.12.0 release notes](v0.12.0.md). Reference files no longer need a coverage report after v0.12.0 is recorded in [v0.12.1 release notes](v0.12.1.md). Review failure localization diagnostics after v0.12.1 is recorded in [v0.12.2 release notes](v0.12.2.md). Fix Claude Code backend reviews always failing on macOS after v0.12.2 is recorded in [v0.12.3 release notes](v0.12.3.md). doctor subcommand and Claude Code probe deadline raised after v0.12.3 is recorded in [v0.12.4 release notes](v0.12.4.md). Recovery hint when the Claude login token expires after v0.12.4 is recorded in [v0.12.5 release notes](v0.12.5.md). Review command states the report comes from stdout after v0.12.5 is recorded in [v0.12.6 release notes](v0.12.6.md). Unreleased changes after v0.12.6 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: Per-backend default model (interface 1.8) -->

## Per-backend default model

When a review or run names no model, delegate now uses the per-backend defaults in `~/.config/delegate/config.json` (or `$XDG_CONFIG_HOME/delegate/config.json`), for example `gpt-6.2-sol` for Codex and `claude-opus-5-5` for Claude Code; name a model as before when you need something else. The contract is in the [default-model spec](../SPEC-default-model.md).

- Precedence: explicit > configuration > host default, resolved separately for model and effort; `--backend auto` uses the defaults of the backend it picks; `--resume` and `--continue` keep the original session. A Claude Code review started from Codex reads the same file.
- Format `delegate.config/v1`: only `schema`, `defaults` and each backend's `model` (plus `effort` for Codex); extra keys, invalid model names or effort values are errors.
- The review report gains the stable field `model_source`, the result file gains `modelSource` and `effortSource`, and the run's model line names the source; `/delegate:doctor` lists the effective defaults first.

## Impact

- Interface `1.7` to `1.8`, additive only; report `schema_version` and result-file `schema` stay `1`. No plugin's main branch reads `model`, `effort` or `requested_model` (checked by ecosystem-lead on 2026-11-26 with `git grep` across each repository's main branch, agent-relay message #23282).
- Without a configuration file, behaviour is the same as v0.12.6.
- **When the file exists but is invalid, every review and run exits 64** with one stderr line `delegate: invalid config <path>: <code>[ at <key>]`, which callers such as module-crew and autopilot can relay as is; `/delegate:doctor` then exits 1.
- The diagnostic field `requested_model` now means the model delegate actually passed to the backend (explicit or configured; `null` for the host default).
- The legacy `codex-exec.sh` entry does not read the configuration.

## Validation and known limitations

New behaviour was tested first and seen to fail before implementation; regressions added after the entry already read the configuration (run-side configuration errors, the ten errors through both entries, `--reviewers` unchanged) passed at once, two of them confirmed by a temporary mutation. Resolution, the ten configuration errors, path rules, review and run end to end, resumes, doctor and the interface shape are covered with stub backends and temporary directories. The regression runner gives each suite an empty private `XDG_CONFIG_HOME`, so no suite reads the real configuration. Nothing ran against real Codex or Claude; the Claude path replaces the review function in process and only checks the model it receives, while the step where the real CLI receives `--model` is unchanged code.
