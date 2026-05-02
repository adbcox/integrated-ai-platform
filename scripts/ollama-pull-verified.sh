#!/usr/bin/env bash
# ollama-pull-verified.sh — D-17-10 gate-enforced ollama pull.
#
# Verifies a HuggingFace source repo via Cisco Provenance Kit BEFORE
# running `ollama pull`. Convention-style wrapper (per platform style;
# does NOT shim the ollama binary). The expectation is that operators
# and automation use this wrapper for new pulls; documented in
# docs/runbooks/pull-new-model.md.
#
# Exit semantics inherit from verify-model-provenance.sh:
#   0 (verified-specific)    -> pull proceeds
#   3 (verified-base-family) -> pull proceeds (still attested, coarser)
#   2 (marginal)             -> pull blocked unless OVERRIDE set
#   1 (unverified)           -> pull blocked unless OVERRIDE set
#
# Override mechanism: set PROVENANCE_OVERRIDE_REASON to a non-empty string;
# the bypass is logged to docs/_provenance/overrides.log with timestamp,
# repo, ollama tag, exit code, and reason. Operator-traceable.
#
# Usage:
#   ollama-pull-verified.sh <hf-source-repo> <ollama-tag>
# Example:
#   ollama-pull-verified.sh google/gemma-3-27b-it gemma3:27b
#
# Override example:
#   PROVENANCE_OVERRIDE_REASON="D-17-12 benchmark; Gemma 4 not in catalog 2026-05-02" \
#     ollama-pull-verified.sh google/gemma-4-26b-it gemma4:26b
set -euo pipefail

HF_REPO="${1:-}"
OLLAMA_TAG="${2:-}"
if [[ -z "$HF_REPO" || -z "$OLLAMA_TAG" ]]; then
  echo "usage: $0 <hf-source-repo> <ollama-tag>" >&2
  echo "  e.g. $0 Qwen/Qwen2.5-Coder-32B-Instruct qwen2.5-coder:32b" >&2
  exit 64
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY="$REPO_ROOT/scripts/verify-model-provenance.sh"
OVERRIDES_LOG="$REPO_ROOT/docs/_provenance/overrides.log"

set +e
"$VERIFY" "$HF_REPO"
VERIFY_RC=$?
set -e

case "$VERIFY_RC" in
  0|3)
    # verified-specific or verified-base-family -> proceed
    echo
    echo "ollama-pull-verified: provenance gate PASSED (exit $VERIFY_RC) — proceeding with pull"
    echo "  ollama pull $OLLAMA_TAG"
    ollama pull "$OLLAMA_TAG"
    ;;
  1|2)
    # unverified or marginal -> require override
    if [[ -z "${PROVENANCE_OVERRIDE_REASON:-}" ]]; then
      echo >&2
      echo "ollama-pull-verified: BLOCKED — provenance gate failed (exit $VERIFY_RC)" >&2
      echo "  HF repo:    $HF_REPO" >&2
      echo "  Ollama tag: $OLLAMA_TAG" >&2
      echo "  To override: re-run with PROVENANCE_OVERRIDE_REASON=\"<reason>\" set." >&2
      echo "  Override is logged to docs/_provenance/overrides.log." >&2
      echo "  See docs/runbooks/pull-new-model.md §Override for the canonical reason template." >&2
      exit "$VERIFY_RC"
    fi
    mkdir -p "$(dirname "$OVERRIDES_LOG")"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    {
      echo "${TIMESTAMP}	repo=${HF_REPO}	ollama_tag=${OLLAMA_TAG}	verify_exit=${VERIFY_RC}	reason=${PROVENANCE_OVERRIDE_REASON}"
    } >> "$OVERRIDES_LOG"
    echo
    echo "ollama-pull-verified: OVERRIDE — provenance gate exit $VERIFY_RC, proceeding with logged reason"
    echo "  reason: ${PROVENANCE_OVERRIDE_REASON}"
    echo "  log:    $OVERRIDES_LOG"
    echo "  ollama pull $OLLAMA_TAG"
    ollama pull "$OLLAMA_TAG"
    ;;
  *)
    echo "ollama-pull-verified: UNEXPECTED verify exit $VERIFY_RC — aborting" >&2
    exit 70
    ;;
esac
