#!/usr/bin/env bash
# Parse docs/tech/ops-calendar.md ## db-restore schedule; exit 1 in warn/overdue window.
# ponytail: bash 3.2-compatible (macOS /bin/bash); upgrade path = require bash 4+ & mapfile
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAL="${ROOT}/docs/tech/ops-calendar.md"
SECTION="${1:-db-restore}"

if [[ ! -f "$CAL" ]]; then
  echo "calendar not found: $CAL" >&2
  exit 2
fi

KV="$(awk -v sec="## ${SECTION}" '
  $0 == sec {p=1; next}
  p && /^## / {exit}
  p && /^- [a-z_]+:/ {
    key=$2; sub(/:$/,"",key);
    val=$0; sub(/^- [^:]+:[[:space:]]*/,"",val);
    print key "=" val
  }
' "$CAL")"

get() {
  local k="$1"
  local line
  while IFS= read -r line; do
    case "$line" in
      "$k="*) echo "${line#*=}"; return 0 ;;
    esac
  done <<EOF
$KV
EOF
  return 1
}

next_due="$(get next_due || true)"
warn_days="$(get warn_days || true)"
last_run="$(get last_run || true)"
runbook="$(get runbook || true)"

if [[ -z "${next_due}" || -z "${warn_days}" ]]; then
  echo "missing next_due or warn_days under ## ${SECTION} in ${CAL}" >&2
  exit 2
fi

to_epoch() {
  local d="$1"
  if date -j -f '%Y-%m-%d' "$d" '+%s' >/dev/null 2>&1; then
    date -j -f '%Y-%m-%d' "$d" '+%s'
  else
    date -d "$d" '+%s'
  fi
}

today="$(date '+%Y-%m-%d')"
today_e="$(to_epoch "$today")"
due_e="$(to_epoch "$next_due")"
warn_e=$((due_e - warn_days * 86400))
days_left=$(( (due_e - today_e) / 86400 ))

rb_path="${runbook:-./db-restore.md}"
rb_path="${rb_path#./}"

echo "section=${SECTION}"
echo "last_run=${last_run:-unknown}"
echo "next_due=${next_due}"
echo "warn_days=${warn_days}"
echo "today=${today}"
echo "days_left=${days_left}"
echo "runbook=${ROOT}/docs/tech/${rb_path}"

if (( today_e >= warn_e )); then
  if (( today_e > due_e )); then
    echo "STATUS=OVERDUE — run the restore runbook and update the calendar." >&2
  else
    echo "STATUS=WARN — within ${warn_days} days of next_due." >&2
  fi
  echo "See: ${ROOT}/docs/tech/ops-calendar.md" >&2
  exit 1
fi

echo "STATUS=OK"
exit 0
