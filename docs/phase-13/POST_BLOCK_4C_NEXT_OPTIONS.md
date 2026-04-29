# Post-Block-4.C — Next Options Readiness Sheet

**Date:** 2026-04-29
**Author:** session continuity (post-Block-4.C closeout)
**Status:** Decision pending. Operator picks one path; this document
does not commit to any of them.

Block 4.C closed at commit `ff05159`. NetBox is authoritative; all
three consumers read through `cmdb_source.py`; YAML fallback works;
regression probe is clean (PASS=15 FAIL=0 WARN=3 at gate
`post-4c-cleanup`); 17 C6 follow-ups recorded, none gating.

This sheet enumerates three candidate next blocks. They are not
mutually exclusive over time, but only one should run next.

---

## Option A — Operating-model doctrine block *(recommended first)*

**Estimate:** 2–3 h
**Prereqs:** none
**Reversibility:** trivially reversible (docs only)

### What it is

A short doctrine-only block that codifies the patterns Block 4.C
surfaced as durable guidance, before they decay into tribal
knowledge. No code changes; only ADRs and the doctrine register.

### Scope

1. **ADR — NetBox as authoritative CMDB.** Decision, alternatives
   considered (homegrown YAML, InvenTree-only, Netshot), the dual-
   source loader as the migration vehicle, and the planned
   `CMDB_SOURCE` default flip (C6 #17).
2. **ADR — Round-trip equivalence at migration time.** Discovery #16
   promoted to doctrine. The rule: when you migrate authoritative
   data between stores, prove byte-identical equivalence at the
   migration commit, not at the deprecation commit.
3. **ADR — Staged-toggle pattern for source migrations.** Default-old
   / opt-in-new env flag, single shared loader, identical container
   image, dual paths verified before flip. Generalizes beyond CMDB.
4. **Doctrine register update** — pull C6 follow-ups #2 (upstream
   pinning), #3 (healthcheck pattern), #4 (upstream-flow default),
   #15 (first-batch verify), #16 (round-trip equivalence) into
   `docs/architecture/DECISION_REGISTER.md` as canonical patterns.
5. **Runbook** — `docs/runbooks/migrate-source-of-truth.md` derived
   from the C5.2 evidence package; turns the dual-source-loader
   recipe into a reusable playbook.

### Why first

Doctrine work decays fastest. The patterns are crisp now because
the migration is one commit behind us; in two weeks they will
require re-derivation. The block also produces no new infra to
operate, so it cannot generate new toil.

### Exit gate

ADRs merged, decision register updated, runbook reviewable. No code
or container changes. Regression probe re-run only as a smoke test.

---

## Option B — Connector hardening block

**Estimate:** 4–6 h
**Prereqs:** none (Plane is live; tests can run against the staging
project rather than the production roadmap project)
**Reversibility:** code-level; reversible via revert

### What it is

A focused audit and hardening pass on `framework/plane_connector.py`,
driven by the bugs found during C4 backfill (Discoveries #10–#15).
The connector is now the single highest-blast-radius integration in
the platform — it can write to 600+ Plane issues — and we know it
has at least one untested apply path.

### Scope

1. **Discovery #14 fix** — `create_issue` builder bug at line 360
   (current code drops the `name` field under one parameter shape).
   Reproduce, fix, regression test.
2. **Discovery #13 closure** — dry-run currently skips the apply
   path. Add an end-to-end integration test that exercises the apply
   path against a Plane staging project, asserts the resulting
   issue/label state matches the request, and tears down.
3. **Discovery #10 — rate-limit handling audit.** Walk every
   consumer of `plane_connector.py`. Confirm 429 retries are
   uniform. Add the per-endpoint rate-limit finding from Block 4.B
   addendum to the connector's docstring as a constraint, not a
   suggestion.
4. **Discovery #11 — error class hierarchy audit.** Today the
   connector raises both bare `Exception` and typed errors
   inconsistently. Pick a hierarchy, propagate, update consumers'
   except clauses.
5. **Discovery #12 — pagination termination contract.** Document the
   exact stop condition (next-page token vs empty results vs HTTP
   204) in the connector README; add a unit test that exercises a
   2-page sequence with the terminal page exactly at the limit.
6. **Discovery #15 — first-batch verify.** Add a helper that runs
   the first batch synchronously and asserts the response shape
   before continuing; consumers opt in via a flag.

### Why second

It's higher-value than doctrine but spends real connector quota and
risks a flaky test against Plane. Better to do this when the
operator has a clear test window. Some sub-items (e.g. #14 fix) are
fast standalone wins if the operator wants a single-day deliverable.

### Exit gate

All six items closed; connector test suite green; one apply-path
integration test runs in CI as a smoke gate.

---

## Option C — Block 4.D — InvenTree deployment + supplier integrations

**Estimate:** 8–12 h (one full work session)
**Prereqs:** Block 4.C closed ✅; Vault populated with Mouser and
DigiKey API credentials (not yet present — operator action)
**Reversibility:** moderate; deployment is reversible by `compose
down` + restic restore of any persistent data, but supplier API
calls cannot be unmade

### What it is

Deploy InvenTree as the platform's hardware/component CMDB
counterpart to NetBox. NetBox owns *what is running and how it
talks*; InvenTree owns *what physical parts exist and where they
came from*. Cross-reference the two so a service tied to a device in
NetBox can resolve the physical components in InvenTree.

### Scope

1. **Pre-deploy** — Vault entries for Mouser + DigiKey API tokens;
   AppRole `inventree`; compose stack on `control-center-net`;
   port-conflict pre-check (Discovery #1).
2. **Deploy** — InvenTree + Postgres + Redis sidecar pattern;
   Vault Agent rendering credentials; healthcheck per pattern #3;
   data persisted to a named volume; Restic include path added.
3. **CSV import** — 129-component inventory from
   `docs/inventory/components-2026-04.csv` into InvenTree parts.
4. **Supplier integrations** —
   - Mouser API: SKU lookup, datasheet URL, current price.
   - DigiKey API: same plus stock level.
   - Both integrations rate-limit-aware (apply Discovery #10
     learnings).
5. **NetBox cross-reference** — custom field on `dcim.device`
   pointing at the InvenTree parts list URL for that device's BOM.
6. **Closeout** — gate `block-4d-final`; regression probe; PHASE_13
   closeout doc.

### Why not first

It is the largest of the three, brings new external API surface
(Mouser/DigiKey), and is the only one with a real-world side effect
(supplier API calls). The operator needs to be in a position to
watch it. There is also no near-term consumer of the parts data —
nothing in the platform breaks without it — so urgency is low.

### Exit gate

InvenTree live and authoritative for parts; 129 components imported
and reconciled; supplier integrations green on a sample of 5 parts;
NetBox→InvenTree cross-reference visible in topology API.

---

## Recommendation

**Run Option A next.** It is the smallest, most reversible block
with the highest decay rate. After A, the operator picks B vs C
based on whether the next priority is platform reliability
(connector hardening) or platform breadth (parts inventory).

A is also the only one of the three that produces no new running
component, so it cannot generate operational surprise during the
next session.

## Decision log slot (to be filled when chosen)

| Field | Value |
|---|---|
| Block chosen | _(pending operator)_ |
| Reasoning | _(pending operator)_ |
| Start commit | _(pending)_ |
| Target close commit | _(pending)_ |
