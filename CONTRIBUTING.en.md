# Contributing

[简体中文](CONTRIBUTING.md) | English

Thank you for helping improve delegate. Start with the [README](README.en.md), [Design and boundaries](docs/en/DESIGN.md), and the [current specifications](docs/en/README.md) for the affected module. Historical task records provide background and do not override current contracts.

## Reporting issues and suggesting changes

Search existing [GitHub Issues](https://github.com/haigeerlab/delegate-plugin/issues) first. A new report should include:

- Claude Code, Codex CLI, Python, Bash, operating-system, and plugin versions;
- Installation method: remote marketplace, local path, or `--plugin-dir`;
- Minimal reproduction steps, expected and actual behavior, and exit status;
- Relevant `/delegate:doctor` diagnostics and necessary log excerpts;
- Git state for write-mode issues, including whether uncommitted changes existed beforehand.

Share only what is needed to reproduce the issue. Remove credentials, personal paths, proprietary source, and unrelated private material before submitting. Do not upload `auth.json`, API keys, full process logs, or machine identity paths from the cache.

## Development setup

See the [README prerequisites](README.en.md#prerequisites). Validate manifests from this repository's root:

```bash
claude plugin validate .
claude plugin validate ./plugins/delegate
```

Explicitly load the source plugin directory from a target Git project when developing:

```bash
claude --plugin-dir /path/to/delegate-plugin/plugins/delegate
```

An installed version number matching the source version does not prove that source content was loaded. See [Updates and uninstalling](README.en.md#updates-and-uninstalling) for remote caches, local paths, and reloading.

## Changes and validation

Keep changes focused. For behavior changes, add a regression that reproduces the failure before fixing the implementation; do not weaken assertions to make tests pass. Update affected specifications and help text so documentation remains consistent with behavior.

Run the free offline validation from the **repository root**:

```bash
/bin/bash scripts/validate.sh
```

The entry point checks JSON/Python/Bash syntax, executable permissions, manifest required fields, evaluator self-tests, all 3 shell product suites, and 2 Python regression suites. The baseline includes 52 product assertions and 17 Python regressions. Stub tests neither read real credentials nor call models.

To isolate a failure, run individual suites:

```bash
/bin/bash plugins/delegate/tests/test-channel.sh
/bin/bash plugins/delegate/tests/test-detection.sh
/bin/bash plugins/delegate/tests/test-routing.sh
python3 -B plugins/delegate/tests/test-backend.py
python3 -B plugins/delegate/tests/test-channel-regressions.py
/bin/bash evals/propose-not-auto.sh --scaffold-only
/bin/bash evals/routing-fitness.sh --scaffold-only
```

Free stubs verify deterministic invocation and process contracts; they do not prove real CLI sandbox or model behavior. The following commands **call models and consume quota**, are excluded from the aggregate validation, and should be run deliberately for a defined verification purpose:

```bash
/bin/bash plugins/delegate/tests/test-channel.sh --live
/bin/bash evals/propose-not-auto.sh
/bin/bash evals/routing-fitness.sh
```

Evaluations explicitly load source with `--plugin-dir`. Exit statuses are 0=PASS, 1=FAIL, and 2=NORUN. routing-fitness accepts only the complete first nonempty line `判断：委托` or `判断：自己做` (delegate or do it in the main session). A single `claude -p` turn cannot establish that interactive sessions always propose delegation when appropriate; global rules may also affect results. See the [routing specification](docs/en/SPEC-routing.md).

Keep Bash 3.2 compatibility: use `${VAR}`, guard empty arrays with `${ARR[@]+"${ARR[@]}"}`, and avoid `cmd | grep -q`. Run shell tests with `/bin/bash` to avoid zsh redirection differences.

## Maintaining bilingual documentation

- `README.md` and root design/specification documents remain Chinese. `README.en.md`, `CONTRIBUTING.en.md`, and `docs/en/` provide English counterparts.
- Correct Chinese facts and reading flow first, then synchronize English. Wording may suit each audience, but options, defaults, exit statuses, permissions, failure semantics, and verification scope must agree.
- Keep language switches in both directions for maintained documentation. English navigation should normally link to English counterparts. Clearly identify source and historical records available only in Chinese or their original language.
- Task examples may be translated. Preserve command names, options, environment variables, paths, and diagnostic or evaluation strings that require exact matching.
- Preserve historical facts and checkbox states, adding archive notices that point to current contracts. Do not rewrite an old design as though later behavior had already been implemented.

After editing documentation, check file links, heading anchors, and code fences, and run `git diff --check`. The [documentation index](docs/en/README.md) lists language pairs.

## Submitting a pull request

Use a separate branch and submit a focused PR. Describe the concrete problem, resulting behavior or reading flow, validation performed, and its limitations. Behavior changes, documentation synchronization, and necessary tests can be reviewed together; avoid unrelated refactoring.

Check manifests and relevant validation before submission, and inspect the actual diff. A write-mode delegation can leave changes after either success or failure; the model's own account is not sufficient to verify correctness.

This project uses the [MIT License](LICENSE). Ensure contributions are compatible with it and retain required copyright and license notices for third-party material.
