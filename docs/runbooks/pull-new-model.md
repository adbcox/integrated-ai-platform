# Pull a new model (provenance-gated)

How to pull a new AI model onto the platform. Every pull goes
through the model-provenance gate (D-17-10) by convention. The gate
attests model lineage; it does NOT verify cryptographic signatures.
See `docs/architecture-facts/model-provenance.md` for the
distinction.

## TL;DR

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

## Install (one-time)

The Cisco Model Provenance Kit lives at `~/repos/external-tools/
model-provenance-kit`, pinned to tag `1.0.0` (commit `5f27dc56`).
Installation is one-time per node:

```sh
mkdir -p ~/repos/external-tools
cd ~/repos/external-tools
git clone --depth 1 --branch 1.0.0 https://github.com/cisco-ai-defense/model-provenance-kit.git
cd model-provenance-kit
uv sync
uv run provenancekit download-deepsignals-fingerprint  # ~866 MB download
```

After install, the wrapper at `scripts/verify-model-provenance.sh`
discovers the kit at the default path. Override with
`PROVENANCE_KIT_DIR` env var if installed elsewhere.

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

See `docs/architecture-facts/model-provenance.md` §"Known kit
limitations" for:

- FP8 weight format intermittent failure (workaround: retry)
- No GGUF support (wrapper verifies upstream HF source, not local
  GGUF blob — correct behavior for lineage attestation)
- Weights re-downloaded for first scan (~14–65 GB per model;
  30-day cache reduces frequency)

## See also

- `docs/architecture-facts/model-provenance.md` — canonical
  doctrine
- `docs/_provenance/backfill-2026-05-02.md` — D-17-10 baseline
  state
- `docs/_provenance/overrides.log` — audit trail of bypass
  decisions
- `docs/architecture-patterns/candidate-tools.md` — Cisco
  Provenance Kit entry (adopted)
