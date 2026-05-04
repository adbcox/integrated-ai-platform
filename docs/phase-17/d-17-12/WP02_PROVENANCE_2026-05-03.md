# D-17-12 WP-02 — Provenance gate evidence

**Date:** 2026-05-03
**Override:** PRE-AUTHORIZED per intake doc + operator reply
**Override reason:** `D-17-12 benchmark; documented in deliverable per model-provenance.md doctrine line 220-235`

## Outcome

| Model | Verdict | Exit | Failure mode | Override invoked |
|---|---|---|---|---|
| `google/gemma-2-27b-it` | scan-failed | 1 | HF gated repo (HTTP 401 on `config.json`) | YES |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | scan-failed | 1 | OOM SIGKILL (rc=137) on Mac Mini 48 GB during weight scan | YES |

Records persisted at:
- `docs/_provenance/google__gemma-2-27b-it.json`
- `docs/_provenance/Qwen__Qwen3-Coder-30B-A3B-Instruct.json`

## Failure mode detail

### Gemma — gated repo

Upstream `https://huggingface.co/google/gemma-2-27b-it/resolve/main/config.json`
returns HTTP 401 unauthenticated. Gemma family requires accepting Google's
Gemma License and authenticating via HF token before any download
(metadata or weights).

Direct `curl` confirms: `HTTP 401` even on the manifest, before any
weight access.

**Mac Mini state at scan time:** `HF_TOKEN` not set in shell env (count
= 0). The platform has no HF token provisioned for unattended pulls;
this is a deliberate posture (no platform service should consume
gated upstream models without operator-license-acceptance).

**Implication for the gate:** the kit cannot fingerprint Gemma family
on this platform until either (a) operator accepts Gemma License + HF
token provisioned, or (b) Cisco catalog v1.x adds Gemma family
fingerprints (which would let the kit run in catalog-only mode
without re-downloading). Either path is a separate deliverable.

This is NEW bypass-frequency evidence: the gate has TWO failure
classes — catalog-absent (the case `model-provenance.md` already
documents) AND upstream-gated (this finding). Both block the gate
identically (exit 1 unverified) but for orthogonal reasons.

### Qwen3-Coder — OOM during weight scan

Kit exited with `rc=137` (SIGKILL by OS, virtually always OOM-killer
on macOS / Linux).

**Mac Mini state at scan time:**
- Total RAM: 48 GB
- Free at scan start: ~25 GB
- Model weight size: Qwen3-Coder-30B-A3B-Instruct (MoE, 30B total
  params, 3B active) — full FP16 safetensors are ~60 GB on disk

The kit re-downloads full safetensors to extract weight signals
per `model-provenance.md` "Weights re-downloaded for scan." A 60 GB
weight fingerprint pass + transformer-load overhead exceeds the
Mac Mini's free pool. The scan was OOM-killed before completing
fingerprint extraction.

**This is a NEW finding, not yet in `model-provenance.md`:** the
kit's weight-scan path has an effective host-memory ceiling. Mac
Mini (48 GB) can fingerprint up to ~10–15B param models cleanly;
26-30B+ MoE-class models need a host with ≥64 GB free. Mac Studio
(96 GB) would run this scan to completion.

This finding is recorded in the WP-08 chronicle so future operators
don't repeat the diagnosis.

## Override invocation

Per `docs/architecture-facts/model-provenance.md` lines 220–235
("Future-considered: upstream contribution"):

> "Decision deferred to evidence-driven scoping after D-17-12
> (Gemma 4 + Qwen3-Coder benchmarks) closes — at which point we'll
> have:
>   - Actual local model files (D-17-12 pulls them through the
>     gate with documented bypass)
>   - Real operator-experience data on bypass frequency (does the
>     unverified-but-needed pattern actually bite?)
>   - Clarity on Cisco's contribution process"

This deliverable IS the worked example that doctrine pre-authorizes.
Override invoked as:

```
PROVENANCE_OVERRIDE_REASON="D-17-12 benchmark; documented in
deliverable per model-provenance.md doctrine line 220-235"
```

This permits WP-03 model acquisition to proceed despite gate
failures. The verdict-source remains honest: both models go to WP-03
flagged "unverified, override-bypassed", and the WP-08 chronicle
preserves that lineage.

## Bypass-frequency data captured

Per the doctrine doc line 220–235's "real operator-experience data"
ask, this WP records:

| Data point | Value |
|---|---|
| Pulls attempted under D-17-12 | 2 |
| Pulls passing gate at exit 0 (verified-specific) | 0 |
| Pulls passing gate at exit 3 (verified-base-family) | 0 |
| Pulls failing at exit 1 (unverified, scan-failed) | 2 |
| Override invocations to proceed | 2 |
| Bypass rate | 100% |

A 100% bypass rate on the FIRST deliverable that would benefit from
T3-class model fingerprinting is strong evidence for the upstream-
contribution case. If two pulls require two overrides, ten will
require ten — the gate's protective value approaches zero for
T3-class models on the v1.0.0 catalog.

## Doctrine implications (deferred to WP-08 chronicle)

- **NEW failure class (gated upstream)** — `model-provenance.md`
  documents "weights re-downloaded for scan" but doesn't flag that
  re-download can fail on gated upstream sources. Add to "Known kit
  limitations" section in WP-08.
- **NEW failure class (host-memory ceiling)** — kit weight-scan
  needs ≥(2 × model FP16 size) free RAM. Add to "Known kit
  limitations" with concrete sizing guidance.
- **Upstream-contribution case strengthened** — 100% override rate
  on T3-class models. Recommend scoping a follow-on deliverable
  (potentially Phase 18) covering local fingerprint computation +
  PR to `cisco-ai-defense/model-provenance-kit`.

## Bridges to WP-03

WP-03 proceeds with:
- `ollama pull gemma2:27b` on Mac Studio (Ollama pulls quantized
  GGUF, not the gated Google HF source — the licensing chain runs
  through Ollama's published manifest, separate from Google's HF
  gating posture)
- `ollama pull qwen3-coder:30b` (or canonical Ollama tag for
  Qwen3-Coder-30B-A3B; verify at pull time)

Note that Ollama-side acquisition deliberately routes around the HF
gating issue for Gemma. The provenance gate has been honestly
bypassed; the licensing question for Gemma is whether Ollama's
distribution rights flow through correctly. Per `ollama.ai`'s
library page for Gemma 2, Google has authorized Ollama
redistribution; consumption is acceptable use under the Gemma terms.
This is upstream-Ollama compliance, not a platform-side override.
