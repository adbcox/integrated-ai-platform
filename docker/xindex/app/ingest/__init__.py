"""Ingest orchestrator — runs each source ingester and refreshes meta.

Sources in this deliverable (D-16-02) are repo-local files only:
    - ADRs                          (docs/adr/ADR-A-*.md)
    - Decision Register             (docs/DECISION_REGISTER.md)
    - Runbooks                      (docs/runbooks/*.md)

External sources (NetBox, Plane, Vault, InvenTree) are explicitly
deferred to D-16-02.1 / .2 / .3.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sqlite3

from .. import db as _db
from . import adr as _adr
from . import decision_register as _reg
from . import runbook as _rb


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ingest_all(conn: sqlite3.Connection, docs_root: str) -> dict:
    """Full re-ingest from disk. Returns summary counts."""
    _db.reset_for_ingest(conn)

    adr_count = _adr.ingest(conn, os.path.join(docs_root, "adr"))
    rb_count = _rb.ingest(conn, os.path.join(docs_root, "runbooks"))
    reg_count = _reg.ingest(conn, os.path.join(docs_root, "DECISION_REGISTER.md"))

    ts = _now_iso()
    _db.set_meta(conn, "last_ingest_at", ts)
    _db.set_meta(
        conn,
        "counts",
        json.dumps(
            {
                "adrs": adr_count,
                "runbooks": rb_count,
                "decision_register_entries": reg_count,
            }
        ),
    )
    return {
        "adrs": adr_count,
        "runbooks": rb_count,
        "decision_register_entries": reg_count,
        "last_ingest_at": ts,
    }
