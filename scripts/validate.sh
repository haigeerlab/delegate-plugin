#!/bin/bash

set -u

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS=0

fail() {
  printf 'validate: %s\n' "${1}" >&2
  STATUS=1
}

check_json() {
  JSON_FILE="${1}"
  if ! python3 -m json.tool "${JSON_FILE}" >/dev/null 2>&1; then
    fail "invalid JSON: ${JSON_FILE#"${ROOT_DIR}/"}"
  fi
}

check_shell() {
  SHELL_FILE="${1}"
  RELATIVE_FILE="${SHELL_FILE#"${ROOT_DIR}/"}"

  if ! /bin/bash -n "${SHELL_FILE}"; then
    fail "bash syntax error: ${RELATIVE_FILE}"
  fi

  if [ ! -x "${SHELL_FILE}" ]; then
    fail "not executable: ${RELATIVE_FILE}"
  fi

  if ! python3 - "${SHELL_FILE}" <<'PY'
import re
import sys

path = sys.argv[1]
text = open(path, "rb").read()
bare_variable_before_multibyte = re.compile(rb'\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7f]')
grep_quiet_pipeline = re.compile(rb'\|\s*(?:[A-Za-z0-9_./-]+\s+)*grep\s+-q(?:\s|$)')

for line_number, line in enumerate(text.splitlines(), 1):
    if bare_variable_before_multibyte.search(line):
        sys.stderr.write("%s:%d: bare variable directly before multibyte text\n" % (path, line_number))
        sys.exit(1)
    if grep_quiet_pipeline.search(line):
        sys.stderr.write("%s:%d: grep -q in a pipeline is forbidden\n" % (path, line_number))
        sys.exit(1)
PY
  then
    fail "unsafe shell pattern: ${RELATIVE_FILE}"
  fi
}

while IFS= read -r -d '' JSON_FILE; do
  check_json "${JSON_FILE}"
done < <(find "${ROOT_DIR}" -path "${ROOT_DIR}/.git" -prune -o -type f -name '*.json' -print0)

# 只按 .sh 后缀找会漏掉 stub-codex 这类没有扩展名的 shell 脚本 ——
# 它照样是 bash，照样会踩 bash 3.2 的坑，必须一起查。
is_shell() {
  case "${1}" in
    *.sh) return 0 ;;
  esac
  FIRST_LINE=$(head -1 "${1}" 2>/dev/null || true)
  case "${FIRST_LINE}" in
    '#!'*bash*|'#!'*/sh|'#!'*/sh\ *|'#!'*env\ sh*) return 0 ;;
  esac
  return 1
}

while IFS= read -r -d '' CANDIDATE_FILE; do
  if is_shell "${CANDIDATE_FILE}"; then
    check_shell "${CANDIDATE_FILE}"
  fi
done < <(find "${ROOT_DIR}" -path "${ROOT_DIR}/.git" -prune -o -type f -print0)

# 只查 JSON 语法是不够的：0.1.0 的 marketplace.json 语法完全合法、
# 却因为缺 owner 字段而**装不上**（claude plugin marketplace add 报 Invalid schema）。
# 一份装不上的清单通过了校验 —— 必填字段必须单独查。
# eval 的判决器自己也要被测：首版 _preflight 的解析器把 Version 找丢了，
# 恒报「没跑起来」—— 那是安全结局，不会吵到人，eval 会安静地一直没用。
if ! /bin/bash "${ROOT_DIR}/evals/_preflight.sh" --selftest >/dev/null 2>&1; then
  fail "_preflight 自检未通过"
fi

if ! python3 "${ROOT_DIR}/scripts/check-manifests.py" "${ROOT_DIR}"; then
  fail "清单必填字段校验未通过"
fi

if ! /bin/bash "${ROOT_DIR}/evals/propose-not-auto.sh" --selftest; then
  fail "propose-not-auto 自检未通过"
fi

if [ "${STATUS}" -ne 0 ]; then
  exit 1
fi

printf 'validate: ok\n'
