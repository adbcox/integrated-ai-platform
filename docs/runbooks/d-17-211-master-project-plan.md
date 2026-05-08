# D-17-211 Master Project Plan — Convergence Rearchitecture

**Date:** 2026-05-08
**Status:** ACCEPTED PROJECT PLAN — execution gated on operator scheduling per phase
**Scope:** Entire 2026-05-08 rearchitecture initiative (hardware migration + software migration + doctrine updates + cross-cutting integrations)
**Pairs with:** all 8 architecture artifacts dated 2026-05-08

## Project summary

This project re-platforms the Integrated AI Platform onto a converged-appliance architecture. Hardware-side conclusion: `architecture-facts/2026-05-08-converged-platform-architecture.md`. Placement principle: `architecture-facts/circulatory-doctrine.md`. Software-side conclusion: `architecture-facts/2026-05-08-platform-unified-architecture.md`. Migration mechanics: `runbooks/d-17-211-convergence-migration.md`. THIS document is the **execution plan** that ties them all together with formal gates, critical paths, decision points, risks, and dependencies.

The project consists of six numbered phases (A-F) plus three follow-on tracks (G, H, I).

## Phase / WBS overview

| Phase | Theme | Scope | Critical-path? |
|---|---|---|---|
| **Pre-flight** | Operator-side prep | All operator-only items before AI-assisted execution can begin | YES — gates Phase A |
| **A** | Hypervisor + OPNsense migration | Proxmox install, OPNsense VM, config restore, plugin install, cutover from Protectli | YES |
| **B** | Linux VM + service migration | Ubuntu LTS VM, Vault relocation, Headscale, arr-stack + extended service set | YES |
| **C** | TB segment | TB cabling, IP plan, mDNS reflection, Mac dual-homing | NO (additive; can run after Phase B stable) |
| **D** | Pi monitoring | Zabbix server migration to Pi 5 | NO |
| **E** | Decommissioning | Mac Mini Docker stack retire, SMB mount retire, Docker Desktop retire, Mac Mini sleep enable, Protectli cold-spare | YES — gates Phase F |
| **F** | Doctrine + audit | CLAUDE.md, PROJECT_FRAMEWORK.md, dependency graph, all affected doctrines updated | YES (closes the project) |
| **G** | Service Registry MVP × OPNsense API | Cross-cutting integration (post-Phase F) | NO — follow-on |
| **H** | NetBox × physical-architecture integration | Cross-cutting integration (post-Phase F) | NO — follow-on |
| **I** | T1-T4 roadmap items | System Prompt Library, Cisco Provenance Kit, Conductor-pattern POC | NO — runs in parallel; not blocked by hardware |

## Critical path

```
Pre-flight  →  Phase A  →  Phase B  →  Phase E  →  Phase F  →  PROJECT COMPLETE
                                ↘ Phase C (parallel after B)
                                ↘ Phase D (parallel after B)
```

**Rationale:** Phase A must precede Phase B (Linux VM bridges through OPNsense). Phase B must precede Phase E (services must run on new substrate before old retires). Phase E must precede Phase F (doctrine documents FINAL state). Phases C, D run in parallel after B is stable. G, H, I are follow-on with their own scheduling.

## Decision points / gates

Each phase boundary has a **gate** — validation criteria that must pass before the next phase begins. Gates are non-negotiable per existing platform Verification Doctrine.

| Gate | Position | Validation criteria | Owner |
|---|---|---|---|
| **G0** | Pre-flight → Phase A | All operator-side pre-flight items confirmed; maintenance window scheduled | Operator |
| **G1** | Phase A → Phase B | OPNsense VM is the active edge; Internet works; DNS resolves; Caddy serves *.internal; Tailscale subnet router operational | Operator |
| **G2** | Phase B → Phase C/D/E | Vault unsealed on MS-01; arr-stack passes hardlink + 1-album/episode/movie test; all Mac Mini Docker services have MS-01 counterparts running | Operator |
| **G3** | Phase C → cleanup | TB segment operational with NFS hardlinks proven; mDNS reflection working for Continuity | Operator |
| **G4** | Phase D → cleanup | Zabbix server on Pi receiving metrics from every host | Operator |
| **G5** | Phase E → Phase F | Mac Mini Docker stack stopped; Docker Desktop uninstalled; Mac Mini Pro sleep verified; Protectli FW4B disposition decided | Operator |
| **G6** | Phase F → COMPLETE | All affected docs updated; dependency graph regenerated; physical-architecture audit refreshed | Operator |

Each gate has a rollback path documented in the migration runbook. Most critical rollback: Phase A cutover → Protectli FW4B.

## Pre-flight (operator-owned, no AI execution)

Before Phase A can begin, ALL of these must be confirmed by the operator:

| ID | Item | Done? |
|---|---|---|
| P-01 | MS-01 operational state confirmed (BIOS POST clean, RAM detected as DDR5-5600, all storage visible) | ☐ |
| P-02 | OPNsense config XML exported from Protectli FW4B (saved off-MS-01) | ☐ |
| P-03 | Vault raft snapshot exported from Mac Mini Pro | ☐ |
| P-04 | Mac Mini Docker arr-stack compose + volumes snapshot | ☐ |
| P-05 | Maintenance window scheduled (target: 2-hour window for Phase A) | ☐ |
| P-06 | Cold-spare Protectli plan committed (recommended: cold-spare) | ☐ |
| P-07 | TB cables procured (minimum: 1× TB4 for MS-01 ↔ QNAP) | ☐ |
| P-08 | Pi 5 8GB sourced for Phase D | ☐ |
| P-09 | Hypervisor decision confirmed (Proxmox VE recommended; bare-metal Ubuntu+KVM fallback) | ☐ |
| P-10 | TB segment IP range chosen (172.20.20.0/24 proposed) | ☐ |
| P-11 | Operator presence confirmed for Phase A maintenance window | ☐ |

**Gate G0 criteria:** all 11 items checked.

## Phase A — Hypervisor and OPNsense migration

**Outage impact:** WAN down briefly during cutover (target: <30 min actual; 2-hour window with rollback margin)
**Rollback:** Power Protectli back on; it retains current config

| WP ID | Work package | Effort | Depends on | Critical? |
|---|---|---|---|---|
| WP-A-01 | Proxmox VE install on MS-01 (ZFS host filesystem, mgmt network) | M | P-01, P-09 | YES |
| WP-A-02 | OPNsense VM provisioning (cores/RAM/disk; PCIe passthrough decision) | M | WP-A-01 | YES |
| WP-A-03 | OPNsense config restore (XML import; verify Dnsmasq 55+ records) | L | WP-A-02, P-02 | YES |
| WP-A-04 | os-caddy plugin install + Caddyfile migration; auto-internal-TLS pre-flight test | M | WP-A-03 | YES |
| WP-A-05 | os-tailscale plugin install + subnet router config | M | WP-A-03 | YES |
| WP-A-06 | Cutover — physical cable move Protectli → MS-01; Internet validation | M | WP-A-01..05 | YES |

**Gate G1 criteria:**
- LAN client can ping 8.8.8.8 (Internet via MS-01 OPNsense)
- LAN client can resolve google.com (DNS via Dnsmasq on MS-01)
- LAN client can curl https://*.internal Caddy routes
- Tailnet client can reach LAN via subnet router
- Protectli FW4B successfully powered down as cold-spare

**Risks:**
- R-A-01: os-caddy lacks auto-internal-TLS feature parity → fallback to os-haproxy + internal CA per ADR D-17-211
- R-A-02: PCIe passthrough fails → use VirtIO networking initially
- R-A-03: WAN config not captured pre-flight → maintenance window extends; mitigate by capturing on Protectli before P-02

## Phase B — Linux VM and service migration

**Outage impact:** brief (~15 min) Vault and arr-stack unavailability during cutover
**Rollback:** Mac Mini Pro Docker stack runs in parallel until WP-B-07

| WP ID | Work package | Effort | Depends on | Critical? |
|---|---|---|---|---|
| WP-B-01 | Ubuntu LTS VM provisioning (8 cores, 20GB RAM, 200GB disk, Docker Engine, tailscale, nfs-common) | M | G1 | YES |
| WP-B-02 | Vault server migration: stand up on Linux VM; restore raft snapshot; verify unsealed | H | WP-B-01, P-03 | YES (D-17-213) |
| WP-B-03 | Headscale migration: state DB export/import; verify nodes + ACL | M | WP-B-01 | YES |
| WP-B-04 | arr-stack compose translation (Mac paths → Linux paths; sidecar URL update) | M | WP-B-02 | YES |
| WP-B-05 | NFS mount QNAP via TB4 (or LAN initially if TB delayed) | M | WP-B-04, P-07 | YES |
| WP-B-06 | arr-stack parallel bring-up + validation (1-album / 1-episode / 1-movie hardlink test) | H | WP-B-05 | YES |
| WP-B-07 | Cutover: stop Mac Mini Docker arr-stack/Vault/Headscale/Caddy; verify Linux VM primary | M | WP-B-06 | YES |
| WP-B-08 | Extended migration: NetBox + Postgres + Redis × 2 + Worker + Housekeeping | H | WP-B-07 | YES |
| WP-B-09 | Extended migration: observability (Grafana, VictoriaMetrics, vmagent, cAdvisor, node-exporter, Uptime Kuma, Topology API, Scraparr) | H | WP-B-07 | YES |
| WP-B-10 | Extended migration: AI/agent layer (LiteLLM, Open WebUI, AnythingLLM, OpenHands, Obot + shims, MCPO, MCP servers, Plex MCP) | H | WP-B-07 | YES |
| WP-B-11 | Extended migration: productivity (OpenProject + Postgres, Nextcloud + Postgres) | M | WP-B-07 | YES |
| WP-B-12 | Extended migration: operator surfaces (Homarr, Homepage, Operator Control Plane, Docker Socket Proxy) | M | WP-B-07 | YES |
| WP-B-13 | Vaultwarden migration | L | WP-B-02 | YES |
| WP-B-14 | seal-vault Transit autounseal verification post-migration | L | WP-B-02 | YES |

**Gate G2 criteria:**
- Vault unsealed on MS-01; AppRoles/policies match; canonical secret round-trip via hash-only verification passes
- arr-stack on MS-01 imports a real test album/episode/movie via hardlink (st_ino matches)
- NetBox UI reachable; Caddy routes serving; agents reporting
- All Mac Mini Docker services have a verified counterpart running on MS-01 Linux VM
- Mac Mini Pro Docker stack still running in parallel

**Risks:**
- R-B-01: Hardlinks don't work over NFS-via-TB → halt; do NOT cutover (would double storage)
- R-B-02: Vault cold-start chicken-and-egg per Finding Z → preserve Transit autounseal; Shamir fallback
- R-B-03: Credential exposure during diagnostics per Finding ZZ → hash-only verification per CLAUDE.md
- R-B-04: Linux VM resource pressure with 60+ containers → if observed, split into "always-on" + "agent runtime" VMs
- R-B-05: Phase 18 Scraparr work disrupted → schedule within WP-B-09

## Phase C — Thunderbolt segment

**Outage impact:** None (additive)

| WP ID | Work package | Effort | Depends on | Critical? |
|---|---|---|---|---|
| WP-C-01 | MS-01 ↔ QNAP TB4 cable + thunderbolt-net config + IP plan | M | G2, P-07, P-10 | YES (within Phase C) |
| WP-C-02 | TB segment DHCP scope on OPNsense | L | WP-C-01 | YES |
| WP-C-03 | Mac Mini Pro ↔ Mac Studio TB5 (already exists) | — | — | — |
| WP-C-04 | Optional: Mac Mini Pro ↔ QNAP TB4 cable | L | extra cable | NO |
| WP-C-05 | mDNS / Bonjour reflection (avahi-daemon or mdns-repeater) | L | WP-C-02 | YES (Continuity) |
| WP-C-06 | Mac dual-homing — keep both LAN and TB initially | L | WP-C-01 | YES |

**Gate G3 criteria:**
- NFS hardlinks proven over TB segment
- AirDrop / AirPlay / Continuity working cross-segment
- LAN/TB failover works in both directions on Macs

## Phase D — Pi monitoring tier

**Outage impact:** brief Zabbix continuity gap

| WP ID | Work package | Effort | Depends on | Critical? |
|---|---|---|---|---|
| WP-D-01 | Pi base provisioning (Pi OS Lite, SSH, hostname, tailscale, Docker Engine) | M | G2, P-08 | YES |
| WP-D-02 | Zabbix server migration: DB+config export/import; agent reconfig | M | WP-D-01 | YES |
| WP-D-03 | Zabbix postgres location decision (Pi or MS-01 Linux VM) | DECISION | WP-D-01 | YES |

**Gate G4 criteria:**
- Zabbix server on Pi reachable from every host
- Metrics flowing for at least 1 hour
- All hosts visible in Zabbix UI
- Mac Mini Docker Zabbix server stopped (cleanup happens in Phase E)

## Phase E — Decommissioning (Finding 9 sub-doctrine)

**Outage impact:** None — decommissioning of already-cutover-from systems
**Doctrine:** "residue is a positive failure mode" — every migration pairs with a retirement

| WP ID | Work package | Effort | Depends on | Critical? |
|---|---|---|---|---|
| WP-E-01 | Mac Mini Docker arr-stack retirement | L | G2 | YES |
| WP-E-02 | Mac Mini Docker Caddy retirement | L | G2 | YES |
| WP-E-03 | Mac Mini Docker Headscale retirement | L | G2 | YES |
| WP-E-04 | Mac Mini Docker Vault retirement (final hash-only verification; AppRole orphan cleanup per Finding 3) | M | G2 | YES (D-17-213 close) |
| WP-E-05 | SMB mount + LaunchDaemon retirement | L | WP-C-01 | YES |
| WP-E-06 | Docker Desktop removal from Mac Mini Pro | L | WP-E-01..04 | YES |
| WP-E-07 | Mac Mini Pro power profile review — sleep enabled, agent-wake validated | M | WP-E-06 | YES |
| WP-E-08 | Protectli FW4B disposition — cold-spare procedure documented | L | G1 | YES |
| WP-E-09 | NetBox + observability + AI/agent + productivity + operator surfaces — all retire from Mac Mini Docker | M | WP-B-08..12 | YES |
| WP-E-10 | Plane CE retirement per ADR-A-018 | M | independent | YES |
| WP-E-11 | Mac Mini Docker Zabbix server retirement | L | G4 | YES |

**Gate G5 criteria:**
- Mac Mini Docker stack: 0 containers running
- Docker Desktop: uninstalled
- SMB mount: unmounted, LaunchDaemon disabled
- Mac Mini Pro: sleeps when idle, wakes cleanly for agent sessions
- Protectli FW4B: cold-spare with documented procedure
- All retired services have entries in `_archive/`

**Risks:**
- R-E-01: Vault AppRole orphans not cleaned up → explicit orphan-detection step in WP-E-04
- R-E-02: SMB mount removal breaks unidentified consumer → audit `~/.platform-logs/` first
- R-E-03: launchd jobs assume Docker Desktop running → audit before WP-E-06

## Phase F — Doctrine + audit

**Outage impact:** None — documentation work

| WP ID | Work package | Effort | Depends on | Critical? |
|---|---|---|---|---|
| WP-F-01 | CLAUDE.md update — Mac Mini "control plane" → "AI orchestration host"; MS-01/Pi added; "M5" stale references removed | M | G5 | YES |
| WP-F-02 | PROJECT_FRAMEWORK.md hardware-reference sweep (157KB; targeted edits) | H | G5 | YES |
| WP-F-03 | Regenerate dependency-graph.md from NetBox post-migration | M | G5 | YES |
| WP-F-04 | Update integration-audit-doctrine.md Finding 22 to narrowed framing | L | G5 | YES |
| WP-F-05 | Update caddy-internal-tls-doctrine.md substrate references | L | G5 | YES |
| WP-F-06 | Update vault-agent-sidecar-pattern.md substrate references | L | G5 | YES |
| WP-F-07 | Update arr-stack-auth-doctrine.md substrate references | L | G5 | YES |
| WP-F-08 | Update download-pipeline-monitoring-doctrine.md (Finding 24 path refs updated) | L | G5 | YES |
| WP-F-09 | Update host-portability.md (Linux VM = Threadripper Linux target realized) | M | G5 | YES |
| WP-F-10 | Retire docs/runbooks/qnap-downloads-mount.md (NFS replaces SMB) | L | G5 | YES |
| WP-F-11 | Update docs/runbooks/add-new-service.md substrate | L | G5 | YES |
| WP-F-12 | Update docs/runbooks/vault-restore-from-backup.md (VM-based Vault) | L | G5 | YES |
| WP-F-13 | Refresh _audit/physical-architecture-2026-05-08.md to post-migration actual state | M | G5 | YES |
| WP-F-14 | Service inventory audit — verify NetBox CMDB matches actual running state | M | G5 | YES |

**Gate G6 criteria:**
- All affected docs updated
- CLAUDE.md no longer references "Mac Mini = control plane"
- Dependency graph regenerated and committed
- Physical-architecture audit reflects post-migration state
- NetBox CMDB matches running services
- Project closeout document authored

## Phase G — Service Registry MVP × OPNsense API integration (FOLLOW-ON)

**Owner:** post-G6 · **Effort:** medium-high · **Trigger:** Phase F complete

| WP ID | Work package | Notes |
|---|---|---|
| WP-G-01 | Extend opnsense_runner.py with declarative DNS module | Per Finding CC + service-registry-mvp.md |
| WP-G-02 | Extend opnsense_runner.py with declarative firewall module | |
| WP-G-03 | Extend opnsense_runner.py with declarative DHCP reservation module | |
| WP-G-04 | Wire registry refresh → OPNsense API automation; drift detection alerts | |
| WP-G-05 | Documentation: new architecture-pattern doc covering registry→network automation | |

## Phase H — NetBox × physical-architecture integration (FOLLOW-ON)

**Owner:** post-G6 · **Effort:** medium

| WP ID | Work package | Notes |
|---|---|---|
| WP-H-01 | NetBox device model populated with physical-architecture-2026-05-08.md fleet | |
| WP-H-02 | Service-to-device parent relationships in NetBox | |
| WP-H-03 | API surface for `physical-architecture` queries | |
| WP-H-04 | Three-substrate drift (Finding 4) reconciliation pass | |

## Phase I — T1-T4 roadmap items (FOLLOW-ON, parallel)

**Owner:** any time; not blocked by hardware migration

| WP ID | Work package | Notes |
|---|---|---|
| WP-I-01 | T1: System Prompt Library deliverable | Locked roadmap T1 priority |
| WP-I-02 | T1: Cisco Provenance Kit installation | Locked roadmap T1 priority |
| WP-I-03 | T2: Gemma 4 vs Qwen3-Coder-Next benchmark on RTX 4070 | Gates on TR1 power-on |
| WP-I-04 | T3: Goose agentic surface (already in motion) | Locked T3 priority |
| WP-I-05 | T4: exo cluster gated on macOS 26.2 both Macs | Upstream-blocked |
| WP-I-06 | Conductor-pattern POC (Sakana RL Conductor architectural insight) | Per `_audit/article-evaluations/sakana-rl-conductor-2026-05-08.md` |

## Risk register (consolidated)

| ID | Risk | Severity | Mitigation | Owner |
|---|---|---|---|---|
| R-A-01 | os-caddy lacks auto-internal-TLS feature parity | M | Pre-flight test; fallback os-haproxy + internal CA | Operator |
| R-A-02 | PCIe passthrough IOMMU groupings | M | VirtIO networking fallback | Operator |
| R-A-03 | WAN config not captured pre-flight | H | Capture before P-02 | Operator |
| R-B-01 | NFS hardlinks don't work over TB | H | Halt; do NOT cutover | Operator |
| R-B-02 | Vault cold-start chicken-and-egg | H | Preserve Transit autounseal; Shamir fallback | Operator |
| R-B-03 | Credential exposure during AI diagnostics | H | Hash-only verification per CLAUDE.md | All sessions |
| R-B-04 | Linux VM resource pressure with 60+ containers | M | Split into two VMs if observed | Operator |
| R-B-05 | Phase 18 Scraparr work disrupted | M | Schedule within WP-B-09 | Operator |
| R-C-01 | TB cable quality | L | Certified 40 Gbps cables only | Operator |
| R-C-02 | Linux thunderbolt-net kernel | L | Modern Proxmox = OK | — |
| R-C-03 | macOS ↔ Linux TB edge cases | L | Iterate | Operator |
| R-D-01 | Pi 5 8GB tight if Zabbix DB co-located | M | Postgres on MS-01 fallback | Operator |
| R-E-01 | Vault AppRole orphans | M | Explicit orphan-detection in WP-E-04 | Operator |
| R-E-02 | SMB mount removal breaks unidentified consumer | M | Audit `~/.platform-logs/` first | Operator |
| R-E-03 | launchd jobs assume Docker Desktop running | M | Audit before WP-E-06 | Operator |
| R-PROJECT-01 | MS-01 single physical point of failure | H | Protectli cold-spare; per circulatory-doctrine, accepted | Operator |
| R-PROJECT-02 | Migration outage window blows past 2 hours | M | Phase A rollback to Protectli; reschedule | Operator |
| R-PROJECT-03 | Hypervisor adds debugging layer | M | Proxmox patterns well-documented | Operator |

## Knowledge items (KI-NNN)

Open questions needing operator decisions:

| ID | Question | Owner |
|---|---|---|
| KI-A | Hypervisor: Proxmox VE vs bare-metal Ubuntu+KVM | Operator (P-09) |
| KI-B | Voice assist tier (potential second mini ~$1000) | Operator (deferred) |
| KI-C | Threadripper #1 power-on cadence | Operator |
| KI-D | Threadripper #2 fix path (Option A: $0-150 X399 + DDR4 ECC UDIMM) | Operator |
| KI-E | TB segment IP range (172.20.20.0/24 proposed) | Operator (P-10) |
| KI-F | Zabbix postgres location (Pi or MS-01) | Operator (WP-D-03) |
| KI-G | NetBox placement (MS-01 Linux VM default) | Operator |
| KI-H | OpenHands/Obot/AnythingLLM resource budget on Linux VM | Operator (post-G2) |
| KI-I | Plex MCP Bridge location | Operator |
| KI-J | Mac dual-homing → TB-only transition timing | Operator (post-Phase C stable) |

## Coordination with in-flight work

The migration cannot disrupt:

- **Phase 18 D-17-46 Scraparr metrics path** — already in flight; must remain operational. Scraparr WP scheduled within WP-B-09.
- **Phase 17 active deliverables** — sweep before Phase E for any deliverable referencing Mac Mini Docker; reschedule or replan as needed.
- **Buildarr daily run** — `com.iap.buildarr-sync` 03:00 launchd job. After migration, runs from MS-01 Linux VM. Reconfigure during WP-B-04.

## Project closeout

Project COMPLETE when Gate G6 passes AND closeout document authored at `docs/phase-NN/PHASE_NN_D-17-211_CLOSEOUT_<date>.md`. Closeout includes:

1. All gate validation evidence (screenshots, command outputs, hash round-trips)
2. Risk register status — which materialized, which were avoided
3. Lessons learned — feed Findings into integration-audit-doctrine.md if new patterns surface
4. Follow-on tracks (G, H, I) status
5. Doctrine-update audit — every WP-F-04..12 doctrine verified updated

## Status

**ACCEPTED PROJECT PLAN** as of 2026-05-08. Execution gated on operator scheduling per phase. Pre-flight items (P-01..11) are immediate operator-side TODOs.

## Cross-references

All architecture artifacts dated 2026-05-08:

1. `architecture-facts/2026-05-08-converged-platform-architecture.md`
2. `architecture-facts/circulatory-doctrine.md`
3. `_audit/physical-architecture-2026-05-08.md`
4. `decision-records/D-17-211-convergence-on-ms01.md`
5. `decision-records/D-17-212-thunderbolt-mesh-topology.md`
6. `decision-records/D-17-213-vault-relocation-to-ms01.md`
7. `runbooks/d-17-211-convergence-migration.md`
8. `architecture-facts/2026-05-08-platform-unified-architecture.md`
9. `architecture-facts/article-intake-protocol.md`
10. `_audit/article-evaluations/sakana-rl-conductor-2026-05-08.md`
11. `runbooks/d-17-211-master-project-plan.md` (this document)

THIS document supersedes any prior implicit project plan and is the canonical execution reference for the rearchitecture.
