# Mac Studio M3 Ultra — Day-1 Onboarding Record

## Hardware
- Model:         Apple Mac Studio M3 Ultra (Mac15,14)
- CPU:           Apple M3 Ultra
- RAM:           96 GB
- MAC:           1C:1D:D3:E1:40:CD
- IP:            192.168.10.142
                 (DHCP currently; static reservation pending operator decision — see Open follow-ups)
- Hostname:      mac-studio (set across hostname / ComputerName /
                 LocalHostName / HostName)
- macOS:         26.4.1 (build 25E253)
- Network:       10Gbase-T full-duplex
- Thunderbolt:   5 buses, TB5 at 120 Gb/s each

## Onboarded
- Date:          2026-05-01
- Deliverable:   17.O — Mac Studio Day-1 execution
- Operator pre-work completed:
    - Remote Login enabled
    - SSH key auth from Mac Mini (id_ed25519)
    - Hostname renamed across all 4 macOS locations
    - macOS version verified ≥26.2 (passes 17.N gating)
- NetBox device ID:  5
- Vault path:        secret/mac-studio/_meta
- Headscale:         pending operator install per
                     `docs/runbooks/headscale-client-onboarding.md`

## Day-1 scope

Identity, network, CMDB, secrets initialization. NOT YET:
- Workload assignment
- Orchestration role
- exo cluster peering (gated on 17.N)
- Service deployments

## Capability ceiling (per D#21 capability plane)

What this node CAN do today (verified Day-1):
- Apple Silicon arm64 compute
- 96 GB unified memory
- Metal GPU (M3 Ultra GPU cores)
- Thunderbolt 5 networking on rear ports (120 Gb/s)
- 10GbE Ethernet
- macOS-native services

What this node WILL do (assigned in subsequent deliverables):
- GPU compute via Metal (Ollama, MLX inference)
- exo cluster peer with Mac Mini for distributed inference (17.N)
- Possibly orchestration secondary (TBD; depends on 17.D OpenProject migration outcome)

What this node is NOT (explicit non-goals):
- Linux compute (Threadripper's role — Phase 18.B)
- SNMP/network monitoring authority (Zabbix's role)
- Backup target (QNAP's role)

## CMDB representation (NetBox)

Device record at `http://netbox.internal/dcim/devices/5/`:

| Field | Value |
|---|---|
| name | mac-studio |
| role | Compute (created 2026-05-01) |
| site | Integrated AI Platform |
| device_type | Mac Studio M3 Ultra (manufacturer: Apple, both created 2026-05-01) |
| serial | Mac15,14 |
| tags | apple-silicon, day-1-onboarding, phase-17 |
| interface en0 | type=10gbase-t, mac=1C:1D:D3:E1:40:CD |

**Schema deviation note.** The Day-1 prompt asked for several
hardware custom-fields (cpu, ram_gb, macos_version,
thunderbolt_version, ethernet_speed, role_intent) on dcim.device.
NetBox today only carries service-oriented custom fields
(container_image, health_url, etc. — added Phase 14 D-DOC). Rather
than sprawl the schema for one device, hardware metadata lives in
the Vault `_meta` key (below) and in this runbook. When a future
deliverable wires up dcim.device hardware fields, backfill from
those sources.

## Vault metadata

Path: `secret/mac-studio/_meta`

Populated 2026-05-01 with:
- created, role_intent, onboarded_via
- cpu, ram_gb
- hostname, macos_version, macos_build
- mac_address, ip_address_dhcp
- ethernet_speed, thunderbolt_version, thunderbolt_buses
- netbox_device_id

Read with:
```
docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault-server vault kv get secret/mac-studio/_meta
```

No AppRole was provisioned for mac-studio yet — no service is
assigned that needs one. Provision when the first credential-
consuming workload lands.

## SSH access

Alias added to `~/.ssh/config` on Mac Mini:

```
Host mac-studio
    HostName 192.168.10.142
    User admin
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 60
```

Verify: `ssh mac-studio 'hostname'` → `mac-studio`.

## Drift detection

`scripts/check-repo-coherence.py mac-studio-reachable` — pings
192.168.10.142 with 2s timeout. Wired into:

- pre-commit hook `mac-studio-reachable` (scoped to changes that
  touch this runbook, the Headscale runbook, or the coherence
  script itself — not every commit)
- `validate-infrastructure` CI workflow (the all-checks job;
  GitHub-hosted runner skips this check via GITHUB_ACTIONS env-var
  detection because it can't reach the home LAN)

## Networking decision space (TB5 vs Ethernet)

The Mac Mini ↔ Mac Studio link can be:

| Option | Speed | Notes |
|---|---|---|
| **1G Ethernet** (current) | 1 Gb/s | Goes through OPNsense-routed 192.168.10.0/24. Works today. |
| **10G Ethernet** | 10 Gb/s on Studio side | Mac Mini's 10GbE port, if added, would unblock. Bottleneck is currently the Mini side. |
| **TB5 direct** | 120 Gb/s | Bypasses LAN routing; needs TB5 cable + manual addressing on the new TB5 interface. **17.N (exo cluster) target.** |

Day-1 stays on Ethernet. TB5 evaluation belongs to 17.N when that
deliverable opens.

## Open follow-ups (NOT KIs — normal pending operator actions)

- **Tailscale install + Headscale approval** — see
  `docs/runbooks/headscale-client-onboarding.md`. Needs operator
  password on Mac Studio.
- **DHCP reservation vs static IP** — operator decision pending.
  192.168.10.142 currently a DHCP lease, not reserved. If DHCP
  shuffles the IP, NetBox + Vault `_meta` + this runbook all
  contain stale IPs.
- **SSH key comment "macbook-to-macmini"** — cosmetic; the key in
  `~/.ssh/id_ed25519` carries an old comment. Cleanup whenever
  convenient.
- **mac-studio.internal subdomain** — allocate when first web
  service lands on the node. Caddy registration pattern in
  `docs/runbooks/add-new-service.md`.
- **TB5 direct-link cable** — order when 17.N opens (exo cluster
  needs the high-bandwidth interconnect).

## Related

- `docs/PHASE_ROADMAP.md` — Phase 17 / 18 context
- `docs/phase-17/PHASE_17_PLAN_2026-05-01.md` — full Phase 17
  deliverable list including 17.O parent + 17.N future use
- `docs/runbooks/headscale-client-onboarding.md` — Tailscale +
  Headscale install procedure
- `docs/PROJECT_FRAMEWORK.md` §3.1 — T1–T4 local model stack
  prioritization (relevant when Mac Studio gets workload
  assignment)
