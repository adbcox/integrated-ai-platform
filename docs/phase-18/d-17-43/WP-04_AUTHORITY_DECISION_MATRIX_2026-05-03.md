# D-17-43 WP-04 — CMDB authority decision matrix (surface-back)

**Date:** 2026-05-03
**Status:** SURFACE-BACK — operator decision required before WP-05
full-deliverable scoping.
**Inputs:** `docs/_audit/cmdb-substrate-inventory-2026-05-03.md`
+ `docs/_audit/cmdb-drift-2026-05-03.md`.

---

## What WP-02 + WP-03 surfaced (compressed for decision)

1. **NetBox is the declared authority (ADR-A-014) but only the
   service-catalog axis is actually populated.** IPAM space (IPs,
   prefixes, VLANs) is empty; physical-asset space (racks, primary
   IPs on devices) is empty. The IPAM authority claim in ADR-A-014
   is declaration-only.
2. **inventory.json is the de-facto runtime authority** — auto-
   refreshing every 30min, sole source for runtime state, Docker-net
   IPs, host-port mappings, reverse deps, credential file
   metadata, Caddy admin-API state. Required-consultation rule in
   CLAUDE.md.
3. **yaml is operationally dead** — frozen 2026-04-29, no active
   reader, retained as A-012 fallback only.
4. **D-17-34 retirement landed in inventory.json + repo docs but
   NOT in NetBox.** Worked example of the §18.K scope bullet's
   thesis: declared authority without enforcement = silent drift.
5. **`depends_on` vs `service_dependencies` collision:**
   inventory tracks compose-mechanical startup deps + vault-agent
   sidecars; NetBox tracks operator-stated capability deps. Same
   field name, different facts. 22 cross-substrate disagreements.
6. **Phase-16+ catalog gap:** ~14 services delivered since the
   yaml freeze and the NetBox bulk-import are missing from NetBox
   (inventree*, openproject*, loki, promtail, structurizr,
   upgrade-watcher, mkdocs, vault-server, etc.).
7. **Sidecar semantic-model split:** inventory.json models 24
   `vault-agent-*` sidecars as services; NetBox treats them as
   `vault_paths` cf on the parent. Not drift, but means the
   "service count" on each substrate is incomparable without
   normalization.

---

## Three options

### Option (a) — NetBox per ADR-A-014 (enforce by migrating consumers)

**Stance:** ADR-A-014 stays. NetBox becomes the authority for *all*
catalog axes by populating what's missing and migrating consumers
off inventory.json for declarative reads.

**Implied work:**
1. **NetBox catalog backfill (~6h):** add the ~14 missing
   Phase-16+ services as `ipam/services` records with all custom
   fields populated. Retire the 6+ zombie records (HA family,
   plane*, anythingllm, homarr, obot-shim-*). Resolve the
   zabbix-web port drift to a single canonical.
4. **NetBox IPAM backfill (~8-12h):** import OPNsense Dnsmasq's
   55 host overrides as `ipam/ip-addresses` records; bind devices
   to their primary_ip4; populate prefixes for the LAN
   (192.168.10.0/24), Docker bridge networks, exo Tailscale
   overlay; populate VLANs if any.
6. **Sync mechanism inventory.json → NetBox (~6-8h):** since
   inventory.json refreshes runtime state every 30min, we need a
   periodic NetBox-update script that diffs runtime against
   NetBox catalog and proposes/auto-applies updates. This is the
   mechanism that ADR-A-014 declared but never built.
7. **Consumer migration (~4-6h):** every consumer currently reading
   inventory.json for catalog facts (port, dependency, container
   name, etc.) gets migrated to read from NetBox. inventory.json
   stays for runtime-only attributes (state, started_at, Docker
   net IPs, credential fingerprints).
9. **YAML deletion gate** (~30min once stable): the existing
   §18.C plan — 30 days of zero-drift, A-012 deprecation harness
   passes, then `git rm`.
10. **Drift detection probe (~3-4h):** Grafana panel + structured
    log surfacing NetBox-vs-inventory diff. (Smaller scope than
    in §18.K's original framing because the sync mechanism above
    handles the auto-resolution path.)

**Total:** ~28-37h. Largest scope.

**Risks:**
- Operator manual NetBox edits become the canonical write path
  for ~15 fields per service. Slow + error-prone.
- NetBox IPAM backfill is busywork against an authority claim
  whose actual operational value is dubious (D-17-21 already
  established Dnsmasq as DNS authority; reproducing the data in
  NetBox creates a second source-of-truth for DNS, which is the
  exact failure mode D-17-21 closed).
- Consumer migration breaks the CLAUDE.md "Service Registry
  Consultation Doctrine" — agents would need to consult NetBox
  for some facts and inventory.json for others, with no clear
  rule.

**Doctrine fit:** Strict adherence to ADR-A-014 as written.

---

### Option (b) — inventory.json promoted to canonical (collapse to single substrate)

**Stance:** Reverse ADR-A-014. inventory.json is the canonical
service-state substrate; NetBox is retired (or repurposed for
something else NetBox is actually good at — the
service-catalog axis with operator-stated capability metadata
that doesn't fit the runtime model).

**Implied work:**
1. **Extend inventory.json schema (~4h):** add fields currently
   only in NetBox custom fields — `capability`, `owner`, `adr_ref`,
   `service_notes`, `superseded_by`. Pull from a new
   `config/service-metadata.yaml` (operator-edited) merged into
   the registry at refresh time.
2. **Migrate cross-index ingest (~3h):** `docker/xindex/app/ingest/netbox.py`
   reads NetBox today; switch to inventory.json reader. Same data
   shape after the schema extension.
3. **Migrate topology-api (~2h):** same swap.
4. **Migrate `cmdb_source.py` (~1h):** drop NetBox path; default
   becomes inventory.json (already the de-facto consultation
   path per CLAUDE.md).
5. **NetBox decommission (~2h):** retire the container per
   `retire-service.md` runbook (proposed but not yet authored —
   itself a sub-deliverable).
6. **YAML deletion (~30min):** same gate.
7. **ADR-A-014 superseded by new ADR (~1h):** documents the
   reversal and rationale (declaration-without-enforcement
   pattern; runtime substrate self-refresh wins).

**Total:** ~13-16h. Smallest scope.

**Risks:**
- Loses NetBox's UI for browsing service relationships (currently
  used by humans for orientation). inventory.json is JSON-only;
  the D-17-17 logical-architecture dashboard partially fills the
  gap, but isn't a structured query surface.
- Loses NetBox's API as an externally-consumable read surface
  (xindex-mcp, anyone-with-an-API-token). Replacing with
  inventory.json reader is a code-write task, not an API swap.
- Reverses an Accepted ADR. Doctrine: ADRs are reversible but the
  reversal must itself be ADR-shaped (operator-recall pattern).
- Throws away ~20h of NetBox bulk-import work from Phase 14 D-DOC.

**Doctrine fit:** Aligns with D-17-21's pattern (declaration-vs-
de-facto residue → cut to single authority per axis). Aligns with
CLAUDE.md "Service Registry Consultation Doctrine" already
treating inventory.json as the runtime canonical.

---

### Option (c) — Hybrid (NetBox = declarative axes, inventory.json = runtime axes; explicit boundary)

**Stance:** Codify the *current de-facto split* as policy. Neither
substrate is "the authority"; each owns specific axes. Drift is
defined as "an axis-owning substrate disagrees with reality"; the
non-owner is read-only on that axis.

**Axis ownership:**

| Axis | Owner | Why |
|---|---|---|
| Service existence | inventory.json | runtime-discoverable; auto-refreshing |
| Service display name (human-friendly) | NetBox | operator-curated, rarely changes |
| Capability / owner / ADR ref / superseded_by | NetBox | declarative metadata, no runtime equivalent |
| Vault path references | NetBox | declarative (which secret paths a service is *expected* to read) |
| Container image | inventory.json | runtime-discoverable; image-tag changes are runtime events |
| Ports (host + container, multi-port) | inventory.json | accurate runtime model; NetBox's single-port shape is a schema constraint |
| Caddy routes | inventory.json | sourced from Caddy admin API, auto-refreshed |
| Container Docker-network IPs | inventory.json | runtime-only |
| Service runtime state (running/healthy/exited) | inventory.json | runtime-only |
| `depends_on` (compose-mechanical, startup) | inventory.json | derived from compose graph |
| `service_dependencies` (capability-level, operator intent) | NetBox | operator-stated, not parseable from compose |
| Reverse deps `depended_on_by` | inventory.json | computed from `depends_on` |
| Credential file path + mode + fingerprint | inventory.json | runtime artifact |
| Hardware host catalog (devices, serials) | NetBox `dcim/devices` | declarative metadata; OPNsense is the live IP authority |
| Network IP allocation (LAN, VLANs) | OPNsense Dnsmasq + DHCP | already canonical per D-17-21; NetBox `ipam/*` left empty by design |
| Docker network IPs (Mac Mini local) | inventory.json | runtime-discoverable |

**Implied work:**
1. **Author the axis-ownership doctrine (~3h):** `docs/architecture-facts/cmdb-reconciliation-doctrine.md`. Above table + worked examples + collision-resolution rules ("NetBox says display_name=X, inventory.json says container_name=Y; both kept; consumers querying 'what's the human label' read NetBox, consumers querying 'what's the docker container_name' read inventory").
2. **Extend ADR-A-014 (~1h):** scope NetBox authority to the
   declarative axes only. Reverses the IPAM authority claim
   explicitly (defers to OPNsense per D-17-21). Marks ADR-A-014
   as "amended" rather than "superseded".
3. **NetBox catalog completion (~3-4h):** add the ~14 missing
   Phase-16+ services *for the declarative axes only*
   (capability, owner, vault_paths, service_notes). Retire the 6
   zombie records. Skip IPAM backfill (per axis ownership).
4. **Drift-detection probe (~3-4h):** scheduled comparison of
   inventory.json (runtime) vs NetBox (declarative) per axis.
   Surfaces:
   - service in NetBox but not inventory → declared but not running (retire-record-needed or zombie)
   - service in inventory but not NetBox → running but not declared (catalog-needed)
   - axis-owner disagrees with the other substrate → real drift, fix per doctrine
   Output: Grafana panel + structured log + pre-commit hook.
5. **inventory.json → NetBox auto-sync for declarative-axis-creation (~3-4h):** when inventory.json first surfaces a new service, an automation creates a NetBox `ipam/services` record stub (just the catalog presence; declarative fields stay operator-edited). Closes the "Phase-16+ services missing" pattern structurally.
6. **YAML deletion gate (~30min):** same as options (a) and (b) — retained as written in §18.K. (D-17-43 leaves YAML in place; deletion is a §18.C scope item.)
7. **Sub-doctrine: D-17-34-style retirement adds NetBox CMDB-update step (~1h):** updates `retire-service.md` runbook (which D-17-43 also queues for separate authoring) to include "NetBox catalog removal" in the 5-artifact-class checklist (Vault AppRole, policy, on-disk role-id, secret dir, NetBox record). D-17-34 closeout missed step 5 because the runbook didn't exist.

**Total:** ~14-18h. Mid-scope.

**Risks:**
- Operator/AI must internalize the axis ownership table. CLAUDE.md
  doctrine block grows by ~16 lines.
- The "auto-create NetBox stub on new service" automation is the
  hardest piece; requires NetBox API write path that doesn't
  currently exist on the platform side.
- ADR-A-014 amendment is awkward — the original was Accepted +
  applied + Phase-14-tested; amending instead of superseding
  creates a longer doctrine narrative for future readers.

**Doctrine fit:**
- Codifies what's *already true de-facto* — no operational
  reversal, just policy alignment.
- Mirrors D-17-21's posture (declared vs operator-canonical
  authority resolution by reading the actual operator intent).
- Aligns with CLAUDE.md "Service Registry Consultation Doctrine"
  (inventory.json for runtime) without contradicting ADR-A-014's
  catalog claim (NetBox for declarative).

---

## Comparison matrix

| Axis | Option (a) NetBox-only | Option (b) inventory.json-canonical | Option (c) hybrid |
|---|---|---|---|
| Total effort | 28-37h | 13-16h | 14-18h |
| ADR-A-014 disposition | enforced as written | superseded | amended |
| Operator workflow change | medium (NetBox UI for ~15 fields per service) | small (mostly schema extension to inventory.json's metadata source) | small (axis table is the new mental model; existing tools mostly stay) |
| NetBox role | full-spectrum CMDB | retired or repurposed | declarative-axes-only catalog |
| inventory.json role | runtime-only | full-spectrum substrate | runtime-axes-only |
| OPNsense / Dnsmasq disposition | reproduced into NetBox IPAM (work duplicated) | left as-is | left as-is + axis-owner per D-17-21 |
| Drift-detection scope | larger (NetBox vs inventory + NetBox vs OPNsense) | smaller (inventory.json self-monitors) | medium (per-axis probe) |
| Risk to existing consumers | high (5 NetBox readers + CLAUDE.md doctrine flip) | medium (5 NetBox readers migrated; CLAUDE.md doctrine reinforced) | low (no consumer migration; NetBox readers stay; inventory.json readers stay) |
| §18.K scope-bullet alignment | "NetBox automation: CRUD on NetBox driven by inventory.json refresh" — fits | inverts the §18.K scope bullets | matches §18.K verbatim |

---

## Recommendation

**Option (c) hybrid.**

Rationale:
1. The §18.K scope bullets *already describe option (c)* —
   re-read: "NetBox and `inventory.json` are BOTH authoritative —
   at different layers" + "Authority hierarchy: inventory.json
   wins for *runtime* attributes (port, IP, healthy); NetBox wins
   for *declarative* attributes (capability, owner, ADR linkage)."
   The §18.K author (operator, 2026-05-03) had already decided.
   D-17-43 just confirms by audit and authors the doctrine.
2. Option (a) requires reproducing OPNsense Dnsmasq's authority
   into NetBox IPAM, which is the exact pattern D-17-21 closed
   (residue-based duplicate authority). Doing it deliberately at
   D-17-43 would be a doctrine regression.
3. Option (b) discards real value in NetBox's declarative metadata
   (capability tagging, ADR linkage, operator-stated capability
   deps that aren't compose-mechanical). Reversing ADR-A-014 also
   creates a more disruptive consumer-migration scope.
4. Hybrid is the smallest *new* doctrine — it codifies what's
   already true. Empirical drift catalog (Class C.2 in particular)
   shows the substrates are already operating on the
   "different-axes-different-owners" model, just without explicit
   policy.

WP-05 full scope (gated on operator approval) would be:

- **WP-05.1** — author `docs/architecture-facts/cmdb-reconciliation-doctrine.md` (axis ownership table + worked examples + collision-resolution rules) — 3h
- **WP-05.2** — amend ADR-A-014 (scope NetBox authority to declarative axes; defer IPAM to OPNsense per D-17-21) — 1h
- **WP-05.3** — NetBox catalog completion (add ~14 Phase-16+ services for declarative axes; retire 6 zombie records; resolve zabbix-web port drift) — 4h
- **WP-05.4** — drift-detection probe (per-axis comparison; Grafana panel + structured log) — 4h
- **WP-05.5** — auto-create NetBox stub on new service (inventory.json refresh trigger → NetBox API call for declarative-axis seed) — 4h
- **WP-05.6** — `retire-service.md` runbook (separate D-NN-NN proposed at WP-06; spans D-17-43 + the §18.K bullet for retirement-step coverage) — 2h, deferred
- **WP-05.7** — yaml deletion gate (≥30 days zero drift then `git rm`) — 30min, deferred

**Hard cap: 16h** (covers WP-05.1 through WP-05.5; .6 and .7 split off).

The retire-service.md runbook (originally proposed in D-17-34
Finding 3) is the natural sibling deliverable. Recommendation: a
new `D-17-44` (next free ID) authored as part of WP-06 of D-17-43,
formally promoting the Finding 3 proposal into the framework. Sized
~2-3h doctrine-shaped.

---

## What WP-05 will NOT include

Excluded from D-17-43's full scope per the intake-only constraint
and the §18.K scope bullets that defer to other work:

- **NetBox IPAM backfill** — defer to OPNsense per D-17-21
  (option (c) explicit).
- **NetBox UI / GraphQL features beyond stub-creation** —
  declarative editing stays operator-driven via NetBox UI.
- **Sidecar semantic-model unification** — keep both stores'
  internal models; they're internally consistent.
- **Plane archive cleanup** — orthogonal D-17-31 follow-up
  (`RM-HW-001/002` stranded items, surfaced in D-17-32 Gap F4).
- **Cross-substrate query MCP surface** — D-17-32 Gap X1
  (separate deliverable proposed).
- **OpenProject sync of D-17-43 row** — `--no-op-sync` was
  passed at WP-01 deliberately because the row will be rewritten
  by close-out. Sync runs at close.

---

## Open question for operator

The recommendation above assumes the §18.K author intended option
(c). Confirming explicitly because:

- §18.K bullet 1 (drift-detection probe) and bullet 2
  (reconciliation doctrine) match option (c).
- §18.K bullet 4 (NetBox automation: CRUD driven by inventory.json
  refresh) matches option (c) exactly.
- §18.K bullet 3 (YAML deletion gate) is option-agnostic.

But:
- §18.K's prerequisite list includes "NetBox CMDB stable ✅
  (Phase 13 D-DOC close)" — could be read as endorsing option (a)
  by implying NetBox is ready to be promoted to full authority.
- §18.K's effort estimate (12-18h) sits between option (b) and
  option (c) — closer to option (c) once .6 and .7 are split off.

**Surface-back questions:**
1. Is option (c) the intended shape? (Recommendation: yes, per scope-bullet alignment.)
2. Should `retire-service.md` (D-17-44 candidate) be promoted now alongside D-17-43, or stay as a separate intake?
3. Should ADR-A-014 amendment be authored as ADR-A-014.1 (explicit amendment marker) or as a new ADR that "amends and supersedes the IPAM scope" while "retains and clarifies the catalog scope"?

---

## End of WP-04 surface-back

WP-05 (full deliverable scope) is **gated on operator decision**.
WP-06 (doctrine + chronicle) lands after WP-05, alongside the
Finding 4 chronicle extension that incorporates this drift catalog
as worked examples.

D-17-43 row stays IN PROGRESS in PROJECT_FRAMEWORK.md §9 until
WP-05 + WP-06 deliver the full scope and the substrate fixes
land.
