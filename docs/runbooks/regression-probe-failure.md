# Runbook: Regression Probe Failure

**Last updated:** 2026-04-29 (Phase 14 D-DOC)

The regression probe (`docs/phase-13/h1-regression-probe.sh`) is the platform's
pass-or-fail gate. A FAIL=1+ output means at least one gate check is failing.
This runbook is the triage procedure for probe failures.

---

## Run the probe

```bash
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
```

Expected output (healthy):
```
PASS=15 FAIL=0 WARN=3
```

WARN entries are documented chronic conditions (ICMP unsupported in Zabbix,
cAdvisor friendly-name labels). WARN does not block phase progression.
FAIL blocks phase progression.

---

## Identify the failing check

The probe outputs labelled results. The label tells you which check (a–h or
numbered) failed. Map the label to the service:

| Check | Service | Port / endpoint |
|---|---|---|
| a | Vault | `vault-server:8200/v1/sys/health` |
| b | Obot | `localhost:8090/api/healthz` |
| c | VictoriaMetrics | `localhost:8428/health` |
| d | VMAgent | `localhost:8429/health` |
| e | Grafana | `localhost:3030/api/health` |
| f | Uptime Kuma | `localhost:3033` |
| g | Plane API | `localhost:8000/api/` |
| h | NetBox | `localhost:8080/api/` |

For numbered checks beyond a–h, read the probe script directly:
```bash
cat ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
```

---

## Triage by service

### Vault FAIL (check a)

```bash
docker inspect vault-server --format '{{.State.Status}}'
docker exec vault-server vault status
```

If sealed:
```bash
# Auto-unseal should trigger automatically if seal-vault is running
docker inspect seal-vault --format '{{.State.Status}}'
```

If sealed and seal-vault is down: see `docs/runbooks/vault-unseal.md`.
If sealed and seal-vault is also unrecoverable: see `docs/runbooks/vault-recovery-from-shamir.md`.

If Vault data is lost: see `docs/runbooks/vault-restore-from-backup.md`.

### Obot FAIL (check b)

```bash
docker inspect obot --format '{{.State.Status}} {{.State.Health.Status}}'
docker logs obot --tail 30
```

Obot depends on `vault-agent-obot` completing successfully:
```bash
docker logs vault-agent-obot --tail 20
# Look for "renewWatcher: max TTL is zero" or "successfully authenticated"
```

If vault-agent-obot failed (credentials not rendered):
```bash
# Check approle files present
ls ~/.vault-approle/obot/
ls ~/.vault-agent-secrets/obot/

# Re-run sidecar + obot
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml up -d obot
```

### VictoriaMetrics / VMAgent FAIL (checks c, d)

```bash
docker inspect vm vmagent --format '{{.Name}} {{.State.Status}}'
docker logs vm --tail 20
docker logs vmagent --tail 20
```

If stopped:
```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f observability-stack.yml up -d vm vmagent
```

### Grafana FAIL (check e)

```bash
docker inspect grafana --format '{{.State.Health.Status}}'
docker logs grafana --tail 20
```

Grafana has a Vault Agent sidecar. If credentials not rendered, the sidecar
may have failed:
```bash
docker logs vault-agent-grafana --tail 20
ls ~/.vault-agent-secrets/grafana/
```

Restart:
```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f observability-stack.yml up -d grafana
```

### Uptime Kuma FAIL (check f)

```bash
docker inspect uptime-kuma --format '{{.State.Status}}'
docker logs uptime-kuma --tail 20
```

Uptime Kuma uses setpriv for UID/GID drop — requires SETUID and SETGID cap_add.
If restarting after a compose change:
```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f observability-stack.yml up -d uptime-kuma
```

### Plane API FAIL (check g)

```bash
docker inspect plane-api --format '{{.State.Status}}'
docker logs plane-api --tail 30
```

Plane depends on Vault Agent sidecars (vault-agent-plane-*) and its Postgres + Redis:
```bash
docker compose -f docker/docker-compose-plane.yml ps
```

If database services are unhealthy, restart in dependency order:
```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f docker-compose-plane.yml up -d
```

### NetBox FAIL (check h)

```bash
docker inspect netbox --format '{{.State.Health.Status}}'
docker logs netbox --tail 30
```

NetBox depends on its Postgres + Valkey:
```bash
cd ~/repos/integrated-ai-platform/docker/netbox
docker compose ps
docker compose up -d
```

---

## Container in restart loop

If `docker inspect <name> --format '{{.RestartCount}}'` is increasing:

1. Check logs: `docker logs <name> --tail 50`
2. Common causes:
   - Vault Agent sidecar failed → `credentials.env` not rendered → entrypoint fails
   - Missing `cap_add` (check for `Operation not permitted` in logs)
   - Port already in use (`address already in use`)
   - Dependency (DB) not healthy yet (wait 30s and recheck)

3. For capability errors, see the `cap_add` requirements table in `docs/ARCHITECTURE.md`.

---

## WARN vs FAIL distinction

- **WARN:** Probe detects a known, documented, non-blocking condition.
  Do not chase WARN entries unless the number increases or a new WARN appears.
- **FAIL:** Service health check returned non-200 or container is not running.
  Do not advance phases until FAIL=0.

---

## Escalation

If a FAIL cannot be resolved in <30 minutes:
1. Document the failure in `docs/runbooks/rewire-log/YYYY-MM-DD-incident.md`
2. Run `docs/runbooks/incident-response.md`
3. Do not proceed with phase work until FAIL=0

---

## After fix

Re-run the probe to confirm resolution:
```bash
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
# Required: FAIL=0
```
