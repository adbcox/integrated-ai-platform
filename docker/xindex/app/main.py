"""xindex FastAPI app (D-16-02).

Endpoints:
    GET  /healthz                          — liveness + last_ingest_at + counts
    GET  /adr/{id}                         — full ADR detail (id or short id)
    GET  /runbook/{topic}                  — full runbook detail
    GET  /search?q=&type=&limit=           — FTS5 search across all sources
    POST /refresh                          — re-ingest in the background
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query

from . import db as _db
from . import ingest as _ingest
from .models import (
    ADRDetail,
    Health,
    RegisterRef,
    RefreshAccepted,
    RunbookDetail,
    SearchHit,
    SearchResponse,
)


DOCS_ROOT = os.environ.get("XINDEX_DOCS_ROOT", "/docs")
DB_PATH = os.environ.get("XINDEX_DB", "/data/xindex.db")


def _do_ingest_sync() -> None:
    """Open a fresh connection and run a full re-ingest."""
    with _db.connect(DB_PATH) as conn:
        _ingest.ingest_all(conn, DOCS_ROOT)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    with _db.connect(DB_PATH) as conn:
        _db.init_schema(conn)
        empty = _db.counts(conn)["adrs"] == 0
    if empty:
        _do_ingest_sync()
    yield


app = FastAPI(
    title="xindex",
    version="0.1.0",
    description="Repo-local cross-index of ADRs, Decision Register, and runbooks (D-16-02).",
    lifespan=lifespan,
)


def get_conn():
    with _db.connect(DB_PATH) as conn:
        yield conn


ConnDep = Annotated[sqlite3.Connection, Depends(get_conn)]


def _normalize_adr_id(raw: str) -> str:
    """Accept 'A-014', 'ADR-A-14', 'adr-a-014' etc; emit 'ADR-A-NNN'."""
    s = raw.strip().upper()
    s = s.replace("ADR-", "", 1) if s.startswith("ADR-") else s
    m = re.match(r"^A-(\d+)$", s)
    if not m:
        raise HTTPException(400, detail=f"Invalid ADR id: {raw!r}")
    return f"ADR-A-{m.group(1).zfill(3)}"


@app.get("/healthz", response_model=Health)
def healthz(conn: ConnDep) -> Health:
    return Health(
        status="ok",
        last_ingest_at=_db.get_meta(conn, "last_ingest_at"),
        counts=_db.counts(conn),
        docs_root=DOCS_ROOT,
        db_path=DB_PATH,
    )


@app.get("/adr/{adr_id}", response_model=ADRDetail)
def get_adr(adr_id: str, conn: ConnDep) -> ADRDetail:
    canonical = _normalize_adr_id(adr_id)
    row = conn.execute(
        "SELECT id, short_id, title, status, date, phase, source, path, body, sections_json "
        "FROM adrs WHERE id = ?",
        (canonical,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail=f"ADR not found: {canonical}")

    reg_row = conn.execute(
        "SELECT short_id, category, title, summary FROM decision_register_entries "
        "WHERE adr_id = ?",
        (canonical,),
    ).fetchone()
    register_entry = (
        RegisterRef(
            short_id=reg_row["short_id"],
            category=reg_row["category"],
            title=reg_row["title"],
            summary=reg_row["summary"],
        )
        if reg_row
        else None
    )

    return ADRDetail(
        id=row["id"],
        short_id=row["short_id"],
        title=row["title"],
        status=row["status"],
        date=row["date"],
        phase=row["phase"],
        source=row["source"],
        path=row["path"],
        body=row["body"],
        sections=json.loads(row["sections_json"] or "{}"),
        register_entry=register_entry,
    )


@app.get("/runbook/{topic}", response_model=RunbookDetail)
def get_runbook(topic: str, conn: ConnDep) -> RunbookDetail:
    name = topic.removesuffix(".md")
    row = conn.execute(
        "SELECT name, title, path, body FROM runbooks WHERE name = ?",
        (name,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Runbook not found: {name}")
    return RunbookDetail(
        name=row["name"], title=row["title"], path=row["path"], body=row["body"]
    )


_FTS_QUOTE_RE = re.compile(r"[^A-Za-z0-9_\-]+")


def _build_fts_query(q: str) -> str:
    """Convert freeform query into a safe FTS5 MATCH expression.

    Each whitespace-split token is wrapped in double quotes (FTS5 phrase
    syntax) after stripping characters that would terminate the phrase.
    Empty tokens are dropped.
    """
    tokens = []
    for raw in q.split():
        cleaned = _FTS_QUOTE_RE.sub(" ", raw).strip()
        if cleaned:
            tokens.append(f'"{cleaned}"')
    if not tokens:
        raise HTTPException(400, detail="empty query")
    return " ".join(tokens)


@app.get("/search", response_model=SearchResponse)
def search(
    conn: ConnDep,
    q: str = Query(..., min_length=1, max_length=200),
    type: str = Query("all", pattern="^(all|adr|runbook|register)$"),
    limit: int = Query(20, ge=1, le=100),
) -> SearchResponse:
    fts_q = _build_fts_query(q)
    base_sql = (
        "SELECT kind, ref, title, "
        "snippet(xindex_fts, 3, '<<', '>>', '…', 12) AS snippet, "
        "bm25(xindex_fts) AS rank "
        "FROM xindex_fts WHERE xindex_fts MATCH ?"
    )
    params: list = [fts_q]
    if type != "all":
        base_sql += " AND kind = ?"
        params.append(type)
    base_sql += " ORDER BY rank LIMIT ?"
    params.append(limit)

    try:
        rows = conn.execute(base_sql, params).fetchall()
    except sqlite3.OperationalError as e:
        raise HTTPException(400, detail=f"search failed: {e}")

    hits = [
        SearchHit(
            kind=r["kind"],
            ref=r["ref"],
            title=r["title"],
            snippet=r["snippet"] or "",
            rank=float(r["rank"]),
        )
        for r in rows
    ]
    return SearchResponse(query=q, type=type, count=len(hits), results=hits)


@app.post("/refresh", response_model=RefreshAccepted, status_code=202)
def refresh(conn: ConnDep, bg: BackgroundTasks) -> RefreshAccepted:
    counts_before = _db.counts(conn)
    bg.add_task(_do_ingest_sync)
    return RefreshAccepted(counts_before=counts_before)
