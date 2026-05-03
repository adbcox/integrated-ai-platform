#!/usr/bin/env bash
# D-17-51 WP-06 verification helper.
# Prints launchctl status + heartbeat recency for com.iap.* agents.

set -euo pipefail

uid="${1:-$(id -u)}"
now_epoch=$(date +%s)
logs_dir="/Users/admin/.platform-logs"

budget_sec() {
  case "$1" in
    com.iap.arr-apikey-sweep) echo 5400 ;;      # 1h + grace
    com.iap.buildarr-sync) echo 108000 ;;       # 30h
    com.iap.backup) echo 129600 ;;              # 36h
    com.iap.docker-events) echo 3600 ;;         # 1h
    com.iap.strava-refresh) echo 7200 ;;        # 2h
    com.iap.strava-sync) echo 93600 ;;          # 26h
    com.iap.vault-audit-rotate) echo 93600 ;;
    com.iap.vault-audit-archive) echo 93600 ;;
    com.iap.caddy-unbound-parity) echo 93600 ;;
    com.iap.platform-registry) echo 93600 ;;
    *) echo 86400 ;;
  esac
}

heartbeat_file() {
  case "$1" in
    com.iap.arr-apikey-sweep) echo "$logs_dir/arr-apikey-sweep.heartbeat" ;;
    com.iap.buildarr-sync) echo "$logs_dir/buildarr-sync.heartbeat" ;;
    com.iap.backup) echo "$logs_dir/backup.heartbeat" ;;
    com.iap.docker-events) echo "$logs_dir/docker-events.heartbeat" ;;
    com.iap.strava-refresh) echo "$logs_dir/strava-refresh.heartbeat" ;;
    com.iap.strava-sync) echo "$logs_dir/strava-sync.heartbeat" ;;
    com.iap.vault-audit-rotate) echo "$logs_dir/vault-audit-rotate.heartbeat" ;;
    com.iap.vault-audit-archive) echo "$logs_dir/vault-audit-archive.heartbeat" ;;
    com.iap.caddy-unbound-parity) echo "$logs_dir/caddy-unbound-parity.heartbeat" ;;
    com.iap.platform-registry) echo "$logs_dir/platform-registry.heartbeat" ;;
    *) echo "$logs_dir/${1#com.iap.}.heartbeat" ;;
  esac
}

printf "%-40s %-10s %-10s %-12s %-10s %-12s\n" "LABEL" "LOADED" "STATE" "LAST_EXIT" "HB_AGE_H" "HB_BUDGET"
printf "%-40s %-10s %-10s %-12s %-10s %-12s\n" "-----" "------" "-----" "---------" "--------" "---------"

shopt -s nullglob
for plist in /Users/admin/Library/LaunchAgents/com.iap*.plist; do
  label=$(plutil -extract Label raw -o - "$plist" 2>/dev/null || basename "$plist" .plist)

  svc=$(launchctl print "user/$uid/$label" 2>/dev/null || true)
  if [ -z "$svc" ]; then
    loaded="no"
    state="-"
    last_exit="-"
  else
    loaded="yes"
    state=$(printf "%s\n" "$svc" | awk -F'= ' '/\tstate =/{print $2; exit}')
    last_exit=$(printf "%s\n" "$svc" | awk -F'= ' '/last exit code =/{print $2; exit}')
    [ -n "$state" ] || state="?"
    [ -n "$last_exit" ] || last_exit="?"
  fi

  hb=$(heartbeat_file "$label")
  bsec=$(budget_sec "$label")
  if [ -f "$hb" ]; then
    hb_epoch=$(stat -f %m "$hb")
    age_sec=$((now_epoch - hb_epoch))
    age_h=$(awk -v s="$age_sec" 'BEGIN{printf "%.1f", s/3600}')
    bud_h=$(awk -v s="$bsec" 'BEGIN{printf "%.1f", s/3600}')
    budget_status="ok"
    if [ "$age_sec" -gt "$bsec" ]; then budget_status="stale"; fi
    hb_disp="$age_h/$budget_status"
  else
    hb_disp="missing"
    bud_h=$(awk -v s="$bsec" 'BEGIN{printf "%.1f", s/3600}')
  fi

  printf "%-40s %-10s %-10s %-12s %-10s %-12s\n" "$label" "$loaded" "$state" "$last_exit" "$hb_disp" "$bud_h h"
done
