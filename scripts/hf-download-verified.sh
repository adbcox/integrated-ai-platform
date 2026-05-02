#!/usr/bin/env bash
# hf-download-verified.sh — D-17-10 gate-enforced HuggingFace download.
#
# Verifies a HuggingFace repo via Cisco Provenance Kit BEFORE running
# `hf download`. Convention-style wrapper (per platform style; does NOT
# shim the binary). Used when pulling a model directly into the HF cache
# (e.g. for transformers / diffusers / direct local inference).
#
# CLI note: `huggingface-cli` is deprecated in huggingface_hub>=1.0; the
# canonical CLI is now `hf` with same `download` subcommand syntax.
# Wrapper updated 2026-05-02 (D-17-14 Finding N) for upstream compat.
#
# Exit semantics inherit from verify-model-provenance.sh:
#   0 (verified-specific)    -> download proceeds
#   3 (verified-base-family) -> download proceeds (still attested, coarser)
#   2 (marginal)             -> download blocked unless OVERRIDE set
#   1 (unverified)           -> download blocked unless OVERRIDE set
#
# Override mechanism: identical to ollama-pull-verified.sh. Set
# PROVENANCE_OVERRIDE_REASON; bypass logged to docs/_provenance/overrides.log.
#
# Usage:
#   hf-download-verified.sh <hf-repo> [extra args passed to hf download]
# Example:
#   hf-download-verified.sh Qwen/Qwen2.5-Coder-7B-Instruct
#   hf-download-verified.sh google/gemma-3-27b-it --revision main
set -euo pipefail

HF_REPO="${1:-}"
if [[ -z "$HF_REPO" ]]; then
  echo "usage: $0 <hf-repo> [extra hf download args]" >&2
  exit 64
fi
shift  # remaining args pass to hf download

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFY="$REPO_ROOT/scripts/verify-model-provenance.sh"
OVERRIDES_LOG="$REPO_ROOT/docs/_provenance/overrides.log"

set +e
"$VERIFY" "$HF_REPO"
VERIFY_RC=$?
set -e

run_download() {
  echo "  hf download $HF_REPO $*"
  hf download "$HF_REPO" "$@"
}

case "$VERIFY_RC" in
  0|3)
    echo
    echo "hf-download-verified: provenance gate PASSED (exit $VERIFY_RC) — proceeding"
    run_download "$@"
    ;;
  1|2)
    if [[ -z "${PROVENANCE_OVERRIDE_REASON:-}" ]]; then
      echo >&2
      echo "hf-download-verified: BLOCKED — provenance gate failed (exit $VERIFY_RC)" >&2
      echo "  HF repo: $HF_REPO" >&2
      echo "  To override: re-run with PROVENANCE_OVERRIDE_REASON=\"<reason>\" set." >&2
      echo "  Override is logged to docs/_provenance/overrides.log." >&2
      echo "  See docs/runbooks/pull-new-model.md §Override for the canonical reason template." >&2
      exit "$VERIFY_RC"
    fi
    mkdir -p "$(dirname "$OVERRIDES_LOG")"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    {
      echo "${TIMESTAMP}	repo=${HF_REPO}	tool=hf	verify_exit=${VERIFY_RC}	reason=${PROVENANCE_OVERRIDE_REASON}"
    } >> "$OVERRIDES_LOG"
    echo
    echo "hf-download-verified: OVERRIDE — provenance gate exit $VERIFY_RC, proceeding with logged reason"
    echo "  reason: ${PROVENANCE_OVERRIDE_REASON}"
    echo "  log:    $OVERRIDES_LOG"
    run_download "$@"
    ;;
  *)
    echo "hf-download-verified: UNEXPECTED verify exit $VERIFY_RC — aborting" >&2
    exit 70
    ;;
esac
