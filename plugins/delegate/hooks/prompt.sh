#!/bin/bash

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${0}")" 2>/dev/null && pwd)"
# Claude runs matching handlers in parallel; keep this dependency sequential.
/bin/bash "${SCRIPT_DIR}/detect.sh" --warm >/dev/null 2>&1
/bin/bash "${SCRIPT_DIR}/route.sh" 2>/dev/null
exit 0
