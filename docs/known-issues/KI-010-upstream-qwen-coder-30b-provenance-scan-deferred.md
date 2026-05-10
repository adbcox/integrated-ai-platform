---
ki: KI-010
title: Upstream Qwen/Qwen3-Coder-30B-A3B-Instruct provenance scan deferred to Mac Studio post-Headscale-resolution
severity: LOW
status: OPEN
discovered: 2026-05-10
phase: D-17-10 governance fulfillment (Block B WP-04, MLX integration test)
---

# KI-010: Upstream Qwen/Qwen3-Coder-30B-A3B-Instruct provenance scan deferred to Mac Studio

## Symptom

The Cisco Model Provenance Kit scan against upstream
`Qwen/Qwen3-Coder-30B-A3B-Instruct` fails on Tier 1 / Tier 2 hardware
due to unified-memory exhaustion. The kit downloads ~60 GB of BF16
safetensors and computes weight-level fingerprints, which requires
>32 GB resident RAM during the fingerprint step.

Two scan attempts confirmed this hardware ceiling:

| Date | Host | RAM | Scan target | scan_rc | Mode |
|---|---|---|---|---|---|
| 2026-05-04 | mac-mini | 16 GB | `Qwen/Qwen3-Coder-30B-A3B` | 1 | graceful failure (kit declined to load weights) |
| 2026-05-10 | macbook-pro | 32 GB | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 137 | SIGKILL/OOM after ~9564s during fingerprint computation |

## Root Cause

Hardware constraint, not catalog absence. The `qwen--qwen` family IS
present in the deep-signals fingerprint DB (152 parquets, 39 families,
SHA `b94040b6…`); a successful scan against the upstream Qwen3-Coder
would be expected to return `verified-specific` (if Coder-30B variant
fingerprints are present) or `verified-base-family` (matching against
`qwen--qwen` base at the typical 0.85–0.95 fine-tune similarity band).
The scan did not get that far on either host because the fingerprint
computation step itself OOMs.

This is the BF16 fingerprinting workload only — operational use of the
MLX-3bit serving derivative is unaffected. The MLX-3bit asset is
12.5 GiB on disk, runs cleanly on macbook-pro 32 GB (vllm-mlx process
RSS 1.7 GB; weights resident in Metal GPU heap). Governance attestation
is what's blocked, not serving.

## Affected

- **Verdict on `docs/_provenance/Qwen__Qwen3-Coder-30B-A3B-Instruct.json`:**
  scan-failed/SCAN_OOM, operator-accepted (Path B) 2026-05-10. Falls
  back to `operator_confirmed` doctrine class (per
  `config/model_provenance/ollama_to_hf_mapping.yaml` line 23,
  operator-confirmed 2026-05-05).
- **MLX-3bit derived disposition** for
  `mlx-community/Qwen3-Coder-30B-A3B-Instruct-3bit`:
  `quantization-of-operator-confirmed-base` (per D-17-92
  quantization-divergence doctrine), distinguishable from
  `quantization-of-verified-base` (the doctrine class that would apply
  post-rescan).
- **Integration test gate** at
  `docs/orchestration-layer-build-mlx-integration-test.md` §9: gate
  status "scan-failed/SCAN_OOM, operator-accepted (Path B)" until
  rescan promotes to verified-*.

## Mitigation Applied

Path B operator-accepted SCAN_OOM disposition. The upstream HF ID was
already operator-confirmed pre-attempt (architecture + parameter-count
+ context-window match: qwen3moe + 30.5B / 3B active + 262K), so the
fallback evidentiary class is the doctrine-acknowledged next-best.

D-17-10 governance obligation from the integration test override
(`docs/_provenance/overrides.log` 2026-05-10T19:19:00Z) is satisfied
via this disposition. Migration commit (orchestration-layer-build) is
unblocked. See `docs/_provenance/backfill-2026-05-10.md` for the full
disposition record.

## Trigger to close

Mac Studio (96 GB unified memory) reachable via Headscale. Then:

```sh
scripts/verify-model-provenance.sh --hf Qwen/Qwen3-Coder-30B-A3B-Instruct
```

Expected verdict: `verified-specific` or `verified-base-family`.

## Closure procedure

1. Run wrapper on Mac Studio (per command above)
2. Per-model JSON record at
   `docs/_provenance/Qwen__Qwen3-Coder-30B-A3B-Instruct.json` is
   overwritten by wrapper with new verdict + top_matches
3. Append a "Promotion" subsection to
   `docs/_provenance/backfill-2026-05-10.md` noting verdict, rescan
   date, and host
4. Update `docs/orchestration-layer-build-mlx-integration-test.md` §9
   "Provenance gate status:" line with the new verdict and remove
   the KI-010 reference
5. Flip this file's status to RESOLVED with close-out summary

Verdict promotion automatically promotes the MLX-3bit derivative chain
from `quantization-of-operator-confirmed-base` to
`quantization-of-verified-base` per D-17-92.

## Cross-references

- Backfill record: `docs/_provenance/backfill-2026-05-10.md`
- Per-model JSON: `docs/_provenance/Qwen__Qwen3-Coder-30B-A3B-Instruct.json`
- Override entry: `docs/_provenance/overrides.log` 2026-05-10T19:19:00Z
- Mapping config: `config/model_provenance/ollama_to_hf_mapping.yaml`
  `hf_direct_models` block (lines 203–224)
- Integration test doc: `docs/orchestration-layer-build-mlx-integration-test.md` §9
- Doctrine: `docs/architecture-facts/model-provenance.md` (D-17-92, D-17-122)

## Impact

- No data loss risk
- No service-impact: MLX-3bit serving operates within hardware bounds
- Governance attestation deferred from `verified-*` to
  `operator_confirmed` — doctrine-acknowledged downgrade, not a gap
- No blocker for migration commit (D-17-10 satisfied via Path B)
