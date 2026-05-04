#!/usr/bin/env bash
# verify-model-provenance.sh — D-17-92 lineage-attestation gate.
#
# Wraps Cisco Model Provenance Kit (cisco-ai-defense/model-provenance-kit
# v1.0.0) `scan` mode. Returns a verdict + writes a provenance record to
# docs/_provenance/<sanitized-repo>.json.
#
# This is a LINEAGE-ATTESTATION gate, NOT a signature-verification gate.
# It answers "do this model's weights statistically match a known
# reference fingerprint?" — not "is this artifact cryptographically
# signed by its claimed publisher?". See
# docs/architecture-facts/model-provenance-doctrine.md.
#
# Exit codes:
#   0 = verified-specific      (top match is the requested repo, score >= threshold)
#   1 = unverified             (no match >= threshold; or scan failed)
#   2 = marginal               (best score in [0.50, threshold))
#   3 = verified-base-family   (match >= threshold but to a base/sibling, not the
#                               specific requested repo — still a real attestation,
#                               but coarser than variant-level)
#
# Usage:
#   verify-model-provenance.sh <ollama-tag>           resolve via config/model-hf-map.yaml
#   verify-model-provenance.sh --hf <hf-repo>         direct HuggingFace model ID
#   verify-model-provenance.sh --refresh-db            update deep-signals fingerprint DB
#   verify-model-provenance.sh --status               show kit + DB status
#
# Examples:
#   verify-model-provenance.sh qwen2.5-coder:14b
#   verify-model-provenance.sh --hf Qwen/Qwen2.5-Coder-14B-Instruct
#   verify-model-provenance.sh --refresh-db
#
# Configuration (env):
#   PROVENANCE_THRESHOLD       default 0.70 (Cisco-calibrated; F1 0.963 at 0.70)
#   PROVENANCE_KIT_DIR         default ~/repos/model-provenance-kit
#   PROVENANCE_CACHE_DAYS      default 30
#   PROVENANCE_RECORDS_DIR     default <repo>/docs/_provenance
#   PROVENANCE_FORCE           if set, ignore cache
#   PROVENANCE_KIT_THRESHOLD   kit-level cutoff for returned matches (default 0.50;
#                              wrapper still applies PROVENANCE_THRESHOLD policy on top)
#
# GGUF / NO_MATCH note:
#   Ollama models are GGUF-quantized; the Cisco kit fingerprints against HuggingFace
#   native weights (BF16/FP16). A NO_MATCH (exit 1) on a GGUF-backed Ollama model
#   is INFORMATIONAL, not a hard failure. See model-provenance-doctrine.md §GGUF.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HF_MAP="${REPO_ROOT}/config/model-hf-map.yaml"

# Resolve ollama tag → HF model ID via config/model-hf-map.yaml
resolve_ollama_tag() {
  local tag="$1"
  python3 - "$HF_MAP" "$tag" <<'PY'
import sys, re
map_file, tag = sys.argv[1], sys.argv[2]
# Keys may contain colons (e.g. "qwen2.5-coder:14b"). The YAML value is a
# HF repo ID "Org/repo" — exactly one slash, no leading whitespace. Match
# lines of the form: <key>: <value> where <key> == tag (case-sensitive).
pattern = re.compile(r'^(.+?):\s+(\S.*)$')
try:
    with open(map_file) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith('#') or not line:
                continue
            m = pattern.match(line)
            if m and m.group(1) == tag:
                print(m.group(2).strip())
                sys.exit(0)
except FileNotFoundError:
    sys.exit(1)
sys.exit(1)
PY
}

# Parse subcommands / flags
REFRESH_DB=0
STATUS_ONLY=0
DIRECT_HF=""
OLLAMA_TAG=""

case "${1:-}" in
  --refresh-db)
    REFRESH_DB=1 ;;
  --status)
    STATUS_ONLY=1 ;;
  --hf)
    if [[ $# -lt 2 ]]; then
      echo "ERROR: --hf requires a HuggingFace model ID" >&2; exit 64
    fi
    DIRECT_HF="$2" ;;
  -h|--help)
    sed -n '2,46p' "$0" | sed 's/^# //' | sed 's/^#//'; exit 0 ;;
  "")
    echo "usage: $0 <ollama-tag|--hf <hf-repo>|--refresh-db|--status>" >&2; exit 64 ;;
  -*)
    echo "ERROR: unknown option '$1'" >&2; exit 64 ;;
  *)
    OLLAMA_TAG="$1" ;;
esac

# Resolve to HF repo ID
if [[ $REFRESH_DB -eq 0 && $STATUS_ONLY -eq 0 ]]; then
  if [[ -n "$DIRECT_HF" ]]; then
    REPO_ARG="$DIRECT_HF"
  else
    RESOLVED=$(resolve_ollama_tag "$OLLAMA_TAG" 2>/dev/null || true)
    if [[ -z "$RESOLVED" ]]; then
      echo "ERROR: '$OLLAMA_TAG' not found in $HF_MAP" >&2
      echo "       Add entry:  $OLLAMA_TAG: <HuggingFace/repo-id>" >&2
      exit 64
    fi
    echo "verify-model-provenance: resolved $OLLAMA_TAG → $RESOLVED"
    REPO_ARG="$RESOLVED"
  fi
else
  REPO_ARG=""
fi

THRESHOLD="${PROVENANCE_THRESHOLD:-0.70}"
KIT_DIR="${PROVENANCE_KIT_DIR:-$HOME/repos/model-provenance-kit}"
CACHE_DAYS="${PROVENANCE_CACHE_DAYS:-30}"
RECORDS_DIR="${PROVENANCE_RECORDS_DIR:-$REPO_ROOT/docs/_provenance}"
ARTIFACT_DIR="$REPO_ROOT/artifacts/model-provenance"
mkdir -p "$RECORDS_DIR" "$ARTIFACT_DIR"

if [[ ! -d "$KIT_DIR" ]]; then
  echo "ERROR: Provenance Kit not installed at $KIT_DIR" >&2
  echo "  git clone https://github.com/cisco-ai-defense/model-provenance-kit.git $KIT_DIR" >&2
  echo "  cd $KIT_DIR && uv sync" >&2
  exit 70
fi

# Handle --status and --refresh-db before any scan logic
if [[ $STATUS_ONLY -eq 1 ]]; then
  echo "verify-model-provenance: kit status"
  echo "  Kit dir:   $KIT_DIR"
  echo "  HF map:    $HF_MAP"
  echo "  Records:   $RECORDS_DIR"
  echo "  Artifacts: $ARTIFACT_DIR"
  echo "  Threshold: $THRESHOLD"
  echo ""
  (cd "$KIT_DIR" && uv run --quiet provenancekit download-deepsignals-fingerprint --status 2>&1) || \
    echo "  Deep-signals: not downloaded (run --refresh-db)"
  exit 0
fi

if [[ $REFRESH_DB -eq 1 ]]; then
  echo "verify-model-provenance: refreshing deep-signals fingerprint database..."
  (cd "$KIT_DIR" && uv run --quiet provenancekit download-deepsignals-fingerprint --update 2>&1)
  echo "verify-model-provenance: database refreshed"
  exit 0
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

# Parse scan output, apply policy, write record + JSONL artifact.
/usr/bin/python3 - "$REPO_ARG" "$RECORD_PATH" "$THRESHOLD" "$SCAN_OUT" "$ARTIFACT_DIR" <<'PY'
import json, sys, datetime

repo, record_path, threshold, scan_out, artifact_dir = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5]
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

# Append to dated JSONL artifact chronicle (hash-only; no credential values)
import pathlib, time
artifact_path = pathlib.Path(artifact_dir) / f"provenance-{datetime.datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
artifact_path.parent.mkdir(parents=True, exist_ok=True)
with artifact_path.open("a") as f:
    json.dump({k: v for k, v in record.items()
               if k not in ("model_info",)}, f)
    f.write("\n")

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
