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
