# ADR-A-019 — Container runtime per host: Colima on Mac Mini production, OrbStack on MacBook roaming workstation

**Status:** Accepted
**Date:** 2026-05-09
**Source:** Tokyo IAP travel session — operator-driven correction after assistant cited ADR-A-003 / Colima three times in succession without checking for unwritten supersession on the MacBook scope. Decision codified to prevent recurrence.

## Context

ADR-A-003 (2026-04-27) established Colima as the container runtime for the Mac Mini production stack. KI-002 (2026-04-27) documented Colima-specific operational quirks: Unix socket bind-mount unsupported across the VM boundary, virtiofs UID mapping with macOS-owned bind-mounts, 8GB→16GB memory tuning required for 30+ containers. That decision remains correct for the Mac Mini's existing compose-based ~30+-container production stack and is **not changed by this ADR**.

The MacBook Pro (roaming workstation, Block 3 parity peer per `docs/architecture-facts/host-portability.md`) was historically running Docker Desktop. Docker Desktop is being removed across the workstation: it is proprietary, slow on macOS, heavy at idle, and Docker Inc. demonstrated willingness to retro-charge developer accounts in 2021. On the MacBook the operator wanted a per-MCP-instance isolation model — each MCP server in its own runtime — that simplifies the three-layer nesting (macOS host → Linux VM → Docker engine → containers) that Docker Desktop and Colima both impose on macOS.

Apple Container framework (`apple/container`, Apache 2.0, macOS 26+) was evaluated as the architecturally ideal match: one-VM-per-container on Apple's Virtualization.framework, no daemon, no shared Linux VM. As of v0.11.0 (March 2026), Apple Container lacks native Docker Compose support, which would force a `docker compose` → `container run × N` migration of any compose-based work on the MacBook.

OrbStack was evaluated as a pragmatic alternative: 2-5x faster than Docker Desktop, ~0.1 GB idle memory vs Docker Desktop's 2 GB+, full `docker` CLI and `docker-compose` compatibility, and Linux VM management alongside containers (each its own instance). OrbStack is **not strict OSS** — it is proprietary, free for personal use, paid for commercial.

## Decision

Container runtime is decided **per-host**, not platform-wide:

| Host | Runtime | Status |
|---|---|---|
| Mac Mini M4 Pro production | Colima | Per ADR-A-003. No change. |
| MacBook Pro roaming workstation | **OrbStack** | This ADR. Replaces Docker Desktop. |
| MS-01 Linux VM (Phase B target) | Native Linux Docker engine | No macOS container runtime needed. |
| Threadripper (when online) | Native Linux Docker engine | Per `docs/_audit/physical-architecture-2026-05-01.md` §2.1. |

OrbStack on the MacBook is the **second deliberate exception** to the platform's "100% open source self-hosted" stack ethos. The first is Proton Mail (ratified earlier). All other stack components remain OSS.

## Rationale for the OSS exception

Accepted on the same reasoning pattern as the Proton Mail exception:

1. **Personal use is free** under OrbStack's licensing. The MacBook is a personal AI workstation and qualifies.
2. **OrbStack uniquely delivers the per-VM-instance simplification** the operator requires for MCP isolation, **without the Compose-incompatibility cost** of Apple Container as of v0.11.0.
3. **Material UX gain on a roaming laptop:** ~2-5x faster than Docker Desktop, ~20x less idle memory, materially better battery life. Travel-relevant.
4. **Standard Docker workloads remain portable:** images (OCI), compose files, volumes, networks — all standard. An exit from OrbStack is a runtime swap, not a workload rewrite.
5. **Proprietary-software risk is bounded:** existing installs continue working if Orbital Labs disappears or changes terms; only future updates are at risk.

## Consequences

- The 100% OSS ethos has two acknowledged exceptions: Proton Mail (cloud email, ratified) and OrbStack (MacBook container runtime, this ADR). All other stack components remain OSS.
- License-tier change risk: Orbital Labs may shift "personal use" definition or pricing. Mitigated by portability of standard Docker workloads — exit cost is bounded.
- Vendor disappearance risk: Orbital Labs is a small company. Mitigated by (a) existing installs continue working without updates, (b) standard workloads migrate to Apple Container, Colima, or Podman Desktop on short notice.
- Closed-source means the operator cannot audit OrbStack code, fix bugs, or fork. Trust is delegated to Orbital Labs' security practices.
- **Avoid OrbStack-specific features** that increase migration cost: `*.orb.local` domain auto-resolution, bidirectional macOS↔container file bridge magic paths, OrbStack-specific k8s integration. Use only when the UX benefit clearly outweighs the lock-in cost. Standard Docker patterns are preferred.
- Compose-based dev → production handoff is preserved: the MacBook can run the same compose files as the Mac Mini production stack (modulo any Linux/macOS path differences).
- Per-host runtime divergence is now policy. Any new host added to the platform requires an explicit runtime decision — not assumed inheritance from another host.

## Alternatives considered

| Alternative | Verdict |
|---|---|
| **Docker Desktop on MacBook** (status quo) | Rejected. Heavier, slower, Docker Inc. license-change history (2021), no per-MCP isolation. |
| **Colima on MacBook** (mirror Mac Mini) | Rejected. Maintains the three-layer nesting the operator wants to eliminate; KI-002 socket-mount and virtiofs-UID quirks carry over to a roaming laptop where troubleshooting is harder. |
| **Apple Container on MacBook** | Architecturally cleanest match for per-MCP isolation. **Deferred** — no Docker Compose support as of v0.11.0 (March 2026). Migration would require rewriting every `docker compose` invocation as `container run × N`. Re-evaluate in a future ADR when Apple Container ships stable Compose support; OrbStack → Apple Container is a viable future migration path. |
| **Podman Desktop on MacBook** | Rejected. OSS-pure but architecturally similar to Colima (Lima-style VM under the hood); does not deliver the simplification target the operator described. |
| **Run all MacBook Docker workloads remotely on MS-01 / Mac Mini** | Rejected. MacBook must retain full functionality off-network (existing requirement per Control Center implementation plan: on-network / Headscale VPN / fully offline). Remote-only Docker fails the offline mode. |

## Future re-evaluation triggers

Review this ADR if any of the following occurs:

1. Apple Container ships native Docker Compose support at stable status. **Likely supersedes this ADR** — OrbStack → Apple Container migration becomes the cleaner path (returns to OSS purity, removes vendor risk).
2. OrbStack license terms change to disadvantage personal use (e.g., narrower "personal use" definition, retro-charge to existing free users).
3. Orbital Labs is acquired, ceases operations, or materially changes product direction.
4. A material security incident in OrbStack that the closed-source nature prevents independent audit of.

## Related

- ADR-A-003 — Monitoring stack: Zabbix + TimescaleDB + Grafana + VictoriaMetrics (Colima Mac Mini production reference; not superseded by this ADR)
- KI-002 — mcp-docker MCP server runtime (Colima quirks; applies to Mac Mini, not MacBook on OrbStack)
- `docs/architecture-facts/host-portability.md` — heterogeneous architecture portability (per-host config pattern this ADR extends to runtime selection)
- `docs/_audit/physical-architecture-2026-05-01.md` §2.1 — Threadripper future role (Linux-native runtime)
- (future) Track 2 foundation install spec — applies this ADR to the MacBook setup
