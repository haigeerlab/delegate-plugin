# Security policy

[简体中文](SECURITY.md) | English

delegate invokes external CLIs, runs model tasks inside sandboxes, and touches local authentication state and project source. Report security problems privately; do not open a public issue.

## Supported versions

| Version | Receives security fixes |
|---|---|
| 0.5.x (current release) | Yes |
| 0.4.x and earlier | No; upgrade to the current release |

The `main` branch may change after a release tag; include the version or commit in your report.

## How to report

Use GitHub private vulnerability reporting: open this repository's [Security → Report a vulnerability](https://github.com/haigeerlab/delegate-plugin/security/advisories/new). Only maintainers can see the report, and it supports private discussion and coordinated fixes. Reports in Chinese or English are welcome.

Please include as much of the following as you can:

- The affected version or commit, backend (codex / claude-code), operating system, and relevant CLI versions;
- The type and impact of the problem: which boundary it crosses and what an attacker needs;
- Minimal reproduction steps, with expected and actual behavior;
- Only the output excerpts you need.

Do not attach credentials, `auth.json`, API keys, full process logs, or business source code.

## Scope

These count as security problems:

- Files written in read-only mode (`/delegate:review`, or `/delegate:run` without `--write`), or files read outside the review snapshot and the specified scope;
- Crossing a declared boundary: the Claude review backend gaining Bash, MCP, network, or re-delegation capabilities, or a recursive delegate call not being refused;
- Credentials, API keys, or authentication data appearing in answers, reports, logs, or caches, or the documented environment variables not being cleared at execution;
- Process logs, review reports, or cache directories with wider permissions than documented (0700 directories, 0600 files), or readable or replaceable by other local users;
- Arbitrary command execution injected through task text, file names, or repository content.

These are not handled as security problems; use a regular [issue](https://github.com/haigeerlab/delegate-plugin/issues) instead:

- Inaccurate or missed review findings, or the model not following behavioral instructions in its prompt (such as "do not commit" or "do not push"). The documentation states these are behavioral constraints, not technical locks;
- Vulnerabilities in upstream components such as Codex, Claude Code, or srt; report them to those projects;
- Writes inside the authorized scope after the user explicitly authorized `--write`.

## Handling

The project has limited maintainer capacity and does not promise a fixed response time. After receiving a report, the maintainer confirms whether it reproduces, assesses the impact, and posts progress in the private report. Fixes ship in a new release and are noted in the release notes; reporters are credited there if they wish. Please do not disclose details before the fix is released.
