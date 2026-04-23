# Post-Convergence Operating Mode

## Purpose

This document records the operating posture after material convergence of the targeted local-autonomy upgrade path.

It is intended to mark the transition from:
- **build the autonomy substrate**, to
- **operate and extend the governed local-execution platform without drift**.

This document does not override canonical item truth.
Canonical roadmap item state remains in:
- `docs/roadmap/items/RM-*.yaml`

## Phase-change statement

The repository is now to be treated as a **governed local-execution platform**, not merely as a feature repository and not merely as an autonomy-substrate buildout effort.

The targeted local-autonomy closure chain is considered materially converged unless future canonical repo truth contradicts it.

## Canonical operating assumptions

The repo is now expected to operate under these assumptions:

1. canonical item truth lives in `docs/roadmap/items/RM-*.yaml`
2. derived planning and dependency surfaces must mirror canonical item truth
3. human-readable summary documents are tertiary views and must not override canonical item state
4. runtime execution is bounded, sessionized, artifact-emitting, and validation-driven
5. goal-to-execution routing is governed by explicit contracts
6. connector use is policy-gated, deny-unlisted, and subordinate to the governed local runtime
7. archive convergence is executable policy, not manual bookkeeping

## Post-convergence default posture

The repo is no longer in default “build the autonomy substrate” mode.
It is now in **post-convergence operating mode**.

That means:
- future work should assume the local-execution substrate exists unless repo truth says otherwise
- future roadmap work should be evaluated as extensions or consumers of the governed platform
- future closeout claims must obey the same truth, artifact, and validation rules that stabilized the substrate

## Closeout acceptance rule

No roadmap closeout is accepted until the change is:

1. committed
2. pushed
3. remote-visible

Local-only state is not sufficient for accepted closure.

## Permanent operating rules

### 1. Canonical truth first
- always prefer canonical item YAML over summary docs
- summary docs are interpretive views, not authority
- if a summary surface conflicts with item YAML, item YAML wins

### 2. Derived truth must be regenerated, not narrated
- planning and dependency surfaces must be regenerated through repo mechanisms
- do not hand-edit derived artifacts as a substitute for canonical correction and regeneration

### 3. Completion means objective-level closure
- patch success is not item completion
- first-slice usability is not automatically completion
- completion requires the item’s own closeout condition to be truthfully satisfied

### 4. Bounded execution is mandatory
- future work must continue to use bounded scope, explicit validations, artifact evidence, and truth-surface synchronization
- do not accept vague “it should be done” claims without evidence

### 5. Push-confirmed acceptance only
- no pass is fully accepted until the commit is remote-visible
- no roadmap closeout is final while still only local

### 6. Clean-branch end state required
- every accepted pass should end in a clean, reconciled branch state
- residual drift, hold-state ambiguity, or unpushed changes invalidate clean closeout

## Work selection after convergence

Because the autonomy substrate is materially closed, future work selection should default to:

1. preserve governance and anti-drift discipline
2. extend the governed local-execution platform into higher-value branches
3. prefer work that reuses the existing control/runtime/connector substrate
4. avoid re-litigating substrate completion unless new repo truth shows regression or contradiction

## What future work should now look like

Future items should generally fall into one of these categories:

### Platform extension
- new capabilities that reuse the governed local execution substrate
- new control surfaces, ingress channels, and connector consumers

### Connector / workflow expansion
- new integrations that remain subordinate to the connector control plane
- new assistant workflows that consume approved shared connector surfaces

### Domain expansion
- voice/ambient assistant behavior
- news/intelligence
- procurement intelligence
- communication workflows
- business operations workflows

### Governance preservation
- maintenance of canonical truth, regeneration discipline, archive integrity, and acceptance controls

## Drift-prevention rules

Do not allow future work to reintroduce these failure modes:

- summary surfaces overriding canonical truth
- local-only closure being treated as accepted completion
- partial validator success being treated as full completion
- directly connected gaps being left open while claiming closure
- unbounded execution instead of explicit contracts and evidence

## When to re-open substrate questions

Do not re-open autonomy-substrate completion by default.
Re-open it only if canonical repo truth shows one or more of the following:

- regression in the local execution path
- contradiction between canonical item state and runtime reality
- reintroduced hold state or archive inconsistency
- broken selector / blocker / queue truth
- failure of the bounded execution and validation model

## Reader guidance

Read these in order when operating in post-convergence mode:

1. `docs/roadmap/ROADMAP_AUTHORITY.md`
2. canonical item YAML under `docs/roadmap/items/`
3. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
4. `docs/roadmap/ROADMAP_MASTER.md`
5. `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`
6. derived planning surfaces and execution artifacts as needed

## Notes

This document is intentionally short and strict.
Its purpose is not to restate every architectural detail.
Its purpose is to preserve the repo’s convergence outcome and keep future work from drifting back into ambiguous, local-only, or narrative closeout behavior.