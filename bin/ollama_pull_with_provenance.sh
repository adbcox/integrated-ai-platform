#!/usr/bin/env bash
# ollama_pull_with_provenance.sh — D-17-122: Ollama pull with Cisco provenance scan.
#
# Usage:
#   bin/ollama_pull_with_provenance.sh <ollama_model> [<hf_id>] [options]
#
# Arguments:
#   <ollama_model>   Ollama model name+tag (e.g. qwen2.5-coder:14b)
#   <hf_id>          Upstream HuggingFace repo ID (e.g. Qwen/Qwen2.5-Coder-14B-Instruct)
#                    If omitted, looked up from config/model_provenance/ollama_to_hf_mapping.yaml
#
# Options:
#   --threshold N    Min pipeline_score to treat as VERIFIED (default: 0.85)
#   --skip-provenance  Skip provenance scan (records SKIPPED verdict)
#   --derivation-type TYPE  Override derivation_type in record
#   --dry-run        Pull model but skip scan; record DRY_RUN verdict
#
# Exit codes:
#   0  Pull succeeded + provenance VERIFIED (or N_A / skipped)
#   1  Usage error
#   2  ollama pull failed
#   3  Provenance SCAN_OOM or UNKNOWN (non-zero; operator must review)
#   4  Provenance threshold not met (pipeline_score below threshold)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PROVENANCEKIT="$REPO_ROOT/venv-provenance/bin/provenancekit"
VENV_PYTHON="$REPO_ROOT/venv-provenance/bin/python3"
MAPPING_FILE="$REPO_ROOT/config/model_provenance/ollama_to_hf_mapping.yaml"
OUTPUT_DIR="$REPO_ROOT/artifacts/model_provenance"
KIT_VERSION="1.0.0"

THRESHOLD="0.85"
SKIP_PROVENANCE=0
DRY_RUN=0
DERIVATION_TYPE="direct_quantization"

# ── Argument parsing ──────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ollama_model> [<hf_id>] [--threshold N] [--skip-provenance] [--dry-run]" >&2
  exit 1
fi

OLLAMA_MODEL="$1"; shift
HF_ID=""

# Second positional arg may be hf_id (if it contains '/')
if [[ $# -gt 0 && "$1" != --* ]]; then
  HF_ID="$1"; shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --threshold)       THRESHOLD="$2"; shift 2 ;;
    --skip-provenance) SKIP_PROVENANCE=1; shift ;;
    --dry-run)         DRY_RUN=1; shift ;;
    --derivation-type) DERIVATION_TYPE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Timestamp / filename helpers ──────────────────────────────────────────────
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DATE_STR="$(date -u +%Y-%m-%d)"
SAFE_MODEL="${OLLAMA_MODEL//:/_}"
SAFE_MODEL="${SAFE_MODEL//\//_}"
RECORD_FILE="$OUTPUT_DIR/${SAFE_MODEL}_${DATE_STR}.json"

mkdir -p "$OUTPUT_DIR"

# ── HF ID lookup from mapping if not provided ─────────────────────────────────
if [[ -z "$HF_ID" ]]; then
  HF_ID="$("$VENV_PYTHON" - <<EOF
import yaml, sys
mapping = yaml.safe_load(open('$MAPPING_FILE'))
for m in mapping.get('ollama_models', []):
    if m['ollama_name'] == '$OLLAMA_MODEL':
        target = m.get('provenance_scan_target') or ''
        print(target)
        sys.exit(0)
print('')
EOF
)"
  if [[ -z "$HF_ID" ]]; then
    echo "[provenance] WARNING: No HF ID found in mapping for '$OLLAMA_MODEL'" >&2
    echo "[provenance] Pass <hf_id> as second argument or update $MAPPING_FILE" >&2
  fi
fi

# ── Step 1: ollama pull ───────────────────────────────────────────────────────
echo "[provenance] Pulling $OLLAMA_MODEL ..."
if ! ollama pull "$OLLAMA_MODEL" 2>&1; then
  echo "[provenance] ERROR: ollama pull failed for $OLLAMA_MODEL" >&2
  exit 2
fi
echo "[provenance] Pull complete."

# ── Step 2: Provenance scan ───────────────────────────────────────────────────
VERDICT="UNKNOWN"
CONFIDENCE="null"
REASON=""
PIPELINE_SCORE="null"
MFI_SCORE="null"
TOKENIZER_SCORE="null"
MATCH_COUNT=0
ELAPSED_MS="null"
PROVENANCE_DECISION="null"
SCOPE_CAVEATS='["Provenance verified at upstream HF source; does not inspect local GGUF blob conversion"]'

if [[ $SKIP_PROVENANCE -eq 1 ]]; then
  VERDICT="SKIPPED"
  REASON="--skip-provenance flag set by operator"
elif [[ -z "$HF_ID" ]]; then
  VERDICT="UNKNOWN"
  REASON="No upstream HF ID available; cannot run provenance scan"
  SCOPE_CAVEATS='["No HF ID mapping found; add entry to config/model_provenance/ollama_to_hf_mapping.yaml"]'
elif [[ $DRY_RUN -eq 1 ]]; then
  VERDICT="DRY_RUN"
  REASON="--dry-run flag; scan skipped"
else
  echo "[provenance] Scanning $OLLAMA_MODEL upstream at HF: $HF_ID ..."
  SCAN_OUT="$("$VENV_PROVENANCEKIT" scan "$HF_ID" --json --top-k 3 2>/dev/null)" || SCAN_RC=$?
  SCAN_RC="${SCAN_RC:-0}"

  if [[ $SCAN_RC -eq -9 ]] || [[ "$SCAN_OUT" == "" && $SCAN_RC -ne 0 ]]; then
    VERDICT="SCAN_OOM"
    REASON="OOM-killed or hard crash scanning $HF_ID; model too large for available RAM"
    SCOPE_CAVEATS='["Kit loads model weights for signal extraction; large models OOM on Mac Mini","Re-run on Mac Studio (96GB) for large models"]'
  else
    # Parse JSON from scan output
    PARSED="$("$VENV_PYTHON" - <<EOF
import json, sys
raw = '''$SCAN_OUT'''
idx = raw.find('{')
if idx == -1:
    print('{}')
    sys.exit(0)
decoder = json.JSONDecoder()
try:
    d, _ = decoder.raw_decode(raw, idx)
    print(json.dumps(d))
except:
    print('{}')
EOF
)"
    if [[ "$PARSED" == "{}" ]]; then
      # Check for kit-level error
      SCAN_ERR="$("$VENV_PROVENANCEKIT" scan "$HF_ID" --json 2>&1 >/dev/null || true)"
      VERDICT="UNKNOWN"
      REASON="Could not parse scan output; kit error: ${SCAN_ERR##*Error: }"
    else
      MATCHES="$(echo "$PARSED" | "$VENV_PYTHON" -c "
import json, sys
d = json.load(sys.stdin)
matches = d.get('matches', [])
print(json.dumps(matches[0] if matches else {}))
")"
      PIPELINE_SCORE="$(echo "$MATCHES" | "$VENV_PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('scores',{}).get('pipeline_score','null'))")"
      MFI_SCORE="$(echo "$MATCHES" | "$VENV_PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('scores',{}).get('mfi_score','null'))")"
      TOKENIZER_SCORE="$(echo "$MATCHES" | "$VENV_PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('scores',{}).get('tokenizer_score','null'))")"
      PROVENANCE_DECISION="$(echo "$MATCHES" | "$VENV_PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('provenance_decision','null'))")"
      MATCH_COUNT="$(echo "$PARSED" | "$VENV_PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('match_count',0))")"
      ELAPSED_MS="$(echo "$PARSED" | "$VENV_PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('elapsed_ms','null'))")"
      CONFIDENCE="$PIPELINE_SCORE"

      # Determine verdict based on threshold
      VERDICT="$("$VENV_PYTHON" - <<EOF
score = $PIPELINE_SCORE if '$PIPELINE_SCORE' != 'null' else 0.0
threshold = float('$THRESHOLD')
decision = '$PROVENANCE_DECISION'
if score >= threshold or 'Confirmed' in decision:
    print('VERIFIED')
elif score >= 0.70:
    print('LIKELY')
elif score >= 0.50:
    print('WEAK_MATCH')
else:
    print('NO_MATCH')
EOF
)"
      REASON="$PROVENANCE_DECISION (pipeline_score=$PIPELINE_SCORE, hf_id=$HF_ID)"
    fi
  fi
fi

# ── Step 3: Write provenance record ──────────────────────────────────────────
"$VENV_PYTHON" - <<EOF
import json
record = {
    "model_id": "$OLLAMA_MODEL",
    "scan_timestamp": "$TIMESTAMP",
    "upstream_hf_id": "$HF_ID" if "$HF_ID" else None,
    "derivation_type": "$DERIVATION_TYPE",
    "cisco_kit_version": "$KIT_VERSION",
    "verdict": "$VERDICT",
    "confidence": $CONFIDENCE,
    "reason": "$REASON",
    "provenance_decision": "$PROVENANCE_DECISION" if "$PROVENANCE_DECISION" not in ("", "null") else None,
    "pipeline_score": $PIPELINE_SCORE,
    "mfi_score": $MFI_SCORE,
    "tokenizer_score": $TOKENIZER_SCORE,
    "match_count": $MATCH_COUNT,
    "elapsed_ms": $ELAPSED_MS,
    "scope_caveats": $SCOPE_CAVEATS,
}
with open("$RECORD_FILE", "w") as f:
    json.dump(record, f, indent=2)
print(json.dumps(record, indent=2))
EOF

echo ""
echo "[provenance] verdict=$VERDICT confidence=$CONFIDENCE"
echo "[provenance] record → $RECORD_FILE"

# ── Step 4: Exit code based on verdict ───────────────────────────────────────
case "$VERDICT" in
  VERIFIED|N_A|SKIPPED|DRY_RUN|N_A_GATED|LIKELY)
    exit 0 ;;
  SCAN_OOM|UNKNOWN)
    echo "[provenance] WARNING: Verdict requires operator review before trusting this model" >&2
    exit 3 ;;
  NO_MATCH|WEAK_MATCH)
    echo "[provenance] WARNING: pipeline_score=$PIPELINE_SCORE below threshold=$THRESHOLD" >&2
    exit 4 ;;
  *)
    exit 3 ;;
esac
