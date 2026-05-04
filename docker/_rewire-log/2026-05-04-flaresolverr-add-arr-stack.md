# Rewire-log — 2026-05-04 — FlareSolverr added to arr-stack (D-17-108)

**File (out-of-repo):**
`/Users/admin/control-center-stack/stacks/arr-stack/docker-compose.yml`

**Deliverable:** D-17-108 — FlareSolverr QNAP → Mac Mini migration

---

## Pre-change state

**Lines:** 421
**MD5:** `aebe14d8eb3fd4ab600c0f7a629c5954`

## Change applied

Added `flaresolverr` service to arr-stack compose:

```yaml
flaresolverr:
  image: ghcr.io/flaresolverr/flaresolverr:latest
  container_name: flaresolverr
  restart: unless-stopped
  environment:
    LOG_LEVEL: "info"
  ports:
    - "8191:8191"
  cap_drop: [ALL]
  security_opt: [no-new-privileges:true]
  networks: [control-center-net]
  healthcheck: POST /v1 sessions.list, interval 30s
```

**Reason:** QNAP FlareSolverr unreachable from Prowlarr container
(172.23.0.12) due to QNAP QTS Docker subnet packet-filtering (Finding 22).
Architecture doctrine: application containers on Mac Mini, not QNAP.

## Post-change state

**Lines:** 452
**Services added:** `flaresolverr` (8191)

## Verification

- `docker exec prowlarr curl -X POST http://flaresolverr:8191/v1 -d '{"cmd":"sessions.list"}'` → `{"status":"ok","version":"3.4.6"}`
- Prowlarr proxy URL updated: `http://192.168.10.201:8191/` → `http://flaresolverr:8191/`
- `IndexerProxyStatusCheck` health issue cleared in Prowlarr

## QNAP decommission

QNAP FlareSolverr on 7-day cooldown. Manual stop via QNAP Container Station web UI required on 2026-05-11.
See: `docs/_retired/flaresolverr-qnap-2026-05-04.md`
