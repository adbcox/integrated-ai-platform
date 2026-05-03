# Service Registry MVP — Intake Doc

**Deliverable ID (provisional):** D-17-29
**Phase:** 17
**Owner:** Adrian Cox (architect/PM); Claude Code (executor)
**Status:** Spec authored 2026-05-02 evening, execution Sunday May 4 morning
**Hard cap:** 6 hours including testing

## 1. Goal

Replace port-discovery archaeology with structured, AI-consultable answers about service reachability.

The 2026-05-02 evening seal-vault recovery cost ~3 hours, primarily because the AI did not know seal-vault listened on port 8201 (not 8200). That archaeology pattern repeats across every recovery, upgrade, and debug session. The registry eliminates it.

## 2. Operator-stated framing

> "It is like a DNS helper to resolve what you think it is gonna be to the correct port. Because it goes two ways. Internally is different in the Docker because of internal addresses chosen; externally it has been lost. You did not know the right port to go to for it. So this is not a document thing; it is a network routing thing."

— Operator, 2026-05-02 evening session

## 3. Why this unlocks autonomous coding

The autonomous coding goal that drove this entire chat requires the agent to operate against the platform without operator babysitting. The agent will need to:

- Reach inference endpoints (litellm, exo cluster)
- Reach context sources (xindex, OpenProject, Notion via MCP)
- Reach storage (Vault for credentials, Postgres for state)
- Reach observability (Zabbix, Caddy admin)

If the agent has to discover where these are at runtime, it will fail in non-obvious ways and the operator will be debugging it instead of using it. The registry is foundational: agents consult it before any operation, and the answers are canonical.

## 4. Data sources (three)

### 4.1 Compose files (intent layer — what was specified)

Two parent directories:
- `/Users/admin/control-center-stack/stacks/*/docker-compose.yml` (~7 files)
- `/Users/admin/repos/integrated-ai-platform/docker/*/docker-compose*.yml` (~25 files)

Extracts per service:
- Container name (from `services.<name>` and `container_name` if set)
- Image + tag/digest
- Internal listen ports (from `expose` and inferred from common patterns)
- Host port mappings (from `ports`)
- Network attachments (from `networks`)
- Volume mounts (from `volumes`)
- Environment variable references (without values)
- Depends-on declarations
- Compose stack origin (file path)

### 4.2 docker inspect runtime state (reality layer — what is actually running)

Source: `docker inspect` for every running container.

Extracts per container:
- Actual running state (Up/Exited/Restarting/healthy/unhealthy)
- Actual port bindings (post-Docker-runtime resolution)
- Actual IP addresses on each network
- Actual mount paths
- Restart policy + restart count
- Health check state + last result
- Started-at timestamp

### 4.3 Caddy admin API + Caddyfile (external routing layer)

Sources:
- `http://localhost:2019/config/` (Caddy admin API)
- `/Users/admin/repos/integrated-ai-platform/docker/caddy/Caddyfile` (intent file)

Extracts per route:
- External hostname (e.g., `vault.internal`)
- Upstream target (e.g., `vault-server:8200`)
- TLS config (internal CA vs external)
- Reverse proxy headers/transforms

## 5. Schema (JSON record per service)

```json
{
  "service_id": "seal-vault",
  "container_name": "seal-vault",
  "stack": "seal-vault",
  "compose_file": "/Users/admin/control-center-stack/stacks/seal-vault/docker-compose.yml",
  "image": "hashicorp/vault:1.20.0",
  "state": {
    "status": "running",
    "health": "healthy",
    "started_at": "2026-05-02T22:42:00Z",
    "restart_count": 0
  },
  "addresses": {
    "internal": [
      {"network": "vault_net", "ip": "172.20.0.5", "port_listen": 8201, "protocol": "http"}
    ],
    "host_mapped": [],
    "caddy_routes": []
  },
  "credentials": {
    "init_keys_file": "/Users/admin/seal-vault-init-keys-20260430.json",
    "is_canonical": true,
    "stale_files": [
      "/Users/admin/vault-init-keys.txt.PRE-KV-LOSS-INVALID-20260430"
    ]
  },
  "depends_on": [],
  "depended_on_by": ["vault-server"],
  "known_failure_modes": [
    {
      "id": "FM-001",
      "trigger": "macOS upgrade affecting lima VM",
      "symptom": "panic: user: unknown userid 502; daemon shutdown",
      "recovery": "colima start auto-recovers user mapping; manual unseal required after",
      "first_observed": "2026-05-02 D-17-28"
    }
  ],
  "access_examples": [
    {
      "context": "from-host-shell",
      "command": "docker exec -e VAULT_ADDR=http://127.0.0.1:8201 seal-vault vault status"
    },
    {
      "context": "from-vault-server-container",
      "url": "http://seal-vault:8201/v1/transit/decrypt/autounseal-key"
    }
  ],
  "documentation_refs": [
    "docs/runbooks/vault-unseal.md"
  ]
}
```

## 6. Output location

- `/Users/admin/.platform-registry/inventory.json` — single canonical file, full registry.
- `/Users/admin/.platform-registry/by-service/<service-id>.json` — per-service files for fast lookup.
- `/Users/admin/.platform-registry/last-refresh.json` — metadata (when generated, source counts, parse errors).

## 7. Refresh model

- **On-demand:** `bash /Users/admin/.platform-registry/refresh.sh` regenerates from sources.
- **Scheduled:** launchd plist `com.iap.platform-registry.plist` runs refresh every 15 minutes.
- **Post-deploy hook:** Add to existing compose-up runbook as final step.

## 8. AI consultation contract

Before any operation involving:
- Container ports (internal or host)
- Container reachability ("is X up?")
- Credential locations
- Service dependencies (planning a restart)
- Caddy-routed external names

The AI must consult `~/.platform-registry/inventory.json` (or the per-service file) and use those values rather than memory or guess.

Failure to consult is a doctrine violation. The 2026-05-02 seal-vault port archaeology is the canonical "what not to do" example.

## 9. Out of scope for MVP (deferred to future deliverables)

- **CoreDNS proxy on host** — exposing Docker internal DNS to host shell tools. v2 stretch goal.
- **Visualization integration** — registry data flowing into network/topology diagrams with health overlays. Belongs in the asset-management deliverable family.
- **Real-time event subscription** — Docker events socket triggering immediate refresh. v2 if 15-min scheduled refresh proves insufficient.
- **Asset/state/lifecycle data** — version tracking, upgrade-pending state, firmware inventory. Findings T, Z deliverable family.
- **Architectural truth layer** — design-level "what is X, how does it relate to Y" prose docs. Finding AA. Separate deliverable.

## 10. Success criteria

- AI can answer "where is seal-vault reachable from Mac Mini host shell, and what is the access pattern?" by reading registry. <5 seconds, no archaeology.
- AI can answer "what services depend on Vault being up?" by reading registry. Used to predict cascade impact before any Vault operation.
- AI can answer "what is the canonical credentials file for seal-vault?" by reading registry. No more grepping for "vault-init-keys" across home directory.
- Registry refresh completes in <30 seconds against current platform state.
- Registry survives all current failure modes (Vault down, Colima down, half the compose files unparseable) — best-effort output, flag what could not be parsed, do not fail entirely.

## 11. Implementation approach

Python script, ~200-300 lines.

```
~/.platform-registry/
├── refresh.sh           # entrypoint
├── lib/
│   ├── compose_parser.py
│   ├── docker_inspector.py
│   ├── caddy_reader.py
│   ├── credential_finder.py
│   ├── registry_writer.py
│   └── failure_modes.py
└── inventory.json
```

Dependencies: `pyyaml`, `requests`, standard library. No new platform-level deps.

## 12. Sequencing for Sunday execution

1. **T0 — pre-flight (15 min):** scan compose-file directories, count services, identify any parse-blockers
2. **T1 — compose parser (90 min):** ingest all compose files, extract per-service intent records
3. **T2 — docker inspector (60 min):** query runtime state, merge with intent records
4. **T3 — caddy reader (45 min):** admin API + Caddyfile, attach external-routing data
5. **T4 — credential finder (30 min):** known credential file patterns, mark canonical vs stale
6. **T5 — registry writer + tests (45 min):** JSON output, per-service split, integration tests against current platform
7. **T6 — launchd schedule + AI consultation doctrine (30 min):** plist for 15-min refresh, doctrine commit to PROJECT_FRAMEWORK.md
8. **T7 — chronicle commit (15 min):** Findings TBD documenting registry build observations

Hard cap 6h with buffer. Surface back at T2 if compose-file parse rate is below 80%.

## 13. Open questions for Sunday-morning resolution

- Are there compose files outside the two parent directories?
- What is the canonical home for the launchd plist?
- Should the registry include exo cluster nodes (Mac Mini + Mac Studio) as services even though they are not Docker?

## 14. Connection to autonomous coding goal

This deliverable is foundation for autonomous coding because:

- Agents need canonical service-discovery answers before they can route inference, retrieve context, or operate against platform services.
- Without registry, every agent operation includes archaeology overhead → agent operations are slow and failure-prone → operator does not trust the agent → autonomous coding never happens.
- With registry, agents consult once and proceed → operations are fast → trust accumulates → delegation becomes possible.

Service Registry MVP is not "infrastructure" in the sense of "boring overhead." It is the substrate that makes the destination reachable.

## 15. Cross-references

Findings from `docs/architecture-facts/exo-cluster.md`:
- Finding CC: Service-registry gap (this deliverable addresses)
- Finding T: Asset-management substrate gap (sister deliverable, post-demo)
- Finding AA: Architectural truth substrate gap (sister deliverable, post-demo)
- Finding BB: Misdiagnosis-via-tool-blame pattern (informs doctrine)
- Finding Z: Vault architectural review (post-demo)

Sequenced before:
- D-17-26 (Open WebUI exo surface)
- D-17-12 (Threadripper benchmarks, Tue/Wed)
- D-17-13 (Goose autonomous coding agent — the demo centerpiece)

Demo deadline: Saturday May 9, 2026.
