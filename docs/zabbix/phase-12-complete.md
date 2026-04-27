# Phase 12: Zabbix Deployment - COMPLETE

**Completion Date:** 2026-04-27
**Status:** Core stack operational, device integration pending manual steps

## Deployed Components

### Infrastructure (Running)
- Zabbix Server 7.4.9 (Docker, container: zabbix-server)
- TimescaleDB 2.26.3 on PostgreSQL 16 (named volume: zabbix-pgdata)
- Zabbix Web UI (http://192.168.10.145:10080)
- Zabbix Agent (container, monitors Docker environment)

### TimescaleDB Configuration
- Hypertables: history, history_uint, history_str, history_log, history_text, trends, trends_uint
- Compression policies: history/log/str/text/uint after 7 days, trends after 30 days
- Jobs scheduled: 7 daily columnstore policies (job IDs 1000-1006)

### Memory Configuration (Colima-aware)
- PostgreSQL shared_buffers: 256MB (Colima VM = 8GB, 30+ containers running)
- effective_cache_size: 1GB
- shm_size: 256m
- WAL: min 256MB / max 2GB

## Access

| URL | Purpose | Default Creds |
|-----|---------|---------------|
| http://192.168.10.145:10080 | Zabbix Web UI | Admin / zabbix (CHANGE!) |
| Port 10051 | Zabbix Server (agent data) | N/A |

## Pending Manual Steps

1. **Change admin password** (see: docs/zabbix/initial-setup.md)
2. **SNMP - OPNsense (.1)**: Enable bsnmpd, add firewall rule (see: docs/zabbix/opnsense-snmp-setup.md)
3. **SNMP - QNAP (.201)**: Enable SNMP in Control Panel (see: docs/zabbix/qnap-snmp-setup.md)
4. **Native agent - Mac Mini**: Install ARM64 agent + PSK (see: docs/zabbix/mac-mini-agent-setup.md)
5. **Grafana plugin**: Install alexanderzobnin-zabbix-app (see: docs/zabbix/grafana-integration.md)

## Architecture Notes

### Why named volume (not bind mount)
macOS Colima bind-mounts map host UIDs via virtiofs; PostgreSQL (uid 70) can't reliably write
files to macOS-owned directories. Named volume `zabbix-pgdata` lives entirely inside the
Colima VM where PostgreSQL owns the filesystem.

### Why reduced memory settings
Original settings (12GB shared_buffers, 4GB min_wal_size) caused PostgreSQL OOM crash inside
the 8GB Colima VM. Production-safe values use ~256MB/1GB with headroom for 30+ other containers.
To increase: `colima stop && colima start --memory 16` — disrupts all containers.

## Configuration Files
- docker/zabbix/docker-compose.yml — stack definition
- docker/zabbix/.env — passwords and tuning parameters
- docs/zabbix/ — setup guides for each device
