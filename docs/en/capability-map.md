# Capability map: delegate

[简体中文](../../spec/CAPABILITY-MAP.md) | English

## Goal

Delegate settled execution and investigation to Codex CLI, separate process logs, and return the final answer with Git evidence for writes. This independent marketplace supports only Codex CLI; runtime does not depend on Spec Guard or agent-skills.

The project adoption scope confirmed on 2026-10-08 standardizes file locations. See the [historical archive](../archive/pre-spec-guard/README.md). This confirmation does not retroactively approve earlier module gates.

## Modules

| Module id | Responsibility | Depends on |
|---|---|---|
| channel | Invocation options, read/write sandboxes, process-group deadline and cleanup, log separation, Git evidence | — |
| detection | CLI checks, identity-bound cache, atomic writes, silent degradation, doctor | — |
| routing | Inject facts and confirmation requirements; skill supplies task criteria | channel, detection |

Build order: channel → detection → routing

channel and detection share `backend.py`; this shared code is not a separate module dependency. routing consumes detection cache and uses channel after confirmation. The build order preserves the existing implementation sequence without adding runtime responsibilities.

```text
backend.py → codex-exec.sh → run_codex.py → codex exec
     ↓
detect.py ← detect.sh / doctor.sh
     ↓ detection.json
prompt.sh: detect.sh --warm → route.sh → delegate-routing skill
```

- channel does not decide which tasks to delegate and checks basic authentication again on every invocation.
- detection makes no model requests. Local checks do not guarantee remote connectivity or quota.
- routing does not invoke Codex or classify by keywords. The model interprets the criteria; the user authorizes execution.
- channel remains manually callable without routing. The shared backend does not depend on hook cache.
- doctor belongs to detection. It refreshes checks and inspects Chinese global rules on demand; temporary cache writes do not modify the target project.
- Write mode does not require a clean working tree. Existing-change counts and staged/unstaged statistics must be visible; failure does not trigger automatic rollback.
- Read-only is the default. Writes require explicit authorization in the current turn; command confirmation rules are not a technical lock that cannot be bypassed.

See [channel](SPEC-channel.md), [detection](SPEC-detection.md), and [routing](SPEC-routing.md) for contracts and validation. No additional backends, non-Git support, background jobs, committing/pushing/publishing, or self-updating installation cache are introduced.
