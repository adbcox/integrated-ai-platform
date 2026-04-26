"""tests/unit/test_bandwidth_manager.py

Unit tests for domains/bandwidth_manager.py.

All time-sensitive behaviour is isolated via monkeypatch on datetime.datetime.now
and psutil.cpu_percent so tests are fully deterministic.
"""
from __future__ import annotations

import importlib
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# ── Import guard ──────────────────────────────────────────────────────────────
try:
    import domains.bandwidth_manager as _bw_module
    from domains.bandwidth_manager import (
        BandwidthManager,
        BandwidthWindow,
        THROTTLE_MBPS,
        FULL_SPEED_MBPS,
        BUSINESS_HOURS_START,
        BUSINESS_HOURS_END,
        TASK_PRIORITY_ORDER,
    )
    _BW_AVAILABLE = True
except ImportError:
    _BW_AVAILABLE = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(not _BW_AVAILABLE, reason="domains.bandwidth_manager not importable"),
]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch, tmp_path) -> BandwidthManager:
    """A fresh BandwidthManager with no YAML config (uses defaults)."""
    # Point config_path at a non-existent file so the manager uses defaults
    return BandwidthManager(config_path=str(tmp_path / "nonexistent.yaml"))


def _mock_now(hour: int, minute: int = 0, monkeypatch: pytest.MonkeyPatch | None = None):
    """Return a fake datetime object representing the given hour of day."""
    fake = MagicMock(spec=datetime)
    fake.hour = hour
    fake.minute = minute
    return fake


# ── Business hours ────────────────────────────────────────────────────────────


class TestIsBusinessHours:
    def test_is_business_hours_at_noon(self, manager: BandwidthManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Hour 12 is within business hours (09:00–18:00)."""
        monkeypatch.setattr(
            _bw_module, "datetime",
            type("_DT", (), {"now": staticmethod(lambda: _mock_now(12))})(),
        )
        # Reload the method's reference if needed — call through the real method
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(12)
            result = manager.is_business_hours()
        assert result is True, "Hour 12 should be within business hours"

    def test_is_business_hours_at_3am(self, manager: BandwidthManager) -> None:
        """Hour 3 is outside business hours."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(3)
            result = manager.is_business_hours()
        assert result is False, "Hour 3 should be outside business hours"

    def test_is_business_hours_at_start(self, manager: BandwidthManager) -> None:
        """Hour 9 (BUSINESS_HOURS_START) is the inclusive start."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(BUSINESS_HOURS_START)
            result = manager.is_business_hours()
        assert result is True

    def test_is_business_hours_at_end(self, manager: BandwidthManager) -> None:
        """Hour 18 (BUSINESS_HOURS_END) is exclusive — should be False."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(BUSINESS_HOURS_END)
            result = manager.is_business_hours()
        assert result is False


# ── Current limit ─────────────────────────────────────────────────────────────


class TestGetCurrentLimit:
    def test_get_current_limit_business_hours(self, manager: BandwidthManager) -> None:
        """During business hours and no windows defined → THROTTLE_MBPS."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(10)
            limit = manager.get_current_limit()
        assert limit == THROTTLE_MBPS, (
            f"Expected THROTTLE_MBPS={THROTTLE_MBPS}, got {limit}"
        )

    def test_get_current_limit_off_hours(self, manager: BandwidthManager) -> None:
        """Outside business hours and no windows defined → FULL_SPEED_MBPS."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(2)
            limit = manager.get_current_limit()
        assert limit == FULL_SPEED_MBPS, (
            f"Expected FULL_SPEED_MBPS={FULL_SPEED_MBPS}, got {limit}"
        )

    def test_custom_window_respected(self, manager: BandwidthManager) -> None:
        """A custom BandwidthWindow overrides the fallback logic."""
        custom_limit = 25.0
        window = BandwidthWindow(start_hour=0, end_hour=24, max_mbps=custom_limit, priority=0)
        manager.add_window(window)

        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(14)
            limit = manager.get_current_limit()
        assert limit == custom_limit, (
            f"Custom window should set limit to {custom_limit}, got {limit}"
        )


# ── Throttle params ───────────────────────────────────────────────────────────


class TestGetThrottleParams:
    def test_get_throttle_params_format(self, manager: BandwidthManager) -> None:
        """Returns a dict with a 'bwlimit' key."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(10)
            params = manager.get_throttle_params()
        assert "bwlimit" in params, "get_throttle_params must return dict with 'bwlimit'"

    def test_get_throttle_params_throttled_string(self, manager: BandwidthManager) -> None:
        """During business hours, bwlimit should be a non-zero string ending in 'M'."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(10)
            params = manager.get_throttle_params()
        bwlimit = params["bwlimit"]
        assert bwlimit != "0", "bwlimit should not be '0' during throttled period"
        assert bwlimit.endswith("M"), f"bwlimit should end with 'M', got: {bwlimit!r}"

    def test_get_throttle_params_full_speed_is_zero(self, manager: BandwidthManager) -> None:
        """Outside business hours with no windows → bwlimit='0' (unlimited)."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(3)
            params = manager.get_throttle_params()
        assert params["bwlimit"] == "0", (
            f"Full speed should map to bwlimit='0', got: {params['bwlimit']!r}"
        )


# ── Should throttle ───────────────────────────────────────────────────────────


class TestShouldThrottle:
    def test_should_throttle_during_business_hours(self, manager: BandwidthManager) -> None:
        """should_throttle() is True during business hours."""
        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(11)
            result = manager.should_throttle()
        assert result is True

    def test_should_not_throttle_off_hours_low_cpu(self, manager: BandwidthManager) -> None:
        """Off-hours + low CPU + empty stats → should_throttle=False."""
        with (
            patch("domains.bandwidth_manager.datetime") as mock_dt,
            patch("domains.bandwidth_manager.psutil") as mock_psutil,
        ):
            mock_dt.now.return_value = _mock_now(3)
            mock_psutil.cpu_percent.return_value = 10.0  # well below threshold
            result = manager.should_throttle()
        assert result is False

    def test_should_throttle_high_cpu(self, manager: BandwidthManager) -> None:
        """Off-hours but high CPU → should_throttle=True."""
        import domains.bandwidth_manager as _bm
        with (
            patch("domains.bandwidth_manager.datetime") as mock_dt,
            patch("domains.bandwidth_manager._PSUTIL_AVAILABLE", True),
            patch("domains.bandwidth_manager.psutil") as mock_psutil,
        ):
            mock_dt.now.return_value = _mock_now(3)
            mock_psutil.cpu_percent.return_value = 95.0  # above CPU_THROTTLE_THRESHOLD
            result = manager.should_throttle()
        assert result is True


# ── Task prioritisation ───────────────────────────────────────────────────────


class TestPrioritize:
    def _sample_tasks(self) -> list[dict]:
        return [
            {"type": "backfill",    "size_gb": 10, "added_at": "2026-01-01T00:00:00"},
            {"type": "catalog",     "size_gb": 5,  "added_at": "2026-01-02T00:00:00"},
            {"type": "new_episode", "size_gb": 2,  "added_at": "2026-01-03T00:00:00"},
            {"type": "catalog",     "size_gb": 3,  "added_at": "2026-01-04T00:00:00"},
        ]

    def test_prioritize_new_episodes_first(self, manager: BandwidthManager) -> None:
        """new_episode tasks must appear before catalog and backfill."""
        tasks = self._sample_tasks()
        ordered = manager.prioritize(tasks)

        types = [t["type"] for t in ordered]
        new_ep_idx = types.index("new_episode") if "new_episode" in types else -1
        first_catalog = next((i for i, t in enumerate(types) if t == "catalog"), len(types))

        assert new_ep_idx < first_catalog, (
            f"new_episode should come before catalog; got order: {types}"
        )

    def test_prioritize_backfill_last(self, manager: BandwidthManager) -> None:
        """backfill tasks must appear after catalog and new_episode."""
        tasks = self._sample_tasks()
        ordered = manager.prioritize(tasks)

        types = [t["type"] for t in ordered]
        backfill_idx = next((i for i, t in enumerate(types) if t == "backfill"), -1)
        last_non_backfill = max(
            (i for i, t in enumerate(types) if t != "backfill"),
            default=-1,
        )

        assert backfill_idx > last_non_backfill, (
            f"backfill should be last; got order: {types}"
        )

    def test_prioritize_preserves_all_tasks(self, manager: BandwidthManager) -> None:
        """prioritize() must return the same number of tasks as input."""
        tasks = self._sample_tasks()
        assert len(manager.prioritize(tasks)) == len(tasks)

    def test_prioritize_empty_list(self, manager: BandwidthManager) -> None:
        """prioritize([]) should return [] without raising."""
        assert manager.prioritize([]) == []

    def test_prioritize_unknown_type_goes_last(self, manager: BandwidthManager) -> None:
        """Tasks with unknown type should sort after known types."""
        tasks = [
            {"type": "new_episode", "size_gb": 1, "added_at": "2026-01-01"},
            {"type": "unknown_type", "size_gb": 1, "added_at": "2026-01-01"},
        ]
        ordered = manager.prioritize(tasks)
        types = [t["type"] for t in ordered]
        assert types[0] == "new_episode"
        assert types[-1] == "unknown_type"


# ── Custom window ─────────────────────────────────────────────────────────────


class TestCustomWindow:
    def test_add_window_returns_at_2am(self, manager: BandwidthManager) -> None:
        """A full-speed window from 2–6am should override the default at hour 3."""
        window = BandwidthWindow(
            start_hour=2, end_hour=6, max_mbps=FULL_SPEED_MBPS, priority=0
        )
        manager.add_window(window)

        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(3)
            limit = manager.get_current_limit()

        assert limit == FULL_SPEED_MBPS, (
            f"Custom full-speed window should give {FULL_SPEED_MBPS}, got {limit}"
        )

    def test_add_window_not_applied_outside_hours(self, manager: BandwidthManager) -> None:
        """A window from 2–6am should NOT apply at hour 14."""
        window = BandwidthWindow(
            start_hour=2, end_hour=6, max_mbps=FULL_SPEED_MBPS, priority=0
        )
        manager.add_window(window)

        with patch("domains.bandwidth_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _mock_now(14)
            limit = manager.get_current_limit()

        # Should fall back to THROTTLE_MBPS (business hours, no other window)
        assert limit == THROTTLE_MBPS, (
            f"Window should not apply at hour 14; expected THROTTLE_MBPS={THROTTLE_MBPS}, got {limit}"
        )
