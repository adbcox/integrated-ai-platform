# Converged Platform Architecture — Hardware Side

**Date:** 2026-05-08
**Status:** Active doctrine (post-rearchitecture session 2026-05-07/2026-05-08)
**Pairs with:** (forthcoming) software/AI architecture documentation → unification doc
**Originating sessions:** 2026-05-07 flight session + 2026-05-08 architectural rework

## Status of this document

Captures the hardware-side architecture as decided across the 2026-05-07/2026-05-08 architectural rework session. Supersedes any prior implicit doctrine that:

- placed services on Mac Mini Pro Docker as default
- treated QNAP as "storage only"
- treated OPNsense as a separate-hardware appliance from MS-01
- assumed multiple hosts could do the same function as fallback

If this file disagrees with any other hardware/topology doc, this file wins (D#22 doctrine — architecture-facts as canonical).

This is the hardware half of a paired architecture. The software/AI half is already extensively laid out in the repo (master log, exo cluster doctrine, system-prompts tiers, integration audits, local LLM stack T1-T4 prioritization, Goose recipes, Symphony/Spec Kit/OpenShell patterns, Cisco Provenance Kit). The unification document examining both halves as one platform is a forthcoming deliverable.

## The architectural principle: circulatory system

The platform is modeled as a circulatory system, not a redundant-tier system.

- **One organ per function.** Each hardware host owns ONE primary function. No "two brains, two lungs" — distinct organs each doing their own job.
- **Each organ is best at its function.** Specialized hardware in specialized roles, not jack-of-all-trades hosts.
- **All organs needed.** No redundant fallback organs. Resilience comes from per-organ health (good monitoring, real backups, hardware-level redundancy inside each organ — ZFS RAID, ECC RAM, UPS), not from duplicate functions.
- **Two flows traverse the system:**
  - **Blood = information.** DNS, secrets, auth tokens, API calls, metrics, sensor data, file paths, agent commands.
  - **Air = compute.** CPU cycles, GPU tensor passes, ZFS scrubs, model inference, transcoding, container scheduling.
- **Information should reach the right organ for compute without unnecessary detours.** Organ placement and information flow design are inseparable.

This principle is canonical for service placement decisions. New service candidates ask: what domain is this, which organ owns that domain, does the placement keep flows clean? If no organ owns the domain, the converged appliance (MS-01) is the fallback. The detailed principle is in `circulatory-doctrine.md`.

## Fleet inventory (current state)

### Online platform organs

| Organ | Function (single) | Hardware | Network |
|---|---|---|---|
| **Convergence appliance** | OPNsense (firewall/DNS/DHCP/VPN/Caddy/subnet router/automation API) + Linux container tier (arr-stack/Vault/Headscale) | MS-01 (i5-12600H 12c, 32GB DDR5, 2× 10G SFP+, 2× 2.5G RJ45, 2× USB4) running Proxmox VE | WAN + Wired LAN + TB compute mesh |
| **Storage + media-serving** | ZFS, Syncthing, Plex/Jellyfin/Navidrome/Audiobookshelf | QNAP TVS-h674T-i5-32G (i5-12400 6c, 32GB DDR4, native 2× TB4, 2× 2.5GbE) | Wired LAN + TB |
| **Home automation** | HA + Zigbee + ESP32 + integrations | Intel NUC i5 (.141) | Wired LAN |
| **AI orchestration** | Claude Code, Goose, agents, launchd host integrations | Mac Mini M4 Pro 48GB (.145, 3× TB5) | TB compute mesh (LAN dual-home initially) |
| **AI inference** | Ollama, future exo cluster peer | Mac Studio M3 Ultra 96GB (.142, 5× TB5, 10GbE) | TB compute mesh (LAN dual-home initially) |
| **Single-zone monitoring** | Zabbix server | Pi 5 8GB | Wired LAN |
| **L2 switching** | Wired switching only | Ruckus ICX 7150-C12P-2X1G | (medium) |
| **L2 wireless AP** | WiFi AP for wireless clients (uplink to wired) | TP-Link Deco BE95 (AP mode) | (medium) |

### Offline / project hardware

| Hardware | Intended role | Status |
|---|---|---|
| **Threadripper #1 (WRX80)** | CUDA compute (document ingestion at scale, AI image/video enhancement, 3D mesh generation) | Built but offline; intent: power on per workload |
| **Threadripper #2 (Fractal Pop XL Silent)** | Future overflow / TBD function | BLOCKED — 3-way platform incompatibility (TR4 CPU + sTRX4 board + RDIMMs); needs Option A fix (used X399 board + DDR4 ECC UDIMM kit, ~$0-150) |
| **Lian Li Dynamic EVO XL** | Showcase build | NO CPU+motherboard yet (9900X went to Build 4) |
| **MacBook Pro (32GB)** | Travel edge dev | Operational, off-platform |
| **Build 4 — AM5 Daily Driver (9900X)** | Operator daily workstation | Operational, off-platform |
| **Protectli FW4B** | Cold-spare OPNsense (post-migration) | Currently active firewall; becomes cold-spare after migration |

### Spare parts pool

- RTX 4080 (from Skytech strip), location TBD
- 4× 6TB HGST SAS drives, 8× 2TB Dell SAS 7.2K
- Samsung 9100 PRO 2TB + 4TB (PCIe 5.0), Samsung 990 PRO 2TB
- Multiple "older AMD systems" — pool, count/specs not formally inventoried
- "Many" Raspberry Pis — pool for future Pi-class single-zone services

## The convergence appliance (MS-01)

The MS-01 hardware platform runs OPNsense and Linux container services as co-tenants on a hypervisor. This collapses what would otherwise be two organs (network edge + application tier) into ONE organ with a coherent function: bridge all platform L2 segments and host the platform's identity/orchestration-tier services.

### Why MS-01 specifically

The MS-01 was designed by Minisforum as a hypervisor/firewall platform:

- Intel i5-12600H 12-core (4P+8E), 32GB DDR5-5600 — substantial CPU and RAM
- 2× 10G SFP+ (Intel X710 controller, excellent FreeBSD/Linux driver support)
- 2× 2.5G RJ45
- 2× USB4 (TB4-equivalent, 40 Gbps)
- 16-lane PCIe 4.0
- M.2 + U.2 NVMe slots

Router-class hardware that has CPU and RAM left over for application workloads. Treating it as just a Docker host, OR as just a firewall, underutilizes it. Convergence is the architecturally honest use of this hardware.

### Hypervisor: Proxmox VE

Recommended hypervisor for the convergence appliance.

Rationale:

1. **Snapshot/backup story.** OPNsense VM snapshotted before plugin updates. Linux VM snapshotted before Docker/host kernel updates. Restore is one click. Addresses recovery-cascade pattern from Findings W/X/Y in master log.
2. **NIC passthrough well-documented for Proxmox + OPNsense.** SR-IOV or full PCIe passthrough both work; patterns heavily tested in the prosumer community.
3. **Web management UI** for hypervisor-level operations.
4. **ZFS support** as host filesystem — parallel to QNAP's ZFS, different layer.
5. **LXC containers available** alongside VMs for services that fit better as LXC than as Docker-in-a-VM.

**Alternative considered:** bare-metal Ubuntu LTS + KVM/libvirt + OPNsense VM. Slightly better Docker performance (no nested virt). Worse snapshot story. Acceptable but Proxmox preferred.

### VM topology

```
MS-01 Hardware
└── Proxmox VE 8.x (host filesystem: ZFS)
    ├── VM 1: OPNsense (FreeBSD 14)
    │   - 2-4 cores, 4-8GB RAM
    │   - PCIe passthrough: WAN NIC, LAN NIC (SFP+)
    │   - Roles: firewall, Dnsmasq (sole DNS authority — 55+ records), DHCP,
    │            VPN, Caddy (os-caddy plugin),
    │            Tailscale subnet router (os-tailscale plugin),
    │            platform automation API surface (extends opnsense_runner.py)
    │
    └── VM 2: Ubuntu LTS 24.04 + Docker Engine
        - 6-8 cores, 16-20GB RAM
        - Network: bridged via OPNsense (sees LAN as a normal client)
        - Docker services:
            - arr-stack (Sonarr, Radarr, Lidarr, Readarr, Sportarr,
              Bazarr, Cleanuparr, Prowlarr, SABnzbd, FlareSolverr, Buildarr)
            - Vault server (relocated from Mac Mini Pro)
            - Headscale control plane (relocated from Mac Mini Docker)
            - Vault Agent sidecars (per arr-app + per platform service)
            - node_exporter for Zabbix
        - NFS mount of QNAP /share/CACHEDEV2_DATA via TB4 (segment 3)
```

Total: ~10-12 cores, ~24-28GB RAM allocated to VMs. Headroom retained for Proxmox host operations and burst capacity.

## Network topology — three L2 segments converging

```
Internet (Google Fiber)
   │
   ↓ WAN
[MS-01 / OPNsense VM]
   │
   ├──→ Wired LAN segment (Ruckus ICX 7150 1G)
   │     ├── HA NUC (.141)
   │     ├── Pi (Zabbix server, .TBD)
   │     ├── Deco BE95 AP uplink (carries wireless clients to LAN)
   │     ├── Wired IoT devices (any)
   │     └── (optional) Mac Mini Pro / Mac Studio LAN dual-home
   │
   ├──→ TB compute segment (40-120 Gbps, 172.20.20.0/24 proposed)
   │     ├── MS-01 USB4 #1 ──→ QNAP TB4 (NFS path for arr-stack)
   │     └── MS-01 USB4 #2 ──→ Mac Studio TB4
   │                            └── (daisy-chain) Mac Studio TB5 → Mac Mini Pro TB5
   │                            └── (Threadripper #1 via TB5 PCIe card when online)
   │
   └──→ Tailnet segment (logical, via os-tailscale subnet router on OPNsense)
         └── Remote clients (MacBook Pro travel)
              ─ Auth via Headscale (on MS-01 Linux VM)
              ─ Routes back to LAN/TB segments via subnet router
```

### Wireless

Not a separate L3 segment. Deco BE95 in AP mode bridges WiFi clients onto wired LAN. Clients get DHCP/DNS from OPNsense and route through MS-01 like any wired client.

### TB segment specifics

- IP range to be allocated (proposed: 172.20.20.0/24 to avoid conflict with current 192.168.10.0/24 LAN)
- DHCP served by OPNsense Dnsmasq with TB segment as a separate scope
- mDNS/Bonjour reflection between TB and LAN segments via avahi-reflector or mdns-repeater on MS-01 (so AirDrop, AirPlay, Continuity work cross-segment)
- MS-01 acts as L3 router between TB and LAN — this is OPNsense's primary function, NOT a second function (avoids "two brains" violation under the metaphor)
- macOS auto-creates `Thunderbolt Bridge` interface on cable connect

### Mac dual-homing decision

**Initial migration:** Macs keep both LAN ethernet AND TB. Route metrics prefer TB for paths reachable via TB peer, fall back to LAN.

**Post-stability transition:** optionally remove LAN ethernet from Macs once TB segment is proven stable for ALL Mac traffic patterns (DNS, mDNS reflection, Tailscale via TB-routed subnet router, Internet via NAT through OPNsense). Operator decision.

## Information flows (blood)

| Flow | Source | Path | Destination |
|---|---|---|---|
| DNS query | any client | → OPNsense Dnsmasq | response |
| Secret fetch | any service | → Vault Agent → Vault server (Linux VM on MS-01) | secret |
| Tailnet auth | tailnet client | → OPNsense subnet router → Headscale (Linux VM on MS-01) | auth |
| Reverse proxy | any client requesting *.internal | → OPNsense Dnsmasq → OPNsense Caddy | upstream service |
| File access (arr-stack) | arr-app on Linux VM | → NFS over TB4 → QNAP /share | file |
| Media playback | client | → QNAP Plex/Jellyfin → QNAP local filesystem | media stream |
| Sensor data | Zigbee/ESP32 | → HA NUC | automation action |
| Metrics | every host | → Zabbix server on Pi | alerts/dashboards |
| Inference request | agent on Mac Mini Pro | → LAN/TB → Ollama on Mac Studio | tokens |
| Agent commands | operator | → Mac Mini Pro → tools → service registry | execution |
| CUDA dispatch | agent or operator | → LAN/TB → Threadripper #1 (when online) | result |

Every flow has ONE source authority. No duplicate organs claiming the same flow.

## Compute flows (air)

| Compute work | Where | Why there |
|---|---|---|
| Network functions (routing, firewall, DNS, reverse proxy) | OPNsense VM on MS-01 | Network OS specialist |
| Application work (arr-stack, Vault, Headscale) | Linux VM on MS-01 | Real Docker, x86, dedicated |
| AI inference (LLM serving) | Mac Studio M3 Ultra | Apple Silicon ML-optimized, 96GB unified |
| AI orchestration (agentic loops) | Mac Mini Pro M4 | M4 Pro performance for multi-tool agent work |
| CUDA compute (GPU heavy) | Threadripper #1 + RTX 4070 | NVIDIA-only workloads, Linux native |
| Storage compute (ZFS, transcoding) | QNAP i5-12400 | Co-located with storage; native QuickSync |
| Home automation compute | HA NUC i5 | Lightweight, dedicated, integration-hosting |
| Monitoring compute (Zabbix evaluation) | Pi 5 8GB | Light always-on, dedicated single-zone |

No work crosses an unnecessary organ boundary.

## Migration approach

Detailed runbook at `docs/runbooks/d-17-211-convergence-migration.md`. High-level phases:

1. **Phase A — Hypervisor and OPNsense migration**
   - Proxmox VE on MS-01
   - OPNsense VM with NIC passthrough
   - Config export from Protectli FW4B → import to MS-01 VM
   - os-caddy + os-tailscale plugins installed
   - Cutover with maintenance window (1-2 hour expected outage with rollback margin)

2. **Phase B — Application tier VM**
   - Ubuntu LTS VM with Docker
   - Vault server migration Mac Mini Pro → VM
   - Headscale migration Mac Mini Docker → VM
   - arr-stack compose translation Mac Mini Docker → VM

3. **Phase C — TB segment**
   - TB4 cable MS-01 ↔ QNAP
   - TB segment IP plan and DHCP
   - mDNS reflection setup
   - Mac dual-homing

4. **Phase D — Monitoring tier**
   - Zabbix server on Pi

5. **Phase E — Decommissioning** (per Finding 9 sub-doctrine — residue is a positive failure mode)
   - Mac Mini Docker arr-stack/Caddy/Headscale/Vault retirement
   - SMB mount + LaunchDaemon retirement
   - Docker Desktop removal from Mac Mini Pro
   - Mac Mini Pro power profile review (sleep enabled)
   - Protectli FW4B disposition (cold-spare recommended)

6. **Phase F — Doctrine and audit**
   - Finding 22 doctrine narrowed to its empirical evidence
   - Physical architecture audit refresh
   - Service Registry MVP plugged into OPNsense automation API

### Critical risks

1. **MS-01 single point of physical failure.** When MS-01 dies: WAN + LAN routing + DNS + application services + secrets + tailnet auth all die simultaneously. Mitigation: Protectli FW4B cold-spare (powered off, config-synced) for emergency network restoration. No mitigation for application tier — accepted under metaphor.
2. **Migration outage window.** OPNsense move = WAN down briefly. Plan maintenance window with operator presence.
3. **Hypervisor adds a layer.** Proxmox debugging, NIC passthrough quirks, VM resource tuning.
4. **TB networking edge cases.** macOS ↔ Linux TB networking patterns exist but not turnkey; expect some config friction.

## Decision provenance

This architecture was produced through architectural correction across the 2026-05-07 / 2026-05-08 session. Key correction points:

| Wrong assumption | Correction | Source |
|---|---|---|
| QNAP is a low-power NAS | TVS-h674T-i5-32G is i5-12400 / 32GB / native TB4 — server-class | Operator pushback with hardware spec |
| MS-01 is "just" an arr-stack host | MS-01 is router-class hardware (dual 10G SFP+) — convergence appliance | Operator framing on TB underutilization |
| Multiple organs can do same function as fallback | One organ per function, no fallbacks | Operator's circulatory metaphor |
| OPNsense is separate hardware | OPNsense is the OS layer of the MS-01 convergence appliance | Operator's "OS = OPNsense, hardware = MS-01" framing |
| Architectural advice can be given without full hardware inventory | Vacuum decisions are wrong; full fleet must be surveyed first | Operator's repeated pushback through session |
| Mac Mini Pro is the always-on auth/identity host | Mac Mini Pro should sleep when idle; Vault and Headscale relocate | Sleep-vs-always-on contradiction surfaced |

## Open items

1. **Mac dual-homing vs TB-only.** Initially dual-homed; transition to TB-only requires mDNS reflection and Tailscale-via-TB-route validation. Operator decision when ready.
2. **Hypervisor confirmation.** Proxmox VE recommended; bare-metal Ubuntu + KVM acceptable alternative. Operator picks.
3. **Voice assist tier (potential second mini).** Deferred — gated on operator confirming HA voice assist is a near-term goal vs roadmap maybe.
4. **Threadripper #1 power-on cadence.** When CUDA workloads warrant powering it on. TB5 PCIe card procurement gated on this.
5. **Threadripper #2 fix path.** Option A recommended ($0-150 for X399 board + DDR4 ECC UDIMM); function assignment deferred until it can boot.
6. **Pi sourcing.** Existing pool vs $80 Pi 5 8GB purchase. Operator inventory check.
7. **TB segment IP range.** 172.20.20.0/24 proposed; can be any non-conflicting range.
8. **Service registry MVP integration with OPNsense API.** Master log Finding CC; this architecture creates the substrate but the MVP itself is a separate deliverable.
9. **Software/AI architecture integration.** Substantial existing software/AI architecture work in repo; needs inventory pass and unification with this hardware doc.

## Cross-references

- `docs/architecture-facts/circulatory-doctrine.md` — the metaphor as standalone reference
- `docs/_audit/physical-architecture-2026-05-08.md` — fleet state audit (replaces 2026-05-01 stale entries)
- `docs/decision-records/D-17-211-convergence-on-ms01.md` — ADR for convergence pattern
- `docs/decision-records/D-17-212-thunderbolt-mesh-topology.md` — ADR for TB topology
- `docs/decision-records/D-17-213-vault-relocation-to-ms01.md` — ADR for Vault move
- `docs/runbooks/d-17-211-convergence-migration.md` — phased migration runbook
- Master log Findings T, AA, BB, CC — Platform Operational Substrate gap (this architecture is partial closure)
- Master log Finding 22 — narrowed to its evidence by this architecture (cross-host Mac-Mini-Docker → QNAP-host pattern only; intra-MS-01 traffic not subject to it)
- Master log Finding 9 — residue is a positive failure mode; retirement discipline applied to all decommissioning steps in Phase E

## Status

**Active doctrine** as of 2026-05-08. Hardware-side architecture decisions captured. Pairs with software/AI architecture documentation already in repo; unification document forthcoming.
