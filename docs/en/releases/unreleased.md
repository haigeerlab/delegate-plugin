# Unreleased changes

[简体中文](../../releases/unreleased.md) | English

This page records changes after v0.4.0 that have not yet been released. Published execution-lifecycle, authentication, cache, and Git-verification fixes are documented in [v0.4.0 release notes](v0.4.0.md) and the [release page](https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.4.0).

## Documentation

- Extend the Chinese README with first read-only delegation, updates/uninstalling, exit statuses, contributions, and feedback.
- Distinguish remote installation cache, local-path loading, and host auto-update settings.
- Add a bilingual documentation index and contribution guide. Provide English counterparts and language switches for README, design, capability map, three specifications, and release notes.
- Identify historical tasks, plans, and older release descriptions, and correct stale statements after v0.4.0 was published.

## Test fixes

- Doctor rule assertions explicitly use the suite CLI stub, synthetic authentication, and temporary log, removing reliance on outer Codex installation/login; free aggregate validation passes without an outer CLI.

## Development conventions

- Adopt Spec Guard's local multi-module convention, adding project AGENTS.md, CLAUDE.md, and a bilingual workflow. Product runtime gains no dependency.
- Move Chinese contracts into spec/, standardize the capability map and bilingual navigation, and archive original tasks byte for byte. Current checklists track maintenance reconciliation only.
- Add a sanitized historical verification index. Historical approval gaps remain unknown rather than retroactively accepted.

## License

- Adopt the MIT License, with identical standard text at the repository root and in the plugin directory.
- Declare `license: MIT` in the plugin manifest and synchronize license information in both READMEs, contribution guides, and documentation indexes.

This revision updates documentation, project development conventions, test fixtures, and license metadata. The plugin version remains 0.4.0; runtime behavior has not changed and no new release has been created.
