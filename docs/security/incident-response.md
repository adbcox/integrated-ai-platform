# Incident Response Playbook

## Process: DETECT → TRIAGE → CONTAIN → INVESTIGATE → REMEDIATE → DOCUMENT

## Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 Critical | Data breach, service compromise | 1 hour | Unauthorized container access |
| P2 High | Service outage, auth failure flood | 4 hours | 50+ failed logins |
| P3 Medium | Degraded performance, single service down | 24 hours | Container OOM restart |
| P4 Low | Configuration drift, non-critical warning | 1 week | Outdated image |

## Runbooks

### Failed Authentication Flood (P2)

**Detection:** Grafana alert — >10 failed auth attempts in 5 minutes from same IP

1. Identify source: `docker logs obot 2>&1 | grep -i "auth\|401\|403" | tail -20`
2. Check source IP in OPNsense firewall logs
3. Temporary block at OPNsense: Firewall → Rules → LAN → Add block rule for source IP
4. If legitimate user: Check Obot admin UI → force password reset
5. Rotate OBOT_ADMIN_PASSWORD in `docker/.env` if compromised
6. Recreate Obot: `docker compose -f docker/obot-stack.yml up -d --force-recreate`
7. Document: IP, time, affected service, action taken

### Container Compromise (P1)

```bash
# 1. Immediate isolation
CONTAINER=affected-container
docker network disconnect control-center-net $CONTAINER
docker network disconnect docker_plane-net $CONTAINER

# 2. Preserve evidence
docker logs $CONTAINER > /tmp/incident-$(date +%Y%m%d-%H%M)-${CONTAINER}.log
docker commit $CONTAINER iap-forensic-$(date +%Y%m%d-%H%M)

# 3. Snapshot running state
docker inspect $CONTAINER > /tmp/inspect-$(date +%Y%m%d-%H%M)-${CONTAINER}.json

# 4. Stop container
docker stop $CONTAINER

# 5. Preserve image
docker save iap-forensic-$(date +%Y%m%d-%H%M) | gzip > /tmp/forensic-image.tar.gz
```

Then investigate offline before redeploying from clean image.

### Vault Secret Exposure (P1)

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=<root-token>

# 1. Identify which secrets were accessed
vault audit list
# If audit enabled, check logs for unauthorized access

# 2. Revoke compromised token immediately
vault token revoke <compromised-token>

# 3. Rotate affected secrets
vault kv put secret/plane/api_token value="<new-token>"
# Update docker/.env and restart affected services

# 4. Generate new root token (requires unseal keys)
vault operator generate-root -init
```

### Service Outage (P3)

```bash
# Check which services are down
./docs/mcp/health-checks.md

# Restart in dependency order:
# 1. Database first
docker compose -f docker/docker-compose-plane.yml up -d plane-db
# 2. Then dependent services
docker compose -f docker/docker-compose-plane.yml up -d
# 3. Then gateway
docker compose -f docker/obot-stack.yml up -d
# 4. Then control center
cd ~/control-center-stack/stacks/gateways && docker compose up -d
cd ~/control-center-stack/stacks/ai-control && docker compose up -d
```

## Post-Incident Documentation Template

```
## Incident Report
Date: 
Severity: 
Duration: 
Affected services: 
Root cause: 
Timeline:
  - HH:MM Detection
  - HH:MM Containment
  - HH:MM Remediation
  - HH:MM Resolution
Impact: 
Remediation taken: 
Preventive measures added: 
```

File incident reports in: `docs/security/incidents/YYYY-MM-DD-description.md`
