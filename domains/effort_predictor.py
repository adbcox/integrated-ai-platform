"""domains/effort_predictor.py — Roadmap effort estimation with velocity calibration.

Predicts hours for roadmap items based on LOE, complexity, and historical
velocity data. Monte Carlo simulation provides p50/p80/p95 completion estimates.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ARTIFACTS_DIR: str = "artifacts"
HISTORY_FILE_DEFAULT: str = os.path.join(ARTIFACTS_DIR, "velocity_history.json")

LOE_BASE_HOURS: Dict[str, float] = {
    "S": 4.0,
    "M": 16.0,
    "L": 40.0,
    "XL": 80.0,
}
RISK_MULTIPLIERS: Dict[str, float] = {
    "low": 1.0,
    "medium": 1.3,
    "high": 1.7,
    "critical": 2.2,
}
SUBTASK_HOUR_FACTOR: float = 0.1       # each subtask adds 10% to base estimate
P80_MULTIPLIER: float = 1.3
P95_MULTIPLIER: float = 1.8
HOURS_PER_DAY: float = 6.0            # productive hours per working day
WORK_DAYS_PER_WEEK: int = 5
MONTE_CARLO_DEFAULT_N: int = 1_000
MIN_HISTORY_FOR_CALIBRATION: int = 3   # need at least 3 records to calibrate


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class VelocityRecord:
    """A historical record of actual versus estimated effort.

    Attributes:
        item_id: Roadmap item ID (e.g. RM-ML-001).
        loe_estimate: LOE bucket used for estimation ('S', 'M', 'L', 'XL').
        actual_hours: Actual hours spent completing the item.
        complexity_score: 0–10 complexity rating assigned at planning time.
        completed_at: ISO-8601 timestamp of completion.
    """

    item_id: str
    loe_estimate: str
    actual_hours: float
    complexity_score: float = 5.0
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SprintCapacity:
    """Capacity and utilisation summary for a planning sprint.

    Attributes:
        sprint_id: Sprint identifier string.
        available_hours: Total productive hours available in the sprint.
        committed_hours: Hours committed to planned items.
        completed_hours: Actual hours spent on completed items.
        velocity: Items completed per sprint (raw count).
    """

    sprint_id: str
    available_hours: float
    committed_hours: float = 0.0
    completed_hours: float = 0.0
    velocity: float = 0.0


# ---------------------------------------------------------------------------
# Predictor
# ---------------------------------------------------------------------------
class EffortPredictor:
    """Estimate future effort using historical calibration and Monte Carlo.

    Example::

        predictor = EffortPredictor()
        predictor.record_completion("RM-ML-001", "M", actual_hours=22.0,
                                    subtask_count=3, risk_level="medium")
        p50, p80, p95 = predictor.predict_hours("M", subtask_count=3, risk_level="medium")
    """

    def __init__(self, history_path: str = HISTORY_FILE_DEFAULT) -> None:
        """Initialise the predictor and load historical velocity data.

        Args:
            history_path: Path to the JSON file storing VelocityRecord history.
        """
        self.history_path = history_path
        self._history: List[VelocityRecord] = []
        self._sprints: Dict[str, SprintCapacity] = {}
        self._load_history()
        logger.info(
            "EffortPredictor initialised with %d historical records", len(self._history)
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_history(self) -> None:
        """Load VelocityRecord list from the history JSON file."""
        if not os.path.exists(self.history_path):
            return
        try:
            with open(self.history_path, "r") as fh:
                data = json.load(fh)
            self._history = [VelocityRecord(**r) for r in data.get("records", [])]
            for sprint_id, attrs in data.get("sprints", {}).items():
                self._sprints[sprint_id] = SprintCapacity(**attrs)
            logger.info("_load_history: loaded %d records", len(self._history))
        except Exception as exc:
            logger.warning("_load_history: %s", exc)

    def _save_history(self) -> None:
        """Persist VelocityRecord and SprintCapacity data to JSON."""
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            data = {
                "records": [asdict(r) for r in self._history],
                "sprints": {sid: asdict(s) for sid, s in self._sprints.items()},
            }
            with open(self.history_path, "w") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:
            logger.warning("_save_history: %s", exc)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_completion(
        self,
        item_id: str,
        loe_estimate: str,
        actual_hours: float,
        subtask_count: int = 0,
        risk_level: str = "medium",
    ) -> None:
        """Record the completion of a roadmap item with its actual effort.

        Args:
            item_id: Roadmap item identifier.
            loe_estimate: The LOE bucket used ('S', 'M', 'L', 'XL').
            actual_hours: Actual hours spent.
            subtask_count: Number of subtasks the item was broken into.
            risk_level: Risk level at planning time ('low', 'medium', 'high', 'critical').
        """
        complexity = subtask_count * 1.5 + RISK_MULTIPLIERS.get(risk_level, 1.0) * 2.0
        record = VelocityRecord(
            item_id=item_id,
            loe_estimate=loe_estimate.upper(),
            actual_hours=actual_hours,
            complexity_score=min(complexity, 10.0),
        )
        self._history.append(record)
        self._save_history()
        logger.info(
            "record_completion: %s loe=%s actual=%.1fh", item_id, loe_estimate, actual_hours
        )

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def _calibration_factor(self, loe: str) -> float:
        """Compute the ratio of actual to estimated hours for a given LOE.

        Falls back to 1.0 (no correction) when insufficient history exists.

        Args:
            loe: LOE bucket ('S', 'M', 'L', 'XL').

        Returns:
            Calibration multiplier (>1 means historically underestimated).
        """
        loe = loe.upper()
        base = LOE_BASE_HOURS.get(loe, 16.0)
        matching = [r for r in self._history if r.loe_estimate == loe]
        if len(matching) < MIN_HISTORY_FOR_CALIBRATION:
            return 1.0
        ratios = [r.actual_hours / base for r in matching]
        return statistics.mean(ratios)

    def _history_std_dev(self, loe: str) -> float:
        """Compute the standard deviation of calibration ratios for a LOE bucket.

        Args:
            loe: LOE bucket.

        Returns:
            Standard deviation of actual/estimate ratios, or 0.3 as default.
        """
        loe = loe.upper()
        base = LOE_BASE_HOURS.get(loe, 16.0)
        matching = [r for r in self._history if r.loe_estimate == loe]
        if len(matching) < MIN_HISTORY_FOR_CALIBRATION:
            return 0.3  # default uncertainty
        ratios = [r.actual_hours / base for r in matching]
        try:
            return statistics.stdev(ratios)
        except statistics.StatisticsError:
            return 0.3

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_hours(
        self,
        loe: str,
        subtask_count: int = 0,
        risk_level: str = "medium",
        description: str = "",
    ) -> Tuple[float, float, float]:
        """Predict effort in hours as a three-point estimate.

        Args:
            loe: LOE bucket ('S', 'M', 'L', 'XL').
            subtask_count: Number of planned subtasks.
            risk_level: Risk level ('low', 'medium', 'high', 'critical').
            description: Optional description (reserved for future NLP features).

        Returns:
            Tuple of (p50_hours, p80_hours, p95_hours).
        """
        loe = loe.upper()
        base = LOE_BASE_HOURS.get(loe, 16.0)
        risk_mult = RISK_MULTIPLIERS.get(risk_level.lower(), 1.3)
        subtask_adj = 1.0 + subtask_count * SUBTASK_HOUR_FACTOR
        calibration = self._calibration_factor(loe)
        std_dev = self._history_std_dev(loe)

        p50 = base * risk_mult * subtask_adj * calibration

        # If we have history, derive p80/p95 from distribution
        if std_dev > 0 and len([r for r in self._history if r.loe_estimate == loe]) >= MIN_HISTORY_FOR_CALIBRATION:
            p80 = p50 * (1 + std_dev)
            p95 = p50 * (1 + std_dev * 2)
        else:
            p80 = p50 * P80_MULTIPLIER
            p95 = p50 * P95_MULTIPLIER

        logger.debug(
            "predict_hours: loe=%s risk=%s subtasks=%d → p50=%.1f p80=%.1f p95=%.1f",
            loe, risk_level, subtask_count, p50, p80, p95,
        )
        return (round(p50, 1), round(p80, 1), round(p95, 1))

    # ------------------------------------------------------------------
    # Sprint planning
    # ------------------------------------------------------------------

    def get_sprint_capacity(self, sprint_id: str) -> SprintCapacity:
        """Return existing or default sprint capacity.

        Args:
            sprint_id: Sprint identifier.

        Returns:
            SprintCapacity for the given sprint.
        """
        if sprint_id not in self._sprints:
            self._sprints[sprint_id] = SprintCapacity(
                sprint_id=sprint_id,
                available_hours=HOURS_PER_DAY * WORK_DAYS_PER_WEEK * 2,  # 2-week sprint
            )
        return self._sprints[sprint_id]

    def forecast_sprint(
        self,
        items: List[dict],
        available_hours: float,
    ) -> dict:
        """Forecast which items fit within available sprint capacity.

        Args:
            items: List of dicts with keys: id, loe, risk_level, subtask_count.
            available_hours: Total productive hours available in the sprint.

        Returns:
            Dict with committed_items, overflow_items, confidence, completion_date.
        """
        committed: List[dict] = []
        overflow: List[dict] = []
        total_p50 = 0.0
        total_p80 = 0.0

        for item in items:
            p50, p80, _ = self.predict_hours(
                loe=item.get("loe", "M"),
                subtask_count=int(item.get("subtask_count", 0)),
                risk_level=item.get("risk_level", "medium"),
            )
            if total_p50 + p50 <= available_hours:
                committed.append({**item, "estimated_p50": p50, "estimated_p80": p80})
                total_p50 += p50
                total_p80 += p80
            else:
                overflow.append(item)

        confidence = max(0.0, min(1.0, 1.0 - (total_p80 - available_hours) / (available_hours + 1)))
        days_needed = math.ceil(total_p80 / HOURS_PER_DAY)
        completion_date = (datetime.utcnow() + timedelta(days=days_needed)).date().isoformat()

        return {
            "committed_items": committed,
            "overflow_items": overflow,
            "confidence": round(confidence, 3),
            "completion_date": completion_date,
            "total_p50_hours": round(total_p50, 1),
            "total_p80_hours": round(total_p80, 1),
        }

    def monte_carlo(
        self,
        items: List[dict],
        n_simulations: int = MONTE_CARLO_DEFAULT_N,
    ) -> dict:
        """Run a Monte Carlo simulation for multi-item completion dates.

        Samples from a log-normal distribution centred on p50 for each item
        in each simulation, then aggregates total days to completion.

        Args:
            items: List of dicts with keys: loe, risk_level, subtask_count.
            n_simulations: Number of simulation runs.

        Returns:
            Dict with p50_days, p80_days, p95_days.
        """
        all_total_hours: List[float] = []
        rng = random.Random(42)  # reproducible

        for _ in range(n_simulations):
            total_hours = 0.0
            for item in items:
                p50, p80, _ = self.predict_hours(
                    loe=item.get("loe", "M"),
                    subtask_count=int(item.get("subtask_count", 0)),
                    risk_level=item.get("risk_level", "medium"),
                )
                # Sample from log-normal: mu/sigma derived from p50/p80
                if p50 > 0:
                    sigma = math.log(p80 / p50) if p80 > p50 else 0.2
                    mu = math.log(p50)
                    sample = rng.lognormvariate(mu, sigma)
                else:
                    sample = 0.0
                total_hours += sample
            all_total_hours.append(total_hours)

        all_total_hours.sort()
        n = len(all_total_hours)

        def _days(h: float) -> int:
            return math.ceil(h / HOURS_PER_DAY)

        p50_h = all_total_hours[int(n * 0.50)]
        p80_h = all_total_hours[int(n * 0.80)]
        p95_h = all_total_hours[int(n * 0.95)]

        logger.info(
            "monte_carlo: %d items × %d sims → p50=%d days, p80=%d days, p95=%d days",
            len(items), n_simulations, _days(p50_h), _days(p80_h), _days(p95_h),
        )
        return {
            "p50_days": _days(p50_h),
            "p80_days": _days(p80_h),
            "p95_days": _days(p95_h),
        }

    # ------------------------------------------------------------------
    # Velocity trends
    # ------------------------------------------------------------------

    def get_velocity_trend(self) -> dict:
        """Compute average items completed per day over rolling windows.

        Returns:
            Dict with '7d', '30d', and 'all_time' velocity floats.
        """
        now = datetime.utcnow()
        windows = {"7d": 7, "30d": 30, "all_time": 36500}
        result: Dict[str, float] = {}

        for key, days in windows.items():
            cutoff = now - timedelta(days=days)
            recent = [
                r for r in self._history
                if datetime.fromisoformat(r.completed_at) >= cutoff
            ]
            velocity = len(recent) / days if days < 36500 else (len(self._history) or 0)
            result[key] = round(velocity, 4)

        return result
