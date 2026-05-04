# Pull a new model (provenance-gated)

How to pull a new AI model onto the platform. Every pull goes
through the RAM-fit check (Step -1) and the model-provenance gate
(Step 0) before `ollama pull`. The provenance gate attests model
lineage; it does NOT verify cryptographic signatures. See
`docs/architecture-facts/model-provenance-doctrine.md` for the
distinction and GGUF-vs-HF-native limitation.

## Step -1 — RAM-fit check (MANDATORY before provenance gate)

**Finding 21 (D-17-104 close, 2026-05-04):** Open-weights ≠ locally-runnable.
Article-claimed benchmark parity is meaningless if the model does not fit
the hardware. RAM-fit is a gate, not a post-hoc discovery.

Check before investing any evaluation time:

```sh
# 1. Total parameter count (from HF model card — check "Model Size" or config.json)
#    For MoE models, note BOTH total and active params.
#
# 2. Estimate minimum RAM for INT4 quantization:
#    total_params_B × 0.5 GB  (rough INT4 floor; add ~10% for KV cache)
#
# 3. Check active platform pool:
#    Mac Studio M3 Ultra: 96 GB unified memory
#    Mac Mini M4 Pro:     48 GB unified memory
#
# 4. Check Ollama registry — is a GGUF available?
curl -s https://ollama.com/library/<model-name>/tags | python3 -c \
  "import sys,re; c=sys.stdin.read(); print([x for x in re.findall(r'[a-z0-9._:-]+', c) if 'cloud' not in x and 'GB' in x or True][:10])"
#    ':cloud' tag = API-routed, requires vendor API key (doctrine-blocked)
#    SIZE '-' in ollama list = cloud-routed, no local weights
```

**RAM-fit decision table:**

| Model size | INT4 floor | Fits 96 GB pool? | Action |
|---|---|---|---|
| ≤14B total | ≤7 GB | Yes | Proceed to Step 0 |
| 30–70B total | 15–35 GB | Yes | Proceed to Step 0 |
| 70–180B total | 35–90 GB | Marginal | Check quantization level; verify GGUF exists |
| >180B total | >90 GB | No (Mac Studio) | Hardware-blocked; defer or escalate |
| MoE (e.g. 1T total / 32B active) | >200 GB typical | No | Hardware-blocked even at INT4 |

**Reactivation criteria for hardware-blocked models:**
hardware upgrade to ≥256 GB unified memory, OR vendor releases a
smaller-active-params distilled variant that fits the pool.

## Step 0 — provenance gate (MANDATORY before any pull)

Before running `ollama pull`, run the provenance gate:

```sh
# By Ollama tag (auto-resolves via config/model-hf-map.yaml):
scripts/verify-model-provenance.sh qwen2.5-coder:14b

# By HuggingFace model ID directly:
scripts/verify-model-provenance.sh --hf Qwen/Qwen2.5-Coder-14B-Instruct
```

If the model is not yet in `config/model-hf-map.yaml`, add it first:

```yaml
# config/model-hf-map.yaml
qwen2.5-coder:14b: Qwen/Qwen2.5-Coder-14B-Instruct
```

**Gate verdicts and actions:**

| Exit | Verdict | Action |
|------|---------|--------|
| 0 | `verified-specific` | Proceed with pull |
| 3 | `verified-base-family` | Proceed; note coarser attestation in chronicle |
| 2 | `marginal` | Operator decision required; note in chronicle |
| 1 | `unverified` — known GGUF source | Informational; see GGUF note below |
| 1 | `unverified` — unknown source | Pause; review publisher before pulling |
| 1 (error) | `scan-failed` | Diagnose kit before pulling |

**GGUF note:** Ollama-pulled models are GGUF-quantized. The Cisco kit fingerprints
HuggingFace native weights (BF16/FP16). `unverified` on a known GGUF model from a
trusted publisher is informational — proceed, record `NO_MATCH-GGUF` in chronicle.
See `docs/architecture-facts/model-provenance-doctrine.md §GGUF`.

## TL;DR (wrapper scripts)

```sh
# Ollama pull (most common):
scripts/ollama-pull-verified.sh <hf-source-repo> <ollama-tag>

# Direct HF download (transformers / direct local inference):
scripts/hf-download-verified.sh <hf-repo> [extra huggingface-cli args]
```

If the gate passes (exit 0 or 3), the pull proceeds. If the gate
fails (exit 1 or 2), the pull is blocked unless an operator
override is set.

## Examples

### Ollama pull, expected pass (model in Cisco catalog)

```sh
scripts/ollama-pull-verified.sh Qwen/Qwen2.5-Coder-7B-Instruct qwen2.5-coder:7b
```

Expected: gate exit 0 (verified-specific), `ollama pull` runs.

### Ollama pull, expected base-family attestation

```sh
scripts/ollama-pull-verified.sh Qwen/Qwen2.5-Coder-32B-Instruct qwen2.5-coder:32b
```

Expected: gate exit 3 (verified-base-family — matches base
`Qwen2.5-32B-Instruct`, not Coder-32B specifically). `ollama pull`
runs. Inspect `docs/_provenance/Qwen__Qwen2.5-Coder-32B-Instruct.json`
to see which base/sibling was attested.

### HF download

```sh
scripts/hf-download-verified.sh google/gemma-3-27b-it
```

Expected: gate exit 0 or 3 (gemma-3 family is in the catalog).
`huggingface-cli download` runs.

## When the gate blocks

If the gate exits 1 (unverified) or 2 (marginal), the wrapper
prints a BLOCKED message and exits with the same code without
running the pull.

Common reasons:
- Model is too new for Cisco's catalog (e.g. Gemma 4 family,
  Qwen3-Coder-Next; absent as of catalog snapshot 2026-05-02)
- Model architecture is rare or absent from the seed catalog
- Scan failed (rare; usually network or kit transient error —
  retry first)

### Override mechanism

When operator judgment authorizes the pull anyway, set
`PROVENANCE_OVERRIDE_REASON` to a non-empty string. The bypass is
logged to `docs/_provenance/overrides.log` with timestamp, repo,
ollama tag (or tool name), exit code, and reason. Operator-
traceable.

```sh
PROVENANCE_OVERRIDE_REASON="D-17-12 benchmark: Gemma 4 26B not in Cisco catalog as of catalog snapshot 2026-05-02. Pull authorized for benchmark evaluation per Phase 17 plan. Re-evaluate gate coverage after D-17-12 closes." \
  scripts/ollama-pull-verified.sh google/gemma-4-26b-it gemma4:26b
```

### Canonical override-reason template

```
<deliverable-id> <action>: <model> not in Cisco catalog as of
catalog snapshot <YYYY-MM-DD>. Pull authorized for <purpose>
per <plan reference>. Re-evaluate gate coverage after <gating
condition>.
```

Examples:
- `D-17-12 benchmark: Gemma 4 26B not in Cisco catalog as of catalog snapshot 2026-05-02. Pull authorized for benchmark evaluation per Phase 17 plan. Re-evaluate gate coverage after D-17-12 closes.`
- `D-17-14 exo cluster: Qwen3-Coder-Next 80B not in Cisco catalog as of catalog snapshot 2026-05-02. Pull authorized for distributed-inference deployment per Phase 17 plan. Re-evaluate after Cisco catalog refresh or D-17-23 (upstream contribution) decision.`

Don't override for ad-hoc reasons. Each override is a deferred
trust decision; the log is the audit trail.

## Verifying a model on demand (no pull)

If you want to check a model's provenance without pulling it:

```sh
scripts/verify-model-provenance.sh <hf-repo>
```

Writes the provenance JSON to `docs/_provenance/<sanitized>.json`.
Cache hit if a record exists and is <30 days old (configurable via
`PROVENANCE_CACHE_DAYS`). Force re-scan with `PROVENANCE_FORCE=1`.

## Install (one-time per node)

The Cisco Model Provenance Kit lives at `~/repos/model-provenance-kit`.
Installation is one-time per node:

```sh
git clone https://github.com/cisco-ai-defense/model-provenance-kit.git ~/repos/model-provenance-kit
cd ~/repos/model-provenance-kit
uv sync
# Optional (recommended): download deep-signals fingerprint DB (~908 MB)
scripts/verify-model-provenance.sh --refresh-db
```

After install, `scripts/verify-model-provenance.sh` discovers the kit
at `~/repos/model-provenance-kit`. Override with `PROVENANCE_KIT_DIR`
env var if installed elsewhere.

**Mac Mini status (2026-05-04):** Kit installed, `uv sync` complete,
deep-signals DB not yet downloaded (run `--refresh-db` to fetch ~908 MB).

## Reading a provenance record

A provenance JSON file has these key fields:

| Field | Meaning |
|---|---|
| `verdict` | one of `verified-specific`, `verified-base-family`, `marginal`, `unverified`, `scan-failed` |
| `exit_code` | 0 / 3 / 2 / 1 / 1 respectively |
| `threshold` | the threshold used at scan time (default 0.70) |
| `kit_version` | Cisco kit version that produced the record |
| `top_matches[]` | up to 5 best matches; each has `model_id`, `family_id`, `pipeline_score`, `match_type`, `provenance_decision` |
| `model_info` | extracted metadata about the scanned model (architecture, hidden_size, etc.) |

When reading exit-3 records: inspect `top_matches[0].model_id` to
see which base/sibling was attested. If it's not the expected base,
treat as suspicious and surface to the operator — the kit's exit-3
is not a free pass; it's "this matches *something* in the
catalog", and the operator's job is to confirm the *something* is
the right *something*.

## Known kit limitations

See `docs/architecture-facts/model-provenance-doctrine.md §GGUF` for:

- No GGUF support (kit fingerprints HF-native weights; GGUF quantized
  models will return `unverified` — this is informational, not a failure)
- FP8 weight format intermittent failure (workaround: retry)
- Statistical evidence only — not cryptographic proof

## See also

- `docs/architecture-facts/model-provenance-doctrine.md` — canonical doctrine (D-17-92)
- `config/model-hf-map.yaml` — Ollama-tag → HuggingFace-ID mapping
- `artifacts/model-provenance/` — dated JSONL provenance chronicle
- `docs/_provenance/` — per-model provenance records (30-day cache)
- `docs/_provenance/overrides.log` — audit trail of bypass decisions
