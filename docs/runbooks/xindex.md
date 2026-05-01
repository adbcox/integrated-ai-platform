# xindex — Cross-Index Service Runbook

**Status:** Live (D-16-02, opened 2026-05-01)
**Service location:** `docker/xindex/`
**Endpoint:** `http://127.0.0.1:8095` (loopback only; no Caddy / .internal yet)
**Container port:** 8000
**Image:** `iap/xindex:0.1.0`
**Network:** `control-center-net`
**Ingestion sources (D-16-02 scope):** repo files only — `docs/adr/`,
`docs/DECISION_REGISTER.md`, `docs/runbooks/`. NetBox / Plane / MCP wrapper
follow in D-16-02.1 / .2 / .3.

## 1. Purpose

xindex is the structural enabler for autonomous coding. It serves as the
queryable view over the repo's authoritative documentation surface (ADRs,
the decision register, runbooks) so an automated coding loop can answer
"what does the platform say about X?" without re-walking markdown by hand.

The existing `scripts/cross-index-validate.py` (ADR↔Plane probe) is a
different scope and is not replaced by this service.

## 2. Architecture

```
docs/  ──read-only mount──▶  xindex container  ──FTS5──▶  /data/xindex.db
                                  │
                                  └──FastAPI (uvicorn) on :8000
                                       ▲
                                       │  127.0.0.1:8095
                                  operator / MCP client
```

- Database: SQLite + FTS5 (porter unicode61 tokenizer)
- Persistence: named Docker volume `xindex_data`
- Ingest: full rebuild on startup if DB is empty; explicit `POST /refresh`
  thereafter. The schema + content are small enough that partial upserts
  are not worth the complexity.

## 3. Endpoints

```bash
# liveness + counts + last_ingest_at
curl -s http://127.0.0.1:8095/healthz | jq

# Full ADR detail (accepts both A-014 and ADR-A-014 forms)
curl -s http://127.0.0.1:8095/adr/A-014 | jq
curl -s http://127.0.0.1:8095/adr/ADR-A-014 | jq

# Runbook detail (filename without .md)
curl -s http://127.0.0.1:8095/runbook/vault-recovery-from-shamir | jq

# Search (FTS5 ranked); type ∈ {all, adr, runbook, register}
curl -s "http://127.0.0.1:8095/search?q=NetBox&type=adr&limit=5" | jq

# Trigger background re-ingest. Poll /healthz to see updated last_ingest_at.
curl -s -X POST http://127.0.0.1:8095/refresh | jq
```

## 4. Refresh cadence

There is no scheduled refresh in this deliverable. Re-ingest happens:
- on container start when the DB is empty,
- on explicit `POST /refresh`.

Adding a periodic refresh (e.g. cron sidecar, or filesystem watcher) is a
follow-up if the manual cadence proves operationally insufficient.

## 5. Common queries

```bash
# What does ADR-A-014 actually decide?
curl -s http://127.0.0.1:8095/adr/A-014 | jq -r '.sections.Decision'

# Which runbook covers Shamir recovery?
curl -s "http://127.0.0.1:8095/search?q=shamir&type=runbook" | jq

# Which ADRs touch the vault?
curl -s "http://127.0.0.1:8095/search?q=vault&type=adr" | jq '.results[].ref'
```

## 6. Adding a new source ingester

Pattern (mirrors `app/ingest/runbook.py`):

1. Add a module under `docker/xindex/app/ingest/<source>.py` that exposes
   `ingest(conn, root) -> int`. It is responsible for upserting into a
   content table and inserting the searchable text into `xindex_fts`.
2. If the source is non-tabular, add a content table to `app/db.py`'s
   `SCHEMA` constant. Keep the schema additive; don't touch existing tables.
3. Wire the new ingester into `app/ingest/__init__.py:ingest_all`.
4. Extend `app/db.py:counts` and the `/healthz` response so operators can
   see the new source populated.
5. Add a fixture and a `test_ingest_<source>.py` mirroring the existing
   tests.

External-source ingesters (NetBox, Plane, Vault, InvenTree) follow this
shape, but additionally need credentials via Vault Agent sidecars and a
`control-center-net` neighbour — covered in D-16-02.1/.2/.3.

## 7. Debugging ingest failures

```bash
# container logs (uvicorn prints stack traces from the lifespan ingest)
docker logs xindex --tail 100

# inspect the live DB inline
docker exec -it xindex sh -lc 'python -c "
import sqlite3, json
c = sqlite3.connect(\"/data/xindex.db\")
c.row_factory = sqlite3.Row
print(\"adrs:\",  c.execute(\"SELECT COUNT(*) FROM adrs\").fetchone()[0])
print(\"runbooks:\", c.execute(\"SELECT COUNT(*) FROM runbooks\").fetchone()[0])
print(\"meta:\", dict(c.execute(\"SELECT key,value FROM meta\").fetchall()))
"'

# force a clean rebuild
curl -s -X POST http://127.0.0.1:8095/refresh
sleep 2
curl -s http://127.0.0.1:8095/healthz | jq '.last_ingest_at, .counts'
```

If the ADR ingester reports a count lower than the number of files, the
likeliest cause is a header-format outlier — both the bolded-field and
the section-style ("## Status") forms are supported, anything else needs
parser extension.

## 8. Recovery

The DB is rebuildable from the repo. To recover from corruption:

```bash
docker compose -f docker/xindex/docker-compose.yml down
docker volume rm xindex_data
docker compose -f docker/xindex/docker-compose.yml up -d
# lifespan ingest runs automatically on first request to /healthz
```

Backups are not required: source of truth is git.

## 9. Tests

```bash
cd docker/xindex
python3.12 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
.venv/bin/python -m pytest app/tests/ -v
```

11 tests cover ADR parsing (both header styles), runbook ingest, and the
five HTTP endpoints. The tests build a synthetic `/docs` tree and never
touch the real repo content.

## 10. Why repo-files-only in this deliverable

D-16-02 ships the foundation. The autonomous-coding meta-goal needs the
*structural* piece — a queryable index that exists, persists, and serves
JSON — before extending it to remote sources. Each external source needs
its own credential plumbing and rate-limit story; bundling them into the
foundation deliverable would force four un-hardened paths into the same
review. They are deferred to:

- **D-16-02.1** — NetBox ingestion (services, devices, IPs)
- **D-16-02.2** — Plane ingestion (issues, projects)
- **D-16-02.3** — MCP tool wrapper so Claude Code agents can query xindex

A small pre-step **D-16-02.0.5** adds Caddy + `xindex.internal` so the
service is reachable from non-loopback consumers.
