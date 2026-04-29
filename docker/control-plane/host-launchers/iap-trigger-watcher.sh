#!/usr/bin/env bash
# iap-trigger-watcher.sh
# Watches /Users/admin/iap-triggers/ for trigger files written by the
# control-plane container. Validates timestamp + nonce, executes the
# matching iap-<action>-trigger.sh, writes structured result back.
#
# Loaded by ~/Library/LaunchAgents/com.iap.control-plane.trigger-watcher.plist.
#
# Block 2.5 D8 — nonce + timestamp anti-replay protocol.

set -uo pipefail

TRIGGER_DIR="/Users/admin/iap-triggers"
RESULTS_DIR="${TRIGGER_DIR}/results"
NONCE_CACHE="${TRIGGER_DIR}/.nonce-cache"     # space-separated nonces, max 5min old
LOG_FILE="${TRIGGER_DIR}/watcher.log"
POLL_INTERVAL=1
TIMESTAMP_SKEW=30        # seconds
NONCE_TTL=300            # seconds

# Allowlist: action -> wrapper path. Installed to /Users/admin/iap-launchers/
# (operator-owned, no sudo required to refresh).
LAUNCHER_DIR="/Users/admin/iap-launchers"
ALLOWED_BACKUP="${LAUNCHER_DIR}/iap-backup-trigger.sh"
ALLOWED_REGRESSION="${LAUNCHER_DIR}/iap-regression-probe-trigger.sh"
ALLOWED_ROTATE="${LAUNCHER_DIR}/iap-credential-rotate-trigger.sh"

mkdir -p "${TRIGGER_DIR}" "${RESULTS_DIR}"
chmod 0700 "${TRIGGER_DIR}" "${RESULTS_DIR}"
touch "${NONCE_CACHE}" "${LOG_FILE}"

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "${LOG_FILE}"
}

# Nonce cache is space-separated "<nonce>:<unix_ts>" pairs.
nonce_recently_seen() {
  local nonce="$1"
  local now
  now=$(date +%s)
  local kept=""
  local seen=0

  while read -r pair; do
    [ -z "${pair}" ] && continue
    local n="${pair%%:*}"
    local t="${pair##*:}"
    if [ -z "${t}" ] || [ "${t}" -lt "$((now - NONCE_TTL))" ]; then
      continue   # expired
    fi
    if [ "${n}" = "${nonce}" ]; then
      seen=1
    fi
    kept="${kept}${pair}\n"
  done < "${NONCE_CACHE}"

  printf '%b' "${kept}" > "${NONCE_CACHE}"
  return $((1 - seen))   # 0 if seen, 1 if new
}

nonce_record() {
  local nonce="$1"
  local now
  now=$(date +%s)
  printf '%s:%s\n' "${nonce}" "${now}" >> "${NONCE_CACHE}"
}

# Reject a trigger: write rejection result, delete trigger file
reject() {
  local trigger_file="$1"
  local nonce="$2"
  local reason="$3"
  log "REJECT ${trigger_file##*/}: ${reason}"
  if [ -n "${nonce}" ]; then
    cat > "${RESULTS_DIR}/${nonce}.rejected.json" <<EOF
{"nonce":"${nonce}","reason":"${reason}","ts":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
    chmod 0600 "${RESULTS_DIR}/${nonce}.rejected.json"
  fi
  rm -f "${trigger_file}"
}

# Execute a validated trigger
execute() {
  local trigger_file="$1"
  local nonce="$2"
  local action="$3"
  local params="$4"

  local wrapper=""
  case "${action}" in
    backup-trigger)     wrapper="${ALLOWED_BACKUP}" ;;
    regression-probe)   wrapper="${ALLOWED_REGRESSION}" ;;
    credential-rotate)  wrapper="${ALLOWED_ROTATE}" ;;
    *)                  reject "${trigger_file}" "${nonce}" "unknown action ${action}"
                        return ;;
  esac

  if [ ! -x "${wrapper}" ]; then
    reject "${trigger_file}" "${nonce}" "wrapper ${wrapper} not installed"
    return
  fi

  local started_at finished_at exit_code
  local stdout_log="${RESULTS_DIR}/${nonce}.stdout"
  local stderr_log="${RESULTS_DIR}/${nonce}.stderr"
  started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  log "EXEC ${action} nonce=${nonce}"

  # Pass params JSON via stdin to the wrapper
  printf '%s' "${params}" | "${wrapper}" \
    > "${stdout_log}" 2> "${stderr_log}"
  exit_code=$?

  finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local stdout_tail stderr_tail
  stdout_tail=$(tail -c 4096 "${stdout_log}" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')
  stderr_tail=$(tail -c 4096 "${stderr_log}" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read()))')

  # Try to parse stdout as JSON; if so, embed; otherwise null
  local structured="null"
  if python3 -c 'import sys,json; json.load(sys.stdin)' < "${stdout_log}" 2>/dev/null; then
    structured=$(cat "${stdout_log}")
  fi

  cat > "${RESULTS_DIR}/${nonce}.json" <<EOF
{"nonce":"${nonce}","action":"${action}","exit_code":${exit_code},"started_at":"${started_at}","finished_at":"${finished_at}","stdout_tail":${stdout_tail},"stderr_tail":${stderr_tail},"structured":${structured}}
EOF
  chmod 0600 "${RESULTS_DIR}/${nonce}.json"
  rm -f "${stdout_log}" "${stderr_log}"
  rm -f "${trigger_file}"
  log "DONE  ${action} nonce=${nonce} exit=${exit_code}"
}

process_trigger() {
  local trigger_file="$1"

  # Parse JSON via python (jq not assumed installed)
  local parsed
  parsed=$(python3 - "${trigger_file}" <<'PY'
import json, sys
p = sys.argv[1]
try:
    with open(p) as fh:
        d = json.load(fh)
except Exception as e:
    print(f"ERR|invalid json: {e}")
    sys.exit(0)
n = d.get("nonce", "")
a = d.get("action", "")
t = d.get("timestamp", "")
import json as J
params = J.dumps(d.get("params", {}))
print(f"OK|{n}|{a}|{t}|{params}")
PY
)

  if [[ "${parsed}" == ERR\|* ]]; then
    reject "${trigger_file}" "" "${parsed#ERR|}"
    return
  fi

  local nonce action timestamp params
  IFS='|' read -r _ nonce action timestamp params <<< "${parsed}"

  # Validate timestamp window
  local trigger_ts now skew
  trigger_ts=$(python3 -c "
import sys, datetime
try:
    t = datetime.datetime.fromisoformat('${timestamp}'.replace('Z','+00:00'))
    print(int(t.timestamp()))
except Exception:
    print(0)
")
  now=$(date +%s)
  if [ "${trigger_ts}" -eq 0 ]; then
    reject "${trigger_file}" "${nonce}" "invalid timestamp"
    return
  fi
  skew=$(( now - trigger_ts ))
  if [ "${skew#-}" -gt "${TIMESTAMP_SKEW}" ]; then
    reject "${trigger_file}" "${nonce}" "timestamp skew ${skew}s exceeds ${TIMESTAMP_SKEW}s"
    return
  fi

  # Replay check
  if nonce_recently_seen "${nonce}"; then
    reject "${trigger_file}" "${nonce}" "nonce replay"
    return
  fi
  nonce_record "${nonce}"

  execute "${trigger_file}" "${nonce}" "${action}" "${params}"
}

log "watcher started (poll=${POLL_INTERVAL}s, skew=${TIMESTAMP_SKEW}s, nonce-ttl=${NONCE_TTL}s)"

while true; do
  for trigger_file in "${TRIGGER_DIR}"/*.json; do
    [ -e "${trigger_file}" ] || continue
    # Skip results subdir's files (shell glob doesn't recurse but be safe)
    case "${trigger_file}" in
      */results/*) continue ;;
    esac
    process_trigger "${trigger_file}"
  done
  sleep "${POLL_INTERVAL}"
done
