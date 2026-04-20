# ADR 0021: Phase 5 Closure — Qualification Promotion Learning Convergence

**Status**: Ratified
**Package**: CAP-P5-CLOSE-1
**Date**: 2026-04-20
**Authority owner**: governance

## Decision

Phase 5 (Qualification Promotion Learning Convergence) is declared **closed_ratified**. Phase 6 capability sessions are authorized.

## Evidence

Qualification-promotion-learning convergence was proven across four bounded commits (`a801e51` through `c280cb6`):

1. `summarize_gate_chain()` — stage3_manager trace data loaded into `bin/level10_qualify.py`; gate-chain evidence summarized (total, accepted, fully_qualified, smoke_fallback, partial, gate_coverage, discovery_mode_distribution, classification_distribution)
2. `gate_chain_ready` hard gate — added to `evaluate_v8_gates()`; requires full_qualification_rate ≥ threshold and `gate_coverage.g4_repo_quick > 0`; `all_ready` structurally false when evidence absent
3. Promotion gate matrix — `gate_chain_ready` in both `candidate_promote_requires` and `stage6_promote_requires` in `bin/level10_promote.py`; any promote action converts to hold when gate-chain evidence is insufficient
4. First-class subsystem — `gate_chain` added to `evaluate_subsystems()` with manifest-driven threshold from `promotion_policy.criteria.gate_chain_min_full_qualification_rate`; added to `_preview_decision()` `core_ready` check alongside `stage_system`, `manager_system`, `rag_system`, `regression_framework`; `gate_chain` entry added to `subsystem_levels` in `config/promotion_manifest.json`

First gate commit: `a801e51`. Final convergence commit: `c280cb6`. Test count: 98 passing.

## Authority

This ADR ratifies:
- `governance/phase5_closure_evidence.json` (package_id: CAP-P5-CLOSE-1)
- `governance/phase5_closure_decision.json` (decision: closed)

No tactical family is unlocked by this closure.

## Next authorized work

Phase 6 (`controlled_expansion`) capability sessions may now proceed.
