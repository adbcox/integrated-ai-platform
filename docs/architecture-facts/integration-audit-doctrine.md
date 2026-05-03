# Stack-integration audit — doctrine

Chronicle of the doctrine that governs how subsystem closure is
verified to compose into integrated-system capability. Items here
outlive any single deliverable; new findings append to the bottom
with date + originating WP.

This chronicle exists because Phase 17 produced 25 deliverables that
each closed cleanly on their own scope, yet the operator's
autonomous-coding goal — agent transparently consuming registry /
cross-index / provenance / inventory / asset / project-management
state — was not verified end-to-end. Subsystems work;
system-as-architecture had not been verified. D-17-32 traced the
gap.

---

## Finding 1 — Stack-integration audit becomes recurring at every phase boundary

**Date:** 2026-05-03
**Originating WP:** D-17-32 (autonomous coding stack integration audit)
**Severity:** Doctrine (governs how subsequent phases close)

### What

Subsystem-level closure does not equal integrated-system-level
capability. A deliverable can be DONE on its own scope and still leave
the integrated flow it participates in broken at the seam.

D-17-32 audited Phase 17 against six target flows (Inference,
InvenTree, Asset/firmware, Provenance, Documentation, Project
management) and found 17 gaps — four B-severity blockers
concentrated in seams between subsystems, not within any single
subsystem:

- **F1** — `autonomous-coding` category missing in OpenProject;
  CLAUDE.md doctrine references a filter that returns nothing
  (D-17-31 close-loose-end)
- **X1** — Service registry has no MCP/agent surface; D#25 doctrine
  has no clean execution path (D-17-29 close-extension)
- **C1** — No asset/firmware/OS register exists; the 2026-05-02
  macOS-upgrade incident was the worked example (asset-mgmt family
  intake-doc'd but not framework-authored)
- **F5** — Container health checks validate liveness, not integration
  paths; the 2026-05-03 Sonarr/QNAP SMB mount break (caught by
  operator-observed import failure, not by any platform health
  signal) is the worked example (Phase 6/7 close-extension —
  monitoring scope was container-layer, not integration-layer)

All four are seams *between* subsystems, not failures within them.
Each subsystem (OpenProject, registry, asset-tracking-substrate)
either works or is correctly framed as out-of-scope; the integration
points are what's missing.

### Why it bit us

Phase-17's deliverable charter optimized for closing scoped work
items. Each closeout verified the subsystem in isolation. No
deliverable explicitly took on "is the *combined* surface usable by
an agent without operator hand-holding."

CLAUDE.md doctrine ("filter by category=autonomous-coding";
"convenience reader for registry") asserted integration paths that
agents would follow — but the surfaces those paths assume (the
category, an MCP wrapper) had not been built. Doctrine drift in two
directions: (a) doctrine asserting features that don't exist (F1, F2);
(b) doctrine assuming agent ergonomics around a substrate that's only
operator-ergonomic (X1).

### Doctrine takeaway

**Every phase plan must include a stack-integration audit as a
phase-close deliverable** (named `D-NN-INT` or equivalent). Audit
format:

1. Enumerate target flows for the phase's autonomous-coding posture
   (typically 4-8 flows that compose the integrated system the
   operator is working toward).
2. For each flow: state happy path, structural requirement (what must
   hold for the flow to be integrated, not subsystem-only),
   integration boundary (the seam most likely to be the gap).
3. Trace each flow end-to-end against actual current state. Verify by
   command output, not by inference from "subsystem X is DONE".
4. Classify gaps: B (blocks autonomous coding outright), D (degrades
   quality), N (nice-to-have). Map each gap to: roadmap item present?
   in OpenProject queue? tagged correctly?
5. Surface back to operator BEFORE queueing remediation deliverables.
   Operator confirms backlog ordering matches the autonomous-coding
   goal.
6. Commit audit doc + gap report + prioritized backlog as the
   deliverable; remediation gets queued in the next planning pass,
   not in the audit.

Constraint: audits are AUDIT-only. No code changes during the audit
window. Hard cap on audit duration (D-17-32 used 4h for 6 flows + 16
gaps).

### Sub-doctrine — close-loose-end discipline

When a deliverable's close asserts a doctrine line ("agents can do X
via Y"), the closer MUST verify that Y exists at close time. D-17-31
asserted two lines that did not match reality:

- "filter by `category=autonomous-coding`" — the category did not
  exist
- "convenience: `--query-backlog [--autonomous-coding-only]`" — those
  flags were not implemented

Both were caught by D-17-32 (Gaps F1 + F2). Future deliverables that
update CLAUDE.md or any doctrine surface must include an explicit
verification step ("doctrine line X verified against actual surface Y
on date Z") in the closeout.

### Sub-doctrine — operator-side actions count as gaps

Some integration gaps require operator action that no deliverable can
perform autonomously (e.g., F1 needs the operator to click through
OpenProject UI to create the category). These are gaps; they must
appear in the gap report; they should be surfaced explicitly so the
operator can schedule them. "Operator-only" is not a reason to omit
from the inventory — it's exactly the kind of thing that gets
forgotten without a tracked surface.

### Sub-doctrine — "container `(healthy)` is not `(integration working)`"

Container-level health checks (Docker `HEALTHCHECK`, Uptime Kuma
liveness, Zabbix host-up) validate the subsystem's own surface —
process is alive, port is responding, agent is reachable. They do
NOT validate that the subsystem's outputs flow correctly through to
its downstream consumers.

The 2026-05-03 Sonarr/QNAP SMB mount break is canonical: the SMB
mount used by Sonarr's media library was broken for an unknown
duration. Sonarr's container health check returned green throughout.
Zabbix triggers were green. Uptime Kuma was green. The break was
only surfaced when the operator observed import failures in a
separate troubleshooting session. **No platform health signal caught
it.**

Going forward, any deliverable that asserts "monitoring complete"
must explicitly state which layer is covered:

- **Container liveness** — process up, health endpoint responding,
  registered with monitoring substrate. (Phase 6/7 scope.)
- **Integration-path validation** — a real request flows through the
  subsystem's interface, produces the expected downstream effect,
  and the effect is observed end-to-end. (Gap F5; new family
  proposed.)

The two are not interchangeable; deliverables claiming the former
must NOT be read as covering the latter. Examples of integration-path
checks that belong in this layer:

- Sonarr import: SMB mount reachable + container can read mount +
  new file lands + library refresh picks it up
- Vault → Vault Agent sidecar → container env: secret X in Vault
  matches `/proc/1/environ` reading inside container Y (per Finding
  DD — `docker exec env` is the wrong probe)
- exo cluster → litellm → Open WebUI: a real chat-completion request
  flows through all three layers and returns expected output
- Backup chain: Restic snapshot create + restore-to-tmpdir verify

For autonomous coding this matters because an agent that consults
health-check signal and trusts it will operate on false-positive
state. Recommendations grounded in "service X is healthy, so the
integration through it works" can be wrong.

### Sub-doctrine — negative datapoints count

D-17-32 WP-04 included a parallel-session audit (operator concern that
a different chat window may have created a roadmap artifact). The
audit found nothing was created. Per operator instruction:
**document this as an honest negative datapoint, not as positive
validation.** D-17-31's roadmap → OpenProject sync mechanism remains
untested by external work since its 2026-05-03 close. Future audits
should preserve the same discipline: report what was verified, not
what would have been nice to verify.

### Status

**Active doctrine.** Applies to every phase boundary going forward.
First application: D-17-32 (this deliverable). Next expected
application: Phase-18 close.

Cross-references:
- Audit format reference: `docs/_audit/integrated-stack-target-2026-05-03.md`
- Audit gap report reference: `docs/_audit/integrated-stack-gaps-2026-05-03.md`
- Audit backlog reference: `docs/_audit/integrated-stack-backlog-2026-05-03.md`
- Related: D#22 (architecture-facts as canonical), D#25 (registry consultation), D#23 (capability self-knowledge is suspect)

---

## Finding 2 — False-positive completion regression (F7): audit recommendations require executed validation

**Date:** 2026-05-03
**Originating WP:** D-17-34 (Home Assistant architecture reconciliation)
**Severity:** Doctrine (governs how audits convert to closure)

### What

An audit can reach an operator-confirmed retirement / cleanup / migration recommendation, surface it explicitly in writing, and **the recommendation can still go un-executed** for days or weeks while the documented "the right thing" sits adjacent to the running "wrong thing." Conversation agreement on a recommendation is not the same as the recommendation being done.

This is the F7 pattern (named in D-17-34 context) and now has at least two empirical examples:

1. **Sonarr/QNAP SMB mount break (2026-05-03, surfaced in D-17-32 Gap F5)** — container `(healthy)` for unknown duration while integration was broken; surfaced only by operator-observed import failure, not by any recommendation execution.

2. **Mac Mini Home Assistant container (2026-05-01 → 2026-05-03, D-17-34)** — Phase-15 audit (`docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` §4.7) reached the verdict "the container is a stray" and laid out a 4-step retirement sequence (verify logs → archive volume to QNAP → stop+remove container → update CMDB). Operator confirmed the recommendation in the audit conversation. **None of the four steps were executed.** The container kept running with health checks green for 48 hours while CMDB still listed it; D-17-34 finally closed the gap.

### Why it bit us

Audit-only deliverables are a deliberate anti-pattern against scope creep (audit and remediation are different cognitive modes; mixing them produces low-quality audits). But once the audit closes, the remediation has to actually be queued as its own deliverable AND executed, not just live in a closeout sentence. If the remediation is small enough that "the operator will do it later" feels acceptable, it tends not to happen — there is no gate failing, no stakeholder asking, no test going red. Documentation drift grows in the gap.

The Phase-15 case is canonical: the audit did its job (verdict + executable plan + operator confirmation). What was missing was a tracked deliverable to *execute* the plan. The plan lived in a closeout markdown file and waited.

### Doctrine takeaway

When an audit reaches a remediation recommendation that the operator confirms, **the audit's closeout MUST emit a tracked execution deliverable** (D-NN-MM in framework §9 or RM-NN item in OpenProject) before the audit deliverable can be marked DONE. "Recommended in audit X" is not closure; "executed via deliverable Y" is.

For audits whose recommendations the operator declines (or defers explicitly with a documented why), record the decision in the audit closeout — the disposition is the closure, not the recommendation.

For prior audits whose recommendations were never converted to execution deliverables: if discovered, treat the discovery itself as a new deliverable invocation (D-17-34 is the worked example — discovered the un-executed Phase-15 recommendation; closed it under a fresh deliverable, did not back-date Phase-15).

### Sub-doctrine — health-check signal hides un-executed retirements

Container/service health checks return green for things that should not be running. The Mac Mini HA container had `wget -q -O /dev/null http://localhost:8123 || exit 1` returning healthy throughout the 48-hour gap — health-check success does not distinguish "running because needed" from "running because never retired." This compounds with Finding 1 sub-doctrine ("container `(healthy)` is not `(integration working)`"): now also "container `(healthy)` is not `(supposed to exist)`."

### Status

**Active doctrine.** First application: D-17-34 (this deliverable). Going forward, any audit closeout that includes a recommendation must emit either an execution deliverable ID or an explicit operator-decline disposition.

---

## Finding 3 — Stranded Vault AppRoles outlive their consumers

**Date:** 2026-05-03
**Originating WP:** D-17-34 (HA reconciliation, Vault cleanup step)
**Severity:** Operating-model (governs §6 AppRole provisioning)

### What

Vault AppRoles, policies, on-disk role-id/secret-id files, and Vault Agent sidecar credential directories can persist after the consuming service is removed. Cleanup is not automatic — the AppRole continues to authenticate and the policy continues to grant access until explicitly revoked.

D-17-34 found four artifact classes for the retired HA container:
- AppRole `homeassistant` in `auth/approle/role/homeassistant` (still issuable)
- Policy `homeassistant-policy` in `sys/policies/acl/` (still grantable)
- On-disk role-id + secret-id at `~/.vault-approle/homeassistant/` (mode 600, still authenticatable)
- On-disk delivered credentials at `~/.vault-agent-secrets/homeassistant/` (Vault Agent sidecar output, still readable)
- Repo policy file `config/vault-policies/homeassistant-policy.hcl` (declarative source, still tracked)

All five were live after the container had been removed. `secret/homeassistant/api` (the credential value the AppRole granted access to) is left in place because the canonical .141 hub may consume it; D-17-34's scope was AppRole/role/policy revoke per operator instruction, not data deletion.

This is empirically the same pattern as the D#25 operating-model rule's plane-web example (orphan AppRole provisioned, never consumed). The mirror failure mode is now documented: orphan AppRole *retained* after consumer removal.

### Why it bit us

Service retirement runbooks have not historically enumerated Vault artifact cleanup as a checklist item. Compose-managed retirements stop the container and update the compose file; Vault state drifts into orphan-after-removal because nothing in the compose tooling knows about Vault.

### Doctrine takeaway

Service-retirement deliverables MUST include an explicit Vault cleanup step that revokes:
1. AppRole (`vault delete auth/approle/role/<svc>`)
2. Policy (`vault policy delete <svc>-policy`)
3. On-disk role-id/secret-id directory (`~/.vault-approle/<svc>/`)
4. On-disk Vault Agent secret directory (`~/.vault-agent-secrets/<svc>/`)
5. Repo policy file (`config/vault-policies/<svc>-policy.hcl`)
6. Decision on secret data (`secret/<svc>/*`) — keep if other consumers exist, delete if truly orphan

Item 6 requires consumer-presence verification before deletion (mirror of D#25 operating-model rule for provisioning). Default to keep unless explicitly verified orphan.

Future: an `add-new-service.md`-style `retire-service.md` runbook should encode this checklist. Not auto-created here; proposed for next planning pass.

### Status

**Active doctrine.** First application: D-17-34 (this deliverable, executed cleanly).

---

## Finding 4 — CMDB authority is unenforced; three substrates can disagree silently

**Date:** 2026-05-03
**Originating WP:** D-17-34 (CMDB update step surfaced the three-way drift)
**Severity:** Architecture (governs how agents consume service-state truth)

### What

The platform has three service-state substrates with overlapping scope and no enforcement that they agree:

1. **NetBox CMDB** (`netbox.internal`) — declared authoritative by ADR-A-014 / `CMDB_SOURCE=netbox` default since Phase 14 D-DOC.
2. **`config/service-registry.yaml`** — declared deprecated A-012 fallback retained only for the Phase-14 transition window.
3. **`~/.platform-registry/inventory.json`** — runtime-descriptive registry per D-17-29 (D#25 doctrine substrate); reflects what containers actually exist on the host.

There is no process that ensures these three agree. D-17-34 surfaced the empirical case: the Mac Mini HA container appeared in the runtime registry (correctly — it was running) and in `dependency-graph.md` mermaid (correctly — that doc lived in the repo); whether NetBox carried it was not verified by D-17-34 (the canonical source per ADR-A-014, but D-17-34 did not query NetBox to check).

This is structurally consistent with the broader D-17-32 Gap X1 finding (registry has no MCP/agent surface) — the substrates are not blended into a single agent-consumable view, so an agent or operator consulting one does not see disagreement with another.

### Why it bit us

The Mac Mini HA container is a small case (one container, one stack). The pattern matters because larger drift is harder to detect: if the .145 control plane and .142 compute node and a future Linux/Threadripper host carry different runtime registries and only NetBox is "authoritative," the substrate divergence becomes the silent failure mode.

### Doctrine takeaway

Reconciliation between the three substrates needs a deliverable. Specifically: a periodic check that diffs `~/.platform-registry/inventory.json` (per host) against NetBox device/service records and surfaces drift — services running but not in NetBox, services in NetBox but not running, port/IP disagreements, etc.

This is **proposed but NOT auto-created** per operator instruction at WP-05 invocation. Operator decides scope/priority in next planning pass. Likely shape: `D-17-NN` or `D-18-NN` — "CMDB authority reconciliation." Cross-references D-17-32 Gap X1 (registry MCP surface) — both are facets of the same broader gap (substrate composition).

`config/service-registry.yaml` deprecation (A-012 gate) should also be revisited as part of this work — Phase 14 D-DOC defaulted `CMDB_SOURCE=netbox` but the YAML file has not been deleted; under what gate does deletion happen?

### Status

**Active finding** (not yet doctrine — pending operator decision on remediation scope). First application of the finding: D-17-34. Cross-references: D#25 (registry as substrate), ADR-A-014 (NetBox authority), D-17-32 Gap X1 (registry agent surface), Phase 14 D-DOC (CMDB_SOURCE default flip).

---

## Finding 5 — Roadmap binary artifacts need a substrate, not ad-hoc copies

**Date:** 2026-05-03
**Originating WP:** D-17-37 (substrate-defining deliverable; D-17-35 became its deferred first consumer)
**Severity:** Architecture (governs how AI sessions ingest non-text artifacts referenced by roadmap items)

### What

Roadmap items routinely reference binary artifacts (PDFs, schematics, source-code dumps, vendor datasheets, photos, screenshots). Before D-17-37 there was no canonical storage layer for them. Each ingestion was ad-hoc: a chat upload to context, a manual operator copy somewhere on the Mac Mini filesystem, a `cp` to `/tmp`, or — most commonly — *no persistence at all*: the binary lived only in the conversation that derived facts from it. When a later session needed the original (for re-extraction at different granularity, or for a downstream deliverable consuming more than the previously-derived facts), the operator re-pasted the same file. D-17-35 surfaced this concretely: the Ono Island permit-set PDF was pasted into chat context **four times in a single day** because the prior derivations had persisted facts to memory but had not persisted the source binary anywhere.

### Why it bit us

Three layers of damage:

1. **Operator burden.** Same artifact ingested N times for N deliverables that consume it; scales with cross-deliverable artifact reuse.
2. **Capability ceiling.** Derived-facts memory cannot answer queries that need structured per-page or per-sheet access ("which sheet in the permit set shows the planned camera locations?"). Only the original PDF can. Without a persistent original, downstream deliverables that need that level of detail are blocked or must re-ingest.
3. **F9 symmetry to F7 / F5.** F7 says recommendations require executed validation, not conversation agreement. F5 says container-healthy is not integration-working. F9 says raw inputs require executed persistence, not conversation ingestion. All three are conversation-as-completion regressions in different layers of the work product.

### The substrate (D-17-37)

- **Storage:** QNAP `/share/CACHEDEV2_DATA/downloads/manual/roadmap-artifacts/<phase>/<deliverable>/` (reachable on Mac Mini at `/Users/admin/mnt/qnap-downloads/manual/roadmap-artifacts/...`). Reuses the existing `download` SMB mount for v1 — backlog item: rename to a dedicated `/share/roadmap-artifacts/` share once Finding Y unblocks reliable LaunchAgent registration for SMB mount persistence.
- **Per-deliverable shape:** `source/`, `extracted/`, `annotations/`, `metadata.yaml`. ACL classes (`property`, `schematics`, `vendor-docs`, `source-files`) determine dir/file modes at ingestion.
- **Pointer schema:** `qnap://download/manual/roadmap-artifacts/<phase>/<deliverable>/source/<filename>`. Embedded in framework row freeform-notes column and OpenProject WP description; resolver `scripts/artifact-resolve.sh` translates back to local mount path.
- **Registry axis:** `~/.platform-registry/artifacts.json` + per-deliverable `~/.platform-registry/artifacts/<D-NN-NN>.json` — sibling to D-17-29 service axis; same convention. `scripts/platform-registry/refresh.sh` chains to `refresh-artifacts.sh` so launchd refresh keeps both indices fresh.
- **Ingestion:** single script `scripts/artifact-ingest.sh <D-NN-NN> <local-path> [--class CLASS] [--no-index]` — moves (not copies) the file into the canonical path, sets perms per class, emits a `metadata.yaml` stub if absent, refreshes the registry, prints the qnap:// pointer to stdout.

### Backup posture (deliberate non-coverage)

Restic's repo target is MinIO **on the QNAP itself** (`s3://192.168.10.201:9000/backups`). Adding the artifact root to `BACKUP_DIRS` would back up QNAP data to the same QNAP — single-host failure loses both copies. **Doctrine: artifact persistence is QNAP RAID + native snapshots, not Restic.** Off-host artifact replication, if desired later, is a separate deliverable (cross-host replication target, e.g., Mac Studio external drive or off-site target — not in D-17-37 scope).

### Substrate-defining deliverable exemption pattern

D-17-37 itself does not retrofit through its own substrate. The artifact axis is meta about other deliverables' binaries; D-17-37 produces no binary it would index. **Doctrine: a substrate-defining deliverable is exempt from being its own first consumer.** The first consumer must be a real deliverable that uses the substrate naturally. For D-17-37, that is D-17-35 (Ono Island property plans); the retrofit completes via a single operator command (`scripts/artifact-ingest.sh D-17-35 ~/Documents/property/ono-island/source/Cox_V3_-_CD_05__Permit_Set__All__signed___25-03-10__House.pdf --class property`) once the operator drops the PDF on the host filesystem.

### smbfs cleanup quirk (minor)

When the registry-refresh emitter or operator removes a deliverable directory from the QNAP-mounted share, smbfs may leave `.smbdeleteAAAxxxxxx.N` placeholder files in the directory that Linux/macOS reports as "Resource busy" until the QNAP-side lock releases. The artifact-axis emitter filters dotfiles (`f.name.startswith(".")`), so the registry index correctly shows zero source files; the placeholder purges itself once smbfs releases the lock. Not a substrate bug; documented here so future operators do not chase it.

### Status

**Active doctrine.** First substrate validation: synthetic D-17-37 self-test (smoke pass — ingest emitted qnap:// pointer, resolver resolved it, registry indexed it). First real-deliverable retrofit: D-17-35 (deferred, single operator command). Cross-references: D#25 (registry doctrine), ADR-A-014 (NetBox out of scope for artifacts), D-17-32 Gap F9 (the gap this closes), D-17-35 (first consumer), Finding Y (SMB mount persistence — blocks dedicated-share rename backlog item).

### Flow-layer closure (D-17-39, 2026-05-03)

D-17-37 closed Gap F9 at the **storage** layer: artifacts now have a durable, indexed home with stable `qnap://` pointers. But the **path from operator intent → substrate** remained a manual two-step (operator drops file on filesystem, operator runs `artifact-ingest.sh`). D-17-35 was the live evidence: the property-plans PDF stayed chat-only after substrate landed because the operator filesystem action was the gating step.

D-17-39 closes Gap F9 at the **flow** layer with `scripts/roadmap-create.sh`, an operator-facing surface that composes (a) D-17-37 substrate ingestion, (b) PROJECT_FRAMEWORK.md row insertion, and (c) OpenProject WP creation into one self-contained transaction. The operator types the artifact path *once* (typed to bash, consumed atomically); the script handles canonical-path placement, registry refresh, framework row composition with embedded `qnap://` pointer, and OP sync. Operator never touches `/Users/admin/mnt/qnap-downloads/...` paths and never invokes `artifact-ingest.sh` directly for new deliverables.

**Surface decision (WP-02):** three candidates evaluated — (a) CLI wrapper, (b) OpenProject attachment hook, (c) MCP tool exposed via xindex-mcp. (a) selected on cost / risk / doctrine grounds: composes existing primitives, no new long-running process, no new credential consumption, fits in a 60-min implementation budget, preserves D-16-02.A "repo-owned docs are canonical" doctrine. (b) explicitly rejected on doctrine inversion grounds (would invert source-of-truth direction by making OP the authoritative origin). (c) deferred to a future deliverable once chat-attachment-pickup primitive is reliable in this surface.

**Substrate-defining vs consumer retrofit asymmetry (Path 1 worked example, WP-04):** D-17-37's first-consumer was itself (synthetic self-test); that's the substrate-defining-deliverable exemption. D-17-39's first-consumer also resolved via synthetic — but for a different reason: D-17-35's real artifact (the property-plans PDF) was still chat-only at WP-04 execution time. Closing D-17-35 on a placeholder file would have been false-positive completion (Gap F7 territory: "deliverable closed, work not actually done"). Resolution: validate D-17-39's flow end-to-end with a placeholder, restore D-17-35's IN PROGRESS state with a note describing the validation, remove the placeholder from canonical store. Doctrine: **substrate-defining deliverables retrofit cleanly via synthetic; consumer deliverables retrofit only with real artifact.** Phase 17 advanced 27/31 → 28/31 (D-17-39 only); D-17-35 stays IN PROGRESS pending real PDF.

**Backlog (deferred, not blocking):** (1) `roadmap-create.sh --update-existing` flag for closing IN PROGRESS rows when their gating artifact lands (~30 min when needed; D-17-35's expected close path); (2) MCP-tool surface (`roadmap_create_with_artifact` exposed via xindex-mcp) once chat-attachment-pickup primitive is reliable in this surface.

**Active doctrine.** Cross-references: D-17-37 (storage-layer F9 closure), D-17-35 (first deferred consumer; awaits real artifact), D-16-02.A (repo-owned-canonical doctrine that disqualified surface (b)), D-17-31 (PHASE_ROADMAP.md → OpenProject sync that the script depends on for OP WP creation).

---

## Finding 6 — Retirement audits stop at the integration layer they personally witnessed; consumer pipelines have phases the auditor never traced (F10)

### What

A retirement audit produces dispositive evidence about ONE phase of a consumer pipeline, then writes a record that implicitly authorizes treating *all* phases as understood. When the same record is later used as a restoration playbook, the un-traced phases surface as latent defects during unpark.

D-17-36 (Sportarr unpark) is the canonical worked example. Four distinct latent defects were discovered post-unpark, each in a phase the 2026-05-01 retirement record (`docs/_retired/sportarr-2026-05-01.md`) had not personally traced:

1. **Indexer URL phase.** Retirement record cited `BaseUrl` column rewrite (`UPDATE Indexers SET BaseUrl = REPLACE(...)`); actual schema column is `Url`. The audit had read the column from a Prowlarr export, not from `sportarr.db`. Sportarr's indexer wiring uses `Indexers.Url`. Restoration step 2 was unrunnable as written.

2. **Indexer ApiKey phase.** Retirement record's restoration steps did not mention ApiKey at all. On restore, all 5 indexers had stale ApiKey (`9b7ed91b...`) that no longer matched live Prowlarr's key (`620626ef...`). Result: Url fix landed correctly, but every fetch returned `401 Unauthorized` until a separate sweep `UPDATE Indexers SET ApiKey = '<live>'`. Phase: indexer→Prowlarr authentication, never traced because retirement-era container wasn't authenticated end-to-end either.

3. **Bind-mount phase.** Retirement record's compose block had `/sports:/data` only — no `/downloads` bind. The canonical Sonarr/Radarr arr-stack pattern is `/Users/admin/mnt/qnap-downloads:/downloads` (plural) for the seedbox-replicated tree, `/Users/admin/mnt/qnap-downloads/data:/data` for the media root. Retirement-era audit looked at runtime `docker inspect` output, not at sibling-pattern conformance. First unpark attempt also used `/download` (singular), which was caught by operator pushback.

4. **Storage-layout phase.** Retirement record's `/sports:/data` framing implied Sportarr stored content at `/data/{TV-style hierarchy}`. Actual Sportarr behavior: stores at `/data/{Sport}/Season {Year}/file.mkv` — flat per-sport, no `/data/media/sports/` parent. Plex library γ-recreate at `/share/CACHEDEV2_DATA/data/media/sports` was based on operator projection of media-tree convention rather than tracing actual Sportarr import behavior. Required γ'.3 reconfiguration (RootFolder add `/data/media/sports`, container-mediated `mv` of existing files, EventFile/Events DB FilePath updates, RootFolder remove `/data`) post-unpark to align with the canonical Sonarr/Radarr arr-stack hierarchy `/data/media/{type}/<show>/Season N/`.

### Why it bit us

A retirement-era audit is *evidence*-driven: trace what failed, document the dispositive datapoint, leave a reversible record. Once written, the record becomes an *authoritative* restoration playbook even though restoration is a fundamentally different operation than retirement. Retirement decommissions one phase that already broke; restoration must verify ALL phases work. Latent defects in un-traced phases stay latent because the retirement-era container never exercised them.

For Sportarr specifically: the retirement audit traced `indexer fetch failure → 6,769 silent failures → low engagement → PARK-RETIRE`. Storage layout, bind-mount canonical pattern, ApiKey freshness, and column-name accuracy were never traced because the retirement-era container never imported a single file successfully — those phases of the pipeline never ran.

### Doctrine takeaway

**Retirement-record-as-restoration-playbook is structurally unsound.** Two complementary fixes:

1. **Retirement audits trace ALL phases, not just the failed one.** Even when a phase doesn't matter for the retirement decision, document its current state so a future restoration has a baseline to verify against. Cost: ~15-30 minutes additional audit time. Prevents: 4 latent defects discovered in real time during unpark.

2. **Restoration audits MUST exist as a separate doctrine step.** The retirement record is one input; current sibling-pattern conformance + live-credential freshness + actual-storage-layout-vs-projected are independent checks. D-17-36 implicitly authored this audit during execution; future unparks should structure it explicitly:
   - Pre-flight phase 1: Re-read all schema columns referenced in the retirement playbook against the preserved data substrate. Retirement-era column names may have changed; retirement-era column names may have been wrong.
   - Pre-flight phase 2: Audit canonical-pattern conformance against current sibling services (Sonarr/Radarr for arr-stack) — bind mounts, network membership, env vars, security_opt.
   - Pre-flight phase 3: Refresh all credential references against live secret stores; retirement-era values are presumptive-stale.
   - Post-bringup phase: Trace the consumer pipeline end-to-end (indexer→grab→download→import→library→playable) before declaring restoration complete. Container `(healthy)` is not `(restoration working)` (per Finding 1 sub-doctrine).

### Sub-doctrine — container-mediated `mv` is canonical for in-Sportarr file relocation

Discovered during γ'.3 step 3-4. When moving files within the SMB-overlaid `/data` tree, two operationally distinct paths exist:

- **Host-side `mv`** via `/Users/admin/mnt/qnap-downloads/...`. Files surface to host as `admin:staff`, but UID translation gap means files surface to container as `root:root 0700`. Move succeeds at SMB protocol layer but Sportarr's filesystem watcher may not observe the change consistently.
- **Container-mediated `mv`** via `docker exec sportarr mv ...`. Move executes at the SMB protocol layer (same as Sonarr's import-by-move per `docs/runbooks/qnap-downloads-mount.md` F3 reference), AND Sportarr's filesystem watcher observes the change as an in-process FS event. Result: `Events.FilePath` and `EventFiles.FilePath` auto-update without manual SQL.

**Doctrine:** for in-arr-stack file relocations within a tree the container can see, prefer container-mediated `mv` over host-side `mv`. The watcher-driven DB auto-update reduces the manual UPDATE surface and prevents path-rewrite drift. (Caveat: watcher only auto-updates the `FilePath` text; release-parser misclassification — Finding 7 below — is NOT auto-corrected by file moves.)

### Status

**Active doctrine.** Worked example: D-17-36 Sportarr unpark, all four latent-defect phases (indexer URL column name, indexer ApiKey staleness, bind-mount canonical pattern, storage-layout projection) discovered and remediated in real time. Retirement record `docs/_retired/sportarr-2026-05-01.md` patched in WP-08: `BaseUrl → Url` schema correction in restoration step 2; ApiKey-refresh sub-step added; bind-mount block updated to canonical `/downloads` (plural) + `/data`; storage-layout note added pointing at γ'.3 reconfiguration as historical evidence that operator projection of the media-tree convention required post-unpark correction.

Cross-references: D-17-36 (the worked example), Finding 1 (sub-doctrine "container `(healthy)` is not `(integration working)`" — directly applicable), Finding 2 (false-positive completion regression — restoration without phase-by-phase verification is the same anti-pattern as audit-recommendations-without-execution), `docs/runbooks/qnap-downloads-mount.md` (F3 SMB import-by-move reference).

---

## Finding 7 — Release-parser confidence is independent from event-correctness; 100% match score can still misclassify (F12)

### What

D-17-36 WP-07 surfaced a defect where a Sportarr indexer fetched the **Miami Grand Prix Qualifying** .mkv at 100% release-match confidence, but linked the EventFile to **Event 1572 = "Australian Grand Prix Qualifying" (2026)** — a different round entirely. State at discovery (post-γ'.3 file relocation):

```
EventFile id=1, EventId=1572 (Australian Qualifying)
  FilePath = /data/media/sports/Formula 1/Season 2026/
             Formula1.2026.Miami.Grand.Prix.Qualifying.1080p.AHDTV.x264-DARKSPORT.mkv

Event 1572 "Australian Grand Prix Qualifying" Round=3 Date=2026-03-15 — HasFile=1 (wrong)
Event 1597 "Miami Grand Prix Qualifying"      Round=4 Date=2026-05-02 — HasFile=0 (also wrong)
```

The filename contains `Miami` unambiguously; Sportarr's release-parser still picked the first 2026 F1 Qualifying event by date order (Australia is round 3, Miami is round 4). Round / venue tokens were either not parsed or not weighted against the event date-ordered candidate list.

### Why it bit us

Release-match confidence and event-correctness are different signals. The release-grab path produced a high-confidence fetch (release-name regex matched, year matched, sport matched), but the event-mapping path (which round, which qualifying session) used a weaker heuristic that fell back to the first-eligible-monitored event. Result: file imported, container healthy, DB consistent (`HasFile=1` on a row), but the row was the wrong event.

This is structurally different from F10 (retirement-audit phase coverage gaps) — F10 is about the audit not tracing a phase; F12 is about a runtime phase producing a confidently-wrong result that no audit would have caught because the failure mode is internal to a working component.

The defect was masked initially by the half-import framing during WP-07 scoping: "file on disk, no DB row" was the working hypothesis. Actual state was "file on disk, DB row exists but points at wrong event." If the scoping question had been "is the imported file linked to the correct event?" rather than "did the import complete?", the misclassification would have surfaced immediately.

### Doctrine takeaway

**Health checks that assert pipeline completion (HasFile=1, FilePath set) do not assert pipeline correctness (linked to the right event).** F5/F8 family integration health checks (per Finding 1) need a correctness layer in addition to the completion layer. For Sportarr specifically:

- **Completion check** (already canonical): for each monitored event in current season, expect HasFile=1 within N days of EventDate.
- **Correctness check** (new): for each EventFile row, parse the filename for venue/round tokens; assert the linked Event's Title contains the same venue token. Mismatch is a soft failure (operator review) not a hard failure (no auto-relink), because correct relink requires release-name parsing logic that may itself be fallible.

A correctness check would have surfaced the Miami→Australia misclassification without needing a Plex-side end-to-end probe, because the filename and the Event.Title disagree on a token (`Miami` vs `Australian`) that any naïve string compare would catch.

### Sub-doctrine — release-parser correctness is a separate doctrine layer from indexer reachability

Sportarr's release-parser is upstream-frozen (linuxserver/sportarr image; we don't fork). Mitigations live on the consumer side:

1. **Filename-vs-event-title token mismatch probe** (sketch above) — runs as a periodic check, surfaces mismatches as a Sportarr-tag or external dashboard signal.
2. **Pre-import naming-format hint** — if Sportarr exposes a way to weight venue tokens in its parser, that's a config-level remediation. Out of scope for D-17-36; investigate as Phase 18 backlog.
3. **Operator-visible "recent imports" surface** — a one-screen view of "what arrived in the last 7 days, mapped to which event" gives the operator a chance to spot a misclassification before the event date passes. F1 cadence (one round/weekend) makes manual review feasible; high-volume sports would need automation.

### Status

**Active doctrine.** Worked example: D-17-36 WP-07 Miami Qualifying misclassification, remediated by manual `UPDATE EventFiles SET EventId = 1597 WHERE Id = 1` + `UPDATE Events SET HasFile=0, FilePath=NULL WHERE Id=1572` + `UPDATE Events SET HasFile=1, FilePath=...` for Event 1597. DB snapshot pre-relink at `/Users/admin/sportarr-db-pre-wp07-relink-2026-05-03.snapshot`. Plex library 4 (Sports) post-relink shows both Sprint AND Qualifying at canonical paths.

Cross-references: D-17-36 (the worked example), Finding 1 (Gap F5 family — integration health checks; correctness layer is a new sub-family), Finding 6 / F10 (retirement-audit phase coverage; this defect would not have been caught by a more thorough retirement audit because it's a runtime-internal failure mode). Backlog: filename-vs-event-title mismatch probe (~3-4h, Phase 18 candidate); Plex movie-mode hierarchy reconfig (Plex agent change, ~1-2h, Phase 18 candidate — the unpark used `tv.plex.agents.none` + `Plex Video Files` scanner because Sportarr's flat-per-sport storage does not match TV-shows agent expectations).
