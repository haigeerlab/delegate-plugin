#!/bin/bash

CACHE_FILE="${TMPDIR:-/tmp}/delegate/detection.json"

python3 - "${CACHE_FILE}" <<'PY' 2>/dev/null || :
import json
import sys
import time

try:
    with open(sys.argv[1]) as cache_file:
        cache = json.load(cache_file)

    if cache.get("available") is not True:
        raise ValueError()

    checked_at = cache.get("checkedAt")
    if isinstance(checked_at, bool) or not isinstance(checked_at, (int, float)):
        raise ValueError()
    if not 0 <= time.time() - checked_at <= 8 * 60 * 60:
        raise ValueError()

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "delegate: Codex 后端可用。若这一步的决策已经定完、只剩执行与查证，先说明要委托什么、等用户确认后再调；判据见 delegate-routing skill。",
        },
    }, ensure_ascii=False))
except Exception:
    pass
PY

exit 0
