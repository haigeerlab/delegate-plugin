#!/bin/bash
# Fail when tracked or new (non-ignored) files contain a machine-specific
# macOS home path such as /Users/<name>/. Placeholders (~, $HOME, <repo>,
# /Users/<用户名>/) are allowed. Usage: check-local-paths.sh [repo-root]

set -u

ROOT="${1:-$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
PATTERN='/Users/[A-Za-z0-9._-]+/'

MATCHES="$(git -C "${ROOT}" grep -nIE --untracked "${PATTERN}" -- . 2>/dev/null)"
case $? in
  0)
    printf 'local-paths: 发现本机绝对路径，请改成 ~/…、$HOME/…、<repo>/… 或 /Users/<用户名>/…：\n%s\n' "${MATCHES}" >&2
    exit 1
    ;;
  1)
    exit 0
    ;;
  *)
    printf 'local-paths: 无法在 %s 上运行 git grep\n' "${ROOT}" >&2
    exit 2
    ;;
esac
