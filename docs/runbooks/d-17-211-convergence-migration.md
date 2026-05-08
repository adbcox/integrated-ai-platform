# D-17-211 Convergence Migration Runbook

**Date:** 2026-05-08 (initial draft)
**Status:** DESIGN DRAFT (pre-execution; needs operator review before each phase begins)
**Migration target:** Move OPNsense from Protectli FW4B to MS-01 (as Proxmox VM) AND move arr-stack/Vault/Headscale from Mac Mini Pro Docker to Ubuntu LTS VM on the same MS-01 hardware
**Pairs with:** ADRs D-17-211, D-17-212, D-17-213; architecture-facts/2026-05-08-converged-platform-architecture.md

## Pre-flight (operator owns these)

These verifications happen BEFORE any phase begins. None require AI execution.

1. **MS-01 operational state confirmed.** Power on, BIOS POST clean, RAM detected as DDR5-5600 (not the originally-mis-ordered DDR4), all storage devices visible. Operator-side check.
2. **Backup of current Protectli OPNsense config exported.** GUI: System > Configuration > Backups > Download. Save outside MS-01 (operator's MacBook is fine).
3. **Backup of current Mac Mini Pro Vault state exported.** Vault snapshot via `vault operator raft snapshot save vault-pre-migration-2026-05-NN.snap`. Save outside Mac Mini.
4. **Backup of current Mac Mini Docker arr-stack compose + volumes.** `docker compose -f ~/control-center-stack/stacks/arr-stack/docker-compose.yml config > arr-stack-compose-pre-migration.yml`; `docker volume ls` snapshot.
5. **Maintenance window scheduled.** Phase A (OPNsense move) requires WAN downtime; ideally 2-hour window with operator presence.
6. **Cold-spare Protectli plan committed.** Decide whether Protectli stays on shelf as cold-spare or is sold. (Recommended: cold-spare. Cost of keeping: zero; benefit: emergency network restoration if MS-01 dies.)
7. **TB cables procured.** Minimum: 1× TB4 cable for MS-01 ↔ QNAP (Phase C). Optional: 2nd TB4 for Mac Mini Pro ↔ QNAP. Spec: certified 40 Gbps Thunderbolt 4 cables; cheap "USB-C" cables won't perform.
8. **Pi 5 8GB sourced** (or confirmed in pool). Required for Phase D.

## Phase A — Hypervisor and OPNsense migration

**Scope:** Install Proxmox VE on MS-01, provision OPNsense VM, migrate config, cutover.
**Outage impact:** WAN down during cutover (target: <30 minutes of actual downtime; 2-hour maintenance window with rollback margin).
**Rollback path:** If MS-01 OPNsense doesn't come up cleanly, power Protectli back on; it retains its current config.

### WP-A-01: Proxmox VE install on MS-01

- Boot MS-01 from Proxmox VE 8.x ISO (USB)
- Install with ZFS as host filesystem (RAID-1 mirror across the 2 NVMe slots if both populated, single-disk otherwise)
- Set root password (operator-side; capture into Vault post-migration)
- Configure management network (initially: bridge to wired LAN via 2.5G RJ45 #1)
- Reboot into Proxmox; verify web UI accessible at https://<MS-01-IP>:8006
- Disable enterprise repo, enable no-subscription repo (operator-side; standard Proxmox setup)

### WP-A-02: OPNsense VM provisioning

- Download OPNsense 24.x amd64 ISO via Proxmox web UI
- Create VM:
  - 2 cores (E-cores acceptable; OPNsense is not heavily threaded)
  - 4 GB RAM (start; can increase if monitoring shows need)
  - 32 GB ZFS-backed disk
  - VirtIO disk + VirtIO network (or PCIe passthrough if dedicating physical NICs)
- **PCIe passthrough decision:** for production, pass through the WAN NIC (one of the 2.5G RJ45 ports) and a LAN NIC (one of the 10G SFP+ ports). Improves performance and isolates from Proxmox host networking. Requires VT-d enabled in BIOS (verify pre-flight) and IOMMU groupings sane (run `find /sys/kernel/iommu_groups/ -type l` to verify).
- Install OPNsense from ISO (FreeBSD console-driven installer)
- Initial config: assign WAN/LAN interfaces to the passed-through NICs

### WP-A-03: OPNsense config restore

- In OPNsense web UI: System > Configuration > Backups > Restore
- Upload the config XML exported pre-flight from Protectli
- Reboot OPNsense VM; verify rules, DHCP, Dnsmasq records all present
- Verify in Dnsmasq: 55+ host records (49 *.internal + 6 bare per D-17-21 close)

### WP-A-04: os-caddy plugin install + Caddyfile migration

- OPNsense > System > Firmware > Plugins > install `os-caddy`
- Configure os-caddy with the same routes as the existing Mac Mini Docker Caddyfile (19+ *.internal domains)
- Test auto-internal-TLS feature: `curl -k https://prowlarr.internal` from a LAN client should return 200 once a backend is reachable (will be reachable after Phase B)
- **Pre-flight gate:** if os-caddy's auto-internal-TLS doesn't work as expected (feature parity with mainline Caddy), fall back to **os-haproxy plugin with internal CA** as the reverse proxy. ADR D-17-212 captures this fallback. The architecture is unchanged; only the implementation changes.

### WP-A-05: os-tailscale plugin install + subnet router migration

- OPNsense > System > Firmware > Plugins > install `os-tailscale`
- Authenticate the OPNsense Tailscale node against the Headscale instance (currently on Mac Mini Pro Docker; will move to Linux VM in Phase B — for now, point at current Mac Mini)
- Configure subnet router: advertise 192.168.10.0/24 (the wired LAN range) to tailnet
- Verify by connecting from MacBook (away or on tailnet): can reach LAN devices via tailnet
- **Note:** Mac Mini Pro is currently the tailnet exit at 100.64.0.1. After this WP, OPNsense becomes the subnet router. Mac Mini Pro becomes a regular tailnet client.

### WP-A-06: Cutover — Protectli → MS-01

- **Critical: maintenance window starts here.**
- Document Protectli's current WAN config (DHCP from Google Fiber? PPPoE? static?) for the new OPNsense VM
- Power down Protectli FW4B
- Move WAN cable from Protectli's WAN port to MS-01's PCIe-passed-through WAN NIC
- Move LAN cable from Protectli's LAN port to Ruckus uplink to MS-01's PCIe-passed-through LAN NIC
- Power up MS-01 (already up); confirm OPNsense VM auto-starts
- Verify Internet from a LAN client (e.g., HA NUC ping 8.8.8.8)
- Verify DNS from a LAN client (e.g., resolve google.com)
- Verify HTTPS to *.internal Caddy routes (will return cert errors until backends online — that's expected)
- **Maintenance window ends.**
- Power down Protectli FW4B for retention as cold-spare. Update its OPNsense config to match the new authoritative MS-01 config periodically (sync via config XML export/import, weekly cadence acceptable).

## Phase B — Linux VM and service migration

**Scope:** Stand up Ubuntu LTS Linux VM on MS-01; migrate arr-stack, Vault server, Headscale from Mac Mini Pro Docker.
**Outage impact:** brief (~15 min) Vault unavailability during cutover; arr-stack downtime ~15 min during cutover.
**Rollback path:** Mac Mini Pro Docker arr-stack and Vault remain RUNNING during validation; cutover only happens after validation passes.

### WP-B-01: Ubuntu LTS VM provisioning

- Proxmox web UI > Create VM:
  - 8 cores, 20 GB RAM
  - 200 GB ZFS-backed disk (primary; for Docker layers and small DBs)
  - Bridged to LAN (sees LAN as a normal client)
- Install Ubuntu 24.04 LTS server
- Standard hardening (operator-side; SSH keys, no password auth, etc.)
- Install Docker Engine (NOT Docker Desktop; this is real Linux)
- Install `tailscale` package; auth against Headscale
- Install `nfs-common` for QNAP NFS mount

### WP-B-02: Vault server migration (per D-17-213)

- Stand up Vault server container in Linux VM (use existing compose from Mac Mini, adjusted for Linux paths)
- Restore Vault raft snapshot from pre-flight backup
- Verify Vault unsealed (auto-unseal via Transit if `seal-vault` reachable; otherwise Shamir manual unseal)
- Verify AppRoles list, policies, all critical secrets present (read by hash, not value, per credential-handling doctrine)
- DO NOT cut over yet — original Vault on Mac Mini still running

### WP-B-03: Headscale migration

- Export Headscale state DB from Mac Mini Docker (the SQLite/PostgreSQL state file)
- Stand up Headscale in Linux VM with same config + state DB restored
- Verify all node keys present, ACL config matches
- DO NOT cut over yet — original Headscale on Mac Mini still running, OPNsense subnet router currently auth'd against it

### WP-B-04: arr-stack compose translation

- Copy compose file from Mac Mini (`/Users/admin/control-center-stack/stacks/arr-stack/docker-compose.yml`) to Linux VM (`/opt/arr-stack/docker-compose.yml`)
- Adjust paths:
  - `/Users/admin/mnt/qnap-downloads:/downloads` → `/mnt/qnap/downloads:/downloads` (or wherever NFS mount lands)
  - Volume mounts adjusted from Mac paths to Linux paths
- Adjust Vault Agent sidecar AppRole config:
  - URL: `https://host.docker.internal:8200` → `http://vault-server:8200` (same Docker network, simpler)
- DO NOT start yet — NFS mount must be ready first (Phase C).

### WP-B-05: NFS mount QNAP via TB4 (depends on Phase C-01)

- Configure QNAP NFSv4 export of `/share/CACHEDEV2_DATA/` with allowlist for MS-01 LAN IP and TB IP
- Mount on Linux VM: `/etc/fstab` entry `<qnap-tb-ip>:/share/CACHEDEV2_DATA /mnt/qnap nfs4 defaults 0 0`
- Verify hardlinks work via inode test:
  - In an alpine container with the mount: `ln /mnt/qnap/downloads/test-file /mnt/qnap/data/test-link`
  - Check inodes match: `stat /mnt/qnap/downloads/test-file /mnt/qnap/data/test-link` — same st_ino
  - **CRITICAL: hardlinks must work end-to-end.** If they don't, arr-stack import-by-hardlink fails and storage doubles. Halt here if test fails; investigate NFS server config (idmap, NFSv4 protocol selected, no fs-level uid mapping issues).

### WP-B-06: arr-stack parallel bring-up + validation

- Start arr-stack on Linux VM with compose
- Both arr-stacks now running: Mac Mini Docker (current production) and Linux VM (new candidate)
- They share the same QNAP library (read-only on new candidate initially)
- Validate end-to-end on new candidate:
  - Lidarr: 1-album test. New release indexed → grabbed → downloaded to `/downloads` → moved to `/data/media/music/.../` via hardlink → playable in Navidrome
  - Sonarr: 1-episode test. Same flow.
  - Radarr: 1-movie test. Same flow.
  - For each: verify hardlink semantics (same st_ino on source and destination)

### WP-B-07: Cutover — Mac Mini Docker → Linux VM

- **Critical: cutover starts here.**
- Stop Mac Mini Docker arr-stack (`docker compose down`)
- Stop Mac Mini Docker Headscale; OPNsense subnet router will need to re-auth against new Headscale on Linux VM (operator-side: update `os-tailscale` config to point at new Headscale URL)
- Stop Mac Mini Docker Vault server; all Vault Agent sidecars on Linux VM authenticate to local Vault (already configured per WP-B-02 and WP-B-04)
- Stop Mac Mini Docker Caddy (Caddy on OPNsense already serving via `os-caddy` plugin)
- Verify all *.internal routes return 200 from a LAN client
- Verify Vault Agent sidecars in arr-stack containers have refreshed credentials successfully
- Verify Tailscale clients can still reach LAN via OPNsense subnet router (Headscale on Linux VM as auth)
- **Cutover complete.** Linux VM is primary.

## Phase C — TB segment

**Scope:** Establish 40 Gbps direct TB connection between MS-01 and QNAP (highest impact); optional Mac Mini ↔ QNAP TB; mDNS reflection for Continuity.
**Outage impact:** None — adds capacity, doesn't replace anything.

### WP-C-01: MS-01 ↔ QNAP TB4 cable + thunderbolt-net config

- Connect TB4 cable: MS-01 USB4 #1 ↔ QNAP TB4 #1
- On Linux VM (or Proxmox host — TBD which holds the TB segment): configure `thunderbolt-net` driver
- On QNAP: install/enable Thunderbolt 3 Networking package (QuTS hero supports it)
- Assign IPs in 172.20.20.0/24 segment (or whatever range chosen):
  - MS-01: 172.20.20.1
  - QNAP: 172.20.20.10
- Verify ping in both directions
- Verify NFS over the TB segment: re-test the WP-B-05 hardlink test with traffic going via TB instead of LAN
- Update `/etc/fstab` on Linux VM to use TB IP for the QNAP NFS mount

### WP-C-02: TB segment IP plan and DHCP

- OPNsense Dnsmasq: add a scope for 172.20.20.0/24
- Reservations for the static endpoints (MS-01, QNAP, Mac Studio, Mac Mini Pro)
- DNS: same Dnsmasq instance authoritative; *.internal still resolves consistently across segments

### WP-C-03: Mac Mini Pro ↔ Mac Studio TB5 (already exists)

- No action; existing exo cluster TB5 link preserved

### WP-C-04: Optional Mac Mini Pro ↔ QNAP TB4

- Add cable if procured
- Configure `Thunderbolt Bridge` interface on Mac Mini Pro
- Update Mac Mini Pro routing to prefer TB for QNAP destinations
- Validate: backup chain (Restic → MinIO on QNAP) traverses TB; throughput should jump from ~125 MB/s to several GB/s

### WP-C-05: mDNS / Bonjour reflection

- Install `avahi-daemon` on Linux VM (or `mdns-repeater`)
- Configure to reflect mDNS between TB segment interface and LAN segment interface
- Validate: AirDrop from iPhone (LAN-side WiFi) to Mac Mini Pro (TB-segment) works; AirPlay to HomePods works

### WP-C-06: Mac dual-homing (initial state)

- Macs keep BOTH LAN ethernet AND TB connections
- macOS routing automatically prefers TB for paths reachable via TB peer
- Validate: TB cable disconnect doesn't kill Mac connectivity (LAN takes over)
- **Post-stability transition (operator-decided, separate decision):** if all Mac traffic patterns prove stable on TB-only, optionally remove LAN ethernet from Macs

## Phase D — Monitoring tier on Pi

**Scope:** Move Zabbix server from Mac Mini Docker to Pi 5 8GB.
**Outage impact:** Zabbix data continuity disrupted briefly during migration; agents reconfigure to point at new server.

### WP-D-01: Pi base provisioning

- Pi OS Lite 64-bit on Pi 5 8GB
- SSH key auth, hostname, network config
- Install `tailscale`; auth against Headscale (now on Linux VM)
- Install Docker Engine (or run Zabbix as native package)

### WP-D-02: Zabbix server migration

- Export Zabbix DB and config from Mac Mini Docker Zabbix
- Stand up Zabbix server on Pi (Docker container or native)
- Import DB
- Reconfigure Zabbix agents on every host to point at Pi IP
- Verify metrics flowing
- Stop Zabbix server on Mac Mini Docker

## Phase E — Decommissioning (Finding 9 sub-doctrine: residue is a positive failure mode)

**Scope:** Retire all the Mac Mini Pro Docker services that were migrated. No residue.

### WP-E-01: Mac Mini Docker arr-stack retirement

- `docker compose down` on Mac Mini Docker arr-stack
- Remove containers, networks, volumes (with operator confirmation)
- Archive compose file to `_archive/`
- Update service registry: arr-stack location → MS-01 Linux VM

### WP-E-02: Mac Mini Docker Caddy retirement

- `docker compose down` on Mac Mini Docker Caddy
- Archive Caddyfile to `_archive/` (Caddy now lives in OPNsense `os-caddy` config)
- Update service registry: reverse proxy location → OPNsense

### WP-E-03: Mac Mini Docker Headscale retirement

- `docker compose down`
- State DB already migrated in WP-B-03
- Update service registry

### WP-E-04: Mac Mini Docker Vault retirement (per D-17-213)

- Final hash-only verification that all consumers are reading from new Vault on Linux VM
- `docker compose down` on Mac Mini Docker Vault
- AppRole/policy cleanup if any orphans (per Finding 3 from `integration-audit-doctrine.md` — Vault AppRoles outliving their consumers)

### WP-E-05: SMB mount + LaunchDaemon retirement

- Unmount `/Users/admin/mnt/qnap-downloads` SMB mount
- Disable + remove the LaunchDaemon plist that mounted it (per Finding Y staleness if applicable)
- Archive any related runbooks (`runbooks/qnap-downloads-mount.md`) — content moves to NFS-via-TB documentation in this runbook

### WP-E-06: Docker Desktop removal from Mac Mini Pro

- Quit Docker Desktop
- Uninstall Docker Desktop application
- Remove residual `~/.docker/`, `~/.config/colima/`, etc. (operator's call on cleanliness vs preservation)
- Verify no platform service still depends on Docker on Mac Mini Pro

### WP-E-07: Mac Mini Pro power profile review

- macOS Energy Saver: enable sleep when idle (was blocked by always-on Vault/Headscale; now unblocked)
- Verify launchd jobs continue to run during sleep where they need to (Power Nap behavior)
- Validate: agent sessions wake the Mac Mini cleanly when operator initiates work

### WP-E-08: Protectli FW4B disposition

- Decision: cold-spare (recommended) vs sell vs sandbox
- If cold-spare: power off, store, periodically (weekly?) sync OPNsense config from MS-01 VM snapshot
- Document cold-spare procedure: power on Protectli, restore latest config snapshot, plug WAN/LAN, replace failed MS-01 in <30 minutes

## Phase F — Doctrine and audit

**Scope:** Update doctrine documents and audit refresh to reflect post-migration state.

### WP-F-01: Finding 22 doctrine narrowing

- Patch `architecture-facts/integration-audit-doctrine.md` Finding 22:
  - Original framing: "QNAP is the NAS, not the application tier"
  - Narrowed framing: "Cross-host Mac-Mini-Docker-bridge → QNAP-host-service hits QTS packet filter; consolidate application tier on a single host (MS-01) to avoid"
  - Note: with arr-stack consolidated on MS-01 Linux VM, the empirical failure pattern of Finding 22 no longer occurs in this architecture

### WP-F-02: Tier-architecture-doctrine update

- New file or update existing: `architecture-facts/converged-appliance-architecture.md` (or extend `2026-05-08-converged-platform-architecture.md` if it suffices)
- Cross-reference circulatory doctrine

### WP-F-03: Physical architecture audit refresh

- Already created at `_audit/physical-architecture-2026-05-08.md` (this session)
- Update post-migration to reflect actual MS-01 state, IP assignments, current operating service inventory

### WP-F-04: Service registry MVP integration

- Hook OPNsense API automation surface (extended `opnsense_runner.py`) into Service Registry MVP per Finding CC
- New service deployment → automatic DNS record + firewall rule + DHCP reservation via OPNsense API
- Out of scope for D-17-211 itself; tracked as follow-on

## Critical risks and rollback paths

| Risk | Mitigation | Rollback |
|---|---|---|
| MS-01 doesn't boot Proxmox cleanly | Pre-flight verification | Boot from USB rescue; rebuild |
| OPNsense VM doesn't reach Internet post-cutover | Test pre-flight on isolated network | Power Protectli back on (cold-spare ready) |
| os-caddy plugin lacks auto-internal-TLS feature parity | Pre-flight test | Fall back to os-haproxy + internal CA |
| Hardlinks don't work over NFS-via-TB | WP-B-05 explicit hardlink validation | Halt; investigate NFS config; do NOT proceed to cutover |
| Vault state restore fails | Snapshot is canonical; can re-snapshot from running Mac Mini | Mac Mini Vault still running until WP-B-07 cutover |
| Cutover (Phase B) leaves arr-stack containers without working credentials | Validate WP-B-02 before cutover; sidecars cache last credential | Cutover is reversible until Mac Mini containers are stopped |
| TB networking macOS ↔ Linux not behaving as expected | Patterns exist but config may need iteration | TB is additive; LAN remains as fallback |

## Status

**DESIGN DRAFT** as of 2026-05-08. Operator review required before each phase begins; ADR D-17-211 is ACCEPTED but execution is gated on operator scheduling maintenance windows and confirming pre-flight items.

## Cross-references

- `architecture-facts/2026-05-08-converged-platform-architecture.md` — master architecture
- `architecture-facts/circulatory-doctrine.md` — placement principle
- `_audit/physical-architecture-2026-05-08.md` — fleet state audit
- `decision-records/D-17-211-convergence-on-ms01.md` — convergence ADR
- `decision-records/D-17-212-thunderbolt-mesh-topology.md` — TB topology ADR
- `decision-records/D-17-213-vault-relocation-to-ms01.md` — Vault relocation ADR
- `architecture-facts/integration-audit-doctrine.md` — Finding 22 (narrowed by this migration); Finding 9 (residue is a positive failure mode); Finding 3 (Vault AppRole orphans)
- `runbooks/qnap-downloads-mount.md` — retired by this migration (NFS replaces SMB)
