# Runbook: Drift Detection Procedure

**Last updated:** 2026-04-29 (Phase 14 D-DOC)

Drift is the condition where running system state diverges from declared state
(compose files, NetBox CMDB, Vault policies). This runbook defines the periodic
procedure to detect and remediate drift before it becomes an incident.

**Recommended cadence:** weekly (or after any untracked change).

---

## What drifts and where to look

| Layer | Canonical state | Drift signal |
|---|---|---|
| Container config | Compose files | `docker inspect` differs from compose spec |
| Service inventory | NetBox CMDB | Container running but not in NetBox |
| Vault policies | `config/vault-policies/*.hcl` | Policy in Vault but no file, or vice versa |
| AppRole credentials | `~/.vault-approle/` | AppRole in Vault but no local role-id/secret-id |
| Caddy routes | `docker/caddy/Caddyfile` | Route with no backing service |
| Out-of-repo composes | `~/control-center-stack/stacks/*/docker-compose.yml` | Modified but not snapshotted in rewire log |
| Hardening | Compose `cap_drop` spec | Running container lacks `cap_drop` |

---

## Step 1: Container vs compose drift

Compare running containers against compose-declared services:

```bash
# All running containers
docker ps --format '{{.Names}}' | sort > /tmp/running.txt

# Declared in in-repo stacks
grep -h 'container_name:' \
  docker/observability-stack.yml \
  docker/knowledge-stack.yml \
  docker/obot-stack.yml \
  docker/netbox/docker-compose.yml \
  docker/mcp/docker-compose.yml \
  docker/mcp/docker-compose.mcp-docker-remote.yml \
  docker/headscale/docker-compose.yml \
  | awk '{print $2}' | sort > /tmp/declared.txt

# Containers running but not declared (orphan candidates)
comm -23 /tmp/running.txt /tmp/declared.txt

# Declared but not running (stopped service candidates)
comm -13 /tmp/running.txt /tmp/declared.txt
```

For out-of-repo stacks, add the container_names from
`~/control-center-stack/stacks/*/docker-compose.yml` to `/tmp/declared.txt`.

Plane CE is retired; include Plane compose only for historical
forensics, not active drift baselines.

---

## Step 2: Service inventory vs NetBox drift

```bash
# Services in NetBox
CMDB_SOURCE=netbox python3 scripts/cmdb_source.py | \
  python3 -c "import json,sys; [print(s.get('container','')) for s in json.load(sys.stdin) if s.get('container')]" \
  | sort > /tmp/netbox.txt

# Compare with running
comm -23 /tmp/running.txt /tmp/netbox.txt  # running but not in NetBox
comm -13 /tmp/running.txt /tmp/netbox.txt  # in NetBox but not running
```

Any container running but absent from NetBox should be registered or
investigated as a rogue container.

---

## Step 3: Vault policy vs file drift

```bash
VAULT_TOKEN=$(cat ~/.vault-token)

# Policies in Vault
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault policy list | grep -v '^default$' | grep -v '^root$' | sort > /tmp/vault-policies.txt

# Policy files on disk
ls config/vault-policies/ | sed 's/-policy\.hcl//' | sort > /tmp/file-policies.txt

# In Vault but no file
comm -23 /tmp/vault-policies.txt /tmp/file-policies.txt

# File exists but not loaded in Vault
comm -13 /tmp/vault-policies.txt /tmp/file-policies.txt
```

---

## Step 4: AppRole vs local credential drift

```bash
VAULT_TOKEN=$(cat ~/.vault-token)

# AppRoles in Vault
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault list auth/approle/role | sort > /tmp/vault-approles.txt

# Local approle directories
ls ~/.vault-approle/ | sort > /tmp/local-approles.txt

# AppRole in Vault but no local credentials (provisioning gap)
comm -23 /tmp/vault-approles.txt /tmp/local-approles.txt

# Local directory but no AppRole in Vault (orphan directory)
comm -13 /tmp/vault-approles.txt /tmp/local-approles.txt
```

---

## Step 5: Caddy route vs backing service drift

```bash
# Extract .internal hostnames from Caddyfile
grep -E '^\S+\.internal' docker/caddy/Caddyfile | awk '{print $1}' | sort > /tmp/caddy-routes.txt

# For each route, check if backing service is reachable
while read route; do
  target=$(grep -A5 "^${route}" docker/caddy/Caddyfile | grep reverse_proxy | awk '{print $2}')
  if [ -n "$target" ]; then
    host=$(echo "$target" | cut -d: -f1)
    port=$(echo "$target" | cut -d: -f2)
    nc -z -w2 "$host" "$port" 2>/dev/null && echo "OK: $route → $target" || echo "DEAD: $route → $target (no listener)"
  fi
done < /tmp/caddy-routes.txt
```

DEAD routes should be pruned from the Caddyfile.

---

## Step 6: Container hardening drift

Check that cap_drop:[ALL] is applied to running containers:

```bash
docker ps -q | xargs -I{} docker inspect {} \
  --format '{{.Name}} cap_drop={{range .HostConfig.CapDrop}}{{.}},{{end}}' \
  | grep -v 'cap_drop=ALL' \
  | grep -v 'cap_drop=.*ALL'
```

Any container missing `cap_drop: ALL` that is not a documented exception
(cAdvisor, Obot-managed containers) should be flagged for remediation.

---

## Step 7: Out-of-repo compose snapshot check

```bash
# Check modification dates on out-of-repo composes
find ~/control-center-stack/stacks -name 'docker-compose.yml' -newer \
  ~/repos/integrated-ai-platform/docs/runbooks/rewire-log/.gitkeep 2>/dev/null \
  | sort
```

Any file modified more recently than the last rewire-log entry indicates
an undocumented change. Take a post-snapshot and create a rewire-log entry.

---

## Remediation

For each drift type:

| Drift | Remediation |
|---|---|
| Orphan container | `docker stop <name> && docker rm <name>` after confirming it's truly unmanaged |
| Missing NetBox registration | Add device/service entry in NetBox |
| Vault policy orphan | `vault policy delete <name>` after confirming no AppRole references it |
| Vault policy file-only | `vault policy write <name> config/vault-policies/<name>-policy.hcl` |
| AppRole orphan directory | `rm -rf ~/.vault-approle/<name>` after confirming AppRole deleted from Vault |
| Caddy dead route | Remove from Caddyfile; `docker exec caddy caddy reload --config /etc/caddy/Caddyfile` |
| Missing cap_drop | Add to compose file; `docker compose -f <stack> up -d <service>` |

---

## Post-drift-check gate

```bash
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
# Expected: FAIL=0, WARN ≤ 3
```

Document findings and remediations in `docs/runbooks/rewire-log/YYYY-MM-DD-drift-check.md`.
