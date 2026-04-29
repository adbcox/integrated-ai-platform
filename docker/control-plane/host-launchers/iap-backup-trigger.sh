#!/usr/bin/env bash
# iap-backup-trigger.sh
# Wrapper invoked by the trigger watcher when the control-plane
# requests a manual Restic backup. Uses the existing backup AppRole
# at ~/.vault-approle/backup/ via scripts/backup.sh.
#
# Reads params JSON from stdin (currently no parameters consumed).
# Prints a JSON status object to stdout. Exit code propagates to
# the trigger result.

set -uo pipefail

REPO_ROOT="/Users/admin/repos/integrated-ai-platform"
BACKUP_SCRIPT="${REPO_ROOT}/scripts/backup.sh"
STATUS_FILE="/Users/admin/iap-triggers/backup-status.json"

if [ ! -x "${BACKUP_SCRIPT}" ]; then
  printf '{"status":"error","reason":"backup script not found at %s"}\n' "${BACKUP_SCRIPT}"
  exit 1
fi

started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
log_file=$(mktemp -t iap-backup-XXXXXXXX.log)

"${BACKUP_SCRIPT}" >"${log_file}" 2>&1
exit_code=$?

finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
tail_b64=$(tail -c 4096 "${log_file}" | base64 -b 0 2>/dev/null || tail -c 4096 "${log_file}" | base64 -w 0)

# Persist last-status for the GET /api/backups/last endpoint to read
cat > "${STATUS_FILE}" <<EOF
{"started_at":"${started_at}","finished_at":"${finished_at}","exit_code":${exit_code},"log_tail_b64":"${tail_b64}"}
EOF
chmod 0600 "${STATUS_FILE}"

# Echo same JSON to stdout (becomes structured payload in trigger result)
cat "${STATUS_FILE}"
rm -f "${log_file}"
exit ${exit_code}
