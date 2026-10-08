#!/bin/bash

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${0}")" 2>/dev/null && pwd)"
python3 -B - "${SCRIPT_DIR}" <<'PY' 2>/dev/null || :
import json
import sys

try:
    sys.path.insert(0, sys.argv[1])
    from detect import read_cache
    cache = read_cache()
    if cache and cache['available']:
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'UserPromptSubmit',
                'additionalContext': 'delegate: Codex 基础条件可用（未验证远端连接或额度）。若这一步的决策已经定完、只剩执行与查证，先说明要委托什么、等用户确认后再调；判据见 delegate-routing skill。',
            },
        }, ensure_ascii=False))
except Exception:
    pass
PY
exit 0
