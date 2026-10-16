# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

Fixes and documentation maintenance after v0.5.0 are recorded in [v0.5.1 release notes](v0.5.1.md). Unreleased changes after v0.5.1 are listed below. Historical acceptance records retain their original version/status without retroactive approval.

## Fixes

- Codex review now attaches file contents with a 1-based line-number prefix on every line, and the prompt says `findings.line` must be that file line number. Previously contents had no line numbers; in a real review the model returned `line=null`, the finding could not be located, and the whole review was marked `failed` (`review_incomplete`). Snapshots, SHA-256 and the rule that any unlocated finding keeps a review incomplete are unchanged; the prefixes count toward the 1 MiB input cap. Not yet re-verified with a real model.

## Documentation

- README prerequisites and quick start fixes (from a real Codex backend review, checked against the code): `/delegate:review` requires a repository with at least one commit, while repositories without commits work only with `/delegate:run`; installing Codex and signing in with ChatGPT is marked as a Codex-backend-only step that Claude-review-only users can skip. Chinese and English kept in sync.
- README troubleshooting fixes (from a real Claude backend review, checked against the code): the `native_authentication_environment_unverified` check now lists variable names only so secret values are not printed; "No proposal after signing in" now explains that since v0.5.0 a proposal appears only on an explicit delegation request; a new row covers Claude backend diagnostics and next steps on non-macOS, without a GUI launchd domain, or when the kernel interface check fails; the meaning of Codex 0.160.0, 0.162.1, and the `@latest` install is spelled out. Chinese and English kept in sync.
