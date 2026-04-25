#!/usr/bin/env bash
# Docker cleanup script
# Removes: exited openhands-runtime containers, one-time init containers,
#           Zabbix monitoring stack (replaced by Grafana/VictoriaMetrics).
# Keeps:   Plane CE (7 containers), OpenHands app, observability stack.
#
# Run dry-run first: bash scripts/cleanup_docker.sh --dry-run
# Run for real:      bash scripts/cleanup_docker.sh

set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  echo "=== DRY RUN MODE — no changes will be made ==="
fi

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] $*"
  else
    echo ">> $*"
    eval "$@"
  fi
}

echo ""
echo "=== STEP 1: Remove exited openhands-runtime containers ==="
EXITED_OPENHANDS=$(docker ps -a --filter "name=openhands-runtime" --filter "status=exited" --format "{{.Names}}" 2>/dev/null)
CREATED_OPENHANDS=$(docker ps -a --filter "name=openhands-runtime" --filter "status=created" --format "{{.Names}}" 2>/dev/null)
ALL_OPENHANDS_DEAD="$EXITED_OPENHANDS $CREATED_OPENHANDS"

if [[ -z "${ALL_OPENHANDS_DEAD// /}" ]]; then
  echo "  Nothing to remove."
else
  for name in $ALL_OPENHANDS_DEAD; do
    run "docker rm \"$name\""
  done
fi

echo ""
echo "=== STEP 2: Remove one-time init containers (Plane migrate + minio-setup) ==="
for name in docker-plane-migrate-1 docker-plane-minio-setup-1 sweet_gould; do
  if docker ps -a --format "{{.Names}}" | grep -q "^${name}$"; then
    run "docker rm \"$name\""
  else
    echo "  $name not found, skipping."
  fi
done

echo ""
echo "=== STEP 3: Stop and remove Zabbix monitoring stack ==="
echo "  Rationale: Grafana + VictoriaMetrics covers application metrics;"
echo "  Zabbix is redundant for this AI platform workload."
ZABBIX_CONTAINERS="zabbix-web zabbix-server zabbix-db zabbix-agent"
for name in $ZABBIX_CONTAINERS; do
  if docker ps -a --format "{{.Names}}" | grep -q "^${name}$"; then
    run "docker stop \"$name\" && docker rm \"$name\""
  else
    echo "  $name not found, skipping."
  fi
done

echo ""
echo "=== STEP 4: Remove unused Docker images ==="
echo "  (Only removes images with no running containers referencing them)"
run "docker image prune -a -f"

echo ""
echo "=== STEP 5: Remove unused build cache ==="
run "docker buildx prune -f"

echo ""
echo "=== Final container state ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

echo ""
echo "=== Disk usage after cleanup ==="
docker system df
