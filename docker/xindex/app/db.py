"""SQLite schema + FTS5 for xindex.

One DB file, three content tables, one FTS5 virtual table that mirrors
their searchable bodies. Schema is small enough that we recreate from
clean on every full ingest — content is repo-local and rebuilds in
under a second.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


DEFAULT_DB_PATH = os.environ.get("XINDEX_DB", "/data/xindex.db")


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

CREATE TABLE IF NOT EXISTS meta (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS xindex_fts USING fts5(
    kind,            -- 'adr' | 'runbook' | 'register'
    ref,             -- pk in source table (id / name / short_id)
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
    """Wipe content tables and FTS so a re-ingest produces a clean state.

    The schema is small and the operation is fast; full rebuild avoids
    drift between the FTS index and the content tables that a partial
    upsert path would have to police.
    """
    init_schema(conn)
    conn.execute("DELETE FROM adrs;")
    conn.execute("DELETE FROM runbooks;")
    conn.execute("DELETE FROM decision_register_entries;")
    conn.execute("DELETE FROM xindex_fts;")


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    out = {}
    for table in ("adrs", "runbooks", "decision_register_entries"):
        row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        out[table] = int(row["n"])
    return out
