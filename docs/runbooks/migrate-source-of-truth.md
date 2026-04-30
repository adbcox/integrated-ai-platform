# Runbook — Migrate a Source of Truth

**Pattern:** Staged-toggle (ADR-A-015)
**Doctrine:** ADR-A-012 (equivalence harness must run at migration time)

## Step 1 — Build the unified loader

Write a single loader module that reads from either the old or new source
based on `CMDB_SOURCE` env var. Both paths must produce identical output
schemas. Example: `scripts/cmdb_source.py`.

## Step 2 — Populate the new source

Migrate data to the new source. Do not write to the old source after this
point.

## Step 3 — Run equivalence harness

```bash
# With both sources populated, prove byte-identical output
python3 scripts/cmdb_source.py --source yaml  > /tmp/old.json
python3 scripts/cmdb_source.py --source netbox > /tmp/new.json
diff /tmp/old.json /tmp/new.json
# Expected: empty diff (byte-identical)
```

Document the diff output in the migration closeout doc (even if empty).
A non-empty diff is a HARD STOP — investigate and resolve before
flipping the default.

## Step 4 — Flip the default

Change the default value of `CMDB_SOURCE` in the loader from old to new.
Add a `CMDB_SOURCE=old` env var to any service that needs rollback access.

## Step 5 — Stability window

Run for ≥1 week under the new default. Monitor for:
- Services that can't read from the new source (check container logs)
- API errors from new-source-specific endpoints

## Step 6 — Deprecation gate

Re-run equivalence harness. Verify output is still identical. Then remove
the old-source code path (or freeze it as read-only).
