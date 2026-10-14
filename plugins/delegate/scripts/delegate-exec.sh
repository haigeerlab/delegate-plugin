#!/bin/bash
# Shared public entry; keep the legacy Codex implementation available.
set -u
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'delegate: 找不到 python3。\n' >&2
  exit 127
fi
exec python3 -B "${SCRIPT_DIR}/delegate_cli.py" "$@"
