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
| review-fingerprint | The review report adds a patch fingerprint scope.fingerprint that does not depend on local git configuration or the git version (sha256 over the from/to object ids of the reviewed files), emitted only for the commits baseline; the algorithm is published in interface.json so consumers can recompute it on another machine; diff_sha256 is unchanged; interface 1.4, fields added only | claude-review, integration-interface |
| review-severity | Each finding in the review report gains severity (blocking or suggestion), labelled by the review model against criteria written into the prompt; both backends share one structure and validation; consumers treat a missing or unknown value as blocking; interface 1.5, fields added only | claude-review, integration-interface |
| review-recheck | --previous-report accepts the previous delegate review report and gives its blocking findings to this round's model; the report marks each as resolved or unresolved and lists new findings separately; both backends; a scope mismatch reports a fixed diagnostic instead of comparing; round counting and hand-off to a person are the caller's decision | review-severity |
| review-snapshot-recheck | Snapshot reviews (--paths/--spec/--plan, from=to) can be rechecked with --previous-report after rework: when both rounds are snapshots only paths and mode are compared, and the baseline may move forward on the same history; the prompt says context_files are only for verifying references, not for findings; interface 1.6, additive | review-recheck |
| design-review-criteria | review gains --profile design (criteria design-v1) for technical designs: a blocking finding must point to a real line in a snapshot file other than the design itself, otherwise it is downgraded to a suggestion marked downgraded=no_code_evidence; with --previous-report the second round only checks the previous round and new findings are suggestions; without the option behavior and criteria are unchanged | review-snapshot-recheck |
| reviewer-selection | review gains --backend auto and --author-host: model-free local checks pick a reviewer from another vendor first, fall back to a fresh same-vendor session, and otherwise return an "unreviewed" report (no_reviewer_available); the report gains top-level reviewer {vendor, backend, same_vendor, selection}; doctor lists available reviewers and hints when only one vendor is set up; interface 1.7, additive | design-review-criteria, detection |
| release-prepare | The repository script scripts/release-prepare.sh <version> [--check] runs unattended and takes release preparation up to one commit on a local release branch: bump the version, generate release notes from the unreleased notes, update current-release links and test counts, run every free check, and print a JSON summary with commit SHAs and the commands a person must run; it never pushes, opens a PR, tags, or touches the local installation | integration-interface |
| validate-speed | Speed up the repository's free full validation: scripts/validate.sh runs the regression suites in parallel across cores (own temporary directory per suite, output printed whole in list order, slowest suites listed at the end), adds --quick to run only the suites this branch's changes touch and fall back to the full run when unmapped, and removes real waiting from timeout tests; no tests deleted, no product behavior or CI changed | release-prepare |

Build order: channel → detection → routing → claude-review → integration-interface → run-resume → run-timeout → write-trust → run-result → run-continue → run-longrun → run-check → run-rules → review-fingerprint → review-severity → review-recheck → review-snapshot-recheck → design-review-criteria → reviewer-selection → release-prepare → validate-speed

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
