# Runbook — OpenProject sync + enrich pipeline

Operate the two-script OpenProject pipeline that maintains
OpenProject as an enriched projection of `PROJECT_FRAMEWORK.md` §9
(framework deliverables) and `PHASE_ROADMAP.md` (roadmap scope items):
sync creates/updates work packages from markdown source, then enrich
adds managed metadata fields without overwriting manual operator
edits.

## The two-script pipeline

### What sync does

`scripts/openproject-sync-from-framework.py` is a one-way sync from
the canonical markdown into OpenProject. From the script docstring
(lines 2–9):

```
D-17-04 WP-17-04-04 — one-way sync from PROJECT_FRAMEWORK.md to OpenProject.

Replaces scripts/plane-sync-from-framework.py (D-16-02.A doctrine
preserved: repo-owned docs are canonical; OpenProject is an operational
overlay). Manual edits made in the OpenProject UI to synced work
packages will be overwritten on the next run; that is intentional. The
OpenProject UI is the right place to attach comments, sub-WPs, and
operational links — not to redefine deliverable scope or status.
```

What sync materializes (lines 11–18):

```
What it syncs (1:1 with the Plane sync, structurally):
  - One OpenProject *version* per phase, keyed by name `Phase-NN`.
  - One OpenProject *work package* per phase, keyed by external_id
    (custom field "External ID") `Phase-NN`, summarising the phase
    header.
  - One OpenProject *work package* per deliverable, keyed by external_id
    (e.g. `D-16-02`, `D-16-02.A`, `D-15-08`, `17.A`), associated with
    the phase version.
```

### What enrich does

`scripts/openproject-enrich-from-framework.py` adds managed
metadata fields to existing D-* work packages. From the docstring
(lines 4–25):

```
Read model:
- docs/PROJECT_FRAMEWORK.md deliverable rows are canonical.
- Optional closeout/results docs augment description.

Write model:
- Enriches existing D-* work packages only (matched by External ID custom field).
- Idempotent delta patching.
- Preserves manual edits by default: non-empty conflicting target fields are skipped.
- --force overrides manual-edit protection for managed fields.

Managed fields:
- description
- percentageDone
- customField<phase>
- customField<deliverable_class>
- customField<finding_refs>
- customField<dependencies>

Never managed:
- dueDate
- customField1 (Plane RM ID)
- customField2 (External ID)
```

### Pipeline coupling

The sync script runs enrichment as a follow-on pass at the end
unless `--skip-enrich` is passed. From the sync script `main()`
(lines 889–904):

```python
# D-17-55 enrichment follow-on pass.
if not args.skip_enrich:
    if not ENRICH_SCRIPT.is_file():
        print(f"WARN: enrichment script missing at {ENRICH_SCRIPT}; skipping enrichment")
    else:
        cmd = [str(ENRICH_SCRIPT)]
        if args.dry_run:
            cmd.append("--dry-run")
        print("\nRunning enrichment pass:", " ".join(cmd))
        erc = subprocess.call(cmd)
        # preserve dry-run semantics if enrichment has pending changes.
        if args.dry_run and erc == 2:
            rc = 2
        elif erc != 0:
            print(f"ERROR: enrichment pass failed (exit {erc})", file=sys.stderr)
            return erc
return rc
```

Dry-run semantics propagate: if either sync or enrich has pending
changes in dry-run mode, the combined exit code is 2.

## Common operations

### Routine sync (framework only, with enrichment)

```bash
python3 scripts/openproject-sync-from-framework.py
```

Applies sync + enrich. Framework deliverables (D-NN-MM) are synced
from `PROJECT_FRAMEWORK.md` §9; enrichment adds metadata.

### Dry-run (plan only)

```bash
python3 scripts/openproject-sync-from-framework.py --dry-run
```

Prints planned creates / updates / no-ops. From the sync script
docstring (lines 31–34):

```
Modes:
  --dry-run   Plan only; print planned creates / updates / no-ops.
              Exits 0 if no changes pending, 2 if changes pending.
              D-16-06's CI hook uses this exit-code contract for drift.
```

### Single-phase limit

Argparse definition (line 773):

```python
ap.add_argument("--phase", type=int, default=None, help="Limit to a single phase")
```

```bash
python3 scripts/openproject-sync-from-framework.py --dry-run --phase 17
```

Restricts sync to a single phase number.

### Include roadmap scope items

Argparse definition (lines 774–775):

```python
ap.add_argument("--include-roadmap", action="store_true",
                help="Also sync PHASE_ROADMAP.md scope items (Phase 16/18 sub-blocks). D-17-31.")
```

```bash
python3 scripts/openproject-sync-from-framework.py --include-roadmap
```

Syncs framework deliverables AND roadmap scope items (RM-*) in one
run.

### Roadmap-only mode

Argparse definition (lines 776–777):

```python
ap.add_argument("--roadmap-only", action="store_true",
                help="Skip framework sync; only sync roadmap. Useful for fast iteration.")
```

```bash
python3 scripts/openproject-sync-from-framework.py --roadmap-only
```

Skips framework sync; only PHASE_ROADMAP.md scope items are
processed.

### Skip enrichment

Argparse definition (lines 780–781):

```python
ap.add_argument("--skip-enrich", action="store_true",
                help="Skip D-17-55 enrichment pass after base sync.")
```

```bash
python3 scripts/openproject-sync-from-framework.py --skip-enrich
```

Runs sync only; suppresses the follow-on enrichment pass.

### One-shot Phase-17 dedup

Argparse definition (lines 778–779):

```python
ap.add_argument("--dedup-phase17", action="store_true",
                help="One-shot: close 17.A–17.T shorthand WPs as superseded by D-17-NN canonical IDs.")
```

```bash
python3 scripts/openproject-sync-from-framework.py --dedup-phase17
```

One-time operation: closes the legacy `17.A`–`17.T` shorthand WPs as
superseded by their `D-17-NN` canonical equivalents. Already executed
2026-05-03; idempotent on re-run.

### Force-overwrite manual edits during enrichment

```bash
python3 scripts/openproject-enrich-from-framework.py --force
```

Overrides the manual-edit safety. From the enrich script
(lines 382–386):

```python
# Preserve manual edits by default if field is non-empty and differs.
if not args.force and not is_empty_value(have):
    local_conflicts.append(k)
    continue
delta[k] = want
```

Without `--force`, non-empty conflicting managed fields are skipped
(preserved as the operator left them).

## Drift handling

### Framework deliverables (D-NN-MM)

Status is **sync-managed**. Operator edits to a D-* work package's
subject (title), status, or description in the OpenProject UI are
overwritten on the next sync run. To change a deliverable's title or
status, edit `PROJECT_FRAMEWORK.md` §9 and re-run sync.

### Roadmap scope items (RM-*)

Status is **operator-owned**. The sync script creates and refreshes
title/description but never overwrites status drift. From the sync
script update path for roadmap items (lines 656–665):

```python
# Update path: only diff name + description. Status drift is
# operator-owned (they may have moved an item from Backlog to
# In Progress); we don't overwrite it.
drift: dict = {}
if (live.get("name") or "") != want_name:
    drift["name"] = want_name
want_md = _html_to_markdown(want_desc)
have_md = live.get("description_raw") or ""
if _normalise_md(have_md) != _normalise_md(want_md):
    drift["description_html"] = want_desc
```

### Enrichment manual-edit safety

Enrichment preserves manual edits by default; `--force` is the
explicit override. The same logic applies field-by-field: each
managed field is independently checked for conflict.

## Status mapping

Markdown status words map to OpenProject status names (sync script
lines 99–104):

```python
STATUS_TO_OP_STATE = {
    "DONE":        "Done",
    "IN PROGRESS": "In Progress",
    "NOT STARTED": "Backlog",
    "DEFERRED":    "On hold",
}
```

## Authentication

Token is pulled from Vault `secret/openproject/api#token` via the
running `vault-server` container. From the sync script `fetch_token()`
docstring (lines 203–210):

```python
def fetch_token() -> str:
    """Pull the OpenProject iap-sync token from Vault via the running
    vault-server container. Avoids putting the value on argv."""
```

Both scripts use HTTP Basic auth with the token encoded as
`apikey:{token}` in base64. From the enrich script `op_request()`
(lines 135–142):

```python
def op_request(method: str, path: str, token: str, *, params: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> Any:
    url = f"{OPENPROJECT_URL}/api/v3{path}"
    if params:
        url += "?" + urlencode(params)
    req = Request(url, method=method)
    basic = base64.b64encode(f"apikey:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {basic}")
```

The token value is never displayed in script output or argv.

## Exit codes

**Sync exit codes** (from the docstring lines 31–34 and `main()`
return logic):

- `0` — apply succeeded, or dry-run with no changes pending
- `2` — dry-run with changes pending (CI drift detector treats this
  as drift)

**Enrichment exit codes** (line 415):

```python
return 2 if args.dry_run and patches > 0 else 0
```

- `0` — apply succeeded, or dry-run with no patches needed
- `2` — dry-run with patches pending

**Combined semantics:** the sync script preserves the dry-run exit
code if enrichment returns 2 (lines 900–901):

```python
if args.dry_run and erc == 2:
    rc = 2
```

A clean dry-run requires both passes to return 0.

## Cross-references

- [OpenProject Enrichment Doctrine — CLAUDE.md](../../CLAUDE.md)
  (D-17-55 doctrine block: managed fields, `--force` semantics,
  customField1/2 preservation as mapping/sync keys).
- [openproject-sync.md](openproject-sync.md) — sibling runbook for
  sync-only operations, prerequisites, troubleshooting (151 lines).
- [PROJECT_FRAMEWORK.md §9](../PROJECT_FRAMEWORK.md) — canonical
  framework deliverable table.
- [PHASE_ROADMAP.md](../PHASE_ROADMAP.md) — canonical roadmap scope
  items.
- [ADR-A-006](../adr/ADR-A-006.md) — architectural decision record
  for the canonical-markdown / operational-overlay split.
