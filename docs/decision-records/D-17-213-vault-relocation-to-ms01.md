# D-17-213: Vault server relocation Mac Mini Pro → MS-01 Linux VM

## Status

**ACCEPTED** — Vault server moves from Mac Mini Pro macOS host to Linux VM on MS-01
**Decision date:** 2026-05-08
**Decided by:** Operator (Adrian Cox)
**Originating session:** 2026-05-07/2026-05-08 architectural rework
**Decision frame:** Circulatory architecture — sleep-vs-always-on contradiction resolution

---

## Context

Vault server has historically run as a Docker container on Mac Mini Pro (.145), originally placed there as part of the platform's general "Mac Mini = control plane" framing. This produced two contradictions:

1. **Sleep-vs-always-on.** The 2026-05-08 architectural rework concluded Mac Mini Pro should sleep when idle (its function is AI orchestration; it does not need to run 24/7). Vault must be always-on (every secret-consuming service depends on it). One host can't satisfy both requirements.
2. **macOS Docker Desktop dependence.** Vault on Mac Mini ran via Docker Desktop, which has surfaced repeated friction throughout the platform's life (per master log Findings W/X/Y/Z/ZZ — recovery cascade). Real Linux Docker is more durable.

A separate concern from master log Finding Z is whether Vault should be retired entirely as the credential store. That question is separate from this ADR — Finding Z's "Vault retirement" review is its own deliverable. This ADR scopes only Vault's PLACEMENT, taking Vault-as-credential-store as given.

## Decision

Relocate Vault server from Mac Mini Pro to the Linux VM running on MS-01 (per D-17-211). The Linux VM hosts both Vault server and the arr-stack containers that consume Vault Agent sidecars; co-location simplifies the consumption path (sidecar → local network → Vault, rather than sidecar → cross-host network → Vault).

The Mac Mini Pro retains:

- Claude Code, Goose, agent runtime
- Various launchd host integrations (Strava sync, vault-audit-rotate, etc.)
- Tailscale client (no longer subnet router — that role moves to OPNsense per D-17-212)

The Mac Mini Pro loses:

- Vault server (this ADR)
- Headscale control plane (separate decision; same migration target)
- Caddy reverse proxy (separate decision; moves to OPNsense `os-caddy`)
- arr-stack Docker containers (separate decision; same migration target as Vault)
- Docker Desktop (decommissioned entirely)

## Consequences

### Positive

- **Mac Mini Pro can sleep when idle.** Closes the sleep-vs-always-on contradiction. Power savings, longer hardware life, less heat in carriage house.
- **Real Linux Docker for Vault.** No Docker Desktop, no macOS-VM friction. Native cgroups, native networking, kernel-level integration.
- **Co-located consumers.** arr-stack Vault Agent sidecars on Linux VM connect to Vault server on same VM (or via Docker network); ultra-low latency, no cross-host network for secret fetches.
- **Backup discipline alignment.** Vault data persistence integrates with Proxmox VM snapshots — pre-update snapshots become a real recovery layer for Vault state, addressing the recovery-cascade pattern from Findings W/X/Y.
- **Identity infra always-on.** Vault is reachable whenever MS-01 is up, which is "always" by design (MS-01 is the convergence appliance; it does not sleep).

### Negative / accepted

- **Cold-start chicken-and-egg risk persists.** Per Finding Z, Vault has cold-start friction (seal-vault Transit autounseal source, 30+ dependent services). Moving to MS-01 doesn't fix this; it stays the same. Mitigation: Proxmox VM start order, Vault auto-unseal config preserved.
- **AI-side credential exposure risk persists.** Per Finding ZZ, AI tools that pretty-print Vault state output expose seal keys. Moving to MS-01 doesn't change the AI behavior; that's a separate concern about diagnostic tooling.
- **Vault retirement question (Finding Z) deferred.** This ADR doesn't decide whether to retire Vault eventually; it just decides where Vault lives until that question is closed.
- **Migration window required.** Vault state (raft data, seal keys, AppRoles, policies, secrets) must be exported, imported, validated. All Vault Agent sidecars need to re-authenticate; brief secret unavailability during cutover.

## Implementation

Detailed steps in `runbooks/d-17-211-convergence-migration.md` Phase B (WP-211-B-02). Approximate sequence:

1. Snapshot current Vault state on Mac Mini Pro (raft data, seal keys, AppRoles list, policies)
2. Stand up Vault server in Linux VM on MS-01 (Docker container or native binary; Docker for consistency)
3. Restore Vault state into new instance
4. Update Vault Agent sidecars on MS-01 Linux VM to point at local Vault (was: cross-host to Mac Mini)
5. Update any host-side Vault clients (Mac Mini launchd jobs that fetch from Vault) to point at MS-01 IP
6. Verify hash-only credential round-trip end-to-end for one canonical service (e.g., a Sonarr Vault Agent sidecar fetches API key)
7. Cutover (Mac Mini Pro Vault stopped)
8. Retirement of Mac Mini Pro Vault per Finding 9 sub-doctrine (compose down + AppRole/policy cleanup if any orphans)

## Risks specifically called out

- **Auto-unseal key migration.** If Vault uses Transit auto-unseal with `seal-vault` as the source, that secondary instance must also be reachable from the new Vault server. May require seal-vault relocation OR cross-VM/cross-host connectivity confirmed.
- **Vault Agent sidecars in containers using `host.docker.internal` may need URL update.** Sidecars on MS-01 Linux VM should reference Vault on same Docker network (e.g., `http://vault-server:8200`) or local IP.
- **Dependent services downtime.** arr-stack containers using Vault Agent sidecars will be unable to render fresh credentials during cutover. Sidecars typically cache the last-rendered credential, so brief unavailability of Vault may not surface as immediate failure — but tokens expire eventually and renewal would fail. Cutover should be brief (target: under 15 minutes).

## Cross-references

- `architecture-facts/2026-05-08-converged-platform-architecture.md` — master architecture
- `architecture-facts/circulatory-doctrine.md` — placement principle
- `decision-records/D-17-211-convergence-on-ms01.md` — convergence ADR (parent)
- `decision-records/D-17-212-thunderbolt-mesh-topology.md` — TB topology ADR
- `runbooks/d-17-211-convergence-migration.md` — migration runbook
- Master log Finding Z — Vault-as-credential-store friction (separate concern; not pre-empted by this ADR)
- Master log Finding ZZ — AI-side credential exposure (separate concern)
- Master log Findings W/X/Y — recovery cascade context for why Proxmox snapshots matter
