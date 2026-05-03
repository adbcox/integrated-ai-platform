#!/usr/bin/env bash
# D-17-51 — verify com.iap LaunchDaemons in system domain + heartbeat recency.

set -euo pipefail

now_epoch=$(date +%s)
LOG_DIR="/Users/admin/Library/Logs/iap"

budget_sec() {
  case "$1" in
    com.iap.arr-apikey-sweep) echo 5400 ;;
    com.iap.buildarr-sync) echo 108000 ;;
    com.iap.backup) echo 129600 ;;
    com.iap.docker-events) echo 3600 ;;
    com.iap.strava-refresh) echo 7200 ;;
    com.iap.strava-sync) echo 93600 ;;
    com.iap.vault-audit-rotate) echo 93600 ;;
    com.iap.vault-audit-archive) echo 93600 ;;
    com.iap.caddy-unbound-parity) echo 93600 ;;
    com.iap.platform-registry) echo 93600 ;;
    *) echo 86400 ;;
  esac
}

heartbeat_file() {
  # Daemon-migrated path first; fallback to legacy path for transition reads.
  case "$1" in
    com.iap.arr-apikey-sweep) echo "$LOG_DIR/arr-apikey-sweep.heartbeat|/Users/admin/.platform-logs/arr-apikey-sweep.heartbeat" ;;
    com.iap.buildarr-sync) echo "$LOG_DIR/buildarr-sync.heartbeat|/Users/admin/.platform-logs/buildarr-sync.heartbeat" ;;
    com.iap.backup) echo "$LOG_DIR/backup.heartbeat|/Users/admin/.platform-logs/backup.heartbeat" ;;
    com.iap.docker-events) echo "$LOG_DIR/docker-events.heartbeat|/Users/admin/.platform-logs/docker-events.heartbeat" ;;
    com.iap.strava-refresh) echo "$LOG_DIR/strava-refresh.heartbeat|/Users/admin/.platform-logs/strava-refresh.heartbeat" ;;
    com.iap.strava-sync) echo "$LOG_DIR/strava-sync.heartbeat|/Users/admin/.platform-logs/strava-sync.heartbeat" ;;
    com.iap.vault-audit-rotate) echo "$LOG_DIR/vault-audit-rotate.heartbeat|/Users/admin/.platform-logs/vault-audit-rotate.heartbeat" ;;
    com.iap.vault-audit-archive) echo "$LOG_DIR/vault-audit-archive.heartbeat|/Users/admin/.platform-logs/vault-audit-archive.heartbeat" ;;
    com.iap.caddy-unbound-parity) echo "$LOG_DIR/caddy-unbound-parity.heartbeat|/Users/admin/.platform-logs/caddy-unbound-parity.heartbeat" ;;
    com.iap.platform-registry) echo "$LOG_DIR/platform-registry.heartbeat|/Users/admin/.platform-logs/platform-registry.heartbeat" ;;
    *) echo "$LOG_DIR/${1#com.iap.}.heartbeat|/Users/admin/.platform-logs/${1#com.iap.}.heartbeat" ;;
  esac
}

pick_existing_file() {
  IFS='|' read -r a b <<< "$1"
  if [ -f "$a" ]; then echo "$a"; return; fi
  if [ -f "$b" ]; then echo "$b"; return; fi
  echo ""
}

printf "%-40s %-8s %-10s %-10s %-14s %-12s\n" "LABEL" "LOADED" "STATE" "EXIT" "HEARTBEAT_AGE" "BUDGET"
printf "%-40s %-8s %-10s %-10s %-14s %-12s\n" "-----" "------" "-----" "----" "-------------" "------"

shopt -s nullglob
for p in /Library/LaunchDaemons/com.iap*.plist; do
  label=$(plutil -extract Label raw -o - "$p" 2>/dev/null || basename "$p" .plist)

  svc=$(launchctl print "system/$label" 2>/dev/null || true)
  if [ -z "$svc" ]; then
    loaded="no"; state="-"; exitc="-"
  else
    loaded="yes"
    state=$(printf "%s\n" "$svc" | awk -F'= ' '/\tstate =/{print $2; exit}')
    exitc=$(printf "%s\n" "$svc" | awk -F'= ' '/last exit code =/{print $2; exit}')
    [ -n "$state" ] || state="?"
    [ -n "$exitc" ] || exitc="?"
  fi

  hb=$(pick_existing_file "$(heartbeat_file "$label")")
  bsec=$(budget_sec "$label")
  if [ -n "$hb" ]; then
    hb_epoch=$(stat -f %m "$hb")
    age_sec=$((now_epoch - hb_epoch))
    age_h=$(awk -v s="$age_sec" 'BEGIN{printf "%.1fh", s/3600}')
    status="ok"
    if [ "$age_sec" -gt "$bsec" ]; then status="stale"; fi
    hb_disp="$age_h/$status"
  else
    hb_disp="missing"
  fi
  bud_h=$(awk -v s="$bsec" 'BEGIN{printf "%.1fh", s/3600}')

  printf "%-40s %-8s %-10s %-10s %-14s %-12s\n" "$label" "$loaded" "$state" "$exitc" "$hb_disp" "$bud_h"
done
