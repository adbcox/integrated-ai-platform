#!/usr/bin/env bash
# iap-regression-probe-trigger.sh
# Wrapper invoked by the trigger watcher when the control-plane
# requests a regression-probe run. The probe reads ~/.vault-token
# (root) and shells into vault-server / other containers — none of
# which we expose to the control-plane container.
#
# Reads params JSON from stdin: {"gate_id": "<id>"}.
# Prints structured JSON result to stdout.

set -uo pipefail

REPO_ROOT="/Users/admin/repos/integrated-ai-platform"
PROBE_SCRIPT="${REPO_ROOT}/docs/phase-13/h1-regression-probe.sh"

if [ ! -x "${PROBE_SCRIPT}" ] && [ ! -r "${PROBE_SCRIPT}" ]; then
  printf '{"status":"error","reason":"probe script missing"}\n'
  exit 1
fi

# Parse gate_id from stdin params JSON (default: "block-2.5")
params_json=$(cat)
gate_id=$(printf '%s' "${params_json}" | python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read() or '{}')
except Exception:
    d = {}
print(d.get('gate_id', 'block-2.5'))
")

started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
log_file=$(mktemp -t iap-regression-XXXXXXXX.log)

bash "${PROBE_SCRIPT}" "${gate_id}" >"${log_file}" 2>&1
exit_code=$?

finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Tally PASS/FAIL/WARN from output
pass=$(grep -c '✅' "${log_file}" 2>/dev/null || echo 0)
fail=$(grep -c '❌' "${log_file}" 2>/dev/null || echo 0)
warn=$(grep -c '⚠️' "${log_file}" 2>/dev/null || echo 0)

tail_b64=$(tail -c 8192 "${log_file}" | base64 -b 0 2>/dev/null || tail -c 8192 "${log_file}" | base64 -w 0)

cat <<EOF
{"gate_id":"${gate_id}","started_at":"${started_at}","finished_at":"${finished_at}","exit_code":${exit_code},"counts":{"pass":${pass},"fail":${fail},"warn":${warn}},"log_tail_b64":"${tail_b64}"}
EOF

rm -f "${log_file}"
exit ${exit_code}
