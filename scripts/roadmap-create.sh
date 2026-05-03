#!/usr/bin/env bash
# Roadmap deliverable creation / close-out — D-17-39 flow surface.
#
# Two modes:
#   1. CREATE (default): single self-contained transaction — framework row +
#      optional artifact ingest + OpenProject WP creation. Operator never
#      invokes artifact-ingest.sh directly and never touches canonical
#      filesystem paths.
#   2. UPDATE-EXISTING (--update-existing): close-out path for an existing
#      IN PROGRESS / NOT STARTED row whose gating artifact has now landed.
#      Augments reference with qnap:// pointer + flips status. Idempotent.
#
# Usage:
#   # Create new deliverable
#   scripts/roadmap-create.sh <deliverable-id> "<title>" \
#       [--status STATUS] [--reference "TEXT"] \
#       [--artifact <local-path>] [--class CLASS] \
#       [--no-op-sync] [--dry-run]
#
#   # Close existing deliverable (title arg ignored — reads from current row)
#   scripts/roadmap-create.sh <deliverable-id> "" --update-existing \
#       --artifact <local-path> [--class CLASS] [--status STATUS] \
#       [--no-op-sync] [--dry-run]
#
# Required:
#   deliverable-id    D-NN-NN (e.g. D-17-40)
#   title             Short title (one line). Pass "" with --update-existing.
#
# Optional:
#   --status          NOT STARTED | IN PROGRESS | DONE | DEFERRED
#                     default for create:           IN PROGRESS
#                     default for --update-existing: DONE
#   --reference       Reference column text. Defaults to "added <today>".
#                     If --artifact is given, the qnap:// pointer is appended.
#                     With --update-existing: appended to existing reference
#                     as a "Closed via --update-existing <date>" note.
#   --artifact        Local path to a binary artifact (PDF, schematic, etc.)
#                     Forwarded to scripts/artifact-ingest.sh. REQUIRED with
#                     --update-existing (the whole point of close-out is the
#                     artifact landing).
#   --class           ACL class for ingestion: property | schematics |
#                     vendor-docs | source-files. Default: property.
#                     Ignored unless --artifact is given.
#   --update-existing Close-out mode: locate existing row by ID; reject if
#                     row not found OR status is already DONE/DEFERRED.
#                     Requires --artifact. Idempotent (re-run with same args
#                     after a successful close = no-op).
#   --no-op-sync      Skip OpenProject WP creation/update step.
#   --dry-run         Print planned actions, change nothing on disk.
#
# Behavior (create mode):
#   1. Validate deliverable-id format + status word + ACL class
#   2. Verify D-NN-NN doesn't already exist in PROJECT_FRAMEWORK.md
#   3. If --artifact: invoke scripts/artifact-ingest.sh, capture qnap:// pointer
#   4. Insert framework row at the bottom of the matching phase table
#   5. Stage the framework edit (git add) — but never commit
#   6. Unless --no-op-sync: invoke openproject-sync-from-framework.py
#   7. Print summary
#
# Behavior (--update-existing mode):
#   1. Validate ID + ACL class; require --artifact
#   2. Locate existing row by ID; reject if not found or already DONE/DEFERRED
#   3. Detect idempotent re-run (qnap:// already present + status already
#      matches target) → exit 0 with no-op message
#   4. Invoke scripts/artifact-ingest.sh (idempotent on size match)
#   5. Replace status word + append qnap:// pointer + close-out note to ref
#   6. Stage edit; invoke OP sync (PATCHes existing WP via diff path)
#   7. Print summary
#
# Exit codes:
#   0  success (or idempotent no-op)
#   64 usage / argument error
#   65 validation failure
#   66 artifact ingest failed
#   67 framework row insertion / update failed
#   68 row already exists (create mode) OR row not found (--update-existing)
#   69 OpenProject sync failed
#   70 row already DONE/DEFERRED (--update-existing rejection)
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

STATUS=""
REFERENCE=""
ARTIFACT=""
ACL_CLASS="property"
DO_OP_SYNC=1
DRY_RUN=0
UPDATE_EXISTING=0
STATUS_EXPLICIT=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --status)          STATUS="$2"; STATUS_EXPLICIT=1; shift 2 ;;
        --reference)       REFERENCE="$2"; shift 2 ;;
        --artifact)        ARTIFACT="$2"; shift 2 ;;
        --class)           ACL_CLASS="$2"; shift 2 ;;
        --update-existing) UPDATE_EXISTING=1; shift ;;
        --no-op-sync)      DO_OP_SYNC=0; shift ;;
        --dry-run)         DRY_RUN=1; shift ;;
        -h|--help)         usage ;;
        *) echo "ERROR: unknown flag $1" >&2; usage ;;
    esac
done

# Mode-aware default status.
if [ "$STATUS_EXPLICIT" -eq 0 ]; then
    if [ "$UPDATE_EXISTING" -eq 1 ]; then
        STATUS="DONE"
    else
        STATUS="IN PROGRESS"
    fi
fi

# --update-existing requires --artifact (the whole point is the artifact landing).
if [ "$UPDATE_EXISTING" -eq 1 ] && [ -z "$ARTIFACT" ]; then
    echo "ERROR: --update-existing requires --artifact (the gating artifact must be provided)" >&2
    exit 64
fi

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

# ── Validate title (create mode only) ──────────────────────────────────────
# In update-existing mode, title is read from the existing row; arg is ignored.
if [ "$UPDATE_EXISTING" -eq 0 ]; then
    if [ -z "$TITLE" ]; then
        echo "ERROR: title is empty" >&2; exit 65
    fi
    if echo "$TITLE" | grep -q '|'; then
        echo "ERROR: title contains '|' which would break the markdown table" >&2; exit 65
    fi
    if [ "$(echo "$TITLE" | wc -l | tr -d ' ')" != "1" ]; then
        echo "ERROR: title must be a single line" >&2; exit 65
    fi
fi

# ── Verify framework file exists, presence/absence per mode ────────────────
if [ ! -f "$FRAMEWORK_MD" ]; then
    echo "ERROR: framework not found: $FRAMEWORK_MD" >&2; exit 65
fi
if [ "$UPDATE_EXISTING" -eq 1 ]; then
    if ! grep -qE "^\| $DELIVERABLE_ID[: ]" "$FRAMEWORK_MD"; then
        echo "ERROR: --update-existing requires existing row; $DELIVERABLE_ID not found in $FRAMEWORK_MD" >&2
        exit 68
    fi
else
    if grep -qE "^\| $DELIVERABLE_ID[: ]" "$FRAMEWORK_MD"; then
        echo "ERROR: $DELIVERABLE_ID already exists in $FRAMEWORK_MD — use --update-existing to close-out an IN PROGRESS row, or edit the row directly" >&2
        exit 68
    fi
fi

# ── UPDATE-EXISTING mode: locate row, validate state, idempotency check ────
if [ "$UPDATE_EXISTING" -eq 1 ]; then
    EXISTING_ROW_LINE=$(grep -nE "^\| $DELIVERABLE_ID[: ]" "$FRAMEWORK_MD" | head -1 | awk -F: '{print $1}')
    if [ -z "$EXISTING_ROW_LINE" ]; then
        echo "ERROR: could not locate row line for $DELIVERABLE_ID (grep matched but line extraction failed)" >&2
        exit 68
    fi
    EXISTING_ROW=$(sed -n "${EXISTING_ROW_LINE}p" "$FRAMEWORK_MD")

    # Parse columns 1, 2, 3 (title-cell, status-cell, reference-cell).
    # Row format: | <id>: <title> | <status> | <reference> |
    EXISTING_TITLE_CELL=$(printf '%s\n' "$EXISTING_ROW" | awk -F'|' '{gsub(/^ +| +$/,"",$2); print $2}')
    EXISTING_STATUS_CELL=$(printf '%s\n' "$EXISTING_ROW" | awk -F'|' '{gsub(/^ +| +$/,"",$3); print $3}')
    EXISTING_REF_CELL=$(printf '%s\n' "$EXISTING_ROW" | awk -F'|' '{
        # Reference is everything from $4 to second-to-last field (last is empty after trailing |).
        out = ""
        for (i = 4; i <= NF - 1; i++) { out = (out == "" ? $i : out "|" $i) }
        gsub(/^ +| +$/, "", out)
        print out
    }')

    # Reject if already DONE or DEFERRED (terminal states; no close-out needed).
    case "$EXISTING_STATUS_CELL" in
        DONE|DEFERRED)
            # Check for idempotent re-run: same target status + qnap:// pointer for THIS artifact already present.
            EXPECTED_QNAP="qnap://download/manual/roadmap-artifacts/phase-${PHASE_NUM}/${DELIVERABLE_ID}/source/$(basename "$ARTIFACT")"
            if [ "$EXISTING_STATUS_CELL" = "$STATUS" ] && printf '%s' "$EXISTING_REF_CELL" | grep -qF "$EXPECTED_QNAP"; then
                echo "── roadmap-create.sh: $DELIVERABLE_ID idempotent no-op ──────────"
                echo "  status:          already $STATUS"
                echo "  artifact:        $EXPECTED_QNAP (already present in reference)"
                echo "  no changes made"
                exit 0
            fi
            echo "ERROR: $DELIVERABLE_ID is already $EXISTING_STATUS_CELL; --update-existing rejects terminal-state rows" >&2
            echo "       (existing reference: $EXISTING_REF_CELL)" >&2
            exit 70
            ;;
    esac
fi

# ── Locate phase section (create mode only — update mode already has the row) ─
if [ "$UPDATE_EXISTING" -eq 0 ]; then
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

# ── Compose row (mode-aware) ────────────────────────────────────────────────
TODAY=$(date -u +%Y-%m-%d)

if [ "$UPDATE_EXISTING" -eq 1 ]; then
    # Build the new reference cell from the existing one + qnap pointer + close note.
    NEW_REFERENCE="$EXISTING_REF_CELL"
    # Avoid double-appending qnap:// pointer if it already resolves to this artifact (idempotent partial state).
    if ! printf '%s' "$NEW_REFERENCE" | grep -qF "$QNAP_PTR"; then
        NEW_REFERENCE="${NEW_REFERENCE} Artifact: \`${QNAP_PTR}\`."
    fi
    # Append close-out note (idempotent: skip if same-day note already present).
    CLOSE_NOTE="Closed via --update-existing ${TODAY}"
    if ! printf '%s' "$NEW_REFERENCE" | grep -qF "$CLOSE_NOTE"; then
        NEW_REFERENCE="${NEW_REFERENCE} ${CLOSE_NOTE}."
    fi
    NEW_ROW="| ${EXISTING_TITLE_CELL} | ${STATUS} | ${NEW_REFERENCE} |"
else
    if [ -z "$REFERENCE" ]; then
        REFERENCE="added ${TODAY} via roadmap-create.sh"
    fi
    if [ -n "$QNAP_PTR" ]; then
        REFERENCE="${REFERENCE}. Artifact: \`${QNAP_PTR}\`"
    fi
    NEW_ROW="| ${DELIVERABLE_ID}: ${TITLE} | ${STATUS} | ${REFERENCE} |"
fi

if [ "$DRY_RUN" -eq 1 ]; then
    if [ "$UPDATE_EXISTING" -eq 1 ]; then
        echo "[dry-run] would replace line $EXISTING_ROW_LINE of $FRAMEWORK_MD:"
        echo "[dry-run] OLD: $EXISTING_ROW"
        echo "[dry-run] NEW: $NEW_ROW"
    else
        echo "[dry-run] would insert at line $((LAST_ROW_LINE + 1)) of $FRAMEWORK_MD:"
        echo "[dry-run] $NEW_ROW"
    fi
    if [ "$DO_OP_SYNC" -eq 1 ]; then
        echo "[dry-run] would then run: $OP_SYNC --phase $PHASE_NUM"
    fi
    exit 0
fi

# ── Apply row (mode-aware) ─────────────────────────────────────────────────
TMPFILE=$(mktemp)
if [ "$UPDATE_EXISTING" -eq 1 ]; then
    awk -v target="$EXISTING_ROW_LINE" -v new_row="$NEW_ROW" '
        NR == target { print new_row; next }
        { print }
    ' "$FRAMEWORK_MD" > "$TMPFILE"

    # Sanity: line count must be unchanged in update mode.
    OLD_LINES=$(wc -l < "$FRAMEWORK_MD" | tr -d ' ')
    NEW_LINES=$(wc -l < "$TMPFILE" | tr -d ' ')
    if [ "$NEW_LINES" != "$OLD_LINES" ]; then
        echo "ERROR: row replacement produced unexpected line count ($OLD_LINES → $NEW_LINES); aborting without write" >&2
        rm -f "$TMPFILE"
        exit 67
    fi
else
    awk -v insert_after="$LAST_ROW_LINE" -v new_row="$NEW_ROW" '
        { print }
        NR == insert_after { print new_row }
    ' "$FRAMEWORK_MD" > "$TMPFILE"

    # Sanity: new file must be exactly 1 line longer in create mode.
    OLD_LINES=$(wc -l < "$FRAMEWORK_MD" | tr -d ' ')
    NEW_LINES=$(wc -l < "$TMPFILE" | tr -d ' ')
    if [ "$NEW_LINES" != "$((OLD_LINES + 1))" ]; then
        echo "ERROR: row insertion produced unexpected line count ($OLD_LINES → $NEW_LINES); aborting without write" >&2
        rm -f "$TMPFILE"
        exit 67
    fi
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
if [ "$UPDATE_EXISTING" -eq 1 ]; then
    echo "── roadmap-create.sh: $DELIVERABLE_ID closed-out ─────────────────"
    echo "  framework row:   replaced at $FRAMEWORK_MD line $EXISTING_ROW_LINE"
    echo "  status:          $EXISTING_STATUS_CELL → $STATUS"
else
    echo "── roadmap-create.sh: $DELIVERABLE_ID created ────────────────────"
    echo "  framework row:   inserted at $FRAMEWORK_MD line $((LAST_ROW_LINE + 1))"
    echo "  status:          $STATUS"
fi
if [ -n "$QNAP_PTR" ]; then
    echo "  artifact:        $QNAP_PTR"
fi
if [ "$DO_OP_SYNC" -eq 1 ]; then
    echo "  OpenProject:     $OP_RESULT"
fi
echo "  next:            review with 'git diff --staged' then commit"
