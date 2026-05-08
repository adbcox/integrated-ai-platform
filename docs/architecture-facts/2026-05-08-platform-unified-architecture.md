# Platform Unified Architecture — Hardware × Software

**Date:** 2026-05-08
**Status:** Active doctrine — synthesis of hardware-side rework (this session) and software/AI side (already extensive in repo)
**Pairs with:** `2026-05-08-converged-platform-architecture.md` (hardware), `circulatory-doctrine.md` (placement principle)
**Supersedes:** any prior implicit assumption that hardware and software architectures are separate concerns

## Status of this document

This document brings together the hardware architecture (captured 2026-05-08 in the converged-platform-architecture.md and circulatory-doctrine.md) with the software/AI architecture (already extensive in repo across 35+ architecture-facts files, 18 ADRs, system-prompts tier docs, dependency graph, and PROJECT_FRAMEWORK.md). It treats the platform as ONE system across both axes.

The hardware rework triggered by the 2026-05-07/08 sessions changes substrate placement. Many existing software/AI doctrines remain doctrinally correct but need their substrate references updated. Some references in CLAUDE.md and PROJECT_FRAMEWORK.md will become stale after the D-17-211 migration completes.

## The two axes

**Hardware axis (organs):**
1. Convergence appliance (MS-01) — network edge + application tier
2. Storage + media-serving (QNAP TVS-h674T)
3. Home automation (HA NUC i5)
4. AI orchestration (Mac Mini Pro M4)
5. AI inference (Mac Studio M3 Ultra)
6. CUDA compute (Threadripper #1, on-demand)
7. Single-zone monitoring (Pi 5)
8. Network infrastructure (Ruckus + Deco)
+ cold-spare (Protectli) and project hardware (TR2, MS-01 future expansion)

**Software/AI axis (logical surfaces — partial enumeration):**
1. Identity infrastructure (Vault + AppRoles + sidecars + Vaultwarden)
2. Network infrastructure (OPNsense + Dnsmasq + Caddy + Headscale + Tailscale subnet router)
3. CMDB / state (NetBox + service registry MVP + artifact registry)
4. Application services (arr-stack 11 services + Buildarr + Plex MCP bridge)
5. Observability (Grafana + VictoriaMetrics + vmagent + Zabbix + cAdvisor + node-exporter + Uptime Kuma + Topology API + Scraparr)
6. AI inference (Ollama + LiteLLM Gateway + Open WebUI + AnythingLLM + exo cluster)
7. AI orchestration (Claude Code + Goose + Aider + OpenHands + Obot + Obot shims + MCP servers + MCPO proxy)
8. Productivity (OpenProject — replaced Plane per ADR-A-018, Nextcloud)
9. Operator surfaces (Homarr + Homepage + Operator Control Plane)
10. Media-serving (Plex + Jellyfin + Navidrome + Audiobookshelf — already on QNAP)
11. Storage primitives (Syncthing + Restic + MinIO + ZFS)
12. Home automation (Home Assistant — on .141, integrations + Zigbee + ESP32)
13. System prompts tier corpus (T1-general + T2-throughput + T3-specialty + T4-distributed + 5 modes + consumer mappings)
14. Provenance + model verification (`hf-download-verified.sh`, Cisco Provenance Kit candidate, _provenance/ JSONs)
15. Goose recipes + Spec Kit (Phase 17/18 in-flight)
16. Doctrine substrate (PROJECT_FRAMEWORK + CLAUDE.md + 35 architecture-facts + 22 ADRs + master log Findings A-DD)

## Mapping — software surfaces to hardware organs

### Identity infrastructure → MS-01 Linux VM (post-D-17-213 migration)

| Software | Hardware organ | Rationale |
|---|---|---|
| Vault server (HashiCorp Vault) | MS-01 Linux VM | Always-on identity infra; relocates from Mac Mini Pro per D-17-213 |
| seal-vault container (Transit autounseal source) | MS-01 Linux VM | Co-located with Vault; cold-start dependency intact |
| Vault Agent sidecars (per service) | Co-located with consumer | If consumer on MS-01 Linux VM → sidecar there; if consumer on QNAP → sidecar via Vault Agent fetching from Vault on MS-01 across LAN |
| Vaultwarden (user password manager) | MS-01 Linux VM | Always-on, web UI, fits application tier |

**Doctrines affected:** `vault-agent-sidecar-pattern.md` — pattern intact, `host.docker.internal` references replaced with same-network DNS (`http://vault-server:8200`).

### Network infrastructure → OPNsense VM on MS-01 hardware

| Software | Hardware organ | Rationale |
|---|---|---|
| OPNsense (firewall, NAT, VPN) | OPNsense VM on MS-01 | Per D-17-211 convergence |
| Dnsmasq (sole DNS authority, 55+ records) | OPNsense VM on MS-01 | Per D-17-21 close; substrate moves with OPNsense |
| Caddy reverse proxy (19+ *.internal routes) | OPNsense VM on MS-01 (`os-caddy` plugin) | Per D-17-211; co-located with DNS authority |
| Headscale control plane | MS-01 Linux VM (NOT OPNsense) | No `os-headscale` plugin; runs as Docker container alongside Vault |
| Tailscale subnet router | OPNsense VM (`os-tailscale` plugin) | Network function on network OS; per D-17-212 |

**Doctrines affected:** `caddy-internal-tls-doctrine.md` (substrate change OPNsense plugin replaces Mac Mini Docker; auto-internal-TLS feature parity verified pre-flight). `opnsense-dns-authority.md` (already VERIFIED post-D-17-21; no doctrinal change, just VM substrate vs bare metal).

### CMDB / state → spans multiple organs

| Software | Hardware organ | Rationale |
|---|---|---|
| NetBox CMDB (canonical service inventory) | MS-01 Linux VM (likely; needs separate decision) | Per ADR-A-014, NetBox is canonical. Heavy multi-container (NetBox + Postgres + Redis + Redis Cache + Worker + Housekeeping). Stays on application tier. |
| Service registry (`~/.platform-registry/inventory.json`) | Generated artifact, not a service | Lives on filesystem; canonical for runtime topology |
| Artifact registry (`~/.platform-registry/artifacts/`) | Generated artifact | Lives on filesystem; sibling to service registry |
| `artifact-resolve.sh` resolver | Runs wherever needed | Path: `qnap://...` → local mount path |

**Doctrines affected:** ADR-A-014 (NetBox authority) intact. Service registry MVP (Finding CC) gains a new integration point: OPNsense API automation surface drives DNS/firewall/DHCP from registry state.

**Critical gap surfaced:** The three-substrate drift (NetBox vs `service-registry.yaml.DEPRECATED` vs runtime `inventory.json`) per Finding 4 from `integration-audit-doctrine.md` is not resolved by the hardware rework. Still requires its own deliverable.

### Application services → MS-01 Linux VM (primary) + QNAP (media serving)

| Software | Hardware organ | Rationale |
|---|---|---|
| arr-stack: Sonarr, Radarr, Lidarr, Readarr, Sportarr, Bazarr, Cleanuparr, Prowlarr, SABnzbd, FlareSolverr | MS-01 Linux VM | Real Linux Docker; native filesystem access via NFS over TB4 to QNAP |
| Buildarr (config-as-code for Radarr+Prowlarr) | MS-01 Linux VM | Co-located with the services it manages |
| Plex Media Server | QNAP Container Station | Storage-coupled; co-located with media files |
| Jellyfin | QNAP Container Station | Per D-17-159 ACCEPTED [B] — replaces Plex over time |
| Navidrome (music) | QNAP Container Station | Storage-coupled |
| Audiobookshelf | QNAP Container Station | Storage-coupled |
| Plex MCP Bridge | MS-01 Linux VM (or QNAP CS) | Bridges Plex API to MCP; can live on application tier or with Plex |
| Syncthing (seedbox→QNAP) | QNAP native (QPKG) | Per ADR-A-007; storage-tier function |

**Doctrines affected:** `arr-stack-auth-doctrine.md`, `download-pipeline-monitoring-doctrine.md`, `media-stack-doctrine.md`, `indexer-strategy-doctrine.md`. None doctrinally invalidated; substrate references updated.

**Critical:** Finding 22 (cross-host Docker→QNAP-host filter) is NARROWED by this architecture. Empirical evidence was Mac-Mini-Docker-bridge → QNAP-host-service. With arr-stack on MS-01 Linux VM, that exact pattern doesn't occur. Container Station containers on QNAP making intra-QNAP calls is a different code path; the Finding 22 doctrine should be edited to reflect its actual evidence (cross-host pattern only).

### Observability → spans organs by function

| Software | Hardware organ | Rationale |
|---|---|---|
| Zabbix server | Pi 5 8GB | Single-zone always-on, dedicated; "we ran enterprise monitoring on a Pi" doctrine |
| Zabbix postgres + web | Co-located with server (Pi or MS-01 — TBD) | Single-zone monitoring tier |
| Zabbix agents | Every host | Native install on each organ; reports to server |
| Grafana | MS-01 Linux VM | Application tier dashboard surface |
| VictoriaMetrics | MS-01 Linux VM | Time-series store; co-located with Grafana |
| vmagent | MS-01 Linux VM | Scrapes targets, writes to VictoriaMetrics |
| cAdvisor | MS-01 Linux VM | Container metrics for the VM's own containers |
| node-exporter | Every host | Native or container per host |
| Uptime Kuma | MS-01 Linux VM | UI surface |
| Topology API | MS-01 Linux VM | Application tier |
| Scraparr (D-17-46 arr-stack metrics path) | MS-01 Linux VM | Co-located with arr-stack it scrapes |

**Doctrines affected:** D-17-46 arr-stack metrics observability doctrine intact; Scraparr → vmagent → VictoriaMetrics → Grafana chain entirely on MS-01 Linux VM = simpler topology than cross-host.

**Open question:** Zabbix postgres on Pi 5 8GB is feasible but tight (postgres + Zabbix server in 8GB). Alternative: Zabbix postgres on MS-01 Linux VM, Zabbix server on Pi reaching back across LAN. Pick one before D-17-211 Phase D.

### AI inference → Mac Studio (canonical) + Threadripper #1 (CUDA) + exo cluster (T4, blocked)

| Software | Hardware organ | Rationale |
|---|---|---|
| Ollama (multi-model serving) | Mac Studio M3 Ultra | Apple Silicon ML-optimized; 96GB unified |
| LiteLLM Gateway | MS-01 Linux VM | Routing layer; not inference itself |
| Open WebUI | MS-01 Linux VM | UI for inference; consumes via LiteLLM |
| AnythingLLM | MS-01 Linux VM | RAG + chat UI; consumes Ollama |
| exo cluster (T4-distributed) | Mac Mini Pro + Mac Studio + (future) Threadripper-1 with TB5 card | Apple Silicon nodes; **broken upstream** per Findings U+V |
| `hf-download-verified.sh` provenance gate | Wherever models are pulled | Standardizes provenance across hosts |
| Cisco Provenance Kit (locked roadmap T1 priority) | TBD | Verifies HF model lineage; CPU-only, can run on MS-01 Linux VM or Mac Mini Pro |

**T1-T4 tier mapping:**

- **T1-general-purpose** (default, fast, broad capability): Ollama on Mac Studio (e.g., Qwen2.5-Coder-32B, Gemma 4)
- **T2-throughput** (high-volume, batch): Ollama on Mac Studio (e.g., 14B models with high context)
- **T3-specialty** (domain-specific): Ollama on Mac Studio for MLX-format; Threadripper #1 + RTX 4070 for CUDA-format models when online
- **T4-distributed** (cluster-only capacity): exo cluster — currently NOT ROUTABLE per Findings U+V; documentation-only tier

Operator's locked roadmap (T1-T4 prioritization, 2026-05-01):
- T1: System Prompt Library + Cisco Provenance Kit (no new hardware needed)
- T2: Gemma 4 vs Qwen3-Coder-Next benchmark on RTX 4070 (Threadripper #1 powered on)
- T3: Goose agentic surface (already in motion)
- T4: exo cluster gated on macOS 26.2

**Doctrines affected:** `local-model-tier-doctrine.md`, `local-prompt-library-doctrine.md`, `model-provenance-doctrine.md`, `model-provenance.md`, `local-tool-calling.md`, `mcp-servers.md`, `exo-cluster.md`. None doctrinally invalidated; tier-to-hardware mapping is explicit in this section.

### AI orchestration → Mac Mini Pro (clean of containers post-migration)

| Software | Hardware organ | Rationale |
|---|---|---|
| Claude Code | Mac Mini Pro M4 (native) | Operator-driven agent runtime; M4 Pro performance |
| Goose | Mac Mini Pro (native) | Agent runtime |
| Aider (compute, intelligence, verifier) | Mac Mini Pro (native) | Per `aider-*-doctrine.md` series; verifier may call Mac Studio Ollama |
| OpenHands | MS-01 Linux VM | Agentic platform; container workload |
| Obot (Acorn Labs platform) | MS-01 Linux VM | Container, multiple shim containers |
| Obot shims (fitness, github, postgres, semgrep, strava, weather, generic-a/b/c) | MS-01 Linux VM | Co-located with Obot |
| MCP servers (Docker Remote, Docs Remote, Filesystem Remote) | MS-01 Linux VM | Container workloads |
| MCPO Proxy | MS-01 Linux VM | Container |
| Plex MCP Bridge | MS-01 Linux VM | Bridges Plex API for agents |
| `claude-local`, `claude-pro`, `claude` aliases | Mac Mini Pro shell config | Operator's CLI shortcuts |

**Doctrines affected:** `goose-capability-boundary.md`, `goose-session-pipeline.md`, `aider-compute-doctrine.md`, `aider-intelligence-doctrine.md`, `aider-verifier-doctrine.md`, `agent-trace-corpus-doctrine.md`, `capability-self-knowledge.md`, `known-capabilities.md`, `work-routing-doctrine.md`. Substrate references updated; orchestration host vs application tier split clarifies which surfaces run where.

### Productivity → MS-01 Linux VM

| Software | Hardware organ | Rationale |
|---|---|---|
| OpenProject | MS-01 Linux VM | Replaces Plane CE per ADR-A-018; container workload |
| OpenProject database (PostgreSQL) | MS-01 Linux VM | Co-located with OpenProject |
| Nextcloud | MS-01 Linux VM | Self-hosted file sync/share |
| Nextcloud database (PostgreSQL) | MS-01 Linux VM | Co-located with Nextcloud |
| Plane CE (deprecated) | RETIRED per ADR-A-018 | Plane + Plane API + Beat + DB + MinIO + Redis + Worker all retire |

**Doctrines affected:** `openproject-enrichment-doctrine.md`, `openproject-migration.md`. Plane retirement is operator-side cleanup task per Finding 9 sub-doctrine.

### Operator surfaces → MS-01 Linux VM

| Software | Hardware organ | Rationale |
|---|---|---|
| Homarr (dashboard) | MS-01 Linux VM | UI service |
| Homepage (Control Center) | MS-01 Linux VM | UI service; consumes OPNsense API + others |
| Operator Control Plane | MS-01 Linux VM | UI service |
| Docker Socket Proxy | MS-01 Linux VM | Per-container Docker socket exposure |

### Storage primitives → QNAP

| Software | Hardware organ | Rationale |
|---|---|---|
| Syncthing (QPKG native) | QNAP | Storage-tier function |
| Restic backup | Mac Mini Pro launchd → MS-01 (post-migration) writing to MinIO on QNAP | Backup chain |
| MinIO (S3-compatible, Restic target) | QNAP Container Station | Storage-tier; per ADR-A-017 (Vault warm-copy backup) |
| ZFS pool (QuTS hero) | QNAP | Native storage layer |

### Home automation → HA NUC

| Software | Hardware organ | Rationale |
|---|---|---|
| Home Assistant | HA NUC i5 (.141) | Per D-17-34 close; canonical sole instance |
| MQTT broker (likely) | HA NUC (Add-on) | Co-located with HA |
| Zigbee2MQTT or ZHA | HA NUC | Co-located with Zigbee USB stick |
| ESPHome (if used) | HA NUC | Co-located with HA |
| HA Add-ons (various) | HA NUC | HA-domain extension |

**Doctrine question:** if a future "edge-AI mini" is added (deferred decision per hardware doc), HA voice assist (Whisper + Gemma 4 E4B + Piper TTS) goes there, not on HA NUC. Currently no edge-AI mini exists.

## Cross-cutting integration points

### 1. Service Registry MVP × OPNsense API automation

This is the unification's biggest synergy. Hardware architecture creates the OPNsense API automation surface (extending existing `opnsense_runner.py`). Software architecture has the service registry MVP (Finding CC, `architecture-patterns/service-registry-mvp.md`) defining the schema. Integration:

```
Service deployed (compose up) → registry refresh (`scripts/platform-registry/refresh.sh`)
                              → registry inventory.json updated
                              → OPNsense API automation script reads registry
                              → DNS records, firewall rules, DHCP reservations
                                ensured to match registry state
                              → Drift detected if manual changes diverge
```

This closes Finding CC at the runtime topology layer AND extends the asset-management substrate (Finding T) with network state. Operator's locked roadmap mentions Symphony + Spec Kit for ticket → agent → PR pipeline; OPNsense API automation is an analogous pattern for service → network state.

### 2. NetBox CMDB × physical-architecture audit

ADR-A-014 makes NetBox canonical for service state. Hardware architecture (this rework) adds canonical fleet state via `physical-architecture-2026-05-08.md`. Three-substrate drift (Finding 4) is not closed; deliverable proposed: NetBox ingests physical-architecture data via API, treats hardware as parent objects of services.

### 3. Vault × all credential consumers

Vault relocation (D-17-213) affects every Vault Agent sidecar, every Goose recipe that reads from Vault, every credentials.env render. Per hash-only verification doctrine, no values displayed during migration; verification is hash round-trip.

### 4. Caddy `*.internal` × Dnsmasq DNS authority

Caddy migration to OPNsense `os-caddy` plugin (D-17-211 WP-A-04) co-locates with Dnsmasq. Reverse proxy + name resolution on the same host. Single config plane for `*.internal` namespace.

### 5. Backup chain × storage tier

Restic → MinIO on QNAP. Post-migration the backup source includes MS-01 Linux VM (snapshots + Vault data + arr-stack configs + container state). Backup target unchanged (MinIO on QNAP). Backup AppRole authentication intact. Restore procedure (`docs/runbooks/vault-restore-from-backup.md`) needs update to reflect VM-based Vault.

### 6. Zabbix monitoring × every host

Zabbix server moves to Pi (D-17-211 Phase D). Every host runs Zabbix agent reporting to Pi. Container-level health checks via cAdvisor on MS-01 Linux VM. Integration health checks per D-17-38 doctrine (Layer 1-3 probing) span the whole platform regardless of which organ hosts the integration.

### 7. exo cluster × TB5 link

TB5 cable Mac Mini Pro ↔ Mac Studio preserved. exo cluster substrate operational; distributed inference blocked upstream per Findings U+V. Hardware architecture doesn't change exo status; preserves existing setup.

When Threadripper #1 comes online with TB5 PCIe card (post-D-17-212 Phase 5 cable plan), it does NOT join exo cluster (exo is Apple Silicon-only via MLX backends). Threadripper-1's TB5 link is for QNAP data path, not for inference clustering.

### 8. Plex/Jellyfin × QNAP × arr-stack

arr-stack on MS-01 imports files via NFS over TB4 to QNAP. Plex/Jellyfin on QNAP read same files from local QNAP filesystem. No cross-host data path for media serving. Plex MCP bridge on MS-01 calls Plex API on QNAP across LAN — small JSON payloads, LAN is fine.

## Doctrines that need updating because of hardware moves

Targeted updates required (NOT full rewrites):

1. **CLAUDE.md** — top-level. References:
   - "Mac Mini M4 Pro is the **control plane** today" → becomes "Mac Mini M4 Pro is the **AI orchestration host**; convergence appliance (MS-01) is the platform control surface"
   - "Deployment target: Mac Mini .145" → becomes "Deployment target depends on tier; orchestration on Mac Mini .145, application tier on MS-01 Linux VM"
   - Hardware section needs MS-01, Pi, Threadripper updates and removal of stale "M5" references
2. **PROJECT_FRAMEWORK.md** (157KB) — sweep needed for hardware references; targeted edits to §9 and any host-specific service placement references
3. **`architecture-facts/dependency-graph.md`** — regenerate from NetBox post-migration; update Caddy/Vault/Headscale/Tailscale arrows to reflect new substrate
4. **`architecture-facts/integration-audit-doctrine.md` Finding 22** — narrow to its empirical evidence
5. **`architecture-facts/caddy-internal-tls-doctrine.md`** — substrate change (OPNsense plugin)
6. **`architecture-facts/vault-agent-sidecar-pattern.md`** — substrate change (Vault on MS-01 Linux VM)
7. **`architecture-facts/arr-stack-auth-doctrine.md`** — substrate change (arr-stack on MS-01 Linux VM)
8. **`architecture-facts/download-pipeline-monitoring-doctrine.md`** — Finding 24 (Syncthing as silent SPOF) still applies; update path references
9. **`architecture-facts/host-portability.md`** — likely affected by hypervisor introduction; Linux VM becomes a portable target
10. **`docs/runbooks/qnap-downloads-mount.md`** — RETIRE (NFS replaces SMB)
11. **`docs/runbooks/add-new-service.md`** — substrate update; new services land on MS-01 Linux VM by default
12. **`docs/runbooks/vault-restore-from-backup.md`** — VM-based Vault restore procedure

## Conflicts and gaps surfaced by the rework

### Resolved by this architecture

- **Sleep-vs-always-on contradiction.** Mac Mini Pro can sleep when idle (Vault + Headscale relocated)
- **Mac Mini Pro overload.** ~66 containers → 0 containers post-migration
- **SMB mount + Docker Desktop friction.** Both retired; NFS over TB4 replaces
- **Cross-host Docker → QNAP-host filter (Finding 22 empirical pattern).** No longer occurs; arr-stack is on its own host
- **Reverse proxy and DNS authority split.** Co-located on OPNsense (one organ for network edge functions)

### Not resolved by this architecture (still need their own deliverables)

1. **NetBox / service-registry / inventory.json three-substrate drift** (Finding 4). Reconciliation pass deliverable still needed.
2. **Cisco Provenance Kit installation** (locked roadmap T1 priority). Independent of hardware.
3. **System Prompt Library versioning** (locked roadmap T1 priority). Pure config; independent of hardware.
4. **exo distributed inference unblock** (Findings U+V). Upstream-gated.
5. **HA voice assist tier** (deferred; second-mini decision pending operator).
6. **3D model license provenance schema** (Manyfold + Gitea LFS). Independent of hardware rework.
7. **Threadripper #2 fix path** (Option A: $0-150 for X399 board + DDR4 ECC UDIMM). Independent.
8. **Inbox Zero deployment** (BLOCKED on Gmail tier scope). Independent.
9. **Symphony + Spec Kit + OpenShell sandboxing** (Phase 13+ agentic layer). Software-side, but hosting decisions affected: agent execution sandboxes likely run on MS-01 Linux VM or in dedicated VMs.

### Conflicts that need operator decision

1. **NetBox placement.** Multi-container heavy service. Stays on MS-01 Linux VM by default but adds resource pressure. Alternative: dedicated VM. Operator picks.
2. **Plane CE retirement timing.** Per ADR-A-018 OpenProject replaces it; if not yet fully retired, this hardware migration is a forcing function. Plane + dependencies retire as part of D-17-211 Phase E.
3. **Zabbix postgres location.** Pi 5 8GB tight; alternative is postgres on MS-01 Linux VM, Zabbix server on Pi calling postgres across LAN. Operator picks before Phase D.
4. **OpenHands, Obot, AnythingLLM resource budget.** These are heavy services (each can use several GB RAM). MS-01 Linux VM with 16-20GB allocated may be tight if all are simultaneously loaded. Consider: split application tier into "always-on services" VM and "agent runtime" VM if pressure surfaces.
5. **Plex MCP Bridge location.** Could go on MS-01 (with arr-stack and other agent services) or on QNAP (with Plex). Either works; operator picks.

## Migration sequencing — software follows hardware

Per the hardware migration runbook (`d-17-211-convergence-migration.md`), software services migrate in defined phases. Critical sequencing:

**Phase A (OPNsense move):**
- Caddy moves to `os-caddy` plugin (or `os-haproxy` fallback)
- Tailscale subnet router moves to `os-tailscale` plugin
- Dnsmasq DNS authority moves with OPNsense (data preserved via config import)

**Phase B (Linux VM + service migration):**
- Vault server moves first (because every other service depends on Vault for credentials)
- Headscale moves second (network auth control plane)
- arr-stack moves third (depends on Vault for sidecar credentials)
- Other services (NetBox, observability stack, AI services, productivity, operator surfaces) migrate per their own dependency order

**Phase C (TB segment):**
- arr-stack uses NFS over TB4 to QNAP (replaces SMB mount)
- Backup chain (Restic → MinIO) uses TB4 if on a TB-connected host

**Phase D (Pi monitoring):**
- Zabbix server migration; agents reconfigure

**Phase E (decommissioning):**
- Mac Mini Docker stack retires entirely
- Docker Desktop uninstalled
- SMB mount + LaunchDaemon retired
- AppRole/policy cleanup per Finding 3 sub-doctrine

**Phase F (doctrine + audit):**
- This unification doc + the hardware-side artifacts become the canonical reference
- Existing doctrines updated per the list above
- NetBox + service-registry + inventory.json reconciliation deliverable scoped (not executed) as follow-on

## Open items (combined hardware + software)

Hardware open items (per `2026-05-08-converged-platform-architecture.md`):

1. Mac dual-homing vs TB-only post-stability transition
2. Hypervisor confirmation (Proxmox VE recommended)
3. Voice assist tier (potential second mini)
4. Threadripper #1 power-on cadence + TB5 PCIe card procurement
5. Threadripper #2 fix path
6. Pi sourcing
7. TB segment IP range
8. Service registry MVP × OPNsense API integration

Software open items (combined with hardware):

9. NetBox placement (this doc)
10. Plane CE retirement timing (this doc + ADR-A-018)
11. Zabbix postgres location (this doc)
12. OpenHands/Obot/AnythingLLM resource budget on Linux VM
13. Plex MCP Bridge location
14. CLAUDE.md update timing (post-migration sweep)
15. PROJECT_FRAMEWORK.md sweep (post-migration)
16. dependency-graph.md regeneration (post-migration)
17. Phase 18 in-flight deliverables (D-17-46 Scraparr, etc.) — coordinate with hardware migration so phase work isn't disrupted

## Status

**Active doctrine** as of 2026-05-08. Closes the operator's request to examine and bring together the hardware and software/AI architectures as one. Subsequent sessions reference this document as the unified canonical reference; targeted updates land in the affected per-doctrine files.

## Cross-references

Hardware-side (this session):
- `architecture-facts/2026-05-08-converged-platform-architecture.md`
- `architecture-facts/circulatory-doctrine.md`
- `_audit/physical-architecture-2026-05-08.md`
- `decision-records/D-17-211-convergence-on-ms01.md`
- `decision-records/D-17-212-thunderbolt-mesh-topology.md`
- `decision-records/D-17-213-vault-relocation-to-ms01.md`
- `runbooks/d-17-211-convergence-migration.md`

Software-side (existing):
- `CLAUDE.md` (root)
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_FRAMEWORK.md` (157KB; canonical)
- `docs/PHASE_ROADMAP.md`
- `docs/architecture-facts/` (35 files)
- `docs/adr/` (18 ADRs) and `docs/decision-records/` (4 records)
- `docs/system-prompts/{tiers,modes,consumers}/`
- `docs/architecture-patterns/service-registry-mvp.md`
- `docs/_provenance/` (verified-model JSONs)
- `goose-recipes/` (5 recipes)

Master log Findings cross-referenced:
- T (asset-management substrate gap) — partial closure
- AA (architectural truth substrate gap) — this document is partial closure
- BB (misdiagnosis-via-tool-blame) — applied during this session's pivots
- CC (service registry gap) — substrate enabled by hardware architecture
- DD (container env-inspection diagnostic trap) — preserved in CLAUDE.md
- 22 (cross-host Docker→QNAP filter) — narrowed by this architecture
- 9 (residue is a positive failure mode) — applied to all decommissioning
- 4 (CMDB three-substrate drift) — NOT resolved; future deliverable
