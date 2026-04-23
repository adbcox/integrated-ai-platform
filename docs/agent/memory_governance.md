# Memory Governance Guide

This guide defines what execution memory can persist, who can approve persistence,
and which evidence is required before updates become canonical.

## Memory Tiers

- `root`: Architecture and safety constraints. Persistent and governance-controlled.
- `modular`: Subsystem operating docs and validated module rules. Persistent with scoped owner review.
- `scoped`: Session-local context and temporary notes. Not canonical by default.
- `known_failures`: Reproducible failure patterns and validated fixes.

## Persistence Decision Flow

1. Classify the candidate memory using `governance/memory_classification.yaml`.
2. Capture provenance fields from `governance/memory_provenance_policy.yaml`.
3. Run required validations for the selected tier.
4. Persist only if all validation gates pass.
5. Record an auditable evidence pointer for persistent tiers.

## Root vs Ephemeral Examples

- Root:
  - "Archive-state updates must reconcile canonical and derived roadmap surfaces."
  - "Forbidden file families remain blocked for bounded execution."
- Scoped:
  - "Temporary hypothesis about a validator failure during this run."
  - "Intermediate notes while tracing an unresolved dependency."

## Summarization Rules

- Keep safety, authority, and rollback constraints verbatim.
- Compress repetitive logs and intermediate reasoning only when outcome and evidence
  pointers remain intact.
- Never summarize away owner, timestamp, or validation evidence for persistent entries.

## Cross-References

- Classification schema: `governance/memory_classification.yaml`
- Provenance policy: `governance/memory_provenance_policy.yaml`
- Agent operating docs baseline: `docs/agent/commands.md`, `docs/agent/validation_order.md`
