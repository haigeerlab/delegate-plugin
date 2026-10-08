#!/bin/bash

set -u
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${SCRIPT_DIR}/../plugins/delegate"

# Live evals explicitly load this directory with --plugin-dir. Installed versions
# are irrelevant and cannot prove that an uncommitted source change was loaded.
if [ "${1:-}" = --selftest ]; then
  python3 - "${0}" <<'PY'
import os
from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory(prefix='delegate-preflight-selftest.') as temporary:
    directory = Path(temporary)
    cli = directory / 'claude'
    cli.write_text('#!/bin/bash\nif [ "${1:-}" = --version ]; then exit "${FAKE_VERSION_STATUS:-0}"; fi\nif [ "${1:-}" = plugin ] && [ "${2:-}" = validate ]; then exit "${FAKE_VALIDATE_STATUS:-0}"; fi\nexit 9\n')
    cli.chmod(0o755)
    for name, overrides, expected in [('current source', {}, 0), ('CLI failure', {'FAKE_VERSION_STATUS': '1'}, 2), ('invalid source', {'FAKE_VALIDATE_STATUS': '1'}, 2)]:
        env = dict(os.environ, PATH=str(directory) + ':' + os.environ['PATH'], **overrides)
        result = subprocess.run(['/bin/bash', sys.argv[1]], env=env, capture_output=True)
        if result.returncode != expected:
            raise SystemExit('FAIL: ' + name)
        print('PASS: ' + name)
PY
  exit $?
fi
if [ "$#" -ne 0 ]; then
  printf '用法：%s [--selftest]\n' "${0}" >&2
  exit 2
fi
if ! claude --version >/dev/null 2>&1 </dev/null; then
  printf '_preflight: NORUN，claude CLI 不可执行\n' >&2
  exit 2
fi
if ! claude plugin validate "${PLUGIN_ROOT}" >/dev/null 2>&1 </dev/null; then
  printf '_preflight: NORUN，当前源目录原生校验失败：%s\n' "${PLUGIN_ROOT}" >&2
  exit 2
fi
exit 0
