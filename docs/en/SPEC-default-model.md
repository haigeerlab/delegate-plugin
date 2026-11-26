# Spec: default-model (per-backend default model from configuration)

[简体中文](../../spec/default-model.md) | English

Drafted 2026-11-26. Source: ecosystem-lead #23280 relaying the user's request ("两步都做"; step 1, the Codex global config, was already done by ecosystem-lead; this module is step 2). On 2026-11-26 the user confirmed the restated requirement and assumptions P1-P6 and the capability-map insertion. This spec doubles as the technical design and regression document; it adds interface fields, tier important, approved by the user. The Chinese page is the authoritative contract.

## Why

The user wants to stop naming a model on every review or run: Codex should default to `gpt-6.2-sol` and Claude Code to Opus 5.5, with an explicit name only for special cases. Today delegate passes nothing when no model is named, so Codex follows `~/.codex/config.toml` and Claude Code falls back to the Claude CLI account default, which is not guaranteed to be Opus 5.5; reports and result files do not say where the model came from.

## Assumptions

Confirmed by the user on 2026-11-26:

- **P1 Location and format.** `${XDG_CONFIG_HOME}/delegate/config.json`, falling back to `~/.config/delegate/config.json` when `XDG_CONFIG_HOME` is unset or not absolute. Per-backend `model` and `effort`. User-level, never in a repository; delegate only reads it and never creates or changes it, nor the Codex or Claude global config.
- **P2 Automatic reviewer selection.** `--backend auto` uses the defaults of whichever backend it chooses; `auto` still rejects explicit `--model`/`--effort` (reviewer-selection E4 unchanged).
- **P3 Resumes ignore the configuration.** `--resume` and `--continue` keep the model and effort recorded for the original session.
- **P4 Unsupported options stay rejected.** `effort` under `claude-code` is a configuration error, not silently ignored.
- **P5 Bad configuration fails hard.** If the file exists but is unreadable, invalid JSON, wrongly shaped, has a model rejected by `model_error`, or an effort outside the allowed values, every review and run exits 64, whether or not this call would use the bad entry. No fallback to the host default.
- **P6 Source in reports and result files.** New fields only; interface 1.8; ecosystem-lead is told first.
- **Both backends go into the delegate configuration**, even though the Codex global config already says `gpt-6.2-sol`, so the source shows as `config` and later changes to the Codex global config do not affect delegation.

Proposed here, for confirmation at review:

- **E1 Precedence and sources.** For each backend, model and effort are resolved separately: explicit option > delegate configuration > host default. Sources: `explicit`, `config`, `host_default`, `resumed`.
- **E2 Format.** Only these keys are accepted; any other key (including a misspelt backend or field name) is an error:

  ```json
  {
    "schema": "delegate.config/v1",
    "defaults": {
      "codex": {"model": "gpt-6.2-sol", "effort": "high"},
      "claude-code": {"model": "claude-opus-5-5"}
    }
  }
  ```

  `schema` and `defaults` are required; every backend and field is optional. `effort` takes the `--effort` values. The file must be a regular file (symlinks not followed), at most 64 KiB, UTF-8. A missing file means no configuration and is not an error.
- **E3 Error output.** One stderr line, `delegate: invalid config <path>: <code>[ at <key path>]` (key path such as `defaults.claude-code.effort` for field errors; names only, never values), so callers such as module-crew and autopilot can relay it verbatim and tell it apart from argument errors and executor failures, with code one of `unreadable`, `not_regular_file`, `too_large`, `invalid_json`, `invalid_schema`, `unknown_key`, `invalid_model`, `model_belongs_to_other_backend`, `invalid_effort`, `effort_not_supported`. File contents are never echoed.
- **E10 Same configuration from both hosts.** The file is located by P1 only, whichever host calls; reviewing with `--backend claude-code` from Codex reads the same configuration (regression DM-15).
- **E4 Report.** New top-level `model_source` (stable v1 field; never `resumed`). `requested_model` now means the model delegate passed to the backend (explicit or configured; `null` for host default) and stays a diagnostic field.
- **E5 Result file.** New `modelSource` and `effortSource`; `model` and `effort` mean the values delegate passed to Codex. `schema` stays `1`.
- **E6 Visible at run time.** The run "model / effort" line names the source; the review `--dry-run` preview carries `requested_model` and `model_source`.
- **E7 Doctor.** `/delegate:doctor` (with or without `--backend`) first prints a "default model" section: config path and whether it exists, each backend's model and effort with source; on a bad configuration it lists the code, finishes the other checks and exits 1. `--reviewers` is unchanged.
- **E8 The legacy `codex-exec.sh` entry does not read the configuration.** Only `delegate-exec.sh` (`/delegate:review`, `/delegate:run`) does.
- **E9 Interface 1.8.** `interface.json` gains top-level `defaults: {"config", "schema": "delegate.config/v1", "sources": [...], "reportField": "model_source", "resultFields": ["modelSource", "effortSource"]}`.

## Design, tests and boundaries

See the Chinese page for the implementation outline (new pure module `delegate_defaults.py`; load in `delegate_cli.main()`; resolve after the final backend is known, including after `auto` selection; sources passed to `codex-exec.sh` through the internal options `--model-source`/`--effort-source`, never the environment; `run_state.py` writes the new result fields), regression cases DM-01 to DM-15 (all free, with temporary `HOME`/`XDG_CONFIG_HOME` and stub backends), risks, trade-offs (JSON rather than TOML because macOS `/usr/bin/python3` is 3.9 without `tomllib`; unknown keys are errors), exclusive files and the Always/Ask first/Never boundaries.

## Open questions

- None.
