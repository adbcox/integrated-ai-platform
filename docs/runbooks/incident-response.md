# Runbook: Incident Response

**Last updated:** 2026-04-29 (Phase 14 D-DOC)

An incident is any unexpected condition that degrades platform availability,
compromises security, or risks data loss. This runbook covers the response
procedure for home-lab-scale incidents (single operator, no on-call rotation).

---

## Incident classification

| Severity | Definition | Response time |
|---|---|---|
| R-CRITICAL | Data loss risk, Vault unsealed but inaccessible, complete platform down | Immediate |
| R-HIGH | Core service (Vault, Obot, Plane) unhealthy, credential exposure risk | Within 1 hour |
| R-MEDIUM | Single non-core service down, probe FAIL=1 | Within 4 hours |
| R-LOW | WARN increase, degraded but functional, cosmetic | Best effort |

---

## Step 1: Triage (5 minutes)

```bash
# Quick platform health snapshot
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh

# All container states
docker ps --format '{{.Names}} {{.Status}}' | sort

# Any restart loops
docker ps --format '{{.Names}} {{.RestartCount}}' | awk '$2 > 3'

# Recent Docker events
docker events --since 1h --until now --format '{{.Time}} {{.Type}} {{.Action}} {{.Actor.Attributes.name}}'
```

Classify severity from the above output. If FAIL=0 and no restart loops,
downgrade to R-LOW or close the incident.

---

## Step 2: Contain

Stop the bleeding before diagnosing root cause.

**If a container is crash-looping and affecting other services:**
```bash
docker stop <container>
```
Stopping a broken sidecar or service prevents it from consuming resources
or writing corrupt state. Do NOT `docker rm` until you've collected logs.

**If credentials may be exposed (value appeared in logs, commit, or output):**
1. Do NOT display the value again
2. Immediately rotate: `docs/runbooks/rotate-credentials.md`
3. Check Vault audit log for unauthorized access:
   ```bash
   docker exec vault-server cat /vault/logs/audit.log | tail -100 | \
     python3 -c "import json,sys; [print(l['time'], l.get('request',{}).get('operation'), l.get('auth',{}).get('accessor','')) for l in map(json.loads, sys.stdin) if 'request' in l]"
   ```

**If Vault is sealed:**
See `docs/runbooks/vault-unseal.md` immediately. Nearly everything depends on Vault.

---

## Step 3: Collect evidence

Before making changes, collect logs:

```bash
# Service logs (last 100 lines)
docker logs <container> --tail 100 > /tmp/incident-<container>-$(date +%s).log

# Container inspect
docker inspect <container> > /tmp/incident-inspect-<container>-$(date +%s).json

# Vault audit tail (last 50 entries)
docker exec vault-server tail -50 /vault/logs/audit.log > /tmp/incident-vault-audit-$(date +%s).log

# Docker events last 2 hours
docker events --since 2h --until now > /tmp/incident-events-$(date +%s).log
```

---

## Step 4: Diagnose

Common incident patterns:

### Pattern: Service not starting after compose change

```bash
# Sidecar didn't complete?
docker logs vault-agent-<svc> --tail 30
ls ~/.vault-agent-secrets/<svc>/  # credentials.env present?

# Missing capability?
docker logs <service> --tail 30 | grep -E 'permission|Operation not permitted|setgroups|setpriv'
```

See `docs/runbooks/regression-probe-failure.md` for per-service triage.

### Pattern: Vault sealed

```bash
docker exec vault-server vault status
# If seal-vault is running, auto-unseal should trigger within 30s
docker logs seal-vault --tail 20
```

See `docs/runbooks/vault-unseal.md`.

### Pattern: Data corruption / Vault data loss

```bash
docker exec vault-server vault status
# If initialized=false: Vault data is gone
```

See `docs/runbooks/vault-restore-from-backup.md`. This is R-CRITICAL.

### Pattern: Out-of-disk

```bash
df -h /  # macOS host
docker system df  # Docker layer usage
```

If Docker volumes are consuming space:
```bash
docker volume ls --format '{{.Name}}'
# Remove only volumes confirmed as orphaned (no running container mounts them)
docker volume prune --filter "label!=keep"
```

### Pattern: Port conflict

```bash
# Find what's using a port
lsof -i :<port>
```

If a stopped-but-not-removed container holds the port:
```bash
docker ps -a | grep <port>
docker rm <stopped-container>
```

---

## Step 5: Remediate

Apply the fix. Use the relevant runbook for the specific service.
Do NOT skip verification steps to "save time" during an incident — this
is how incidents cascade.

After every remediation step:
```bash
docker inspect <container> --format '{{.State.Status}} {{.State.Health.Status}}'
```

---

## Step 6: Verify

```bash
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
# Required: FAIL=0 before declaring incident closed
```

Also verify the specific service that was affected is healthy:
```bash
curl -sf http://localhost:<port>/<healthpath> && echo "OK"
```

---

## Step 7: Document

Create an incident record at `docs/runbooks/rewire-log/YYYY-MM-DD-incident-<description>.md`:

```markdown
# Incident: <short title>

**Date:** YYYY-MM-DD
**Severity:** R-<level>
**Duration:** HH:MM
**Affected services:** <list>

## Timeline
- HH:MM — detected (probe FAIL / alert / observation)
- HH:MM — contained (<action>)
- HH:MM — root cause identified
- HH:MM — remediated (<action>)
- HH:MM — probe FAIL=0, incident closed

## Root cause
<one paragraph>

## Remediation applied
<commands run>

## Follow-up actions
- [ ] <any drift or hardening gaps to fix>
- [ ] <any runbook updates needed>
```

---

## R-CRITICAL: Full platform recovery order

If everything is down (power cycle, host crash):

1. Start Vault + seal-vault:
   ```bash
   cd ~/control-center-stack/stacks/vault && docker compose up -d
   cd ~/control-center-stack/stacks/seal-vault && docker compose up -d
   sleep 30
   docker exec vault-server vault status | grep Sealed  # must be false
   ```

2. Start core infrastructure (Caddy, observability):
   ```bash
   cd ~/repos/integrated-ai-platform/docker
   docker compose -f observability-stack.yml up -d
   ```

3. Start platform services:
   ```bash
   docker compose -f docker-compose-plane.yml up -d
   docker compose -f netbox/docker-compose.yml up -d
   ```

4. Start AI / MCP layer:
   ```bash
   docker compose -f obot-stack.yml up -d
   docker compose -f mcp/docker-compose.yml up -d
   docker compose -f mcp/docker-compose.mcp-docker-remote.yml up -d
   ```

5. Start out-of-repo stacks:
   ```bash
   for stack in arr-stack dashboards ai-control; do
     (cd ~/control-center-stack/stacks/$stack && docker compose up -d)
   done
   ```

6. Run regression probe:
   ```bash
   bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
   ```
