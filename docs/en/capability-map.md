# Capability map: delegate

[简体中文](../../capability-map.md) | English

Repair contract dated 2026-10-08, based on user-confirmed scope; early task records remain historical evidence.
An independent marketplace supporting only Codex CLI, without dependencies on spec-guard or agent-skills.

| Module | Responsibility | Dependency |
|---|---|---|
| channel | Invocation options, read/write sandboxes, process-group deadline and cleanup, log separation, Git evidence | Shared backend readiness checks |
| detection | CLI checks, identity-bound cache, atomic writes, silent degradation, doctor | Shared backend readiness checks |
| routing | Inject facts and confirmation requirements; skill supplies task criteria | Detection cache; channel executes after confirmation |

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
