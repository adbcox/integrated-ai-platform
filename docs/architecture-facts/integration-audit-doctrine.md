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
2. **`config/service-registry.yaml.DEPRECATED`** — declared deprecated A-012 fallback retained only for the Phase-14 transition window.
3. **`~/.platform-registry/inventory.json`** — runtime-descriptive registry per D-17-29 (D#25 doctrine substrate); reflects what containers actually exist on the host.

There is no process that ensures these three agree. D-17-34 surfaced the empirical case: the Mac Mini HA container appeared in the runtime registry (correctly — it was running) and in `dependency-graph.md` mermaid (correctly — that doc lived in the repo); whether NetBox carried it was not verified by D-17-34 (the canonical source per ADR-A-014, but D-17-34 did not query NetBox to check).

This is structurally consistent with the broader D-17-32 Gap X1 finding (registry has no MCP/agent surface) — the substrates are not blended into a single agent-consumable view, so an agent or operator consulting one does not see disagreement with another.

### Why it bit us

The Mac Mini HA container is a small case (one container, one stack). The pattern matters because larger drift is harder to detect: if the .145 control plane and .142 compute node and a future Linux/Threadripper host carry different runtime registries and only NetBox is "authoritative," the substrate divergence becomes the silent failure mode.

### Doctrine takeaway

Reconciliation between the three substrates needs a deliverable. Specifically: a periodic check that diffs `~/.platform-registry/inventory.json` (per host) against NetBox device/service records and surfaces drift — services running but not in NetBox, services in NetBox but not running, port/IP disagreements, etc.

This is **proposed but NOT auto-created** per operator instruction at WP-05 invocation. Operator decides scope/priority in next planning pass. Likely shape: `D-17-NN` or `D-18-NN` — "CMDB authority reconciliation." Cross-references D-17-32 Gap X1 (registry MCP surface) — both are facets of the same broader gap (substrate composition).

`config/service-registry.yaml.DEPRECATED` deprecation (A-012 gate) should also be revisited as part of this work — Phase 14 D-DOC defaulted `CMDB_SOURCE=netbox` but the YAML file has not been deleted; under what gate does deletion happen?

### Status

**Active finding** (not yet doctrine — pending operator decision on remediation scope). First application of the finding: D-17-34. Cross-references: D#25 (registry as substrate), ADR-A-014 (NetBox authority), D-17-32 Gap X1 (registry agent surface), Phase 14 D-DOC (CMDB_SOURCE default flip).

### 2026-05-03 intake extension (D-17-45 WP-03 worked examples)

D-17-45 intake audit quantified the three-way drift and supplied
concrete examples:

- Service-ID divergence at baseline: NetBox=77, YAML.DEPRECATED=75,
  inventory.json=74.
- NetBox-only vs YAML: `xindex` and `xindex-mcp` exist in NetBox but
  not in YAML fallback.
- Runtime-only service set: 42 IDs present in inventory.json but
  absent from both NetBox and YAML (examples: `openproject`,
  `inventree`, `loki`, `promtail`, `traefik`).
- Declarative-only set: 45 IDs present in NetBox+YAML but absent
  from runtime inventory (examples: `homeassistant-container`,
  `anythingllm`, multiple `obot-shim-*`).
- Attribute conflicts on shared IDs: dependency edges diverge
  (`control-plane`, `homepage`) and port semantics diverge (`netbox`
  internal 8080 vs host-mapped 8084 in runtime substrate).
- IPAM authority gap: NetBox IP/prefix/vlan counts are all zero while
  OPNsense Dnsmasq has 55 host records (6 unique IPs) and runtime
  inventory carries 51 internal IP entries across 14 docker networks.

These are not one-off errors; they are structural differences in
schema intent + update cadence + consumer usage, and they directly
justify the authority-decision gate in D-17-45 WP-04.

Sub-doctrine formalization: **CMDB authority requires consumer
enforcement, not declaration alone.** ADR-A-014's declaration is
necessary but insufficient until every consumer is explicitly bound to
the correct substrate layer (intent vs runtime) and drift checks run
continuously.

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

**Backlog status (2026-05-03 update):** (1) `roadmap-create.sh --update-existing` flag — **landed 2026-05-03**. Implementation: mode-aware default status (DONE for update, IN PROGRESS for create); `--artifact` required; row located by `^| <ID>:` prefix; existing title cell preserved verbatim; reference column augmented with qnap:// pointer + `Closed via --update-existing <date>` note; status word flipped in place; idempotent re-run with same artifact + same target status against an already-closed row exits 0 with no-op message. Rejection paths: missing `--artifact` (exit 64), row not found (exit 68), row already DONE/DEFERRED with different artifact (exit 70). Validated end-to-end via D-17-35 dry-run + three rejection-path tests. OP sync picks up the row change automatically through its diff-against-external_id mechanism — no separate PATCH path needed. (2) MCP-tool surface (`roadmap_create_with_artifact` exposed via xindex-mcp) — still deferred pending chat-attachment-pickup primitive reliability.

**Active doctrine.** Cross-references: D-17-37 (storage-layer F9 closure), D-17-35 (first deferred consumer; awaits real artifact), D-16-02.A (repo-owned-canonical doctrine that disqualified surface (b)), D-17-31 (PHASE_ROADMAP.md → OpenProject sync that the script depends on for OP WP creation).

---

## Finding 6 — Retirement audits stop at the integration layer they personally witnessed; consumer pipelines have phases the auditor never traced (F10)

### What

A retirement audit produces dispositive evidence about ONE phase of a consumer pipeline, then writes a record that implicitly authorizes treating *all* phases as understood. When the same record is later used as a restoration playbook, the un-traced phases surface as latent defects during unpark.

D-17-36 (Sportarr unpark) is the canonical worked example. Five distinct latent defects were discovered post-unpark, each in a phase the 2026-05-01 retirement record (`docs/_retired/sportarr-2026-05-01.md`) had not personally traced:

1. **Indexer URL phase.** Retirement record cited `BaseUrl` column rewrite (`UPDATE Indexers SET BaseUrl = REPLACE(...)`); actual schema column is `Url`. The audit had read the column from a Prowlarr export, not from `sportarr.db`. Sportarr's indexer wiring uses `Indexers.Url`. Restoration step 2 was unrunnable as written.

2. **Indexer ApiKey phase.** Retirement record's restoration steps did not mention ApiKey at all. On restore, all 5 indexers had stale ApiKey (`9b7ed91b...`) that no longer matched live Prowlarr's key (`620626ef...`). Result: Url fix landed correctly, but every fetch returned `401 Unauthorized` until a separate sweep `UPDATE Indexers SET ApiKey = '<live>'`. Phase: indexer→Prowlarr authentication, never traced because retirement-era container wasn't authenticated end-to-end either.

3. **Bind-mount phase.** Retirement record's compose block had `/sports:/data` only — no `/downloads` bind. The canonical Sonarr/Radarr arr-stack pattern is `/Users/admin/mnt/qnap-downloads:/downloads` (plural) for the seedbox-replicated tree, `/Users/admin/mnt/qnap-downloads/data:/data` for the media root. Retirement-era audit looked at runtime `docker inspect` output, not at sibling-pattern conformance. First unpark attempt also used `/download` (singular), which was caught by operator pushback.

4. **Storage-layout phase.** Retirement record's `/sports:/data` framing implied Sportarr stored content at `/data/{TV-style hierarchy}`. Actual Sportarr behavior: stores at `/data/{Sport}/Season {Year}/file.mkv` — flat per-sport, no `/data/media/sports/` parent. Plex library γ-recreate at `/share/CACHEDEV2_DATA/data/media/sports` was based on operator projection of media-tree convention rather than tracing actual Sportarr import behavior. Required γ'.3 reconfiguration (RootFolder add `/data/media/sports`, container-mediated `mv` of existing files, EventFile/Events DB FilePath updates, RootFolder remove `/data`) post-unpark to align with the canonical Sonarr/Radarr arr-stack hierarchy `/data/media/{type}/<show>/Season N/`.

5. **Prowlarr-side mirror record phase (D-17-36 follow-on, 2026-05-03).** D-17-36 fixed Sportarr's `Indexers.Url` and `Indexers.ApiKey` columns inside `sportarr.db` (consumer side). It did not audit the **upstream Prowlarr Application record** that mirrors the same wiring (Prowlarr → consumer). On post-D-17-36 inspection, Prowlarr's Application record for Sportarr held `prowlarrUrl=http://localhost:9696` AND `baseUrl=http://mac-mini.internal:1867` — both non-canonical. Symptoms: ApplicationIndexerSync fullSync runs were appending duplicate indexer rows in Sportarr (8 rows for 5 Prowlarr slots) instead of updating the existing rows, because Prowlarr couldn't reach itself via `localhost:9696` from inside its own container, breaking the round-trip identity check that distinguishes "create new row" from "update existing row". Bilateral fix required: PUT /api/v1/applications/1 with `prowlarrUrl=http://prowlarr:9696` (container DNS) + `baseUrl=http://sportarr:1867` (Sportarr's by-design custom port, NOT 8989), then DELETE the 3 duplicate Sportarr indexer rows, then re-run forceSync to confirm idempotent state. Phase: bidirectional sync record, never traced because D-17-36 audited only the consumer side.

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

### Sub-doctrine — bidirectional sync records require bilateral fix; single-side fix leaves drift

D-17-36 fixed Sportarr's consumer-side wiring (`Indexers.Url` + `Indexers.ApiKey` in `sportarr.db`) without auditing the upstream Prowlarr Application record that mirrors the same wiring. The defect surfaced two days later: Prowlarr's Application record still held `localhost:9696` (non-canonical) and `mac-mini.internal:1867` (LAN-routed instead of container-DNS). Each time ApplicationIndexerSync ran, Prowlarr couldn't recognize its own existing rows in Sportarr (because the round-trip URL no longer matched what Prowlarr believed it had written), so it created NEW rows instead of updating, producing duplicate indexer entries (8 rows for 5 Prowlarr slots).

**Pattern:** when two services hold mirrored configuration (Prowlarr Application record ↔ Sportarr Indexer rows; in general, any A↔B sync), an audit on side A alone leaves side B as latent drift. The sync engine does not "self-heal" the un-audited side because sync engines treat their own stored URLs as authoritative — they reconcile *content*, not their own *identity beliefs*. A single-side fix can appear successful (consumer-side test passes) while the upstream record drifts further on every sync run.

**Doctrine:** for retirement audits and restoration audits of services that hold mirrored config in an upstream coordinator (Prowlarr↔Sonarr/Radarr/Sportarr; any Application/Coordinator pattern), the audit MUST trace BOTH sides:
- Consumer-side: schema columns hold canonical URL+key.
- Upstream-side: Application record holds canonical URL+key for the SAME consumer.

If the two diverge, the upstream record is presumptively the drift source (because the upstream is what writes the consumer side on sync; the consumer side gets refreshed on every fullSync, the upstream side only on operator edit). Verify both, fix both. Worked example: D-17-36 follow-on 2026-05-03 — `prowlarrUrl=http://localhost:9696` + `baseUrl=http://mac-mini.internal:1867` → `prowlarrUrl=http://prowlarr:9696` + `baseUrl=http://sportarr:1867`; DELETE 3 duplicate indexer rows; re-fullSync confirms idempotent state.

**Sub-finding revision (D-17-50, 2026-05-03) — two-key auth model, not single-master drift.** The earlier single-master comparison frame was incorrect for Sonarr/Radarr. Empirical recovery sequence in D-17-50 showed:
- Sonarr and Radarr were functionally broken (`release query` empty/error + indexer-unavailable health), then recovered after Prowlarr-side `Application` DELETE+recreate + forced `ApplicationIndexerSync`.
- Post-recovery, Sonarr/Radarr consumer indexer-row apiKey hashes remained `07ab59f4731b` (did **not** converge to Prowlarr master hash `a3051e37707a`) while functional probes returned data again.
- Sportarr rows remained `a3051e37707a`, indicating implementation-dependent key-path behavior across application types.

**Doctrine update:** per-consumer apiKey freshness checks must use **functional auth probes** as the remediation trigger (consumer release endpoint via proxied indexers; `HTTP 401` is actionable). Hash audits remain useful observability, but only with per-implementation expected-key resolution; hash mismatch to Prowlarr master alone is not sufficient evidence of drift for Sonarr/Radarr-class applications.

**Mechanism doctrine (D-17-50 worked example #6):** consumer-side indexer-row edits are not authoritative when Prowlarr owns sync. Structural remediation must originate Prowlarr-side (recreate or equivalent rewrite of the `Application` record), then force `ApplicationIndexerSync`, then re-probe functionally.

### Status

**Active doctrine.** Worked examples: D-17-36 Sportarr unpark (4 latent-defect phases — indexer URL column name, indexer ApiKey staleness, bind-mount canonical pattern, storage-layout projection); D-17-36 follow-on 2026-05-03 (5th latent-defect phase — Prowlarr-side Application record drift, bilateral-sync sub-doctrine, fullSync-creates-duplicates-on-broken-URL pattern). Retirement record `docs/_retired/sportarr-2026-05-01.md` patched in WP-08: `BaseUrl → Url` schema correction in restoration step 2; ApiKey-refresh sub-step added; bind-mount block updated to canonical `/downloads` (plural) + `/data`; storage-layout note added pointing at γ'.3 reconfiguration as historical evidence that operator projection of the media-tree convention required post-unpark correction. Phase 18 18.E backlog item authored: Prowlarr Application URL canonicalization sweep (sweep all Application records for `localhost:` or `<host>.internal:` patterns; rewrite to container-DNS; verify by post-fix fullSync producing no new rows) + per-consumer apiKey-freshness probe (hash-compare consumer indexer rows against `<Prowlarr config.xml>.ApiKey`, flag drift).

Cross-references: D-17-36 (the original worked example), D-17-36 follow-on 2026-05-03 (5th defect + bilateral-sync sub-doctrine), Finding 1 (sub-doctrine "container `(healthy)` is not `(integration working)`" — directly applicable), Finding 2 (false-positive completion regression — restoration without phase-by-phase verification is the same anti-pattern as audit-recommendations-without-execution), `docs/runbooks/qnap-downloads-mount.md` (F3 SMB import-by-move reference).

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

---

## Finding 8 — Integration health check failures cluster at three distinct layers; conflating them produces wrong remediations

D-17-38 worked example. Self-heal cycle reported `5 issues, 0 fixes` indefinitely; symptoms looked like one failure ("services unhealthy") but were three independent failures that happened to share an output channel.

### Layer taxonomy (D-17-38)

| Layer | Failure mode | Right probe | Wrong probe |
|---|---|---|---|
| **L1 network** | host/IP unreachable, port closed | TCP connect to advertised port | HTTPS GET (might fail for L3 reasons) |
| **L2 transport** | TLS handshake failure, cert untrusted | `openssl s_client` from same execution context | `requests.get(verify=True)` (conflates with L3) |
| **L3 application** | API returns 401/403/5xx, parser fails | HTTP GET with auth + status classification | TCP connect (says "alive", misses auth bug) |
| **L4 semantic** | API returns 200 but data is wrong / stale | application-specific (e.g. arr `/api/health` reports per-indexer) | any reachability probe |

D-17-38 baseline had: arr-stack failing at L3 (stale credentials) but reported as "unreachable" (L1 framing); QNAP failing at L2 (TLS handshake) reported as L1; selfheal classifying L3 auth failures as warnings (silence-mechanism F5).

### Root causes (all three present simultaneously)

1. **Vault credential drift.** `secret/arr/{sonarr,radarr,prowlarr}` held URL values that resolved on the host (`mac-mini.internal`) but not from inside containers — appeared as L1 unreachable from the dashboard. Plus stale API keys: drift accumulates because Vault writes are infrequent and operator-driven, while service config updates from inside the container (Sonarr regenerates ApiKey on certain version upgrades).
2. **Selfheal severity misclassification.** `framework/health_checker.py` `_classify_http_exc` treated 401/403 as warning (F5 silence mechanism). Auth failures must be critical — if the credential layer is broken, every downstream metric is meaningless.
3. **TLS environment incompatibility (Debian 13 OpenSSL 3.5.5 vs QNAP).** Container TLS handshake to QNAP returns alert 80 ("internal error") regardless of TLS version, SNI, or cipher hint. Same handshake from macOS host succeeds. Workaround: bare TCP-connect fallback for reachability classification (D-17-40 is the deeper investigation).

### Remediation pattern (D-17-38 close)

Order matters:

1. Fix selfheal severity first (`_classify_http_exc`) — without this, no other remediation is observable.
2. Plumb credentials end-to-end (Vault Agent sidecar + shell-sourced entrypoint) — value never lands in image `Config.Env`, only in PID 1 environ via `set -a && . /vault/secrets/credentials.env && set +a && exec ...`.
3. Harvest live credentials from running services, write to Vault, verify via hash read-back (`vault kv get -field=api_key | shasum -a 256 | cut -c1-12`). Never display value.
4. For L2-incompatible appliance probes, use a layered fallback: app-probe → TCP-connect. The TCP fallback is doctrine-clean reachability proof without conflating with the L2/L3 layers.

### Doctrine takeaways

- **Hash-only verification means hash-only — even during diagnostics.** D-17-38 produced one near-miss this turn: `tr "\0" "\n" < /proc/1/environ | grep ^QNAP_` emitted `QNAP_PASS=<value>` to the conversation transcript (twice, before redaction was applied). Correct form: `... | sed 's/=.*/=<set>/'` for presence-only, or `... | grep -c ^VAR=` for count. The QNAP password is now considered burned-and-deferred under operator-stated stability-baseline rotation policy. This is a Sev-3 incident on the deferred-rotation list, not an immediate-action incident.
- **Vault credential drift is a sibling F-class** (candidate F13). Vault is a write-and-trust store; live service config drifts from Vault. Refresh procedure must verify against live, not write-and-trust-Vault. For services where the live config IS the source of truth (Sonarr ApiKey), the Vault record is a cache, not the canonical.
- **Container-side TLS environment is not the host TLS environment.** Validating an appliance is reachable from the host does not validate it is reachable from a containerized consumer. Always test from the actual consumer execution context. Debian 13 + OpenSSL 3.5.5 vs older OpenSSL/LibreSSL is a real divergence; D-17-40 will investigate the workaround.
- **Layered probe patterns close ambiguity.** `health_check()` should return True when *any* of (L1 TCP, L2/L3 HTTPS) succeeds, with the classification feeding back into the issue severity. A connector that only does HTTP and has no fallback will misclassify L2 failures as L1 unreachability forever.

### Status

**Active doctrine, F5 closed.** Worked example: D-17-38 close 2026-05-03. Selfheal cycle post-close: 4/5 services up (sonarr/radarr/prowlarr/qnap), correctly-classified upstream warnings (per-indexer failures, QNAP storage stats deferred under L2 chase), seedbox warning operator-deferred. Critical count: 4 → 2 (both criticals are real upstream — radarr/prowlarr "all indexers unavailable", a third-party state, not platform misconfiguration).

Cross-references: Finding 1 (Gap F5 family, now empirically closed at the silence-mechanism layer), D-17-40 candidate in PHASE_ROADMAP §18.C (QNAP TLS root-cause + workaround), D-17-26 Finding DD (container env inspection — extended this turn with the redactor-discipline sub-doctrine).

---

## Finding 9 — Configuration audits verify against operator-stated intent, not against currently-running config; running state can be unintended residue

**Worked example:** D-17-21 (2026-05-03) — OPNsense DNS authority audit.

### What happened

The 2026-05-01 KI-009 root-cause statement asserted that Unbound's host-override table is empty by design and Dnsmasq is the authority. That assertion was probe-derived: the author queried `/api/unbound/settings/get` `.unbound.hosts` (returned 0) and `/api/dnsmasq/settings/get` `.dnsmasq.hosts` (returned 6). The reasoning was: 0 < 6, therefore Dnsmasq is the authority.

Two independent errors compounded:

1. **Wrong-endpoint probe.** OPNsense Unbound stores user-added host overrides in the **`searchHostOverride` UI overrides table**, not in the `settings/get` general-settings blob. The empty `.unbound.hosts` result didn't mean Unbound was empty — it meant the probe was looking at the wrong field. The actual Unbound `searchHostOverride` table held **38 `.internal` host overrides**, served on port 53.
2. **Observed-state-as-intent inversion.** Even if the first probe had been correct, "Unbound has more entries than Dnsmasq" would not establish *which is the operator-intended authority*. Authority is an operator-intent question; record-count is observation. The 2026-05-01 audit chain treated observation as authority signal, then renamed the parity check to query the daemon with fewer entries — making the check structurally wrong against either operator-intended posture (because either daemon could have been the authority, depending on operator intent).

The right probe order, in retrospect:

1. **Read the operator-stated intent** from architecture-facts (or, if absent, ask the operator and record the answer).
2. **Probe to verify the runtime matches that intent.** If runtime matches: green. If runtime diverges: drift, to be remediated.
3. **Never collapse step 1 and step 2.** Observed state is not authority. The architecture-fact is the authority signal; the probe is the divergence detector.

### Sub-doctrine: residue is a positive failure mode

When a daemon is running but operator-intent says it shouldn't be, that is **residue** — unintended state that has accumulated from a prior session or rollback. Residue patterns:

- A service enabled by a long-ago session that was never disabled (Unbound on this platform).
- A container left running after a sibling deliverable's "retirement" plan was authored but never executed (D-17-34 stray Home Assistant container).
- An AppRole / policy / Vault Agent secret directory that outlives its consumer (D-17-34 Finding 3).
- A docker compose file in `~/control-center-stack/stacks/*` that runs but isn't in the repo (D-17-34 Finding 4 territory).

The doctrine response is **not** to take residue as evidence about correct posture. The right move is to compare against operator-stated intent, recognize the divergence, and remediate (here: disable Unbound, migrate records to Dnsmasq).

### Sub-doctrine: re-probe an audit's premises before depending on its conclusions

The KI-009 fix went out under the assumption that the underlying probe was correct (the rename direction Unbound → Dnsmasq took the wrong-endpoint result as truth). When KI-009 itself goes from `RESOLVED` to `RE-OPENED`, the right close-out is not just "fix the rename direction" but **re-validate the original probe**. D-17-21 only discovered the 38 Unbound overrides because the auditor ran `searchHostOverride` independently. If a future deliverable depends on a prior audit's conclusion, it must re-probe at least the foundational evidence — especially when the operator's pushback ("two services running simultaneously") contradicts the audit's framing.

### Migration pattern (programmatic, no GUI work)

D-17-21 WP-04 demonstrates a clean autonomous migration when both source and destination expose API endpoints. The seven-step pattern:

1. Snapshot both daemons' state to a logging directory.
2. Compose the target record list (source records + new additions). Skip records already in destination.
3. Add records to destination via API; reconfigure to make them runtime-active.
4. Validate destination resolves the records on its current port (pre-flip validation).
5. Disable source daemon (frees its port if needed) and stop service.
6. Move destination to source's port if required; reconfigure.
7. Final validation on the unified port.

Halt on any error. Both daemons can coexist mid-migration as long as they are on different ports — port collision must be the LAST step, not a precondition. Migration script: `scripts/d-17-21-dns-migration.sh`.

### Sub-doctrine: parity-check shape priority

When a parity check matches against records that can appear in multiple shapes (e.g. Dnsmasq accepts `host=foo, domain=internal` AND `host=foo, domain=""` AND `host=foo.internal, domain=""` for the FQDN `foo.internal`), the check must **prefer the most-specific shape** (Shape 1) over fallback shapes. If a bare-hostname record (Shape 3) exists alongside an explicit `.internal` record (Shape 1), Shape 3 might point at an upstream IP (a DHCP reservation) while Shape 1 points at the Caddy front IP. Iteration-order matching is fragile; explicit priority is correct. Worked example: `homeassistant.internal` Shape 1 → 192.168.10.145 (Caddy front), Shape 3 (bare `homeassistant`) → 192.168.10.141 (upstream HA hub on the LAN). The Shape 3 record is a DHCP-paired bare-hostname reservation that has its own purpose; the parity check was matching it instead of the Shape 1 record and falsely reporting `wrong_target`. Fix: walk records, return Shape 1 / Shape 2 immediately, defer Shape 3 to a fallback variable. (Patch landed in `scripts/check-repo-coherence.py` `_dns_match` at D-17-21 close.)

### KI-009 retroactive Vault incident review

D-17-21 WP-05 trace: did the multi-day Vault troubleshooting incident (Sev-2, 2026-04-30, `docs/phase-15/PHASE_15_VAULT_API_ADDR_NETWORK_INCIDENT_2026-04-30.md`) have a silent DNS-routing contribution that was misdiagnosed at the time?

**Conclusion: no.** The incident's root cause was `api_addr = "http://192.168.10.145:8200"` — a literal host LAN IP that forced every in-Docker Vault redirect to U-turn through Docker Desktop's userland-proxy. That misconfig is an IP-literal issue, not a hostname-resolution issue; DNS path was never invoked for `192.168.10.145`. The incident would have produced the same userland-proxy saturation regardless of which DNS daemon was running on OPNsense. The fix (`api_addr = "http://vault-server:8200"`) reroutes through Docker bridge DNS (in-bridge service name resolution), which is internal to Docker Desktop, not OPNsense Unbound or Dnsmasq.

KI-009 status flipped to `RESOLVED` based on D-17-21 close + this confirmed-no-contribution review. The advisory-mode pre-commit gate auto-resumes strict-fail behavior on KI-009 file's `**Status:**` line value.

### Status

**Active doctrine.** Worked example: D-17-21 close 2026-05-03. Post-migration state: 55 Dnsmasq host records (49 `.internal` + 6 bare), Unbound disabled, port 53 owned solely by Dnsmasq, parity check exit 0 (`missing=0, wrong_target=0, extra_internal=16`). KI-009 RESOLVED. Architecture-fact `opnsense-dns-authority.md` flipped from PROVISIONAL to VERIFIED.

Cross-references: Finding 4 (CMDB authority unenforced — three substrates can disagree silently; Finding 9 extends this with the broader rule that running state cannot be the authority signal regardless of substrate count), D-17-32 Finding 1 ("subsystem closure ≠ integrated-system capability"; Finding 9 names a specific failure mode within that frame).

---

## Finding 10 — Loose-doc accumulation is a recurring phase-boundary failure mode; retirement must be a scheduled deliverable, not opportunistic cleanup

**D-17-16 close, 2026-05-03.**

### Observation

Walking `docs/` at D-17-16 intake surfaced **48 loose markdown files** outside the canonical-paths set (`architecture-facts/`, `runbooks/`, `_audit/`, `phase-NN/`, `troubleshooting/`, `known-issues/`, `architecture-patterns/`, `adr/`, `dashboards/`, `_provenance/`, `_archive/`, `system-prompts/`, plus the four top-level files `ARCHITECTURE.md` / `PROJECT_FRAMEWORK.md` / `PHASE_ROADMAP.md` / `DECISION_REGISTER.md`). The 48 clustered into nine semantic groups; six required moves to canonical homes, two consolidated into a single canonical runbook, three required substrate-merge into existing canonical dirs, and the rest archived.

The accumulation pattern is mechanical: every phase produces audit reports, capability assessments, retrospective fragments, and ad-hoc analysis docs. Without a forcing function, these land at convenient ad-hoc paths (`docs/audits/capability/`, `docs/zabbix/`, `docs/canonical-patterns/`, `docs/architecture/`, `docs/templates/`, `docs/performance/`, `docs/phases/`, top-level `*_AUDIT_*.md`). Each path was reasonable when authored; collectively they fragment the canonical-paths surface and produce the stale-pointer-decay problem (D-17-21 surfaced two such pointers; D-17-16 surfaced ten more — two ADRs, four runbook line refs, plus the live cross-references in CLAUDE.md / ARCHITECTURE.md / PHASE_ROADMAP.md / PROJECT_FRAMEWORK.md, and several parked-compose audit-path comments).

### Doctrine

**Loose-doc retirement is a recurring phase-boundary deliverable, not an opportunistic cleanup.** Schedule one D-NN-MM per major phase boundary (Phase rollover, or every ~6 months when phase cadence stretches) with the following surface:

1. **WP-01 — Framework intake.** Open the deliverable; sequence after any audits whose pointers may need reconciling (DNS, services, etc.).
2. **WP-02 — Inventory.** Walk `docs/` for files outside canonical-paths set. Categorize each as: stale / misplaced / reference-only / active. Surface back if >50 items (operator gate on the cluster decisions, not file-by-file).
3. **WP-03 — Retire / move / consolidate.** Single batch commit. `git mv` preserves history; never `rm` + recreate. Where multiple loose docs cover one operational surface, consolidate into one canonical runbook rather than parallel-import each as-is.
4. **WP-04 — Cross-reference verification.** Grep the repo for paths to all moved/retired docs. Update or break-link with deprecation notes. Frozen retros (`docs/phase-NN/` closeouts, `_archive/` records) are state-at-time and **left alone** during this sweep — only update live canonical surfaces (CLAUDE.md, ARCHITECTURE.md, PROJECT_FRAMEWORK.md, ADRs, runbooks, DECISION_REGISTER.md, active scripts).
5. **WP-05 — Doctrine + chronicle.** Author or update this doctrine entry; flip framework row.

### Subsidiary rules

- **Canonical-paths set is closed.** New top-level `docs/<dirname>/` paths require an ADR (the architecture-patterns / architecture-facts / etc. set is intentionally bounded). When a new operational surface needs persistence, fold it into an existing canonical path rather than minting a new one. The temptation to add `docs/<topic>/` for one or two files is the exact mechanism that produces accumulation.
- **`_archive/` vs `_retired/` distinction.** `_retired/` is for compose stacks and service records that the operator may restore (with a recipe). `_archive/` is for documentation snapshots that have been superseded but retain historical value (per-phase subdirs). D-17-16 ratified `_archive/` as the retirement home for documentation, with `_archive/phase-NN/` subdirs for phase-bounded retros that didn't make it into the official `phase-NN/` closeout flow.
- **Frozen retrospective doctrine.** Phase closeout docs in `docs/phase-NN/` accurately reflect the state-at-time of phase close. Cross-reference verification does NOT update path references in these docs — that would falsify the historical record. The reader of a Phase 14 closeout should see Phase 14's doc-paths, not Phase 17's. Same for `_archive/` records (they were retired *with* their then-current path refs).
- **Self-referential migration notes are load-bearing, not stale.** When ADR-A-006 carries the note "path corrected — `docs/architecture/DECISION_REGISTER.md` was a stale filing convention; never moved", that reference to the stale path is *the documentation of the migration itself* and must be preserved. A future grep for `docs/architecture/` will hit it; that is correct, not a defect. Same applies to "merged from `docs/canonical-patterns/`" notes in DECISION_REGISTER and ADR-A-016.
- **Drift sibling fixes welcome during the sweep.** D-17-16 caught and fixed the "Mac Mini M5" → "Mac Mini M4 Pro" drift in `host-portability.md` and `ARCHITECTURE.md` (sibling to D-17-18's .146 → .142 correction). When a loose-doc move surfaces in-line content drift in the same touch, fix it; the cost is bounded and the alternative (logging it as a separate finding) creates more friction than the patch.
- **Out-of-scope discipline.** When the sweep surfaces broken references in pre-existing dead infrastructure (Phase-8 roadmap-executor pipeline, CI workflow refs to long-deleted Phase-8 architecture files, AnythingLLM ingestion presets that have been broken-but-graceful for 8+ phases), DO NOT fix them in this deliverable. Each is its own retirement deliverable; touching them in a doc-move sweep crosses scope and obscures the cleanup commit. Note them and move on.

### Worked example — D-17-16 close

48 loose docs → 0 outside canonical paths. Nine clusters processed:

- **Cluster A** (top-level audits + 2 misplaced runbooks): 2 → `_audit/`, 1 → `runbooks/`, 1 → `_archive/`, 2 → `_archive/phase-NN/`.
- **Cluster B** (`docs/architecture/`): 3 files folded into `docs/architecture-facts/` with renames (`mcp-server-architecture.md` → `mcp-servers.md`, `portability.md` → `host-portability.md`). Empty dir retired. Reduced canonical-paths dir count.
- **Cluster C** (`docs/audits/capability/`): 12 files → `docs/_audit/capability/`. Empty `docs/audits/` retired.
- **Cluster D** (`docs/canonical-patterns/`): openproject-connector → `architecture-patterns/`; plane-connector → `_archive/` (Plane CE retired in WP-17-04-06).
- **Cluster E** (`docs/performance/baseline-metrics.md`): → `_archive/phase-10/`.
- **Cluster F** (`docs/phases/`): 2 files → per-phase `_archive/phase-NN/`.
- **Cluster G** (`docs/system-prompts/`): canonical-as-is (operator decision; preserves D-17-11 self-contained library shape).
- **Cluster H** (`docs/templates/`): 1 file → `architecture-patterns/`.
- **Cluster I** (`docs/zabbix/`): consolidated to single canonical `docs/runbooks/zabbix-operations.md`; Phase 12 retro fragments → `_archive/phase-12/`.

WP-04 fixed 10 live cross-references (CLAUDE.md, ARCHITECTURE.md, PHASE_ROADMAP.md, PROJECT_FRAMEWORK.md, observability-doctrine.md, ADR-A-001 / A-006 / A-008 / A-010 / A-014 / A-016, DECISION_REGISTER.md, sportarr retired-record, two parked-compose audit-path comments) and identified two pre-existing dead-infrastructure broken-pointer clusters left alone (Phase-8 roadmap-executor pipeline; AnythingLLM `ingest-docs.py` preset). Total batch: ~48 git mv operations, ~15 in-file edits, 9 empty-dir retirements.

### Refresh cadence

- Trigger: phase rollover OR observation that >25 loose docs have accumulated outside canonical paths OR a moved-doc cross-reference defect surfaces in a non-doc-cleanup deliverable (signal that the previous sweep is overdue).
- Owner: whoever is closing the phase; loose-doc retirement is the final step before phase closeout's commit batch.

### Cross-references

- D-17-21 (DNS authority) close surfaced the first wave of cross-reference defects this sweep then completed.
- D-17-18 (.146 → .142 hostname drift) is the reference precedent for "patch in-line drift during the sweep."
- ADR-A-016 (Canonical Patterns Registry) explicitly accommodates the `docs/canonical-patterns/` → `docs/architecture-patterns/` merge at the ADR level.
- Finding 9 (configuration audits verify against intent, not running config) — same authority-vs-residue distinction applies: doc trees accumulate residue (loose docs) that doesn't match the canonical-paths intent stated by the doctrine. Both findings share the rule "the operator-stated intent is the authority signal, not the on-disk-state".

---

## Finding 11 — Declarative config-as-code substrate prevents URL drift structurally; reactive remediation is the wrong layer for config-class incidents

**D-17-44 close, 2026-05-03.**

### Observation

The D-17-38 root cause was a Prowlarr application record holding stale URLs (`mac-mini.internal:1867` for Sportarr instead of `sportarr:1867`) that caused authentication failures silently attributed to other causes until a deep integration audit traced them. The fix was reactive: detect the drift, patch the records, update Vault, re-verify. This cycle took the majority of D-17-38's effort.

A declarative config substrate (Buildarr) would have prevented this incident entirely: the canonical form of those application URLs lives in `config/arr-stack/buildarr/buildarr.yml`; any manual UI change diverging from that YAML is detected and reverted on the next daily run. The operator never had to author a "drift audit" — the reconciliation loop is automatic.

**The F10 retirement-record-as-restoration-playbook problem (Finding 6) is the reactive equivalent of the same gap**: without a canonical YAML, the restoration playbook is "re-enter the values you remember from the last time." With Buildarr, the playbook is `buildarr-run.sh`.

### First worked example — D-17-44 (2026-05-03)

Buildarr deployed against Radarr (v6.1.1.10360) and Prowlarr (v2.3.5.5327) on Mac Mini.

**Drift extraction via `dump-config`:** `buildarr radarr/prowlarr dump-config` extracted full live state into Buildarr-native YAML. The extraction is itself the drift-detection mechanism: any deviation between the extracted YAML and a prior-committed YAML would be an empirical drift record.

At first extraction (2026-05-03), state matched expected post-D-17-38 baseline — confirming D-17-38's remediation held. No drift found on first run.

**First `buildarr run` output (WP-05):**
```
<prowlarr> (default) Remote configuration is up to date
<radarr> (default) Remote configuration is up to date
<radarr> (default) Remote configuration is clean
<prowlarr> (default) Remote configuration is clean
```
Zero mutations applied. Idempotency confirmed.

**Schema coverage gaps surfaced by this deployment:**

| Area | Status | Notes |
|---|---|---|
| Radarr media_management, profiles, quality, custom_formats, indexers, download_clients | Managed by Buildarr | Full lockdown |
| Prowlarr applications (consumer URLs + api_keys) | Managed by Buildarr | **This is the D-17-38 prevention layer** |
| Prowlarr indexer definitions | NOT managed | Plugin schema gap — `dump-config` returns count=0; indexers remain manual |
| Prowlarr download clients | NOT managed | Plugin schema gap |
| Radarr notifications (Plex/PlexServer) | NOT managed | Plugin emits `Unsupported... ignoring`; `delete_unmanaged: false` protects it |
| Sonarr (all) | NOT managed | v4.0.17: `buildarr-sonarr` plugin supports v3 only |
| Sportarr (all) | NOT managed | No Buildarr plugin (official or community) |

### Doctrine

**Declarative config-as-code eliminates the reactive-remediation loop for covered config fields.** For Prowlarr application URLs specifically, the canonical form is `http://<container-name>:<port>` (container DNS) as locked in `config/arr-stack/buildarr/buildarr.yml`. Any future session that encounters "Prowlarr can't reach Radarr" should:

1. Run `buildarr-run.sh` first — if the URL drifted, Buildarr restores it automatically.
2. If drift recurs across multiple runs, the root cause is something that overwrites Buildarr's writes (e.g., a Prowlarr auto-import that resets the URL on new indexer registration). That is a Finding 11 second-order problem, not a URL-entry problem.

**Reactive remediation (`vault kv put`, manual UI edits) is still required for:** credentials (Vault is the authority for secrets; Buildarr is the authority for config), Sonarr/Sportarr until plugin coverage lands, Prowlarr indexer definitions until the plugin schema gap closes.

**The `dump-config` → commit loop is the drift-detection primitive.** Running `buildarr radarr/prowlarr dump-config` after any manual UI change session and committing the diff to `config/arr-stack/buildarr/buildarr.yml` is the operator-facing equivalent of `git diff` for arr-stack config. This should happen after: any Radarr/Prowlarr major version upgrade, any quality-profile or custom-format change, any application record modification.

### Known limitations (scope reduction)

Per D-17-44 pre-flight Q1–Q3:

- **Sonarr v4 blocker:** `buildarr-sonarr` plugin is v3-only. Sonarr v4.0.17 cannot be managed. Remediation: wait for upstream v4 plugin, then re-run `dump-config` and extend `buildarr.yml`. No Sonarr downgrade.
- **Sportarr no-plugin:** No Buildarr plugin exists. Sportarr remains under the retirement-record-as-restoration-playbook pattern (D-17-36 record). If a community plugin lands, activate via §18.G component 2 extension.
- **Prowlarr plugin schema gaps (indexers, download_clients):** These fields will be auto-captured once the upstream plugin adds them. Until then, `delete_unmanaged: false` prevents Buildarr from deleting these objects.

### Deployment substrate

- YAML: `config/arr-stack/buildarr/buildarr.yml` (839 lines, dump-config-generated)
- Credentials: `${RADARR_API_KEY}` / `${PROWLARR_API_KEY}` placeholders; Python-substituted at runtime from Vault-rendered `credentials.env`
- Vault: AppRole `buildarr`, policy `config/vault-policies/buildarr-policy.hcl`, reads `secret/arr/{radarr,prowlarr,sonarr,sportarr}`
- Compose: `docker/docker-compose-buildarr.yml` (sidecar + one-shot run pattern)
- Run wrapper: `scripts/buildarr-run.sh` (sidecar refresh → env substitution → `buildarr run`)
- Launchd: `docker/launchd-agents/com.iap.buildarr-sync.plist` (daily 03:00, after backup at 02:00)
- Heartbeat: `/Users/admin/.platform-logs/buildarr-sync.heartbeat`
- Log: `/Users/admin/.platform-logs/buildarr-sync.log`

### Cross-references

- D-17-38 (the worked incident that Finding 11 would have prevented — Prowlarr URL drift silently causing auth failures)
- Finding 6 (F10) — retirement-records-as-restoration-playbook; Buildarr YAML is the structural replacement
- Finding 8 — L3 (integration) health checks; Buildarr is a config-plane complement (it restores config; it does not probe health)
- §18.G component 2 (PHASE_ROADMAP — this is the first closed sub-deliverable of the arr-stack ecosystem family)
- §18.G component 8 (Profilarr/Recyclarr — TRaSH-Guides automation; extends Buildarr's quality-profile lockdown with community-maintained profiles)

---

## Finding 12 — Metrics-layer observability for arr-stack should use community exporters; selfheal remains remediation-layer only

**D-17-46 close, 2026-05-03.**

### Observation

D-17-38 closed the F5 silence mechanism at the remediation layer
(`selfheal.py` classification + credential drift repair), but that
layer is reactive and incident-shaped. It does not provide continuous
Prometheus-native telemetry for queue depth, scrape timing, or service
collector health in VictoriaMetrics/Grafana.

D-17-46 added a sibling metrics layer using Scraparr, scraped by
vmagent into VictoriaMetrics, with a provisioned minimal Grafana
dashboard (`arr-stack-overview-p18`).

### Doctrine

- **Use community-standard exporters for metrics-class observability**
  instead of extending custom remediation code for metrics ingestion.
- **Keep layers distinct:** selfheal remains active-remediation and
  error-classification logic; exporter metrics remain telemetry plane.
- **Credential handling remains D-17-38 pattern:** exporter reads
  Vault-rendered API keys via Vault Agent sidecar; hash-only
  verification for all key-comparison operations.

### Worked result (D-17-46)

- Scraparr chosen over Exportarr at WP-02: active maintenance and
  single-instance multi-service coverage fit this stack better.
- Sidecar + AppRole/policy pattern mirrored from D-17-38 / D-17-44.
- vmagent target `job=\"scraparr\"` reached `up` and VictoriaMetrics
  began returning `sonarr_last_scrape`/`radarr_last_scrape`/
  `prowlarr_last_scrape` series.
- Community dashboard adaptation deferred intentionally as a backlog
  item due to non-trivial datasource templating mismatch.

### Cross-references

- Finding 8 (reactive integration health-check layer)
- Finding 11 (declarative config control layer)
- §18.G component 1 (observability) and component 2 (Buildarr) as
  sibling structural prerequisites before arr-stack expansion

---

## Finding 13 — Container image provenance/availability is a sibling structural risk to model provenance for community tooling

**D-17-49 chronicle note, 2026-05-03.**

### Observation

During §18.G component 3 deployment, the planned Huntarr image
(`huntarr/huntarr`) became unreachable from the runtime host
(no pullable current or historical tested tags). The functional scope
was preserved by consolidating to Cleanuparr-only (Seeker module),
but the event exposed a supply-chain failure mode independent from
runtime configuration correctness:

- the repository and docs can still exist while image distribution
  becomes unavailable;
- deployment plans that assume mutable `:latest` continuity can fail
  mid-deliverable without any local regression;
- fallback pressure can push operators toward low-provenance forks.

### Doctrine

- **Treat container-image provenance/availability as a first-class
  pre-flight gate** for arr-stack expansion deliverables.
- **Pin to verified, pullable references** (tag+digest when possible)
  before integration work depends on them.
- **Prefer role-consolidation in trusted tools** over introducing
  unproven forks under deployment pressure.
- **Model provenance and container provenance are sibling controls:**
  both protect platform continuity against upstream disappearance or
  trust breaks.

### Worked result (D-17-49)

- Huntarr role was consolidated into Cleanuparr Seeker.
- Huntarr scaffolding was moved to deferred state:
  `docker/_deferred/huntarr-upstream-unreachable-2026-05-03/`.
- Component status explicitly recorded as DEPLOYED (observable/inert)
  pending credential-chain completion and operator-gated enablement.

### Cross-references

- Finding 10 (F10 family closure mechanics; reactive -> structural)
- Finding 12 (observable-but-inert sibling pattern)
- §18.G component 3 (Cleanuparr Seeker consolidation)
- §18.L prerequisite chain (credentials before remediation enablement)

---

## Finding 14 — DNS authority and DNS cache-invalidation are sibling concerns; both must be correct for end-to-end resolution

**Date:** 2026-05-03
**Originating WP:** D-17-13 WP-03
**Severity:** Medium (silent multi-minute resolution failure on
hosts that queried a hostname pre-creation; confused initial
diagnosis between "Dnsmasq broken" vs "consumer cache stuck")

### What

D-17-21 established Dnsmasq on OPNsense as the sole DNS authority
for `*.internal`. That doctrine is necessary but not sufficient:
records added on the authority side don't propagate to consumers
that have a cached negative response.

Worked example (D-17-13 WP-03): the `mac-studio.internal` Shape 1
record was added on OPNsense Dnsmasq via API. Resolver state on
Mac Mini after the record was live:

| Probe | Result |
|---|---|
| `dig mac-studio.internal @192.168.10.1` | ✅ 192.168.10.142 |
| `dns-sd -q mac-studio.internal` | ❌ `0.0.0.0 No Such Record` (cached) |
| `python3 socket.gethostbyname` | ❌ `gaierror: nodename...` |
| `curl http://mac-studio.internal:11434` | ❌ `Could not resolve host` |
| `dscacheutil -flushcache` | ❌ no effect |

`dig` queries Dnsmasq directly and is correct. Everything else
funnels through `mDNSResponder`, which had cached an NXDOMAIN from a
query that landed before the record was created. macOS's
`mDNSResponder` cache is **independent** from the legacy
`DirectoryService` cache that `dscacheutil` flushes.

Fix:

```bash
sudo killall -HUP mDNSResponder
```

Verifies immediately:

```bash
python3 -c "import socket; print(socket.gethostbyname('mac-studio.internal'))"
# 192.168.10.142
```

### Doctrine

When adding a `.internal` record via OPNsense Dnsmasq, treat
**consumer-side cache invalidation as part of the record-creation
runbook**, not a separate operator concern. The authority side
(Dnsmasq host entry) is necessary; the consumer side
(`mDNSResponder` HUP for macOS, `systemd-resolve --flush-caches`
for Linux, `nscd -i hosts` or `systemctl restart dnsmasq` for
Linux nscd/dnsmasq-local) closes the loop.

This is a sibling of D-17-21's authority doctrine (`opnsense-dns-
authority.md`), not a duplicate of it:

- **D-17-21 = authority surface.** *Who answers `*.internal`?*
  Dnsmasq, sole; Unbound forbidden.
- **Finding 14 = cache-invalidation surface.** *How do consumers
  learn the answer changed?* Authority-side flush is not enough;
  per-consumer flush per OS family.

Both must be correct. The interesting failure mode is when only
one is correct: `dig` works (authority is right) but `curl` fails
(consumer cache is wrong), which produces ambiguous symptoms
unless an operator explicitly probes both surfaces.

### Operational pattern (extends `opnsense-dns-authority.md`
"Where to add a new `.internal` record")

After adding the host entry on OPNsense:

```bash
# macOS consumers (Mac Mini, Mac Studio, MacBook)
sudo killall -HUP mDNSResponder

# Linux consumers (Threadripper future, Docker host VMs)
sudo systemd-resolve --flush-caches    # systemd-resolved hosts
sudo nscd -i hosts                     # nscd hosts (older distros)
sudo systemctl restart dnsmasq         # local-dnsmasq hosts
```

Cross-reference: `opnsense-dns-authority.md` "Consumer-side cache
invalidation" section, added concurrently with this finding.

### Why this matters beyond D-17-13

Future deliverables that add `.internal` records (any new
caddy-fronted service, any new bare-hostname DHCP reservation
that other services need to resolve) will hit this same failure
mode if the consumer-side flush is skipped. Specifically: any
Day-N node that has previously been on the LAN and may have
queried a hostname before the OPNsense record was added —
mDNSResponder will hold the NXDOMAIN until manually flushed or
the cache TTL expires (typically 15 minutes for negative
responses).

### Cross-references

- Finding 9 (config-audit doctrine; sibling rule about state vs
  intent) — same shape: running state can hide what's actually
  authoritative
- D-17-21 chronicle: `opnsense-dns-authority.md`
- D-17-21 migration script: `scripts/d-17-21-dns-migration.sh`
  (worked example for cross-daemon record migration; future
  successor scripts should incorporate the consumer-flush step
  per this finding)

---

## Finding 15 — Headless macOS launchd requires user-domain bootstrap with privileged registration path (Finding Y)

**Date:** 2026-05-03
**Originating WP:** D-17-51 WP-02..WP-05
**Severity:** Medium-High (unattended automation blocked across multiple agents)

### What was observed

- `launchctl print gui/<uid>` fails with `Domain does not support specified action` on the Mac Mini headless posture (no active GUI login session).
- `launchctl print user/<uid>` succeeds (domain exists, `session = Background`).
- `launchctl bootstrap user/<uid> <plist>` from non-root shell fails with `Bootstrap failed: 5: Input/output error` (reproduced on both production and minimal probe plists), and services remain absent from `launchctl print user/<uid>/<label>`.

### Canonical pattern

For headless server operation, **`user/<uid>` is canonical** and `gui/<uid>` is non-canonical.
Registration is performed with privileged bootstrap:

1. `launchctl bootout user/<uid>/<label>` (best-effort)
2. `launchctl bootstrap user/<uid> <plist>`
3. `launchctl enable user/<uid>/<label>`
4. `launchctl kickstart -k user/<uid>/<label>`
5. `launchctl print user/<uid>/<label>` + heartbeat recency verification

### Deliverable state

D-17-51 first attempted the user-domain path (`user/<uid>` bootstrap) and
captured a hard empirical failure: even with root execution, the target agent
set returned `Bootstrap failed: 5: Input/output error` uniformly on this
headless configuration. That path is now a **documented failed branch**, not an
open action item.

Resolution pivot: migrate unattended `com.iap.*` jobs to LaunchDaemons in
`system` domain with `UserName=admin` (headless-safe, no GUI-session
dependency). Migration/verification artifacts:

- `scripts/d-17-51-migrate-to-launchdaemons.sh`
- `scripts/d-17-51-verify-launchdaemons.sh`

Operator executes one sudo migration run; Finding Y is resolved by this
daemon-domain canonical pattern.

### Cross-references

- D-17-29 (platform-registry LaunchAgent known blocked by Finding Y)
- D-17-44 (`--no-verify` commit path due to stale launchd recency checks)
- D-17-50 (arr-apikey-sweep deployment unblocked by daemon-domain pivot)

### Sub-finding 15.A — Publisher-uniqueness check before LaunchDaemon authoring

**Date:** 2026-05-04
**Originating WP:** D-17-51 close-out (MCP-trio outlier classification)
**Severity:** Medium (creates spurious FAILs in migration verification;
masks "service is fine, plist is duplicate" as "service is broken")

#### What was observed

Three `com.iap.mcp.*` LaunchDaemons in the D-17-51 migration set
(`com.iap.mcp.docker`, `com.iap.mcp.docs`, `com.iap.mcp.filesystem`)
hit a clean throttle/SIGTERM loop: their wrapper supergateway
processes started, logged `Listening on port NNNN`, then were
immediately killed. Verification reported `loaded=no`.

Investigation showed the failure was **not** a plist defect, **not**
a launchd-domain semantic problem, **not** a stdio-vs-HTTP design
issue. The three target ports (8091/8092/8093) were already owned by
healthy Docker containers (`mcp-filesystem-remote`, `mcp-docker-remote`,
`mcp-docs-remote`) since the container migration on 2026-05-03. The
plists predate that migration (wrapper scripts dated 2026-04-27);
they were left behind as residue. They were trying to publish a
service that already had a canonical publisher.

#### Canonical pattern

Before authoring or retaining a system-domain `com.iap.*`
LaunchDaemon for a service that exposes a TCP port or named socket,
verify that no other supervisor already publishes it. The check is
the launchd analogue of the D-17-29 "consult `~/.platform-registry/`
before guessing" doctrine.

Pre-flight checks to add to migration scripts:

1. **Port-uniqueness probe.** For every plist whose `ProgramArguments`
   ultimately binds a TCP port: parse the port (from the wrapper
   script or env), then run `lsof -nP -iTCP:<port> -sTCP:LISTEN`. If
   any process owns it, classify the plist as `DUPLICATE-PUBLISHER`
   (not OK, not FAIL — a third state) and emit retirement guidance.
2. **Container-publisher probe.** For each candidate port, also check
   `docker ps --format '{{.Names}}\t{{.Ports}}' | grep ':<port>->'`.
   If a container publishes that port, the launchd plist is almost
   certainly stale residue from a pre-containerization design.
3. **Service-registry consult.** Cross-reference
   `~/.platform-registry/inventory.json` for `service_id` matches.
   A service present in the registry with `state.running == true` is
   the canonical publisher; a parallel launchd plist is stale.

#### Migration verifier classification

Update `scripts/d-17-51-verify-launchdaemons.sh` (and any successor
verifier) to emit four states rather than two:

- `OK` — loaded, last-exit-code=0, heartbeat in budget
- `FAIL` — loaded but failing, OR not loaded for a non-publisher
  reason
- `DUPLICATE-PUBLISHER` — port held by Docker/Colima/another
  supervisor; recommend `bootout` + plist retirement
- `SKIP` — GUI-dependent or otherwise out-of-scope for system domain

`DUPLICATE-PUBLISHER` does not gate close-out; it triggers a
retirement task instead.

#### Worked example (D-17-51)

The MCP trio was reclassified `DUPLICATE-PUBLISHER` post-hoc. The
effective migration result moves from `11 OK / 3 FAIL` to
`11 OK / 3 retire / 1 skip` — same physical state, correct
classification. See `docs/phase-18/d-17-51/CLOSEOUT_2026-05-04.md`.

#### Cross-references

- D-17-29 — service-registry consultation doctrine (parent rule).
- D-17-51 close-out — first applied instance.
- CLAUDE.md "D#30 three permanently non-compose-hardened
  containers" — the duplicate-publisher trio is the same set of
  services, evidence that bare-docker-run / Obot-managed lifecycles
  are the canonical publishers, not launchd.

---

## Finding 16 — SSH non-interactive sudo is a recurring automation blocker; remote privileged scripts require terminal allocation or explicit manual handoff

**Date:** 2026-05-04
**Originating WP:** D-17-59
**Severity:** Medium (automation path break; service usually recoverable through manual privileged execution)

### What was observed

- D-17-51 documented a repeated pattern where unattended bootstrap/migration work still required an operator-run sudo path.
- D-17-58 showed the same class on a remote host: `scripts/install-ollama-launchdaemon-mac-studio.sh` used `ssh "$REMOTE_HOST" "sudo /bin/bash -s"` (no tty allocation), and the operator completed install using manual `sudo cp/bootstrap` steps on Mac Studio.
- This is a transport/execution-plane failure class: **the privileged action is correct, but the invocation posture (`ssh` non-interactive + `sudo`) is not.**

### Canonical pattern

For remote privileged automation scripts:

1. Use explicit terminal allocation for sudo paths:
   - `ssh -t <host> "sudo <command>"`
2. Keep remote privileged blocks idempotent and reversible (`bootout` before `bootstrap`, overwrite-safe file install).
3. If remote sudo policy/host posture still blocks scripted execution, stop retry loops and emit a canonical manual sequence for operator execution.

### Scope boundary vs Finding 15

- **Finding 15:** launchd domain semantics on headless macOS (`gui/<uid>` vs `user/<uid>` vs `system` daemon pivot).
- **Finding 16:** remote privileged command-transport semantics (`ssh` + `sudo` interaction model).

They are sibling controls and both must hold for unattended reliability.

### Cross-references

- D-17-51 (Finding Y resolution; daemon pivot)
- D-17-58 (Mac Studio Ollama persistence; script-level failing example)
- `docs/runbooks/remote-sudo-scripts.md` (canonical remote-sudo execution pattern)

---

## Finding 17 — Sourced credentials.env vars do not reach `python3 -c` subprocesses without explicit export

**Date:** 2026-05-04
**Originating WP:** D-17-76 WP-04 (rTorrent client live-bootstrap)
**Severity:** Doctrine (touches every Vault Agent sidecar consumer that uses inline-python helpers)

### What

A bootstrap script that does `. /vault/secrets/credentials.env` and then invokes `python3 -c '... os.environ.get("VAR","")'` will silently get the empty default for any sidecar var, because shell-`source` sets shell-scope variables, not exported environment variables — and the python3 subprocess inherits only the exported environment.

D-17-76 WP-04 worked example: `scripts/cleanuparr-bootstrap-config.sh` sourced the rendered Vault Agent credentials file (containing `RTORRENT_USER`, `RTORRENT_PASSWORD`, etc.), then a `python3 -c` block constructed the Cleanuparr `download_client` POST body using `os.environ.get("RTORRENT_USER","")`. The subprocess saw an empty username — but the script `export`ed only `CLEANUPARR_API_KEY` (line 73 at the time). Cleanuparr accepted the POST with empty username; the registered client was authenticated by password alone, which happens to work for ruTorrent httprpc but masks a real config defect.

The defect is not visible from the bootstrap script's `[hash12]` log lines, because those operate on *shell* variables (which are populated correctly by `source`). It only surfaces when: (a) the consumer subprocess actually reads the env, and (b) you GET-back the registered record from the consumer API to check what stuck.

Discovery sequence in D-17-76 WP-04: Cleanuparr `GET /api/configuration/download_client/` returned `username: ''` for the freshly-registered client. The two-line fix was `export RTORRENT_URL RTORRENT_USER RTORRENT_PASSWORD` after the `. ${CRED_FILE}` line, plus `enabled: True` in the POST body (separate orthogonal bug — Cleanuparr's POST default for new clients is disabled).

### Why this is doctrine, not a one-off bug

This is the third recurrence of the env-asymmetry-between-shell-and-subprocess pattern in 2026:

1. D-17-26 sub-doctrine: `docker exec env` ≠ PID 1 environ when entrypoint sources secret files (consumer-side asymmetry).
2. D-17-38 near-miss: `/proc/1/environ` reads must redact when var holds a credential (display-side asymmetry).
3. D-17-76 WP-04 (this finding): sourced creds don't reach `python3 -c` without `export` (producer-side asymmetry).

All three are about the same underlying truth: **shell scope, exported env, and PID-1 environ are three distinct readings of "the environment", and they diverge by design**. Diagnosis must specify which reading is being tested.

### How to apply

For any new bootstrap/automation script that follows the Vault Agent sidecar pattern (`. ${CRED_FILE}` → consume credentials in subprocesses):

1. **Always `export` the vars after sourcing**, even when subprocess use looks superficially-shell-only. Subprocess-via-`python3 -c`, `node -e`, `jq --arg`, or any inline interpreter all need exported env.
2. **Verification step is consumer-side, not script-side.** A `[hash12]` log of the *shell* variable proves the source-load worked, but it does NOT prove the subprocess saw the value. Verify by GET-back from the consumer API and inspect what actually stuck.
3. **Live-test new bootstrap scripts** by reading the registered record back from the consumer API on first run, with credential-presence flags (`bool(field)`) — never display the value.

### Related anti-patterns to retire

- "If `[hash12]` logs the right hash, the credential is wired" — wrong. The hash is on the shell variable; subprocess inheritance is independent.
- "Cleanuparr (or any API) accepting the POST means the body was correct" — wrong. APIs frequently accept empty-string fields; the GET-back is the only honest verification.

### Cross-references

- D-17-26 sub-doctrine (`docker exec env` vs PID 1 environ — consumer side)
- D-17-38 "Hash-only verification — `/proc/1/environ` reads must redact" near-miss (display side)
- D-17-76 WP-04 (this finding's worked example #1)
- D-17-86 WP-07 (this finding's worked example #2 — see below)
- `scripts/cleanuparr-bootstrap-config.sh` (canonical fixed example, now exports `RTORRENT_*` vars before any subprocess AND uses schema-truth-derived POST body)

### Worked example #2 — GET-mutate-PUT round-trip omits fields the API silently swallows

**Date:** 2026-05-04
**Originating WP:** D-17-86 WP-07 (Cleanuparr download-client URL repair fold-in)

The same anti-family of asymmetries surfaced again, this time on the API-response side rather than the env-source side. The trigger was operator-observed `Invalid URI: The format of the URI could not be determined.` errors in cleanuparr health-check logs every 5 min, against the rtorrent-seedbox client registered at D-17-49 close.

Discovery sequence:

1. Hypothesis (wrong): GET-mutate-PUT round-trip on `download_client/<id>` was silently dropping `port` and `useSsl` from the request body, causing the live record to lose those fields. Built explicit-field PUT body, re-applied. Health check still failed.
2. Hypothesis (wrong): API list endpoint hides `port` and `useSsl` for UI-display reasons but persists them. Inspected the SQLite store directly: `download_clients` table has columns `(id, enabled, name, type_name, type, host, username, password, url_base, external_url)` — **no `port` column, no `use_ssl` column.** The fields the bootstrap was POSTing didn't exist in the schema; Cleanuparr accepted them at the API layer (silent ignore) and discarded them at the persistence layer.
3. Root cause: Cleanuparr's `host` field is the **full origin URL** (e.g., `https://5.nl19.seedit4.me`), and `url_base` is the **path-only suffix**. The model's `get_Url()` accessor concatenates `host + url_base` and parses with `System.Uri`. A bare hostname in `host` fails URI parsing → `Invalid URI: The format of the URI could not be determined.`
4. Fix: rewrote `parse_url()` in `scripts/cleanuparr-bootstrap-config.sh` to emit `HOST=<scheme>://<hostname>[:<port>]` (full origin) and removed `port`/`useSsl` from the POST body. Recreated the client; health-check tick at 10:54:48 reported `Client a71214b7-... health changed: Healthy`.

The doctrine-relevant pattern: **API field-level acceptance is not field-level persistence.** Two distinct asymmetries collide:

- **API → DB asymmetry:** the POST/PUT validator accepts a field name; the ORM/EF-Core mapper has no column for it; the value lands nowhere.
- **DB → API asymmetry:** the GET-list serializer omits columns it considers UI-irrelevant (in this case it omits *all* fields, including the model-computed ones, because they're populated from a transient property bag that the list endpoint doesn't bind).

Both asymmetries make the GET-mutate-PUT pattern hostile when the GET is your only source of schema truth. The honest sources are:

1. The DB schema itself (`sqlite3 ".schema <table>"`) — definitive.
2. The OpenAPI/Swagger surface — when the service exposes one. (Cleanuparr does not.)
3. The original POST body that produced a known-working state — assuming you can find a worked example.
4. Direct DB-row inspection of a working record — when no Swagger and no working POST template exists.

### How to apply (worked example #2)

For any consumer-API integration script in this platform:

1. **Treat GET-list as a UI-display projection, not a schema source.** Field omissions in the response can mean: (a) UI redaction (e.g., `password: '••••••••'`), (b) computed field not bound by the list endpoint, OR (c) field doesn't exist in the underlying schema. You cannot tell which without inspecting the store.
2. **When in doubt, inspect the persistence layer.** SQLite, Postgres, the ORM migrations folder — whatever's authoritative. For Cleanuparr that's `/config/cleanuparr.db` (must copy `.db + .db-wal + .db-shm` together for a coherent read; running container has WAL not yet checkpointed).
3. **Avoid GET-mutate-PUT for record patches.** Either (a) author the full PUT body from authoritative sources (schema + env + known-working-example), OR (b) DELETE + POST to recreate from the canonical create flow when the API supports it.
4. **The "health-check log" is the most reliable feedback signal** — much more reliable than a clean PUT response, which can be a false-positive when the server silently drops unrecognized fields.

### Anti-patterns retired (worked example #2)

- "GET-back the live record, modify the field I care about, PUT it back" — wrong when the GET-back is incomplete or is a UI-display projection. Round-trip can lose fields you didn't even know about.
- "If the POST returned a non-error response, the schema accepted everything I sent" — wrong; .NET model binders silently ignore unknown JSON properties by default. The 415 errors only fire on Content-Type mismatch or malformed bodies, not field-name mismatches.
- "If the GET response shows the field, the field is persistable" — converse-of-the-above also fails: the GET response may include only persisted fields, OR may include both persisted and computed-on-the-fly fields. Use schema introspection.

---

## Finding 18 — Out-of-repo compose changes require rewire-log snapshots; cumulative gap produces an unrecoverable forensic blind spot

**Deliverable:** D-17-89 (arr-stack compose git integration audit, 2026-05-04)

The arr-stack compose file at `/Users/admin/control-center-stack/stacks/arr-stack/docker-compose.yml` had 4 service additions (Bazarr D-17-47, Cleanuparr D-17-49, Sportarr D-17-36, Lidarr D-17-87) with no rewire-log snapshots. The D#15 doctrine ("out-of-repo compose changes require pre/post snapshots") was followed for the `ai-control` stack (homarr retirement, 2026-05-01) but never applied to the arr-stack.

The failure mode: if a compose change breaks a sibling service, there is no git-diff equivalent to recover from — the rewire log IS the pre/post diff. Without it, rollback requires operator memory or container inspection, both of which degrade with time.

### How to apply

1. **Before any compose edit to `~/control-center-stack/stacks/*`:** run `shasum -a 256 <compose-file>` + `wc -l <compose-file>` and record the pre-state in a new `docker/_rewire-log/<YYYY-MM-DD>-<stack>-<reason>.md` entry.
2. **After the edit:** record the post-state SHA256 + line count in the same file. Include which services were added/removed/changed.
3. **For post-hoc recovery:** write a "snapshot" entry (as done for D-17-89) that captures current state and notes the gap period. This is better than no entry but is not a substitute for the pre-state.
4. **Enforcement:** the pre-commit hook cannot check out-of-repo files; this is an operator discipline item. A future periodic audit deliverable could diff `~/control-center-stack/stacks/` against recorded hashes.

### D-17-88 retroactive note

D-17-87 (Lidarr deployment) was committed with `--no-verify`. The bypassed hook was `detect-secrets` (no credential content in the diff). The process deviation is acknowledged; `--no-verify` should be used only when the specific failing hook is verified safe for the specific diff. Using it as a blanket bypass is not acceptable under hook discipline.

---

## Finding 19 — Aider+local-LLM has the same source-fidelity boundary as Goose+local-LLM for multi-paragraph doc-authoring

**Date:** 2026-05-04
**Originating WP:** D-17-101 WP-02 / WP-07
**Severity:** Doctrine (routing boundary correction)

### What

Empirical N=2 evidence on 2026-05-04 shows the boundary is local-LLM-class,
not surface-specific:

1. `scripts/aider-task.sh --class C1` on `qwen2.5-coder:14b` (Mac Mini)
   proposed replacing an entire long chronicle file with only the new section
   body (reconstruction instead of append).
2. `scripts/aider-task.sh --hard --class C1` on `qwen3-coder-next:latest`
   (Mac Studio M3 Ultra) proposed rewrites of unrelated existing Findings while
   attempting to append one new finding, then timed out (`exit 124`) before a
   safe apply point.

Both attempts targeted append-to-existing-doc work in
`docs/architecture-facts/integration-audit-doctrine.md` and both failed
source-fidelity semantics. The failure mode matches D-17-53 (Goose + local
LLM): once the model is prompted for whole-edit-style output on long narrative
documents, it can emit a reconstructed "new file" instead of a constrained
append delta.

### Canonical statement (Finding 19)

Tier-classification is a pre-dispatch obligation, not a post-hoc label.
Skipping classification and auto-routing to frontier was the root cause of zero
operator-initiated LOCAL_AIDER invocations in an 18-day window (D-17-93). Every
AI session must classify incoming work against Tier 1/2/3 before emitting the
first tool call. Classifier:
`docs/architecture-facts/work-routing-doctrine.md` (D-17-95). Chronicle:
2026-05-04.

### How to apply

- Multi-paragraph doc-authoring, doctrine extension, and structured finding
  append work are permanently Tier 2 (Claude Code/Codex), not Tier 1 Aider.
- Aider should refuse these tasks and surface back with routing guidance.
- Benchmark wins on long-context throughput do not override this safety boundary
  unless empirical source-fidelity evidence says otherwise.

### Cross-references

- D-17-53 (Goose posture boundary)
- D-17-91 (benchmark results; long-context strength did not imply safe doc append)
- D-17-97 (compute redirect did not remove the boundary)
- D-17-101 (this deliverable)

---

## Finding 20 — Download-client category segregation is a hard isolation boundary across *arr apps

**Date:** 2026-05-04
**Originating WP:** D-17-102 WP-02/03/04
**Severity:** Operational correctness (cross-app queue contamination risk)

### What

In the arr-stack, category values on download clients are not cosmetic
labels; they are the routing/isolation key that decides which app
consumes which queue entries.

D-17-102 worked example: Lidarr had SABnzbd attached with
`musicCategory=sonarr` while rTorrent was correctly `lidarr`. Result:

- Lidarr consumed Sonarr queue scope (TV items) instead of music scope.
- Lidarr health warned on Docker path checks against Sonarr completion
  path, because Lidarr-specific remote-path mapping did not exist for
  that path pairing.

### Why this recurs

The failure mode is templating drift: copying a known-good Sonarr/Radarr
client payload into Lidarr without updating app-specific category and
associated remote-path mappings.

### How to apply

1. For each app/client pair, category must equal app identity:
   - Sonarr=`sonarr`, Radarr=`radarr`, Lidarr=`lidarr`.
2. Server-side categories must exist on the downloader (SAB `get_cats`).
3. Remote path mappings must include category-specific completion paths
   (`/home/.../complete/<category>/` → container-local `/downloads/.../<category>/`).
4. Provisioners must enforce these fields idempotently post-deploy.

### Status (worked example outcome)

D-17-102 correction path:

- Added SAB `lidarr` category via API config.
- Patched Lidarr SAB category to `lidarr`.
- Added Lidarr remote-path mappings for SAB `lidarr` and rTorrent paths.
- Health warning cleared; Lidarr queue normalized to zero cross-app items.

### Cross-references

- D-17-100 (operational parity follow-on)
- D-17-102 (this worked example)
- `docs/runbooks/arr-stack-add-component.md` §7.1

---

## Finding 21 — Open-weights ≠ locally-runnable; RAM-fit is Step -1 before provenance

**Date:** 2026-05-04
**Originating WP:** D-17-104 WP-02/WP-03 (Kimi K2.6 evaluation)
**Severity:** Workflow efficiency (avoidable evaluation dead-end)

### What

Kimi K2.6 (moonshotai/Kimi-K2.6) is a 1T-total-parameter MoE model
with 32B active parameters and 256K context. Public SWE-Bench Verified
score: 80.2% (vs Claude Opus 4.6 at 80.8% — marginally behind, not
ahead; article framing was sensationalized).

D-17-104 initiated a full evaluation cycle (provenance gate, pull,
D-17-12 benchmark) before discovering the hardware constraint:

- BF16 weights split across 46 files (~447 GB uncompressed)
- Aggressive INT4 quantization still exceeds 200 GB
- Mac Studio M3 Ultra has 96 GB unified memory pool
- Model is hardware-blocked by ~3–5× regardless of quantization format

Secondary blockers: Ollama only publishes `kimi-k2.6:cloud` (API-routed,
requires Moonshot API key); LLM Access Doctrine prohibits cloud API keys
in Vault. Provenance gate returned `scan-failed` because the HF repo
requires `trust_remote_code=True` for feature extraction.

### Why this matters

Article-claimed benchmark parity (SWE-Bench, etc.) is meaningless if
the model doesn't fit the target hardware. The evaluation pipeline
(D-17-92 provenance gate, D-17-91 benchmark harness) implicitly assumes
the model is deployable. Without a Step -1 RAM-fit check, evaluation
effort is wasted when the answer is "hardware-blocked" regardless of
benchmark quality.

MoE models compound this: a "32B active params" framing creates a
false impression of RAM requirements (32B active × 0.5 GB/B ≈ 16 GB).
The real constraint is total parameter weight, not active parameter
count, because the full MoE routing table must reside in memory.

### How to apply

RAM-fit check is now Step -1 in `docs/runbooks/pull-new-model.md`.
Before any provenance or evaluation work:

1. Find total parameter count (HF model card `config.json` or README).
2. For MoE: note total params, not active params.
3. Estimate INT4 floor: `total_params_B × 0.5 GB`.
4. Compare to platform pool (96 GB Mac Studio, 48 GB Mac Mini).
5. Check Ollama registry: `:cloud` tag = API-only; `SIZE -` in `ollama list` = no local weights.

If hardware-blocked: chronicle and defer with reactivation criteria.
Do not invest provenance or benchmark time on an undeployable model.

### Note on article framing (2026-05-04)

The article that prompted D-17-104 (thinkpol.ca) compared Kimi K2.6
to Claude/GPT-5.5 on a single sliding-tile word puzzle and framed it as
dramatically superior. Actual SWE-Bench Verified scores: Kimi K2.6 =
80.2%, Claude Opus 4.6 = 80.8%. The Kilo Code review found a 23-point
gap behind Claude Opus 4.7 on multi-agent contention tasks (68 vs 91).
Sensationalized single-benchmark framings should not trigger evaluation
work without a RAM-fit pre-check.

### Cross-references

- D-17-104 (this worked example — DEFERRED)
- D-17-92 (provenance gate, Step 0)
- D-17-91 (benchmark harness, Step 1+)
- `docs/architecture-facts/aider-compute-doctrine.md` (96 GB constraint)
- `docs/runbooks/pull-new-model.md` §Step -1 (RAM-fit gate added)

## Finding 22 — QNAP QTS blocks Docker bridge subnet source IPs; application containers must run on Mac Mini

**Deliverable:** D-17-108 (FlareSolverr migration)
**Date:** 2026-05-04
**Pattern:** Architecture topology constraint — applies to ALL Docker→QNAP network paths

### Canonical statement

QNAP QTS packet-filtering blocks inbound connections from Docker bridge
subnet source IPs (172.23.x.x, 172.25.x.x, etc.) to services bound on
QNAP host interfaces. This affects any Docker container attempting to
reach a QNAP-hosted service directly by host IP:port.

Confirmed blocked paths as of 2026-05-04:

| Source container | QNAP target | Result |
|---|---|---|
| zabbix-server (172.25.x.x) | QNAP Syncthing :8384 | TCP RST |
| prowlarr (172.23.0.12) | QNAP FlareSolverr :8191 | TCP RST |

Mac Mini host (192.168.10.145) reaches both services normally — the
block is selective to Docker bridge subnet source IPs, not all external
IPs.

### Implication for architecture

Services that Docker containers need to reach must not run on QNAP.
This is consistent with the architecture doctrine that QNAP is the NAS
(downloads, media, backups) and Mac Mini Docker is the application tier.
Any pre-architecture-lock QNAP-hosted application container that a Mac
Mini Docker service depends on is broken by design and must be migrated.

### Workaround pattern for QNAP-only data sources

Where the data source (not service) is on QNAP and no Mac Mini-side
alternative exists, use the host-side bridge pattern:
- Push from Mac Mini host (not Docker): `zabbix_sender`, SSH→QNAP
  loopback curl (Syncthing D-17-105)
- Pull via Mac Mini host process: launchd agent that reaches QNAP and
  feeds results to Docker containers via trapper/file/socket

Never add `extra_hosts` pointing Docker containers at QNAP IPs for
application services — the TCP connection will be refused regardless of
name resolution.

### Verification before assuming container-absent

**Finding 20 repeat in D-17-107:** FlareSolverr was assumed absent
because Prowlarr health showed proxy unavailable. Correct probe sequence:

1. Probe from Mac Mini host: `curl http://QNAP_IP:PORT/probe`
2. Probe from inside the consumer container: `docker exec <container> curl ...`
3. If (1) succeeds and (2) fails → QNAP routing block, not absent service
4. If (1) fails → service actually absent

Short-circuiting to step 4 without step 1 is a verification gap that
wastes diagnosis time and can produce wrong remediation (deploying a
service that already exists).

### Cross-references

- D-17-105 (Syncthing — first instance; resolved via host-side launchd sender)
- D-17-108 (FlareSolverr — migrated to Mac Mini Docker)
- Finding 20 (D-17-107 note on probe-before-assume)
- `docs/architecture-facts/download-pipeline-monitoring-doctrine.md`
