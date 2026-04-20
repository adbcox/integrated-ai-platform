# ADR 0024: Phase 7 Definition — V8 Gate Closure and Codex 5.1 Benchmark

**Status**: Ratified
**Package**: CAP-P7-DEF-1
**Date**: 2026-04-20
**Authority owner**: governance

## Decision

Phase 7 (`v8_gate_closure_and_codex51_benchmark`) is hereby **defined and authorized**. Phase 7 capability sessions may proceed immediately.

## Phase 7 Definition

**Name**: `v8_gate_closure_and_codex51_benchmark`

**Goal**: Close all v8 upgrade gates through real stage8 plan execution and produce the first complete codex51 replacement benchmark run with actual campaign data.

**Entry precondition**: Phase 6 closed_ratified (CAP-P6-CLOSE-1 at `0649d79`). ✓

**Capability session targets** (bounded sessions; any ordering):
1. Real stage8 execution trace data causing `stage8_ready`, `manager8_ready`, `rag8_ready`, `worker8_ready` gates to become True in `level10_qualify --json`
2. First `codex51_replacement_benchmark --write-report` run consuming real `artifacts/codex51/campaign/runs.jsonl`
3. `qualify_v4_artifact_builder.py` extended to consume codex51 benchmark output when present; stage3 fallback retained when not
4. `level10_qualify --fail-on-incomplete-v8-gates` exits 0 (all 9 gates True)
5. `qualify_v4` status advanced to `complete` in `config/promotion_manifest.json`

**Narrative roadmap correspondence**: `docs/version15-master-roadmap.md` Phase A — "Stabilize v8 completions"

**Exit criteria**:
- `all_ready: true` in `python3 bin/level10_qualify.py --json` output
- real codex51 campaign benchmark artifact present (non-proxy class evidence)
- `regression_qualification_framework.status: complete` in promotion manifest

## Authority

This ADR authorizes:
- `governance/phase7_definition.json` (package_id: CAP-P7-DEF-1, authorization_status: authorized)
- Phase 7 capability sessions to proceed immediately

No tactical family is unlocked by this definition.

## Next authorized work

Phase 7 capability sessions may begin immediately. The highest-leverage first session targets `stage8_ready`, which requires real stage8 plan execution to produce trace data in `artifacts/manager6/traces.jsonl`.
