"""ADR ingester contract tests."""
from __future__ import annotations

import json
from pathlib import Path

from app import db as _db
from app.ingest import adr as _adr


def test_bolded_header_is_parsed(fixture_docs: Path, db_path: str) -> None:
    with _db.connect(db_path) as conn:
        _db.init_schema(conn)
        n = _adr.ingest(conn, str(fixture_docs / "adr"))
        assert n == 2

        row = conn.execute(
            "SELECT id, short_id, title, status, date, phase, sections_json "
            "FROM adrs WHERE id='ADR-A-001'"
        ).fetchone()

    assert row is not None
    assert row["id"] == "ADR-A-001"
    assert row["short_id"] == "A-001"
    assert row["title"] == "Sample bolded-header ADR"
    assert row["status"] == "Accepted"
    assert row["date"] == "2026-04-01"
    assert row["phase"] == "15"

    sections = json.loads(row["sections_json"])
    assert "Decision" in sections
    assert "NetBox" in sections["Decision"]


def test_section_header_style_falls_back(fixture_docs: Path, db_path: str) -> None:
    with _db.connect(db_path) as conn:
        _db.init_schema(conn)
        _adr.ingest(conn, str(fixture_docs / "adr"))

        row = conn.execute(
            "SELECT title, status, date FROM adrs WHERE id='ADR-A-007'"
        ).fetchone()

    assert row is not None
    assert row["title"] == "Section-style header sample"
    assert row["status"] == "Accepted"
    assert row["date"] == "2026-04-27"
