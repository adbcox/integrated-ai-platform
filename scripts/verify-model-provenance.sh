#!/usr/bin/env bash
# verify-model-provenance.sh — D-17-10 lineage-attestation gate.
#
# Wraps Cisco Model Provenance Kit (cisco-ai-defense/model-provenance-kit
# v1.0.0) `scan` mode. Returns a verdict + writes a provenance record to
# docs/_provenance/<sanitized-repo>.json.
#
# This is a LINEAGE-ATTESTATION gate, NOT a signature-verification gate.
# It answers "do this model's weights statistically match a known
# reference fingerprint?" — not "is this artifact cryptographically
# signed by its claimed publisher?". See
# docs/architecture-facts/model-provenance.md.
#
# Exit codes:
#   0 = verified-specific      (top match is the requested repo, score >= threshold)
#   1 = unverified             (no match >= threshold; or scan failed)
#   2 = marginal               (best score in [0.50, threshold))
#   3 = verified-base-family   (match >= threshold but to a base/sibling, not the
#                               specific requested repo — still a real attestation,
#                               but coarser than variant-level)
#
# Usage: verify-model-provenance.sh <hf-repo>
# Example: verify-model-provenance.sh Qwen/Qwen2.5-Coder-7B-Instruct
#
# Configuration (env):
#   PROVENANCE_THRESHOLD       default 0.70 (Cisco-calibrated; F1 0.963 at 0.70)
#   PROVENANCE_KIT_DIR         default ~/repos/external-tools/model-provenance-kit
#   PROVENANCE_CACHE_DAYS      default 30
#   PROVENANCE_RECORDS_DIR     default <repo>/docs/_provenance
#   PROVENANCE_FORCE           if set, ignore cache
#   PROVENANCE_KIT_THRESHOLD   kit-level cutoff for returned matches (default 0.50;
#                              wrapper still applies PROVENANCE_THRESHOLD policy on top)
set -euo pipefail

REPO_ARG="${1:-}"
if [[ -z "$REPO_ARG" ]]; then
  echo "usage: $0 <hf-repo>" >&2
  echo "  e.g. $0 Qwen/Qwen2.5-Coder-7B-Instruct" >&2
  exit 64
fi

THRESHOLD="${PROVENANCE_THRESHOLD:-0.70}"
KIT_DIR="${PROVENANCE_KIT_DIR:-$HOME/repos/external-tools/model-provenance-kit}"
CACHE_DAYS="${PROVENANCE_CACHE_DAYS:-30}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECORDS_DIR="${PROVENANCE_RECORDS_DIR:-$REPO_ROOT/docs/_provenance}"
mkdir -p "$RECORDS_DIR"

if [[ ! -d "$KIT_DIR" ]]; then
  echo "ERROR: Provenance Kit not installed at $KIT_DIR" >&2
  echo "  Install per docs/runbooks/pull-new-model.md §Install." >&2
  exit 70
fi

# Sanitize repo path for filename: "Qwen/Qwen2.5-Coder-7B-Instruct" -> "Qwen__Qwen2.5-Coder-7B-Instruct"
SANITIZED="${REPO_ARG//\//__}"
RECORD_PATH="$RECORDS_DIR/${SANITIZED}.json"

# Cache check — skip re-scan if record exists, is fresh, AND was scored at the
# same threshold as the current request (a 0.70-threshold record cannot
# satisfy a 0.80-threshold query).
if [[ -z "${PROVENANCE_FORCE:-}" && -f "$RECORD_PATH" ]]; then
  AGE_SECONDS=$(( $(date +%s) - $(stat -f %m "$RECORD_PATH") ))
  CACHE_SECONDS=$(( CACHE_DAYS * 86400 ))
  if (( AGE_SECONDS < CACHE_SECONDS )); then
    CACHED_THRESHOLD=$(/usr/bin/python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('threshold',''))" "$RECORD_PATH")
    if [[ "$CACHED_THRESHOLD" == "$THRESHOLD" || "$CACHED_THRESHOLD" == "$(printf '%g' "$THRESHOLD")" ]]; then
      CACHED_VERDICT=$(/usr/bin/python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['verdict'])" "$RECORD_PATH")
      CACHED_EXIT=$(/usr/bin/python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['exit_code'])" "$RECORD_PATH")
      echo "verify-model-provenance: cache hit ($((AGE_SECONDS/86400))d old, <${CACHE_DAYS}d window)"
      echo "  repo:    $REPO_ARG"
      echo "  verdict: $CACHED_VERDICT (exit $CACHED_EXIT)"
      echo "  record:  $RECORD_PATH"
      exit "$CACHED_EXIT"
    fi
  fi
fi

# Run scan; capture stdout (JSON) and stderr separately. Use threshold 0.50
# at the kit level by default so we receive marginal matches too; the 0.70
# policy is applied here in the wrapper. PROVENANCE_KIT_THRESHOLD overrides
# the kit-level cutoff (used by validation tests to force empty matches).
KIT_THRESHOLD="${PROVENANCE_KIT_THRESHOLD:-0.50}"
SCAN_OUT=$(mktemp)
SCAN_ERR=$(mktemp)
trap 'rm -f "$SCAN_OUT" "$SCAN_ERR"' EXIT

set +e
( cd "$KIT_DIR" && uv run --quiet provenancekit scan --json --threshold "$KIT_THRESHOLD" --top-k 5 "$REPO_ARG" ) \
  >"$SCAN_OUT" 2>"$SCAN_ERR"
SCAN_RC=$?
set -e

if (( SCAN_RC != 0 )); then
  echo "verify-model-provenance: scan command failed (rc=$SCAN_RC) for $REPO_ARG" >&2
  echo "stderr (last 20 lines):" >&2
  tail -n 20 "$SCAN_ERR" >&2 || true
  # Write a failure record so the next run sees the failure (cached for 30d unless force).
  /usr/bin/python3 - "$REPO_ARG" "$RECORD_PATH" "$THRESHOLD" "$SCAN_RC" <<'PY'
import json, sys, datetime, subprocess
repo, record_path, threshold, rc = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
record = {
    "schema_version": 1,
    "repo": repo,
    "verdict": "scan-failed",
    "exit_code": 1,
    "threshold": threshold,
    "kit_version": "1.0.0",
    "timestamp_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "scan_rc": rc,
    "matches": [],
    "note": "Provenance Kit scan failed; treat as unverified.",
}
with open(record_path, "w") as f:
    json.dump(record, f, indent=2)
PY
  echo "  record:  $RECORD_PATH (verdict=scan-failed, exit=1)"
  exit 1
fi

# Parse scan output, apply policy, write record.
/usr/bin/python3 - "$REPO_ARG" "$RECORD_PATH" "$THRESHOLD" "$SCAN_OUT" <<'PY'
import json, sys, datetime

repo, record_path, threshold, scan_out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
with open(scan_out) as f:
    scan = json.load(f)

matches = scan.get("matches", []) or []

def normalize(s: str) -> str:
    # "Qwen/Qwen2.5-Coder-7B-Instruct" -> "qwen2.5-coder-7b-instruct"
    return s.split("/")[-1].lower().replace("_", "-")

requested_norm = normalize(repo)

top = matches[0] if matches else None
top_score = (top or {}).get("scores", {}).get("pipeline_score") if top else None
top_id = (top or {}).get("model_id") if top else None

# Look across ALL matches above threshold for an exact-name hit. The kit
# routinely returns multiple sibling models at score 1.0 (match_type=exact_arch);
# top-1 ordering among ties is not stable, so a top-1-only check would mis-
# classify "verified-specific" as "verified-base-family" when the requested
# repo is in the tie cluster but not at rank 1.
specific_hit = any(
    (m.get("scores", {}).get("pipeline_score") or 0.0) >= threshold
    and normalize(m.get("model_id") or "") == requested_norm
    for m in matches
)

if top is None or top_score is None:
    verdict, exit_code = "unverified", 1
elif top_score >= threshold:
    if specific_hit:
        verdict, exit_code = "verified-specific", 0
    else:
        verdict, exit_code = "verified-base-family", 3
elif top_score >= 0.50:
    verdict, exit_code = "marginal", 2
else:
    verdict, exit_code = "unverified", 1

record = {
    "schema_version": 1,
    "repo": repo,
    "verdict": verdict,
    "exit_code": exit_code,
    "threshold": threshold,
    "kit_version": "1.0.0",
    "timestamp_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "top_matches": [
        {
            "model_id": m.get("model_id"),
            "family_id": m.get("family_id"),
            "pipeline_score": m.get("scores", {}).get("pipeline_score"),
            "match_type": m.get("match_type"),
            "provenance_decision": m.get("provenance_decision"),
        }
        for m in matches[:5]
    ],
    "model_info": {
        "architectures": scan.get("model_info", {}).get("architectures", []),
        "model_type": scan.get("model_info", {}).get("model_type"),
        "hidden_size": scan.get("model_info", {}).get("hidden_size"),
        "num_hidden_layers": scan.get("model_info", {}).get("num_hidden_layers"),
    },
    "scan_elapsed_ms": scan.get("elapsed_ms"),
}
with open(record_path, "w") as f:
    json.dump(record, f, indent=2)

print(f"verify-model-provenance: {verdict} (exit {exit_code})")
print(f"  repo:      {repo}")
print(f"  threshold: {threshold}")
if top is not None:
    print(f"  top match: {top_id} (score={top_score:.3f}, type={top.get('match_type')})")
    if exit_code == 3:
        print(f"  note:      base-family attestation — top match is not the specific requested repo.")
        print(f"             Inspect docs/_provenance for top-K to confirm lineage.")
elif verdict == "unverified":
    print(f"  no matches above 0.50 threshold; model not in Cisco fingerprint DB.")
print(f"  record:    {record_path}")
sys.exit(exit_code)
PY
