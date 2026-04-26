# Arr Stack Migration — QNAP to Mac Mini

**Status:** PLANNED — services still running on QNAP .201  
**Target date:** Phase 5, Week 1

## Current State (pre-migration)

| Service | Current Host | Port | Status |
|---------|-------------|------|--------|
| Sonarr | QNAP .201 | :8989 | ✅ Running |
| Radarr | QNAP .201 | :7878 | ✅ Running |
| Prowlarr | QNAP .201 | :9696 | ✅ Running |

Services are reachable at `http://192.168.10.201:PORT`.

## Target State (post-migration)

| Service | Target Host | Port | Config Storage |
|---------|------------|------|---------------|
| Sonarr | Mac Mini .145 | :8989 | Docker volume `sonarr-config` |
| Radarr | Mac Mini .145 | :7878 | Docker volume `radarr-config` |
| Prowlarr | Mac Mini .145 | :9696 | Docker volume `prowlarr-config` |

Media files remain on QNAP — only the app containers move.

## Migration Procedure

### Step 1: Backup from QNAP (run on QNAP via SSH)

```bash
ssh admin@192.168.10.201

docker exec sonarr tar czf /tmp/sonarr-backup.tar.gz -C /config .
docker exec radarr tar czf /tmp/radarr-backup.tar.gz -C /config .
docker exec prowlarr tar czf /tmp/prowlarr-backup.tar.gz -C /config .

docker cp sonarr:/tmp/sonarr-backup.tar.gz ~/
docker cp radarr:/tmp/radarr-backup.tar.gz ~/
docker cp prowlarr:/tmp/prowlarr-backup.tar.gz ~/
```

Copy to Mac Mini:
```bash
# Run from QNAP:
scp ~/sonarr-backup.tar.gz ~/radarr-backup.tar.gz ~/prowlarr-backup.tar.gz \
  admin@192.168.10.145:~/arr-backups/
```

### Step 2: Record API keys before migration

From each service web UI → Settings → General → copy API Key:
- Sonarr API key → add to `~/.env` or `docker/.env` as `SONARR_API_KEY`
- Radarr API key → `RADARR_API_KEY`
- Prowlarr API key → `PROWLARR_API_KEY`

### Step 3: Mount QNAP SMB shares on Mac Mini

NFS is not available (RPC timeout). Use SMB:

```bash
# Set credentials
export QNAP_SMB_USER=admin
export QNAP_SMB_PASS=<your-qnap-password>

# Mount
~/mount-qnap.sh

# Verify (note actual share names from QNAP File Station)
ls /Volumes/qnap-media
ls /Volumes/qnap-downloads
```

If share names differ from "Media"/"Downloads", edit `~/mount-qnap.sh` accordingly.

### Step 4: Deploy Arr stack on Mac Mini

```bash
cd ~/control-center-stack/stacks/arr-stack
docker compose up -d

# Wait for startup (linuxserver images take ~30s)
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "sonarr|radarr|prowlarr"
```

### Step 5: Restore configurations

```bash
cd ~/arr-backups

# Sonarr
docker cp sonarr-backup.tar.gz sonarr:/tmp/
docker exec sonarr sh -c 'cd /config && tar xzf /tmp/sonarr-backup.tar.gz'
docker restart sonarr

# Radarr
docker cp radarr-backup.tar.gz radarr:/tmp/
docker exec radarr sh -c 'cd /config && tar xzf /tmp/radarr-backup.tar.gz'
docker restart radarr

# Prowlarr
docker cp prowlarr-backup.tar.gz prowlarr:/tmp/
docker exec prowlarr sh -c 'cd /config && tar xzf /tmp/prowlarr-backup.tar.gz'
docker restart prowlarr
```

### Step 6: Update root folder paths

In each service web UI, update root folders to match QNAP mount points:
- Sonarr → Settings → Media Management → Root Folders → `/media/TV` (or actual path)
- Radarr → Settings → Media Management → Root Folders → `/media/Movies`
- Download client paths → `/downloads`

### Step 7: Verify before cutover

```bash
# Test Prowlarr indexers (UI: Indexers → Test All)
# Test a Sonarr search (Manual Search on a show)
# Test a Radarr search (Manual Search on a movie)
```

### Step 8: Cut over (AFTER verification)

```bash
# Stop QNAP Arr services (run on QNAP)
ssh admin@192.168.10.201 "docker stop sonarr radarr prowlarr"

# Update connector config on Mac Mini
sed -i '' 's/192\.168\.10\.201:\(8989\|7878\|9696\)/192.168.10.145:\1/g' \
  ~/repos/integrated-ai-platform/config/connectors.yaml \
  ~/repos/integrated-ai-platform/config/domains.yaml
```

## Rollback Procedure

If migration fails:
```bash
# 1. Stop Mac Mini Arr stack
cd ~/control-center-stack/stacks/arr-stack && docker compose down

# 2. Restart QNAP services
ssh admin@192.168.10.201 "docker start sonarr radarr prowlarr"

# 3. Revert connector URLs
sed -i '' 's/192\.168\.10\.145:\(8989\|7878\|9696\)/192.168.10.201:\1/g' \
  ~/repos/integrated-ai-platform/config/connectors.yaml \
  ~/repos/integrated-ai-platform/config/domains.yaml
```

## Post-migration: Update Homarr widgets

Add Arr stack widgets in Homarr (http://192.168.10.145:7575):
1. Sonarr → http://192.168.10.145:8989 + API key
2. Radarr → http://192.168.10.145:7878 + API key
3. Prowlarr → http://192.168.10.145:9696 + API key
4. Calendar widget (shows upcoming releases)
