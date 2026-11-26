# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

<!-- Before a release, add after the "recorded in…" paragraph below, in the format of the "Releasing" section of CONTRIBUTING.en.md: the title comment line, this release's change sections, ## Impact and ## Validation and known limitations; scripts/release-prepare.sh generates the release notes from them. -->

Run-timeout progress keeping (interface 1.2) and write mode no longer writing Codex project trust, both after v0.6.0, are recorded in [v0.7.0 release notes](v0.7.0.md); reclaiming commands started by Codex on abort, after v0.7.0, is recorded in [v0.7.1 release notes](v0.7.1.md); interface 1.3 after v0.7.1 (result file, continue, long tasks, check and write authorization, rules section) is recorded in [v0.8.0 release notes](v0.8.0.md); the documentation catch-up after v0.8.0 is recorded in [v0.8.1 release notes](v0.8.1.md); the run command description fixes after v0.8.1 are recorded in [v0.8.2 release notes](v0.8.2.md). The user documentation fixes after v0.8.2 are recorded in [v0.8.3 release notes](v0.8.3.md). The dedicated diagnostic for repositories without commits after v0.8.3 is recorded in [v0.8.4 release notes](v0.8.4.md). The Codex review schema fix and failure-cause diagnostics after v0.8.4 are recorded in [v0.8.5 release notes](v0.8.5.md). The sandbox certificate trust after v0.8.5 is recorded in [v0.8.6 release notes](v0.8.6.md). The review report patch fingerprint (interface 1.4) after v0.8.6 is recorded in [v0.9.0 release notes](v0.9.0.md). Finding severity and re-review against the previous round (interface 1.5) after v0.9.0 are recorded in [v0.10.0 release notes](v0.10.0.md). Rechecking snapshot reviews (interface 1.6) after v0.10.0 is recorded in [v0.11.0 release notes](v0.11.0.md). Technical design review and second reviewer (interface 1.7) after v0.11.0 is recorded in [v0.12.0 release notes](v0.12.0.md). Reference files no longer need a coverage report after v0.12.0 is recorded in [v0.12.1 release notes](v0.12.1.md). Review failure localization diagnostics after v0.12.1 is recorded in [v0.12.2 release notes](v0.12.2.md). Fix Claude Code backend reviews always failing on macOS after v0.12.2 is recorded in [v0.12.3 release notes](v0.12.3.md). doctor subcommand and Claude Code probe deadline raised after v0.12.3 is recorded in [v0.12.4 release notes](v0.12.4.md). Unreleased changes after v0.12.4 follow. Historical acceptance records retain their original version/status without retroactive approval.

<!-- release-title: Recovery hint when the Claude login token expires -->

## Recovery hint when the Claude login token expires

After the Claude login token expires, `review --backend claude-code` always fails, while the check and `claude auth status` still report logged in and the report only carries `claude_api_authentication_failed`, so callers did not know how to recover. Such failures now also add the fixed code `claude_login_refresh_required` to `diagnostics`, and stderr gets one fixed line: run `claude` once in a terminal outside the sandbox (for example `claude -p "ok"`) to refresh the login and retry; if it still fails, run `claude /login`. `/delegate:doctor --backend claude-code` also notes that logged in does not mean the token is still valid and gives the same hint. delegate does not refresh tokens or read or write credentials.

## Impact

Only the diagnostic code and stderr of failed Claude Code backend reviews change, plus one extra note line in the claude-code check. Report fields, exit codes and interface version (1.7) are unchanged; the Codex backend and run are unaffected.

## Validation and known limitations

New regressions (failing before the fix): an authentication failure event gives both codes in order and other API errors do not add it; through the public entry (explicit claude-code and auto) stderr carries the fixed hint exactly once, none without the code, and stdout holds only JSON; the check prints the note and `--reviewers` is unchanged. Token expiry cannot be produced on demand; the real effect is to be recorded with the installed version when it happens.
