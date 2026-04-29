# Phase 13 Increment 1 — Phase C: Plane label back-fill

**Date:** 2026-04-29
**Status:** Script ready; operator-driven run pending (idempotent — safe to re-run)
**Depends on:** commit `1eed06c` (F1+F2 connector wire-format fix) **landed**.

## Why this Phase C is necessary

Until commit `1eed06c` (Block 4.C C6 follow-up landing in this
increment), `framework/plane_connector.py` had two wire-format bugs:

1. `create_issue` sent `payload["label_ids"]` instead of
   `payload["labels"]`. Plane V1 silently ignored the unknown key.
   Every issue created via `create_issue` (and therefore every
   issue created via `upsert_issue`'s create branch — which is
   how `bin/sync_roadmap_to_plane.py` and the AI requirement
   translator create issues) landed *without labels*.
2. `upsert_issue`'s update branch had the same bug:
   `updates["label_ids"]` instead of `updates["labels"]`. Every
   re-sync of an existing roadmap item silently dropped the
   label update on PATCH.

Block 4.C's C4 back-fill (commit `f5742e1` and
`scripts/backfill-plane-labels.py`) ran a one-shot reconciliation
using the *correct* wire-format key — but only against issues
present at C4 close. Any issue created or re-synced *after*
C4 via the buggy connector path will have either (a) no label
at all, or (b) a stale label from the moment before the most
recent re-sync.

Phase C re-runs the back-fill to reconcile the gap.

## Pre-conditions (verify before run)

- [x] Connector fix landed: `git log --oneline -1 framework/plane_connector.py`
      shows `1eed06c` or later. **Verified:** committed 2026-04-29.
- [x] F8 first-batch verify added to `scripts/backfill-plane-labels.py`.
      **Verified:** committed in this Phase C closeout.
- [ ] Plane reachable from the Mac Mini at `http://localhost:8000`
      (`curl -sf http://localhost:8000/ | grep -q OK`).
- [ ] Vault token at `~/.vault-token` is valid
      (`vault kv get secret/plane/api` succeeds).

## Run procedure (on Mac Mini)

```bash
cd ~/repos/integrated-ai-platform

# 1. Dry-run first — print plan, no PATCHes
/Users/admin/.venv-block-4c/bin/python scripts/backfill-plane-labels.py --dry-run \
    | tee /tmp/c_phase_dry.log

# 2. Read the dry-run log:
#    - check the "apply" count (the actual planned writes)
#    - check the "skip-already-labeled" count (issues C4 already covered)
#    - check the "skip-no-prefix" count (issues that don't match RM-* —
#      these are expected and fine to skip)
#    - check for any "UNMATCHED" prefixes — if new ones appear that
#      don't have an entry in UNMATCHED_MAP, stop and surface

# 3. Apply
/Users/admin/.venv-block-4c/bin/python scripts/backfill-plane-labels.py \
    | tee /tmp/c_phase_apply.log

# 4. Watch for the "VERIFY OK first-batch" line in the apply log.
#    If it says "VERIFY FAIL", the script returns exit 2 and stops —
#    this means the connector fix did not land correctly and Phase C
#    is not safe to continue. Surface immediately.
```

## Stop-and-surface conditions

The script exits non-zero on any of:

- **Exit 2 — first-batch verify failed.** The first PATCH returned
  200, but the re-GET showed labels did not land. This indicates
  the connector wire-format fix is not actually deployed. **Do not
  re-run the script** — first reconcile the connector state and
  Phase C readiness.
- **Exit 1 — at least one item-level failure.** The full apply log
  has every failure line (`FAIL  <issue_id>: <reason>`). If the
  failure rate is >1%, surface to operator before deciding whether
  to re-run.
- **Exit 0 — clean.** Apply log has `applied`, `failed=0`,
  `429 backoffs ≥ 0`. Phase C closes; closeout proceeds to Phase D.

## Idempotency notes

- The script's `skip-already-labeled` branch makes re-running safe.
  Issues that already carry the target label are not re-PATCHed.
- The first-batch verify happens ON THE FIRST SUCCESSFUL APPLY of
  the run, regardless of whether previous runs verified — this
  re-checks the wire format every run, costing one extra GET per
  invocation (~1s wall time).
- The pacing (1 req/sec) and 65s 429 backoff make the script safe
  to run alongside other Plane operations; just watch for 429
  bursts in the log.

## Expected scope

The connector bug landed when the connector was first written
(pre-Block-4.C). Post-C4, any roadmap-sync run or AI-translator
invocation that touched an issue could have left it with stale or
missing labels. Practical estimate: **dozens to low hundreds**
of issues need re-labeling. The dry-run will give the exact count;
no need to estimate ahead of it.

If the dry-run shows >300 planned applies, surface the volume to
operator before the live run — it suggests a longer-tail problem
(e.g., issues created via a path the audit didn't catch, or a
prior back-fill regression) that is worth investigating before
applying.

## Closeout artifact

After the live run completes, the `/tmp/c_phase_apply.log` should
be archived (or its summary captured) into the Increment 1
closeout document (Phase D), with:

- Total applied count
- Total failed count (with failure breakdown if >0)
- 429 backoff count
- Wall time
- VERIFY OK confirmation line

This forms the load-bearing evidence that the connector fix is
actually working end-to-end, not just at unit-test time.
