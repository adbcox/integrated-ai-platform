# NetBox CMDB

**Stack:** NetBox 4.5 (image `v4.5-4.0.2`) + Postgres 18 + Valkey 9 ×2
**Phase:** 13 Block 4.C C2.2
**Vault auth:** AppRole `netbox` with policy `netbox-policy.hcl`
**Caddy route:** `https://netbox.internal` → host:127.0.0.1:8084
**Operator entrypoint:** `https://netbox.internal/login/`

## What this is

NetBox is the CMDB (Configuration Management Database) for the
platform — the source of truth for "what services exist, where,
with which dependencies." Phase 13 Block 4.C migrates the homegrown
`config/service-registry.yaml` into NetBox; the YAML is then
deprecated. Block 4.D layers InvenTree on top for hardware-asset
inventory; Block 4.E adds a cross-index service spanning the two.

## Stack topology

```
  ┌──────────────────────────────────────────────────────────┐
  │                  vault-server (separate stack)            │
  │                       AppRole: netbox                     │
  │                policy: config/vault-policies/             │
  │                        netbox-policy.hcl                  │
  └──────────────────────────────────────────────────────────┘
            ▲                 ▲              ▲              ▲
            │                 │              │              │
  ┌─────────┴────────┐ ┌──────┴──────┐ ┌─────┴──────┐ ┌─────┴───────┐
  │ vault-agent-     │ │ vault-agent-│ │ vault-agent│ │ vault-agent-│
  │   netbox         │ │   postgres  │ │   redis    │ │ redis-cache │
  │ (renders secrets │ │ (renders pw)│ │ (pw)       │ │ (pw)        │
  │  to env file)    │ │             │ │            │ │             │
  └────────┬─────────┘ └─────┬───────┘ └─────┬──────┘ └─────┬───────┘
           │                 │               │              │
           ▼                 ▼               ▼              ▼
  ┌──────────────┐  ┌────────────────┐ ┌───────────┐ ┌────────────┐
  │   netbox     │  │ netbox-postgres│ │netbox-redis│ │netbox-redis│
  │  + worker    │  │   (PG 18)      │ │ (Valkey 9) │ │   -cache   │
  │  + housekeep │  │                │ │            │ │ (Valkey 9) │
  └──────────────┘  └────────────────┘ └───────────┘ └────────────┘
         │
         ▼ port 127.0.0.1:8084
  ┌──────────────┐
  │     Caddy    │ → https://netbox.internal
  └──────────────┘
```

## Operations

### First-time provisioning

From the repo root on the Mac Mini:

```sh
# 1. Provision Vault policy, AppRole, secrets
sudo -E ./scripts/provision-netbox.sh   # idempotent

# 2. Bring up the stack
cd docker/netbox
/opt/homebrew/bin/docker compose up -d

# 3. Watch logs until netbox is healthy
/opt/homebrew/bin/docker logs -f netbox 2>&1 | grep -m1 "Listening on"

# 4. Create the superuser (one-shot, password from Vault)
/opt/homebrew/bin/docker exec vault-server \
  vault kv get -field=password secret/netbox/admin | \
  /opt/homebrew/bin/docker exec -i netbox \
    /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py \
      shell -c "
import sys
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
User = get_user_model()
pw = sys.stdin.read().rstrip('\n')
u, _ = User.objects.update_or_create(
  username='admin',
  defaults=dict(is_superuser=True, is_staff=True, is_active=True, password=make_password(pw)),
)
print('admin user ensured')
"

# 5. Generate API token (idempotent: returns existing if present)
/opt/homebrew/bin/docker exec netbox \
  /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py \
    shell -c "
from users.models import Token
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(username='admin')
t, _ = Token.objects.get_or_create(user=u, defaults={})
print(t.key)
" | /opt/homebrew/bin/docker exec -i vault-server \
    sh -c "vault kv put secret/netbox/api_token token=- >/dev/null"
```

### Hash-only verification

```sh
# Confirm a written secret matches the Vault copy without displaying.
H1=$(printf '%s' "$EXPECTED" | shasum -a 256 | awk '{print substr($1,1,12)}')
H2=$(/opt/homebrew/bin/docker exec vault-server \
       vault kv get -field=password secret/netbox/postgres | \
     shasum -a 256 | awk '{print substr($1,1,12)}')
[ "$H1" = "$H2" ] && echo OK || echo MISMATCH
```

### Upgrades

NetBox image tag is pinned in `docker-compose.yml`. To upgrade:

1. Pin a new tag in `docker-compose.yml`.
2. Snapshot Postgres (`docker exec netbox-postgres pg_dump …`).
3. `docker compose pull && docker compose up -d`.
4. Run any pending migrations: `docker exec netbox /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py migrate`.

### Backup

NetBox state lives in `netbox-postgres-data` and the three
file-volumes (`netbox-media-files`, `netbox-reports-files`,
`netbox-scripts-files`). The repo's `scripts/backup.sh` (Restic,
authenticated by the `backup` AppRole) is configured to capture
these named volumes nightly.

## Secret surface (KV paths)

| Path | Key | Purpose |
|---|---|---|
| `secret/netbox/postgres` | `password` | Postgres user password |
| `secret/netbox/redis` | `password` | Valkey database password |
| `secret/netbox/redis-cache` | `password` | Valkey cache password |
| `secret/netbox/secret_key` | `value` | Django SECRET_KEY |
| `secret/netbox/app` | `api_token_pepper` | NetBox API-token pepper |
| `secret/netbox/admin` | `password` | Bootstrap admin password |
| `secret/netbox/api_token` | `token` | API token (populated post-bootstrap) |

All keys generated by `scripts/provision-netbox.sh`. Rotation is
opt-in per key via `NETBOX_ROTATE_<KEY>=1` env vars on script
re-run.

## Hardening posture

| Container | cap_drop | cap_add | mem | read-only? |
|---|---|---|---|---|
| netbox | ALL | CHOWN, SETUID, SETGID, FOWNER, DAC_OVERRIDE, NET_BIND_SERVICE | 2g | no (Django collects static) |
| netbox-worker | ALL | CHOWN, SETUID, SETGID, FOWNER, DAC_OVERRIDE | 1g | no |
| netbox-housekeeping | ALL | CHOWN, SETUID, SETGID, FOWNER, DAC_OVERRIDE | 256m | no |
| netbox-postgres | ALL | CHOWN, SETUID, SETGID, DAC_OVERRIDE | 1g | no (PG writes) |
| netbox-redis | ALL | SETUID, SETGID | 512m | no (AOF) |
| netbox-redis-cache | ALL | SETUID, SETGID | 512m | no |
| All vault-agent-* sidecars | ALL | (none) | default | no |

`no-new-privileges: true` set universally.

## Troubleshooting

**Symptom:** netbox container restarts immediately, logs show
`KeyError: 'DB_PASSWORD'`. **Cause:** Vault Agent sidecar failed
to render `credentials.env`. **Fix:** Check
`docker logs vault-agent-netbox`; common causes are stale role-id
or secret-id in `~/.vault-approle/netbox/`. Re-run
`scripts/provision-netbox.sh` to refresh.

**Symptom:** `502 Bad Gateway` from Caddy at `netbox.internal`.
**Cause:** netbox container not yet healthy (check
`docker compose ps`). NetBox 4.5 first-boot can take 60–90s for
migrations.

**Symptom:** API client gets 401 with a token from
`secret/netbox/api_token`. **Cause:** Token revoked or admin
recreated. **Fix:** Re-run step 5 of First-time provisioning.

## Related artifacts

- `scripts/provision-netbox.sh` — Vault provisioning (idempotent)
- `config/vault-policies/netbox-policy.hcl` — Vault policy
- `docker/caddy/Caddyfile` — `netbox.internal` block
- `docs/phase-13/PHASE_13_BLOCK_4C_PLAN_2026-04-29.md` — phase plan
- `docs/phase-13/PHASE_13_BLOCK_4C_C1_AUDIT_2026-04-29.md` — architecture audit
