# Identifier conventions (canonical)

**Status:** Canonical (D#22 — architecture-fact, survives compaction)
**Source of truth:** `docs/PROJECT_FRAMEWORK.md` §1 Lifecycle Vocabulary
**Last verified:** 2026-05-02

Future sessions MUST consult this file before generating new
identifiers in any committed artifact (commits, docs, code, configs).

---

## Canonical formats

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| Phase | `Phase-NN` | `Phase-17` | Top-level grouping; numeric only |
| Deliverable | `D-NN-MM` | `D-17-04` | NN = phase, MM = deliverable index within phase, zero-padded |
| Work Package | `WP-NN-MM-XX` | `WP-17-04-02` | NN-MM matches parent deliverable; XX = WP index, zero-padded |
| Change Record | `CR-NN-NNN` | `CR-17-001` | NN = phase, NNN = sequence within phase |
| Risk | `R-NN` (cross-cutting) <br> `R-NN-MM-XX` (deliverable-scoped) | `R-01` <br> `R-17-04-01` | Cross-cutting risks numbered globally; scoped risks mirror WP numbering |
| Known Issue | `KI-NNN` | `KI-009` | Globally numbered, no phase scoping |
| Doctrine | `D#NN` | `D#22` | Globally numbered platform doctrine entries (not deliverables — distinct namespace) |
| Incident severity | `Sev-N` | `Sev-2` | 1=critical, 2=high, 3=medium, 4=low |
| Task | `T<n>.<m>` | `T1.7` | Ad-hoc within WPs; intentionally not enforced — operational, not tracked |

---

## Phase 17 historical migration (2026-05-02)

Phase 17 was authored using letter-shorthand identifiers (`17.A`
through `17.U`) and `WP-17-D-NN` (with literal `D` as a deliverable
proxy). This violated the framework's own conventions. Migration
landed in commit before `WP-17-04-02` to prevent wrong identifiers
flowing into the OpenProject project structure as primary keys.

| Old shorthand | Canonical | Description |
|---------------|-----------|-------------|
| `17.A` | `D-17-01` | Stack architecture audit promoted to repo |
| `17.B` | `D-17-02` | Capability audit template |
| `17.C` | `D-17-03` | Physical architecture audit |
| `17.D` | `D-17-04` | Replace Plane with OpenProject |
| `17.E` | `D-17-05` | Observability role-clarification |
| `17.F` | `D-17-06` | Agent surface audit + consolidation |
| `17.G` | `D-17-07` | topology-api audit |
| `17.H` | `D-17-08` | Sportarr fix-or-retire |
| `17.I` | `D-17-09` | OPNsense API integration for DNS-parity |
| `17.J` | `D-17-10` | Cisco Provenance Kit |
| `17.K` | `D-17-11` | Local LLM system prompt library |
| `17.L` | `D-17-12` | Gemma 4 + Qwen3-Coder-Next benchmarks |
| `17.M` | `D-17-13` | Goose agent CLI integration |
| `17.N` | `D-17-14` | exo distributed inference cluster |
| `17.O` | `D-17-15` | Mac Studio Day-1 execution |
| `17.P` | `D-17-16` | Loose-doc retirement |
| `17.Q` | `D-17-17` | Logical service architecture dashboard |
| `17.R` | `D-17-18` | Physical architecture visualization |
| `17.S` | `D-17-19` | Article-intake findings consolidated to repo |
| `17.T` | `D-17-20` | D#17/D#18/D#19/D#20/D#21 codified |
| `17.U` | `D-17-21` | OPNsense DNS state audit + Unbound disable + retroactive Vault incident review |

Work-package mapping for `D-17-04`:

| Old | Canonical | Description |
|-----|-----------|-------------|
| `WP-17-D-01` | `WP-17-04-01` | OpenProject deployment |
| `WP-17-D-01.5` | `WP-17-04-01.5` | Identifier convention correction (this work) |
| `WP-17-D-02` | `WP-17-04-02` | Plane data export + DB snapshot |
| `WP-17-D-03` | `WP-17-04-03` | Data import + structure mapping |
| `WP-17-D-04` | `WP-17-04-04` | Tooling rewrite (openproject_connector.py + sync) |
| `WP-17-D-05` | `WP-17-04-05` | Repo reference sweep |
| `WP-17-D-06` | `WP-17-04-06` | Plane retirement |

---

## Migration grace period

For one cycle, deliverable rows in `PROJECT_FRAMEWORK.md` and the
Phase 17 plan retain a `(historical: 17.X)` annotation so anyone
grep-ing the old shorthand finds the new identifier. After Phase 17
closes, these annotations may be dropped.

Tooling regexes in `scripts/phase-deliverable-count.py` and
`scripts/plane-sync-from-framework.py` accept BOTH forms during this
grace period; canonical form only after Phase 17 closeout.

---

## Why this matters

The whole point of migrating from Plane CE to OpenProject is to make
PMP+ITIL identifiers first-class in the project-management substrate.
Migrating with shorthand IDs would defeat the purpose: OpenProject
work packages would have wrong external IDs as primary keys, and
every subsequent connector/sync round-trip would propagate the
mistake.

Caught from control window 2026-05-02 between `WP-17-04-01` close and
`WP-17-04-02` start — earliest point at which the historical artifact
preserves correct IDs.
