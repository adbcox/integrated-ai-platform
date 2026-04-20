# ADR 0023: Phase 6 Closure — Controlled Expansion

**Status**: Ratified
**Package**: CAP-P6-CLOSE-1
**Date**: 2026-04-20
**Authority owner**: governance

## Decision

Phase 6 (Controlled Expansion) is declared **closed_ratified**. Phase 7 definition is the next required governance step before new capability sessions are authorized.

## Evidence

Controlled expansion was proven across three bounded commits (`9fc41af` through `95bb7db`):

1. **qualify-v3 strict gate enforcement** (`9fc41af`) — `--fail-on-incomplete-v8-gates` in `bin/level10_qualify.py` exits 1 when `v8_gate_assertions.all_ready` is False; `--strict-v8-gates` in `bin/level10_promote.py` passes the flag through to qualification on every promote invocation.

2. **benchmark8_ready gate** (`44639dc`) — `summarize_benchmark()` reads `{"classes": {"name": {"passed": bool}}}` format and returns `class_count`, `passed_classes`, `failed_classes`, `all_classes_passed`; `benchmark8_ready` in `evaluate_v8_gates()` requires `class_count >= benchmark_min_class_count` (manifest-driven from `promotion_policy.criteria.benchmark_min_class_count`) and `all_classes_passed=True`.

3. **attribution8_ready gate** (`44639dc`) — `summarize_attribution()` reads `{"orchestration_delta": float, "model_delta": float}` format and emits `has_attribution`; `attribution8_ready` requires `has_attribution=True`.

4. **qualify_v4_artifact_builder** (`95bb7db`) — `bin/qualify_v4_artifact_builder.py` reads `artifacts/stage3_manager/traces.jsonl`, classifies entries by target directory into named benchmark classes, computes pass/fail (acceptance_rate ≥ 0.5), computes `orchestration_delta` and `model_delta` from acceptance/fallback rates, writes `artifacts/codex51/benchmark/latest.json` and `artifacts/codex51/attribution/latest.json`; both artifacts committed at `95bb7db`.

5. **gates True on committed state** — `benchmark8_ready=True` and `attribution8_ready=True` confirmed by `python3 bin/level10_qualify.py --json` at `95bb7db`.

First gate commit: `9fc41af`. Final convergence commit: `95bb7db`. Test count: 57 passing in packet validation.

## Authority

This ADR ratifies:
- `governance/phase6_closure_evidence.json` (package_id: CAP-P6-CLOSE-1)
- `governance/phase6_closure_decision.json` (decision: closed)

No tactical family is unlocked by this closure.

## Next authorized work

Phase 7 definition and canonical roadmap extension are required before new capability sessions are authorized. No Phase 7 capability work may proceed until a governance packet adds Phase 7 to `governance/canonical_roadmap.json` and ratifies the extension. New capability sessions are suspended at `ratification_only` class until that packet is produced and ratified.
