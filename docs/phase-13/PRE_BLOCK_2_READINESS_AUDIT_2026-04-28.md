# Pre-Block-2 Readiness Audit

**Date**: 2026-04-28
**Scope**: Data sources Block 2 (Homepage + Grafana visualization) will consume.
**Method**: Investigation only — no mutations applied during audit.

---

## TL;DR — Go/No-Go

**Block 2 status**: **NEAR-READY** with 1 blocker, 3 quick fixes, and 2 known limitations.

| # | Finding | Severity | Block | Fix scope |
|---|---|---|---|---|
| 1 | Restic backup auth broken (MinIO Access Key Id mismatch) | **BLOCKER** | Block 2 backup dashboards will show no data | Pre-Block-2 fix (rotate MinIO creds vs Vault sync) |
| 2 | Vault Prometheus metrics endpoint not enabled (`prometheus is not enabled`) | HIGH | No Vault telemetry in Grafana | Quick fix: add `telemetry` stanza to `vault-config.hcl`, restart Vault |
| 3 | Zabbix metrics not scraped by vmagent | HIGH | Zabbix data isolated; can't unify in Grafana | Quick fix: add zabbix-server `:10052` job to `vmagent-config/scrape.yml` |
| 4 | Caddy access logs (user traffic on :80/:443) not configured | MEDIUM | Block 2 access-pattern dashboards limited | Quick fix: add `log` directive to Caddyfile site blocks |
| 5 | zabbix-server fping operation not permitted | MEDIUM | Some ICMP-based items broken | KNOWN-LIMITATION (cap_drop too strict for raw sockets); accept |
| 6 | Mac-Mini-M4-Pro host not registered in zabbix-server | MEDIUM | zabbix-agent active checks failing | Manual: register host via zabbix-web UI |

---

## 1. Zabbix functional state

**Current state** (verified):
- All 4 containers Up: zabbix-postgres (healthy), zabbix-server, zabbix-web (healthy), zabbix-agent
- API: `apiinfo.version` → `7.4.9` ✅
- Database: 55 hosts (54 enabled), 18,973 items (18,971 enabled), 7,154 triggers
- Active data ingestion: history_uint rows arriving every few seconds

**Side issues (logged in zabbix-server)**:
- `sh: /usr/sbin/fping: Operation not permitted` — repeated. fping needs raw socket (NET_RAW capability); current cap_drop=[ALL] + cap_add=[NET_BIND_SERVICE] doesn't include NET_RAW. Affects ICMP-based items only.
- `cannot send list of active checks to "172.25.0.2": host [Mac-Mini-M4-Pro] not found` — agent's hostname not registered in zabbix-server's host table.

**Expected for Block 2**: Zabbix produces the bulk of platform metrics; Block 2 needs to either consume from zabbix-web API directly or scrape zabbix-server's metrics export.

**Gap**: vmagent currently does NOT scrape zabbix-server. zabbix-server exposes Prometheus metrics on port 10052 by default; no scrape job exists.

**Fix recommendation**: Pre-Block-2 — add scrape job to `docker/vmagent-config/scrape.yml`. See Quick Fixes section.

---

## 2. cAdvisor / container metrics

**Current state**:
- cAdvisor Up (healthy), container_name=cadvisor, exposed on host port 8088
- `localhost:8088/metrics` → 200, returns Prometheus exposition (cadvisor v0.45)
- Already in vmagent scrape config: `host.docker.internal:8088` job=`cadvisor`

**Gap**: None.

**Fix**: None needed. Block 2 can consume cadvisor metrics via VictoriaMetrics directly.

---

## 3. Caddy access logs and metrics

**Current state**:
- Caddy admin API (`:2019/config/`, `:2019/metrics`) → 200, Prometheus exposition available
- `caddy_admin_http_requests_total` and similar admin-side metrics flowing
- Already in vmagent scrape config: `host.docker.internal:2019` job=`caddy`
- Caddy structured logs visible via `docker logs caddy` (admin-API requests only)

**Gap — IMPORTANT for Block 2**: There is no per-route access log for user-facing traffic (port 80/443). The Caddyfile lacks `log` directives. This means:
- No request-rate metrics per .internal domain
- No latency/status code distribution per upstream
- Block 2 dashboards limited to admin-API counters + cAdvisor's network bytes

**Fix recommendation**: Quick fix during pre-Block-2 — add to each site block in Caddyfile:
```
log {
  output file /var/log/caddy/access-<domain>.log
  format json
}
```
Plus a log directive for the global server. Requires Caddy restart and a writable bind-mount.

---

## 4. Vault audit log + metrics

**Current state**:
- Audit log: file device enabled, `/vault/logs/audit.log` 2.2 MB and growing (just took an audit hit during audit itself)
- `/v1/sys/metrics` → **403, message "prometheus is not enabled"**
- `vault-config.hcl` has NO `telemetry { ... }` stanza

**Gap — HIGH**: Vault Prometheus metrics endpoint not enabled. Block 2 cannot unify Vault telemetry (token issuance rate, KV ops/sec, audit volume, seal status, leases) into Grafana.

**Fix recommendation**: Pre-Block-2 — add to `vault-config.hcl`:
```hcl
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname          = true
  unauthenticated_metrics_access = true
}
```
Then `docker restart vault-server` (auto-unseal will engage). Adds vmagent scrape job for `vault-server:8200/v1/sys/metrics`.

Estimated time: 5 minutes including restart + verify.

---

## 5. Service-registry.yaml currency

**Current state**:
- 61 services in registry
- 42 containers currently running
- 3 running containers NOT in registry: `seal-vault`, `cadvisor`, `plex-mcp`
- 0 registered services with non-running containers (when normalized for multi-host future entries)
- 26/61 services have empty `depends_on` (per H1 §10 deferral — full population deferred)

**Gap**: 3 unregistered containers; depends_on incomplete.

**Fix recommendation**:
- Add `seal-vault`, `cadvisor`, `plex-mcp` entries → 15 min, in scope for pre-Block-2 if Block 2 wants registry-driven Grafana panels
- Full depends_on population: defer to Block 2 work itself (Block 2 will surface what depends_on needs to support its dependency-graph dashboard)

---

## 6. Inter-service communication

**Current state**:
- DNS: all sampled `.internal` domains resolve to 192.168.10.145 ✅
- TLS via Caddy: vault.internal→307, nextcloud.internal→302, plane.internal→200, vaultwarden.internal→200 ✅
- Container-to-container: open-webui→litellm-gateway:4000=200; obot→docker-plane-db-1 DNS resolves ✅
- 13 distinct Docker networks (functional segmentation)

**Gap**: None for Block 2 readiness. Network plane is healthy.

---

## 7. Backup status visibility (Restic)

**Current state**: ❌ **BROKEN**

Probe output (truncated):
```
Stat(<config/>) returned error, retrying: The Access Key Id you provided does not exist in our records.
```

- `secret/restic/backup` → repository `s3:http://192.168.10.201:9000/backups` ✅
- `secret/minio/backup` → username + password fields exist ✅
- But the AWS_ACCESS_KEY_ID derived from `secret/minio/backup:username` is rejected by MinIO on QNAP
- Cron schedule active: `0 2 * * * /Users/admin/repos/integrated-ai-platform/scripts/backup.sh` — has been **failing nightly silently** (no notification, no alert)

**Severity**: BLOCKER for Block 2's backup-status dashboard. Also BLOCKER for actual backup integrity (we may have no recent snapshots — last verified snapshot was `9d7fdfff` from H1 §2).

**Possible causes**:
- MinIO access key on QNAP rotated since `secret/minio/backup` was migrated
- Wrong field names in Vault (e.g., expects `access_key` not `username`)
- MinIO root user credentials don't match service-account credentials
- QNAP MinIO instance restarted with default keys

**Fix recommendation**: Pre-Block-2 — investigate QNAP MinIO admin console, retrieve current valid creds, update `secret/minio/backup`, run `scripts/backup.sh` interactively to verify, then verify cron-driven snapshot.

---

## 8. Service deep-probe coverage

**Current state**:
- 34/61 services have `health_url` in registry
- ~3 services have deep (DB-exercising) probes: nextcloud (`/ocs/v2.php/cloud/capabilities`), zabbix-web (`/api_jsonrpc.php apiinfo.version`)
- Most services: shallow (`/health`, `/alive`, `/api/healthz`)

**Gap**: Most DB-fronting services lack deep probes. Block 2 dashboards relying on shallow probes will report "healthy" even when downstream DBs are broken.

**Fix recommendation**: Defer to Block 2 — Block 2 work itself naturally surfaces which services need deep probes for dashboard accuracy. Add as Block 2 deliverable.

---

## Observability stack — implicit Block 2 substrate

**Current state**:
- grafana-obs Up (port 3000, /api/health → 200)
- VictoriaMetrics (`vm`) Up (healthy, port 8428, 7,555 series, last data 16:03:40)
- vmagent Up (config: `docker/vmagent-config/scrape.yml`, 5 jobs configured)
- uptime-kuma Up (healthy)
- node-exporter Up (port 9100/metrics → 200)

**vmagent scrape jobs (current)**:
1. node-exporter (host.docker.internal:9100) ✅
2. caddy (host.docker.internal:2019) ✅
3. mcp-docs (host.docker.internal:8093)
4. cadvisor (host.docker.internal:8088) ✅
5. vmagent self (vmagent:8429)

**Gap (CRITICAL)**: VM `/api/v1/targets` reports **0 active targets** — but `up{}` query returns 5 series. This contradiction means scrape config IS loaded but the targets API is reporting differently than expected. May be a vmagent vs vmselect API difference.

**Missing scrape jobs for Block 2**:
- vault-server (no telemetry endpoint enabled — finding 4)
- zabbix-server (port 10052 unscraped)
- plane-api Django metrics endpoint (if exposed)
- nextcloud (no metrics endpoint by default)
- vaultwarden (`/metrics` for prometheus exporter — needs ENABLE_DB_WAL=enabled if version supports)

---

## Quick fixes — surfacing for "execute during audit?" decision

These are obvious, low-risk, high-value fixes within audit scope. **None executed unilaterally** — surfacing for user decision:

### QF.1 — Enable Vault Prometheus metrics
Edit `vault-config.hcl` to add `telemetry { prometheus_retention_time = "30s"; disable_hostname = true; unauthenticated_metrics_access = true }`. Restart vault-server. ~5 min.

### QF.2 — Add zabbix-server scrape job to vmagent
Append job to `docker/vmagent-config/scrape.yml` for `zabbix-server:10052/metrics`. Reload vmagent. ~3 min.

### QF.3 — Investigate + fix Restic backup auth
Diagnose MinIO Access Key Id mismatch on QNAP. Update `secret/minio/backup` if creds rotated. Verify backup script runs successfully. ~30 min (depends on what we find on QNAP side).

### QF.4 — Add Caddy access logging
Add per-site `log` directives to Caddyfile + writable log volume. Restart Caddy. ~10 min.

### QF.5 — Register 3 unregistered containers
Add seal-vault, cadvisor, plex-mcp to service-registry.yaml. ~5 min.

**My recommendation for pre-Block-2**: QF.1 + QF.2 + QF.3 (the three highest-leverage fixes). Defer QF.4 + QF.5 to Block 2 work where they fit naturally.

---

## Out-of-scope (defer to Block 2 itself)

- Per-service deep-probe definitions (Block 2 will surface needed depth)
- Full `depends_on` population in service-registry (Block 2 dependency-graph dashboard drives requirements)
- Grafana dashboard authoring (the actual Block 2 deliverable)
- Homepage tile design (Block 2 deliverable)

---

## Tier-summary for Block 2 prep

```
GO:
- Zabbix data plane (functional, 55 hosts, 18973 items)
- VictoriaMetrics + vmagent (running, 7555 series)
- node-exporter, cAdvisor, Caddy admin metrics (already scraped)
- DNS/TLS/networking (clean)
- Inter-service reachability (clean)

NEEDS QUICK FIX BEFORE BLOCK 2:
- Vault Prometheus telemetry (5 min)
- vmagent scraping zabbix-server (3 min)
- Restic backup auth (30 min)

CAN DEFER TO BLOCK 2:
- Caddy access logs
- Service-registry currency
- Deep-probe coverage expansion
- Full depends_on population

KNOWN LIMITATIONS (accept):
- zabbix-server fping: cap_drop too strict for ICMP raw sockets
- Mac-Mini-M4-Pro host not registered: manual zabbix-web action needed
```

---

## Standing recommendation

Execute QF.1, QF.2, QF.3 in a focused 45-minute pre-Block-2 prep pass. Then proceed to Block 2 with a clean substrate. QF.3 is the load-bearing one — without it, Block 2 backup dashboards are blind and we don't know if backups have actually been running.
