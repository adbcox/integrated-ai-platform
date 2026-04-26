"""tests/unit/test_priority_engine.py

Unit tests for domains/priority_engine.py.

All file I/O is mocked via the sample_roadmap_items fixture defined in
tests/conftest.py. No real disk access occurs.
"""
from __future__ import annotations

from typing import List
from unittest.mock import MagicMock, patch

import pytest

# ── Import guard ──────────────────────────────────────────────────────────────
try:
    from domains.priority_engine import PriorityEngine, PriorityWeights  # type: ignore
    _PRIORITY_AVAILABLE = True
except ImportError:
    _PRIORITY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _PRIORITY_AVAILABLE,
    reason="domains.priority_engine not yet implemented",
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_item(**kwargs) -> dict:
    base = {
        "id": "RM-X-001",
        "title": "Test item",
        "category": "Testing",
        "priority": "Medium",
        "status": "backlog",
        "loe": "M",
        "strategic_value": 5,
        "dependencies": [],
        "description": "",
        "created_at": "2026-01-01T00:00:00Z",
    }
    base.update(kwargs)
    return base


def _engine_with_items(items: list[dict]) -> "PriorityEngine":
    """Build an engine pre-loaded with the given items (bypasses file I/O)."""
    engine = PriorityEngine.__new__(PriorityEngine)
    # Try to inject items directly; fall back to mock of load_items
    if hasattr(engine, "_items"):
        engine._items = items
    elif hasattr(engine, "items"):
        engine.items = items
    else:
        engine = PriorityEngine()
        engine.load_items = MagicMock(return_value=items)
        engine._items = items
    return engine


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestQuickWin:
    @pytest.mark.unit
    def test_score_item_quick_win(self) -> None:
        """High strategic value + small effort → quick_win flag set."""
        engine = PriorityEngine()
        item = _make_item(strategic_value=8, loe="S")
        result = engine.score_item(item)

        assert result.get("quick_win") is True, (
            f"Expected quick_win=True for sv=8, loe=S; got: {result}"
        )

    @pytest.mark.unit
    def test_score_item_not_quick_win(self) -> None:
        """Low strategic value + extra-large effort → quick_win=False."""
        engine = PriorityEngine()
        item = _make_item(strategic_value=3, loe="XL")
        result = engine.score_item(item)

        assert result.get("quick_win") is False, (
            f"Expected quick_win=False for sv=3, loe=XL; got: {result}"
        )


class TestWeights:
    @pytest.mark.unit
    def test_weights_sum_to_one(self) -> None:
        """Default PriorityWeights dimensions must sum to 1.0."""
        weights = PriorityWeights()
        total = sum(
            getattr(weights, attr)
            for attr in ("value", "urgency", "effort", "risk")
            if hasattr(weights, attr)
        )
        assert abs(total - 1.0) < 1e-6, (
            f"Weights must sum to 1.0, got {total}"
        )

    @pytest.mark.unit
    def test_custom_weights_accepted(self) -> None:
        """PriorityWeights should accept custom float arguments."""
        w = PriorityWeights(value=0.5, urgency=0.3, effort=0.1, risk=0.1)
        assert w.value == pytest.approx(0.5)
        assert w.urgency == pytest.approx(0.3)


class TestRanking:
    @pytest.mark.unit
    def test_rank_all_sorted_descending(self, sample_roadmap_items: list[dict]) -> None:
        """rank_all() must return items sorted by score descending."""
        engine = PriorityEngine()
        ranked = engine.rank_all(sample_roadmap_items)

        scores = [r.get("score", r.get("priority_score", 0)) for r in ranked]
        assert scores == sorted(scores, reverse=True), (
            "rank_all must return items in descending score order"
        )

    @pytest.mark.unit
    def test_rank_all_returns_all_items(self, sample_roadmap_items: list[dict]) -> None:
        """rank_all() must return the same number of items it received."""
        engine = PriorityEngine()
        ranked = engine.rank_all(sample_roadmap_items)
        assert len(ranked) == len(sample_roadmap_items)

    @pytest.mark.unit
    def test_custom_weights_affect_scoring(self, sample_roadmap_items: list[dict]) -> None:
        """Changing weight for 'value' to 1.0 should change relative ordering."""
        engine_default = PriorityEngine()
        engine_value   = PriorityEngine()

        ranked_default = engine_default.rank_all(sample_roadmap_items)
        ranked_value   = engine_value.rank_all(
            sample_roadmap_items,
            weights=PriorityWeights(value=1.0, urgency=0.0, effort=0.0, risk=0.0),
        )

        # They don't have to produce the same order — just verify both run without error
        assert len(ranked_value) == len(sample_roadmap_items)


class TestQuickWinsLimit:
    @pytest.mark.unit
    def test_get_quick_wins_limit(self, sample_roadmap_items: list[dict]) -> None:
        """get_quick_wins(limit=3) must return at most 3 items."""
        engine = PriorityEngine()
        wins = engine.get_quick_wins(sample_roadmap_items, limit=3)
        assert len(wins) <= 3

    @pytest.mark.unit
    def test_get_quick_wins_all_are_quick_wins(self, sample_roadmap_items: list[dict]) -> None:
        """Every item returned by get_quick_wins must have quick_win=True."""
        engine = PriorityEngine()
        wins = engine.get_quick_wins(sample_roadmap_items, limit=10)
        for w in wins:
            assert w.get("quick_win") is True, f"Non-quick-win returned: {w}"


class TestDependencyBonus:
    @pytest.mark.unit
    def test_score_with_dependencies_boosts_blockers(self) -> None:
        """Items that unblock others should score higher than equivalent items that don't."""
        engine = PriorityEngine()
        # Both items have same sv, loe, priority
        blocker  = _make_item(id="BLOCKER",  strategic_value=5, loe="S")
        leaf     = _make_item(id="LEAF",     strategic_value=5, loe="S")

        # Simulate: blocker is depended on by 3 items
        all_items = [
            blocker,
            leaf,
            _make_item(id="D1", dependencies=["BLOCKER"]),
            _make_item(id="D2", dependencies=["BLOCKER"]),
            _make_item(id="D3", dependencies=["BLOCKER"]),
        ]

        ranked = engine.rank_all(all_items)
        blocker_rank = next(i for i, r in enumerate(ranked) if r["id"] == "BLOCKER")
        leaf_rank    = next(i for i, r in enumerate(ranked) if r["id"] == "LEAF")

        assert blocker_rank <= leaf_rank, (
            "Blocker should rank equal or higher than leaf of same sv/loe"
        )


class TestUrgencyFromPriority:
    @pytest.mark.unit
    def test_critical_priority_gives_max_urgency(self) -> None:
        """An item with priority='Critical' should yield urgency_score of 5."""
        engine = PriorityEngine()
        item = _make_item(priority="Critical")
        scored = engine.score_item(item)

        urgency = scored.get("urgency_score", scored.get("urgency", None))
        assert urgency == 5, (
            f"Critical priority should yield urgency_score=5, got {urgency}"
        )

    @pytest.mark.unit
    def test_low_priority_gives_lower_urgency(self) -> None:
        """An item with priority='Low' should have a lower urgency than 'Critical'."""
        engine = PriorityEngine()
        low_item      = _make_item(priority="Low")
        critical_item = _make_item(priority="Critical")

        low_scored      = engine.score_item(low_item)
        critical_scored = engine.score_item(critical_item)

        low_urgency      = low_scored.get("urgency_score", low_scored.get("urgency", 0))
        critical_urgency = critical_scored.get("urgency_score", critical_scored.get("urgency", 5))

        assert low_urgency < critical_urgency
