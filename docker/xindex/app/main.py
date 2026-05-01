"""xindex FastAPI app.

Endpoints:
    GET  /healthz                          — liveness + per-source health
    GET  /adr/{id}                         — full ADR detail (id or short id)
    GET  /runbook/{topic}                  — full runbook detail
    GET  /service/{name}                   — service detail + entity links
    GET  /node/{name}                      — node detail + entity links
    GET  /links?from_kind=&from_ref=&...   — entity-link query
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
    EntityLink,
    Health,
    LinksResponse,
    NodeDetail,
    PerSourceHealth,
    PlaneIssueDetail,
    PlaneIssueRef,
    PlaneModuleDetail,
    RegisterRef,
    RefreshAccepted,
    RunbookDetail,
    SearchHit,
    SearchResponse,
    ServiceDetail,
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
    version="0.3.0",
    description=(
        "Cross-index of ADRs, Decision Register, runbooks (D-16-02), "
        "NetBox services + nodes + entity_links (D-16-02.1), and Plane "
        "issues + modules + tracked_in links (D-16-02.2). Plane data is "
        "read-only (ADR-A-006)."
    ),
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


def _per_source_health(conn: sqlite3.Connection) -> list[PerSourceHealth]:
    out: list[PerSourceHealth] = []
    for src in _db.ALL_SOURCES:
        st = _db.get_source_status(conn, src)
        out.append(
            PerSourceHealth(
                source=st["source"],
                last_ingest_at=st["last_ingest_at"],
                status=st["status"],
                error=st["error"],
            )
        )
    return out


@app.get("/healthz", response_model=Health)
def healthz(conn: ConnDep) -> Health:
    return Health(
        status="ok",
        last_ingest_at=_db.get_meta(conn, "last_ingest_at"),
        counts=_db.counts(conn),
        docs_root=DOCS_ROOT,
        db_path=DB_PATH,
        sources=_per_source_health(conn),
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

    plane_tracking = _plane_tracking_for_adr(conn, canonical)

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
        plane_tracking=plane_tracking,
    )


def _plane_tracking_for_adr(
    conn: sqlite3.Connection, adr_id: str
) -> PlaneIssueRef | None:
    """Resolve the Plane issue tracking this ADR via tracked_in entity_link."""
    row = conn.execute(
        """
        SELECT pi.external_id, pi.name, pi.state_name, pi.module_name,
               pi.updated_at
        FROM entity_links el
        JOIN plane_issues pi ON pi.external_id = el.to_ref
        WHERE el.from_kind='adr' AND el.from_ref=?
          AND el.to_kind='plane_issue' AND el.link_type='tracked_in'
          AND el.source='plane'
        LIMIT 1
        """,
        (adr_id,),
    ).fetchone()
    if row is None:
        return None
    return PlaneIssueRef(
        external_id=row["external_id"],
        name=row["name"],
        state_name=row["state_name"],
        module_name=row["module_name"],
        updated_at=row["updated_at"],
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


def _links_for(conn: sqlite3.Connection, kind: str, ref: str) -> list[EntityLink]:
    rows = conn.execute(
        """
        SELECT from_kind, from_ref, to_kind, to_ref, link_type, source
        FROM entity_links
        WHERE (from_kind=? AND from_ref=?) OR (to_kind=? AND to_ref=?)
        ORDER BY link_type, to_kind, to_ref
        """,
        (kind, ref, kind, ref),
    ).fetchall()
    return [EntityLink(**dict(r)) for r in rows]


@app.get("/service/{name}", response_model=ServiceDetail)
def get_service(name: str, conn: ConnDep) -> ServiceDetail:
    row = conn.execute(
        "SELECT name, netbox_id, protocol, ports_json, parent_kind, parent_ref, "
        "description, custom_json, source FROM services WHERE name = ?",
        (name,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Service not found: {name}")
    return ServiceDetail(
        name=row["name"],
        netbox_id=row["netbox_id"],
        protocol=row["protocol"],
        ports=json.loads(row["ports_json"] or "[]"),
        parent_kind=row["parent_kind"],
        parent_ref=row["parent_ref"],
        description=row["description"] or "",
        custom=json.loads(row["custom_json"] or "{}"),
        source=row["source"],
        links=_links_for(conn, "service", row["name"]),
    )


@app.get("/node/{name}", response_model=NodeDetail)
def get_node(name: str, conn: ConnDep) -> NodeDetail:
    row = conn.execute(
        "SELECT name, netbox_id, role, site, status, primary_ip, "
        "description, custom_json, source FROM nodes WHERE name = ?",
        (name,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Node not found: {name}")
    return NodeDetail(
        name=row["name"],
        netbox_id=row["netbox_id"],
        role=row["role"],
        site=row["site"],
        status=row["status"],
        primary_ip=row["primary_ip"],
        description=row["description"] or "",
        custom=json.loads(row["custom_json"] or "{}"),
        source=row["source"],
        links=_links_for(conn, "node", row["name"]),
    )


@app.get("/plane/{external_id}", response_model=PlaneIssueDetail)
def get_plane_issue(external_id: str, conn: ConnDep) -> PlaneIssueDetail:
    row = conn.execute(
        "SELECT external_id, plane_id, name, state_name, module_name, "
        "project_id, description, updated_at, source FROM plane_issues "
        "WHERE external_id = ?",
        (external_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Plane issue not found: {external_id}")
    return PlaneIssueDetail(
        external_id=row["external_id"],
        plane_id=row["plane_id"],
        name=row["name"],
        state_name=row["state_name"],
        module_name=row["module_name"],
        project_id=row["project_id"],
        description=row["description"] or "",
        updated_at=row["updated_at"],
        source=row["source"],
        links=_links_for(conn, "plane_issue", row["external_id"]),
    )


@app.get("/plane/module/{name}", response_model=PlaneModuleDetail)
def get_plane_module(name: str, conn: ConnDep) -> PlaneModuleDetail:
    row = conn.execute(
        "SELECT name, plane_id, external_id, description, source "
        "FROM plane_modules WHERE name = ?",
        (name,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, detail=f"Plane module not found: {name}")
    issue_rows = conn.execute(
        "SELECT external_id, name, state_name, module_name, updated_at "
        "FROM plane_issues WHERE module_name = ? "
        "ORDER BY external_id",
        (row["name"],),
    ).fetchall()
    issues = [
        PlaneIssueRef(
            external_id=r["external_id"],
            name=r["name"],
            state_name=r["state_name"],
            module_name=r["module_name"],
            updated_at=r["updated_at"],
        )
        for r in issue_rows
    ]
    return PlaneModuleDetail(
        name=row["name"],
        plane_id=row["plane_id"],
        external_id=row["external_id"],
        description=row["description"] or "",
        source=row["source"],
        issues=issues,
    )


@app.get("/links", response_model=LinksResponse)
def list_links(
    conn: ConnDep,
    from_kind: str | None = Query(None, max_length=32),
    from_ref: str | None = Query(None, max_length=128),
    to_kind: str | None = Query(None, max_length=32),
    to_ref: str | None = Query(None, max_length=128),
    link_type: str | None = Query(None, max_length=32),
    source: str | None = Query(None, max_length=32),
    limit: int = Query(200, ge=1, le=2000),
) -> LinksResponse:
    clauses: list[str] = []
    params: list = []
    for col, val in (
        ("from_kind", from_kind),
        ("from_ref", from_ref),
        ("to_kind", to_kind),
        ("to_ref", to_ref),
        ("link_type", link_type),
        ("source", source),
    ):
        if val:
            clauses.append(f"{col} = ?")
            params.append(val)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    rows = conn.execute(
        "SELECT from_kind, from_ref, to_kind, to_ref, link_type, source "
        f"FROM entity_links{where} ORDER BY from_kind, from_ref, link_type LIMIT ?",
        params,
    ).fetchall()
    links = [EntityLink(**dict(r)) for r in rows]
    return LinksResponse(count=len(links), results=links)


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
    type: str = Query(
        "all", pattern="^(all|adr|runbook|register|service|node|plane_issue)$"
    ),
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
