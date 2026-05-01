"""Runbook ingester contract tests."""
from __future__ import annotations

from pathlib import Path

from app import db as _db
from app.ingest import runbook as _rb


def test_runbook_is_keyed_by_filename(fixture_docs: Path, db_path: str) -> None:
    with _db.connect(db_path) as conn:
        _db.init_schema(conn)
        n = _rb.ingest(conn, str(fixture_docs / "runbooks"))
        assert n == 1

        row = conn.execute(
            "SELECT name, title, body FROM runbooks WHERE name='sample-runbook'"
        ).fetchone()

    assert row is not None
    assert row["title"] == "Sample Runbook"
    assert "Procedure" in row["body"]
