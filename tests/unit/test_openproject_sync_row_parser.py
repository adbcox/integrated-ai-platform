"""ROW_RE coverage for scripts/openproject-sync-from-framework.py.

The parser was forked from plane-sync and didn't tolerate the
"(historical: 17.X)" annotation that Phase 17 framework rows carry
(added in WP-17-04-01.5 / commit 51b012e). Result: Phase 17 rows
parsed as 0 deliverables — silent no-op against OpenProject.

These tests pin down the row formats the parser must accept (Phase 16
and earlier — no parenthetical; Phase 17 — with historical
parenthetical) and the formats it must reject (header lines, blank
table rows). They guard against regression on either direction of the
fix.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = REPO_ROOT / "scripts" / "openproject-sync-from-framework.py"


def _load_sync_module():
    spec = importlib.util.spec_from_file_location(
        "openproject_sync_from_framework", SYNC_SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


SYNC = _load_sync_module()
ROW_RE = SYNC.ROW_RE


def _match_row(line: str):
    return ROW_RE.match(line)


# ── Phase 16 and earlier (no parenthetical) ───────────────────────────────────


def test_phase16_canonical_row_matches():
    line = "| D-16-01: Audit deliverable | DONE | abc1234 |"
    m = _match_row(line)
    assert m is not None
    assert m.group("extid") == "D-16-01"
    assert m.group("phase_d") == "16"
    assert m.group("title") == "Audit deliverable"
    assert m.group("status") == "DONE"
    assert m.group("reference") == "abc1234"


def test_phase15_dotted_subdeliverable_matches():
    line = "| D-15-02.A: Sub-deliverable | IN PROGRESS | per phase plan |"
    m = _match_row(line)
    assert m is not None
    assert m.group("extid") == "D-15-02.A"
    assert m.group("phase_d") == "15"
    assert m.group("status") == "IN PROGRESS"


# ── Phase 17 (with historical parenthetical) ──────────────────────────────────


def test_phase17_with_historical_parenthetical_matches():
    """The fix: rows with '(historical: 17.X)' between extid and colon."""
    line = (
        "| D-17-01 (historical: 17.A): Stack architecture audit promoted to "
        "repo | DONE | 8193014 |"
    )
    m = _match_row(line)
    assert m is not None, "Phase 17 row with historical parenthetical must match"
    assert m.group("extid") == "D-17-01"
    assert m.group("phase_d") == "17"
    assert m.group("title") == "Stack architecture audit promoted to repo"
    assert m.group("status") == "DONE"
    assert m.group("reference") == "8193014"


def test_phase17_done_with_long_hash_chain_matches():
    """The D-17-04 row carries an 11-commit hash chain + ADR ref."""
    line = (
        "| D-17-04 (historical: 17.D): Replace Plane with OpenProject | DONE "
        "| 8819861+a184202+3a30c6f+51b012e+f8e23ba+37f874c+d283fa1+abbbba8+"
        "cf0ff61+32b7ad0+2f6cc32 (ADR-A-018) |"
    )
    m = _match_row(line)
    assert m is not None
    assert m.group("extid") == "D-17-04"
    assert m.group("phase_d") == "17"
    assert m.group("status") == "DONE"
    assert "2f6cc32" in m.group("reference")
    assert "ADR-A-018" in m.group("reference")


def test_phase17_dotted_historical_matches():
    """Defensive: '(historical: 17.A.1)' if multi-part historical IDs land."""
    line = "| D-17-01 (historical: 17.A.1): Foo | DONE | abc |"
    m = _match_row(line)
    assert m is not None
    assert m.group("extid") == "D-17-01"
    assert m.group("phase_d") == "17"


def test_phase17_extra_whitespace_around_parenthetical_matches():
    line = "| D-17-05 (historical: 17.E):  Observability  | DONE | xyz |"
    m = _match_row(line)
    assert m is not None
    assert m.group("extid") == "D-17-05"
    assert m.group("title") == "Observability"


# ── Negative cases ───────────────────────────────────────────────────────────


def test_phase_heading_row_does_not_match():
    line = "## 9. Phase 17 — current state"
    assert _match_row(line) is None


def test_table_separator_row_does_not_match():
    line = "|---|---|---|"
    assert _match_row(line) is None


def test_table_header_row_does_not_match():
    line = "| Deliverable | Status | Reference |"
    assert _match_row(line) is None


def test_non_extid_row_does_not_match():
    """Rows whose first column isn't a D-NN-MM identifier are not deliverables."""
    line = "| Notes | Some text | another col |"
    assert _match_row(line) is None
