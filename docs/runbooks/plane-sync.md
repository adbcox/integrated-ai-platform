# Plane sync from PROJECT_FRAMEWORK.md — Runbook

**Status:** Live (D-16-02.A, opened 2026-05-01)
**Script:** `scripts/plane-sync-from-framework.py`
**Source of truth:** `docs/PROJECT_FRAMEWORK.md` §7 (Phase 15) + §8 (Phase 16)
**Plane project:** `iap` workspace, project id `dbcd4476-1e37-4812-a443-0914ec8380fc`
**Token:** `secret/plane/api#homepage_token` (Vault), pulled via `vault-server` container
**Doctrine:** ADR-A-006 — repo-owned docs are canonical; Plane is an
operational overlay. Sync is one-way (repo → Plane); Plane edits to
synced fields are overwritten on the next run.

## 1. Purpose

Bootstrap and maintain a Plane mirror of the Phase / Deliverable table
in PROJECT_FRAMEWORK.md so operators viewing Plane see the same set of
deliverables, in the same states, as the canonical markdown. The sync
is a one-way write from repo to Plane.

The sync is the foundation for D-16-06 (drift detection): the
`--dry-run` mode exits 2 when changes are pending, which a CI hook can
use to fail loudly when the markdown table and the Plane state
disagree.

ADR stubs (any Plane issue whose `external_id` starts with `ADR-`) are
**not touched** by this sync. Those are owned by
`scripts/cross-index-validate.py`. The two scripts share a Plane
project but operate on disjoint key-spaces.

## 2. What gets created

For each phase parsed out of the markdown:

| Plane object       | external_id key     | Name shape                              |
|--------------------|---------------------|------------------------------------------|
| Module             | `Phase-NN`          | `Phase-NN`                               |
| Phase summary issue | `Phase-NN`         | `[Phase-NN] <header line>`               |
| Deliverable issue  | `D-NN-MM[.suffix]`  | `[D-NN-MM[.suffix]] <title from row>`    |

Status mapping (markdown → Plane state):

| PROJECT_FRAMEWORK.md status | Plane state  |
|------------------------------|--------------|
| `DONE`                       | Done         |
| `IN PROGRESS`                | In Progress  |
| `NOT STARTED`                | Backlog      |
| `DEFERRED [...]`             | Cancelled    |

Phase summary state:
- header contains `CLOSED` → state `Done`
- otherwise → state `In Progress`

## 3. Invocation

Token comes from Vault via the `vault-server` container — the script
never displays the value and never accepts it on argv.

```bash
# Dry-run — plan only. Exit 0 on clean, 2 if changes pending.
# This is what D-16-06's CI hook will call.
/Users/admin/.venv-block-4c/bin/python scripts/plane-sync-from-framework.py --dry-run

# Apply.
/Users/admin/.venv-block-4c/bin/python scripts/plane-sync-from-framework.py

# Limit to a single phase (debug aid; same exit-code contract).
/Users/admin/.venv-block-4c/bin/python scripts/plane-sync-from-framework.py --dry-run --phase 16
```

## 4. Idempotency contract

- Modules and issues are matched by `external_id` only. A run that
  finds the right `external_id` will never create a duplicate.
- The script computes a minimal diff per row — `name`, `state`,
  `description_html` — and PATCHes only when something actually
  drifts. `description_html` is compared after stripping the Plane
  `<div>...</div>` envelope so the round-trip matches the input.
- Module → issue association is **additive only**. A deliverable that
  used to belong to a phase but no longer appears in the markdown
  stays linked in Plane until manually unlinked. The next dry-run
  surfaces the orphan as a row with no markdown counterpart (visible
  in Plane but not in the script's plan).
- Two consecutive applies with no markdown change produce 0 PATCHes.

## 5. Rate-limit handling

Plane CE uses a 60 req/min limiter. The script paces at 1 req/sec
(matches `scripts/backfill-plane-labels.py`) and on a 429 sleeps for
65 s and then continues. A row that hits 429 mid-create may need a
second run to land — the second run picks it up via a `+ create`
plan row.

If a module-issues fetch hits 429 even after the cooldown, the
script logs `RATE-LIMIT again — skipping module association` for
that phase and the next run picks up the missing links.

## 6. Operator workflows

### Status change for a deliverable

1. Edit the row in `docs/PROJECT_FRAMEWORK.md` §7 / §8.
2. Commit.
3. Run `scripts/plane-sync-from-framework.py` (or wait for CI).
4. Confirm the Plane state changed via the dry-run plan or the UI.

Do **not** change state in the Plane UI as the canonical action — it
will be overwritten on the next sync.

### Adding a new deliverable

1. Add a new row under the appropriate phase table.
2. Run the sync. The new row appears as a `+ deliverable-issue`
   plan entry.
3. Verify by re-running `--dry-run` and seeing `Summary: ... no-op=N`
   with N = total rows.

### Closing a phase

1. Update the phase header in the markdown (e.g. add `— CLOSED 2026-MM-DD`).
2. Re-run the sync. The phase summary issue moves to `Done`.
3. Deliverables with status `DONE` already track to Plane `Done`; no
   per-row edit needed unless a status word changed.

### Plane UI / sync conflict

If an operator edits a synced field in Plane and a sync run later
overwrites it, that is **expected**. The sync is the authority. If a
particular field needs to live in Plane only (e.g. assignee,
due-date, comments), it must be a field the script does not write —
the current write-set is `{name, state, description_html}` plus the
module link.

## 7. Failure modes

| Symptom                                         | Likely cause                                | Fix                                              |
|--------------------------------------------------|---------------------------------------------|--------------------------------------------------|
| `ERROR: could not read Plane API token`         | `~/.vault-token` is stale and the post-rebuild keys file is missing | Re-establish a Vault session (`vault login` or read `~/vault-init-keys-NEW-20260430.txt`) |
| `ERROR: Plane health-check failed`              | Plane stack down                             | `docker ps | grep plane` and restart per `docs/runbooks/restart-services.md` |
| Repeated `update` plan rows for the same field every run | Plane normalised the value differently from input | Tighten `_normalise_html` (or equivalent) in the script |
| Issue created without `external_id`             | Plane V1 ignored `external_id` on POST      | The script PATCHes `external_id` after create; if that PATCH 429'd the second run will repair on its own (matches by name search via `get_issue_by_external_id`, then back-fills) |
| `--dry-run` exits 2 with no plan changes        | Module-only or association-only diff that the summary doesn't count | Inspect the plan for `+ module` or association rows |

## 8. Why one-way

The decision is anchored in ADR-A-006: bidirectional sync is a known
class of inconsistency-generator. Plane has richer per-issue state
than the markdown does (assignees, comments, sub-tasks, modules); the
markdown owns one slim slice — name, status, reference — and that
slice is canonical. Two-way sync would require resolving conflicts
on every round-trip, and the operator-meta-goal (autonomous coding)
needs a single source of truth that automated tooling can write to
without permission negotiation. The repo wins.

## 9. Tests / validation

There are no pytest fixtures for this script — the parser is small
enough that the canonical validation is the live `--dry-run` against
Plane. The `--dry-run` clean state (`Summary: ... no-op=N` with N =
total rows) is the green-light signal.

## 10. Related

- ADR-A-006 — sync direction doctrine
- `scripts/cross-index-validate.py` — ADR↔Plane probe (different
  scope; reads only)
- `framework/plane_connector.py` — Plane CE V1 client used by all
  Plane-touching scripts
- `docs/runbooks/xindex.md` — cross-index service runbook (no
  overlap; mentioned for navigation)
