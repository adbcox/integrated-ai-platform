# ADR-0007: Autonomy Scorecard

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation), Phase 7 (capability_session — closed_ratified)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-V7-01, AS-11-HANDOFF-V7, governance/canonical_roadmap.json, governance/phase_gate_status.json

---

## Context

The platform's primary goal is real capability gain toward the Codex 5.1 replacement milestone — not infrastructure or benchmarks. Measuring progress requires a scorecard that quantifies:
1. How much work the platform can do autonomously (without human escalation)
2. The quality of autonomous outputs (semantic generation rate, validation pass rate)
3. The cost of escalation paths (fallback rate, intervention frequency)

The V7 handoff (AS-V7-01) and Phase 7 closure evidence (`governance/phase7_closure_evidence.json`) established that all 9 v8 capability gates are READY. The autonomy scorecard formalizes what those gates measure and how to interpret regression.

Phase 7 is closed_ratified at commit `f5013c3`. The scorecard must be compatible with the Phase 7 evidence baseline.

---

## Decision

The **autonomy scorecard** is a structured assessment of platform capability across five dimensions:

```
autonomy_scorecard:
  scorecard_id:         string
  session_id:           string
  phase_id:             int
  generated_at:         iso8601
  baseline_commit:      string   # git SHA of evidence baseline
  dimensions:           object   # five scored dimensions (below)
  overall_autonomy_grade: enum   # A | B | C | D | F
  regression_detected:  bool
  regression_details:   list

dimension (each):
  dimension_id:         string
  name:                 string
  score:                float     # 0.0–1.0
  evidence_ref:         string
  gate_status:          enum      # READY | PARTIAL | BLOCKED | NOT_MEASURED
```

**Five scored dimensions**:

1. **semantic_generation_rate** — fraction of modifications generated semantically (non-deterministic fallback) on the bounded benchmark task set. Phase 7 baseline: 88.9% on 18-task set.

2. **validation_pass_rate** — fraction of generated modifications that pass `make check` / `make quick` / real-path validation on first attempt. Target: ≥ 90%.

3. **real_path_coverage** — fraction of bounded task categories (guard clause, assertion, replacement, refactor) with at least one validated real-path execution. Phase 7 baseline: all 9 v8 gates READY.

4. **escalation_rate** — fraction of session steps requiring human or control-window escalation. Lower is better. Includes HARD_STOP events, scope overflows, and permission rejections.

5. **governance_conformance** — fraction of produced artifacts that are `bundle_valid=true` with conformant schema references. Must be 1.0 for governance sessions.

**Overall grade mapping**:
```
A: semantic_generation_rate >= 0.85 AND validation_pass_rate >= 0.90 AND escalation_rate <= 0.10
B: semantic_generation_rate >= 0.70 AND validation_pass_rate >= 0.80 AND escalation_rate <= 0.20
C: semantic_generation_rate >= 0.50 AND validation_pass_rate >= 0.70
D: any required dimension gate_status == BLOCKED
F: regression_detected == true with severity >= HIGH
```

---

## Consequences

**Positive**:
- The scorecard provides a single governance artifact that records capability state at any phase transition
- `regression_detected=true` is a hard gate on Phase 1 closure — regressions must be resolved before ratification
- The five dimensions correspond directly to the BOUNDED_SESSION_DISCIPLINE requirements in CLAUDE.md

**Negative / constraints**:
- `overall_autonomy_grade` is computed from dimension scores; subjective override is not permitted
- Scorecard must reference a specific `baseline_commit`; floating comparisons are non-conformant
- A `D` grade (any BLOCKED gate) blocks phase progression regardless of other dimension scores

**Phase gate impact**:
- Phase 0 closure must include an autonomy scorecard with `phase_id=0` as part of the closure artifact bundle
- Phase 1 ratification requires `regression_detected=false` and `overall_autonomy_grade` in {A, B, C}
- Future phases (8+) must produce scorecards that improve on or maintain the Phase 7 baseline
