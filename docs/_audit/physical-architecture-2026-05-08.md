# Physical architecture audit — 2026-05-08

**Date:** 2026-05-08
**Status:** Audit snapshot (replaces stale entries in `physical-architecture-2026-05-01.md`)
**Origin:** 2026-05-07/2026-05-08 architectural rework session
**Pairs with:** `architecture-facts/2026-05-08-converged-platform-architecture.md`

## Why this audit

The 2026-05-01 audit captured a 4-host platform view (Mac Mini, Mac Studio, QNAP, Threadripper-1) that was incomplete. The 2026-05-07/08 architectural rework session surfaced the broader fleet (MS-01, Threadripper #2, Lian Li EVO XL, Build 4 daily driver, multiple Pis, multiple AMD systems, Protectli FW4B). This audit replaces the prior with the fuller fleet view and assigns each host a function per the circulatory architecture (`circulatory-doctrine.md`).

This is a snapshot, not a polled audit. Online/offline status reflects operator-reported state at the time of the rework session; live state may have changed.

## Method

This audit synthesizes from:

- `LocalAIConfig/HOME_SYSTEM_INVENTORY.md` (operator-maintained inventory, captured 2026-05-07)
- `LocalAIConfig/inventory/current_host_inventory.txt`
- `Downloads/full-system-inventory.md`
- `Downloads/build_inventory_v3.md` (operator's build inventory v3 from Gmail purchase records, 2026-04-28)
- `repo/config/network_inventory.yaml` (some entries stale — Brocade vs Ruckus, .113/.202 outdated)
- `repo/docs/_audit/physical-architecture-2026-05-01.md` (prior audit)
- Operator's verbal corrections during 2026-05-07/08 rework session

Conflicts resolved in favor of: operator memory > HOME_SYSTEM_INVENTORY.md > build_inventory_v3.md > prior audit > network_inventory.yaml (most-stale-first).

## Online platform organs (powered, operating)

### Network edge / convergence appliance

**Hardware:** Currently Protectli FW4B (Atom-class fanless mini-PC) at .1
**Future state (post-D-17-211):** MINISFORUM MS-01 at TBD IP, running Proxmox VE
**Function:** Firewall, DNS (Dnsmasq sole authority — 55+ records), DHCP, VPN, Caddy reverse proxy, Tailscale subnet router, platform automation API, plus (post-migration) Linux container tier hosting arr-stack/Vault/Headscale
**API access:** OPNsense API key/secret stored at Vault `secret/data/opnsense/api`; consumed by `repo/opnsense_runner.py` and `repo/bin/test_seedbox_connection.py` and homepage dashboard widget

### Storage + media-serving

**Hardware:** QNAP TVS-h674T-i5-32G-US (.201)

- Intel 12th-gen Core i5-12400 6-core
- 32GB DDR4
- Native 2× TB4 ports (40 Gbps each)
- 2× 2.5GbE
- 6-bay ZFS via QuTS hero
- HBA card support (currently has SAS HBA per build inventory)

**Function:** ZFS storage pool, Syncthing receiver from seedbox, native QNAP Plex/Jellyfin/Navidrome/Audiobookshelf via Container Station and QPKG packages

### Home automation

**Hardware:** Intel NUC i5 (.141, exact model not formally inventoried)
**Function:** Home Assistant canonical instance per D-17-34, Zigbee2MQTT or ZHA for Zigbee sensors, ESP32 device integration, future IKEA MYGGSPRAY pilot

### AI orchestration

**Hardware:** Mac Mini M4 Pro 48GB (.145)

- 3× TB5 ports
- 1× GbE en0
- macOS 26.4.1
- Tailscale: 100.64.0.1 (currently subnet exit; relocates to MS-01 OPNsense post-D-17-212)

**Function:** Claude Code, Goose, agent runtime, Aider/OpenCode/Continue, Vault server (CURRENT — relocates to MS-01 Linux VM post-D-17-213), various launchd host integrations
**Post-D-17-211 function:** Pure AI orchestration host; no Vault, no Headscale, no Docker Desktop, no arr-stack. Sleeps when idle.

### AI inference

**Hardware:** Mac Studio M3 Ultra 96GB (.142)

- 5× TB5 ports
- 10GbE en0 (currently negotiated to 1G via Ruckus)
- macOS 26.4.1

**Function:** Ollama 7-model serving; future exo cluster peer (currently blocked at distributed inference layer per Findings U+V — single-node inference operational)

### Single-zone monitoring

**Hardware:** Pi 5 8GB (TBD — currently Zabbix server runs on Mac Mini Docker; relocates per D-17-211 Phase D)
**Function:** Zabbix server, single-zone always-on monitoring per "we ran enterprise monitoring on a Pi" doctrine

### Network infrastructure (medium, not organs)

- **Ruckus ICX 7150-C12P-2X1G PoE+ switch** (.2) — 12× 1GbE PoE + 2× 1GbE uplink. **Note: 1GbE only**, no 10G ports. The 10G en0 on Mac Studio and 2.5GbE on QNAP both negotiate down to 1GbE on this switch. TB segments bypass this limitation.
- **TP-Link Deco BE95** (.3) — WiFi mesh AP in AP mode (not router). Wired uplink to Ruckus. WiFi clients get DHCP/DNS from OPNsense.

## Offline / project hardware

### Threadripper #1 (WRX80 chassis)

**Components:**

- AMD Threadripper Pro CPU (24-core class per audit)
- WRX80 motherboard
- RTX 4070 12GB
- 64GB DDR4 ECC
- Intel X550-AT2 10GbE NIC
- (storage TBD)

**Status:** Built, currently OFFLINE
**Intended function:** CUDA compute (document ingestion at scale, AI image/video enhancement/upscaling/tagging/facial recognition, 3D model generation per InstantMesh + TripoSR pipeline)
**Power-on cadence:** On-demand per CUDA workload; not always-on
**Future TB integration:** TB5 PCIe add-in card when CUDA workloads warrant; connects via TB to Mac Mini Pro for low-latency dispatch

### Threadripper #2 (Fractal Pop XL Silent chassis)

**Components per build_inventory_v3.md:**

- AMD TR 2970WX (TR4 socket)
- ASRock TRX40 Creator (sTRX4 socket — INCOMPATIBLE with 2970WX)
- 8× Micron PC4-2666V-RD1 RDIMMs ($165 — INCOMPATIBLE with TRX40 board)
- HP 8-bay SAS backplane
- 8× 2TB Dell SAS 12Gbps drives = 16TB raw
- LSI 9300-8i HBA + 9300-16i HBA
- 10Gtek SFP+ DAC cables

**Status:** BLOCKED — three-way platform incompatibility prevents boot
**Recommended fix:** Option A per build_inventory_v3.md (used X399 board + DDR4 ECC UDIMM kit, ~$0-150 net cost)
**Function assignment:** DEFERRED until it can boot. Future overflow / TBD function under circulatory architecture.

### Lian Li Dynamic EVO XL (showcase build)

**Components:**

- Full custom water loop showcase
- Case + cooling installed
- NO CPU+motherboard yet (originally earmarked for 9900X which is now in Build 4)

**Status:** Showcase chassis, not currently a platform candidate
**Function assignment:** None until completed

### MINISFORUM MS-01

**Components per build_inventory_v3.md (Build #3):**

- Intel i5-12600H 12-core (4P+8E)
- 32GB DDR5-5600 SODIMM (DDR4 was first ordered erroneously; DDR5 re-ordered Dec 31)
- 2× 10G SFP+ (Intel X710 controller)
- 2× 2.5G RJ45
- 2× USB4 (TB4-equivalent, 40 Gbps)
- 16-lane PCIe 4.0
- M.2 + U.2 NVMe slots

**Status:** Built; operational state needs verification (BIOS, RAM detection, current OS) before D-17-211 Phase A begins
**Function assignment:** Convergence appliance (per D-17-211)

### MacBook Pro (32GB)

**Function:** Travel / edge dev (operator's mobile workstation)
**Status:** Operational, off-platform (used for travel sessions including this one)

### Build 4 — AM5 Daily Driver

**Components:**

- Ryzen 9 9900X (12-core Zen 5; pulled from Skytech Omega 2)
- MSI MAG X670E Tomahawk WiFi
- 64GB + 32GB DDR5
- (other components TBD)

**Status:** Operational, off-platform
**Function:** Operator's daily workstation (not a platform organ)

### Protectli FW4B

**Status:** Currently the active firewall (.1)
**Post-D-17-211 status:** Cold-spare for OPNsense
**Function (post-migration):** Emergency backup for MS-01 OPNsense failure; powered off, config-synced from Proxmox snapshot of OPNsense VM

## Spare parts pool

Not formally inventoried; operator-known. Highlights from build inventory and conversation:

- RTX 4080 (from Skytech Omega 2 strip), location TBD
- 4× 6TB HGST SAS drives
- Samsung 9100 PRO 2TB + 4TB (PCIe 5.0)
- Samsung 990 PRO 2TB
- Multiple "older AMD systems" — count and specs not formally inventoried; pool for future workloads
- "Many" Raspberry Pis — pool for future Pi-class single-zone services (Zabbix server is the immediate consumer; future single-zone services will draw from this pool)

## Network corrections from prior audit

**Items in `repo/config/network_inventory.yaml` known stale:**

| Stale entry | Current reality |
|---|---|
| `Brocade Switch ICX 6450-24` at .2 | Actually Ruckus ICX 7150-C12P-2X1G (Ruckus acquired Brocade switching; common confusion) |
| `Mac Mini M5` at .113 | Actually Mac Mini M4 Pro at .145 |
| `Mac Studio M3` at .202 | Actually Mac Studio M3 Ultra at .142 |

**Items in `physical-architecture-2026-05-01.md` known stale:**

- 4-host platform view (missing MS-01, Threadripper #2, Pi pool, AMD systems, Build 4)
- QNAP listed as "10GbE" in the 2026-05-01 table — actually 2.5GbE per current TVS-h674T spec; 10G claim was aspirational
- Threadripper #1 listed as "OFFLINE at probe time" with no role assignment — now assigned CUDA compute role

## ARP / network nodes not yet identified

The 2026-05-01 audit flagged 20 unidentified active LAN nodes (.101, .104, .105, .111, .113, .122-127, .133-136, .144-148, .152, .184-185, .193-194). These remain operator-known but not formally inventoried. Out of scope for this audit; tracked for future formalization if any need to enter the architecture.

## Status

**Audit snapshot complete** as of 2026-05-08. Pairs with `architecture-facts/2026-05-08-converged-platform-architecture.md` as the canonical fleet reference. Subsequent audits should refresh this on a defined cadence (post-deliverable phase boundary, or quarterly).

## Cross-references

- `architecture-facts/2026-05-08-converged-platform-architecture.md` — master architecture
- `architecture-facts/circulatory-doctrine.md` — placement principle
- `decision-records/D-17-211-convergence-on-ms01.md` — convergence ADR
- `decision-records/D-17-212-thunderbolt-mesh-topology.md` — TB topology ADR
- `decision-records/D-17-213-vault-relocation-to-ms01.md` — Vault relocation ADR
- `runbooks/d-17-211-convergence-migration.md` — migration runbook
- `_audit/physical-architecture-2026-05-01.md` — prior audit (superseded by this one)
- `LocalAIConfig/HOME_SYSTEM_INVENTORY.md` — operator-maintained inventory source
- `Downloads/build_inventory_v3.md` — operator's build inventory v3 source
