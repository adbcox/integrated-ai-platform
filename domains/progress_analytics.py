"""domains/progress_analytics.py — Burndown/burnup data, velocity, and forecasting.

Derives completion velocity from git history or a persisted JSON fallback,
generates burndown/burnup series, and uses Monte Carlo simulation to forecast
completion dates with p50/p80/p95 confidence intervals.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import re
import statistics
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ITEMS_DEFAULT_DIR: str = "docs/roadmap/ITEMS"
HISTORY_DEFAULT_PATH: str = "artifacts/progress_history.json"
ARTIFACTS_DIR: str = "artifacts"
MONTE_CARLO_N: int = 1_000
HOURS_PER_DAY: float = 6.0
STATUS_DONE_VALUES = frozenset({"done", "completed", "accepted", "closed"})
STATUS_IN_PROGRESS_VALUES = frozenset({"in progress", "in-progress", "active", "wip"})


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class VelocityPoint:
    """A snapshot of roadmap progress on a single day.

    Attributes:
        date: Calendar date of this data point.
        items_completed: Items completed on this day.
        items_added: New items added on this day.
        cumulative_completed: Running total of completed items to this date.
        cumulative_total: Running total of all items (including new) to this date.
    """

    date: str  # ISO-8601 date string
    items_completed: int = 0
    items_added: int = 0
    cumulative_completed: int = 0
    cumulative_total: int = 0


@dataclass
class BurndownData:
    """Burndown chart data for a single sprint.

    Attributes:
        sprint_id: Sprint identifier string.
        start_date: Sprint start date (ISO-8601).
        end_date: Sprint end date (ISO-8601).
        total_points: Total story points / item count at sprint start.
        remaining_by_day: Remaining work at the end of each sprint day.
        ideal_line: Ideal linear burndown values for the same period.
    """

    sprint_id: str
    start_date: str
    end_date: str
    total_points: float
    remaining_by_day: List[float]
    ideal_line: List[float]


@dataclass
class ForecastResult:
    """Probabilistic completion date forecast.

    Attributes:
        p50_date: Median completion date (ISO-8601).
        p80_date: 80th-percentile completion date.
        p95_date: 95th-percentile completion date.
        current_velocity: Items completed per day (recent window).
        trend: 'improving', 'declining', or 'stable'.
    """

    p50_date: str
    p80_date: str
    p95_date: str
    current_velocity: float
    trend: str


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class ProgressAnalytics:
    """Compute roadmap progress metrics, burndown, burnup, and forecasts.

    Example::

        analytics = ProgressAnalytics()
        history = analytics.load_completion_history()
        velocity = analytics.get_velocity(window_days=7)
        forecast = analytics.forecast_completion(remaining_items=150)
    """

    def __init__(
        self,
        items_dir: str = ITEMS_DEFAULT_DIR,
        history_path: str = HISTORY_DEFAULT_PATH,
    ) -> None:
        """Initialise with paths to roadmap items and progress history.

        Args:
            items_dir: Path to RM-*.md files.
            history_path: Path to the JSON progress history fallback.
        """
        self.items_dir = items_dir
        self.history_path = history_path
        self._history: List[VelocityPoint] = []
        logger.info("ProgressAnalytics initialised")

    # ------------------------------------------------------------------
    # History loading
    # ------------------------------------------------------------------

    def _load_from_git(self) -> List[VelocityPoint]:
        """Derive daily completion counts from git log of the items directory.

        Runs: git log --follow --format='%ad' --date=short docs/roadmap/ITEMS/
        and counts commits per day as a proxy for items completed.

        Returns:
            List of VelocityPoint objects, or empty list on failure.
        """
        try:
            result = subprocess.run(
                ["git", "log", "--format=%ad", "--date=short", "--", self.items_dir],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                logger.debug("_load_from_git: git returned non-zero, using fallback")
                return []

            date_counts: Dict[str, int] = {}
            for line in result.stdout.splitlines():
                d = line.strip()
                if re.match(r"\d{4}-\d{2}-\d{2}", d):
                    date_counts[d] = date_counts.get(d, 0) + 1

            if not date_counts:
                return []

            sorted_dates = sorted(date_counts)
            cumulative = 0
            points: List[VelocityPoint] = []
            for d in sorted_dates:
                count = date_counts[d]
                cumulative += count
                points.append(VelocityPoint(
                    date=d,
                    items_completed=count,
                    items_added=count,
                    cumulative_completed=cumulative,
                    cumulative_total=cumulative,
                ))
            logger.info("_load_from_git: derived %d data points", len(points))
            return points
        except Exception as exc:
            logger.debug("_load_from_git: %s", exc)
            return []

    def _load_from_json(self) -> List[VelocityPoint]:
        """Load progress history from the JSON fallback file.

        Returns:
            List of VelocityPoint objects.
        """
        if not os.path.exists(self.history_path):
            return []
        try:
            with open(self.history_path, "r") as fh:
                data = json.load(fh)
            points = [VelocityPoint(**entry) for entry in data.get("history", [])]
            logger.info("_load_from_json: loaded %d points", len(points))
            return points
        except Exception as exc:
            logger.warning("_load_from_json: %s", exc)
            return []

    def load_completion_history(self) -> List[VelocityPoint]:
        """Load completion history, preferring git over JSON fallback.

        Returns:
            Sorted list of VelocityPoint objects (oldest first).
        """
        points = self._load_from_git()
        if not points:
            points = self._load_from_json()
        points.sort(key=lambda p: p.date)
        self._history = points
        return points

    # ------------------------------------------------------------------
    # Velocity
    # ------------------------------------------------------------------

    def get_velocity(self, window_days: int = 7) -> float:
        """Return the average items completed per day over the given window.

        Args:
            window_days: Rolling window size in calendar days.

        Returns:
            Items per day (float), or 0.0 if no history.
        """
        if not self._history:
            self.load_completion_history()
        if not self._history:
            return 0.0

        cutoff = (date.today() - timedelta(days=window_days)).isoformat()
        recent = [p for p in self._history if p.date >= cutoff]
        total_completed = sum(p.items_completed for p in recent)
        return round(total_completed / window_days, 4) if window_days > 0 else 0.0

    def get_velocity_trend(self) -> dict:
        """Return velocity averages for 7-day, 30-day, and all-time windows.

        Returns:
            Dict with '7d', '30d', and 'all_time' velocity floats.
        """
        return {
            "7d": self.get_velocity(7),
            "30d": self.get_velocity(30),
            "all_time": self.get_velocity(36500),
        }

    # ------------------------------------------------------------------
    # Burndown
    # ------------------------------------------------------------------

    def get_burndown(
        self,
        sprint_start: date,
        sprint_end: date,
        sprint_items: List[str],
    ) -> BurndownData:
        """Compute sprint burndown data.

        Args:
            sprint_start: First day of the sprint.
            sprint_end: Last day of the sprint.
            sprint_items: List of item IDs included in the sprint.

        Returns:
            BurndownData with actual remaining and ideal line series.
        """
        total_points = float(len(sprint_items))
        n_days = (sprint_end - sprint_start).days + 1
        if n_days <= 0:
            n_days = 1

        # Ideal linear burndown
        ideal_line = [round(total_points * (1 - i / (n_days - 1)), 2) for i in range(n_days)] if n_days > 1 else [0.0]

        # Actual remaining: proxy from velocity history during sprint
        sprint_id = f"{sprint_start.isoformat()}_{sprint_end.isoformat()}"
        start_str = sprint_start.isoformat()
        end_str = sprint_end.isoformat()

        daily_completed = {
            p.date: p.items_completed
            for p in self._history
            if start_str <= p.date <= end_str
        }

        remaining = total_points
        remaining_by_day: List[float] = []
        for i in range(n_days):
            day_str = (sprint_start + timedelta(days=i)).isoformat()
            completed_today = daily_completed.get(day_str, 0)
            remaining = max(0.0, remaining - completed_today)
            remaining_by_day.append(round(remaining, 2))

        return BurndownData(
            sprint_id=sprint_id,
            start_date=start_str,
            end_date=end_str,
            total_points=total_points,
            remaining_by_day=remaining_by_day,
            ideal_line=ideal_line,
        )

    # ------------------------------------------------------------------
    # Burnup
    # ------------------------------------------------------------------

    def get_burnup(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> dict:
        """Return burnup chart data (total scope vs completed work over time).

        Args:
            start: Start date for the series (defaults to earliest history entry).
            end: End date for the series (defaults to today).

        Returns:
            Dict with 'dates', 'completed', and 'total' parallel lists.
        """
        if not self._history:
            self.load_completion_history()

        if not self._history:
            return {"dates": [], "completed": [], "total": []}

        start_str = start.isoformat() if start else self._history[0].date
        end_str = end.isoformat() if end else date.today().isoformat()

        history_in_range = [p for p in self._history if start_str <= p.date <= end_str]

        dates: List[str] = []
        completed: List[int] = []
        total: List[int] = []

        for point in history_in_range:
            dates.append(point.date)
            completed.append(point.cumulative_completed)
            total.append(point.cumulative_total)

        return {"dates": dates, "completed": completed, "total": total}

    # ------------------------------------------------------------------
    # Forecasting
    # ------------------------------------------------------------------

    def forecast_completion(
        self,
        remaining_items: int,
        velocity: Optional[float] = None,
    ) -> ForecastResult:
        """Forecast completion dates using Monte Carlo simulation.

        Samples velocity from historical distribution (mean ± std_dev) over
        MONTE_CARLO_N simulations to produce p50/p80/p95 date estimates.

        Args:
            remaining_items: Number of items yet to be completed.
            velocity: Override daily velocity. If None, uses get_velocity(7).

        Returns:
            ForecastResult with p50/p80/p95 dates and trend assessment.
        """
        if velocity is None:
            velocity = self.get_velocity(7) or 1.0

        # Compute velocity std_dev from history
        recent_daily = [p.items_completed for p in self._history if p.items_completed > 0]
        if len(recent_daily) >= 3:
            try:
                vel_std = statistics.stdev(recent_daily)
            except statistics.StatisticsError:
                vel_std = velocity * 0.3
        else:
            vel_std = velocity * 0.3

        rng = random.Random(42)
        all_days: List[float] = []

        for _ in range(MONTE_CARLO_N):
            remaining = remaining_items
            days = 0
            while remaining > 0 and days < 3_650:  # 10-year cap
                sampled_v = max(0.1, rng.gauss(velocity, vel_std))
                remaining -= sampled_v
                days += 1
            all_days.append(float(days))

        all_days.sort()
        n = len(all_days)
        today = date.today()

        def _date_offset(percentile: float) -> str:
            days = int(all_days[int(n * percentile)])
            return (today + timedelta(days=days)).isoformat()

        # Trend assessment
        v_7 = self.get_velocity(7)
        v_30 = self.get_velocity(30)
        if v_7 > v_30 * 1.1:
            trend = "improving"
        elif v_7 < v_30 * 0.9:
            trend = "declining"
        else:
            trend = "stable"

        return ForecastResult(
            p50_date=_date_offset(0.50),
            p80_date=_date_offset(0.80),
            p95_date=_date_offset(0.95),
            current_velocity=round(velocity, 4),
            trend=trend,
        )

    # ------------------------------------------------------------------
    # Milestone risk
    # ------------------------------------------------------------------

    def get_milestone_risk(
        self,
        milestone_items: List[str],
        target_date: date,
    ) -> float:
        """Estimate the probability that a milestone will be missed.

        Args:
            milestone_items: Item IDs included in the milestone.
            target_date: Target completion date.

        Returns:
            Risk score from 0.0 (no risk) to 1.0 (almost certain miss).
        """
        remaining = len(milestone_items)
        if remaining == 0:
            return 0.0

        velocity = self.get_velocity(14) or 0.5
        days_available = (target_date - date.today()).days
        expected_completion = remaining / velocity if velocity > 0 else float("inf")

        if expected_completion <= days_available:
            # Ahead of schedule — low risk but not zero
            risk = max(0.0, 0.1 - (days_available - expected_completion) / days_available)
        else:
            overshoot = expected_completion - days_available
            risk = min(1.0, overshoot / expected_completion)

        return round(risk, 4)

    # ------------------------------------------------------------------
    # Category breakdown
    # ------------------------------------------------------------------

    def get_category_breakdown(self) -> Dict[str, dict]:
        """Scan the items directory and count per-category completion stats.

        Returns:
            Dict mapping category → {total, done, in_progress, pct_complete}.
        """
        categories: Dict[str, Dict[str, int]] = {}
        items_path = Path(self.items_dir)

        if not items_path.exists():
            return {}

        for md_file in items_path.glob("RM-*.md"):
            item_id = md_file.stem
            parts = item_id.split("-")
            category = parts[1] if len(parts) >= 2 else "UNKNOWN"
            cat = categories.setdefault(category, {"total": 0, "done": 0, "in_progress": 0})
            cat["total"] += 1
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                status_match = re.search(r"status[:\s]+([^\n]+)", text, re.IGNORECASE)
                status = status_match.group(1).strip().lower() if status_match else "backlog"
                if status in STATUS_DONE_VALUES:
                    cat["done"] += 1
                elif status in STATUS_IN_PROGRESS_VALUES:
                    cat["in_progress"] += 1
            except Exception:
                pass

        result: Dict[str, dict] = {}
        for cat_name, counts in categories.items():
            total = counts["total"] or 1
            result[cat_name] = {
                **counts,
                "pct_complete": round(counts["done"] / total * 100, 1),
            }
        return result

    # ------------------------------------------------------------------
    # Dashboard aggregation
    # ------------------------------------------------------------------

    def to_dashboard_data(self) -> dict:
        """Aggregate all chart data into a single dict for dashboard rendering.

        Returns:
            Dict with keys: velocity_trend, burnup, category_breakdown,
            forecast, and history (list of VelocityPoint dicts).
        """
        if not self._history:
            self.load_completion_history()

        forecast = self.forecast_completion(remaining_items=100)

        return {
            "velocity_trend": self.get_velocity_trend(),
            "burnup": self.get_burnup(),
            "category_breakdown": self.get_category_breakdown(),
            "forecast": {
                "p50_date": forecast.p50_date,
                "p80_date": forecast.p80_date,
                "p95_date": forecast.p95_date,
                "current_velocity": forecast.current_velocity,
                "trend": forecast.trend,
            },
            "history": [
                {
                    "date": p.date,
                    "items_completed": p.items_completed,
                    "cumulative_completed": p.cumulative_completed,
                    "cumulative_total": p.cumulative_total,
                }
                for p in self._history
            ],
        }
