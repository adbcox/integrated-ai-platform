# QNAP NAS — Media Storage + Backup

## Hardware

| Spec | Value |
|------|-------|
| IP | 192.168.10.201 |
| Hostname | qnap.local (DNS) |
| Role | NAS: media storage, platform backups, Plex server |
| Web UI | http://192.168.10.201:8080 |
| API | http://192.168.10.201:8080/api/v1 |

## Services

| Service | Port | Purpose |
|---------|------|---------|
| QNAP Web UI | 8080 (HTTP) | NAS management |
| QNAP Web UI | 5000 (alternate) | NAS management |
| Plex Media Server | 32400 | Media streaming |
| Sonarr | 8989 | TV series automation |
| Radarr | 7878 | Movie automation |
| Prowlarr | 9117 | Indexer proxy for Sonarr/Radarr |

## Storage Layout

| Share | Purpose | Path |
|-------|---------|------|
| /media | Plex media library (TV, Movies, Music) | `/share/media` |
| /backup | Platform backups (Plane DB, config) | `/share/backup` |
| /data | General data, artifacts | `/share/data` |
| /downloads | Active download staging | `/share/downloads` |

## API Integration

The QNAP connector (`connectors/qnap.py`, `framework/qnap_client.py`) provides:
- Disk health monitoring
- Storage utilization metrics
- NAS system info

Connection config in `config/connectors.yaml`:
```yaml
qnap:
  host: 192.168.10.201
  port: 8080
  username: admin
  # password: set QNAP_PASSWORD in docker/.env
```

## Media Stack Integration

Sonarr/Radarr/Prowlarr are configured on the NAS. The platform's media domain
(`domains/media.py`, `connectors/arr_stack.py`) integrates with them via API:
- Sonarr API: `http://192.168.10.201:8989/api/v3`
- Radarr API: `http://192.168.10.201:7878/api/v3`
- Prowlarr API: `http://192.168.10.201:9117/api/v1`
- Plex API: `http://192.168.10.201:32400` (needs Plex token)

Keys are stored in `docker/.env`: `SONARR_API_KEY`, `RADARR_API_KEY`, `PROWLARR_API_KEY`.

## Backup Procedures

The QNAP is the backup destination for critical platform data:

```bash
# Plane postgres backup → QNAP
docker exec docker-plane-db-1 pg_dump -U plane plane | \
  gzip > /tmp/plane-$(date +%Y%m%d).sql.gz
# Then rsync to QNAP:
rsync -avz /tmp/plane-*.sql.gz admin@192.168.10.201:/share/backup/plane/

# Obot audit log backup
docker exec obot cat /data/audit.log | \
  gzip > /tmp/obot-audit-$(date +%Y%m%d).log.gz
rsync -avz /tmp/obot-audit-*.log.gz admin@192.168.10.201:/share/backup/obot/
```

## vmagent Monitoring

The observability stack scrapes QNAP via node-exporter (if installed) or via
QNAP SNMP. See `docker/vmagent-config/scrape.yml` for current targets.
