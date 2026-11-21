#!/bin/bash
# Unattended release preparation (spec/release-prepare.md): stdin is never read.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 -B "${ROOT_DIR}/scripts/release_prepare.py" "$@" </dev/null
