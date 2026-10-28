# Capability map: delegate

[简体中文](../../spec/CAPABILITY-MAP.md) | English

## Goal

The current implementation delegates settled execution and investigation to Codex CLI, separates process logs, and returns the final answer with Git evidence for writes. This independent marketplace does not depend on Spec Guard or agent-skills at runtime.

The optional Claude Code read-only review backend was approved on 2026-10-09; see [claude-review](SPEC-claude-review.md). v0.5.0 includes review/run, scope shortcuts and model-free previews, with both local installations checked. Real reviews have succeeded in both directions and the module has completed acceptance under layered criteria; active model boundary attempts and complete abnormal-case scenarios remain unverified; see the [release notes](releases/v0.5.0.md).

The project adoption scope confirmed on 2026-10-08 standardizes file locations. See the [historical archive](../archive/pre-spec-guard/README.md). This confirmation does not retroactively approve earlier module gates.

## Modules

| Module id | Responsibility | Depends on |
|---|---|---|
| channel | Invocation options, read/write sandboxes, process-group deadline and cleanup, log separation, Git evidence | — |
| detection | CLI checks, identity-bound cache, atomic writes, silent degradation, doctor | — |
| routing | Optional criteria/confirmation for explicit delegation; no automatic reminders | channel, detection |
| claude-review | Explicit backend selection, Claude Code read-only reviews, and a shared review result contract while preserving existing Codex behavior | channel, detection, routing |
| integration-interface | Publish a static interface.json declaring external capabilities and the interface version, and document review report schema_version 1 as an external compatibility contract | claude-review |
| run-resume | Add an opt-in resumable mode to run: return a runId and an end status of done/needs-input, and resume the original Codex session with the user's answer through --resume; interface 1.1 adds fields only | channel, integration-interface |
| run-timeout | Keep progress on run timeout: every run gets a time budget in its prompt; a stopped resumable run gets one more read-only wrap-up round; when no progress is obtained, a model-free fallback is printed; new end status timeout (exit 124), and a timed-out resumable run can be --resume'd; fix killpg EPERM; interface 1.2 adds fields only | channel, integration-interface, run-resume |
| write-trust | --write runs no longer let Codex write project trust to the user's ~/.codex/config.toml: when the user config has no trust entry for this repository, an inline -c table trusts it for that run only; existing entries (including untrusted) are left alone; when the check is uncertain, no override is added and a notice is printed | channel, run-resume |
| run-result | run calls Codex with --json and writes a JSON result file on every run (status, commands and exit codes, changed files, marker text, tokens for this run and the whole chain, duration); --strict marks a missing first-line marker as unmarked; the session ID now comes from thread_id; interface 1.3 adds fields only | channel, run-timeout |
| run-continue | --continue <runId> dispatches the next Task after done, accepting only chains started with --resumable and reusing the resume checks for repository, write mode and placeholders; chain state and result files are kept for 14 days and are not pushed out by the 50-group log cleanup | run-resume, run-result |
| run-longrun | --timeout <seconds> only lifts the deadline (541–7200); the caller runs it in the host's background mode and delegate hosts no background process; the main run, wrap-up round and threshold use the run-timeout formulas, and abort cleanup uses the 0.7.1 descendant process-group reclaiming | run-timeout, run-result |
| run-check | --check runs the caller's check command after a run ends with done, as an argument list without a shell (operator rule copied from module-crew S30), and records the result in the result file; --authorized-by records the source file and sha256 of a pre-granted write authorization, identical across the chain | run-result |
| run-rules | --rules-file places a rules section for this delegation only verbatim after the delegate preamble; it wins on conflict (except safety boundaries); its path and sha256 go into the result file; AGENTS.md is neither read nor merged | run-result |

Build order: channel → detection → routing → claude-review → integration-interface → run-resume → run-timeout → write-trust → run-result → run-continue → run-longrun → run-check → run-rules

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
