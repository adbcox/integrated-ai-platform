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
- D-17-122 addendum: 2026-05-05. See §D-17-122 below.

## D-17-122 addendum (2026-05-05) — Structured backfill + pull wrapper

D-17-122 extends D-17-92 with a structured mapping table, per-model JSON provenance
records, and a pull wrapper that integrates provenance into the Ollama ingestion path.

### What D-17-122 covers vs does not cover

**Covered (this deliverable):** upstream HF model lineage via Cisco Provenance Kit.
The kit scans the HuggingFace-hosted source model and classifies its family derivation.
F1 0.963 at threshold 0.70 on the kit's benchmark set.

**NOT covered — GGUF blob integrity:** Ollama stores weights as GGUF blobs. The Cisco
kit only supports safetensors/PyTorch format and cannot inspect GGUF files.

**GGUF integrity mitigation:** all models sourced from `registry.ollama.ai` only; Ollama
client verifies SHA-256 blob checksums at download time. This is the current GGUF
integrity control; GGUF metadata fingerprinting is a future deliverable candidate.

### New tooling (D-17-122)

| Artifact | Purpose |
|----------|---------|
| `config/model_provenance/ollama_to_hf_mapping.yaml` | Structured Ollama → HF ID mapping with derivation types, fallback chains, scan targets |
| `bin/ollama_pull_with_provenance.sh` | Pull wrapper: `ollama pull` + provenance scan + JSON record |
| `bin/run_provenance_backfill.py` | Batch backfill runner for all mapped models |
| `artifacts/model_provenance/<model>_<date>.json` | Per-model provenance records (structured schema) |
| `venv-provenance/` | Python 3.12 venv with `cisco-ai-provenance-kit==1.0.0` |

### Standing operational rule (supplements pull-new-model.md Step 0)

```bash
bin/ollama_pull_with_provenance.sh <ollama_model> [<hf_id>]
```

Every new Ollama model pull uses this wrapper. Exception: `local_modelfile_derivative`
models (created via `ollama create`) inherit provenance from their base model.

### Verdict taxonomy (D-17-122 JSON records)

| Verdict | pipeline_score | Action |
|---------|---------------|--------|
| `VERIFIED` | ≥ 0.85 | None required |
| `LIKELY` | 0.70–0.84 | Review; accept or re-scan with deep-signals |
| `WEAK_MATCH` | 0.50–0.69 | Investigate; do not use in production without review |
| `NO_MATCH` | < 0.50 | Block; surface to operator |
| `SCAN_OOM` | — | Kit OOM-killed; re-scan on Mac Studio (96GB) |
| `UNKNOWN` | — | HF repo missing / kit error / HF ID unconfirmed; operator resolves |
| `N_A` | — | Cloud-only or Modelfile derivative; provenance inherited or N/A |
| `N_A_GATED` | — | Gated HF model; provision `secret/huggingface/admin` |

### Backfill results (2026-05-05)

| Model | Host | Verdict | Score | Notes |
|-------|------|---------|-------|-------|
| qwen3-coder:30b | Mac Studio | SCAN_OOM | — | 30.5B OOM on Mac Mini; re-scan on Mac Studio |
| qwen3-coder:30b-coding | Mac Studio | N_A | — | Modelfile derivative |
| qwen3-coder-next:latest | Mac Studio | UNKNOWN | — | 79.7B; HF source unconfirmed; all fallback IDs 404 or timeout |
| qwen3-coder-next:coding | Mac Studio | N_A | — | Modelfile derivative |
| deepseek-coder-v2:16b-lite-instruct | Mac Studio | SCAN_OOM | — | 16B OOM on Mac Mini |
| kimi-k2.6:cloud | Mac Studio | N_A | — | Cloud API proxy |
| gemma2:27b | Mac Studio | N_A_GATED | — | Gated; provision secret/huggingface/admin |
| qwen2.5-coder:7b | Mac Mini | **VERIFIED** | 1.000 | Confirmed Match; in Cisco reference DB |
| qwen2.5-coder:14b | Mac Mini | **VERIFIED** | 1.000 | Confirmed Match |
| qwen2.5-coder:32b | Mac Mini | **VERIFIED** | 1.000 | Confirmed Match |
| nomic-embed-text:latest | Mac Mini | **VERIFIED** | 0.992 | Confirmed Match |
| devstral:latest | Mac Mini | UNKNOWN | — | Kit error: Mistral tokenizer v3 `special_tokens` key missing |
| deepseek-coder-v2:latest (alias) | Mac Mini | SCAN_OOM | — | Same as instruct variant |

**Open follow-up actions:**
- Install deep-signals DB (`provenancekit download-deepsignals-fingerprint`) and
  re-scan SCAN_OOM models on Mac Studio
- Confirm qwen3-coder-next HF repo with Qwen; update mapping
- File upstream issue against cisco-ai-provenance-kit for Mistral tokenizer v3 support
- Provision `secret/huggingface/admin` with `token` field for gemma2 scan

## Related docs

- `docs/runbooks/pull-new-model.md` — lifecycle runbook with Step 0 gate
- `config/model-hf-map.yaml` — Ollama-tag → HF-ID mapping (D-17-92; superseded by D-17-122 YAML for new models)
- `config/model_provenance/ollama_to_hf_mapping.yaml` — structured mapping (D-17-122)
- `docs/architecture-facts/goose-capability-boundary.md` — Goose deployment posture
- `docs/architecture-facts/local-prompt-library-doctrine.md` — D-17-90 (T1 substrate)
- arXiv:2512.12921 — Cisco AI Security and Safety Framework Report (F1 0.963 source)
