# D-17-212: Thunderbolt mesh topology — three L2 segments converging at MS-01

## Status

**ACCEPTED** — establish a TB compute segment alongside wired LAN; MS-01 routes between segments
**Decision date:** 2026-05-08
**Decided by:** Operator (Adrian Cox)
**Originating session:** 2026-05-07/2026-05-08 architectural rework
**Decision frame:** Circulatory architecture + operator's "OS/hardware = one system, 3 networks converging" framing

---

## Context

The platform had multiple TB-capable hosts but only ONE TB connection in active use:

**Available TB endpoints:**

- Mac Mini M4 Pro — 3× TB5 (120 Gbps each)
- Mac Studio M3 Ultra — 5× TB5
- QNAP TVS-h674T — 2× TB4 native (40 Gbps; QuTS hero supports thunderbolt-net)
- MS-01 — 2× USB4 (TB4-equivalent, 40 Gbps; Linux supports thunderbolt-net on kernel 5.13+)
- Threadripper #1 — no TB; could add via TB5 PCIe card

**Currently in use:**

- Mac Mini Pro ↔ Mac Studio TB5 link → exo cluster `bridge0` (single-node inference works; distributed broken upstream per Findings U+V)

**The Ruckus ICX 7150 is 1G-only.** Mac Studio's 10GbE en0, QNAP's 2.5GbE — both negotiate down to 1GbE on this switch. Storage and inter-host bandwidth between compute hosts is gated to ~125 MB/s when traversing the switch.

The operator surfaced this underutilization explicitly: "the macs run a service to communucate over TB that is like IP addresses, why do we need the normal IP network for them if they run off the ms o1 and the the other decives mainly iot and wireless run off the ms as well."

## Decision

Establish a Thunderbolt compute segment as an L2 network alongside the wired LAN. MS-01 acts as the L3 router between segments. The architecture is three L2 segments converging at MS-01:

1. **WAN** — Google Fiber via OPNsense WAN interface
2. **Wired LAN** (Ruckus 1G) — HA NUC, Pi monitoring, Deco AP uplink, wired IoT, optional Mac LAN dual-home
3. **TB compute mesh** (40-120 Gbps) — Macs, QNAP, MS-01, Threadripper-1 (when TB5-carded)

Wireless is an L2 extension of the wired LAN via Deco AP in AP mode (not a separate L3 segment).

OPNsense (running on MS-01 per D-17-211) routes between all three L2 segments with shared DHCP/DNS authority via Dnsmasq.

### TB segment specifics

- **IP range:** 172.20.20.0/24 proposed (any non-conflicting range with current 192.168.10.0/24 LAN works)
- **DHCP:** OPNsense Dnsmasq with TB segment as a separate scope
- **DNS:** Same Dnsmasq instance authoritative for both segments; *.internal namespace consistent
- **mDNS reflection:** avahi-reflector or `mdns-repeater` on MS-01 to bridge Bonjour between TB and wired LAN segments (so AirDrop, AirPlay, Continuity work cross-segment)
- **Routing:** OPNsense L3 routes between TB segment and wired LAN segment (and to WAN for Internet egress)
- **Cabling:** macOS auto-creates `Thunderbolt Bridge` interface on cable connect; Linux uses `thunderbolt-net` driver; QNAP uses QuTS hero's Thunderbolt 3 Networking package

### Cable plan (ranked by impact)

1. **MS-01 ↔ QNAP TB4 cable** (~$30) — biggest win; eliminates 1G bottleneck for arr-stack data path. NFS reads/writes go to 5 GB/s ceiling instead of 125 MB/s.
2. **Mac Mini Pro ↔ Mac Studio TB5 cable** — already exists for exo. ✓
3. **Mac Mini Pro ↔ QNAP TB4 cable** (~$30) — backup chain throughput, direct media access from operator's Mac.
4. **Mac Studio ↔ QNAP TB4 cable** (~$30, lower priority) — model storage path if QNAP becomes model store.
5. **Threadripper #1 TB5 PCIe card + cable to QNAP** (~$200 card + $30 cable, gated on TR coming online) — large CUDA jobs reading from QNAP at TB speed.
6. **MS-01 ↔ Mac Mini Pro USB4 cable** (~$30, lower priority) — orchestration channel for tight loops; most agent traffic is small HTTP, low priority.

Initial procurement: $60 for cables #1 and #3 (MS-01 ↔ QNAP, Mac Mini Pro ↔ QNAP).

## Why TB mesh, not LAN-only

Multiple alternatives were considered:

1. **LAN-only with 10G switch upgrade** — would replace Ruckus with a 10G-capable switch (~$500-1000). Solves bandwidth issue but doesn't use the existing TB ports. Higher cost than ~$60 in TB cables.
2. **TB-only Macs (no LAN ethernet to Macs)** — operator's initial proposal. Considered but deferred to "post-stability transition." Initial migration uses dual-homing (TB + LAN) so Macs retain LAN fallback during config validation.
3. **Direct TB without IP networking, just storage protocols** — limits flexibility; IP-over-TB enables the same protocols (NFS, SMB, SSH, etc.) over the high-bandwidth medium.

TB mesh wins because:

- Hardware already paid for (TB ports exist on all relevant hosts)
- ~$60 in cables is far less than $500+ switch upgrade
- Each TB connection is independent — no single shared switch fabric
- macOS, Linux, and QuTS hero all support thunderbolt-net natively
- 40 Gbps direct beats any switch-mediated path on this fleet today

## Why dual-homed Macs initially (not TB-only)

The operator proposed TB-only Macs (eliminating LAN ethernet from Macs entirely, routing all Mac traffic through MS-01 via TB). Architecturally clean under the convergence framing, but operationally:

- mDNS reflection complexity for Apple Continuity (AirDrop, AirPlay, HomePod handoff) — requires explicit reflector config
- Single point of failure: MS-01 down = no Internet for Macs (no Anthropic API, no Claude Code, no model downloads)
- Tailscale path traverses MS-01 → OPNsense (two hops instead of one) — small overhead

**Initial decision: dual-homed.** Macs keep both LAN ethernet AND TB. Route metrics prefer TB for paths reachable via TB peer, fall back to LAN for everything else.

**Post-stability transition (operator-decided):** once TB segment is proven stable for ALL Mac traffic patterns (DNS, mDNS reflection, Tailscale via subnet router, Internet via NAT), Mac LAN ethernet may be removed.

## Consequences

### Positive

- arr-stack on MS-01 reads QNAP at 40 Gbps via TB4 instead of 1G via switch (40x improvement for I/O-bound operations like full library scans, large file transfers)
- exo cluster TB5 link (Mac Mini Pro ↔ Mac Studio) preserved
- Backup chain (Mac Mini Pro → Restic → MinIO on QNAP) goes from 1G to TB4 (40x throughput improvement)
- Operator's "3 networks converging" framing realized — MS-01 IS the convergence point with WAN, wired LAN, and TB segments
- TB ports on all hosts now utilized; no underutilized hardware

### Negative / accepted

- mDNS reflection adds config item — Continuity features require explicit reflector setup
- TB cable quality matters at 40+ Gbps; cheap cables may underperform
- Linux thunderbolt-net is kernel-version sensitive (5.13+); MS-01 host kernel must be modern enough
- macOS ↔ QNAP TB networking has fewer documented patterns than Mac ↔ Mac TB; expect some config friction

### Neutral

- IP addresses on TB segment are new (172.20.20.0/24); some service configs may need to handle dual-homed source addresses

## Implementation

Detailed steps in `runbooks/d-17-211-convergence-migration.md` Phase C. Bounded effort: ~4-8 hours including TB cable plan, IP assignments, DHCP scope config, mDNS reflector, route metric tuning, validation.

## Cross-references

- `architecture-facts/2026-05-08-converged-platform-architecture.md` — master architecture
- `architecture-facts/circulatory-doctrine.md` — placement principle
- `decision-records/D-17-211-convergence-on-ms01.md` — convergence ADR (parent)
- `runbooks/d-17-211-convergence-migration.md` — migration runbook
- Master log Findings U+V — exo distributed inference upstream blocks (TB5 link still useful for cluster substrate even though distributed inference not operational)
