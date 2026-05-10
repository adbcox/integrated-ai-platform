# Model provenance

How the platform handles AI model provenance. D#22 architecture
fact: this is the canonical reference; if this file disagrees with
any other doc, this file wins.

## Purpose

The platform pulls AI model weights from upstream sources (mostly
HuggingFace via Ollama, occasionally direct HF cache for transformers-
format use). Without a gate, every pull is unverified — the operator
trusts the upstream source's claim about what the model is, with no
independent attestation. The model-provenance gate (D-17-10) closes
that gap for what's coverable; names what's not.

## What the gate is, and what it isn't

The gate is a **lineage-attestation gate**, NOT a **signature-
verification gate**. The two answer different questions and address
different threat models. Conflating them leads to over-claiming.

### Lineage-attestation gate (what we have)

> **Question answered:** Does this model's weights statistically match
> a known reference fingerprint?

> **Threat model:** Catches base-model swaps, undisclosed major
> fine-tunes, lineage misrepresentation. If a publisher says "this is
> a fine-tune of Llama-3-70B" but the weights actually descend from
> Mistral-Small, the gate detects the mismatch.

> **Mechanism:** Cisco Model Provenance Kit (v1.0.0+) computes a
> multi-signal fingerprint (architecture metadata, tokenizer
> structure, weight-level features) and compares against a curated
> reference DB of known base models. Returns a similarity score
> 0.0–1.0 per match, plus top-K matches.

### Signature-verification gate (what we DON'T have)

> **Question answered:** Is this artifact cryptographically signed by
> its claimed publisher?

> **Threat model:** Catches supply-chain compromise where an attacker
> swaps a publisher's hosted artifact with a malicious version while
> preserving outward identity (same repo path, same metadata).

> **Mechanism:** Sigstore, transparency logs, in-toto attestations,
> HuggingFace's signed-commit feature, etc. Out of scope for D-17-10.

Both are useful. We have the lineage gate; we do not have a
signature-chain gate. Don't over-claim. If a future deliverable
needs signature-chain verification, that's a separate deliverable
(out of scope here).

## Threshold + exit codes

Default threshold: **0.70** (Cisco-calibrated; F1 0.963 / accuracy
96.4% / precision 98.1% / recall 94.6% on the 111-pair benchmark in
the kit's release validation).

Threshold reasoning: tightening to 0.80 creates alert-fatigue risk
on legitimate fine-tunes (fine-tunes typically score 0.85–0.95
against their base; tighter threshold trips false-negatives on
heavy adaptation). The 0.70 calibration sits at the F1 maximum.
**Revisit after first 6 months if operational data suggests drift.**

Wrapper exit codes (`scripts/verify-model-provenance.sh`):

| Exit | Verdict | Meaning |
|---|---|---|
| **0** | verified-specific | The requested repo appears in matches with score ≥ threshold (lineage attested at variant level). |
| **1** | unverified | No match ≥ threshold; or scan failed. Pull is BLOCKED in gate wrappers unless `PROVENANCE_OVERRIDE_REASON` is set. |
| **2** | marginal | Best match in [0.50, 0.70). Pull is BLOCKED unless override set. |
| **3** | verified-base-family | Top match ≥ threshold but to a base/sibling, not the requested-specific repo. Lineage attested at base-family level only. Gate wrappers ALLOW the pull (informational-success); operators reviewing provenance JSON should inspect top-K to confirm the lineage is what they expect. |

Exit 3 is intentionally non-blocking. The kit returns base-family
matches whenever the specific variant isn't in the catalog
(exceedingly common for code-fine-tunes; see "Cisco DB structural
truths" below). Treating exit 3 as failure would block legitimate
pulls that have honest base-family attestation.

## Cisco DB structural truths

These are first-class doctrine, not runbook footnotes. Catalog
snapshot 2026-05-02 (Cisco Model Provenance Kit v1.0.0,
deep-signals.zip SHA-256 `b94040b6…`, 152 fingerprints across 39
families).

### 1. Family-grouping namespace

Cisco groups fingerprints by parameter regime / architecture
lineage, NOT publisher namespace. Devstral (Mistral-published) lives
under `mistralai--ministral` despite Mistral publishing it. When
querying coverage by hand, search by model architecture +
parameter count, not by publisher path. Failed search by publisher
namespace ≠ "model not present"; check the architecture-lineage
namespace before concluding a gap.

The kit's `scan` command resolves this automatically: given the
operator-facing repo path `mistralai/Devstral-Small-2-24B-Instruct-2512`
it correctly navigates to `mistralai--ministral` family and returns
the matching fingerprint at score 1.0 (verified during D-17-10 T4
backfill, 2026-05-02). Operators using the wrapper don't need to
know the architecture-lineage namespace; only humans manually
inspecting the catalog do.

### 2. Code-fine-tune coverage gap

Cisco's seed catalog (v1.0.0) skews toward base instruction models.
Code-specialized fine-tunes are systematically under-represented.
As of catalog snapshot 2026-05-02:

- base model present + coder variant absent for: gemma-3,
  qwen2.5-14B/32B (Coder variants absent), deepseek-coder-v2 (full
  V2 absent; only Lite variant present), nomic-embed (entire
  family absent)
- The one code-variant exception: `Qwen2.5-Coder-7B-Instruct` is
  in the catalog (under `qwen--qwen` family).

**Implication:** Platform workloads centered on autonomous coding
(D-17-13 Goose, D-17-14 exo cluster) and on code-specialized
T2 models operate against models in Cisco's thinnest-coverage
category. The gate is genuinely useful for what IS covered + base-
family matches; coverage for code variants is coarse-grained
(base-family attestation, not specific-variant attestation).

### 3. Variant-scoring caveat

Fine-tunes typically score 0.85–0.95 against their base. "Verified"
at the 0.70 threshold can mean either:

- (a) verified as the specific model (the requested repo appears
  in matches at score ≥ threshold) → wrapper returns exit 0
- (b) verified as descended from this base family (the requested
  repo is NOT in the matches, but a base/sibling is) → wrapper
  returns exit 3

The wrapper reports both the verdict AND the top-3 matches in the
provenance JSON record so the distinction is legible. Operators
reviewing provenance status MUST inspect the top-K matches array
when reading exit-3 records to confirm the attested base is what
they expect.

**Doctrine: when communicating provenance status, never say
"verified" without naming whether attestation is at variant level
or base-family level.** "Verified-specific (exit 0)" and
"verified-base-family (exit 3)" are the two correct phrasings.

## Backfill verdicts: scan-confirmed vs inferred

The Cisco Provenance Kit's deep-signals computation is the source
of fingerprints in the catalog. Querying the catalog (the T0.5
method used in D-17-10) produces verdicts equivalent to running
the scan locally — without the bandwidth cost. The platform's
backfill on 2026-05-02 used catalog inference + Ollama→HF mapping
for 5 of 6 models, scan-confirmed for the 1 already-cached model
plus 1 namespace-resolution test (Devstral).

This is load-bearing because:

1. **The catalog IS the scan output.** Local recomputation produces
   the same answer (modulo flaky weight-precision edges; see below).
2. **Ollama tag → HF repo mapping is deterministic** per Ollama
   manifest; not a guess.
3. **Every inferred verdict carries an evidence chain.** Operators
   can upgrade inference→scan via the wrapper at any time.
4. **The gate's protective value is on FORWARD pulls.** Backfill
   establishes baseline state honestly; forward operation is where
   threat protection lives.

When inference is NOT sufficient: cases where the local model file
may have been tampered post-pull. The kit cannot detect this — GGUF
isn't a transformer checkpoint, and the kit re-downloads the
upstream HF source to compute fingerprints. For tamper detection at
rest, separate mechanisms (filesystem integrity monitoring, Vault-
stored hashes captured at install time) would be required. Out of
scope for D-17-10.

A fourth verdict-source class, **operator-accepted (Path B)**, is
a doctrine-level disposition layered on top of any of the three
Path A sources above (most commonly scan-confirmed in its failure
mode). Path B applies when the kit's automated fingerprinting
workload is blocked by hardware constraint and the operator
accepts the next-best evidence class as the active doctrine grade.
Full trigger conditions, disposition outcome, upgrade path, and
audit requirements: see
`docs/architecture-facts/model-provenance-doctrine.md`
§"Operator-accepted (Path B) — doctrine-level disposition". First
precedent: `docs/_provenance/backfill-2026-05-10.md`
(`Qwen/Qwen3-Coder-30B-A3B-Instruct`, 2026-05-10); upgrade path
tracked as KI-010.

See `docs/_provenance/backfill-2026-05-02.md` for the per-model
results and verdict-source labels; see also
`docs/architecture-facts/model-provenance-doctrine.md` for the
canonical disposition authority.

## Known kit limitations (as of v1.0.0)

Surfaced during D-17-10 implementation; document in case future
operators hit the same edges.

- **FP8 weight format intermittent failure.** First scan against
  `mistralai/Devstral-Small-2-24B-Instruct-2512` (FP8 quantization,
  `Float8_e4m3fn` dtype) failed with `"gt_cpu" not implemented for
  'Float8_e4m3fn'`. Second scan succeeded via metadata-only fast
  path (the kit cached the metadata signal from the partial first
  download). Behavior: transient on first encounter for FP8 models;
  stable on retry. Workaround: re-run the wrapper if the first call
  fails on a known-FP8 model. Upstream issue worth filing if this
  pattern persists across multiple FP8 models — out of scope for
  D-17-10 itself.

- **Weight-only kit; no GGUF support.** The kit consumes
  transformers-format safetensors (or local snapshot directories
  in the same format). Ollama's GGUF blobs cannot be scanned
  directly; the gate verifies the upstream HF source repo, not the
  local quantized blob. This is correct behavior for lineage
  attestation (quantization preserves architecture; lineage of the
  base is what we want to attest), but operators should not expect
  the kit to verify a local GGUF file.

- **Weights re-downloaded for scan.** The kit pulls the full
  safetensors version from HF to extract weight signals. For
  models the platform has via Ollama (GGUF), this is a fresh
  download (~14–65 GB depending on model size). Cache window in
  the wrapper (default 30 days) reduces re-download frequency.

## Future-considered: upstream contribution

Cisco's catalog has gaps for several models the platform cares
about (Gemma 4 family, Qwen3-Coder-Next, qwen2.5-coder-14B/32B
specific variants). Upstream contribution path: compute fingerprints
locally and submit a PR to `cisco-ai-defense/model-provenance-kit`
(or its companion HF dataset).

This is **named here as a future opportunity, not a committed
deliverable.** Decision deferred to evidence-driven scoping after
D-17-12 (Gemma 4 + Qwen3-Coder benchmarks) closes — at which point
we'll have:

- Actual local model files (D-17-12 pulls them through the gate
  with documented bypass)
- Real operator-experience data on bypass frequency (does the
  unverified-but-needed pattern actually bite?)
- Clarity on Cisco's contribution process (license terms,
  fingerprint compute cost)

If evidence supports the contribution work, scope a follow-on
deliverable (D-17-23 candidate, or Phase 18). If not, leave the
opportunity named here without forcing it.

## See also

- `docs/runbooks/pull-new-model.md` — operator workflow including
  the gate
- `docs/_provenance/backfill-2026-05-02.md` — D-17-10 baseline
- `docs/architecture-patterns/candidate-tools.md` — Cisco
  Provenance Kit entry (adopted)
- `scripts/verify-model-provenance.sh` — wrapper
- `scripts/ollama-pull-verified.sh` — gate-enforced ollama pull
- `scripts/hf-download-verified.sh` — gate-enforced HF download
