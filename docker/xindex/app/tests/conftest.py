"""Shared pytest fixtures for xindex tests.

Each test gets a fresh on-disk SQLite DB and a tiny synthetic /docs tree
covering the three repo-local sources we ingest.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# Make `app` importable when pytest is run from docker/xindex/.
_HERE = Path(__file__).resolve()
_PKG_PARENT = _HERE.parents[2]  # .../xindex
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))


@pytest.fixture()
def fixture_docs(tmp_path: Path) -> Path:
    """Build a minimal docs tree mirroring the real layout."""
    docs = tmp_path / "docs"
    (docs / "adr").mkdir(parents=True)
    (docs / "runbooks").mkdir(parents=True)

    (docs / "adr" / "ADR-A-001.md").write_text(
        """# ADR-A-001 — Sample bolded-header ADR
**Status:** Accepted
**Date:** 2026-04-01
**Phase:** 15

## Context

There was a need for a fixture.

## Decision

Use NetBox-style fixtures so the parser exercise covers the load-bearing path.

## Consequences

Tests can run without the full repo.
""",
            encoding="utf-8",
    )

    (docs / "adr" / "ADR-A-007-section-style.md").write_text(
        """# ADR-A-007: Section-style header sample

## Status
Accepted (2026-04-27)

## Context

Verifies that the alternate header style is parsed.
""",
            encoding="utf-8",
    )

    (docs / "DECISION_REGISTER.md").write_text(
        """# Decision Register

## Architecture and runtime

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-001](adr/ADR-A-001.md) | Sample bolded-header ADR | Fixture for the bolded header style. |

## Operations and security

| ADR | Title | One-line summary |
|-----|-------|------------------|
| [A-007](adr/ADR-A-007-section-style.md) | Section-style header sample | Fixture for the section header style. |
""",
            encoding="utf-8",
    )

    (docs / "runbooks" / "sample-runbook.md").write_text(
        """# Sample Runbook

## Procedure

Run the fixture. Verify the rainbow.
""",
            encoding="utf-8",
    )
    return docs


@pytest.fixture()
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    p = str(tmp_path / "xindex.db")
    monkeypatch.setenv("XINDEX_DB", p)
    return p
