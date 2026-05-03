# Zabbix Operations Runbook

Canonical runbook for the Zabbix 7.4 + TimescaleDB stack on Mac Mini.
Consolidates the prior `docs/zabbix/` reference fragments (D-17-16 close).

**Deployed shape (verified 2026-05-03):**
- `zabbix-server` — `zabbix/zabbix-server-pgsql:alpine-7.4-latest`
- `zabbix-web` — `zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest` (UI on `:10080`)
- `zabbix-postgres` — `timescale/timescaledb:latest-pg16`
- `zabbix-agent` — `zabbix/zabbix-agent:alpine-7.4-latest` (container-side)
- Caddy front: `zabbix.internal` (per service-registry)

Phase 12 deployment retro lives at `docs/_archive/phase-12/` for incident
archaeology. Initial-deployment one-shots are out of scope for this
runbook (use `docs/runbooks/restart-services.md` + the registry).

---

## 1. Add a SNMP target (OPNsense, QNAP, generic SNMPv2)

The pattern is identical for any SNMPv2 device. Worked examples:
OPNsense at `192.168.10.1`, QNAP at `192.168.10.201`.

### 1.1 Enable SNMP on the device

**OPNsense (192.168.10.1)** — GUI: *Services → Net-SNMP* → Enable.
- Community: `zabbix_monitor`
- Allowed clients: `192.168.10.145`

Then add a firewall rule (*Firewall → Rules → LAN*): Pass UDP, source
`192.168.10.145`, destination port `161`, description "Zabbix SNMP
Monitoring".

**QNAP (192.168.10.201)** — *Control Panel → Network & File Services
→ SNMP*:
- Enable SNMP Service ✓
- SNMP Version: SNMPv2
- Community (Read): `zabbix_monitor`
- Allowed Clients: `192.168.10.145`

### 1.2 Verify reachability from the Zabbix server container

```bash
docker exec zabbix-server snmpwalk -v2c -c zabbix_monitor 192.168.10.1   system  # OPNsense
docker exec zabbix-server snmpwalk -v2c -c zabbix_monitor 192.168.10.201 system  # QNAP
```

### 1.3 Create the host in Zabbix UI

`https://zabbix.internal` (or `http://192.168.10.145:10080`) →
*Configuration → Hosts → Create host*:

| Field      | OPNsense                                       | QNAP                                  |
|------------|------------------------------------------------|---------------------------------------|
| Host name  | `OPNsense-Firewall`                            | `QNAP-NAS`                            |
| Templates  | `OPNsense by SNMP` (or `Network Generic SNMPv2`) | `Template Net QNAP NAS SNMPv2`      |
| Groups     | Network devices                                | Storage devices                       |
| Interface  | SNMP, `192.168.10.1`, port 161, SNMPv2         | SNMP, `192.168.10.201`, port 161, SNMPv2 |

In *Macros* tab: `{$SNMP_COMMUNITY}` = `zabbix_monitor`.

Latest data should populate within 5–10 minutes (volume status, disk
info, temperature, network for QNAP; firewall counters + interface
stats for OPNsense).

---

## 2. Mac Mini native agent (host-OS metrics)

The container-side `zabbix-agent` only sees the container environment.
For true macOS host metrics (SMC temperatures, host disk volumes,
Bonjour, etc.), install the native agent on Mac Mini.

```bash
curl -o /tmp/zabbix-agent.pkg \
  https://cdn.zabbix.com/zabbix/binaries/stable/7.4/7.4.0/zabbix_agent-7.4.0-macos-arm64-openssl.pkg
sudo installer -pkg /tmp/zabbix-agent.pkg -target /

# Generate PSK
openssl rand -hex 128 | sudo tee /usr/local/etc/zabbix/agent.psk
sudo chmod 600 /usr/local/etc/zabbix/agent.psk
PSK_VALUE=$(sudo cat /usr/local/etc/zabbix/agent.psk)
echo "PSK: $PSK_VALUE"   # used in Zabbix UI host config below
```

Agent config:

```bash
sudo tee /usr/local/etc/zabbix/zabbix_agentd.conf << 'EOF'
Server=192.168.10.145
ServerActive=192.168.10.145
Hostname=Mac-Mini-M4-Pro
ListenIP=192.168.10.145
ListenPort=10050
TLSConnect=psk
TLSAccept=psk
TLSPSKIdentity=Mac-Mini-M4-PSK
TLSPSKFile=/usr/local/etc/zabbix/agent.psk
LogFile=/var/log/zabbix/zabbix_agentd.log
EOF

sudo mkdir -p /var/log/zabbix
sudo launchctl load /Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist
```

In Zabbix UI: *Configuration → Hosts → Create host* — Host name
`Mac-Mini-M4-Pro`, template `macOS by Zabbix agent`, interface Agent
on `192.168.10.145:10050`. *Encryption* tab: PSK, identity
`Mac-Mini-M4-PSK`, value from the `PSK_VALUE` echo above.

**Mac Studio (.142) follow-on:** identical pattern, host name
`Mac-Studio-M3-Ultra`, PSK identity `Mac-Studio-M3-PSK`. Pending; see
CLAUDE.md "Heterogeneous Architecture" notes.

---

## 3. Grafana integration

```bash
docker exec grafana grafana-cli plugins install alexanderzobnin-zabbix-app
docker restart grafana
```

In Grafana (`https://grafana.internal` or `http://192.168.10.145:3030`):
*Configuration → Data sources → Add → Zabbix*:

- URL: `http://zabbix-web/api_jsonrpc.php` (Docker network DNS) — host-side
  fallback `http://192.168.10.145:10080/api_jsonrpc.php`
- Auth type: User login
- Username: `grafana_reader`
- Password: from Vault (`vault kv get -field=password secret/zabbix/grafana_reader`)
- Enable "Trends" + "Direct DB Connection"

For PostgreSQL direct-query (raw queries), add a second data source:

- Type: PostgreSQL
- Host: `zabbix-postgres:5432` (same Docker network) or `192.168.10.145:5432` (host)
- Database: `zabbix`
- User: `grafana_reader` (needs SELECT grant — `GRANT SELECT ON ALL
  TABLES IN SCHEMA public TO grafana_reader;`)
- SSL Mode: disable

Provisioned dashboard `zabbix-overview-p14` is the canonical entry
point (Phase 14 D-ZBX deliverable).

---

## 4. Security checklist

**On first deploy:**

- [ ] Change default admin password (Admin / zabbix → strong password)
- [ ] Disable guest access: *Administration → Authentication*
- [ ] Create read-only `grafana_reader` user; password into Vault at
      `secret/zabbix/grafana_reader`
- [ ] Configure housekeeping periods (30d history, 365d trends)

**Network surface:**

- [ ] OPNsense firewall rule: only `192.168.10.145` reaches `:161/udp`
      on `.1` and `.201`
- [ ] Port 10051 (Zabbix trapper) not exposed externally
- [ ] Web UI on `:10080` reachable from LAN only (Caddy front
      `zabbix.internal` is the canonical path)

**Agent encryption:**

- [ ] Mac Mini native agent: PSK encryption (identity `Mac-Mini-M4-PSK`)
- [ ] Mac Studio (when delivered): PSK encryption (identity `Mac-Studio-M3-PSK`)

**Periodic:**

- Weekly — *Administration → Audit log* review
- Monthly — failed-login check
- Quarterly — user-permission review

---

## 5. Backups

Zabbix DB snapshot is included in the nightly Restic job (`scripts/backup.sh`)
via the `zabbix-postgres` container path. Manual snapshot:

```bash
docker exec zabbix-postgres pg_dump -U zabbix zabbix | \
  gzip > ~/backups/zabbix-$(date +%Y%m%d).sql.gz
find ~/backups/zabbix-*.sql.gz -mtime +30 -delete
```

Restore lives in `docs/runbooks/vault-restore-from-backup.md` (same Restic
target; per-container path differs).

---

## 6. Known trade-offs (linked from CLAUDE.md)

- **ICMP/fping not available** — `zabbix-server` runs `cap_drop:[ALL]`
  which excludes `NET_RAW`. ICMP items will be in unsupported state.
  Use TCP-based health checks (telnet item type, `agent.ping`,
  `http.test`). Adding `NET_RAW` was rejected as exceeding minimal-cap
  doctrine.
- **Host-level disk/network** items reach the *agent container's* view,
  not the macOS host. True host-OS introspection requires the native
  agent (§2 above) or a macOS-native exporter sidecar.
- **Prometheus metrics** — see `zabbix-exporter` container at port `9224`
  (Phase 14 D-ZBX). Custom exporter scrapes Zabbix API and exposes
  `zabbix_triggers_active{severity=...}` + `zabbix_hosts_available{status=...}`
  via vmagent.
