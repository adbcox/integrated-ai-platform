"""SQLite schema + FTS5 for xindex.

One DB file, several content tables, one FTS5 virtual table that
mirrors their searchable bodies. Repo-local sources (adrs, runbooks,
decision register) are wiped and rebuilt on every refresh; external
sources (NetBox, future Plane) refresh per-source via reset_source()
so a failure in one external source never wipes another's data.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


DEFAULT_DB_PATH = os.environ.get("XINDEX_DB", "/data/xindex.db")


# Sources that refresh independently. Repo-local sources rebuild
# atomically; external sources are isolated so partial failures don't
# wipe healthy data.
LOCAL_SOURCES = ("adr", "runbook", "register")
EXTERNAL_SOURCES = ("netbox", "plane")
ALL_SOURCES = LOCAL_SOURCES + EXTERNAL_SOURCES


SCHEMA = """
CREATE TABLE IF NOT EXISTS adrs (
    id              TEXT PRIMARY KEY,        -- ADR-A-NNN
    short_id        TEXT NOT NULL,           -- A-NNN
    title           TEXT NOT NULL,
    status          TEXT,
    date            TEXT,
    phase           TEXT,
    source          TEXT,
    path            TEXT NOT NULL,
    body            TEXT NOT NULL,
    sections_json   TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS runbooks (
    name    TEXT PRIMARY KEY,    -- filename without .md
    title   TEXT NOT NULL,
    path    TEXT NOT NULL,
    body    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_register_entries (
    short_id    TEXT PRIMARY KEY,    -- A-NNN
    adr_id      TEXT,                -- ADR-A-NNN (denormalized for join)
    category    TEXT NOT NULL,       -- the H2 the row falls under
    title       TEXT NOT NULL,
    summary     TEXT NOT NULL,
    link_path   TEXT
);

CREATE TABLE IF NOT EXISTS services (
    name            TEXT PRIMARY KEY,    -- ipam.service.name (canonical)
    netbox_id       INTEGER,             -- ipam.service primary key
    protocol        TEXT,                -- tcp/udp/sctp
    ports_json      TEXT NOT NULL DEFAULT '[]',
    parent_kind     TEXT,                -- 'device' | 'virtual_machine' | NULL
    parent_ref      TEXT,                -- device.name or vm.name
    description     TEXT NOT NULL DEFAULT '',
    custom_json     TEXT NOT NULL DEFAULT '{}',
    source          TEXT NOT NULL DEFAULT 'netbox'
);

CREATE TABLE IF NOT EXISTS nodes (
    name            TEXT PRIMARY KEY,    -- dcim.device.name (canonical)
    netbox_id       INTEGER,
    role            TEXT,                -- device_role.name
    site            TEXT,                -- site.name
    status          TEXT,                -- active/planned/...
    primary_ip      TEXT,                -- primary_ip.address (with CIDR)
    description     TEXT NOT NULL DEFAULT '',
    custom_json     TEXT NOT NULL DEFAULT '{}',
    source          TEXT NOT NULL DEFAULT 'netbox'
);

-- Plane (D-16-02.2). Read-only mirror per ADR-A-006: xindex never
-- writes to Plane. external_id is the human-stable key set by
-- plane-sync (e.g. 'D-16-02.2', 'ADR-A-006'); state_name and
-- module_name are denormalized so the UI can avoid an extra hop.
CREATE TABLE IF NOT EXISTS plane_issues (
    external_id     TEXT PRIMARY KEY,        -- 'D-NN-MM' / 'ADR-A-NNN' / ...
    plane_id        TEXT NOT NULL,           -- Plane issue UUID
    name            TEXT NOT NULL,
    state_name      TEXT,                    -- resolved from state UUID
    module_name     TEXT,                    -- first module's name (if any)
    project_id      TEXT,
    description     TEXT NOT NULL DEFAULT '',
    updated_at      TEXT,
    source          TEXT NOT NULL DEFAULT 'plane'
);

CREATE TABLE IF NOT EXISTS plane_modules (
    name            TEXT PRIMARY KEY,        -- module.name
    plane_id        TEXT NOT NULL,           -- module UUID
    external_id     TEXT,                    -- e.g. 'Phase-16'
    description     TEXT NOT NULL DEFAULT '',
    source          TEXT NOT NULL DEFAULT 'plane'
);

-- Entity links: M:N junction. Untyped enough to carry future ADR
-- linkages, runbook references, etc., without schema churn.
CREATE TABLE IF NOT EXISTS entity_links (
    from_kind   TEXT NOT NULL,   -- 'service' | 'node' | 'adr' | ...
    from_ref    TEXT NOT NULL,
    to_kind     TEXT NOT NULL,
    to_ref      TEXT NOT NULL,
    link_type   TEXT NOT NULL,   -- 'depends_on' | 'hosted_on' | 'governs' | ...
    source      TEXT NOT NULL,   -- which ingester wrote the link
    PRIMARY KEY (from_kind, from_ref, to_kind, to_ref, link_type, source)
);

CREATE INDEX IF NOT EXISTS idx_links_from ON entity_links(from_kind, from_ref);
CREATE INDEX IF NOT EXISTS idx_links_to   ON entity_links(to_kind, to_ref);
CREATE INDEX IF NOT EXISTS idx_links_src  ON entity_links(source);

CREATE TABLE IF NOT EXISTS meta (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS xindex_fts USING fts5(
    kind,            -- 'adr' | 'runbook' | 'register' | 'service' | 'node' | 'plane_issue'
    ref,             -- pk in source table
    title,
    body,
    tokenize = 'porter unicode61'
);
"""


@contextmanager
def connect(db_path: str = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def reset_for_ingest(conn: sqlite3.Connection) -> None:
    """Wipe LOCAL content tables and their FTS rows.

    Repo-local sources (ADRs, runbooks, register) are small and
    rebuild fast; full wipe avoids drift between FTS and content.
    External-source rows (services, nodes, their entity_links) are
    intentionally preserved here — those are reset per-source via
    reset_source() so a NetBox outage doesn't drop the local index.
    """
    init_schema(conn)
    conn.execute("DELETE FROM adrs;")
    conn.execute("DELETE FROM runbooks;")
    conn.execute("DELETE FROM decision_register_entries;")
    conn.execute(
        "DELETE FROM xindex_fts WHERE kind IN ('adr','runbook','register');"
    )


def reset_source(conn: sqlite3.Connection, source: str) -> None:
    """Wipe one external source's rows + its FTS rows + its links.

    Called by an external ingester at the start of its run, inside a
    transaction. If the ingester fails mid-run the surrounding
    rollback discards the wipe, leaving the prior data intact (and
    flagged stale by the caller via meta).
    """
    init_schema(conn)
    if source == "netbox":
        conn.execute("DELETE FROM services WHERE source=?", (source,))
        conn.execute("DELETE FROM nodes WHERE source=?", (source,))
        conn.execute(
            "DELETE FROM xindex_fts WHERE kind IN ('service','node');"
        )
    elif source == "plane":
        conn.execute("DELETE FROM plane_issues WHERE source=?", (source,))
        conn.execute("DELETE FROM plane_modules WHERE source=?", (source,))
        conn.execute(
            "DELETE FROM xindex_fts WHERE kind = 'plane_issue';"
        )
    conn.execute("DELETE FROM entity_links WHERE source=?", (source,))


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_source_status(
    conn: sqlite3.Connection,
    source: str,
    status: str,
    error: str | None = None,
    timestamp: str | None = None,
) -> None:
    """Record the outcome of one source's ingest run.

    Three meta keys per source: last_ingest_at, last_ingest_status
    ('ok' | 'error' | 'stale'), last_ingest_error (string or empty).
    Stale rows survive on error; healthz reports them as degraded.
    """
    if timestamp is not None:
        set_meta(conn, f"last_ingest_at:{source}", timestamp)
    set_meta(conn, f"last_ingest_status:{source}", status)
    set_meta(conn, f"last_ingest_error:{source}", error or "")


def get_source_status(conn: sqlite3.Connection, source: str) -> dict[str, str]:
    return {
        "source": source,
        "last_ingest_at": get_meta(conn, f"last_ingest_at:{source}") or "",
        "status": get_meta(conn, f"last_ingest_status:{source}") or "unknown",
        "error": get_meta(conn, f"last_ingest_error:{source}") or "",
    }


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    out = {}
    for table in (
        "adrs",
        "runbooks",
        "decision_register_entries",
        "services",
        "nodes",
        "entity_links",
        "plane_issues",
        "plane_modules",
    ):
        row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        out[table] = int(row["n"])
    return out
