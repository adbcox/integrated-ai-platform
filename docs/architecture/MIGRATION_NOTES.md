# Architecture Migration Notes

## Purpose

This document records how architecture content was consolidated from scattered sources into the current canonical architecture set under `docs/architecture/`.

## Why this exists

The platform accumulated architecture truth across:

- revised target architecture handoffs
- control-window adoption packets
- roadmap master files
- execution and governance notes
- scattered repo-local documents
- chat-derived planning material

This created ambiguity about what was current, what was historical, and what was actually authoritative.

## Migration outcome

The canonical architecture set is now:

- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/AUTHORITY_SURFACES.md`
- `docs/architecture/RUNTIME_SUBSTRATE.md`
- `docs/architecture/EXTERNAL_SYSTEMS_POLICY.md`
- `docs/architecture/DOMAIN_BRANCH_RULES.md`
- `docs/architecture/PHASE_MODEL.md`
- `docs/architecture/CURRENT_STATE_VS_TARGET_STATE.md`
- `docs/architecture/TRACEABILITY_TO_ROADMAP.md`
- `docs/architecture/GLOSSARY.md`
- `docs/architecture/DECISION_REGISTER.md`
- `docs/architecture/CHANGE_CONTROL.md`
- `docs/architecture/REVIEW_CHECKLIST.md`

## Migration rule

Once durable content has been incorporated into the canonical architecture set, the source handoff or planning note should be treated as:

- historical input
- explanatory support
- migration provenance

It should not be treated as equal authority with the canonical repo-owned architecture documents.

## Ongoing rule

If a new architecture handoff or review document introduces durable platform rules, those rules must be folded into the canonical architecture set in the same workstream or immediately after.
