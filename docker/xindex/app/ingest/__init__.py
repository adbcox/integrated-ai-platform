"""Ingest orchestrator — runs each source ingester and refreshes meta.

Two source classes:

  Local (repo files)        — adr, runbook, register
                              Atomic full rebuild via reset_for_ingest().
                              Failure here is unusual (file-system level).

  External (D-16-02.1+)     — netbox, plane (D-16-02.2)
                              Per-source partial refresh via reset_source().
                              Each runs through snapshot-then-restore; a
                              failure flips that source's status to 'error'
                              and rewrites the prior rows, leaving the prior
                              successful ingest's data intact (stale).
                              No external source ever wipes another's data.

D-16-02.1 doctrine: external-source failures must NEVER cause the
HTTP API to return 500 from /refresh, and must NEVER reduce
counts of unrelated kinds. Stale-survival is preferred over
data loss.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sqlite3

from .. import db as _db
from . import adr as _adr
from . import decision_register as _reg
from . import netbox as _netbox
from . import plane as _plane
from . import runbook as _rb


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ingest_local(conn: sqlite3.Connection, docs_root: str) -> dict[str, int]:
    """Atomic rebuild of the three repo-local sources."""
    _db.reset_for_ingest(conn)
    adr_count = _adr.ingest(conn, os.path.join(docs_root, "adr"))
    rb_count = _rb.ingest(conn, os.path.join(docs_root, "runbooks"))
    reg_count = _reg.ingest(
        conn, os.path.join(docs_root, "DECISION_REGISTER.md")
    )
    ts = _now_iso()
    for src in ("adr", "runbook", "register"):
        _db.set_source_status(conn, src, "ok", timestamp=ts)
    return {
        "adrs": adr_count,
        "runbooks": rb_count,
        "decision_register_entries": reg_count,
    }


def _ingest_netbox(
    conn: sqlite3.Connection,
    *,
    fetcher=None,
) -> _netbox.NetboxIngestResult:
    """Partial refresh of the NetBox source.

    Snapshot-then-restore: rather than relying on SAVEPOINT semantics
    (which interact awkwardly with the stdlib sqlite3 module's
    autocommit/legacy transaction handling), we capture the prior
    rows, run the ingest, and on failure restore the snapshot. This
    keeps the partial-refresh guarantee testable and portable across
    Python's sqlite3 isolation modes.
    """
    ts = _now_iso()
    snapshot = _snapshot_netbox(conn)
    try:
        _db.reset_source(conn, "netbox")
        result = _netbox.ingest(conn, fetcher=fetcher)
    except Exception as exc:  # defensive
        _restore_netbox(conn, snapshot)
        _db.set_source_status(
            conn, "netbox", "stale", error=f"unhandled: {exc!r}"
        )
        return _netbox.NetboxIngestResult(ok=False, error=f"unhandled: {exc!r}")

    if not result.ok:
        _restore_netbox(conn, snapshot)
        # Status: 'error' if we tried and failed, 'unknown' if we
        # explicitly skipped (no token). Prior data survives because
        # the snapshot was restored.
        status = "error" if not result.skipped else "unknown"
        _db.set_source_status(conn, "netbox", status, error=result.error)
        return result

    _db.set_source_status(conn, "netbox", "ok", timestamp=ts)
    return result


def _snapshot_netbox(conn: sqlite3.Connection) -> dict:
    return {
        "services": [
            tuple(r) for r in conn.execute(
                "SELECT name, netbox_id, protocol, ports_json, parent_kind, "
                "parent_ref, description, custom_json, source FROM services"
            )
        ],
        "nodes": [
            tuple(r) for r in conn.execute(
                "SELECT name, netbox_id, role, site, status, primary_ip, "
                "description, custom_json, source FROM nodes"
            )
        ],
        "links": [
            tuple(r) for r in conn.execute(
                "SELECT from_kind, from_ref, to_kind, to_ref, link_type, source "
                "FROM entity_links WHERE source='netbox'"
            )
        ],
        "fts": [
            tuple(r) for r in conn.execute(
                "SELECT kind, ref, title, body FROM xindex_fts "
                "WHERE kind IN ('service','node')"
            )
        ],
    }


def _restore_netbox(conn: sqlite3.Connection, snap: dict) -> None:
    _db.reset_source(conn, "netbox")
    conn.executemany(
        "INSERT INTO services(name, netbox_id, protocol, ports_json, "
        "parent_kind, parent_ref, description, custom_json, source) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        snap["services"],
    )
    conn.executemany(
        "INSERT INTO nodes(name, netbox_id, role, site, status, primary_ip, "
        "description, custom_json, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        snap["nodes"],
    )
    conn.executemany(
        "INSERT INTO entity_links(from_kind, from_ref, to_kind, to_ref, "
        "link_type, source) VALUES(?, ?, ?, ?, ?, ?)",
        snap["links"],
    )
    conn.executemany(
        "INSERT INTO xindex_fts(kind, ref, title, body) VALUES(?, ?, ?, ?)",
        snap["fts"],
    )


def _ingest_plane(
    conn: sqlite3.Connection,
    *,
    fetcher=None,
) -> _plane.PlaneIngestResult:
    """Partial refresh of the Plane source.

    Same snapshot-then-restore guarantee as NetBox: a 429, network
    error, or any other failure leaves the prior plane_issues /
    plane_modules / tracked_in entity_links intact (stale), while
    NetBox + local source data is unaffected.
    """
    ts = _now_iso()
    snapshot = _snapshot_plane(conn)
    try:
        _db.reset_source(conn, "plane")
        result = _plane.ingest(conn, fetcher=fetcher)
    except Exception as exc:  # defensive
        _restore_plane(conn, snapshot)
        _db.set_source_status(
            conn, "plane", "stale", error=f"unhandled: {exc!r}"
        )
        return _plane.PlaneIngestResult(ok=False, error=f"unhandled: {exc!r}")

    if not result.ok:
        _restore_plane(conn, snapshot)
        # 'error' if we tried and failed, 'unknown' if we explicitly
        # skipped (no creds). Prior data survives via the snapshot.
        status = "error" if not result.skipped else "unknown"
        _db.set_source_status(conn, "plane", status, error=result.error)
        return result

    _db.set_source_status(conn, "plane", "ok", timestamp=ts)
    return result


def _snapshot_plane(conn: sqlite3.Connection) -> dict:
    return {
        "issues": [
            tuple(r) for r in conn.execute(
                "SELECT external_id, plane_id, name, state_name, module_name, "
                "project_id, description, updated_at, source FROM plane_issues"
            )
        ],
        "modules": [
            tuple(r) for r in conn.execute(
                "SELECT name, plane_id, external_id, description, source "
                "FROM plane_modules"
            )
        ],
        "links": [
            tuple(r) for r in conn.execute(
                "SELECT from_kind, from_ref, to_kind, to_ref, link_type, source "
                "FROM entity_links WHERE source='plane'"
            )
        ],
        "fts": [
            tuple(r) for r in conn.execute(
                "SELECT kind, ref, title, body FROM xindex_fts "
                "WHERE kind = 'plane_issue'"
            )
        ],
    }


def _restore_plane(conn: sqlite3.Connection, snap: dict) -> None:
    _db.reset_source(conn, "plane")
    conn.executemany(
        "INSERT INTO plane_issues(external_id, plane_id, name, state_name, "
        "module_name, project_id, description, updated_at, source) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        snap["issues"],
    )
    conn.executemany(
        "INSERT INTO plane_modules(name, plane_id, external_id, description, "
        "source) VALUES(?, ?, ?, ?, ?)",
        snap["modules"],
    )
    conn.executemany(
        "INSERT INTO entity_links(from_kind, from_ref, to_kind, to_ref, "
        "link_type, source) VALUES(?, ?, ?, ?, ?, ?)",
        snap["links"],
    )
    conn.executemany(
        "INSERT INTO xindex_fts(kind, ref, title, body) VALUES(?, ?, ?, ?)",
        snap["fts"],
    )


def ingest_all(
    conn: sqlite3.Connection,
    docs_root: str,
    *,
    netbox_fetcher=None,
    plane_fetcher=None,
) -> dict:
    """Full re-ingest. Local sources atomic, externals partial.

    `netbox_fetcher` and `plane_fetcher` are dependency-injectable for tests.
    """
    local_counts = _ingest_local(conn, docs_root)
    nb_result = _ingest_netbox(conn, fetcher=netbox_fetcher)
    pl_result = _ingest_plane(conn, fetcher=plane_fetcher)

    ts = _now_iso()
    _db.set_meta(conn, "last_ingest_at", ts)
    summary = {
        **local_counts,
        "services": nb_result.services,
        "nodes": nb_result.nodes,
        "entity_links": nb_result.entity_links + pl_result.entity_links,
        "plane_issues": pl_result.plane_issues,
        "plane_modules": pl_result.plane_modules,
        "last_ingest_at": ts,
    }
    _db.set_meta(conn, "counts", json.dumps(summary))
    return summary
