# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Fixes and documentation maintenance after v0.5.0 are recorded in [v0.5.1 release notes](v0.5.1.md). Unreleased changes after v0.5.1 are listed below. Historical acceptance records retain their original version/status without retroactive approval.

## Documentation

- README troubleshooting fixes (from a real Claude backend review, checked against the code): the `native_authentication_environment_unverified` check now lists variable names only so secret values are not printed; "No proposal after signing in" now explains that since v0.5.0 a proposal appears only on an explicit delegation request; a new row covers Claude backend diagnostics and next steps on non-macOS, without a GUI launchd domain, or when the kernel interface check fails; the meaning of Codex 0.160.0, 0.162.1, and the `@latest` install is spelled out. Chinese and English kept in sync.
