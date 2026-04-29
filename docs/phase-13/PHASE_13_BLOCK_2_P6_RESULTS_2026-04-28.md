# Phase 13 — Block 2 P6 Results (2026-04-28)

**Scope**: Zabbix host registration + Caddy per-site logging/metrics

**Operator**: claude-opus-4-7[1m] under autonomous large-prompt mode

---

## Deliverables

### 1. Zabbix host registration

| Field | Value |
|---|---|
| host | `mac-mini` |
| name | `Mac Mini M5 (control center)` |
| hostid | `10783` |
| group | `Linux servers` (groupid 2) |
| template | `Linux by Zabbix agent` (templateid 10001) |
| interface | DNS `zabbix-agent:10050`, type 1 (agent) |
| availability | `1` (reachable) |
| tags | platform=mac-mini, phase=13, role=control-center |

**Verification (sample collecting items)**:

```
69875  vm.memory.size[available]   lastvalue=9.4 GiB     lastclock fresh
69876  vm.memory.size[pavailable]  lastvalue=56.20 %     lastclock fresh
```

**API doctrine note**: Zabbix 7.4.9 removed the JSON-RPC `auth` field. All
post-login API calls must use `Authorization: Bearer <token>` HTTP header.

### 2. zabbix-agent compose update

`docker/zabbix/docker-compose.yml`: `ZBX_HOSTNAME` aligned to `mac-mini`
(previously `Mac-Mini-M4-Pro`) so passive checks register against the host
created above.

### 3. Caddy access logging (resolved)

`docker/caddy/Caddyfile`:

- Added shared `(access_log)` snippet writing JSON to
  `/var/log/caddy/access.log` (volume `caddy-logs`), rolled at 100 MiB / 7 keeps.
- Inserted `import access_log` into all 36 `*.internal` site blocks.
- Each entry includes `host`, `method`, `uri`, `status`, `duration`, response
  headers — sufficient for per-site analysis via grep/jq.

### 4. Caddy Prometheus metrics (resolved with caveat)

`docker/caddy/Caddyfile`: added global `metrics` directive (replaced the
deprecated `servers { metrics }` after Caddy reload warning).

**Verified in VictoriaMetrics**:

```
caddy_http_requests_total{server="srv0",handler="subroute",job="caddy",service="caddy"}
caddy_http_request_duration_seconds_*  (14 series)
caddy_admin_http_requests_total
caddy_config_last_reload_successful
caddy_reverse_proxy_upstreams_healthy
```

**KNOWN-LIMITATION**: Caddy 2.11.2's default Prometheus output does **not**
include a per-host label on `caddy_http_request_*` series — only `code`,
`handler`, `method`, `server`. Per-site metric analysis is therefore deferred
to Loki-tailing the JSON access log in Phase 14. Documented in
`CLAUDE.md` Known Hardening Trade-offs.

### 5. Docker Desktop bind-mount workaround

Single-file bind mount on `Caddyfile` exhibited the documented inode-snapshot
issue: container saw a truncated 171-line file while host had 247. Resolved by
`docker compose restart caddy` (refreshes the bind). Same workaround pattern
documented for topology-api in P5 results.

### 6. Dashboard markdown updated

`docker/grafana-provisioning/dashboards/network-caddy.json` — Note panel
rewritten to reflect resolved state and document the per-host-label ceiling
+ how to query per-site by grepping access.log.

---

## Regression probe (h1)

```
PASS=14  FAIL=0  WARN=4
```

WARN breakdown (all benign):

- `openhands.internal`: not in macOS DNS cache (service exists, just not
  exercised this run)
- restic snapshot recency: creds Vault-fetched only — probe runs without
  AppRole, expected
- gate-specific dependency probes: probe was run with `unspecified` gate
- temp credential file warn: cleared (`rm /tmp/zbx_*.txt`)

No restarting containers, vault unsealed, audit log advancing, Caddy serving
HTTP 200/307 across .internal hosts.

---

## P6 gate close

All Block 2 control-center deliverables green:

- [x] §P2.1–P2.6 homepage on canonical AppRole + sidecar pattern
- [x] §P3 Grafana datasources provisioned (VictoriaMetrics, Infinity, TopologyJSON)
- [x] §P4 5 dashboards (Container Health, Network/Caddy, Vault Audit, Backup
       Status, Platform Overview retained)
- [x] §P5 topology-api + Service Topology Node Graph dashboard
- [x] §P6 mac-mini Zabbix host registered + Caddy per-site access logs

Mac Mini control-center is feature-complete for Block 2. Ready for user
inspection before P7 (MacBook Pro M5 parity).
