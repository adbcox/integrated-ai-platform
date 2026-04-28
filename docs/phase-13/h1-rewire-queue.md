# H1 §6 Rewire Queue — Authoritative Roster

**Generated**: 2026-04-28 (Phase 0 closure)
**Source of truth**: This file. Replaces all prior service-count statements in CHECKPOINT and RESULTS docs.

---

## Tracked deferred user actions

1. **seal-vault keys at temporary holding location**: `~/Documents/pending-offline-storage/seal-vault-keys.txt` (697 bytes, mode 600). User commits to moving to USB + printed copy in fire safe when higher-quality USB drive arrives (afternoon of 2026-04-28). **§14 fresh-session validation is gated on this completion.**

---

## Post-H1 follow-ups (deferred, non-blocking)

1. **Vaultwarden ADMIN_TOKEN format remediation**: token currently stored as plain text; vaultwarden's admin endpoint requires argon2-hashed format. Fix path: generate argon2 hash via `vaultwarden_argon2` utility (or the upstream-recommended `argon2` CLI), update `secret/vaultwarden/admin:admin_token`, `docker restart vaultwarden`. Estimated 15 min. Not blocking on §6 closure because admin endpoint is rarely used and user-facing /api remains functional. Filed during A.1 vaultwarden rewire (2026-04-28).

2. **Git history credential scrub**: Git history contains historical `.env` files. Current `LLM_API_KEY` is the ollama placeholder (`ollama-p...`), not a real secret. History scrub via `git-filter-repo` or BFG is scheduled for the same window as any other historical credential cleanup pass. Risk acceptance: ollama doesn't validate API keys, so the historical placeholder provides no actual access. Filed during A.3 openhands-app rewire (2026-04-28).

3. **openhands sandboxing verification**: `SANDBOX_RUNTIME_CONTAINER_IMAGE=openhands-runtime-custom:0.59` references a locally-built image not present on the host. Either openhands rebuilds on-demand (test by triggering a sandbox), or sandboxing has been broken since the image was deleted. Investigation steps: check openhands logs for runtime-image-build attempts; check last successful sandbox spawn date. Not blocking H1 because cred-delivery is independent of sandboxing functionality. Filed during A.3 openhands-app rewire (2026-04-28).

---

## §13 deferred to-do (CLAUDE.md cleanup pass)

1. **Compose-location split note**: Out-of-repo compose changes (`~/control-center-stack/stacks/*`) require pre/post snapshots in the rewire log because git won't track them automatically. Document in `CLAUDE.md` as a platform rule.

2. **Deprecate `bin/oss_wave_openhands.sh`**: Move to `bin/deprecated/` with header comment: "This launcher was the pre-compose path (docker run-based). openhands-app is now compose-managed via `docker/openhands/docker-compose.yml`. This file is retained for historical reference; do not invoke." Document deprecation in `CLAUDE.md` as a platform rule: pre-compose launcher scripts are deprecated; compose is the canonical lifecycle for all services. Filed during A.3 openhands-app rewire (2026-04-28).

---

## BP2 — plane stack rotation + rewire (6 services + obot)

Single coordinated rotation event:
- **Rotation hashes**: `secret/plane/db` sha `fad900280ce5` (length 5, weak default `plane`) → sha `0e1f80537ac8` (length 44, hex)
- **First attempt** used base64 — failed because resulting password contained `/` which broke DSN parsing in plane-migrate (`failed to resolve host 'plane'`). Re-rotated with hex (URL-safe).
- KV v2 versions: v1 (original weak), v2 (intermediate base64 — broken), v3 (current hex). Rollback paths exist for v1.

Services rewired (all reading rotated value):
- **plane-api**: 4-cred sidecar (DATABASE_URL with embedded password + SECRET_KEY + DEFAULT_PASSWORD + AWS_ACCESS_KEY_ID/SECRET_KEY for MinIO). Policy expanded to include `secret/data/plane/db`. Healthcheck passing.
- **plane-worker / plane-beat**: same 4-cred template (shared via copy). Policies expanded with `plane/admin + plane/minio + plane/db`. Both up.
- **plane-db**: 1-cred sidecar (POSTGRES_PASSWORD only). Healthy.
- **plane-minio**: 2-cred sidecar (MINIO_ROOT_USER + MINIO_ROOT_PASSWORD from `secret/plane/minio`). Up.
- **plane-web**: §7 hardening only (no creds; nginx static frontend).
- **plane-redis**: §7 hardening only (no creds).
- **plane-migrate / plane-minio-setup**: init containers; sidecar-aware (use plane-api / plane-minio respective renders). Both completed successfully on recreate.
- **obot**: 3-cred sidecar (OBOT_ADMIN_PASSWORD + GITHUB_TOKEN + POSTGRES_DSN with embedded plane password). Policy expanded with `secret/data/plane/db`. Vestigial POSTGRES_USER/PASSWORD/DB env vars removed. Health 200.

Architectural pattern added to canonical README: **credential-embedded URL rendering** with explicit URL-safe character requirement (hex over base64 for embedded credentials). Discovered during BP2 rotation; documented as sub-pattern.

Side findings:
- obot connects as `plane` superuser to plane DB — privilege separation post-H1 follow-up: provision separate obot user with scoped grants.
- plane-migrate/plane-minio-setup are init containers using sidecar renders; works but tightly coupled (if AppRole rotation needed for plane-api, the migrate init also depends on it).

Probe (BP2): PASS=13 FAIL=0 WARN=5 (warns: openhands DNS, homepage offline, restic creds Vault-only, 5 pre-existing/now-cleaned /tmp files).

## C.1 nextcloud — rewire log

- 2-cred sidecar (NEXTCLOUD_ADMIN_PASSWORD + POSTGRES_PASSWORD) rendered from `secret/nextcloud/{admin,db}`.
- Hash matches Vault for both.
- Image `nextcloud:29-apache`. Entrypoint `/entrypoint.sh`, Cmd `apache2-foreground`. Wrapper preserves both via `exec /entrypoint.sh "$0" "$@"` + Cmd `["apache2-foreground"]`.
- §7 hardening: cap_drop=[ALL], cap_add=[CHOWN, SETUID, SETGID, DAC_OVERRIDE, NET_BIND_SERVICE], no-new-privileges, mem_limit 512m, cpus 1.0.
- Deep probe `/ocs/v2.php/cloud/capabilities` → 200; data sanity unchanged (105 tables, 1 oc_users).
- `.env` disposition deferred — `docker/nextcloud/.env` retains both `NEXTCLOUD_ADMIN_PASSWORD` and `NEXTCLOUD_DB_PASSWORD` but neither is now consumed by nextcloud or nextcloud-db. Filing as Phase C cleanup.

## C.2/C.3 zabbix-server + zabbix-web — rewire log

- 1-cred sidecar each (POSTGRES_PASSWORD from `secret/zabbix/db`); hash matches.
- zabbix-server: original 4-arg Cmd preserved through exec wrapper. §7: cap_drop=[ALL]+NET_BIND_SERVICE, mem 2g (zabbix caches), cpus 2.0.
- zabbix-web: image had empty Cmd; entrypoint wrapper exec's docker-entrypoint.sh. §7: cap_drop=[ALL]+CHOWN/SETUID/SETGID/DAC_OVERRIDE/NET_BIND_SERVICE, mem 256m.
- Deep probe `/api_jsonrpc.php apiinfo.version` → 200 with `{"result":"7.4.9"}`; auth failure scan: empty.
- `.env` disposition deferred — `docker/zabbix/.env` still consumed by zabbix-agent (which has no AppRole and was unmodified). Phase C cleanup must verify zabbix-agent doesn't actually use POSTGRES_PASSWORD; if not, remove from agent's compose env interpolation and drain .env.

## C.4 obot — DEFERRED to Big Prompt 2 (architectural coupling)

obot's database credential is NOT separate — it IS plane's credential. obot's POSTGRES_DSN connects as user `plane` to database `plane` on docker-plane-db-1, sharing the credential stored in `secret/plane/db`. Verified hash equality:

- `obot DSN-embedded password sha256-12 = fad900280ce5`
- `secret/plane/db                 sha256-12 = fad900280ce5`

Confirmed plane-db has a single user `plane` (superuser) + single application database `plane` — no obot-specific user or DB.

Vestigial obot env vars (unused by obot when DSN is set; remove during rewire):
- `POSTGRES_USER=obot`
- `POSTGRES_PASSWORD=<weak length-4 value, hash ec929dcd98fb>`
- `POSTGRES_DB=obot`

Big Prompt 2 obot rewire requirements:
1. Update `config/vault-policies/obot-policy.hcl` to add `read` on `secret/data/plane/db` (currently grants only `obot/admin + github/api`).
2. Sidecar template renders `OBOT_ADMIN_PASSWORD`, `GITHUB_TOKEN`, AND a complete `POSTGRES_DSN=postgresql://plane:{{ .Data.data.password }}@docker-plane-db-1:5432/plane`.
3. Remove vestigial `POSTGRES_USER/PASSWORD/DB` from compose `environment:` (they're unused).
4. plane-db rotation in Big Prompt 2 implicitly rotates obot's connection — the rotated password is rendered into obot's DSN by the same Vault data update.
5. Recreate obot last (after plane-* services have new password active in their sidecars).

## B.3 plane-db Gap-7 verification — DEFERRED REWIRE

Gap-7: MATCH (Vault hash = container env hash, length 5 = upstream default). Rewire deferred to Big Prompt 2 with rotation per Option γ. Data baseline: users=2, projects=2 in `plane` database.

## B.2 zabbix-postgres — rewire log

- Gap-7 verification: MATCH (Vault sha=7e3ff814baef = container env hash, length 31, both via TCP auth probe).
- Compose service name is `postgres-server` (NOT `zabbix-postgres`); container_name overrides. AppRole + sidecar named `vault-agent-zabbix-postgres` (matches AppRole convention from Phase 0).
- Image: `timescale/timescaledb:latest-pg16` (postgres 16 + TimescaleDB extension; preserved verbatim from running config).
- Postgres command preserves all 16 `-c` tuning flags via the `exec docker-entrypoint.sh "$0" "$@"` pattern.
- §7 hardening: cap_drop=[ALL], cap_add=[CHOWN, SETUID, SETGID, DAC_OVERRIDE], no-new-privileges, mem_limit 512m (covers shared_buffers 256MB + maintenance_work_mem 128MB + headroom; baseline was 197 MiB but configured shared_buffers exceeds that), cpus 2.0.
- No Colima bind-mount visibility delay this time — RestartCount=0 on first startup. Confirms B.1 retry behavior was a one-off, not a guaranteed pattern; `restart: unless-stopped` is still required as defensive measure.
- zabbix UI deep probe `/api_jsonrpc.php apiinfo.version` → 200 with valid JSON `{"result":"7.4.9"}` (proves DB-backed chain).
- Data sanity: 207 public-schema tables + TimescaleDB internal schemas, 415 hosts, 2 users, 18973 items — identical pre/post.
- **Side finding (deferred)**: `secret/zabbix/db` has `database`, `password`, `username` fields; only `password` is a credential. Per Phase 0 doctrine should be cleaned to `password`-only, but skipped during B.2 to avoid scope creep. Filing as Phase B follow-up.
- `.env` disposition: `docker/zabbix/.env` retained with all 14 fields (POSTGRES_PASSWORD, ZBX_*, PHP_TZ, image tags, memory tuning). Zabbix-server, zabbix-web, zabbix-agent still consume `${POSTGRES_PASSWORD}` from env. zabbix-postgres no longer references `${POSTGRES_PASSWORD}`. Mixed state expected; closes in Phase C when zabbix-server, zabbix-web, zabbix-agent are rewired.
- Phase B follow-up: clean `secret/zabbix/db` to `password`-only field.

## B.1 nextcloud-db — rewire log

- Gap-7 verification: MATCH. Sha=7e5128a8078e at verification time.
- Rewire applied with full canonical pattern (sidecar + entrypoint wrapper + §7 hardening).
- §7 hardening: cap_drop=[ALL], cap_add=[CHOWN, SETUID, SETGID, DAC_OVERRIDE], no-new-privileges, mem_limit 256m, cpus 1.0. Memory baseline was 54 MiB but 150% (82m) would OOM postgres shared_buffers default; 256m is postgres-safe minimum.
- ROTATION (doctrine response to inadvertent value exposure during diagnostics): pre-rotation sha=7e5128a8078e (length 44, base64), post-rotation sha=f36e9aa8aa04 (length 44, base64 with `=` padding to match format). Vault audit captured event. ALTER USER ran cleanly via psql heredoc with value passed as env var (not argv). nextcloud's .env temporarily updated (option (i)) and nextcloud force-recreated to pick up new value; full chain re-verified via TCP auth + deep probe `/ocs/v2.php/cloud/capabilities` 200.
- Issues encountered: `--no-deps` misuse, Colima bind-mount visibility delay (16-retry recovery), hash-extraction newline trap (now baked into doctrine), inadvertent value exposure (now baked into doctrine).
- Canonical pattern README updated with 4 anti-patterns + KNOWN-LIMITATION + non-root verification path.

## Phase B follow-ups (deferred to post-Phase-B hygiene pass — 30 min bundled)

Pre-existing `/tmp/` files flagged by regression probe check (h). All pre-date B.1 rotation. Do NOT touch during B.2/B.3.

1. **`/tmp/ha-secrets.yaml`** — investigate before delete; confirm not actively read by Home Assistant container.
2. **`/tmp/rsl-token.html`** — investigate; likely test artifact.
3. **`/tmp/vault-secrets-only.txt`** — investigate; may contain real secret values from prior session work.
4. **(4th file flagged by probe)** — identify first via `ls /tmp/*pass* /tmp/*token* /tmp/*secret*`, then triage.

Single ~30-minute hygiene pass after Phase B completes.

## A.7 open-webui — rewire log

- 2-cred sidecar render: WEBUI_SECRET_KEY (from `secret/open-webui/app:secret_key`) + OPENAI_API_KEY (from `secret/litellm/master:master_key` — open-webui calls litellm via OpenAI-compatible API).
- Stack contains `homarr` (no creds) — left untouched, no sidecar.
- TRANSIENT CLOSED: open-webui's PID 1 environ post-A.7 has rotated `LITELLM_MASTER_KEY` (sha 439bcdb691d6, length 67); pre-A.7 had stale `sk-{platform}-master` (sha de61033bbd7e, length 17). Cross-service probe: open-webui → litellm /v1/models = HTTP 200.
- §7 hardening: cap_drop=[ALL], no-new-privileges, no privileged. **mem_limit not set** (preserved upstream config) — see Phase B follow-up below.
- ai-control/.env deleted; restart cycle confirms durability.

## Phase A close (gate A.8) follow-ups (deferred to Phase B+)

1. **open-webui mem_limit**: apply during Phase F vault compose revisit as part of combined §7 resource-tuning sweep. Do NOT recreate open-webui standalone for this — bundle with the broader §7 mem/cpu pass.
2. **Caddy regression probe (check d)** returned HTTP 000 due to TLS verification failure against Caddy's internal CA. Fix: either pass `-k` to curl, or add Caddy's root CA to the probe's trust store. Apply as first action of Phase B before B.1 starts.

## A.5 gateways stack (litellm-gateway + mcpo-proxy) — rewire log

- **OPENAI_API_KEY** in `secret/openai/api` is a template placeholder (`sk-your-...`, length 16). litellm_config.yaml routes `gpt-4o` model via `openai/...` provider. Populate with real key OR remove the openai routes from config. Filed during A.5 (2026-04-28).
- **LITELLM_MASTER_KEY rotation (Option γ)**: pre-rotation length=17 sha=de61033bbd7e (`sk-platform-master` upstream default); post-rotation length=67 sha=439bcdb691d6 (`sk-` + 32-byte hex). KV v2 metadata: pre-version=1, post-version=2 (rollback available via `vault kv rollback -version=1`). Audit log captured rotation read+write. Filed during A.5 (2026-04-28).
- **mcpo-proxy AppRole created** (was not in §5 inventory): policy grants only `secret/data/plane/api`; isolation verified (in-policy READ ✅, out-of-policy DENIED on litellm/master and anthropic/api).
- **Finding 7 resolution**: removed `secret/data/plane/api` from `litellm-gateway-policy.hcl` (litellm doesn't consume PLANE_API_TOKEN; mcpo-proxy does, owns its own AppRole).
- **TRANSIENT GAP — open-webui ↔ litellm**: Between A.6 close and A.7 close, open-webui has the old (pre-rotation) `LITELLM_MASTER_KEY` cached in its env. litellm-gateway now rejects the old value (HTTP 400). Open-webui chat UI is non-functional during this window. Resolution: A.7 rewire delivers rotated value via sidecar. **User: do not use open-webui UI until A.7 closes.** Filed during A.5/A.6 (2026-04-28).
- **Canonical pattern correction**: `exec` is now mandatory (not optional) in entrypoint wrapper. Reasons: signal propagation (SIGTERM goes to PID 1; without exec, sh wrapper is PID 1 and doesn't propagate to child app), verification-path consistency (PID 1 environ shows rendered creds for all services), no zombie wrapper processes. Discovered in A.5 mcpo (sh-c-with-&& pattern leaves sh as PID 1); fixed by inserting `exec` before the final app invocation. Empirical proof: docker stop went from 10s timeout → 0s clean shutdown.

## A.3 openhands-app — rewire log

- WORKSPACE_BASE quirk preserved verbatim from running container. Bind mount destination is `/opt/workspace`. Path mismatch could be intentional (parent-dir convention where openhands creates per-conversation subdirs) or pre-existing drift. Not investigating during §6; preserving running behavior to avoid scope creep.
- Vault `secret/openhands/llm` cleaned: pre-state had `api_key, base_url, model`; post-state has `api_key` only (KV v2 version 2). Per Phase 0 doctrine: secret paths contain ONLY credentials; operational config goes in compose `environment:`. KV v2 retains version 1 history; rollback via `vault kv rollback -version=1` if needed.
- Docker socket KNOWN-LIMITATION: `/var/run/docker.sock` mount required for openhands sandboxing. Gives effective host root regardless of caps. `cap_drop:[ALL]` reduces blast radius of OTHER attack vectors (openhands code vuln, poisoned LLM response, malicious package).

---

## Database password posture (Phase 0 spot-check)

| Path | Length | Strength | Action |
|---|---|---|---|
| `secret/nextcloud/db` | 44 (base64-shaped) | STRONG | none |
| `secret/zabbix/db` | 31 | STRONG | none |
| `secret/plane/db` | 5 (`p***e`, upstream default) | WEAK | **Rotate during Phase C plane rewire (Option γ)** |

Plane-db rotation procedure (executed during Phase C, before plane-api/web/worker/beat sidecar rewire):
1. Generate: `openssl rand -base64 32 | tr -d '/+=' | cut -c1-32`
2. `vault kv put secret/plane/db password=<new>`
3. `docker exec docker-plane-db-1 psql -U <user> -c "ALTER USER <user> WITH PASSWORD '<new>';"`
4. Recreate plane-{api,web,worker,beat} with sidecars reading new value
5. Then rewire plane-db with sidecar (Phase B step deferred to land after rotation)
6. Document old/new lengths + sha256 prefixes in rewire log for audit trail

---

## Service roster (16 active rewires)

Phases reflect dependency ordering and §6/§7 coordination doctrine (each service `docker compose up --force-recreate <svc>` exactly once with both sidecar AND §7 hardening applied).

| # | Service | AppRole | Vault paths | Cred fields | Phase | Compose location |
|---|---|---|---|---|---|---|
| 1 | vaultwarden | vaultwarden | `secret/vaultwarden/admin` | 1 (ADMIN_TOKEN) | A | `~/repos/integrated-ai-platform/docker/vaultwarden/` |
| 2 | openhands-app | openhands-app | `secret/openhands/llm` | 3 (api_key, base_url, model) | A | (TBD — bring under compose at `~/repos/integrated-ai-platform/docker/openhands/`) |
| 3 | litellm-gateway | litellm-gateway | 4 paths (anthropic, openai, litellm/master, plane/api*) | 3 confirmed + 1 to verify | A | `~/control-center-stack/stacks/gateways/` (out-of-repo) |
| 4 | open-webui | open-webui | `secret/open-webui/app, secret/litellm/master` | 2 (WEBUI_SECRET_KEY, OPENAI_API_KEY=litellm-master) | A | `~/control-center-stack/stacks/ai-control/` (out-of-repo) |
| 5 | nextcloud-db | nextcloud-db (NEW) | `secret/nextcloud/db` | 1 (POSTGRES_PASSWORD) | B | `~/repos/integrated-ai-platform/docker/nextcloud/` |
| 6 | zabbix-postgres | zabbix-postgres | `secret/zabbix/db` | 1 (POSTGRES_PASSWORD) | B | `~/repos/integrated-ai-platform/docker/zabbix/` |
| 7 | docker-plane-db | plane-db (NEW) | `secret/plane/db` | 1 (POSTGRES_PASSWORD, rotated in Phase C) | B (after rotation) | `~/repos/integrated-ai-platform/docker/` (`docker-compose-plane.yml`) |
| 8 | nextcloud | nextcloud | `secret/nextcloud/{admin,db}` | 2 (NEXTCLOUD_ADMIN_PASSWORD, POSTGRES_PASSWORD) | C | `~/repos/integrated-ai-platform/docker/nextcloud/` |
| 9 | zabbix-server | zabbix-server | `secret/zabbix/{admin,db}` | 2-3 (POSTGRES_PASSWORD primary; ZABBIX_ADMIN at first init only) | C | `~/repos/integrated-ai-platform/docker/zabbix/` |
| 10 | zabbix-web | zabbix-web | `secret/zabbix/{admin,db}` | 1-2 (POSTGRES_PASSWORD primary) | C | `~/repos/integrated-ai-platform/docker/zabbix/` |
| 11 | docker-plane-api | plane-api | `secret/plane/{admin,api,app,minio}` | 4+ (SECRET_KEY, AWS_*, REDIS, etc.) | C | `~/repos/integrated-ai-platform/docker/` |
| 12 | docker-plane-web | plane-web | `secret/plane/{admin,api}` | TBD (verified during rewire) | C | `~/repos/integrated-ai-platform/docker/` |
| 13 | docker-plane-worker | plane-worker | `secret/plane/{api,app}` | TBD | C | `~/repos/integrated-ai-platform/docker/` |
| 14 | docker-plane-beat | plane-beat | `secret/plane/{api,app}` | TBD | C | `~/repos/integrated-ai-platform/docker/` |
| 15 | docker-plane-minio | plane-minio (NEW) | `secret/plane/minio` | 2 (username, password) | C (with plane stack) | `~/repos/integrated-ai-platform/docker/` |
| 16 | obot | obot | `secret/obot/admin, secret/github/api` | 2 (OBOT_ADMIN_PASSWORD, GITHUB_TOKEN) | C | `~/repos/integrated-ai-platform/docker/` (`obot-stack.yml`) |

**Dropped from §6**: homepage (Gap 9 — not currently deployed; will be rewired at deploy-time using canonical pattern).

**No-sidecar services in rewire queue**: caddy (Phase E, §7 hardening only), vault-server (Phase F, §7 only).

## Naming convention

Sidecar container names follow `vault-agent-<approle-name>`. AppRoles match the table above. Application container names unchanged (e.g., `docker-plane-api-1` retains its name; sidecar is `vault-agent-plane-api`).

## Compose-location split

**In-repo** (git-tracked): vaultwarden, nextcloud, nextcloud-db, zabbix-{postgres,server,web}, plane (5 containers), obot, openhands-app (after compose conversion).
**Out-of-repo** (`~/control-center-stack/`, not git-tracked): litellm-gateway, open-webui.

Out-of-repo edits do not flow through standard git review. Pre/post snapshots written to `docs/phase-13/h1-rollback-state/<svc>-pre-rewire/` for both. To be documented in §13 CLAUDE.md platform rules.

## AppRole inventory (post Phase 0)

26 AppRoles total: 22 from §5 + `backup` (§2) + 3 new from Phase 0 (`nextcloud-db`, `plane-db`, `plane-minio`).

```
backup, grafana-obs, headscale, homeassistant, homepage, litellm-gateway,
nextcloud, nextcloud-db, obot, open-webui, openhands-app,
plane-api, plane-beat, plane-db, plane-minio, plane-web, plane-worker,
plex-mcp, prowlarr, radarr, sonarr, strava-sync, vaultwarden,
zabbix-postgres, zabbix-server, zabbix-web
```

Isolation verified for 3 new AppRoles: each can read its own path, denied on adjacent service paths.

## Render scope per service

**Doctrine**: sidecar templates render only credential fields. Non-cred config (POSTGRES_USER, POSTGRES_DB, etc.) stays in compose `environment:` block. This matches §5 policy granularity (paths granted only contain cred fields).

## Phase A sequencing (intra-phase gating)

A.1 vaultwarden — canonical pattern proof against simplest, already-compose-managed service.
A.2 GATE — pattern proven, README accurate, no flaws.
A.3 openhands-app — compose conversion + sidecar in one recreation.
A.4 GATE — openhands-app stable.
A.5 litellm-gateway.
A.6 GATE.
A.7 open-webui.
A.8 GATE — Phase A close.

Each intra-phase gate is independently passed before the next sub-service starts. No bundling of canonical-pattern proof with compose-conversion-plus-sidecar work on a never-compose-managed service.

## Per-service verification step — litellm-gateway (A.5)

**Phase A verification**: confirm whether `secret/plane/api` token is actually consumed by litellm. If not consumed, remove the path from `litellm-gateway-policy.hcl`. Don't carry over policy paths that aren't actually used.

litellm-gateway AppRole grants `secret/data/plane/api`. Container env shows LITELLM_MASTER_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, but PLANE_API_TOKEN was NOT visible in the running container env. During Phase A litellm rewire (step A.5), inspect the compose file for `PLANE_API_TOKEN`. If absent:
- Remove `path "secret/data/plane/api" { capabilities = ["read"] }` from `config/vault-policies/litellm-gateway-policy.hcl`
- Reload: `vault policy write litellm-gateway config/vault-policies/litellm-gateway-policy.hcl`
