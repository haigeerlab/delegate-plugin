#!/bin/bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PATH="${SCRIPT_DIR}:${PATH}"
export PATH

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "${1}"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "${1}" >&2
}

printf '  总计 %s 通过 / %s 失败\n' "${PASS_COUNT}" "${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then
  exit 1
fi
