# `docs/_audit/` — audit artifacts index

Audit outputs are point-in-time validation artifacts used to support
deliverable decisions and doctrine updates. These files are historical
records; do not rewrite old audits in place.

## Inventory

### Integration / architecture audits

| File | Date | Purpose | Origin deliverable |
|---|---|---|---|
| `stack-architecture-2026-05-01.md` | 2026-05-01 | Stack architecture baseline audit | D-17-01 family |
| `physical-architecture-2026-05-01.md` | 2026-05-01 | Physical topology and host-state audit | D-17-15 family |
| `integrated-stack-target-2026-05-03.md` | 2026-05-03 | Target-state definition for integrated audit | D-17-32 |
| `integrated-stack-gaps-2026-05-03.md` | 2026-05-03 | Gap report (B/D/N severities) | D-17-32 |
| `integrated-stack-backlog-2026-05-03.md` | 2026-05-03 | Prioritized remediation backlog from audit | D-17-32 |
| `phase-18-status-audit-2026-05-04.md` | 2026-05-04 | §18 status and cross-reference reconciliation | D-17-60 |

### CMDB audits

| File | Date | Purpose | Origin deliverable |
|---|---|---|---|
| `cmdb-substrate-inventory-2026-05-03.md` | 2026-05-03 | Three-substrate inventory (NetBox/YAML/inventory.json) | D-17-43/45 intake |
| `cmdb-drift-2026-05-03.md` | 2026-05-03 | Concrete drift instance catalog | D-17-43/45 intake |

### DNS audits

| File | Date | Purpose | Origin deliverable |
|---|---|---|---|
| `opnsense-dns-state-2026-05-03.md` | 2026-05-03 | DNS authority verification state | D-17-21 |
| `caddy-unbound-parity-2026-05-01.md` | 2026-05-01 | Historical parity audit before Dnsmasq finalization | D-17-09 era |

### Capability audits (`_audit/capability/`)

Point-in-time capability checks from early phase-17 architecture
reconciliation. Some are heavily referenced; others remain historical
evidence with low inbound references.

## Lifecycle

- New audits should be additive (new timestamped files), not in-place edits.
- If an audit is superseded, reference the newer audit in its replacement doc.
- Long-term forensic records can be rehomed to `_archive/` only when no active doctrine relies on them.
