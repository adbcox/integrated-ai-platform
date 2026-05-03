#!/usr/bin/env bash
# Roadmap deliverable creation — D-17-39 flow surface.
#
# Single self-contained transaction: framework row + optional artifact ingest +
# OpenProject WP creation, with operator never invoking artifact-ingest.sh
# directly and never touching canonical filesystem paths.
#
# Usage:
#   scripts/roadmap-create.sh <deliverable-id> "<title>" \
#       [--status STATUS] [--reference "TEXT"] \
#       [--artifact <local-path>] [--class CLASS] \
#       [--no-op-sync] [--dry-run]
#
# Required:
#   deliverable-id    D-NN-NN (e.g. D-17-40)
#   title             Short title (one line)
#
# Optional:
#   --status          NOT STARTED | IN PROGRESS | DONE | DEFERRED
#                     default: IN PROGRESS
#   --reference       Reference column text. Defaults to "added <today>".
#                     If --artifact is given, the qnap:// pointer is appended.
#   --artifact        Local path to a binary artifact (PDF, schematic, etc.)
#                     Forwarded to scripts/artifact-ingest.sh.
#   --class           ACL class for ingestion: property | schematics |
#                     vendor-docs | source-files. Default: property.
#                     Ignored unless --artifact is given.
#   --no-op-sync      Skip OpenProject WP creation step (framework row only).
#   --dry-run         Print planned actions, change nothing on disk.
#
# Behavior:
#   1. Validate deliverable-id format + status word + ACL class
#   2. Verify D-NN-NN doesn't already exist in PROJECT_FRAMEWORK.md (no
#      duplicate-row creation; if you want to update an existing row, edit
#      the markdown directly)
#   3. If --artifact: invoke scripts/artifact-ingest.sh, capture qnap:// pointer
#   4. Insert framework row at the bottom of the matching phase table
#   5. Stage the framework edit (git add) — but never commit
#   6. Unless --no-op-sync: invoke openproject-sync-from-framework.py
#      --phase NN to mint the OpenProject WP for the new row
#   7. Print a compact summary: deliverable id, qnap:// pointer (if any),
#      OpenProject WP id (if synced), next-step git commit guidance
#
# Exit codes:
#   0  success
#   64 usage / argument error
#   65 validation failure
#   66 artifact ingest failed
#   67 framework row insertion failed
#   68 row already exists
#   69 OpenProject sync failed
#
# Composes: D-17-37 (artifact substrate) + scripts/openproject-sync-from-framework.py
# Doctrine: docs/architecture-facts/integration-audit-doctrine.md Finding 5;
#           CLAUDE.md "Roadmap Ingestion Flow Doctrine (D-17-39)" block.

set -euo pipefail

REPO_ROOT="/Users/admin/repos/integrated-ai-platform"
FRAMEWORK_MD="$REPO_ROOT/docs/PROJECT_FRAMEWORK.md"
ARTIFACT_INGEST="$REPO_ROOT/scripts/artifact-ingest.sh"
OP_SYNC="$REPO_ROOT/scripts/openproject-sync-from-framework.py"

usage() {
    sed -n '3,40p' "$0"
    exit 64
}

if [ "$#" -lt 2 ]; then usage; fi

DELIVERABLE_ID="$1"
TITLE="$2"
shift 2

STATUS="IN PROGRESS"
REFERENCE=""
ARTIFACT=""
ACL_CLASS="property"
DO_OP_SYNC=1
DRY_RUN=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --status)     STATUS="$2"; shift 2 ;;
        --reference)  REFERENCE="$2"; shift 2 ;;
        --artifact)   ARTIFACT="$2"; shift 2 ;;
        --class)      ACL_CLASS="$2"; shift 2 ;;
        --no-op-sync) DO_OP_SYNC=0; shift ;;
        --dry-run)    DRY_RUN=1; shift ;;
        -h|--help)    usage ;;
        *) echo "ERROR: unknown flag $1" >&2; usage ;;
    esac
done

# ── Validate deliverable-id format ─────────────────────────────────────────
if ! echo "$DELIVERABLE_ID" | grep -Eq '^D-[0-9]+-[0-9]+$'; then
    echo "ERROR: deliverable-id must match D-NN-NN (got: $DELIVERABLE_ID)" >&2
    exit 65
fi
PHASE_NUM=$(echo "$DELIVERABLE_ID" | awk -F- '{print $2}')

# ── Validate status word ───────────────────────────────────────────────────
case "$STATUS" in
    "NOT STARTED"|"IN PROGRESS"|"DONE"|"DEFERRED") ;;
    *) echo "ERROR: --status must be one of: NOT STARTED | IN PROGRESS | DONE | DEFERRED (got: $STATUS)" >&2; exit 65 ;;
esac

# ── Validate ACL class (only meaningful with --artifact) ───────────────────
if [ -n "$ARTIFACT" ]; then
    case "$ACL_CLASS" in
        property|schematics|vendor-docs|source-files) ;;
        *) echo "ERROR: --class must be one of: property | schematics | vendor-docs | source-files (got: $ACL_CLASS)" >&2; exit 65 ;;
    esac
    if [ ! -f "$ARTIFACT" ]; then
        echo "ERROR: --artifact file not found: $ARTIFACT" >&2
        exit 65
    fi
fi

# ── Validate title is single-line, non-empty, no pipe character ────────────
if [ -z "$TITLE" ]; then
    echo "ERROR: title is empty" >&2; exit 65
fi
if echo "$TITLE" | grep -q '|'; then
    echo "ERROR: title contains '|' which would break the markdown table" >&2; exit 65
fi
if [ "$(echo "$TITLE" | wc -l | tr -d ' ')" != "1" ]; then
    echo "ERROR: title must be a single line" >&2; exit 65
fi

# ── Verify framework file exists, deliverable-id is unique ─────────────────
if [ ! -f "$FRAMEWORK_MD" ]; then
    echo "ERROR: framework not found: $FRAMEWORK_MD" >&2; exit 65
fi
if grep -qE "^\| $DELIVERABLE_ID[: ]" "$FRAMEWORK_MD"; then
    echo "ERROR: $DELIVERABLE_ID already exists in $FRAMEWORK_MD — edit the row directly, do not re-create" >&2
    exit 68
fi

# ── Locate phase section ────────────────────────────────────────────────────
PHASE_HEADING_LINE=$(grep -n "^## .* Phase ${PHASE_NUM} —" "$FRAMEWORK_MD" | head -1 | awk -F: '{print $1}')
if [ -z "$PHASE_HEADING_LINE" ]; then
    echo "ERROR: no phase section found for Phase ${PHASE_NUM} in $FRAMEWORK_MD" >&2
    echo "       (looked for: '## … Phase ${PHASE_NUM} —')" >&2
    exit 65
fi

# Find the next phase heading (or end-of-file) to bound the insertion range.
NEXT_HEADING_LINE=$(awk -v start="$PHASE_HEADING_LINE" '
    NR > start && /^## / { print NR; exit }
' "$FRAMEWORK_MD")
if [ -z "$NEXT_HEADING_LINE" ]; then
    NEXT_HEADING_LINE=$(wc -l < "$FRAMEWORK_MD" | tr -d ' ')
    NEXT_HEADING_LINE=$((NEXT_HEADING_LINE + 1))
fi

# Find the last `| D-NN-…` row inside the phase section — we insert right after it.
LAST_ROW_LINE=$(awk -v start="$PHASE_HEADING_LINE" -v end="$NEXT_HEADING_LINE" '
    NR > start && NR < end && /^\| D-[0-9]+-/ { last = NR }
    END { if (last) print last }
' "$FRAMEWORK_MD")
if [ -z "$LAST_ROW_LINE" ]; then
    echo "ERROR: no existing D-NN-NN rows found inside Phase ${PHASE_NUM} section — manual placement required" >&2
    exit 67
fi

# ── Optional: artifact ingest ──────────────────────────────────────────────
QNAP_PTR=""
if [ -n "$ARTIFACT" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "[dry-run] would invoke: $ARTIFACT_INGEST $DELIVERABLE_ID $ARTIFACT --class $ACL_CLASS"
        QNAP_PTR="qnap://download/manual/roadmap-artifacts/phase-${PHASE_NUM}/${DELIVERABLE_ID}/source/$(basename "$ARTIFACT")"
    else
        if [ ! -x "$ARTIFACT_INGEST" ]; then
            echo "ERROR: $ARTIFACT_INGEST not executable" >&2; exit 66
        fi
        QNAP_PTR=$("$ARTIFACT_INGEST" "$DELIVERABLE_ID" "$ARTIFACT" --class "$ACL_CLASS")
        if [ -z "$QNAP_PTR" ]; then
            echo "ERROR: artifact-ingest produced no qnap:// pointer" >&2; exit 66
        fi
    fi
fi

# ── Compose reference column ───────────────────────────────────────────────
TODAY=$(date -u +%Y-%m-%d)
if [ -z "$REFERENCE" ]; then
    REFERENCE="added ${TODAY} via roadmap-create.sh"
fi
if [ -n "$QNAP_PTR" ]; then
    REFERENCE="${REFERENCE}. Artifact: \`${QNAP_PTR}\`"
fi

# ── Compose row ─────────────────────────────────────────────────────────────
NEW_ROW="| ${DELIVERABLE_ID}: ${TITLE} | ${STATUS} | ${REFERENCE} |"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] would insert at line $((LAST_ROW_LINE + 1)) of $FRAMEWORK_MD:"
    echo "[dry-run] $NEW_ROW"
    if [ "$DO_OP_SYNC" -eq 1 ]; then
        echo "[dry-run] would then run: $OP_SYNC --phase $PHASE_NUM"
    fi
    exit 0
fi

# ── Insert row (after LAST_ROW_LINE) ───────────────────────────────────────
TMPFILE=$(mktemp)
awk -v insert_after="$LAST_ROW_LINE" -v new_row="$NEW_ROW" '
    { print }
    NR == insert_after { print new_row }
' "$FRAMEWORK_MD" > "$TMPFILE"

# Sanity: new file must be exactly 1 line longer.
OLD_LINES=$(wc -l < "$FRAMEWORK_MD" | tr -d ' ')
NEW_LINES=$(wc -l < "$TMPFILE" | tr -d ' ')
if [ "$NEW_LINES" != "$((OLD_LINES + 1))" ]; then
    echo "ERROR: row insertion produced unexpected line count ($OLD_LINES → $NEW_LINES); aborting without write" >&2
    rm -f "$TMPFILE"
    exit 67
fi
mv "$TMPFILE" "$FRAMEWORK_MD"

# Stage but don't commit (operator owns the commit).
git -C "$REPO_ROOT" add "$FRAMEWORK_MD" >/dev/null 2>&1 || true

# ── OpenProject sync ───────────────────────────────────────────────────────
OP_RESULT=""
if [ "$DO_OP_SYNC" -eq 1 ]; then
    if [ ! -f "$OP_SYNC" ]; then
        echo "WARN: $OP_SYNC not found; skipping OP sync (framework row inserted, OP WP not minted)" >&2
    else
        VENV_PY="/Users/admin/.venv-block-4c/bin/python"
        if [ ! -x "$VENV_PY" ]; then
            VENV_PY="python3"
        fi
        if "$VENV_PY" "$OP_SYNC" --phase "$PHASE_NUM" >/tmp/op-sync.log 2>&1; then
            OP_RESULT="ok"
        else
            echo "WARN: OpenProject sync exited non-zero (see /tmp/op-sync.log); framework row stands, WP creation deferred" >&2
            OP_RESULT="failed"
        fi
    fi
fi

# ── Summary ────────────────────────────────────────────────────────────────
echo "── roadmap-create.sh: $DELIVERABLE_ID created ────────────────────"
echo "  framework row:   inserted at $FRAMEWORK_MD line $((LAST_ROW_LINE + 1))"
echo "  status:          $STATUS"
if [ -n "$QNAP_PTR" ]; then
    echo "  artifact:        $QNAP_PTR"
fi
if [ "$DO_OP_SYNC" -eq 1 ]; then
    echo "  OpenProject:     $OP_RESULT"
fi
echo "  next:            review with 'git diff --staged' then commit"
