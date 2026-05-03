# Loose-doc inventory — 2026-05-03 (D-17-16 WP-02)

**Trigger:** D-17-16 (re-parented from D-16-05) — loose-doc retirement.
**Method:** `find docs -type f -name '*.md'` minus canonical paths
(`architecture-facts/`, `runbooks/`, `_audit/`, `phase-NN/`,
`troubleshooting/`, `known-issues/`, `architecture-patterns/`, `adr/`,
`dashboards/`, `_provenance/`, `_retired/`) minus canonical top-level
files (`ARCHITECTURE.md`, `PROJECT_FRAMEWORK.md`, `PHASE_ROADMAP.md`,
`PHASE_LOG.md`, `DECISION_REGISTER.md`, `README.md`, `index.md`).
**Total loose:** 48 files across 9 non-canonical clusters.
**Surface-back rule:** operator set 50-item threshold; this is at 48
(under) but the *kind* of decisions hidden in three of the clusters
exceed mechanical retire/move and warrant operator ratification before
WP-03 batch execution.

---

## Cluster A — Top-level loose files (7 files)

| File | Category | Disposition |
|------|----------|-------------|
| `docs/PLATFORM_OVERVIEW.md` | STALE (already-archived stub; superseded by `ARCHITECTURE.md` per Phase 14 D-DOC) | move to `_retired/` |
| `docs/PHYSICAL_ARCHITECTURE_AUDIT_2026-05-01.md` | MISPLACED (active D-17-01/D#21 audit) | move to `_audit/physical-architecture-2026-05-01.md` |
| `docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md` | MISPLACED (active D-17-01/D#21 audit) | move to `_audit/stack-architecture-2026-05-01.md` |
| `docs/nextcloud-caldav.md` | MISPLACED (operator-facing setup) | move to `runbooks/nextcloud-caldav.md` |
| `docs/phase-9-completion.md` | STALE (Phase 9 closed Q2 2026) | move to `_retired/phase-9-completion.md` |
| `docs/phase-10-validation-report.md` | STALE (Phase 10 closed) | move to `_retired/phase-10-validation-report.md` |
| `docs/index.md` / `docs/README.md` | CANONICAL | keep |

## Cluster B — `docs/architecture/` (3 files)

| File | Last touched | Category | Disposition |
|------|--------------|----------|-------------|
| `dependency-graph.md` | 3h ago | ACTIVE (Phase 14 D-DOC, NetBox-generated) | needs decision (see Question 1) |
| `mcp-server-architecture.md` | 4d ago | ACTIVE (Phase 14 D-DOC rewrite) | needs decision (see Question 1) |
| `portability.md` | 5d ago | ACTIVE but contains stale "M5" hardware claim | needs decision (see Question 1) + factual fix |

## Cluster C — `docs/audits/capability/` (12 files)

All dated `2026-05-01`, products of D-17-06 agent surface audit + D-17-08 + others.
Files: `ai-platform-dashboard`, `anythingllm`, `homarr`, `homepage`, `obot`,
`open-webui`, `openhands-app`, `sms1obot-mcp-server`,
`sms1obot-mcp-server-shim`, `sportarr`, `topology-api`, `victoriametrics`,
`zabbix` — each `*-2026-05-01.md`.

**Category:** MISPLACED (active per-tool capability audits; canonical home is
`docs/_audit/` per existing convention — `caddy-unbound-parity-2026-05-01.md`,
`opnsense-dns-state-2026-05-03.md`, etc., all live there).

**Disposition:** move 12 files into `docs/_audit/capability/` (preserve
sub-grouping; follows existing `_audit/` flat dated-file pattern with one
sub-dir for the per-tool family).

## Cluster D — `docs/canonical-patterns/` (2 files)

| File | Category | Disposition |
|------|----------|-------------|
| `openproject-connector-usage.md` | ACTIVE (D-17-04 WP-04 authoritative) | move to `architecture-patterns/openproject-connector-usage.md` |
| `plane-connector-usage.md` | STALE (Plane CE retired in WP-17-04-06) | move to `_retired/plane-connector-usage.md` (or delete — see Question 2) |

## Cluster E — `docs/performance/baseline-metrics.md` (1 file)

Phase 10 measurement (April 27, 2026), config "10 MCP servers operational"
— current MCP count is 7 (per CLAUDE.md), so the baseline is structurally
stale.

**Disposition:** STALE → `_retired/performance-baseline-2026-04-27.md`.

## Cluster F — `docs/phases/` (2 files)

| File | Category | Disposition |
|------|----------|-------------|
| `phase-1-10-summary.md` | STALE (Phase 1-10 retro; superseded by `phase-NN/` per-phase docs + `PHASE_LOG.md`) | move to `_retired/` |
| `phase-11-complete.md` | STALE (Phase 11 closed) | move to `_retired/` |

After move, the `docs/phases/` directory becomes empty — delete the
empty dir (it conflicts with the canonical `docs/phase-NN/` pattern
and invites confusion).

## Cluster G — `docs/system-prompts/` (11 files)

Self-contained library: 1 README + 5 `modes/` + 4 `tiers/` + 2 `consumers/`.
D-17-11 deliverable; updated 24h ago. The README declares the directory
canonical for the platform's local-LLM stack ("if a consumer service
ships inline prompt text that differs from the content here, the
content here wins").

**Category:** ACTIVE-CANONICAL but living outside the documented
canonical-paths list in CLAUDE.md.

**Disposition:** needs decision (see Question 3).

## Cluster H — `docs/templates/capability-audit-template.md` (1 file)

D-17-02 active template; consumed by the Cluster C audits.

**Disposition:** MISPLACED → `architecture-patterns/capability-audit-template.md`
(matches the existing pattern home for reusable methodology). After move,
`docs/templates/` becomes empty — delete the empty dir.

## Cluster I — `docs/zabbix/` (7 files)

| File | Last touched | Category |
|------|--------------|----------|
| `initial-setup.md` | 6d | STALE ("EXECUTE MANUALLY" — Zabbix already deployed) |
| `phase-12-complete.md` | 6d | STALE (Phase 12 closed retro) |
| `grafana-integration.md` | 6d | REFERENCE (one-time install instructions) |
| `mac-mini-agent-setup.md` | 6d | REFERENCE (one-time setup) |
| `opnsense-snmp-setup.md` | 6d | REFERENCE (one-time setup) |
| `qnap-snmp-setup.md` | 6d | REFERENCE (one-time setup) |
| `security-checklist.md` | 6d | REFERENCE (operational) |

**Disposition:** consolidate the 5 reference files into a single
`runbooks/zabbix-operations.md` (one stop for "how do I add an SNMP
target / install grafana plugin / verify security"); retire the 2
stale Phase-12-history files to `_retired/`. Delete empty
`docs/zabbix/` dir after.

## Cluster J — `docs/_archive/README.md` + 2 binary-ish artifacts (3 files, not counted in 48)

`README.md` is the archive marker; `plane-final-snapshot-2026-05-02.manifest`
+ `plane-export-2026-05-02.json` are the Plane CE final-snapshot artifacts
preserved by the WP-17-04-06 retirement. **Disposition:** keep as-is;
`docs/_archive/` is its own canonical home for "preserved-but-cold"
data (sibling to `_retired/` for narrative docs).

## Empty / stray dir

- `docs/roadmap/` — empty directory; delete.

---

## Surface-back to operator — three decisions before WP-03 batch

### Question 1 — `docs/architecture/` (Cluster B): canonical sibling, or fold into `architecture-facts/`?

The 3 files are actively maintained Phase-14-D-DOC artifacts. Two paths:

- **(a) Promote `docs/architecture/` to a canonical-paths list entry** in
  CLAUDE.md (sibling to `architecture-facts/`). Rationale: these are
  *generated/derivative* architecture views (NetBox-rendered dependency
  graph, MCP-server architecture overview), not per-subsystem chronicles.
  Different artifact class.
- **(b) Fold into `architecture-facts/`** (rename each file to fit the
  per-subsystem-chronicle pattern: `dependency-graph.md` → keep,
  `mcp-server-architecture.md` → `mcp-servers.md`,
  `portability.md` → `host-portability.md`). Rationale: collapses the
  canonical-paths list (fewer top-level dirs); aligns with the
  "per-subsystem chronicle" doctrine of `architecture-facts/`.

Recommendation: **(b)** — `architecture-facts/` is already the canonical
fact home, and the 3 `architecture/` files are facts about specific
subsystems (dependency graph, MCP servers, host portability). One fewer
canonical dir is one fewer thing for future sessions to remember.

### Question 2 — `docs/canonical-patterns/plane-connector-usage.md` (Cluster D): retire-to-`_retired/` or delete outright?

Plane CE was retired in WP-17-04-06 (commit `726725a` per recent log).
The connector module itself was deleted as part of that retirement (or
should be — worth verifying before deleting the doc). Two paths:

- **(a) `_retired/plane-connector-usage.md`** — preserves history;
  searchable from prior chat references; matches existing `_retired/`
  convention.
- **(b) Delete outright** — `git log` retains it; `_retired/` is for
  retirements where future sessions might need to consult the historical
  shape. Plane is fully unwound; no future consumer.

Recommendation: **(a) `_retired/`** — cheap to keep, matches existing
discipline (e.g. `_retired/sportarr-2026-05-01.md` was kept and ended
up being the restoration playbook for D-17-36 unpark).

### Question 3 — `docs/system-prompts/` (Cluster G): canonical-as-is, or fold somewhere?

The directory is self-contained (README + tiers/ + modes/ + consumers/),
self-described as canonical, and the D-17-11 deliverable. Three paths:

- **(a) Add `docs/system-prompts/` to the canonical-paths list** in
  CLAUDE.md — preserves the directory's self-contained shape; signals to
  future sessions that this is a canonical artifact class.
- **(b) Move under `architecture-patterns/` as a single nested dir**
  (`architecture-patterns/system-prompts/`) — collapses canonical-paths
  count by one. Possible loss of "this is a library not a pattern"
  framing.
- **(c) Move under `runbooks/` as a single nested dir** — wrong fit;
  prompt content is reference, not procedure.

Recommendation: **(a)** — the directory is a library of versioned
content with its own internal taxonomy (tiers/modes/consumers). That's
not a pattern (single canonical recipe) and not a runbook (procedure);
it's reference content. Treat as canonical sibling.

---

## Plan after operator ratifies the 3 decisions (WP-03 sketch)

Single batch commit covering:

1. **Moves (preserved):** Cluster A items, Cluster C 12 files into
   `_audit/capability/`, Cluster D openproject-connector → `architecture-patterns/`,
   Cluster F 2 files → `_retired/`, Cluster H template → `architecture-patterns/`,
   Cluster I 5 reference files consolidated into
   `runbooks/zabbix-operations.md`, Cluster I 2 stale files → `_retired/`,
   plus Cluster B + G + D-stale per ratified decisions.
2. **Empty-dir cleanup:** `docs/phases/`, `docs/templates/`, `docs/zabbix/`,
   `docs/roadmap/` (and `docs/architecture/` + `docs/canonical-patterns/`
   + `docs/audits/` + `docs/performance/` + `docs/system-prompts/` per
   ratified decisions).
3. **Stale-fact correction:** `portability.md` "Mac Mini M5" → "Mac Mini
   M4 Pro" per CLAUDE.md hardware-correction record.
4. **CLAUDE.md canonical-paths list update:** add any newly-canonical
   dirs (per Q1 + Q3 ratifications).

WP-04 then greps the repo for references to the moved/retired files and
either updates pointers or adds short break-link deprecation notices.

WP-05 doctrine: loose-doc retirement as a recurring phase-boundary
deliverable (chronicle in `architecture-facts/integration-audit-doctrine.md`).
