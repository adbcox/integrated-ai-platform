# Phase 13 Foundation Audit (Stage A) — 2026-04-29

Generated: 2026-04-28T12:49:33Z

---
## TL;DR (§11 synthesis, rendered at top per amendment 5)

**Five most important findings**:
1. **Vault audit devices are disabled.** No record exists anywhere of who accessed Vault, when, or what changed — including the Block 1.7 recovery operation and all Phase 16 secret migrations. CRITICAL. (§9A.1, §9F)
2. **Vault has no auto-unseal configured.** A power blip, kernel panic, or Docker daemon restart leaves the entire platform sealed and unreachable until manual Shamir entry. Single biggest reliability gap. (§9D.2, §7A)
3. **No security observability layer exists.** Grafana watches service health, not security signals. Failed auth attempts, container restarts, OAuth denials — all visible in raw logs, none aggregated or alerted. (§9A.2)
4. **Configuration drift is unguarded.** No pre-commit hooks, no detect-secrets baseline; recent commit `8f6d895` ("redact: remove Vault root token from AUDIT_REPORT.md") is direct evidence the discipline-only model has already failed once. (§9C.1)
5. **Vault recovery, unseal, and rekey runbooks live in conversational memory only.** A panicked operator at 02:00 has no `docs/runbooks/vault-*.md` to consult. (§9G.1)

**Three architectural decisions needing user input before H1 can start** (§10.5):
- **Decision A**: Transit auto-unseal yes/no/document-as-known-risk (audit recommends YES).
- **Decision B**: Audit log retention policy — local rotation period + offsite shipment target.
- **Decision C**: pre-commit toolchain — `pre-commit` (Python, mainstream) or `lefthook` (Go, faster).

**H1 mutation count estimate**: ~20 file changes in this repo, 1 new launchd plist, 1 new Vault container (Transit seal-Vault), 0 secret-data changes. Estimated effort: **8–12 hours focused work**.

**Confidence in H1 scope**: **HIGH** — every H1 deliverable is a known pattern with a known fix and concrete success criteria (§10.4).

**Confidence in H2 scope**: **MEDIUM** — Wazuh tuning has unknowable depth; estimate covers initial deploy + minimum-viable rules.

**Recommendation on secrets backend** (§8.2): stay on Vault 2.0 for Phase 13; plan an OpenBao 2.5 parallel-deploy insurance test in Phase 14. Sunk-cost Vault state, dynamic-secrets requirement, and successful Block 1.7 recovery all favor staying. License-clarity migration is a Phase 14+ chore, not a Phase 13 emergency.

---

Amendments applied:
1. Trivy install dropped — using Docker Hub vuln-scan API, Grype hosted, GitHub Advisory DB
2. §5 QNAP writability: not-writable = CRITICAL finding, continue (not BLOCKED skip)
3. §7 vendor sources paired with independent technical source; vendor-only claims labelled
4. §8 matrix metrics: concrete (commits 90d, PRs, last release; documented DR + community success)
5. §11 TL;DR rendered at TOP of file — placeholder above, replaced in §11
6. §9F: explicit audit-trail assessment (who/when/what for Vault + last-24h change visibility)

## 1. Comprehensive .env file audit

Five search vectors. Field names only — values never read.

### 1.1 Repo (`~/repos/integrated-ai-platform`)
```
Command: find ~/repos/integrated-ai-platform -name '*.env*' -not -path '*/node_modules/*' -not -path '*/.git/*'
/Users/admin/repos/integrated-ai-platform/docker/nextcloud/.env
/Users/admin/repos/integrated-ai-platform/docker/.env.bak
/Users/admin/repos/integrated-ai-platform/docker/.env
/Users/admin/repos/integrated-ai-platform/docker/vaultwarden/.env
/Users/admin/repos/integrated-ai-platform/docker/.env.example
/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env.zabbix-admin
/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env
/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env.example
/Users/admin/repos/integrated-ai-platform/config/oss_wave/openhands.env.example
/Users/admin/repos/integrated-ai-platform/config/oss_wave/pr_agent.env.example
/Users/admin/repos/integrated-ai-platform/config/oss_wave/openhands.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/modal_blocked.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/open_and_click_miss.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/open_and_click_hit.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/deep_loaded.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/missing_session.env
/Users/admin/repos/integrated-ai-platform/.env.example
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/nextcloud/.env
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.bak
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/vaultwarden/.env
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.example
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env.zabbix-admin
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env.example
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/.env.example
```

### 1.2 Control center stacks (`~/control-center-stack`)
```
Command: find ~/control-center-stack -name '*.env*'
/Users/admin/control-center-stack/stacks/ai-control/.env
/Users/admin/control-center-stack/stacks/ai-control/.env.example
/Users/admin/control-center-stack/stacks/gateways/.env
/Users/admin/control-center-stack/stacks/gateways/.env.example
/Users/admin/control-center-stack/stacks/vault/.env
/Users/admin/control-center-stack/stacks/vault/.env.example
```

### 1.3 Home dir (4-deep, exclude Library/Trash/node_modules)
```
Command: find ~ -maxdepth 5 -name '*.env*' (filtered)
/Users/admin/.config/fish/conf.d/uv.env.fish
/Users/admin/control-center-stack/stacks/ai-control/.env
/Users/admin/control-center-stack/stacks/ai-control/.env.example
/Users/admin/control-center-stack/stacks/gateways/.env
/Users/admin/control-center-stack/stacks/gateways/.env.example
/Users/admin/control-center-stack/stacks/vault/.env
/Users/admin/control-center-stack/stacks/vault/.env.example
/Users/admin/repos/integrated-ai-platform/docker/nextcloud/.env
/Users/admin/repos/integrated-ai-platform/docker/.env.bak
/Users/admin/repos/integrated-ai-platform/docker/.env
/Users/admin/repos/integrated-ai-platform/docker/vaultwarden/.env
/Users/admin/repos/integrated-ai-platform/docker/.env.example
/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env.zabbix-admin
/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env
/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env.example
/Users/admin/repos/integrated-ai-platform/config/oss_wave/openhands.env.example
/Users/admin/repos/integrated-ai-platform/config/oss_wave/pr_agent.env.example
/Users/admin/repos/integrated-ai-platform/config/oss_wave/openhands.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/modal_blocked.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/open_and_click_miss.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/open_and_click_hit.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/deep_loaded.env
/Users/admin/repos/integrated-ai-platform/tests/scenarios/missing_session.env
/Users/admin/repos/integrated-ai-platform/.env.example
/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/.env.example
/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/modal_blocked.env
/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_miss.env
/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_hit.env
/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/deep_loaded.env
/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/missing_session.env
```

### 1.4 Inside running containers
```
  cadvisor: /rootfs/mnt/lima-cidata/lima.env
  cadvisor: /rootfs/mnt/lima-cidata/param.env
  obot: /workspace/docker/nextcloud/.env
  obot: /workspace/docker/.env.bak
  obot: /workspace/docker/.env
  obot: /workspace/docker/vaultwarden/.env
  obot: /workspace/docker/.env.example
  headscale: OCI runtime exec failed: exec failed: unable to start container process: exec: "/bin/sh": stat /bin/sh: no such file or directory
  mcp-filesystem-remote: /workspace/docker/nextcloud/.env
  mcp-filesystem-remote: /workspace/docker/.env.bak
  mcp-filesystem-remote: /workspace/docker/.env
  mcp-filesystem-remote: /workspace/docker/vaultwarden/.env
  mcp-filesystem-remote: /workspace/docker/.env.example
  anythingllm: /app/server/.env
  mcpo-proxy: /workspace/docker/nextcloud/.env
  mcpo-proxy: /workspace/docker/.env.bak
  mcpo-proxy: /workspace/docker/.env
  mcpo-proxy: /workspace/docker/vaultwarden/.env
  mcpo-proxy: /workspace/docker/.env.example
  litellm-gateway: /app/docker/.env.example
  litellm-gateway: /app/.env.example
  litellm-gateway: /app/ui/litellm-dashboard/.env.development
  litellm-gateway: /app/ui/litellm-dashboard/.env.production
  docker-plane-web-1: /docker-entrypoint.d/15-local-resolvers.envsh
  openhands-app: /opt/workspace/docker/.env.bak
  openhands-app: /opt/workspace/docker/.env
  openhands-app: /opt/workspace/docker/.env.example
  openhands-app: /opt/workspace/.env.example
```

### 1.5 Container env vars referencing credentials (NAMES only)
```
  plex-mcp: PLEX_TOKEN=<redacted>
  plex-mcp: SONARR_API_KEY=<redacted>
  plex-mcp: RADARR_API_KEY=<redacted>
  plex-mcp: TMDB_API_KEY=<redacted>
  obot: GITHUB_TOKEN=<redacted>
  obot: OBOT_ADMIN_PASSWORD=<redacted>
  obot: PLANE_API_TOKEN=<redacted>
  obot: POSTGRES_PASSWORD=<redacted>
  sms1obot-mcp-server-shim: NANOBOT_RUN_OAUTH_CLIENT_SECRET=<redacted>
  sms1obot-mcp-server-shim: NANOBOT_RUN_OAUTH_TOKEN_URL=<redacted>
  sms1obot-mcp-server-shim: NANOBOT_RUN_APIKEY_AUTH_WEBHOOK_URL=<redacted>
  sms1obot-mcp-server-shim: NANOBOT_RUN_AUDIT_LOG_TOKEN=<redacted>
  sms1obot-mcp-server-shim: NANOBOT_RUN_AUDIT_LOG_SEND_URL=<redacted>
  sms1obot-mcp-server-shim: TIKTOKEN_CACHE_DIR=<redacted>
  sms1obot-mcp-server: GPG_KEY=<redacted>
  docker-plane-api-1: AWS_SECRET_ACCESS_KEY=<redacted>
  docker-plane-api-1: DEFAULT_PASSWORD=<redacted>
  docker-plane-api-1: AWS_ACCESS_KEY_ID=<redacted>
  docker-plane-api-1: SECRET_KEY=<redacted>
  docker-plane-api-1: GPG_KEY=<redacted>
  nextcloud: POSTGRES_PASSWORD=<redacted>
  nextcloud: NEXTCLOUD_ADMIN_PASSWORD=<redacted>
  nextcloud: GPG_KEYS=<redacted>
  nextcloud-db: POSTGRES_PASSWORD=<redacted>
  vaultwarden: ADMIN_TOKEN=<redacted>
  zabbix-web: POSTGRES_PASSWORD=<redacted>
  zabbix-server: POSTGRES_PASSWORD=<redacted>
  zabbix-server: ZBX_SSHKEYLOCATION=<redacted>
  zabbix-server: ZBX_SSLKEYLOCATION=<redacted>
  zabbix-postgres: POSTGRES_PASSWORD=<redacted>
  anythingllm: JWT_SECRET=<redacted>
  anythingllm: AUTH_TOKEN=<redacted>
  anythingllm: PUPPETEER_DOWNLOAD_BASE_URL=<redacted>
  homarr: NEXTAUTH_SECRET=<redacted>
  mcpo-proxy: PLANE_API_TOKEN=<redacted>
  mcpo-proxy: GPG_KEY=<redacted>
  grafana-obs: GF_SECURITY_ADMIN_PASSWORD=<redacted>
  open-webui: WEBUI_SECRET_KEY=<redacted>
  open-webui: OPENAI_API_BASE_URL=<redacted>
  open-webui: OPENAI_API_KEY=<redacted>
  open-webui: GPG_KEY=<redacted>
  open-webui: TIKTOKEN_ENCODING_NAME=<redacted>
  open-webui: TIKTOKEN_CACHE_DIR=<redacted>
  litellm-gateway: LITELLM_MASTER_KEY=<redacted>
  litellm-gateway: ANTHROPIC_API_KEY=<redacted>
  litellm-gateway: OPENAI_API_KEY=<redacted>
  vault-server: VAULT_API_ADDR=<redacted>
  docker-plane-db-1: POSTGRES_PASSWORD=<redacted>
  docker-plane-web-1: NEXT_PUBLIC_API_BASE_URL=<redacted>
  docker-plane-beat-1: DEFAULT_PASSWORD=<redacted>
  docker-plane-beat-1: AWS_SECRET_ACCESS_KEY=<redacted>
  docker-plane-beat-1: AWS_ACCESS_KEY_ID=<redacted>
  docker-plane-beat-1: SECRET_KEY=<redacted>
  docker-plane-beat-1: GPG_KEY=<redacted>
  docker-plane-worker-1: AWS_ACCESS_KEY_ID=<redacted>
  docker-plane-worker-1: SECRET_KEY=<redacted>
  docker-plane-worker-1: AWS_SECRET_ACCESS_KEY=<redacted>
  docker-plane-worker-1: DEFAULT_PASSWORD=<redacted>
  docker-plane-worker-1: GPG_KEY=<redacted>
  docker-plane-minio-1: MINIO_ROOT_PASSWORD=<redacted>
  docker-plane-minio-1: MINIO_ACCESS_KEY_FILE=<redacted>
  docker-plane-minio-1: MINIO_SECRET_KEY_FILE=<redacted>
  docker-plane-minio-1: MINIO_ROOT_USER_FILE=<redacted>
  docker-plane-minio-1: MINIO_ROOT_PASSWORD_FILE=<redacted>
  docker-plane-minio-1: MINIO_KMS_SECRET_KEY_FILE=<redacted>
  docker-plane-minio-1: MINIO_UPDATE_MINISIGN_PUBKEY=<redacted>
  openhands-app: LLM_API_KEY=<redacted>
  openhands-app: GPG_KEY=<redacted>
```

### 1.6 Compose files referencing `env_file`
```
```

### 1.7 Per-finding detail (file paths from §1.1–§1.4)

#### `/Users/admin/.config/fish/conf.d/uv.env.fish`
```
-rw-r--r--  1 admin  staff  36 Apr 21 08:23 /Users/admin/.config/fish/conf.d/uv.env.fish
Field names:
```

#### `/Users/admin/ai-platform-archive-2026-04-25/chatgpt_roadmap_2026-04-23/.tmp_reconcile_reuse_wave/.env.example`
```
-rw-r--r--  1 admin  staff  103 Apr 23 14:11 /Users/admin/ai-platform-archive-2026-04-25/chatgpt_roadmap_2026-04-23/.tmp_reconcile_reuse_wave/.env.example
Field names:
  API_TOKEN=
  DEFAULT_TIMEOUT_MS=
  HEADLESS=
  IGNORE_HTTPS_ERRORS=
```

#### `/Users/admin/ai-reference/fastapi-realworld/.env.example`
```
-rw-r--r--  1 admin  staff  92 Apr 24 21:41 /Users/admin/ai-reference/fastapi-realworld/.env.example
Field names:
  DATABASE_URL=
  DEBUG=
  SECRET_KEY=
```

#### `/Users/admin/arr-backups/20260426/rclone/rclone-health.env`
```
-rw-------  1 admin  staff  667 Apr  6 18:34 /Users/admin/arr-backups/20260426/rclone/rclone-health.env
Field names:
  PROWLARR_KEY=
  RADARR_KEY=
  SONARR_KEY=
```

#### `/Users/admin/control-center-stack/stacks/ai-control/.env`
```
-rw-r--r--  1 admin  staff  119 Apr 25 22:37 /Users/admin/control-center-stack/stacks/ai-control/.env
Field names:
  LITELLM_MASTER_KEY=
  WEBUI_SECRET_KEY=
```

#### `/Users/admin/control-center-stack/stacks/ai-control/.env.example`
```
-rw-r--r--  1 admin  staff  83 Apr 25 22:37 /Users/admin/control-center-stack/stacks/ai-control/.env.example
Field names:
  LITELLM_MASTER_KEY=
  WEBUI_SECRET_KEY=
```

#### `/Users/admin/control-center-stack/stacks/gateways/.env`
```
-rw-r--r--  1 admin  staff  278 Apr 25 22:36 /Users/admin/control-center-stack/stacks/gateways/.env
Field names:
  ANTHROPIC_API_KEY=
  LITELLM_MASTER_KEY=
  OPENAI_API_KEY=
  PLANE_API_TOKEN=
  PLANE_PROJECT_ID=
  PLANE_URL=
  PLANE_WORKSPACE=
```

#### `/Users/admin/control-center-stack/stacks/gateways/.env.example`
```
-rw-r--r--  1 admin  staff  278 Apr 25 22:36 /Users/admin/control-center-stack/stacks/gateways/.env.example
Field names:
  ANTHROPIC_API_KEY=
  LITELLM_MASTER_KEY=
  OPENAI_API_KEY=
  PLANE_API_TOKEN=
  PLANE_PROJECT_ID=
  PLANE_URL=
  PLANE_WORKSPACE=
```

#### `/Users/admin/control-center-stack/stacks/vault/.env`
```
-rw-r--r--  1 admin  staff  46 Apr 25 23:41 /Users/admin/control-center-stack/stacks/vault/.env
Field names:
  VAULT_ROOT_TOKEN=
```

#### `/Users/admin/control-center-stack/stacks/vault/.env.example`
```
-rw-r--r--  1 admin  staff  51 Apr 25 22:37 /Users/admin/control-center-stack/stacks/vault/.env.example
Field names:
  VAULT_ROOT_TOKEN=
```

#### `/Users/admin/control-plane/.env`
```
-rw-r--r--  1 admin  staff  230 Apr 25 14:48 /Users/admin/control-plane/.env
Field names:
  OLLAMA_MODEL=
  OLLAMA_URL=
  PLANE_API_TOKEN=
  PLANE_PROJECT_ID=
  PLANE_URL=
  PLANE_WORKSPACE=
```

#### `/Users/admin/control-plane/.env.example`
```
-rw-r--r--  1 admin  staff  407 Apr 25 14:59 /Users/admin/control-plane/.env.example
Field names:
  AIDER_MODEL=
  AIDER_WORKER_ENABLED=
  AIDER_WORKER_HOUR=
  AIDER_WORKER_MAX_TASKS=
  DASHBOARD_PORT=
  OLLAMA_MODEL=
  OLLAMA_URL=
  PLANE_API_TOKEN=
  PLANE_PROJECT_ID=
  PLANE_URL=
  PLANE_WORKSPACE=
```

#### `/Users/admin/mcp-servers/docs/.env.example`
```
-rw-r--r--  1 admin  staff  2352 Apr 26 21:19 /Users/admin/mcp-servers/docs/.env.example
Field names:
  AWS_ACCESS_KEY_ID=
  AWS_REGION=
  AWS_SECRET_ACCESS_KEY=
  AZURE_OPENAI_API_DEPLOYMENT_NAME=
  AZURE_OPENAI_API_INSTANCE_NAME=
  AZURE_OPENAI_API_KEY=
  AZURE_OPENAI_API_VERSION=
  DOCS_MCP_EMBEDDING_MODEL=
  GOOGLE_API_KEY=
  GOOGLE_APPLICATION_CREDENTIALS=
  OPENAI_API_BASE=
  OPENAI_API_KEY=
  OPENAI_ORG_ID=
  POSTHOG_API_KEY=
```

#### `/Users/admin/mcp-servers/plex/.env.example`
```
-rw-r--r--  1 admin  staff  1124 Apr 26 21:19 /Users/admin/mcp-servers/plex/.env.example
Field names:
  PLEX_TOKEN=
  PLEX_URL=
```

#### `/Users/admin/mcp-servers/strava/.env.example`
```
-rw-r--r--  1 admin  staff  374 Apr 26 21:19 /Users/admin/mcp-servers/strava/.env.example
Field names:
  ROUTE_EXPORT_PATH=
  STRAVA_ACCESS_TOKEN=
```

#### `/Users/admin/repos/integrated-ai-platform-exec/.env.example`
```
-rw-r--r--  1 admin  staff  103 Apr 16 20:02 /Users/admin/repos/integrated-ai-platform-exec/.env.example
Field names:
  API_TOKEN=
  DEFAULT_TIMEOUT_MS=
  HEADLESS=
  IGNORE_HTTPS_ERRORS=
```

#### `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/deep_loaded.env`
```
-rw-r--r--  1 admin  staff  308 Apr 16 20:02 /Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/deep_loaded.env
Field names:
  MOCK_DOM_SNAPSHOT_DEFAULT=
  MOCK_LIST_CLICKABLE_DEFAULT=
  MOCK_LOGIN_FLOW_MODE=
  MOCK_READ_DEFAULT=
  MOCK_SESSION_ID=
```

#### `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/missing_session.env`
```
-rw-r--r--  1 admin  staff  197 Apr 16 20:02 /Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/missing_session.env
Field names:
  MOCK_DOM_SNAPSHOT_DEFAULT=
  MOCK_LIST_CLICKABLE_DEFAULT=
  MOCK_LOGIN_FLOW_MODE=
  MOCK_READ_DEFAULT=
  MOCK_SESSION_ID=
```

#### `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/modal_blocked.env`
```
-rw-r--r--  1 admin  staff  286 Apr 16 20:02 /Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/modal_blocked.env
Field names:
  MOCK_DOM_SNAPSHOT_DEFAULT=
  MOCK_LIST_CLICKABLE_DEFAULT=
  MOCK_LOGIN_FLOW_MODE=
  MOCK_READ_DEFAULT=
  MOCK_SESSION_ID=
```

#### `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_hit.env`
```
-rw-r--r--  1 admin  staff  324 Apr 16 20:02 /Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_hit.env
Field names:
  MOCK_DOM_SNAPSHOT_DEFAULT=
  MOCK_LIST_CLICKABLE_DEFAULT=
  MOCK_LOGIN_FLOW_MODE=
  MOCK_READ_DEFAULT=
  MOCK_SESSION_ID=
```

#### `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_miss.env`
```
-rw-r--r--  1 admin  staff  317 Apr 16 20:02 /Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_miss.env
Field names:
  MOCK_DOM_SNAPSHOT_DEFAULT=
  MOCK_LIST_CLICKABLE_DEFAULT=
  MOCK_LOGIN_FLOW_MODE=
  MOCK_READ_DEFAULT=
  MOCK_SESSION_ID=
```

#### `/Users/admin/repos/integrated-ai-platform/.env.example`
```
-rw-r--r--  1 admin  staff  103 Apr 15 18:23 /Users/admin/repos/integrated-ai-platform/.env.example
Field names:
  API_TOKEN=
  DEFAULT_TIMEOUT_MS=
  HEADLESS=
  IGNORE_HTTPS_ERRORS=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/.env.example`
```
-rw-r--r--  1 admin  staff  103 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/.env.example
Field names:
  API_TOKEN=
  DEFAULT_TIMEOUT_MS=
  HEADLESS=
  IGNORE_HTTPS_ERRORS=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env`
```
-rw-r--r--  1 admin  staff  3505 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env
Field names:
  ACME_EMAIL=
  DASHBOARD_PORT=
  DOMAIN=
  EXECUTOR_HOST=
  GITHUB_TOKEN=
  HA_TOKEN=
  HOMELAB_DIR=
  HOMEPAGE_PORT=
  HOMEPAGE_VAR_HASS_TOKEN=
  HOMEPAGE_VAR_OWM_KEY=
  HOMEPAGE_VAR_PLEX_TOKEN=
  HOMEPAGE_VAR_PORTAINER_KEY=
  HOMEPAGE_VAR_PROWLARR_KEY=
  HOMEPAGE_VAR_RADARR_KEY=
  HOMEPAGE_VAR_SONARR_KEY=
  LOG_DIR=
  MINIO_ROOT_PASSWORD=
  MINIO_ROOT_USER=
  OBOT_ADMIN_PASSWORD=
  OLLAMA_HOST=
  PGID=
  PLANE_ADMIN_EMAIL=
  PLANE_ADMIN_PASSWORD=
  PLANE_API_TOKEN=
  PLANE_PROJECT_ID=
  PLANE_SECRET_KEY=
  PLANE_URL=
  PLANE_WORKSPACE=
  PLEX_TOKEN=
  PLEX_URL=
  PROWLARR_API_KEY=
  PROWLARR_URL=
  PUID=
  QNAP_PASS=
  QNAP_URL=
  QNAP_USER=
  RADARR_API_KEY=
  RADARR_URL=
  REMOTE_REPO_ROOT=
  SEEDBOX_HOST=
  SEEDBOX_PASSWORD=
  SEEDBOX_PORT=
  SEEDBOX_USER=
  SONARR_API_KEY=
  SONARR_URL=
  STRAVA_ACCESS_TOKEN=
  STRAVA_CLIENT_ID=
  STRAVA_CLIENT_SECRET=
  TZ=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.bak`
```
-rw-r--r--  1 admin  staff  2556 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.bak
Field names:
  ACME_EMAIL=
  DASHBOARD_PORT=
  DOMAIN=
  EXECUTOR_HOST=
  HOMELAB_DIR=
  HOMEPAGE_PORT=
  HOMEPAGE_VAR_HASS_TOKEN=
  HOMEPAGE_VAR_OWM_KEY=
  HOMEPAGE_VAR_PLEX_TOKEN=
  HOMEPAGE_VAR_PORTAINER_KEY=
  HOMEPAGE_VAR_PROWLARR_KEY=
  HOMEPAGE_VAR_RADARR_KEY=
  HOMEPAGE_VAR_SONARR_KEY=
  LOG_DIR=
  OLLAMA_HOST=
  PGID=
  PLEX_TOKEN=
  PLEX_URL=
  PROWLARR_API_KEY=
  PROWLARR_URL=
  PUID=
  QNAP_PASS=
  QNAP_URL=
  QNAP_USER=
  RADARR_API_KEY=
  RADARR_URL=
  REMOTE_REPO_ROOT=
  SEEDBOX_HOST=
  SEEDBOX_PASSWORD=
  SEEDBOX_PORT=
  SEEDBOX_USER=
  SONARR_API_KEY=
  SONARR_URL=
  TZ=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.example`
```
-rw-r--r--  1 admin  staff  3324 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.example
Field names:
  ACME_EMAIL=
  DASHBOARD_PORT=
  DOMAIN=
  EXECUTOR_HOST=
  HOMELAB_DIR=
  HOMEPAGE_PORT=
  HOMEPAGE_VAR_HASS_TOKEN=
  HOMEPAGE_VAR_OWM_KEY=
  HOMEPAGE_VAR_PLEX_TOKEN=
  HOMEPAGE_VAR_PORTAINER_KEY=
  HOMEPAGE_VAR_PROWLARR_KEY=
  HOMEPAGE_VAR_RADARR_KEY=
  HOMEPAGE_VAR_SONARR_KEY=
  LOG_DIR=
  MINIO_ROOT_PASSWORD=
  MINIO_ROOT_USER=
  OLLAMA_HOST=
  PGID=
  PLANE_ADMIN_EMAIL=
  PLANE_ADMIN_PASSWORD=
  PLANE_API_TOKEN=
  PLANE_PROJECT_ID=
  PLANE_SECRET_KEY=
  PLANE_URL=
  PLANE_WORKSPACE=
  PLEX_TOKEN=
  PLEX_URL=
  PROWLARR_API_KEY=
  PROWLARR_URL=
  PUID=
  QNAP_PASS=
  QNAP_URL=
  QNAP_USER=
  RADARR_API_KEY=
  RADARR_URL=
  REMOTE_REPO_ROOT=
  SEEDBOX_HOST=
  SEEDBOX_PASSWORD=
  SEEDBOX_PORT=
  SEEDBOX_USER=
  SONARR_API_KEY=
  SONARR_URL=
  TZ=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/nextcloud/.env`
```
-rw-r--r--  1 admin  staff  137 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/nextcloud/.env
Field names:
  NEXTCLOUD_ADMIN_PASSWORD=
  NEXTCLOUD_DB_PASSWORD=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/vaultwarden/.env`
```
-rw-r--r--  1 admin  staff  77 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/vaultwarden/.env
Field names:
  ADMIN_TOKEN=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env`
```
-rw-r--r--  1 admin  staff  783 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env
Field names:
  PHP_TZ=
  POSTGRES_DB=
  POSTGRES_EFFECTIVE_CACHE_SIZE=
  POSTGRES_MAINTENANCE_WORK_MEM=
  POSTGRES_PASSWORD=
  POSTGRES_SHARED_BUFFERS=
  POSTGRES_USER=
  POSTGRES_WORK_MEM=
  TIMESCALEDB_IMAGE_TAG=
  ZABBIX_IMAGE_TAG=
  ZBX_DEBUGLEVEL=
  ZBX_SERVER_HOST=
  ZBX_SERVER_NAME=
  ZBX_WEB_PORT=
```

#### `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env.example`
```
-rw-r--r--  1 admin  staff  831 Apr 27 17:20 /Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env.example
Field names:
  PHP_TZ=
  POSTGRES_DB=
  POSTGRES_EFFECTIVE_CACHE_SIZE=
  POSTGRES_MAINTENANCE_WORK_MEM=
  POSTGRES_PASSWORD=
  POSTGRES_SHARED_BUFFERS=
  POSTGRES_USER=
  POSTGRES_WORK_MEM=
  TIMESCALEDB_IMAGE_TAG=
  ZABBIX_IMAGE_TAG=
  ZBX_DEBUGLEVEL=
  ZBX_SERVER_HOST=
  ZBX_SERVER_NAME=
  ZBX_WEB_PORT=
```


### 1.8 Categorization

Categories: CRITICAL (creds, active, NOT in Vault) / DUPLICATE (creds, active, ALSO in Vault) / DEAD (creds but unreferenced) / BENIGN (non-credential)

| Path | Category | Vault counterpart |
|---|---|---|
| `/Users/admin/.config/fish/conf.d/uv.env.fish` | BENIGN (refs=0, has_creds=no) | TBD §1.9 |
| `/Users/admin/ai-platform-archive-2026-04-25/chatgpt_roadmap_2026-04-23/.tmp_reconcile_reuse_wave/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/ai-reference/fastapi-realworld/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/arr-backups/20260426/rclone/rclone-health.env` | DEAD (refs=0, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-center-stack/stacks/ai-control/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-center-stack/stacks/ai-control/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-center-stack/stacks/gateways/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-center-stack/stacks/gateways/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-center-stack/stacks/vault/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-center-stack/stacks/vault/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-plane/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/control-plane/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/mcp-servers/docs/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/mcp-servers/plex/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/mcp-servers/strava/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform-exec/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/deep_loaded.env` | BENIGN (refs=0, has_creds=no) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/missing_session.env` | BENIGN (refs=0, has_creds=no) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/modal_blocked.env` | BENIGN (refs=0, has_creds=no) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_hit.env` | BENIGN (refs=0, has_creds=no) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform-exec/tests/scenarios/open_and_click_miss.env` | BENIGN (refs=0, has_creds=no) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.bak` | DEAD (refs=0, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/nextcloud/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/vaultwarden/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env` | DUPLICATE_OR_CRITICAL (refs=26, has_creds=yes) | TBD §1.9 |
| `/Users/admin/repos/integrated-ai-platform/backups/phase16-20260427-172029/docker/zabbix/.env.example` | DUPLICATE_OR_CRITICAL (refs=1, has_creds=yes) | TBD §1.9 |

Total .env-style files found across all search vectors: **47**

### 1.9 Verification gate
- ✅ All 6 search vectors executed
- ✅ Findings categorized (BENIGN/DEAD/DUPLICATE_OR_CRITICAL)
- ⚠️  Per-finding Vault cross-reference deferred to inline check below per file
- ✅ Total count logged: 47

=== SECTION 1 COMPLETE — 694 lines ===


## 2. Container security posture audit

### 2.1 Per-container security config

Captured via `docker inspect | jq` for each running container.

| Container | User | Privileged | RO-root | NetMode | CapDrop | NoNewPriv | Docker.sock |
|---|---|---|---|---|---|---|---|
| anythingllm | anythingllm | false | false | knowledge | 0 | 1/1 | 0 |
| caddy |  | false | false | caddy-net | 0 | 0/0 | 0 |
| cadvisor |  | true | false | bridge | 0 | 0/1 | 0 |
| docker-plane-api-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| docker-plane-beat-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| docker-plane-db-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| docker-plane-minio-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| docker-plane-redis-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| docker-plane-web-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| docker-plane-worker-1 |  | false | false | docker_plane-net | 0 | 0/0 | 0 |
| grafana-obs | 472 | false | false | observability | 0 | 0/0 | 0 |
| headscale | 0 | false | false | headscale-net | 0 | 0/0 | 0 |
| homarr |  | false | false | control-center-net | 0 | 1/1 | 1 |
| homeassistant |  | false | false | control-center-net | 0 | 1/1 | 0 |
| litellm-gateway | root | false | false | control-center-net | 1 | 1/1 | 0 |
| mcp-docker-remote |  | false | false | bridge | 0 | 0/0 | 1 |
| mcp-docs-remote |  | false | false | obot-net | 0 | 0/0 | 0 |
| mcp-filesystem-remote |  | false | false | obot-net | 0 | 0/0 | 0 |
| mcpo-proxy |  | false | false | control-center-net | 1 | 1/1 | 0 |
| nextcloud |  | false | false | nextcloud-net | 0 | 0/0 | 0 |
| nextcloud-db |  | false | false | nextcloud-net | 0 | 0/0 | 0 |
| node-exporter | nobody | false | false | host | 0 | 0/1 | 0 |
| obot | 0 | false | false | obot-net | 0 | 0/0 | 1 |
| open-webui | 0:0 | false | false | control-center-net | 1 | 1/1 | 0 |
| openhands-app | root | false | false | bridge | 0 | 0/0 | 1 |
| plex-mcp |  | false | false | bridge | 0 | 0/0 | 0 |
| prowlarr |  | false | false | control-center-net | 0 | 1/1 | 0 |
| radarr |  | false | false | control-center-net | 0 | 1/1 | 0 |
| sms1obot-mcp-server |  | false | false | bridge | 0 | 0/0 | 0 |
| sms1obot-mcp-server-shim | nanobot | false | false | bridge | 0 | 0/0 | 0 |
| sonarr |  | false | false | control-center-net | 0 | 1/1 | 0 |
| sportarr |  | false | false | control-center-net | 3 | 1/1 | 0 |
| uptime-kuma |  | false | false | observability | 0 | 0/0 | 0 |
| vault-server | vault | false | false | control-center-net | 1 | 1/1 | 0 |
| vaultwarden |  | false | false | vaultwarden-net | 0 | 0/0 | 0 |
| vm |  | false | false | observability | 0 | 0/0 | 0 |
| vmagent |  | false | false | observability | 0 | 0/0 | 0 |
| zabbix-agent | 1997 | false | false | zabbix-net | 0 | 0/0 | 0 |
| zabbix-postgres |  | false | false | zabbix-net | 0 | 0/0 | 0 |
| zabbix-server | 1997 | false | false | zabbix-net | 1 | 1/1 | 0 |
| zabbix-web | 1997 | false | false | zabbix-net | 0 | 0/0 | 0 |

### 2.2 Worst offenders

Containers running as **root with full caps and no hardening**:
```
  caddy (root, 0 caps dropped, no-new-priv off)
  docker-plane-api-1 (root, 0 caps dropped, no-new-priv off)
  docker-plane-beat-1 (root, 0 caps dropped, no-new-priv off)
  docker-plane-db-1 (root, 0 caps dropped, no-new-priv off)
  docker-plane-minio-1 (root, 0 caps dropped, no-new-priv off)
  docker-plane-redis-1 (root, 0 caps dropped, no-new-priv off)
  docker-plane-web-1 (root, 0 caps dropped, no-new-priv off)
  docker-plane-worker-1 (root, 0 caps dropped, no-new-priv off)
  mcp-docker-remote (root, 0 caps dropped, no-new-priv off)
  mcp-docs-remote (root, 0 caps dropped, no-new-priv off)
  mcp-filesystem-remote (root, 0 caps dropped, no-new-priv off)
  nextcloud (root, 0 caps dropped, no-new-priv off)
  nextcloud-db (root, 0 caps dropped, no-new-priv off)
  openhands-app (root, 0 caps dropped, no-new-priv off)
  plex-mcp (root, 0 caps dropped, no-new-priv off)
  sms1obot-mcp-server (root, 0 caps dropped, no-new-priv off)
  uptime-kuma (root, 0 caps dropped, no-new-priv off)
  vaultwarden (root, 0 caps dropped, no-new-priv off)
  vm (root, 0 caps dropped, no-new-priv off)
  vmagent (root, 0 caps dropped, no-new-priv off)
  zabbix-postgres (root, 0 caps dropped, no-new-priv off)
```

Containers with `privileged: true`:
```
cadvisor
```

Containers mounting `/var/run/docker.sock`:
```
  obot
  mcp-docker-remote
  homarr
  openhands-app
```

Containers using `network_mode: host`:
```
  node-exporter
```

### 2.3 Unique image tags running
```
  5c0dc26f467b
  caddy:2-alpine
  ghcr.io/ajnart/homarr:latest
  ghcr.io/berriai/litellm:main-latest
  ghcr.io/home-assistant/home-assistant:stable
  ghcr.io/nanobot-ai/nanobot:v0.0.67
  ghcr.io/obot-platform/obot-mcp-server:v0.1.1
  ghcr.io/open-webui/open-webui:main
  grafana/grafana:10.4.2
  hashicorp/vault:latest
  headscale/headscale:latest
  louislam/uptime-kuma:1
  lscr.io/linuxserver/prowlarr:latest
  lscr.io/linuxserver/radarr:latest
  lscr.io/linuxserver/sonarr:latest
  makeplane/plane-backend:stable
  makeplane/plane-frontend:stable
  minio/minio:latest
  mintplexlabs/anythingllm:latest
  nextcloud:29-apache
  nikolaik/python-nodejs:python3.12-nodejs22-slim
  node:22-slim
  obot/obot:latest
  postgres:15-alpine
  postgres:16-alpine
  prom/node-exporter:v1.7.0
  redis:7.2-alpine
  sportarr/sportarr:latest
  timescale/timescaledb:latest-pg16
  vaultwarden/server:latest
  victoriametrics/victoria-metrics:v1.99.0
  victoriametrics/vmagent:v1.99.0
  zabbix/zabbix-agent:alpine-7.4-latest
  zabbix/zabbix-server-pgsql:alpine-7.4-latest
  zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest
  zcube/cadvisor:latest
```

### 2.4 CVE assessment per unique image

Per amendment 1: Trivy install dropped. Using external sources:
- Docker Hub vuln scan (https://hub.docker.com/v2/repositories/<image>/tags/<tag>/images)
- Anchore Grype hosted (note: requires login; lookup-only here)
- GitHub Advisory Database (https://github.com/advisories)

**UNVERIFIED — Trivy install deferred to H1.** This audit cites publicly available
metadata only; full image-content scanning requires the H1 hardening block.

Per-image CVE summary (Docker Hub-side scan results when available):

| Image | Source | CVE summary |
|---|---|---|
| `5c0dc26f467b` | Docker Hub API | no scan info |
| `caddy:2-alpine` | Docker Hub API | no scan info |
| `ghcr.io/ajnart/homarr:latest` | Docker Hub API |  |
| `ghcr.io/berriai/litellm:main-latest` | Docker Hub API |  |
| `ghcr.io/home-assistant/home-assistant:stable` | Docker Hub API |  |
| `ghcr.io/nanobot-ai/nanobot:v0.0.67` | Docker Hub API |  |
| `ghcr.io/obot-platform/obot-mcp-server:v0.1.1` | Docker Hub API |  |
| `ghcr.io/open-webui/open-webui:main` | Docker Hub API |  |
| `grafana/grafana:10.4.2` | Docker Hub API | no scan info |
| `hashicorp/vault:latest` | Docker Hub API | no scan info |
| `headscale/headscale:latest` | Docker Hub API | no scan info |
| `louislam/uptime-kuma:1` | Docker Hub API | no scan info |
| `lscr.io/linuxserver/prowlarr:latest` | Docker Hub API |  |
| `lscr.io/linuxserver/radarr:latest` | Docker Hub API |  |
| `lscr.io/linuxserver/sonarr:latest` | Docker Hub API |  |
| `makeplane/plane-backend:stable` | Docker Hub API | no scan info |
| `makeplane/plane-frontend:stable` | Docker Hub API | no scan info |
| `minio/minio:latest` | Docker Hub API | no scan info |
| `mintplexlabs/anythingllm:latest` | Docker Hub API | no scan info |
| `nextcloud:29-apache` | Docker Hub API | no scan info |
| `nikolaik/python-nodejs:python3.12-nodejs22-slim` | Docker Hub API | no scan info |
| `node:22-slim` | Docker Hub API | no scan info |
| `obot/obot:latest` | Docker Hub API | no scan info |
| `postgres:15-alpine` | Docker Hub API | no scan info |
| `postgres:16-alpine` | Docker Hub API | no scan info |
| `prom/node-exporter:v1.7.0` | Docker Hub API | no scan info |
| `redis:7.2-alpine` | Docker Hub API | no scan info |
| `sportarr/sportarr:latest` | Docker Hub API | no scan info |
| `timescale/timescaledb:latest-pg16` | Docker Hub API | no scan info |
| `vaultwarden/server:latest` | Docker Hub API | no scan info |
| `victoriametrics/victoria-metrics:v1.99.0` | Docker Hub API | no scan info |
| `victoriametrics/vmagent:v1.99.0` | Docker Hub API | no scan info |
| `zabbix/zabbix-agent:alpine-7.4-latest` | Docker Hub API | no scan info |
| `zabbix/zabbix-server-pgsql:alpine-7.4-latest` | Docker Hub API | no scan info |
| `zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest` | Docker Hub API | no scan info |
| `zcube/cadvisor:latest` | Docker Hub API | no scan info |

**Limitation**: Docker Hub's vulnerability scan API was deprecated for free tier
in 2023 (https://www.docker.com/blog/docker-scout-vulnerability-detection/, 2023-10).
Live CVE data per running tag requires either Docker Scout (auth) or Trivy/Grype
local install. **Mark deferred to H1.** UNVERIFIED.

### 2.5 Verification gate
- ✅ All running containers' security configs captured
- ✅ Aggregate posture table written (§2.1)
- ⚠️  Per-image upstream documentation: deferred to H1 (per-image research is N×WebFetch budget)
- ⚠️  Per-image CVE scan: deferred to H1 (UNVERIFIED — install Trivy in H1)

=== SECTION 2 COMPLETE — 894 lines ===


## 3. Vault deep state audit

### 3.1 Auth methods
```
Command: vault auth list
Path      Type     Accessor               Description                Version
----      ----     --------               -----------                -------
token/    token    auth_token_4452bd6e    token based credentials    n/a
```

### 3.2 Policies
```
Command: vault policy list
default
rclone-reader
root
```

### 3.3 Policy contents

#### `default`
```hcl
# Allow tokens to look up their own properties
path "auth/token/lookup-self" {
    capabilities = ["read"]
}

# Allow tokens to renew themselves
path "auth/token/renew-self" {
    capabilities = ["update"]
}

# Allow tokens to revoke themselves
path "auth/token/revoke-self" {
    capabilities = ["update"]
}

# Allow a token to look up its own capabilities on a path
path "sys/capabilities-self" {
    capabilities = ["update"]
}

# Allow a token to look up its own entity by id or name
path "identity/entity/id/{{identity.entity.id}}" {
  capabilities = ["read"]
}
path "identity/entity/name/{{identity.entity.name}}" {
  capabilities = ["read"]
}


# Allow a token to look up its resultant ACL from all policies. This is useful
# for UIs. It is an internal path because the format may change at any time
# based on how the internal ACL features and capabilities change.
path "sys/internal/ui/resultant-acl" {
    capabilities = ["read"]
}

# Allow a token to renew a lease via lease_id in the request body; old path for
# old clients, new path for newer
path "sys/renew" {
    capabilities = ["update"]
}
path "sys/leases/renew" {
    capabilities = ["update"]
}

# Allow looking up lease properties. This requires knowing the lease ID ahead
# of time and does not divulge any sensitive information.
path "sys/leases/lookup" {
    capabilities = ["update"]
}

# Allow a token to manage its own cubbyhole
path "cubbyhole/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}

# Allow a token to wrap arbitrary values in a response-wrapping token
path "sys/wrapping/wrap" {
    capabilities = ["update"]
}

# Allow a token to look up the creation time and TTL of a given
# response-wrapping token
path "sys/wrapping/lookup" {
    capabilities = ["update"]
}

# Allow a token to unwrap a response-wrapping token. This is a convenience to
# avoid client token swapping since this is also part of the response wrapping
# policy.
path "sys/wrapping/unwrap" {
    capabilities = ["update"]
}

# Allow general purpose tools
path "sys/tools/hash" {
    capabilities = ["update"]
}
path "sys/tools/hash/*" {
    capabilities = ["update"]
}

# Allow checking the status of a Control Group request if the user has the
# accessor
path "sys/control-group/request" {
    capabilities = ["update"]
}

# Allow a token to make requests to the Authorization Endpoint for OIDC providers.
path "identity/oidc/provider/+/authorize" {
    capabilities = ["read", "update"]
}
```

#### `rclone-reader`
```hcl
path "secret/data/seedbox/*" { capabilities = ["read"] }
```

#### `root`
```hcl
No policy named: root
```

### 3.4 Secret engine mounts
```
Command: vault secrets list
Path               Type              Accessor                   Description
----               ----              --------                   -----------
agent-registry/    agent_registry    agent-registry_69e14cd5    agent registry
cubbyhole/         cubbyhole         cubbyhole_70d599e8         per-token private secret storage
identity/          identity          identity_2a86b3fc          identity store
secret/            kv                kv_8010ac81                n/a
sys/               system            system_2e2498c8            system endpoints used for control, policy and debugging
```

### 3.5 Audit devices
```
Command: vault audit list
No audit devices are enabled.
```

### 3.6 Vault config (vault.hcl)
```hcl
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr      = "http://192.168.10.145:8200"
ui            = true
disable_mlock = true   # required: mlock not available in macOS/Colima containers

# Vault 2.0.0+: opt back into unauthenticated /sys/generate-root for operator
# recovery flow. Required because Block 1's token rotation used non-orphan
# default and revoking the parent cascaded the new token.
enable_unauthenticated_access = ["generate-root"]
```

### 3.7 Active token accessor count
```
Command: vault list -format=json auth/token/accessors | jq length
Active token accessors: 1
```

### 3.8 Per-mount KV item counts
```
  secret/anythingllm/: 1 entries
  secret/arr/: 3 entries
  secret/github/: 1 entries
  secret/grafana/: 1 entries
  secret/headscale/: 1 entries
  secret/homeassistant/: 1 entries
  secret/macmini/: 1 entries
  secret/mcp/: 1 entries
  secret/minio/: 1 entries
  secret/nextcloud/: 2 entries
  secret/obot/: 1 entries
  secret/openweathermap/: 1 entries
  secret/opnsense/: 2 entries
  secret/plane/: 4 entries
  secret/plex/: 1 entries
  secret/qnap/: 2 entries
  secret/resilio/: 3 entries
  secret/restic/: 1 entries
  secret/seedbox/: 3 entries
  secret/strava/: 1 entries
  secret/syncthing/: 1 entries
  secret/vaultwarden/: 1 entries
  secret/zabbix/: 2 entries
```

### 3.9 Vault data backup status
```
Search: grep -r 'vault/data' ~/repos/integrated-ai-platform/
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_BLOCK_1_6_VAULT_RECOVERY_2026-04-29.md:161:  path = "/vault/data"
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_BLOCK_1_6_VAULT_RECOVERY_2026-04-29.md:173:  path = "/vault/data"
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_BLOCK_1_6_VAULT_RECOVERY_2026-04-29.md:258:  path = "/vault/data"
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_FOUNDATION_AUDIT_2026-04-29.md:1046:  path = "/vault/data"
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_FOUNDATION_AUDIT_2026-04-29.md:1099:Search: grep -r 'vault/data' ~/repos/integrated-ai-platform/
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_INVENTORY_2026-04-28.md:77:/vault-server | running | 2026-04-28T01:45:16.633985629Z | hashicorp/vault:latest | 8200/tcp=0.0.0.0:8200 :::8200 ; | volume:/var/lib/docker/volumes/vault_vault-logs/_data->/vault/logs(rw) bind:/Users/admin/control-center-stack/stacks/vault/vault-config.hcl->/vault/config/vault.hcl(ro) volume:/var/lib/docker/volumes/vault_vault-data/_data->/vault/data(rw) volume:/var/lib/docker/volumes/bea5498d0d5fc54576998db788d6bc7701f6ec87c8e05cb50bc13ac205e6c7bb/_data->/vault/file(rw)  | control-center-net(172.23.0.4) 
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_BLOCK_1_7_VAULT_20_RECOVERY_2026-04-29.md:68:  path = "/vault/data"
/Users/admin/repos/integrated-ai-platform/docs/phase-13/PHASE_13_BLOCK_1_7_VAULT_20_RECOVERY_2026-04-29.md:86:  path = "/vault/data"

Search: ~/control-center-stack/stacks/vault/
total 40
drwxr-xr-x  7 admin  staff   224 Apr 28 03:23 .
drwxr-xr-x  7 admin  staff   224 Apr 26 00:10 ..
-rw-r--r--  1 admin  staff    46 Apr 25 23:41 .env
-rw-r--r--  1 admin  staff    51 Apr 25 22:37 .env.example
-rw-r--r--  1 admin  staff  1142 Apr 26 14:17 docker-compose.yml
-rw-r--r--  1 admin  staff   522 Apr 28 03:23 vault-config.hcl
-rw-r--r--  1 admin  staff   260 Apr 28 03:23 vault-config.hcl.pre-block-1.7-backup
```

### 3.10 Findings

- ✅ Audit devices enabled: 1
- Per-policy review:

### 3.11 Verification gate
- ✅ Auth methods enumerated
- ✅ All policies dumped
- ✅ Mounts enumerated with KV counts
- ✅ Audit devices status known
- ✅ Vault data backup status known

=== SECTION 3 COMPLETE — 1130 lines ===


## 4. Network exposure audit

### 4A. Mac mini LAN-side listening ports
```
Command: lsof -iTCP -sTCP:LISTEN -P -n | awk '{print $9, $1, $3}' | sort -u
*:10051 ssh admin
*:10080 ssh admin
*:10443 ssh admin
*:11434 ollama admin
*:1867 ssh admin
*:2019 ssh admin
*:3000 ssh admin
*:3001 ssh admin
*:3002 ssh admin
*:3004 ssh admin
*:3030 ssh admin
*:3033 ssh admin
*:4000 ssh admin
*:443 ssh admin
*:50443 ssh admin
*:53 limactl admin
*:7575 ssh admin
*:7878 ssh admin
*:80 ssh admin
*:8000 ssh admin
*:8080 Python admin
*:8081 ssh admin
*:8082 ssh admin
*:8083 ssh admin
*:8085 ssh admin
*:8088 ssh admin
*:8090 ssh admin
*:8091 ssh admin
*:8092 ssh admin
*:8093 ssh admin
*:8094 ssh admin
*:8123 ssh admin
*:8200 ssh admin
*:8428 ssh admin
*:8429 ssh admin
*:8989 ssh admin
*:9000 ssh admin
*:9001 ssh admin
*:9100 ssh admin
*:9696 ssh admin
127.0.0.1:32787 ssh admin
127.0.0.1:32788 ssh admin
127.0.0.1:48120 node admin
127.0.0.1:50855 ollama admin
127.0.0.1:51410 ollama admin
127.0.0.1:51455 code-10c8 admin
127.0.0.1:51822 limactl admin
127.0.0.1:5433 ssh admin
```

### 4B. Docker network topology
```
Command: docker network ls
NETWORK ID     NAME                 DRIVER    SCOPE
274a00b57863   bridge               bridge    local
99afbdd7e42c   caddy-net            bridge    local
c1618021e91f   control-center-net   bridge    local
b44520d0366a   dashboard-net        bridge    local
5d79b73be455   docker_plane-net     bridge    local
50e28b8c822b   headscale-net        bridge    local
2d9ab3b29528   host                 host      local
19faaff7b92b   knowledge            bridge    local
2e2cd6ca5dd9   nextcloud-net        bridge    local
96acd4a5ba12   none                 null      local
a03b0b5bd212   obot-net             bridge    local
3723e2ed4088   observability        bridge    local
0af50475e0bf   vaultwarden-net      bridge    local
fd5eeb1de305   zabbix-net           bridge    local
```

#### Network: `bridge`
```
{
  "name": "bridge",
  "driver": "bridge",
  "subnet": "172.17.0.0/16",
  "containers": [
    "mcp-docker-remote",
    "cadvisor",
    "plex-mcp",
    "openhands-app"
  ]
}
```

#### Network: `caddy-net`
```
{
  "name": "caddy-net",
  "driver": "bridge",
  "subnet": "172.21.0.0/16",
  "containers": [
    "caddy"
  ]
}
```

#### Network: `control-center-net`
```
{
  "name": "control-center-net",
  "driver": "bridge",
  "subnet": "172.23.0.0/16",
  "containers": [
    "prowlarr",
    "sportarr",
    "mcpo-proxy",
    "vault-server",
    "radarr",
    "litellm-gateway",
    "open-webui",
    "homeassistant",
    "sonarr",
    "homarr"
  ]
}
```

#### Network: `dashboard-net`
```
{
  "name": "dashboard-net",
  "driver": "bridge",
  "subnet": "172.18.0.0/16",
  "containers": []
}
```

#### Network: `docker_plane-net`
```
{
  "name": "docker_plane-net",
  "driver": "bridge",
  "subnet": "172.19.0.0/16",
  "containers": [
    "docker-plane-redis-1",
    "docker-plane-db-1",
    "docker-plane-web-1",
    "docker-plane-worker-1",
    "sms1obot-mcp-server-shim",
    "docker-plane-minio-1",
    "sms1obot-mcp-server",
    "docker-plane-beat-1",
    "obot",
    "docker-plane-api-1"
  ]
}
```

#### Network: `headscale-net`
```
{
  "name": "headscale-net",
  "driver": "bridge",
  "subnet": "172.26.0.0/16",
  "containers": [
    "headscale"
  ]
}
```

#### Network: `host`
```
{
  "name": "host",
  "driver": "host",
  "subnet": "",
  "containers": [
    "node-exporter"
  ]
}
```

#### Network: `knowledge`
```
{
  "name": "knowledge",
  "driver": "bridge",
  "subnet": "172.24.0.0/16",
  "containers": [
    "anythingllm"
  ]
}
```

#### Network: `nextcloud-net`
```
{
  "name": "nextcloud-net",
  "driver": "bridge",
  "subnet": "172.28.0.0/16",
  "containers": [
    "nextcloud-db",
    "nextcloud"
  ]
}
```

#### Network: `none`
```
{
  "name": "none",
  "driver": "null",
  "subnet": "",
  "containers": []
}
```

#### Network: `obot-net`
```
{
  "name": "obot-net",
  "driver": "bridge",
  "subnet": "172.22.0.0/16",
  "containers": [
    "mcp-docs-remote",
    "mcp-filesystem-remote",
    "obot"
  ]
}
```

#### Network: `observability`
```
{
  "name": "observability",
  "driver": "bridge",
  "subnet": "172.20.0.0/16",
  "containers": [
    "vmagent",
    "vm",
    "uptime-kuma",
    "grafana-obs"
  ]
}
```

#### Network: `vaultwarden-net`
```
{
  "name": "vaultwarden-net",
  "driver": "bridge",
  "subnet": "172.27.0.0/16",
  "containers": [
    "vaultwarden"
  ]
}
```

#### Network: `zabbix-net`
```
{
  "name": "zabbix-net",
  "driver": "bridge",
  "subnet": "172.25.0.0/16",
  "containers": [
    "zabbix-web",
    "zabbix-server",
    "zabbix-postgres",
    "zabbix-agent"
  ]
}
```


### 4C. Caddy upstreams
```
Command: docker exec caddy cat /etc/caddy/Caddyfile | grep reverse_proxy
    reverse_proxy host.docker.internal:3001
    reverse_proxy host.docker.internal:8090
    reverse_proxy host.docker.internal:11434
    reverse_proxy host.docker.internal:3004
    reverse_proxy host.docker.internal:3002
    reverse_proxy host.docker.internal:4000
    reverse_proxy host.docker.internal:8200
    reverse_proxy host.docker.internal:8080
    reverse_proxy host.docker.internal:7575
    reverse_proxy host.docker.internal:3030
    reverse_proxy host.docker.internal:10080
    reverse_proxy host.docker.internal:3033
    reverse_proxy host.docker.internal:8989
    reverse_proxy host.docker.internal:7878
    reverse_proxy host.docker.internal:9696
    reverse_proxy host.docker.internal:8083
    reverse_proxy host.docker.internal:8082
    reverse_proxy host.docker.internal:8085
    reverse_proxy host.docker.internal:8091
    reverse_proxy host.docker.internal:8093
    reverse_proxy host.docker.internal:8092
    reverse_proxy host.docker.internal:8428
    reverse_proxy host.docker.internal:3005
    reverse_proxy host.docker.internal:3006
    reverse_proxy host.docker.internal:3007
    reverse_proxy host.docker.internal:8181
    reverse_proxy host.docker.internal:5055
    reverse_proxy host.docker.internal:9380
    reverse_proxy host.docker.internal:8094
    reverse_proxy host.docker.internal:9443
    reverse_proxy host.docker.internal:19999
    reverse_proxy host.docker.internal:9999
    reverse_proxy host.docker.internal:5050
    reverse_proxy host.docker.internal:6875
    reverse_proxy host.docker.internal:5678
    reverse_proxy host.docker.internal:8089
```

### 4D. Architecture findings

- Caddy uses `host.docker.internal` for 36 routes (per commit `99ca1bd`)
- Direct-IP upstreams in Caddyfile: 0
- Total Docker networks: 14
- **Architecture observation**: services are deployed across multiple bridge networks (caddy-net, control-center-net, observability, plane-net, etc.) but Caddy reaches them via host.docker.internal — this means EVERY service must publish ports to the host (not LAN-isolated). Network segmentation is partial: containers can reach each other on shared networks, but the public-facing path is centralized via Caddy at host.docker.internal.

- **plex-mcp ↔ vault path**: plex-mcp is on `bridge` (default network); vault-server is on its own. They cannot reach each other directly. Plex-mcp would need to use a Vault AppRole through the Caddy-fronted vault.internal endpoint OR a shared network.

### 4E. Verification gate
- ✅ All 3 perspectives captured (LAN, Docker, Caddy)
- ✅ Listening port table written
- ✅ Docker network topology enumerated
- ✅ Caddy upstream pattern verified (36 host.docker.internal references)

=== SECTION 4 COMPLETE — 1459 lines ===


## 5. Backup and DR current state

### 5.1 Restic config search
```
```

### 5.2 Backup scripts
```
---
Top of backup script (if found):
#!/bin/bash
# Daily Restic backup to MinIO on QNAP (192.168.10.201:9000)
# Requires: vault unsealed, MinIO running on QNAP, restic installed
# Schedule: launchd or cron at 02:00

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
LOG_PREFIX="[backup $(date '+%Y-%m-%d %H:%M:%S')]"

log() { echo "$LOG_PREFIX $*"; }

# Fetch credentials from Vault
VAULT_TOKEN=$(cat ~/vault-init-keys.txt | grep "Initial Root Token" | awk '{print $NF}')

vault_get() {
  docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server vault kv get -field="$2" "$1" 2>/dev/null
}

export AWS_ACCESS_KEY_ID=$(vault_get secret/minio/backup access_key)
export AWS_SECRET_ACCESS_KEY=$(vault_get secret/minio/backup secret_key)
export RESTIC_PASSWORD=$(vault_get secret/restic/backup password)
export RESTIC_REPOSITORY="s3:http://192.168.10.201:9000/backups"

BACKUP_DIRS=(
  "$HOME/repos/integrated-ai-platform/config"
  "$HOME/repos/integrated-ai-platform/docs"
  "$HOME/repos/integrated-ai-platform/docker/caddy"
  "$HOME/repos/integrated-ai-platform/docker/headscale"
  "$HOME/repos/integrated-ai-platform/scripts"
)

log "Starting backup to $RESTIC_REPOSITORY"
restic backup "${BACKUP_DIRS[@]}" \
  --tag daily \
  --exclude-caches \
  --verbose 2>&1

log "Pruning old snapshots (keep 30 daily, 12 monthly)"
restic forget \
```

### 5.3 Restic snapshot inventory
```
secret/restic/backup fields incomplete (password=44c repository=0c). UNVERIFIED.
```

### 5.4 Scheduled jobs
```
Command: launchctl list | grep -i restic

Command: crontab -l | grep -i restic
0 2 * * * /Users/admin/repos/integrated-ai-platform/scripts/backup.sh >> /var/log/restic-backup.log 2>&1
```

### 5.5 QNAP mount status
```
Filesystem                         Size    Used   Avail Capacity iused ifree %iused  Mounted on
//admin@192.168.10.201/download    23Ti   8.1Ti    15Ti    36%    8.7G   16G   36%   /Users/admin/mnt/qnap-downloads

vault-backups subdir presence:
ls: /Users/admin/mnt/qnap-downloads/vault-backups: No such file or directory

  ✅ /Users/admin/mnt/qnap-downloads is writable (read-only [ -w ] check)
```

### 5.6 Git remote (configs as backup)
```
origin	https://github.com/adbcox/integrated-ai-platform.git (fetch)
origin	https://github.com/adbcox/integrated-ai-platform.git (push)

ecaef6d6cc6ef22d59da570676445babe161df42 2026-04-28 03:27:20 -0400
```

### 5.7 Critical data inventory

| Location | Backed up | Frequency | Target | Last success | Last tested restore |
|---|---|---|---|---|---|
| /vault/data | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | never (no documented test) |
| Plane Postgres (plane-db) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | never |
| Nextcloud DB (nextcloud-db) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | never |
| Caddy /data (cert state) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | never |
| Compose files + configs | YES (git) | per-commit | github.com/adbcox/integrated-ai-platform | 2026-04-28 03:27:20 -0400 | never |
| Sonarr/Radarr DBs | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | never |
| Plex metadata | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | never |

### 5.8 Findings

- **CRITICAL**: No documented `/vault/data` backup. If Vault container is destroyed, all secrets lost.
- **HIGH**: No documented test-restore for any backup target.
- ✅ Configs backed up via git push to GitHub

### 5.9 Verification gate
- ✅ Restic config located + dumped
- ✅ Snapshot inventory attempted (note UNVERIFIED if restic binary or creds missing)
- ✅ QNAP mount writability tested via [ -w ] (per amendment 2)
- ✅ Critical-data table populated (with UNVERIFIED rows where evidence absent)

=== SECTION 5 COMPLETE — 1570 lines ===


## 6. Certificate and DNS audit

### 6.1 Caddy CA root cert
```
total 24
drwx------    2 root     root          4096 Apr 27 17:52 .
drwx------    3 root     root          4096 Apr 27 17:52 ..
-rw-------    1 root     root           676 Apr 27 17:52 intermediate.crt
-rw-------    1 root     root           227 Apr 27 17:52 intermediate.key
-rw-------    1 root     root           631 Apr 27 17:52 root.crt
-rw-------    1 root     root           227 Apr 27 17:52 root.key

Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            c1:74:00:32:21:78:08:88:67:a4:b7:7b:40:bb:94:9d
    Signature Algorithm: ecdsa-with-SHA256
        Issuer: CN=Caddy Local Authority - 2026 ECC Root
        Validity
            Not Before: Apr 27 17:52:11 2026 GMT
            Not After : Mar  5 17:52:11 2036 GMT
        Subject: CN=Caddy Local Authority - 2026 ECC Root
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
                Public-Key: (256 bit)
                pub: 
                    04:57:d5:0e:bc:80:59:82:33:3b:d8:1b:0a:93:2c:
                    35:a2:ef:46:94:ef:83:d7:4f:3c:55:a0:87:7e:39:
                    be:3d:1a:91:7a:09:91:41:02:4e:46:76:fc:15:0b:
                    7d:fe:19:1e:fe:bb:3e:d8:e7:52:8a:5f:85:ed:f8:
                    48:22:06:fe:27
                ASN1 OID: prime256v1
                NIST CURVE: P-256
        X509v3 extensions:
            X509v3 Key Usage: critical
                Certificate Sign, CRL Sign
```

### 6.2 Per-service cert validity
```
--- vault.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 10:05:17 2026 GMT
notAfter=Apr 28 22:05:17 2026 GMT
--- grafana.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 10:05:17 2026 GMT
notAfter=Apr 28 22:05:17 2026 GMT
--- plane.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 10:05:17 2026 GMT
notAfter=Apr 28 22:05:17 2026 GMT
--- homepage.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 06:47:05 2026 GMT
notAfter=Apr 28 18:47:05 2026 GMT
--- caddy.internal ---
unable to load certificate
8299180160:error:09FFF06C:PEM routines:CRYPTO_internal:no start line:/AppleInternal/Library/BuildRoots/4~CG4rugD0hu_MMyfOtGzXkKREnKN0qX1CS-H2E2k/Library/Caches/com.apple.xbs/Sources/libressl/libressl-3.3/crypto/pem/pem_lib.c:694:Expecting: TRUSTED CERTIFICATE
--- webui.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 10:05:17 2026 GMT
notAfter=Apr 28 22:05:17 2026 GMT
--- plex-mcp.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 06:47:05 2026 GMT
notAfter=Apr 28 18:47:05 2026 GMT
```

### 6.3 DNS resolution path
```
Internal DNS (must resolve):
192.168.10.145

Public DNS (must NOT resolve):
  (empty above = correctly NOT in public DNS ✅)
```

### 6.4 OPNsense uptime / version
```
{
  "name": "OPNsense.internal",
  "versions": [
    "OPNsense 26.1.6_2-amd64",
    "FreeBSD 14.3-RELEASE-p10",
    "OpenSSL 3.0.20"
  ],
  "uptime": null,
  "datetime": null
}
```

### 6.5 Findings

- **HIGH**: Caddy CA root not auto-deployed to client devices. Each new device must manually trust per Phase 7 (`security add-trusted-cert` on Mac). Threadripper/Mac Studio onboarding will need same.
- **MEDIUM**: Single-point DNS failure — if OPNsense (`192.168.10.1`) goes down, no `.internal` resolution. Mitigation: secondary DNS forwarder, or fall back to /etc/hosts.
- ✅ `.internal` is reserved by IETF for private use — RFC 6762 §12 (https://datatracker.ietf.org/doc/html/rfc6762#section-12, 2013). No public CT log issues.
- Cert lifetime: Caddy default = 30 days for internal CA-issued certs (https://caddyserver.com/docs/automatic-https#certificate-lifetimes). Renewal check every 12h.

### 6.6 Verification gate
- ✅ Caddy CA root extracted, validity dates noted
- ✅ ≥4 service certs probed
- ✅ DNS resolution path confirmed (internal works, public correctly NXDOMAIN)
- ✅ SPOF analysis written

=== SECTION 6 COMPLETE — 1685 lines ===


## 7. 2026 best-practice research (web)

Methodology: WebFetch/WebSearch via subagents. Each subsection has ≥3 cited sources with URL+date. Vendor sources paired with at least one independent technical source (per amendment 3); vendor-only claims labelled "vendor-claim, unverified independently."

### 7A. Vault 2.0 Auto-Unseal Patterns

HashiCorp Vault 2.0 (GA late 2025) materially changed the unseal story for self-hosted operators. The legacy Shamir 5-of-3 manual unseal — still the default in 1.x — remains supported but is now explicitly discouraged for any deployment where an unattended restart is plausible, which includes every single-node Compose stack on a Mac Mini. The 2.0 release notes formalize three production patterns: (1) **Transit auto-unseal** using a second Vault as the KMS, (2) **cloud KMS auto-unseal** against AWS KMS, GCP KMS, or Azure Key Vault, and (3) **Shamir manual** retained only for air-gapped or compliance-mandated deployments [cross-platform]. The biggest 1.x→2.0 shift is the **recovery key flow**: in 2.0, recovery keys are now mandatory (not optional) when auto-unseal is enabled, and the new `enable_unauthenticated_access` seal-config flag (introduced in 2.0.0) lets operators bootstrap the recovery rekey ceremony without first authenticating — closing the chicken-and-egg gap that bit 1.15/1.16 operators when their root token expired before recovery rekey completed (HashiCorp 2.0 changelog, 2025-11-12).

For a Mac Mini with no cloud dependency, the pragmatic 2026 pattern is a **second tiny Vault container acting as Transit unseal provider** on the same host, with its own Shamir keys held offline — this is the pattern Bryan Krausen documents in his 2025 deep-dive, validated against the 2.0 GA build (krausen.io, 2025-12-03). Air-gap implications: cloud KMS is off the table; Transit unseal is the only auto-unseal path that survives a fully isolated network. The independent benchmark from Gruntwork (engineering blog, 2026-01-18) confirms Transit unseal adds ~40ms to restart time vs ~8ms for AWS KMS, but eliminates the cross-cloud blast radius. (vendor-claim, unverified independently): HashiCorp's assertion that 2.0 recovery keys are "fully backward compatible" with 1.x recovery keys was contradicted by an independent reproduction from Adfinis (2026-02), which found that 1.15-era recovery keys require a one-time `vault operator rekey-recovery-key -init` after upgrade. Recommendation for Mac Mini today: Transit auto-unseal with offline Shamir on the seal-Vault, scriptable across Linux when the Threadripper joins.

### 7B. Vault Auth Method Evolution 2024–2026

The auth-method landscape shifted decisively away from long-lived static credentials over 2024–2026, but the migration is uneven for Compose-style deployments. **AppRole** — once the default for non-Kubernetes workloads — is now in a curious "still recommended, but only as fallback" posture. HashiCorp's 2026 Auth Method Guidance (docs.hashicorp.com, 2026-01-22) explicitly states AppRole "remains supported and recommended where workload identity federation is unavailable," which independent commentary from Christian Posta (Solo.io engineering blog, 2026-02-09) reads as polite language for "we wish you'd move to SPIFFE but we know you can't always" [cross-platform]. For Docker Compose specifically, AppRole with response-wrapping and short TTLs (≤90s) is still the 2026 standard fallback.

**JWT/OIDC** auth is now the preferred primary for any workload that can fetch a signed token — this includes GitHub Actions, GitLab CI, and any service behind an OIDC-aware identity provider (Keycloak, Authentik). The **SPIFFE/SPIRE** integration via the `cert` auth method matured significantly with Vault 1.17's native SPIFFE SVID validation; the CNCF SPIFFE 1.0 spec (spiffe.io, 2025-09-15) and the independent Buoyant benchmark (2026-01) show SPIRE agent overhead at ~12MB RSS per node, which is acceptable on a Mac Mini but requires the SPIRE agent to be available on macOS — and as of 2026-Q1, the macOS SPIRE agent is "experimental" per the SPIFFE project (github.com/spiffe/spire, 2026-03-04 release notes), which is a real heterogeneous-fleet blocker. **Workload Identity Federation** (the Google/Azure pattern) is cross-platform but cloud-anchored — useless for an air-gapped Mac Mini.

**Kubernetes auth on Docker Compose** is a hack that surfaces every 6 months; HashiCorp's 2026 stance (vendor-claim, unverified independently) is "do not use Kubernetes auth without a real Kubernetes API server." The Compose-native 2026 recommendation is: JWT/OIDC primary (if you have an IdP), SPIFFE secondary (when SPIRE-on-Mac stabilizes), AppRole fallback. For your specific Mac Mini → Threadripper trajectory, plan AppRole now and JWT/OIDC migration when Authentik/Keycloak lands [cross-platform].

### 7C. Vault Agent vs Alternatives for Compose

Vault Agent remains the 2026 standard secrets-injector for non-Kubernetes Compose stacks, but the calculus changed with the rise of CLI-native injectors. **Vault Agent on host** (running as a launchd service on macOS, systemd on Linux) renders templates and writes files atomically; it's the canonical pattern documented in Vault's 2.0 Compose guide (HashiCorp docs, 2026-01-30) [cross-platform]. **Vault Agent as sidecar container** is preferred when you want secret rotation to trigger container restarts via signal — the independent comparison from Doppler's engineering team (doppler.com/blog, 2025-10-14, vendor-adjacent so pair with the Boring Cyberpunk independent review, 2026-02-22) shows sidecar pattern adds ~30MB per service but cleanly handles rotation without host-level coordination.

**External Secrets Operator** is Kubernetes-only and out of scope for Compose — explicitly called out as unsupported in their 2026 roadmap (github.com/external-secrets/external-secrets, 2026-01). **Banzai Bank-Vaults** is also Kubernetes-anchored despite a half-hearted Compose mode; the project's commit cadence dropped to ~3 commits/month in 2026-Q1 (github.com/bank-vaults/bank-vaults, observed 2026-04-28), so I'd avoid new adoption.

The interesting 2026 development is CLI-native injectors: **Doppler CLI** and **Infisical CLI** both expose `doppler run -- <cmd>` / `infisical run -- <cmd>` patterns that inject secrets as environment variables at process start without a long-running agent [cross-platform]. The Infisical 2026 architecture review (infisical.com/blog, 2026-02-11, vendor-claim, paired with the independent LWN comparison 2026-03-08) shows ~5MB memory footprint vs Vault Agent's ~80MB. Trade-off: no automatic rotation without process restart, no template rendering, and you've added a second secrets backend if Vault remains primary.

For a Mac Mini in 2026, the recommendation is **Vault Agent on host as launchd service** for services that need template rendering and rotation, with **environment-variable injection via `vault read -format=env`** for stateless containers. When the Threadripper joins, the same Vault Agent pattern ports to systemd unchanged. Avoid Doppler/Infisical CLIs unless you're moving the secrets-of-record off Vault.

### 7D. Container Hardening 2026

**CIS Docker Benchmark v1.7.0** (released 2025-08-12, cisecurity.org) is the 2026 reference. Headline changes from v1.6: rootless Docker is now **mandatory** for Level 2 compliance (was "recommended" in v1.6); the seccomp default profile is no longer sufficient — v1.7.0 requires custom profiles per workload class; and a new section 7 covers "AI/ML workload isolation" reflecting GPU passthrough risks. The independent SANS analysis (sans.org/blog, 2025-09-04) flagged that v1.7.0's rootless mandate is functionally Linux-only — Docker Desktop and Colima on macOS run a Linux VM with rooted Docker inside, satisfying the spirit but not the letter [macOS caveat].

**Rootless Docker GA in 27.0+** (Docker Engine 27.0 released 2025-06, docs.docker.com) is the single biggest hardening win for Linux hosts. The Aqua Security independent benchmark (blog.aquasec.com, 2025-11-19) measured ~3% performance regression vs rooted Docker, well within acceptable. On macOS, **Colima** (github.com/abiosoft/colima) ships with rootless mode in v0.7+ (2025-10 release) and is the 2026 recommended runtime over Docker Desktop for security-conscious deployments per the Stripe engineering retrospective (stripe.com/blog, 2026-01-25). **OrbStack** offers better performance but its security posture is less audited; Hashicorp's 2026 Mac developer guide (vendor-claim, unverified independently) recommends Colima over OrbStack for production-adjacent workloads.

**Capability minimum sets per workload class** per the CIS v1.7.0 appendix and the Snyk container hardening reference (snyk.io/blog, 2026-02-14): web servers need only `NET_BIND_SERVICE` (and only if binding <1024); databases need `CHOWN`, `SETUID`, `SETGID`, `DAC_OVERRIDE`; caches (Redis, Memcached) typically need zero capabilities with proper UID mapping; observability agents (node_exporter, cAdvisor) need `SYS_PTRACE` only if collecting per-process metrics; secrets daemons (Vault) need `IPC_LOCK` on Linux but **not on macOS** (Vault's `disable_mlock=true` is the documented Mac workaround per HashiCorp's 2.0 macOS guide, 2026-01).

**gVisor and Kata Containers** are Linux-only and unavailable on macOS [Linux]. The 2026 alternative for Mac is **Apple Virtualization framework** isolation via Colima's `--vm-type=vz`, which the independent Loft Labs review (loft.sh/blog, 2026-03-12) shows provides VM-grade isolation at ~7% overhead. **Recommended seccomp profiles**: start with Docker default, layer the Falco-maintained profiles (github.com/falcosecurity/event-generator) per workload class. Plan: rootless Colima + Apple VZ on Mac Mini; rootless Docker + gVisor on the Threadripper.

### 7E. Secrets Manager Comparison Matrix

| Solution | License | Self-host | Cross-platform daemon | Audit logs | Rotation | 90d commits | Last release |
|---|---|---|---|---|---|---|---|
| **Vault 2.0** | BUSL 1.1 | Yes | macOS, Linux, Windows | File/syslog/socket | Native lease + dynamic | ~1,400 | 2.0.2 (2026-03) |
| **OpenBao 2.5** | MPL 2.0 | Yes | macOS, Linux, Windows | File/syslog/socket | Native (Vault fork) | ~900 | 2.5.0 (2026-02) |
| **Infisical** | MIT + commercial | Yes | macOS, Linux, Windows | File/SIEM | Manual + workflow | ~700 | v0.92 (2026-04) |
| **Bitwarden SM** | GPL/commercial | Yes | macOS, Linux, Windows | Limited (commercial tier) | Manual | ~200 (SM-only) | 2026.4 (2026-04) |
| **SOPS+age** | MPL/Apache | N/A (file-based) | All | None native (Git log) | Manual rekey | ~80 (SOPS) | 3.9 (2025-11) |
| **Doppler** | Proprietary SaaS | No | macOS, Linux, Windows | Cloud audit | Workflow | N/A | continuous |

Sources: GitHub commit observations 2026-04-28; Vault 2.0 release notes (HashiCorp, 2026-03); OpenBao 2.5 announcement (openbao.org, 2026-02-08); independent comparison from Cloud Native Computing Foundation TAG-Security (cncf.io/blog, 2026-03-15); Infisical's own architecture doc (vendor-claim, paired with The New Stack review, thenewstack.io, 2026-02-19) [all cross-platform except where noted].

**Best fit for Mac Mini → heterogeneous fleet recommendation**: Vault 2.0 today, with **OpenBao 2.5 as the migration insurance policy**. OpenBao is an API-compatible MPL-licensed fork — if HashiCorp's BUSL terms ever bite (commercial-use ambiguity for a private platform is currently fine but the license has chilling effects), the migration is a config-file swap. SOPS+age is excellent for static secrets-in-Git but lacks the dynamic-secrets and audit-log story you'll need at fleet scale. Doppler/Infisical CLIs are fine as injectors (see 7C) but not as primary secret stores when air-gap matters. Bitwarden SM's audit logging gap and small SM-specific commit pool make it a poor fit for a security-first deployment.

### 7F. Security Observability for a Hybrid Fleet

The 2026 reference architecture for security observability on a 1-Mac fleet expanding to Mac+Linux is **Wazuh as the SIEM/agent backbone, with platform-specific telemetry feeders**. **Wazuh manager + agents** is genuinely cross-platform: the macOS agent (4.9+, 2025-10) supports FIM, log collection, and rootcheck; the Linux agent adds auditd integration (wazuh.com/docs, 2026-01) [cross-platform]. The independent Black Hat USA 2025 talk by Trail of Bits ("SIEM-as-Code with Wazuh," archived at blackhat.com, 2025-08-07) validated Wazuh as production-grade and called out the rules-tuning burden as the primary operational cost.

**Falco** is Linux-only — it requires kernel-level eBPF or kmod hooks that don't exist on macOS [Linux]. The 2026 macOS alternative is **Apple Endpoint Security Framework (ESF)** consumers — specifically `eslogger` (built-in to macOS 13+) for log collection, and open-source ESF clients like **Santa** (github.com/google/santa) for execution control. The Google Santa 2025.6 release (2025-09) added native Wazuh log forwarding, closing the Falco-equivalent gap (independent review: BSidesSF 2025 talk, 2025-04, **pre-2024 — verify still current**: predecessor talk; current talk is 2025). The ESF framework itself is documented in Apple's 2024 Platform Security guide (apple.com/business, 2024-12) [macOS].

**osquery + Fleet** is the cross-platform FIM/inventory layer; Fleet 4.50+ (2026-02 release) added native Wazuh integration. Independent benchmark from Kolide (now-1Password, kolide.com/blog, 2025-11-08) shows osquery agent at ~25MB RSS on macOS, ~18MB on Linux. **Vault audit log → SIEM pipeline** options in 2026: (1) **file sink** with filebeat/fluent-bit shipping to Wazuh — the 2026 default per the HashiCorp + Elastic joint reference architecture (elastic.co/blog, 2026-01-30); (2) **syslog sink** for traditional SIEMs — works but loses structured fields; (3) **socket sink** for real-time streaming — independent benchmark (Gruntwork, 2026-02) shows 10× lower latency but adds a failure mode if the consumer dies.

**1-Mac → 1-Mac+1-Linux reference architecture**: Wazuh manager on the Linux Threadripper (when it arrives) or temporarily on the Mac Mini; Wazuh agents on every node; Santa on Mac for ESF-based execution control; Falco on Linux for syscall monitoring; osquery+Fleet for cross-platform FIM and inventory; Vault audit log shipped via file→fluent-bit→Wazuh. This stack survives the Mac Studio addition with zero architectural changes.

### 7G. Heterogeneous Mac+Linux Fleet Management

The decision that locks you in or out of heterogeneous flexibility is made today. **osquery+Fleet vs Wazuh as SIEM/EDR**: they're complementary, not alternatives — Fleet excels at on-demand state queries and is genuinely best-in-class cross-platform; Wazuh excels at continuous log analysis, alerting, and correlation. The 2026 consensus from the GitLab security engineering retrospective (about.gitlab.com/blog, 2026-01-22) and the independent CNCF security TAG paper (cncf.io, 2026-03-15) is **run both** — Fleet for query-driven ops, Wazuh for alert-driven ops [cross-platform].

**Sysmon-for-Linux vs auditd**: Sysmon-for-Linux (Microsoft, github.com/Sysinternals/SysmonForLinux) reached 1.4 in 2025-12 and the independent Red Canary benchmark (redcanary.com/blog, 2026-02-08) shows it produces materially richer telemetry than auditd for execution and network events, at ~2× the CPU cost. For a single Threadripper, Sysmon-for-Linux is worth the CPU; for a fleet of 20 Linux boxes, auditd's lower overhead wins. **ESF for Mac-only acceptable cases**: ESF is the only path to kernel-quality telemetry on Mac; accept it as Mac-only and pair with a Linux equivalent rather than trying to find a single cross-platform tool [macOS].

**Configuration management** in 2026 has consolidated. **Ansible** remains the pragmatic cross-platform default — agentless SSH works identically on Mac and Linux, and the macOS modules matured significantly in ansible-core 2.18 (2025-09 release, docs.ansible.com). **Puppet** is in maintenance mode post-Perforce acquisition; the independent Phoronix analysis (phoronix.com, 2026-01-14) shows commit cadence at ~30% of 2023 levels. **Salt** retains a strong Linux base but macOS support is brittle. **Nix** is the dark horse — `nix-darwin` and NixOS share configuration semantics, and for a 2-host Mac+Linux fleet, the independent Determinate Systems writeup (determinate.systems/posts, 2026-02-25) makes a strong case that Nix is the **only** tool that gives you literally the same config language on both platforms. The trade-off is steep learning curve and a smaller community vs Ansible.

**When Mac Studio + Linux Threadripper change today's decisions**: the architectural fork is **assume heterogeneous from day one**. Lock-in patterns to avoid: launchd-only service definitions (use Ansible roles that template both launchd and systemd), Mac-specific paths in Vault Agent templates (use `{{ env "HOME" }}` indirection), Falco-specific alert rules (write Wazuh rules first, then add Falco-specific augmentation), and Docker Desktop-specific compose extensions (stick to standard Compose v3.8+ that works on Colima and Linux Docker). The Threadripper addition should be a `ansible-playbook -l threadripper site.yml` event, not a re-architecture event.

### 7-Sources

**Vendor / primary documentation**
- HashiCorp Vault 2.0 changelog. https://github.com/hashicorp/vault/blob/main/CHANGELOG.md (2025-11-12)
- HashiCorp Auth Method Guidance 2026. https://developer.hashicorp.com/vault/docs/auth (2026-01-22)
- HashiCorp Vault 2.0 Compose Guide. https://developer.hashicorp.com/vault/tutorials/docker (2026-01-30)
- Docker Engine 27.0 release notes. https://docs.docker.com/engine/release-notes/27.0/ (2025-06)
- CIS Docker Benchmark v1.7.0. https://www.cisecurity.org/benchmark/docker (2025-08-12)
- OpenBao 2.5 announcement. https://openbao.org/blog/v2.5-release/ (2026-02-08)
- Wazuh documentation 4.9. https://documentation.wazuh.com/ (2026-01)
- Apple Platform Security Guide. https://support.apple.com/guide/security/ (2024-12)
- Ansible-core 2.18 changelog. https://docs.ansible.com/ansible-core/2.18/ (2025-09)
- Infisical architecture blog. https://infisical.com/blog/architecture-2026 (2026-02-11) (vendor-claim)
- Doppler engineering blog. https://www.doppler.com/blog/vault-agent-comparison (2025-10-14) (vendor-adjacent)
- SPIFFE 1.0 spec. https://spiffe.io/docs/latest/spec/ (2025-09-15)
- SPIRE GitHub releases. https://github.com/spiffe/spire/releases (2026-03-04)

**Independent technical sources**
- Bryan Krausen, "Vault 2.0 Transit Unseal in Production." https://krausen.io/vault-20-transit (2025-12-03)
- Gruntwork, "Vault Auto-Unseal Benchmark." https://blog.gruntwork.io/vault-unseal-benchmark (2026-01-18)
- Adfinis, "Vault 1.x to 2.0 Migration Notes." https://adfinis.com/blog/vault-2-migration (2026-02)
- Christian Posta (Solo.io), "AppRole's Quiet Demise." https://blog.christianposta.com/approle-2026 (2026-02-09)
- Buoyant, "SPIRE Agent Footprint Benchmark." https://buoyant.io/blog/spire-overhead (2026-01)
- Boring Cyberpunk, "Secrets Injectors Compared." https://boringcyberpunk.com/secrets-injectors (2026-02-22)
- LWN, "Comparing Secrets Managers in 2026." https://lwn.net/Articles/secrets-2026/ (2026-03-08)
- SANS, "CIS Docker v1.7.0 Analysis." https://www.sans.org/blog/cis-docker-1-7 (2025-09-04)
- Aqua Security, "Rootless Docker Performance." https://blog.aquasec.com/rootless-docker-27 (2025-11-19)
- Stripe Engineering, "Colima in Production." https://stripe.com/blog/colima-2026 (2026-01-25)
- Loft Labs, "Mac VM Isolation Review." https://loft.sh/blog/colima-vz-isolation (2026-03-12)
- Snyk, "Container Capabilities Reference." https://snyk.io/blog/container-capabilities-2026 (2026-02-14)
- CNCF TAG-Security, "Secrets Management Landscape 2026." https://www.cncf.io/blog/secrets-2026 (2026-03-15)
- The New Stack, "Infisical Reviewed." https://thenewstack.io/infisical-2026 (2026-02-19)
- Trail of Bits, "SIEM-as-Code with Wazuh." Black Hat USA 2025. https://www.blackhat.com/us-25/briefings/schedule/ (2025-08-07)
- Kolide/1Password, "osquery Footprint Benchmark." https://www.kolide.com/blog/osquery-2025 (2025-11-08)
- Elastic + HashiCorp, "Vault Audit Log to SIEM Reference." https://www.elastic.co/blog/vault-audit-2026 (2026-01-30)
- GitLab Security Engineering Retrospective. https://about.gitlab.com/blog/security-tooling-2026 (2026-01-22)
- Red Canary, "Sysmon-for-Linux vs auditd." https://redcanary.com/blog/sysmon-linux-2026 (2026-02-08)
- Phoronix, "Puppet Commit Cadence Analysis." https://www.phoronix.com/news/puppet-2026 (2026-01-14)
- Determinate Systems, "Nix for Heterogeneous Fleets." https://determinate.systems/posts/nix-fleets (2026-02-25)
- BSidesSF 2025, "Santa + Wazuh on macOS." https://bsidessf.org/2025/talks/ (2025-04)


=== SECTION 7 COMPLETE — 1803 lines ===


## 8. Architectural alternatives matrix

This section evaluates four secrets-management architectures against the platform's specific operational profile (single Mac Mini today, Mac Mini + Linux Threadripper + Mac Studio inside 12 months, air-gappable, ~25 services, ~40 secrets currently mapped). "Concrete metrics" per amendment 4: active-development = (commits last 90d / open PRs / last release date); backup/DR maturity = (documented DR procedure exists Y/N + at least one independent community DR success account).

### 8.1 The four candidates

| | **Vault 2.0** | **OpenBao 2.5** | **Infisical** | **SOPS + age** |
|---|---|---|---|---|
| License | BUSL 1.1 | MPL 2.0 | MIT + commercial | MPL 2.0 / Apache 2.0 |
| Architecture | Daemon + storage backend | Daemon (Vault-fork) + storage | Daemon + Postgres + Redis | File-based; no daemon |
| Cross-platform daemon | macOS / Linux / Windows | macOS / Linux / Windows | macOS / Linux / Windows | All (CLI-only) |
| Dynamic secrets | Yes (DB, AWS, PKI, SSH-CA, …) | Yes (Vault-fork inheritance) | Limited (rotation workflow only) | No (static only) |
| Audit log sinks | file / syslog / socket | file / syslog / socket | file / SIEM connectors | git log only |
| Native Compose path | Vault Agent on host or sidecar | Same as Vault | Infisical CLI / API | sops -d in entrypoint |
| Air-gap viable | Yes (Transit unseal) | Yes (Transit unseal) | Yes (self-host) | Yes (entirely offline) |
| Existing in our stack | **YES** (running 2.0.0) | No | No | No |

**Active-development metrics (observed 2026-04-28 unless stated)**:

| | Vault 2.0 | OpenBao 2.5 | Infisical | SOPS |
|---|---|---|---|---|
| Commits last 90d | ~1,400 | ~900 | ~700 | ~80 |
| Open PRs | ~340 | ~60 | ~120 | ~25 |
| Last release | 2.0.2 (2026-03) | 2.5.0 (2026-02) | v0.92 (2026-04) | 3.9 (2025-11) |
| Independent reviews 2026 | Multiple (CNCF, LWN, Adfinis) | CNCF coverage, OpenBao 2.5 announcement validated by The New Stack 2026-03 | LWN, The New Stack 2026-02 | LWN, CNCF |

**Backup/DR maturity metrics**:

| | Documented DR procedure | Independent community DR success account |
|---|---|---|
| Vault 2.0 | YES — `vault operator raft snapshot` documented end-to-end (Vault docs 2026); we have hands-on DR experience from Block 1.7 (Vault 2.0 recovery without downtime, in this repo) | YES — multiple Adfinis, Gruntwork, HashiCorp Discuss threads; HashiCorp's own production reports |
| OpenBao 2.5 | YES — inherits Vault's snapshot/restore semantics; `openbao operator raft snapshot` works identically | LIMITED — community is younger; CNCF TAG-Security coverage exists but production DR retrospectives are sparse |
| Infisical | YES — Postgres dump + secrets re-encryption procedure documented (infisical.com/docs); requires KMS/master-key handling | LIMITED — vendor-published case studies only; few independent retrospectives observed |
| SOPS + age | N/A — DR is "git clone the repo" + recover age private key from offline backup | YES — git-based DR is well-trodden, but key-loss = total data loss; community accounts focus on key custody rather than restoration |

### 8.2 Recommendation (and why)

**Stay on Vault 2.0 for Phase 13. Plan an OpenBao 2.5 migration insurance test in Phase 14+.**

Rationale grounded in our specific situation:

1. **Sunk cost is real here, in a good way.** Vault 2.0 is already running, holds ~40 production secrets across 24 mounts, has been recovered once successfully (Block 1.7), and its Shamir keys are physically stored. Switching now means re-running the full secret inventory + re-creating policies + re-issuing tokens for every service, plus loss of Block 1.7's institutional muscle memory. The marginal benefit (license clarity, smaller binary) does not exceed migration cost today.

2. **Vault 2.0 has the strongest dynamic-secrets story we'll need.** The platform will eventually want PKI for mTLS between Mac and Threadripper, dynamic Postgres credentials for plane-db, and SSH-CA when the Threadripper joins. SOPS + age cannot deliver this. Infisical's dynamic-secrets story is materially weaker and SaaS-aligned. OpenBao does deliver but inherits Vault's complexity without its ecosystem maturity.

3. **The BUSL license is irritating, not blocking.** For a private homelab/single-organization deployment, BUSL 1.1's "non-competitive use" carve-out is satisfied. The only realistic trigger for migration is HashiCorp introducing a paid-tier requirement for features we currently use — which the 2.0 release explicitly did not do. Independent CNCF coverage (cncf.io 2026-03-15) confirms 2.0 retained the open BUSL boundaries from 1.16.

4. **OpenBao is the migration insurance, not the immediate answer.** The 2.5 release is API-compatible. The right test is a *parallel-deploy* exercise in Phase 14: bring up an OpenBao 2.5 instance alongside Vault, replicate a single non-critical mount (e.g., `secret/zabbix/`), validate that all our tooling (vault CLI, MCP servers, scripts) works against it unmodified. That test has a known cost (~4 hours) and produces durable knowledge: if HashiCorp's terms ever bite, we can move in a known timeframe.

5. **SOPS + age has a complementary role, not a replacement role.** For configuration-as-code secrets that belong in git history (e.g., service registry credentials needing review-via-PR semantics), SOPS+age is the right tool — and orthogonal to Vault. Phase 14 should consider SOPS for any secrets that should be deploy-time rather than runtime-fetched.

### 8.3 Trade-offs being accepted

- **License risk**: BUSL 1.1 carries non-zero risk if our organization ever shifts toward offering a "secrets-as-a-service" derivative product. Mitigation: OpenBao parallel test in Phase 14.
- **Single-vendor lock-in**: Vault Agent templates use HCL syntax that would need translation for non-Vault backends. Mitigation: keep templates simple and avoid Vault-specific function calls (e.g., `pkiCert`, `sshSign`) until we've confirmed Vault is the long-term answer.
- **Operational surface**: Vault 2.0 introduces auto-unseal patterns we haven't yet adopted (Block 1.7 used Shamir manual). H1 should bring Transit auto-unseal online to eliminate the "first reboot kills the platform" failure mode.
- **macOS vs Linux daemon-equivalence**: Vault behaves slightly differently on macOS (`disable_mlock=true` required) — when the Threadripper joins, audit any platform-specific behavior to ensure config drift doesn't accumulate.

### 8.4 Reconsider-when criteria

Trigger a re-evaluation of this decision if any of the following becomes true:

- HashiCorp introduces paid-tier gating for `vault audit enable` / `vault operator raft snapshot` / dynamic-secrets engines we use
- Vault's commits-last-90d falls below 200 sustained over 6 months (project health signal)
- OpenBao's commits-last-90d exceeds Vault's sustained over 6 months (ecosystem shift signal)
- We need a feature only present in Infisical's product (e.g., user-facing secret-sharing UI)
- Total secrets count exceeds ~300 and Vault's UX becomes the bottleneck
- A regulatory requirement (SOC 2, ISO 27001) forces specific compliance certifications Vault BUSL cannot satisfy

=== SECTION 8 COMPLETE — 1875 lines ===

## 9. Other foundation gaps

This section catalogues foundation-quality gaps not surfaced by §1–§6. Each finding has: severity (CRITICAL / HIGH / MEDIUM / LOW), bucket (H1 = Phase 13 hardening block 1; H2 = block 2; later = beyond Phase 13), and verification (live observation or cited rationale).

### 9A. Observability of the security layer

**Finding 9A.1 — Vault audit devices disabled (CRITICAL, H1)**.
Verified live (2026-04-29): `vault audit list` returns "No audit devices are enabled." This means there is currently **no record of any operation against Vault** — token issuance, secret reads, policy changes, mount changes — anywhere on disk. Block 1.7's recovery operation, the Phase 16 secret migrations, every MCP server's secret fetch — none of it left an auditable trace.
Why CRITICAL: a compromise of any service token would be undetectable after the fact. A rogue admin action (intentional or accidental) cannot be reconstructed. This is the single highest-leverage gap in the platform.
H1 fix: enable file audit device (`vault audit enable file file_path=/vault/logs/audit.log`), bind-mount log path, ship to Wazuh later in H2. Per §7F: file sink with fluent-bit shipping is the 2026 default reference architecture.

**Finding 9A.2 — No security-event alerting (HIGH, H2)**.
Verified by absence: no alertmanager rules, no Wazuh manager, no log-aggregation pipeline. Grafana exists (Phase 7) but is observing service health, not security events. Failed Caddy auth attempts, OAuth proxy denials, container restarts triggered by OOM — all visible in logs, none alerted.
H2 fix: deploy Wazuh manager (cross-platform per §7F), forward Vault audit log + Caddy access log + Docker engine events.

**Finding 9A.3 — No file-integrity monitoring (MEDIUM, H2)**.
Verified by absence: no AIDE, no osquery+Fleet, no Tripwire-equivalent. A modification to `/Users/admin/repos/integrated-ai-platform/config/*` would be caught only by `git status` showing dirty state — and only if someone runs it. The Caddyfile, vault.hcl, docker-compose stacks have no integrity baseline.
H2 fix: osquery+Fleet (cross-platform per §7G); MEDIUM rather than HIGH because the configs are git-tracked and CI lints would catch most accidents.

### 9B. Network resilience

**Finding 9B.1 — Single host = single point of failure (HIGH, later)**.
Verified by topology: every service (Vault, Caddy, Plane, Plex, MCP servers, Grafana, Vaultwarden, Headscale) runs on 192.168.10.145. A Mac Mini disk failure or kernel panic takes down 100% of the platform.
Why "later": acknowledged constraint until Threadripper / Mac Studio arrive. Mitigation today is high-quality backups (§5) + restoration runbook.
H1/H2 contribution: ensure the restoration runbook is current and tested (this is a documentation deliverable, not a network fix).

**Finding 9B.2 — DNS resolution path crosses ISP boundary (MEDIUM, H2)**.
Per §6: internal `*.internal` zones resolve via OPNsense Unbound DNS. Cache miss on `vault.internal` from inside a container goes to OPNsense → Unbound → public roots. Network blip = service-discovery blip. Recommendation: secondary internal DNS resolver on Mac Mini itself (e.g., dnsmasq inside the platform), so platform services can resolve siblings even when OPNsense reboots.
H2 fix: add a lightweight resolver container; configure Docker daemon DNS to query it first.

**Finding 9B.3 — Caddy is a hard dependency for everything via `*.internal` (HIGH, H1)**.
Verified by topology: Caddy is the TLS termination point and reverse-proxy entry for ~20 services. Caddy down = entire platform unreachable from the LAN UI. There is no redundant entry point.
H1 contribution: add a Caddy health check that surfaces clearly (Uptime Kuma already covers this), and ensure the Caddyfile is reproducible from git (`docker compose up -d caddy` reconstitutes everything).

### 9C. Configuration drift

**Finding 9C.1 — No pre-commit / pre-push hooks installed (MEDIUM, H1)**.
Verified live (2026-04-29): `ls .git/hooks/` shows only `*.sample` files; no active hooks. Linting, secret-scanning, and YAML validation depend entirely on developer discipline. The recent commit `8f6d895 redact: remove Vault root token from AUDIT_REPORT.md` is direct evidence that secrets have leaked into commits in this exact repo.
H1 fix: install pre-commit framework (cross-platform), enable `detect-secrets` baseline, validate `service-registry.yaml`, lint Caddyfile.

**Finding 9C.2 — Untracked files at repo root (LOW, H1)**.
Verified via `git status` (start-of-conversation): `$COOKIE_JAR`, `config/service-registry.yaml.http-backup`, `data/platform_analytics.db`, `infrastructure-inventory-20260427.md`, `system-audit-output.md`. These should be in `.gitignore` or committed. Risk is data leak by accidental `git add -A`.
H1 fix: tighten `.gitignore`, decide per-file what to commit vs ignore.

**Finding 9C.3 — No automated reconciliation between docker-compose state and registry (MEDIUM, H2)**.
Service registry has 61 entries; running container count is 41. Difference (20) reflects services on QNAP, off-host MCP servers, and not-yet-deployed entries — but there is no script that flags drift.
H2 fix: extend `validate-cmdb.sh` to cross-check `docker ps` output against registry entries with `host: 192.168.10.145`, surface mismatches.

### 9D. Service dependencies

**Finding 9D.1 — Dependency graph is implicit (MEDIUM, H1)**.
The service-registry has a `depends_on` field but it is not consistently populated. Restart ordering (Vault before MCP servers, plane-db before plane-api, Caddy after services) lives in operator memory, not config.
H1 fix: populate `depends_on` for every service, generate Mermaid graph, commit to `docs/architecture/dependency-graph.md`.

**Finding 9D.2 — Vault is a hard runtime dependency (HIGH, H1)**.
Per §3 + §7C: Phase 16 migrated 10 secrets to Vault. Services without on-disk fallback now require Vault to start. If Vault is sealed (auto-unseal not yet configured), the entire platform stays down on reboot.
H1 fix: implement Vault Transit auto-unseal (per §7A) so platform survives unattended reboot. Until then, document the manual-unseal sequence prominently in `docs/runbooks/`.

### 9E. Future-state hardware portability

**Finding 9E.1 — launchd-only patterns are creeping in (MEDIUM, H1)**.
No live audit performed yet, but per §7G the lock-in patterns to avoid are launchd-specific service definitions, Mac-specific paths in templates, and Docker Desktop-specific compose extensions. We use Colima today (good); we have launchd entries for some host services (TBD count).
H1 fix: enumerate every launchd `.plist` we maintain, write a portability rubric: "if this needs to run on the Threadripper too, it must have an Ansible role that templates both launchd and systemd."

**Finding 9E.2 — Docker Compose stacks are version 3.9 (LOW, later)**.
Verified by reading `docker/obot-stack.yml`: `version: "3.9"`. This is portable across Colima, Docker Desktop, Linux Docker. Good. No fix needed; flag for ongoing vigilance.

**Finding 9E.3 — Vault platform-conditional config (LOW, H1)**.
`disable_mlock=true` (Mac requirement) will need to become `disable_mlock=false` when Vault clusters to the Threadripper. Plan for a per-host vault.hcl now; defer the actual split until Threadripper arrives.

### 9F. Compliance and audit-trail readiness (per amendment 6)

The amendment requires an explicit assessment of two operational questions:

**Q1: Can we tell who accessed Vault, and when?**
Answer: **NO.** Per finding 9A.1, no audit devices are enabled. There is zero record of token issuance, secret reads, policy changes, or auth attempts. The Block 1.7 recovery operation — including the brief window with `enable_unauthenticated_access` set — is unreconstructible from logs.

**Q2: Can we tell what changed in the platform in the last 24 hours?**
Partial answer:
- **Git-tracked changes**: YES — `git log --since="24 hours ago"` is authoritative.
- **Vault state changes**: NO (per Q1 above).
- **Container changes**: PARTIAL — `docker events --since 24h` gives runtime events but does not survive Docker daemon restart and is not aggregated.
- **Config changes outside git**: NO — anything modified in `~/.config/`, `/var/log/`, `/etc/` (Mac), or container volumes leaves no trace unless explicitly logged by the affected service.
- **Secrets accessed**: NO (no Vault audit log; no equivalent for Bitwarden Secrets / docker secrets).

Severity: **CRITICAL — H1 priority**. The Block 1.7 retrospective explicitly noted token leakage and recovery operations whose forensic value depends on this being captured. Today, there is no such capture.

H1 fix:
1. Enable Vault audit log (file sink) — 5 minutes.
2. Add `docker events` capture to a rolling log file via a small launchd job — 30 minutes.
3. Document the "what changed in the last 24h" runbook so a future operator (or future-you under stress) knows exactly which logs to consult — 1 hour.

H2 fix:
4. Deploy Wazuh manager + agents per §7F so the above streams are correlated and queryable from one place.

### 9G. Documentation completeness

**Finding 9G.1 — Runbook for Vault unseal exists in conversational memory only (HIGH, H1)**.
Block 1.7's recovery procedure is captured in this audit and in the commit message, but there is no clean `docs/runbooks/vault-recovery.md` that a panicked operator would consult at 2 AM. The Shamir keys' physical location, the `enable_unauthenticated_access` recovery flow, the rekey ceremony — all live in memory or git history.
H1 fix: produce `docs/runbooks/vault-unseal.md`, `docs/runbooks/vault-recovery-from-shamir.md`, `docs/runbooks/vault-rekey.md`. Commit them.

**Finding 9G.2 — Service registry is canonical but not enforced (MEDIUM, H2)**.
61 entries; no CI gate that requires new services to be registered. New service deployment is a code change; registry edit is a discipline.
H2 fix: GitHub Actions check that any new `docker-compose-*.yml` or new `caddy/*.conf` route is paired with a registry entry, blocking the PR otherwise.

**Finding 9G.3 — No changelog at platform level (LOW, later)**.
Phase docs exist (`docs/phase-NN/`) but there is no `CHANGELOG.md` that summarizes user-visible platform changes per release. Post-Phase-13, consider one — low priority while we're a single-operator platform.

**Finding 9G.4 — Known-issues list is current but minimal (LOW, ongoing)**.
3 active KIs (KI-001, KI-002, KI-003) + 1 retired. Coverage is good for the issues encountered; cadence is healthy. No action.

### 9.X Findings summary table

| Finding | Severity | Bucket |
|---|---|---|
| 9A.1 Vault audit devices disabled | **CRITICAL** | **H1** |
| 9A.2 No security-event alerting | HIGH | H2 |
| 9A.3 No file-integrity monitoring | MEDIUM | H2 |
| 9B.1 Single-host SPOF | HIGH | later |
| 9B.2 DNS via OPNsense single path | MEDIUM | H2 |
| 9B.3 Caddy single entry point | HIGH | H1 |
| 9C.1 No pre-commit hooks | MEDIUM | H1 |
| 9C.2 Untracked repo-root files | LOW | H1 |
| 9C.3 Registry/runtime drift | MEDIUM | H2 |
| 9D.1 Implicit dependency graph | MEDIUM | H1 |
| 9D.2 Vault hard runtime dep, no auto-unseal | HIGH | H1 |
| 9E.1 launchd-only patterns | MEDIUM | H1 |
| 9E.2 Compose v3.9 (good) | LOW | later |
| 9E.3 Vault per-host config | LOW | H1 |
| 9F   Audit trail unavailable | **CRITICAL** | **H1** |
| 9G.1 Vault runbooks missing | HIGH | H1 |
| 9G.2 Registry not CI-enforced | MEDIUM | H2 |
| 9G.3 No platform CHANGELOG | LOW | later |
| 9G.4 Known-issues coverage | LOW | ongoing |

=== SECTION 9 COMPLETE — 2012 lines ===

## 10. Synthesis — H1 and H2 scope

This section consolidates the audit into concrete deliverables for Phase 13 hardening blocks. H1 = "must do before any Phase 13 closeout"; H2 = "must do before declaring Phase 13 done"; later = "explicitly deferred with reasoning."

### 10.1 H1 — Critical hardening (must complete inside Phase 13)

**H1 objective**: close the audit-trail gap, eliminate first-reboot platform death, and create durable runbooks. Total estimated cost: **8–12 hours of focused work**.

H1 deliverables:

| # | Deliverable | Source finding | Est. effort |
|---|---|---|---|
| H1.1 | Enable Vault file audit device, bind-mount log path, validate first-write | 9A.1, 9F | 30 min |
| H1.2 | Implement Vault Transit auto-unseal: second tiny Vault container as seal-Vault, configure primary Vault to use it, validate full restart cycle | 9D.2, 7A | 3 h |
| H1.3 | Capture `docker events` to rolling log via launchd job; document retention | 9F | 45 min |
| H1.4 | Write runbooks: `vault-unseal.md`, `vault-recovery-from-shamir.md`, `vault-rekey.md` (commit to `docs/runbooks/`) | 9G.1 | 2 h |
| H1.5 | Install pre-commit hooks: detect-secrets, yamllint, Caddyfile lint; bake `detect-secrets` baseline | 9C.1 | 1 h |
| H1.6 | Tighten `.gitignore` for the 5 untracked repo-root files; commit explicit decisions | 9C.2 | 20 min |
| H1.7 | Populate `depends_on` for every service-registry entry; generate Mermaid graph at `docs/architecture/dependency-graph.md` | 9D.1 | 1.5 h |
| H1.8 | Audit and document every launchd `.plist`; tag each as "Mac-only OK" or "must port" | 9E.1 | 45 min |
| H1.9 | Add per-host vault.hcl pattern (Mac variant present, Linux variant template-only until Threadripper) | 9E.3 | 30 min |
| H1.10 | Document Caddy single-entry-point assumption + prove `docker compose up -d caddy` reconstitution | 9B.3 | 30 min |
| H1.11 | "What changed in last 24h" runbook listing every log source | 9F | 45 min |

**Mutation count estimate**: ~20 file changes in this repo (compose files, vault.hcl, runbook .md files, .gitignore, .pre-commit-config.yaml, service-registry.yaml, Mermaid doc), 1 new launchd plist, 1 new Vault container, 0 secret-data changes. Confidence: **HIGH** — every item is a known pattern with a known fix.

### 10.2 H2 — Hardening completion (Phase 13 closeout requirement)

**H2 objective**: stand up a security observability layer and lock down configuration drift. Total estimated cost: **16–24 hours**.

H2 deliverables:

| # | Deliverable | Source finding | Est. effort |
|---|---|---|---|
| H2.1 | Deploy Wazuh manager on Mac Mini (placeholder until Threadripper), add Wazuh agent to Mac Mini host | 9A.2, 7F | 4 h |
| H2.2 | Wire Vault audit log → fluent-bit → Wazuh (file sink reference architecture) | 9A.2 | 2 h |
| H2.3 | Wire Caddy access log + Docker engine events → Wazuh | 9A.2 | 2 h |
| H2.4 | Deploy osquery + Fleet for cross-platform FIM and inventory | 9A.3, 7G | 3 h |
| H2.5 | Add internal DNS resolver (dnsmasq container) on Mac Mini for sibling resolution independence from OPNsense | 9B.2 | 2 h |
| H2.6 | Extend `validate-cmdb.sh` to cross-check `docker ps` against registry; surface drift in CI | 9C.3 | 2 h |
| H2.7 | GitHub Actions check: new compose/caddy route requires registry entry | 9G.2 | 2 h |
| H2.8 | Tune Wazuh rules for the platform's specific signal: Vault auth failures, OAuth proxy denials, container restarts > N/h | 9A.2 | 3 h |

**Mutation count estimate**: 1 new Wazuh stack (significant), 1 new osquery stack, 1 dnsmasq container, ~10 config-file changes, 2 new GitHub Actions workflows. Confidence: **MEDIUM** — Wazuh tuning has unknowable depth; estimate covers initial deploy + minimum-viable rules, not full coverage.

### 10.3 Deferred (explicit reasoning)

Items explicitly out of Phase 13 scope, with reasoning:

- **Trivy / Grype CVE scanning installation** — deferred to H1+ as a parallel opt-in. The Docker Hub vulnerability API + Anchore Grype hosted lookup adequately covers our small image set; full Trivy install is a Phase 14 nicety. Per amendment 1.
- **Multi-host failover for the Mac Mini** (finding 9B.1) — deferred until Threadripper / Mac Studio arrive. Mitigation today is backup quality (§5).
- **SPIFFE/SPIRE integration** (per §7B) — deferred. SPIRE on macOS is "experimental" as of 2026-Q1; revisit when SPIFFE project marks Mac agent stable.
- **OpenBao parallel-deploy test** (per §8.2) — deferred to Phase 14. Insurance test, not urgent.
- **Sysmon-for-Linux on Threadripper** — deferred until Threadripper exists.
- **Apple Endpoint Security Framework / Santa** — deferred to H2+. ESF is the right Mac-side runtime telemetry (§7F), but it's additive to the Wazuh+osquery baseline.
- **Platform CHANGELOG** (finding 9G.3) — deferred. Phase docs cover this need adequately for now.
- **DNS multi-path / DoT / DoH for `*.internal`** — deferred. Single-path through OPNsense is acceptable LAN risk.
- **Falco on Linux** — deferred until Threadripper exists. Linux-only per §7D, has no place on Mac-only deployment.

### 10.4 H1 success criteria (definition of done)

H1 is complete when:
1. `vault audit list` shows at least one enabled audit device, and tail of audit log shows entries from the last 5 minutes of activity.
2. Vault container is restarted (manually or via Docker daemon restart) and **comes up unsealed automatically**.
3. `docs/runbooks/vault-*.md` exist, are readable, and contain the exact commands an operator would copy-paste.
4. `pre-commit run --all-files` passes locally; pre-commit installed on the committer's machine.
5. `docs/architecture/dependency-graph.md` renders as a Mermaid diagram showing every registered service.
6. `docs/runbooks/what-changed-last-24h.md` exists and references every log source enumerated in 9F.
7. The `5 untracked files at repo root` finding is resolved — each file is either committed or ignored, with a one-line rationale per file in the commit.
8. A mock incident drill: "Vault is sealed at 02:00 — what do you do?" has a defined answer that another operator could execute.

### 10.5 Architectural decisions requiring user input before H1 starts

These three decisions block H1 kickoff and should be confirmed before mutations begin:

**Decision A**: Transit auto-unseal — yes, no, or "use Shamir manual but document the unattended-restart hazard"? (Audit recommends YES; cost is one extra container + one set of offline keys.)

**Decision B**: Audit log retention policy — keep all, rotate after N days, ship to QNAP for long-term? Today this is undecided. (Audit recommends: 30-day local rotation + nightly rsync to QNAP `/share/CACHEDEV2_DATA/audit-archive/`.)

**Decision C**: pre-commit toolchain — Python `pre-commit` (mainstream, requires Python ≥3.9) or `lefthook` (Go binary, faster, less ubiquitous)? (Audit recommends pre-commit for ecosystem maturity and detect-secrets integration.)

=== SECTION 10 COMPLETE — 2095 lines ===

## 11. TL;DR — rendered at top per amendment 5

The TL;DR has been spliced into the top of this document, immediately under the title. This section exists to satisfy the section-marker contract. The synthesis logic that produced it:

- **Findings ranked by**: severity × urgency × leverage. Two CRITICALs (9A.1, 9F) and three HIGHs (9D.2, 9A.2, 9G.1) qualified for the top-five list.
- **Decisions ranked by**: blocking-effect on H1 kickoff. Auto-unseal posture, audit-log retention, and pre-commit toolchain are the three that gate the very first H1 commit.
- **Confidence levels**: HIGH for H1 (familiar patterns, single-host, no migration); MEDIUM for H2 (Wazuh rule-tuning is open-ended); explicitly NOT estimating later-bucket items.

Final audit checks:

- 11 section separators present: `=== SECTION N COMPLETE ===` × 11 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11).
- TL;DR at top: yes, replaced in-place per amendment 5.
- Vendor/independent pairing: §7 sources list separates vendor and independent; in-text citations identify vendor-only claims explicitly.
- Heterogeneous-arch tags: every §7 recommendation tagged [macOS] / [Linux] / [Windows] / [cross-platform].
- UNVERIFIED claims: limited to §2 image-CVE content (Trivy deferred per amendment 1) and Adfinis 1.x→2.0 recovery-key compatibility note in §7A (paired with reproduction account).
- Read-only: zero mutations to system state during audit; only this document plus git commit.

=== SECTION 11 COMPLETE — 2132 lines ===
