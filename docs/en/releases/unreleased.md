# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Technical design review and second reviewer (interface 1.7) after v0.11.0 is recorded in [v0.12.0 release notes](v0.12.0.md). Reference files no longer need a coverage report after v0.12.0 is recorded in [v0.12.1 release notes](v0.12.1.md). Review failure localization diagnostics after v0.12.1 is recorded in [v0.12.2 release notes](v0.12.2.md). Fix Claude Code backend reviews always failing on macOS after v0.12.2 is recorded in [v0.12.3 release notes](v0.12.3.md). Unreleased changes after v0.12.3 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: doctor subcommand and Claude Code probe deadline raised -->

## `delegate-exec.sh doctor` subcommand

`delegate-exec.sh` used to recognise only `review` and `run` and treat anything else as a legacy no-subcommand call, so `delegate-exec.sh doctor` took "doctor" as the task text: without `--backend` it really started a read-only Codex run, and with `--backend claude-code` it printed the misleading `claude-code requires --review-context`. Now `delegate-exec.sh doctor [--backend codex|claude-code] | --reviewers [--json]` is forwarded unchanged to `review_doctor.py`, the same as `/delegate:doctor`, without calling a model; the help text lists the subcommand.

## Claude Code probe deadline raised to 15 seconds

To decide whether Claude Code is usable, the `--version`, `--help` and `auth status` probes each had only 5 seconds. When the Claude CLI occasionally starts slowly, a probe timed out and `--backend auto` and `doctor --reviewers` misjudged it as unusable, so users with only Claude Code got an "unreviewed" report. Each probe now gets 15 seconds (worst case 45 in total), with no retry; the "unreviewed" report of `--backend auto` appends `probe_stage_*` after the original code to name the failing probe, and the `doctor --reviewers` output is unchanged. The preflight of `review --backend claude-code` uses the same probes, so its deadline is raised too.

## Impact

Only calls whose first argument is exactly `doctor` change: they used to be legacy task text and now run the model-free check. Legacy calls written as `-- "<task>"`, and `review` and `run`, are unaffected. Interface version (1.7) is unchanged.

Probe deadline: only the Claude Code backend preflight and the Claude Code availability decision of `--backend auto` and `doctor --reviewers` change. A real CLI hang waits up to 30 seconds longer. Report fields, exit codes and interface version (1.7) are unchanged.

## Validation and known limitations

New CLI regression: `doctor` with invalid arguments prints `review_doctor.py`'s usage, exits 64 and starts no executor, and the help text lists the subcommand; the test failed before the fix. Running `delegate-exec.sh doctor --backend claude-code` locally reaches the model-free check.

Probe deadline: new and revised regressions (all failing before the fix): all three probes get 15 seconds; `claude_check` returns the main code plus the stage on a probe failure and only the main code on an authentication judgement; `choose` records all codes in order; `doctor --reviewers` shows only the main code. The slow start did not reproduce reliably; the real effect is to be confirmed after release by three consecutive runs with the installed version.
