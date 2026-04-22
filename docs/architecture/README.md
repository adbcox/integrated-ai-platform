# Architecture Documentation Index

This directory contains the canonical architecture documents for the integrated AI platform.

## Reading order

Read these in order:

1. `MASTER_SYSTEM_ARCHITECTURE.md` — master architecture source of truth
2. `AUTHORITY_SURFACES.md` — what document or system controls which kind of truth
3. `RUNTIME_SUBSTRATE.md` — shared runtime substrate expectations and boundaries
4. `EXTERNAL_SYSTEMS_POLICY.md` — adopt/build/hybrid policy and external integration rules
5. `DOMAIN_BRANCH_RULES.md` — branch-expansion rules and constraints

## Purpose

These files exist to prevent architecture intent from becoming fragmented across roadmap notes, tactical handoffs, old planning docs, and scattered repo-local guidance.

## Relationship to roadmap docs

- `docs/architecture/*` = architecture truth and platform design direction
- `docs/roadmap/*` = planning, sequencing, grouping, and status control

When roadmap interpretation conflicts with architecture interpretation, architecture controls unless explicitly revised.
