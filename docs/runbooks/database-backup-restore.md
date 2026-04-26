# Database Backup & Restore

## Backup Targets

| Database | Container | Size Est. | Destination |
|----------|-----------|-----------|-------------|
| Plane PostgreSQL | docker-plane-db-1 | ~50MB | QNAP /share/backup/plane/ |
| SQLite analytics | host process | <1MB | Git repo |
| Obot data | obot container | ~10MB | QNAP /share/backup/obot/ |
| LiteLLM DB | litellm-gateway | N/A (file-mode) | — |
| Vault data | vault-server | <1MB | Encrypted backup |

## Plane PostgreSQL

```bash
# Backup (creates compressed SQL dump)
docker exec docker-plane-db-1 pg_dump -U plane plane | \
  gzip > /tmp/plane-$(date +%Y%m%d-%H%M).sql.gz

# Verify dump integrity
gzip -t /tmp/plane-$(date +%Y%m%d)*.sql.gz && echo "Backup OK"

# Copy to QNAP
rsync -avz /tmp/plane-*.sql.gz admin@192.168.10.201:/share/backup/plane/
# Clean up local copy
rm /tmp/plane-$(date +%Y%m%d)*.sql.gz
```

```bash
# Restore
# CAUTION: This will OVERWRITE the current database
gunzip < /path/to/plane-YYYYMMDD.sql.gz | \
  docker exec -i docker-plane-db-1 psql -U plane plane
```

## Obot Audit Log

```bash
# Backup audit log
docker exec obot cat /data/audit.log | \
  gzip > /tmp/obot-audit-$(date +%Y%m%d).log.gz
rsync -avz /tmp/obot-audit-*.log.gz admin@192.168.10.201:/share/backup/obot/
```

## Vault (Dev Mode — Manual)

⚠️ Vault in dev mode does NOT persist data across container restarts.
All secrets are lost on restart. To prevent this:

```bash
# Option 1: Back up secrets before restart
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$(grep VAULT_ROOT_TOKEN ~/control-center-stack/stacks/vault/.env | cut -d= -f2-)

# List and dump all secrets
vault kv list secret/ 2>/dev/null
vault kv get -format=json secret/plane/api_token > /tmp/vault-backup.json

# Option 2: Migrate to production mode Vault with file storage
# Requires: vault.hcl config with file backend + unseal key management
```

## SQLite Analytics

```bash
# Backup
cp /Users/admin/repos/integrated-ai-platform/data/platform_analytics.db \
   /Users/admin/repos/integrated-ai-platform/data/platform_analytics.db.bak

# Also committed to git if small enough:
git add data/platform_analytics.db
git commit -m "chore: backup analytics DB snapshot"
```

## Automated Daily Backup (cron)

Add to crontab (`crontab -e`):

```cron
# Daily Plane DB backup at 2 AM
0 2 * * * docker exec docker-plane-db-1 pg_dump -U plane plane | gzip > /tmp/plane-$(date +\%Y\%m\%d).sql.gz && rsync -az /tmp/plane-$(date +\%Y\%m\%d).sql.gz admin@192.168.10.201:/share/backup/plane/ && rm /tmp/plane-$(date +\%Y\%m\%d).sql.gz

# Weekly Obot audit backup on Sundays at 3 AM
0 3 * * 0 docker exec obot cat /data/audit.log | gzip > /tmp/obot-audit-$(date +\%Y\%m\%d).log.gz && rsync -az /tmp/obot-audit-*.log.gz admin@192.168.10.201:/share/backup/obot/
```
