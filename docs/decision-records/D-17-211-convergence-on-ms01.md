# D-17-211: Convergence of network edge and application tier on MS-01

## Status

**ACCEPTED** — converge OPNsense (network OS) and Linux container tier (arr-stack/Vault/Headscale) onto MS-01 hardware via Proxmox VE hypervisor

**Decision date:** 2026-05-08
**Decided by:** Operator (Adrian Cox)
**Originating session:** 2026-05-07 flight session + 2026-05-08 architectural rework
**Decision frame:** Circulatory architecture (`architecture-facts/circulatory-doctrine.md`)

---

## Context

Prior architecture had:

- **OPNsense on Protectli FW4B** at .1 — Atom-class fanless firewall
- **arr-stack on Mac Mini Pro Docker** — running 11 containers + Vault Agent sidecars
- **Vault server on Mac Mini Pro** — identity infra, conflicting with sleep-when-idle goal
- **Headscale on Mac Mini Pro Docker** — fragile because Mac Mini sleeps
- **Caddy on Mac Mini Pro Docker** — reverse proxy for 19+ *.internal domains
- **MS-01 onboarded but underutilized** — operator bought it on advice, was unsure why a server-class spec was needed; original framing was "arr-stack host"

This produced multiple architectural problems:

1. **Mac Mini Pro overloaded.** Per master log Finding T (2026-05-02 OS upgrade incident), the orchestration host was running so much infrastructure that routine OS upgrades cascaded into platform-wide outages.
2. **Always-on requirement vs sleep-when-idle goal.** Vault and Headscale must be always-on; Mac Mini Pro was the host but should sleep. Contradiction surfaced during the 2026-05-08 review.
3. **MS-01 underutilized.** Router-class hardware (i5-12600H 12-core, 32GB DDR5, 2× 10G SFP+, 2× USB4, 16-lane PCIe) was being treated as a Docker box.
4. **Finding 22 over-generalization.** The doctrine "QNAP is the NAS, not the application tier" was operator-derived from empirical Mac-Mini-Docker-bridge → QNAP-host filter behavior. The cross-host split was the actual failure pattern; the doctrine generalized too far.
5. **Two separate boxes for what is logically one organ.** OPNsense (network edge) on Protectli, Linux containers (application tier) on Mac Mini Pro — but both serve "things that bridge zones," and both were always-on requirements with sleep-incompatible workloads on Mac Mini Pro.

The operator's reframe — "OPNsense = OS, MS-01 = hardware. it is one system converging 3 networks TB, wired, wireless" — collapses what would otherwise be two organs into ONE convergence appliance.

## Decision

**Run OPNsense and Linux Docker container services as co-tenants on MS-01 via Proxmox VE hypervisor.** The MS-01 hardware platform is the converged appliance bridging WAN, wired LAN, TB compute mesh, and (logically) tailnet. It hosts:

- **OPNsense VM:** firewall, Dnsmasq DNS authority, DHCP, VPN, Caddy reverse proxy (`os-caddy` plugin), Tailscale subnet router (`os-tailscale` plugin), platform automation API surface
- **Linux VM (Ubuntu LTS + Docker):** arr-stack (11 services), Vault server, Headscale control plane, Vault Agent sidecars

The Protectli FW4B is retired from active duty and becomes a cold-spare (powered off, config-synced from Proxmox snapshot of OPNsense VM) for emergency network restoration if MS-01 dies.

## Why MS-01 specifically (not "buy a new mini" or "QNAP Container Station")

Multiple alternatives were considered and withdrawn during the rework session:

1. **arr-stack to QNAP Container Station** — withdrawn because Finding 22's empirical evidence narrowed under careful re-reading; consolidating on QNAP Container Station was viable but MS-01 has more CPU (12c vs 6c), faster RAM (DDR5 vs DDR4), and dedicated host (no NAS workload competition).
2. **OrbStack on Mac Mini Pro + NFS to QNAP** — withdrawn because it loaded an already-overloaded orchestration host with another VM doing heavy I/O.
3. **Dedicated cheap Mac mini (~$1000) for media tier** — withdrawn because MS-01 was already-purchased and more capable than a base M4 mini for this work; spending on new hardware to do what MS-01 was bought for was wasteful.
4. **Network edge stays on Protectli + Linux tier on MS-01 (separate organs)** — withdrawn because the operator's "OS vs hardware" reframe pointed out these were one logical system; MS-01 has the hardware to host both.

MS-01 wins on these concrete points relative to alternatives:

- More CPU than QNAP's i5-12400 (12 cores vs 6 cores; 4P+8E architecture)
- Faster RAM (DDR5-5600 vs DDR4)
- Dedicated host (no contention with QNAP's ZFS scrubs, snapshot work, native media servers)
- Native Linux Docker (no Container Station packaging/version drift, no Finding 22 ambiguity for intra-host traffic)
- Already paid for; using it costs nothing additional
- Router-class NICs (2× 10G SFP+, 2× 2.5G, 2× USB4) — designed for this role
- Hypervisor pattern is well-trodden for MS-01 in the prosumer/homelab community

## Why Proxmox VE specifically

Proxmox VE recommended over alternatives:

1. **Snapshot/backup story** — addresses recovery-cascade pattern from Findings W/X/Y in master log (the 2026-05-02 OS upgrade incident chain)
2. **NIC passthrough well-documented** for Proxmox + OPNsense (SR-IOV or full PCIe passthrough)
3. **Web management UI** for hypervisor-level operations
4. **ZFS support** as host filesystem
5. **LXC containers** available alongside VMs

Alternatives considered:

- **Bare-metal Ubuntu LTS + KVM/libvirt + OPNsense VM** — slightly better Docker performance, worse snapshot story; acceptable but Proxmox preferred
- **OPNsense as host with bhyve VMs** — limited Linux tooling, not recommended
- **OPNsense as host with `os-docker` plugin** — no such plugin exists in the OPNsense ecosystem

## Consequences

### Positive

- **One organ per function** (per circulatory doctrine). MS-01 hosts the convergence function: bridges all L2 segments, hosts identity infra, hosts cross-domain application services.
- **Mac Mini Pro freed of always-on duties.** Sleeps when idle; pure AI orchestration host. Closes the sleep-vs-always-on contradiction.
- **MS-01 used at the level its hardware was designed for.** No more underutilization.
- **Service registry MVP (Finding CC) integration substrate.** OPNsense API automation surface now under operator control via existing `opnsense_runner.py`; new modules for declarative DNS/firewall/DHCP can be authored and consumed by Plane CE / Goose recipes.
- **TB segment becomes possible.** USB4 ports on MS-01 are available for direct TB connections to QNAP, Mac Studio, Mac Mini Pro, Threadripper-1 (when TB5-carded).

### Negative / accepted risks

- **Single-physical-point-of-failure for the entire platform.** When MS-01 dies: WAN + LAN routing + DNS + application services + secrets + tailnet auth all fail simultaneously. Mitigation: cold-spare Protectli FW4B (powered off, config-synced) for emergency network restoration. No mitigation for application tier — accepted under circulatory metaphor (no fallback organs; resilience is per-organ health).
- **Migration outage window.** Cutover from Protectli to MS-01 OPNsense = WAN down briefly. Plan maintenance window with operator presence (1-2 hours expected).
- **Hypervisor adds a layer.** Proxmox debugging, NIC passthrough quirks, VM resource tuning are real ops concerns.
- **Resource consumption on MS-01.** ~10-12 cores allocated to VMs (out of 12 total), ~24-28GB RAM allocated (out of 32 total). Headroom is tight; new heavy services on MS-01 may require reallocation.

## Implementation

Detailed migration plan in `docs/runbooks/d-17-211-convergence-migration.md`. High-level phases: A (hypervisor + OPNsense migration), B (Linux VM + service migration), C (TB segment), D (monitoring on Pi), E (decommissioning per Finding 9 sub-doctrine), F (doctrine + audit refresh).

## Decision provenance

Multiple architectural pivots were taken in this session before the convergence answer landed:

1. arr-stack → QNAP Container Station (withdrawn after Finding 22 review)
2. arr-stack → OrbStack on Mac Mini Pro (withdrawn — overload pattern)
3. arr-stack → dedicated cheap mini purchase (withdrawn — MS-01 already capable)
4. arr-stack → MS-01 as separate organ from OPNsense (withdrawn — operator OS/hardware reframe)
5. Final: arr-stack + OPNsense → MS-01 as one converged organ ✓

The convergence answer required the operator's circulatory metaphor and OS/hardware reframe to surface. AI advice prior to those reframes was producing "two brains, two lungs" architectures by default.

## Cross-references

- `architecture-facts/2026-05-08-converged-platform-architecture.md` — master architecture
- `architecture-facts/circulatory-doctrine.md` — placement principle
- `_audit/physical-architecture-2026-05-08.md` — fleet state audit
- `decision-records/D-17-212-thunderbolt-mesh-topology.md` — TB topology ADR
- `decision-records/D-17-213-vault-relocation-to-ms01.md` — Vault relocation ADR
- `runbooks/d-17-211-convergence-migration.md` — migration runbook
- Master log Finding T — asset-management substrate gap (this decision partially addresses)
- Master log Finding 22 — narrowed by this decision
- Master log Finding CC — service registry gap (substrate for MVP enabled by this)
