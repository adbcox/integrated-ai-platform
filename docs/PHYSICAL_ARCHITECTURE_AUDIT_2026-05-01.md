# Physical Architecture Audit — 2026-05-01

**Purpose.** D#21 establishes three audit planes — physical, logical,
capability — and requires each to have a current artifact. The
logical-plane audit exists (`docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md`,
17.A); the capability-plane methodology exists
(`docs/templates/capability-audit-template.md`, 17.B). This document
is the missing third leg: a physical-plane audit grounded in probed
hardware, network, and storage state as of 2026-05-01.

**Scope.** What hardware exists, where it sits, what it's wired to,
what's powered on, what's powered off, and where the visible gaps
are. Not: what services run on the hardware (logical plane) or what
the hardware is theoretically capable of (capability plane).

**Probe context.** Probes executed from mac-mini (192.168.10.145) on
2026-05-01. Mac Studio data captured Day-1 (17.O). LAN topology from
ARP table at probe time. QNAP from active SMB mount. Threadripper
data from prior inventory (host offline at probe time).

---

## Section 0 — Audit method (reproducibility)

For re-audits, the data sources used here are:

- macOS hardware identity: `system_profiler SPHardwareDataType`
- macOS network identity: `ifconfig en0`, `system_profiler SPThunderboltDataType`
- macOS version: `sw_vers`
- Container count: `docker ps -q | wc -l`
- LAN ARP: `arp -an` from mac-mini (one-side view; OPNsense ARP would
  give the authoritative table)
- QNAP: `mount | grep qnap`, `df` against the mounted share
- Threadripper: prior procurement record (host offline)

Each data point in the body cites which probe produced it.

---

## Section 1 — Compute nodes (powered + reachable)

### 1.1 — mac-mini (192.168.10.145)

The control-plane host. Carries all platform services today.

| Field | Value | Source |
|---|---|---|
| Model | Mac Mini (Mac16,11) | `system_profiler SPHardwareDataType` |
| CPU | Apple M4 Pro | same |
| RAM | 48 GB unified | same |
| Serial | XXKT21723D | same |
| SSD | 994.7 GB internal (230 GiB used, 664 GiB avail) | `df -h` against `/System/Volumes/Data` |
| macOS | 26.3 build 25D125 | `sw_vers` |
| Hostname | mac-mini.internal | `hostname` |
| en0 MAC | d0:11:e5:2c:0b:69 | `ifconfig en0` |
| en0 link | **1000baseT full-duplex** | `ifconfig en0` |
| Thunderbolt | 3 buses, all TB5 at 120 Gb/s | `system_profiler SPThunderboltDataType` |
| Containers running | 66 | `docker ps -q \| wc -l` |

**Observation — 1G Ethernet is the current Mac Mini bottleneck.**
The host's en0 is 1G; the LAN switch is 10G-capable; the Mac Studio
peer is 10GbE-capable; QNAP is 10GbE-capable. Until a 10GbE adapter
or TB5 direct-link is added on the Mini side, all north-south traffic
to/from this node is gated at 1 Gb/s. This is acceptable for
control-plane work today; it will not be acceptable for distributed
inference (17.N) or for storage workloads that move large objects.

### 1.2 — mac-studio (192.168.10.142)

Onboarded 2026-05-01 via 17.O. Day-1 scope only — no workload yet.

| Field | Value | Source |
|---|---|---|
| Model | Mac Studio (Mac15,14) | Day-1 probe |
| CPU | Apple M3 Ultra | same |
| RAM | 96 GB unified | same |
| Serial | CX67160P2W | same |
| SSD | 994.7 GB internal | same |
| macOS | 26.4.1 build 25E253 | same |
| Hostname | mac-studio | same |
| en0 MAC | 1c:1d:d3:e1:40:cd | same (matches ARP entry .142) |
| en0 link | 10Gbase-T full-duplex | same |
| Thunderbolt | 5 buses, all TB5 at 120 Gb/s | same |

DHCP lease — static reservation pending operator decision (Day-1
runbook open follow-up).

### 1.3 — Hardware comparison

| Property | mac-mini | mac-studio |
|---|---|---|
| CPU class | M4 Pro | M3 Ultra |
| RAM | 48 GB | 96 GB |
| GPU cores | M4 Pro GPU | M3 Ultra GPU (more) |
| Ethernet | 1 GbE (bottleneck) | 10 GbE |
| TB buses | 3 × TB5 | 5 × TB5 |
| Role today | control plane (66 containers) | identity-only Day-1 |
| Role planned | control plane + orchestration | inference (Phase 17.N exo cluster), specialty model serving |

The two Macs are complementary, not redundant — different
generations, different memory ceilings, different roles.

---

## Section 2 — Compute nodes (offline at probe time)

### 2.1 — threadripper

Prior inventory (host not currently powered on; future Phase 18.B
target):

| Field | Value | Source |
|---|---|---|
| Class | Threadripper workstation | procurement record |
| Chipset | WRX80 | same |
| GPU | NVIDIA RTX 4070 | same |
| RAM | 64 GB DDR4 ECC | same |
| NIC | Intel X550-AT2 (10 GbE) | same |
| Status | offline | no ARP entry; not pingable |

Role intent: Linux compute for workloads that need NVIDIA CUDA or
Linux-native services (containers without macOS Docker Desktop
overhead, Linux-only software stacks). NOT a control-plane peer to
the Macs.

### 2.2 — Other powered-off / not-on-LAN today

None known. The MacBook Pro M5 (Block 3 parity peer) is a roaming
device, not LAN-resident; not in scope for this physical audit.

---

## Section 3 — Network topology

### 3.1 — LAN identity

- **Subnet:** 192.168.10.0/24
- **Router/gateway:** 192.168.10.1 (OPNsense — ARP 38:05:25:32:72:06)
- **Broadcast:** 192.168.10.255
- **DHCP server:** OPNsense (assumed; not separately probed here)

### 3.2 — Identified nodes (ARP from mac-mini, 2026-05-01)

| IP | MAC | Identity | Notes |
|---|---|---|---|
| 192.168.10.1 | 38:05:25:32:72:06 | OPNsense gateway | DHCP + routing + DNS |
| 192.168.10.142 | 1c:1d:d3:e1:40:cd | mac-studio | Day-1 onboarded |
| 192.168.10.145 | d0:11:e5:2c:0b:69 | mac-mini | platform control plane |
| 192.168.10.150 | 8c:90:2d:26:35:cf | (operator-known) | UP |
| 192.168.10.151 | c4:f7:c1:39:c9:2e | (operator-known) | UP |
| 192.168.10.197 | 34:b7:da:fd:25:c0 | (operator-known) | UP |
| 192.168.10.141 | fc:aa:14:a9:9f:d2 | (operator-known) | UP |
| 192.168.10.201 | 24:5e:be:7f:38:26 | qnap | 10 GbE NAS — see §4 |

### 3.3 — Unidentified active nodes (need operator confirmation)

These IPs respond to ARP from mac-mini but the owner is not
documented in this repo. Not necessarily anomalies — likely operator
devices, IoT, or peripherals — but the audit surfaces them for
disposition (NetBox entry, or explicit "not platform" tag):

```
192.168.10.101  c4:f7:c1:02:5e:1c
192.168.10.104  e4:65:b8:cf:b0:e8
192.168.10.105  34:b7:da:fd:31:04
192.168.10.111  cc:8d:a2:a2:a1:f4
192.168.10.113  4a:fd:5e:7a:19:83
192.168.10.122  60:83:e7:df:86:64
192.168.10.123  04:e4:b6:17:98:f2
192.168.10.124  60:83:e7:df:86:66
192.168.10.127  1a:b9:6c:76:50:10
192.168.10.133  cc:8d:a2:b4:e5:30
192.168.10.134  d0:b0:cd:01:17:e9
192.168.10.136  a0:cc:2b:ea:59:db
192.168.10.144  10:2b:41:56:dc:64
192.168.10.147  60:74:f4:02:71:e4
192.168.10.148  c0:09:25:37:35:8a
192.168.10.152  60:74:f4:03:0e:7c
192.168.10.184  ea:a8:91:74:57:1c
192.168.10.185  c8:2e:18:57:a5:ec
192.168.10.193  60:83:e7:df:78:f1
192.168.10.194  34:b7:da:fd:21:80
```

Recommended disposition: walk this list with the operator; either
register each in NetBox (with the appropriate role tag, even if
"non-platform IoT"), or explicitly mark them as out-of-scope.
Tracked as a Phase 17 follow-up.

### 3.4 — Incomplete ARP entries

```
192.168.10.146  (incomplete)
192.168.10.149  (incomplete)
```

Either powered off, on a different VLAN, or not responding to ARP at
this moment. Not flagged as anomalous unless one of these IPs is
expected to be a platform host.

### 3.5 — Link-local + multicast

```
169.254.x.x      Apple link-local (normal; auto-assigned when DHCP fails)
224.0.0.251      mDNS multicast (normal; Bonjour)
```

No action.

### 3.6 — Network bottleneck inventory

| Link | Current speed | Endpoints capable of more |
|---|---|---|
| mac-mini ↔ switch | 1 GbE | mini en0 is 1G; switch 10G |
| mac-studio ↔ switch | 10 GbE | already at endpoint speed |
| qnap ↔ switch | 10 GbE | already at endpoint speed |
| mac-mini ↔ mac-studio | 1 GbE (via switch) | both have TB5 (120 Gb/s) — direct link is 17.N target |
| OPNsense ↔ switch | unknown from this side | (operator can confirm) |

The Mac Mini's 1 GbE is the only documented bottleneck on the
hot-path between platform compute and storage. The TB5-direct option
(Mac Mini ↔ Mac Studio) is reserved for 17.N (exo cluster).

---

## Section 4 — Storage

### 4.1 — qnap (192.168.10.201)

| Field | Value | Source |
|---|---|---|
| IP | 192.168.10.201 | ARP |
| MAC | 24:5e:be:7f:38:26 | ARP |
| Mount on mac-mini | `//admin@192.168.10.201/download` → `/Users/admin/mnt/qnap-downloads` | `mount` |
| Filesystem | smbfs (nodev, nosuid) | same |
| Capacity | 23 TB | prior probe |
| Used | 8.2 TB (~37%) | prior probe |

QNAP also runs MinIO (port 9000) — that's a logical-plane fact, not
physical. Listed here only because the physical capacity ceiling
(23 TB) constrains both SMB and MinIO use simultaneously.

### 4.2 — Internal SSDs

| Host | Capacity | Used | Available |
|---|---|---|---|
| mac-mini | 994.7 GB | 230 GiB | 664 GiB |
| mac-studio | 994.7 GB | (Day-1; not separately probed) | (large; node carries no workloads yet) |

Mac Mini SSD is at 26% — comfortable headroom. Container volumes,
Vault data, and audit logs all live here; restic backs them to QNAP.

### 4.3 — Backup chain

- Source: mac-mini (Vault data + service volumes)
- Restic repo: on QNAP (over SMB mount)
- Schedule: nightly via launchd (`scripts/backup.sh`)
- Vault snapshot directory: `/Users/admin/.vault-snapshot/current`
  (warm-copy strategy, ADR-A-017 in progress)

The backup chain itself is logical-plane; what matters physically is
that QNAP capacity is the hard ceiling for retention and that the
SMB link (10 GbE on QNAP side, 1 GbE on Mac Mini side) is the
throughput ceiling for restore time.

---

## Section 5 — Power and physical environment

Out of scope for this revision. Future passes should capture:
- UPS coverage (which hosts are on battery, runtime budget)
- Rack/shelf placement (so a physical incident — leak, fall — can be
  scoped quickly)
- Cable inventory (TB5 cables on hand for 17.N)

These are operator-domain facts not derivable from probes; capture
on the next physical visit.

---

## Section 6 — Visible gaps and follow-ups

Numbered for cross-reference:

1. **Mac Mini en0 is 1 GbE.** Bottleneck for distributed-inference
   and large object I/O. Resolution paths: (a) USB/TB 10GbE adapter,
   (b) TB5 direct link to Mac Studio (17.N target).
2. **Mac Studio IP is DHCP, not reserved.** Static reservation
   pending operator decision (logged in Day-1 runbook).
3. **20 unidentified active LAN nodes** (§3.3) need disposition —
   register or explicitly out-of-scope.
4. **Two incomplete ARP entries** (.146, .149) — need operator
   confirmation that these aren't expected platform hosts.
5. **Threadripper is offline.** Phase 18.B target; powering it on
   becomes a deliverable when that phase opens.
6. **No OPNsense-side ARP probe.** This audit's LAN view is from
   one host; OPNsense's table would be authoritative. Add an
   OPNsense API probe to a future audit.
7. **Power/environment data missing** (§5).
8. **Mac Mini → QNAP throughput is 1 GbE-bound on the Mac side.**
   Restore-time budget assumes this; revisit if Mini gets a 10GbE
   path.

---

## Section 7 — How to refresh this audit

Trigger an audit refresh when:

- A compute node is added or removed (Day-1 onboarding or
  retirement)
- Network topology changes (new switch, new VLAN, OPNsense
  reconfig touching subnets)
- Storage layout changes (QNAP reconfig, new NAS, encryption
  rotation that changes mount paths)
- Phase boundary review (D#19) sweeps the physical plane

Re-run the probes from Section 0; re-author this document at
`docs/PHYSICAL_ARCHITECTURE_AUDIT_{YYYY-MM-DD}.md`. Keep the prior
audit as a snapshot — physical history is rarely revisited but
occasionally load-bearing for incident scoping.

---

## Decision log

- **Auditor:** Claude session (operator-reviewed)
- **Date:** 2026-05-01
- **Probe context:** see Section 0
- **Linked artifacts:**
  - `docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md` (logical plane,
    17.A)
  - `docs/templates/capability-audit-template.md` (capability plane
    methodology, 17.B)
  - `docs/audits/capability/zabbix-2026-05-01.md` (capability plane
    first worked example, 17.B)
  - `docs/runbooks/mac-studio-day-1.md` (Mac Studio physical record,
    17.O)
  - D#21 (three-plane audit doctrine)
- **Phase deliverable:** 17.C
