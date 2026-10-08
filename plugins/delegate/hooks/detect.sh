#!/bin/bash

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${0}")" 2>/dev/null && pwd)"
if ! python3 -B "${SCRIPT_DIR}/detect.py" "${1:-}" 2>/dev/null; then
  if [ "${1:-}" = --print ]; then
    printf '不可用：基础探测失败，请安装 Python 3 并检查插件文件\n'
  fi
fi
exit 0
