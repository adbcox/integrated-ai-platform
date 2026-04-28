# What Changed in the Last 24 Hours — Runbook

**When to use**: Investigating a regression, anomaly, or after-the-fact debugging. Single source of truth for "what happened recently".

## Git history

```bash
cd ~/repos/integrated-ai-platform
git log --since="24 hours ago" --all --pretty=format:'%h %ai %s' | head -30
```

Includes branches, tags, all refs.

## Vault audit log

```bash
docker exec vault-server tail -200 /vault/logs/audit.log | \
  jq -c 'select(.time > "'"$(date -u -v-1d +%FT%TZ)"'")' | wc -l
# Count of events in last 24h

# Sample recent events:
docker exec vault-server tail -200 /vault/logs/audit.log | \
  jq -c 'select(.time > "'"$(date -u -v-1d +%FT%TZ)"'") | {time, type, op: .request.operation, path: .request.path}' | tail -30
```

## Docker events

```bash
tail -200 /Users/admin/.platform-logs/docker-events.log | \
  jq -c 'select(.time > '"$(date -u -v-1d +%s)"') | {time: .time, type, action, name: .Actor.Attributes.name}' | tail -50
```

(`docker-events.log` populated by `com.adbcox.docker-events.plist` launchd job; see §12 docs.)

## Container restart events

```bash
docker ps -a --format 'table {{.Names}}\t{{.RunningFor}}\t{{.Status}}' | \
  awk 'NR==1 || /minutes ago|hour/'
# Anything started <24h ago surfaces here
```

## Service-registry diff

```bash
cd ~/repos/integrated-ai-platform
git log --since="24 hours ago" -- config/service-registry.yaml --pretty=format:'%h %ai %s'
git diff "@{1 day ago}" -- config/service-registry.yaml
```

## Phase document changes

```bash
git log --since="24 hours ago" -- docs/phase-*/  --pretty=format:'%ai %s'
```

## Restic backup status

```bash
# Last snapshot timestamp:
ROLE_ID=$(cat ~/.vault-approle/backup/role-id)
SECRET_ID=$(cat ~/.vault-approle/backup/secret-id)
TOKEN=$(curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
  http://localhost:8200/v1/auth/approle/login | jq -r '.auth.client_token')
RESTIC_PASS=$(curl -sH "X-Vault-Token: $TOKEN" http://localhost:8200/v1/secret/data/restic/backup | jq -r '.data.data.password')
RESTIC_PASSWORD="$RESTIC_PASS" restic -r s3:http://192.168.10.201:9000/backups snapshots latest
```

## Vault audit rotation

```bash
ls -la /Users/admin/control-center-stack/stacks/vault/logs/ 2>/dev/null
# Check for recent rotated files
```

## launchd plist firing history

```bash
log show --predicate 'process == "launchd"' --last 24h --style compact 2>&1 | \
  grep -E 'com\.(adbcox|iap)\.' | head -20
```

## Output one-pager

For incident response, run all of the above in sequence and pipe to a temp file:

```bash
exec > /tmp/last-24h-$(date +%Y%m%d-%H%M).txt 2>&1
echo "=== Git ==="; git log --since="24 hours ago" --all --pretty=format:'%h %ai %s'
echo; echo "=== Vault audit ==="; docker exec vault-server tail -100 /vault/logs/audit.log | tail -30
# ... etc
```
