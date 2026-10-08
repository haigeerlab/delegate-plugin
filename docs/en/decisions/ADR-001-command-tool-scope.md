# ADR-001: Retain the command's current Bash declaration

Status: Accepted. Date: 2026-10-08. Authorization: the user replied “继续” to the concrete combined request for batches A/B. This accepts the current decision and does not retroactively approve earlier work.

## Context

Archived channel:7-A1 required Bash with a fixed script-path glob. The command has declared allowed-tools: Bash since introduction. Commit cd0ebafb28723a7d195de9ee029f8832670e0885 explains that fixed globs fail when installation paths change; that developer rationale alone is not human approval.

## Decision

Retain the current Bash declaration. Explicit task authorization, default read-only execution and separate current-turn write authorization remain required. Runtime code, the declaration and installation are unchanged. Classify the earlier literal fixed-path criterion as superseded, rather than satisfied.

## Alternatives and consequences

A fixed installation path harms portability; a variable-based narrow rule has not received compatibility testing in this batch and is not substituted directly. Bash permits a broader tool scope. Textual confirmation rules do not establish least privilege or an authorization lock that cannot be bypassed. Future narrowing requires a separate design and tests against source and user installation paths. Historical completion and approval remain unknown.

[中文决定](../../decisions/ADR-001-command-tool-scope.md).
