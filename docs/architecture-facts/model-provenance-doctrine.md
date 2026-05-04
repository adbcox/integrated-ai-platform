# Model Provenance Doctrine
# Deliverable: D-17-92 (Goose maturity unblock T1-sibling — Cisco Provenance Kit deployment)
# Status: ESTABLISHED 2026-05-04

## Purpose

This doctrine defines the platform's model provenance posture: how lineage of deployed
LLM weights is verified, what verdicts mean, and where provenance gates are enforced in
the model lifecycle.

## What provenance verification answers

The Cisco Model Provenance Kit (Apache 2.0) answers a statistical question:

> "Do this model's weights match a known reference fingerprint in the Cisco database?"

This is a **lineage-attestation gate**, NOT a cryptographic signature check. It does not
prove the file was published by a specific party; it answers whether the weights are
statistically derived from a known base model. See §Limitations.

## Tool

**Cisco Model Provenance Kit** — `github.com/cisco-ai-defense/model-provenance-kit`

- Version: 1.0.0 (Apache 2.0)
- Language: Python 3.12+
- Install location: `~/repos/model-provenance-kit` (source; managed by `uv`)
- CLI: `provenancekit scan <hf-model-id>` / `provenancekit compare <a> <b>`
- Reference DB: ~150 base models, 45+ families, 20+ publishers (Meta, Google, Alibaba /
  Qwen, Mistral AI, DeepSeek, NVIDIA, IBM, etc.)
- DB location (deep-signals): `~/repos/model-provenance-kit/src/provenancekit/data/database/`
- F1 0.963 on 111-pair benchmark at threshold 0.70 (per arXiv:2512.12921)

**Platform wrapper:** `scripts/verify-model-provenance.sh`

```bash
# By Ollama tag (auto-resolved via config/model-hf-map.yaml):
scripts/verify-model-provenance.sh qwen2.5-coder:14b

# By HuggingFace model ID directly:
scripts/verify-model-provenance.sh --hf Qwen/Qwen2.5-Coder-14B-Instruct

# Refresh fingerprint database:
scripts/verify-model-provenance.sh --refresh-db

# Show kit status:
scripts/verify-model-provenance.sh --status
```

## Ollama-tag → HF-ID mapping

`config/model-hf-map.yaml` is the canonical map from Ollama pull tag to HuggingFace
model ID. When adding a new model via `pull-new-model.md`, the operator adds a row to
this file as part of Step 0. Format:

```yaml
qwen2.5-coder:14b: Qwen/Qwen2.5-Coder-14B-Instruct
```

## Verdict taxonomy

| Exit code | Verdict | Meaning |
|-----------|---------|---------|
| 0 | `verified-specific` | Top match IS the requested repo; score ≥ threshold (0.70) |
| 1 | `unverified` | No match above 0.50; or scan failed |
| 2 | `marginal` | Best score in [0.50, 0.70); weak lineage signal |
| 3 | `verified-base-family` | A related base/sibling matches above threshold; coarser attestation |

## GGUF vs HF-native fingerprinting — critical limitation

**Ollama-pulled models are GGUF-quantized.** The Cisco kit fingerprints weights against
HuggingFace native (BF16/FP16) snapshots. Weight quantization changes numerical values
significantly enough that kit scoring may return `unverified` (exit 1) for an entirely
legitimate Ollama model.

**This is expected and informational, not a failure signal.**

Implication for already-deployed models (WP-06 backfill):

- A `verified-specific` result on a GGUF model means the kit has indirect evidence
  (architecture metadata + tokenizer) that is architecture-matching, and the seed DB
  may contain the HF-native weights at the same family.
- An `unverified` result on a GGUF model means the kit could not find a match — most
  likely because the deep-signals DB contains HF-native weights and the GGUF numerical
  profile diverges beyond the scoring threshold.
- Either verdict is **informational only** for GGUF models. The Step 0 gate in
  `pull-new-model.md` uses this as a governance signal, not a hard block, when the
  model source (HuggingFace) and publisher (verified org) are known-good.

**For future enforcement:** if an operator pulls a model from an unrecognized publisher
or a suspicious source, a `verified-specific` result at the HF-native level IS a meaningful
positive signal. An `unverified` from a suspicious source warrants deeper review.

## Enforcement point: pull-new-model.md Step 0

`docs/runbooks/pull-new-model.md` §Step 0 mandates a provenance check before any
`ollama pull`. The gate semantics:

| Verdict | Gate action |
|---------|-------------|
| `verified-specific` (0) | Green — proceed with pull |
| `verified-base-family` (3) | Yellow — proceed; note coarser attestation in chronicle |
| `marginal` (2) | Yellow — operator decision required; note in chronicle |
| `unverified` (1) — known GGUF model | Informational — proceed; record `NO_MATCH-GGUF` |
| `unverified` (1) — unknown source | Orange — pause; review publisher; escalate if needed |
| `scan-failed` (1 from error) | Red — diagnose kit before pulling |

## Artifact chronicle

Provenance scans are logged to two locations:

1. **Per-model record:** `docs/_provenance/<sanitized-hf-id>.json`
   - 30-day cache; re-scan after expiry or when `PROVENANCE_FORCE=1`
   - Contains: verdict, exit_code, threshold, top_matches, model_info, timestamp

2. **Dated JSONL artifact:** `artifacts/model-provenance/provenance-YYYY-MM-DD.jsonl`
   - Append-only chronicle; one line per scan invocation
   - Hash-only (no credential values, F6 doctrine compliant)

## Relationship to D-17-53 (Goose deployed on wrong model)

D-17-53 revealed that Goose was running C1 tasks against `qwen3-coder:30b-a3b` when
the operator believed `qwen3-coder:30b` (full dense, not MoE) was deployed. The root
cause was `ollama pull` being executed without a pre-flight lineage check.

Had this provenance gate been in place:
- Step 0 would have required mapping `qwen3-coder:30b-a3b` → `Qwen/Qwen3-Coder-30B-A3B`
- The scan would have returned `verified-specific` or `verified-base-family`
- The architecture metadata (MoE vs dense) would appear in `model_info.architectures`
- The operator would have had explicit confirmation of which variant was being pulled

The gate does not prevent pulling; it forces explicit acknowledgement of WHAT is being
pulled and establishes a verifiable chronicle entry.

## Backfill scan results (2026-05-04)

The following are the provenance scan results for currently-deployed models captured
at D-17-92 delivery. All are GGUF-quantized (Ollama-pulled); results reflect the
GGUF limitation described above. See `artifacts/model-provenance/provenance-2026-05-04.jsonl`
for raw JSONL records.

| Ollama tag | HF model ID | Verdict | Score | Notes |
|------------|------------|---------|-------|-------|
| qwen2.5-coder:7b | Qwen/Qwen2.5-Coder-7B-Instruct | (see JSONL) | — | GGUF |
| qwen2.5-coder:14b | Qwen/Qwen2.5-Coder-14B-Instruct | (see JSONL) | — | GGUF |
| qwen2.5-coder:32b | Qwen/Qwen2.5-Coder-32B-Instruct | (see JSONL) | — | GGUF |
| qwen3-coder:30b | Qwen/Qwen3-Coder-30B-A3B | (see JSONL) | — | GGUF |
| gemma2:27b | google/gemma-2-27b-it | (see JSONL) | — | GGUF |
| deepseek-coder-v2:latest | deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct | (see JSONL) | — | GGUF |
| devstral:latest | mistralai/Devstral-Small-2505 | (see JSONL) | — | GGUF |

Note: backfill scans require the deep-signals fingerprint DB (~908 MB). Run
`scripts/verify-model-provenance.sh --refresh-db` once to download; then re-run
each tag to populate the JSONL. The `(see JSONL)` placeholder will be replaced
with actual results after DB download.

## Chronicle

- D-17-92 established: 2026-05-04. Cisco Provenance Kit v1.0.0 deployed at
  `~/repos/model-provenance-kit`. Wrapper `scripts/verify-model-provenance.sh` live.
  Ollama-tag map at `config/model-hf-map.yaml`. Step 0 gate added to `pull-new-model.md`.
  GGUF limitation documented. Backfill scan log at
  `artifacts/model-provenance/provenance-2026-05-04.jsonl` (partial — awaits deep-signals DB).

## Related docs

- `docs/runbooks/pull-new-model.md` — lifecycle runbook with Step 0 gate
- `config/model-hf-map.yaml` — Ollama-tag → HF-ID mapping
- `docs/architecture-facts/goose-capability-boundary.md` — Goose deployment posture
- `docs/architecture-facts/local-prompt-library-doctrine.md` — D-17-90 (T1 substrate)
- arXiv:2512.12921 — Cisco AI Security and Safety Framework Report (F1 0.963 source)
