# Runbook: Retire a Service (Canonical Decommission Flow)

**Status:** Active doctrine (authored D-17-57, 2026-05-03)  
**Scope:** Any platform service retirement where runtime state, framework state, and doctrine state must all converge.

## Why this exists

A service is not retired when a container is stopped. Retirement is complete only when all authority surfaces agree:

- framework/deliverable state (`docs/PROJECT_FRAMEWORK.md`),
- runtime substrate (`~/.platform-registry/inventory.json` + live containers),
- secrets/app-role substrate (Vault + local sidecar artifacts),
- architecture/doctrine references.

This runbook codifies the anti-drift pattern surfaced in D-17-34 Findings 2-4.

## Inputs (required)

- Service identifier(s): container name, compose service key, Caddy route(s), Vault path(s).
- Retirement decision reference: deliverable ID and closeout scope.
- Disposition plan for data artifacts: archive/preserve/delete.
- Operator decision on secret disposition: rotate/destroy/defer.

## Retirement flow

1. **Create/enter retirement deliverable**
- Add or update a framework row for the retirement work package (`D-NN-MM`) and mark `IN PROGRESS`.
- Establish explicit gates for destructive steps and a surface-back checkpoint.

2. **Capture pre-flight evidence (read-only)**
- Confirm whether consumers still depend on the service (`depends_on`/reverse deps from registry).
- Confirm whether external routes still target it (Caddy + DNS authority records).
- Snapshot runtime/service logs sufficient for forensics.

3. **Archive mutable state before mutation**
- Archive persistent volumes/config dirs to canonical store (QNAP/manual path or equivalent).
- Record integrity hash (sha256) of archive artifact(s).
- Define retention horizon and expiration date.

4. **Runtime retirement**
- Stop/remove runtime service (container/process) using canonical stack lifecycle path.
- Remove or comment service definition from compose/deployment source (preserve historical block if doctrine requires).
- Refresh runtime registry substrate.

5. **Secret/AppRole disposition**
- Evaluate each secret surface separately:
  - AppRole role + policy
  - sidecar role-id/secret-id files
  - rendered credentials directories
  - secret data path(s)
- Apply operator-approved action per surface:
  - destroy (remove),
  - rotate (replace),
  - defer (retain with rationale).

6. **Authority-surface cleanup**
- Update architecture docs and dependency graphs to remove retired runtime node.
- Preserve historical references in closeout records; avoid rewriting history.

7. **Framework/OpenProject closure**
- Mark deliverable `DONE` with concrete execution evidence (not recommendation-only language).
- Ensure OpenProject canonical WP reflects closure state after sync.

8. **Doctrine/chronicle closeout**
- Append worked-example findings if this retirement exposed a new class of drift.
- Record what was intentionally not touched (scope boundary), with rationale.

## OpenProject + framework checklist

- Framework row exists and status transitions: `IN PROGRESS` -> `DONE`.
- Closeout doc includes:
  - what was true at start,
  - what changed,
  - what was deliberately out-of-scope,
  - archive location + hash evidence.
- OpenProject work package closes via canonical sync path (framework-driven).

## Vault/credential disposition checklist

For each retired service, explicitly classify each item as `destroy`, `rotate`, or `defer`:

- Vault AppRole (`auth/approle/role/<service>`)
- Vault policy (`<service>-policy`)
- Local AppRole files (`~/.vault-approle/<service>/`)
- Rendered sidecar secrets (`~/.vault-agent-secrets/<service>/`)
- Secret data path(s) (`secret/<service>/*`)

No implicit deletions.

## Filesystem artifact handling checklist

- Pre-retirement snapshot/archive captured.
- Hash recorded.
- Retention period recorded.
- Restore path documented.
- Local defense-in-depth copy policy decided (keep/remove).

## Worked example: Sportarr retirement record (2026-05-01)

Reference: `docs/_retired/sportarr-2026-05-01.md`

What it demonstrates:
- Retirement decision + reversal trail can coexist in one immutable historical record.
- "Retirement record as future restoration playbook" should preserve steps and gate questions, not just disposition.
- Archive/preservation decisions must be explicit (volume retained; restoration reversible).
- Reversal evidence should append (not overwrite) original retirement rationale.

## Worked example: Home Assistant container retirement closure (D-17-34)

Reference: `docs/phase-17/d-17-34/CLOSEOUT_2026-05-03.md`

What it demonstrates:
- Recommendation-only state is not completion (Finding 2 / F7).
- Retirement includes secret-surface cleanup, not just container removal (Finding 3).
- CMDB/runtime/doc surfaces can disagree silently unless retirement closes all of them (Finding 4).

## Restoration-record preservation rule

When retiring a service, preserve enough evidence for future operator reversal:
- exact compose/runtime path,
- archived state location,
- known failure mode at retirement time,
- concrete restore sequence.

A retirement record is both a closure artifact and a potential restoration playbook.
