# ADR 0007 — Next Allowed Package Class After RECON-W2

Status: accepted (RECON-W2)
Owner: governance/next_package_class.json
Baseline commit: 53ae4d4f177b176a7bffaa63988f63fa0efa622c

## Context

RECON-W2 closes Phase 0, ratifies Phase 1, and records Phase 2 as
`adopted_partial`. It does not unlock any tactical family, and it does not
close Phase 2. The next-allowed package class must reflect that state.

## Decision

1. `governance/next_package_class.json#current_allowed_class` is
   `ratification_only` after RECON-W2.
2. A future move to `capability_session` is permitted only when Phase 2 is
   ratified closed (see ADR 0005). That transition requires committed
   real-capability evidence and a reconciliation package that updates
   `governance/phase2_adoption_decision.json#decision` to `closed`.
3. A future move to `tactical_review` is permitted only when a per-family
   unlock review packet satisfies the preconditions recorded in
   `governance/tactical_unlock_criteria.json` (see ADR 0006).
4. This ADR does not authorize any tactical package, capability-session
   package, or feature-expansion package at baseline commit.

## Consequences

- Agents executing on this branch must treat `ratification_only` as an
  upper bound on the packet class until a subsequent ADR lifts it.
- Planning artifacts or conversations that assume broader scope must defer
  to this ADR.

## Supersedes

- The RECON-W1 value `reconciliation_only` for
  `next_allowed_package_class`, which is superseded by `ratification_only`
  as the post-RECON-W2 value.
