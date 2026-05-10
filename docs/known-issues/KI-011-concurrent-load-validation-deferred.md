---
ki: KI-011
title: Concurrent-load (N=3-5) validation for vllm-mlx deferred to Mac Studio post-Headscale-resolution
severity: LOW
status: OPEN
discovered: 2026-05-10
phase: Orchestration-layer-build closeout (vllm-mlx stunt-double promotion, commit 81db99ea)
---

# KI-011: Concurrent-load (N=3-5) validation for vllm-mlx deferred to Mac Studio

## Symptom

Integration test 2026-05-10 validated single-stream `tool_calls`
structurally clean in both stream and non-stream modes (TASK-0001
wall-clock 368s, 21.5% improvement vs Ollama baseline 469s).
Concurrent-load behavior at N=3-5 simultaneous requests was NOT
tested on the integration host (MacBook 32 GB). The server flag
`--max-num-seqs 4` is set per the launchd plist
`com.adriancox.vllm-mlx`; concurrent-sequence headroom + RAM
pressure under load remain empirically unvalidated.

## Root Cause

Scope deferral. The integration test's binary pass/fail criterion
was structured `tool_calls` emission — single-stream sufficed to
prove the Finding 2 failure mode (MLX engines leaking `<tools>`
markers as text in `message.content`) did not materialize. N>1
contention is a different validation axis (throughput, memory
pressure under load, per-request latency degradation, queue
saturation behavior) and was descoped as out-of-scope for the
binary promotion gate.

Documented at commit `81db99ea` body paragraph 2: "Concurrent-load
validation (N=3-5) parked pending Mac Studio reachability." This KI
is the first doc-level surface for that deferral; prior to it the
parked-status lived only in the commit message.

## Affected

- **Integration test gate** at
  `docs/orchestration-layer-build-mlx-integration-test.md` §9:
  post-promotion concurrent-load behavior unvalidated. Reliance on
  single-stream evidence + the `--max-num-seqs 4` plist setting.
- **vllm-mlx default stunt-double posture:** serving operates
  cleanly at N=1 (proven by TASK-0001); N>1 behavior is empirically
  unknown. No data loss risk; no current service impact (single-
  stream is the validated path).

## Mitigation Applied

- `--max-num-seqs 4` set in the launchd plist as a conservative
  ceiling pending validation. Limits the vllm-mlx engine to 4
  concurrent sequences regardless of incoming request volume.
- Ollama stunt-double plist (renamed `.plist.disabled` per the
  migration commit) preserved for one-step rollback. If concurrent-
  load issues surface in production-shaped workloads on MacBook
  before the Mac Studio rescan opportunity, rollback is:
  `launchctl load ~/Library/LaunchAgents/com.adriancox.ollama-stunt-double.plist`.

## Trigger to close

Mac Studio (96 GB unified memory) reachable via Headscale, with
vllm-mlx deployable there. Then run a concurrent-load probe: 3-5
parallel TASK-0001-shaped requests via LiteLLM at port 4000
routing through to vllm-mlx; capture per-request wall-clock + p95
latency + peak RAM + counts of 429 / timeout / structural-failure
responses.

## Closure procedure

1. Mac Studio runs vllm-mlx with the same plist shape
   (`--max-num-seqs 4` initially; adjust upward if Mac Studio's
   96 GB justifies higher concurrency).
2. Run the concurrent-load probe (3-5 parallel requests, TASK-0001
   shape).
3. Capture results either in
   `docs/orchestration-layer-build-mlx-integration-test.md` (appended
   as a new section) or in a sibling
   `docs/orchestration-layer-build-mlx-concurrent-load-results-YYYY-MM-DD.md`.
4. Update the integration test §9 "Concurrent-load validation status:"
   line with the validated N=3-5 throughput numbers + observed RAM
   pressure + per-request p95 latency.
5. Flip this KI's status to RESOLVED with close-out summary.

## Cross-references

- Integration test doc: `docs/orchestration-layer-build-mlx-integration-test.md` §9
- Migration commit: `81db99ea` (parked statement in body paragraph 2: "Concurrent-load validation (N=3-5) parked pending Mac Studio reachability.")
- Orchestration-layer-build closeout commit: `d8a72af9`
- Parallel Mac Studio deferral: KI-010 (upstream Qwen provenance scan — both KIs close together when Headscale reachability lands)
- vllm-mlx plist: `~/Library/LaunchAgents/com.adriancox.vllm-mlx.plist` (currently `--max-num-seqs 4`)

## Impact

- No data loss risk.
- No current service impact: single-stream operation is the
  validated path; concurrent-load behavior is unknown but not
  actively broken.
- Operational ceiling: `--max-num-seqs 4` is a conservative bound.
  Productionizing the stunt-double beyond this concurrency level
  requires empirical justification (the probe above) before raising.
