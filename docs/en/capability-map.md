# Capability map: delegate

[简体中文](../../spec/CAPABILITY-MAP.md) | English

## Goal

The current implementation delegates settled execution and investigation to Codex CLI, separates process logs, and returns the final answer with Git evidence for writes. This independent marketplace does not depend on Spec Guard or agent-skills at runtime.

The optional Claude Code read-only review backend was approved on 2026-10-09; see [claude-review](SPEC-claude-review.md). Mac source and free checks are connected, and strict original authentication plus a limited Codex→Claude real review passed. Normal real reviews succeeded in both directions; active model boundary attempts and complete abnormal-case acceptance remain incomplete. Unreleased review/run commands, scope shortcuts and model-free previews are added; published v0.4.0 does not contain these changes.

The project adoption scope confirmed on 2026-10-08 standardizes file locations. See the [historical archive](../archive/pre-spec-guard/README.md). This confirmation does not retroactively approve earlier module gates.

## Modules

| Module id | Responsibility | Depends on |
|---|---|---|
| channel | Invocation options, read/write sandboxes, process-group deadline and cleanup, log separation, Git evidence | — |
| detection | CLI checks, identity-bound cache, atomic writes, silent degradation, doctor | — |
| routing | Optional criteria/confirmation for explicit delegation; no automatic reminders | channel, detection |
| claude-review | Explicit backend selection, Claude Code read-only reviews, and a shared review result contract while preserving existing Codex behavior | channel, detection, routing |

Build order: channel → detection → routing → claude-review

channel and detection share `backend.py`; this shared code is not a separate module dependency. routing uses detection diagnostics for explicit requests and invokes channel after authorization. The build order preserves the existing implementation sequence without adding runtime responsibilities.

```text
backend.py → codex-exec.sh → run_codex.py → codex exec
     ↓
detect.py ← detect.sh / doctor.sh
     ↓ detection.json → doctor
explicit request → delegate-routing skill → review/run
```

- channel does not decide which tasks to delegate and checks basic authentication again on every invocation.
- detection makes no model requests. Local checks do not guarantee remote connectivity or quota.
- routing does not invoke Codex or classify by keywords. The model interprets the criteria; the user authorizes execution.
- channel remains manually callable without routing. The shared backend does not depend on hook cache.
- doctor belongs to detection. It refreshes checks and inspects Chinese global rules on demand; temporary cache writes do not modify the target project.
- Write mode does not require a clean working tree. Existing-change counts and staged/unstaged statistics must be visible; failure does not trigger automatic rollback.
- Read-only is the default. Writes require explicit authorization in the current turn; command confirmation rules are not a technical lock that cannot be bypassed.

See [channel](SPEC-channel.md), [detection](SPEC-detection.md), and [routing](SPEC-routing.md) for existing contracts and validation. The new module is tracked separately in [claude-review](SPEC-claude-review.md). No non-Git support, background orchestration, committing/pushing/publishing, or self-updating installation cache is introduced.

The first real reverse run started Codex from Claude but reviewed no files. Codex review now receives bounded inline file data, with a 1 MiB serialized input limit and verified disabled shell/apps/plugins/multi-agent features. The repaired real reverse review completed 4/4; see the [latest evidence and limits](../verification/2026-10-12-claude-review-mac-reverse-fourth-success.md) (Chinese). The first failed run remains historical.
