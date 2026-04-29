# Control Plane (Operator Web App)

Phase 13 Block 2.5 — operator-only web app on `control.internal` for
day-to-day platform actions (container ops, manual backup, queue
management, audit search, regression probe).

## Trust model

- **Outer door:** Caddy `control.internal` matches `remote_ip 100.64.0.0/10`
  (Headscale CGNAT). Off-tailnet requests get 403 before reaching
  this app.
- **App-level re-check:** `auth.require_tier1` re-validates the X-F-F header
  against the same CIDR (defense in depth).
- **Tier 3 (sensitive actions):** operator submits the password to
  `/auth/unlock`; we Argon2-verify against the hash in
  `secret/control-plane/operator` and open a 5-minute sliding window
  per client IP.
- **Hash-only verification doctrine:** credential values are never
  returned by any endpoint. `/api/credentials/*` returns paths and
  metadata only.

## Tier table

| Tier | Operations |
|------|------------|
| T1 read | container list/inspect/logs, queue read, audit search, registry, last-backup |
| T2 write | container start/stop/restart, queue retry/remove |
| T3 sensitive | manual backup, regression probe, credential rotate |
| forbidden via web | exec into container, vault root operations |

## Components

```
docker/control-plane/
  Dockerfile                  python:3.12-slim + restic + bundled htmx
  requirements.txt            FastAPI, httpx, jinja2, argon2-cffi, ...
  docker-compose.yml          3 services: sidecar, socket-proxy, main
  app/
    main.py                   FastAPI bootstrap, tier middleware, /metrics
    auth.py                   tailnet gate + Argon2 + sliding window
    triggers.py               trigger-file dispatch (D8 nonce+timestamp)
    audit_log.py              JSON-line action audit
    metrics.py                Prometheus counters
    config.py                 pydantic-settings (env-driven)
    ui.py                     HTMX page + partial routes
    modules/                  T1/T2/T3 action implementations
    templates/                Jinja2 + HTMX
    static/                   tw.css, cp.js, htmx.min.js (bundled)
  vault-agent/
    agent.hcl                 sidecar config (exit_after_auth)
    credentials.env.tmpl      operator hash + arr keys + restic creds
  host-launchers/
    iap-trigger-watcher.sh    launchd watcher (validates nonce+ts, executes)
    iap-backup-trigger.sh     wraps scripts/backup.sh
    iap-regression-probe-trigger.sh  wraps docs/phase-13/h1-regression-probe.sh
    com.iap.control-plane.trigger-watcher.plist  LaunchAgent
```

## Deploy

1. Provision Vault policy + AppRole + operator hash
   ```
   bash scripts/provision-control-plane.sh
   ```
   You'll be prompted for the operator password (≥ 12 chars, twice).

2. Build + launch
   ```
   cd docker/control-plane
   docker compose build
   docker compose up -d
   ```
   Verify: `vault-agent-control-plane` exits 0; `control-plane` and
   `docker-socket-proxy-control` show `Up`.

3. Install host launchers (operator-owned, no sudo)
   ```
   cp docker/control-plane/host-launchers/iap-*.sh /Users/admin/iap-launchers/
   chmod 0755 /Users/admin/iap-launchers/*.sh
   cp docker/control-plane/host-launchers/com.iap.control-plane.trigger-watcher.plist \
      ~/Library/LaunchAgents/
   launchctl load -w ~/Library/LaunchAgents/com.iap.control-plane.trigger-watcher.plist
   ```

4. Reload Caddy
   ```
   docker exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```

5. Add `control.internal → 192.168.10.145` to OPNsense Unbound DNS.

## Verify

```
curl http://127.0.0.1:8086/healthz                                                # 200
curl -o /dev/null -w '%{http_code}\n' \
     -H "Host: control.internal" --resolve control.internal:443:127.0.0.1 \
     -k https://control.internal/healthz                                          # 403 off-tailnet
curl -H "X-Forwarded-For: 100.64.0.1" http://127.0.0.1:8086/api/registry/services | jq .  # 65 services
```

Trigger-pipeline self-test:

```
NONCE=$(uuidgen)
TS=$(python3 -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).isoformat())")
cat > /Users/admin/iap-triggers/regression-probe-${NONCE}.json <<EOF
{"nonce":"${NONCE}","timestamp":"${TS}","action":"regression-probe","params":{"gate_id":"smoke"}}
EOF
chmod 0600 /Users/admin/iap-triggers/regression-probe-${NONCE}.json
# Result lands in /Users/admin/iap-triggers/results/${NONCE}.json within ~5s
```

## Caps + hardening

| Container | cap_drop | cap_add | read_only | mem |
|-----------|----------|---------|-----------|-----|
| `vault-agent-control-plane` | ALL | (none) | n/a (sidecar) | default |
| `docker-socket-proxy-control` | ALL | CHOWN, SETGID, SETUID | yes | 64m |
| `control-plane` | ALL | NET_BIND_SERVICE, DAC_READ_SEARCH | yes | 256m |

`DAC_READ_SEARCH` is granted so root inside the container can read
the 0600 Vault audit log mounted RO. The container has only narrow
RO mounts (audit, access logs, registry yaml, credentials.env), so
the cap doesn't expand the attack surface meaningfully.

## Trigger-file protocol (D8)

Anti-replay: every trigger written by control-plane carries a UUID
`nonce` and an ISO-8601 `timestamp`. The host watcher rejects:
- timestamps more than 30 s skewed from now
- nonces seen in the last 300 s
- actions not in the allowlist (`backup-trigger`, `regression-probe`,
  `credential-rotate`)

Rejections are persisted as `<nonce>.rejected.json` so the API
caller sees the reason instead of just timing out.
