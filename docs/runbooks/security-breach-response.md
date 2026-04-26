# Security Breach Response

## Immediate Triage (First 5 Minutes)

```bash
# 1. Assess what's running
docker ps --format "{{.Names}}: {{.Status}}" | grep -v healthy

# 2. Check for unusual network connections from containers
docker stats --no-stream --format "{{.Name}}: NET={{.NetIO}}"

# 3. Check recent authentication failures
docker logs obot 2>&1 | grep -iE "401|403|auth|denied" | tail -20
docker logs litellm-gateway 2>&1 | grep -iE "401|403|invalid.*key" | tail -20

# 4. Check Vault for unauthorized access (if audit enabled)
docker exec vault-server vault audit list 2>/dev/null
```

## Containment Checklist

### Step 1: Isolate affected container

```bash
# Disconnect from all networks (blocks external communication)
CONTAINER=<name>
docker network disconnect control-center-net $CONTAINER 2>/dev/null
docker network disconnect docker_plane-net $CONTAINER 2>/dev/null
docker network disconnect docker_obot-net $CONTAINER 2>/dev/null
```

### Step 2: Preserve forensic evidence

```bash
TS=$(date +%Y%m%d-%H%M)
CONTAINER=<name>

# Save logs before they roll
docker logs $CONTAINER > /tmp/incident-${TS}-${CONTAINER}.log 2>&1

# Commit current container state as image
docker commit $CONTAINER iap-forensic-${TS}

# Save full inspect output
docker inspect $CONTAINER > /tmp/inspect-${TS}-${CONTAINER}.json

echo "Evidence preserved at /tmp/*${TS}*"
```

### Step 3: Rotate exposed secrets immediately

```bash
# Identify which .env values may be exposed
grep -E "API_KEY|TOKEN|PASSWORD|SECRET" ~/control-center-stack/stacks/gateways/.env | \
  sed 's/=.*/=REDACTED/'

# Revoke LiteLLM master key (invalidates all virtual keys)
# → Generate new key in gateways/.env LITELLM_MASTER_KEY
# → docker compose -f ~/control-center-stack/stacks/gateways/docker-compose.yml restart litellm

# Revoke Vault root token if exposed
export VAULT_ADDR=http://localhost:8200
vault token revoke <compromised-token>
# Generate new root token — requires vault operator generate-root with unseal keys
```

### Step 4: Block source IP at OPNsense

1. OPNsense web UI → Firewall → Rules → LAN
2. Add block rule: Source = `<attacker IP>`, Destination = `this firewall`
3. Apply changes
4. Verify: `ping -c 1 <attacker IP>` should still succeed (routing), but services blocked

---

## Scenario-Specific Response

### Leaked API Key (Anthropic, OpenAI, Plane)

```bash
# 1. Revoke at source
# - Anthropic: console.anthropic.com → API Keys → Revoke
# - OpenAI: platform.openai.com → API Keys → Delete
# - Plane: Workspace Settings → API Tokens → Revoke

# 2. Update locally
# Edit ~/control-center-stack/stacks/gateways/.env
# Update ANTHROPIC_API_KEY or OPENAI_API_KEY with new value

# 3. Store in Vault going forward
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$(grep VAULT_ROOT_TOKEN ~/control-center-stack/stacks/vault/.env | cut -d= -f2-)
vault kv put secret/api-keys/anthropic value="<new-key>"

# 4. Restart LiteLLM to pick up new key
cd ~/control-center-stack/stacks/gateways
docker compose restart litellm
```

### Unauthorized Model API Usage (LiteLLM abuse)

```bash
# 1. Check usage logs
docker logs litellm-gateway 2>&1 | grep -E "model|tokens" | tail -50

# 2. Identify which virtual key was used
docker logs litellm-gateway 2>&1 | grep "api_key" | tail -20

# 3. Disable the key
curl -X POST http://localhost:4000/key/delete \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keys": ["<compromised-virtual-key>"]}'

# 4. Rotate master key (nuclear option)
# Update LITELLM_MASTER_KEY in gateways/.env
# docker compose restart litellm
# All existing virtual keys are invalidated
```

### Container File System Tampering

```bash
# Check for changes vs original image
docker diff <container-name> | grep -v "^C /tmp" | head -30
# A = Added, C = Changed, D = Deleted
# Legitimate changes: /tmp, /var/log, named volumes

# Compare against known-good image
docker run --rm --entrypoint="" <image> find / -newer /etc/hostname \
  -not -path "*/proc/*" -not -path "*/sys/*" 2>/dev/null | head -20
```

### Vault Secret Exposure

See `docs/security/incident-response.md` → Vault Secret Exposure (P1).

---

## Post-Breach Recovery

### Service Rebuild (clean slate)

```bash
# 1. Pull fresh images (don't reuse potentially tainted layers)
docker compose -f ~/control-center-stack/stacks/gateways/docker-compose.yml pull
docker compose -f ~/control-center-stack/stacks/ai-control/docker-compose.yml pull

# 2. Remove all containers and volumes for affected stack
docker compose -f <stack-file> down -v

# 3. Redeploy from config
docker compose -f <stack-file> up -d

# 4. Re-seed secrets from Vault (not from .env files)
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=<new-root-token>
vault kv get -field=value secret/api-keys/anthropic
```

### Credential Re-issuance Checklist

| Credential | Action | Completed |
|------------|--------|-----------|
| Anthropic API key | Revoke + reissue at console.anthropic.com | ☐ |
| OpenAI API key | Revoke + reissue at platform.openai.com | ☐ |
| Plane API token | Revoke + reissue in Plane workspace settings | ☐ |
| LiteLLM master key | Generate new random string | ☐ |
| Vault root token | Rotate via `vault operator generate-root` | ☐ |
| GitHub PAT | Revoke + reissue at github.com/settings/tokens | ☐ |
| Brave API key | Revoke + reissue at api.search.brave.com | ☐ |

---

## Incident Report Template

File at: `docs/security/incidents/YYYY-MM-DD-<description>.md`

```markdown
## Incident Report
Date: YYYY-MM-DD
Severity: P1 / P2 / P3 / P4
Duration: HH:MM to HH:MM
Affected services: [list]

### Timeline
- HH:MM Detection — how noticed
- HH:MM Containment — what was isolated
- HH:MM Remediation — what was changed
- HH:MM Resolution — service restored

### Root Cause
[What allowed this to happen]

### Impact
[Data accessed, services disrupted, credentials exposed]

### Remediation Taken
[Specific actions: containers rebuilt, keys rotated, rules added]

### Preventive Measures
[What was added to prevent recurrence]
```
