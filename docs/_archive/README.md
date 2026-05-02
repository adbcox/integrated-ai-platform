# `docs/_archive/` — forensic / migration artifacts

Files here are migration inputs and forensic snapshots taken at substrate
boundaries. They are read-only history; do not edit in place.

## What's stored in-repo

| File | Purpose | Sensitivity |
|------|---------|-------------|
| `plane-export-YYYY-MM-DD.json` | Structured Plane API export (states, labels, modules, cycles, issues). Primary input to WP-17-04-03 mapping. | Public — issue text only, no credentials. |
| `plane-final-snapshot-YYYY-MM-DD.manifest` | SHA256 + row counts + reconciliation notes for the corresponding SQL dump. | Public. |

## What's stored OUT of repo

Full DB dumps contain password hashes (`pbkdf2_sha256$…`) and live API
tokens (`api_tokens.token`). Per platform doctrine ("credential values
in tool output, commit messages, or transcripts" forbidden), they are
NOT committed.

| Path | Source | Purpose |
|------|--------|---------|
| `~/plane-final-snapshot/plane-final-snapshot-2026-05-02.sql.gz` | `scripts/plane-final-snapshot.sh` (D-17-04 WP-17-04-02) | Forensic-grade pg_dump of the Plane DB at substrate-replacement time. Hash recorded in the in-repo `.manifest` for tamper-evidence. |

To verify integrity:

```bash
shasum -a 256 ~/plane-final-snapshot/plane-final-snapshot-2026-05-02.sql.gz
# compare against sql_sha256 in plane-final-snapshot-2026-05-02.manifest
```

## Lifecycle

These artifacts are kept until the migration they support is fully
verified and the source system is retired. After WP-17-04-06 (Plane
retirement) is closed and OpenProject has been running clean for one
operational cycle, the SQL dump may be moved to long-term cold storage
on QNAP via the existing Restic backup chain.
