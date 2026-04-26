"""domains/release_scheduler.py — Show release pattern learning and prediction.

Learns the day-of-week and time-of-day patterns for each tracked show, predicts
upcoming release dates, detects delayed episodes, and can pre-warm search
engines ahead of expected drops.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------
try:
    import requests  # type: ignore
    _REQUESTS_AVAILABLE = True
except ImportError:
    requests = None  # type: ignore[assignment]
    _REQUESTS_AVAILABLE = False

try:
    from framework.event_bus import publish_event  # type: ignore
except ImportError:
    def publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        logger.debug("event_bus unavailable — skipped event: %s", name)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ARTIFACTS_DIR: str = "artifacts"
PATTERNS_FILE: str = os.path.join(ARTIFACTS_DIR, "release_patterns.json")
CONFIDENCE_DENOMINATOR: int = 5           # approaches 1.0 after ~20 releases
MIN_RELEASES_FOR_PATTERN: int = 2        # need at least 2 data points
DEFAULT_RELEASE_HOUR: int = 8            # 08:00 UTC — common streaming drop time
PROWLARR_SEARCH_PATH: str = "/api/v1/search"
REQUEST_TIMEOUT: int = 10


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class ReleasePattern:
    """Learned release cadence for a single show.

    Attributes:
        show_id: Unique show identifier (e.g. Sonarr series ID).
        show_name: Human-readable show name.
        typical_day_of_week: Most common ISO weekday (0=Mon, 6=Sun).
        typical_hour: Most common UTC hour of release.
        avg_delay_hours: Average hours between air-date and indexer availability.
        confidence: Confidence in the pattern (n / (n + CONFIDENCE_DENOMINATOR)).
    """

    show_id: str
    show_name: str
    typical_day_of_week: int = 0
    typical_hour: int = DEFAULT_RELEASE_HOUR
    avg_delay_hours: float = 2.0
    confidence: float = 0.0


@dataclass
class EpisodePrediction:
    """A predicted release date for a forthcoming episode.

    Attributes:
        show_id: Unique show identifier.
        season: Season number.
        episode: Episode number within the season.
        predicted_at: Predicted UTC release datetime.
        confidence: Confidence score from the ReleasePattern.
        early_check_at: Suggested early search trigger datetime.
    """

    show_id: str
    season: int
    episode: int
    predicted_at: datetime
    confidence: float
    early_check_at: datetime


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
class ReleaseScheduler:
    """Learn and predict episode release dates for monitored shows.

    Example::

        sched = ReleaseScheduler()
        sched.record_release("12345", "Breaking Bad", datetime(2024, 1, 7, 3, 0), 5, 1)
        prediction = sched.predict_next("12345", last_season=5, last_episode=1)
    """

    def __init__(self) -> None:
        self._patterns: Dict[str, ReleasePattern] = {}
        self._history: Dict[str, List[Tuple[datetime, int, int]]] = {}
        self._load_patterns()
        logger.info("ReleaseScheduler initialised with %d patterns", len(self._patterns))

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_patterns(self) -> None:
        """Load persisted release patterns from artifacts/release_patterns.json."""
        if not os.path.exists(PATTERNS_FILE):
            return
        try:
            with open(PATTERNS_FILE, "r") as fh:
                data = json.load(fh)
            for show_id, attrs in data.get("patterns", {}).items():
                self._patterns[show_id] = ReleasePattern(**attrs)
            for show_id, raw_history in data.get("history", {}).items():
                self._history[show_id] = [
                    (datetime.fromisoformat(ts), s, ep)
                    for ts, s, ep in raw_history
                ]
            logger.info("_load_patterns: loaded %d patterns", len(self._patterns))
        except Exception as exc:
            logger.warning("_load_patterns: %s", exc)

    def _save_patterns(self) -> None:
        """Persist patterns and history to artifacts/release_patterns.json."""
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            history_serialisable = {
                show_id: [(ts.isoformat(), s, ep) for ts, s, ep in entries]
                for show_id, entries in self._history.items()
            }
            data = {
                "patterns": {k: asdict(v) for k, v in self._patterns.items()},
                "history": history_serialisable,
            }
            with open(PATTERNS_FILE, "w") as fh:
                json.dump(data, fh, indent=2, default=str)
        except Exception as exc:
            logger.warning("_save_patterns: %s", exc)

    # ------------------------------------------------------------------
    # Learning
    # ------------------------------------------------------------------

    def _most_common(self, values: List[int]) -> int:
        """Return the most frequent value in a list.

        Args:
            values: List of integers.

        Returns:
            Mode of the list, or 0 if empty.
        """
        if not values:
            return 0
        counts: Dict[int, int] = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return max(counts, key=counts.__getitem__)

    def record_release(
        self,
        show_id: str,
        show_name: str,
        released_at: datetime,
        season: int,
        episode: int,
    ) -> None:
        """Record an observed release and update the learned pattern.

        Confidence approaches 1.0 as more releases are observed:
        confidence = n / (n + CONFIDENCE_DENOMINATOR).

        Args:
            show_id: Unique show identifier.
            show_name: Human-readable show name.
            released_at: UTC datetime the release appeared on the indexer.
            season: Season number.
            episode: Episode number.
        """
        # Append to raw history
        history = self._history.setdefault(show_id, [])
        history.append((released_at, season, episode))

        # Extract pattern from history
        days = [ts.weekday() for ts, _, _ in history]
        hours = [ts.hour for ts, _, _ in history]
        n = len(history)
        confidence = n / (n + CONFIDENCE_DENOMINATOR)

        # Compute average delay relative to previous release (if available)
        delays: List[float] = []
        for i in range(1, n):
            prev_ts = history[i - 1][0]
            curr_ts = history[i][0]
            delay_h = (curr_ts - prev_ts).total_seconds() / 3600.0
            if 0 < delay_h < 24 * 7 * 2:  # sanity: within 2 weeks
                delays.append(delay_h)

        avg_delay = statistics.mean(delays) if delays else 2.0

        self._patterns[show_id] = ReleasePattern(
            show_id=show_id,
            show_name=show_name,
            typical_day_of_week=self._most_common(days),
            typical_hour=self._most_common(hours),
            avg_delay_hours=round(avg_delay, 2),
            confidence=round(confidence, 4),
        )

        logger.info(
            "record_release: '%s' S%02dE%02d → pattern day=%d hour=%d conf=%.2f",
            show_name, season, episode,
            self._patterns[show_id].typical_day_of_week,
            self._patterns[show_id].typical_hour,
            confidence,
        )
        publish_event("media.release.predicted", {
            "show_id": show_id,
            "show_name": show_name,
            "confidence": confidence,
        })
        self._save_patterns()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_pattern(self, show_id: str) -> Optional[ReleasePattern]:
        """Return the learned pattern for a show, or None if unknown.

        Args:
            show_id: Unique show identifier.

        Returns:
            ReleasePattern or None.
        """
        return self._patterns.get(show_id)

    def predict_next(
        self,
        show_id: str,
        last_season: int,
        last_episode: int,
    ) -> Optional[EpisodePrediction]:
        """Predict the release datetime for the next episode.

        Uses the learned weekly cadence pattern to project when the next
        episode should appear. Returns None if no pattern is available.

        Args:
            show_id: Unique show identifier.
            last_season: Season number of the most recently released episode.
            last_episode: Episode number of the most recently released episode.

        Returns:
            EpisodePrediction or None if insufficient data.
        """
        pattern = self._patterns.get(show_id)
        history = self._history.get(show_id, [])

        if pattern is None or len(history) < MIN_RELEASES_FOR_PATTERN:
            logger.debug("predict_next: insufficient data for show_id=%s", show_id)
            return None

        last_ts, _, _ = history[-1]
        # Find next occurrence of the typical day, at least 1 day out
        now = datetime.now(timezone.utc)
        base = last_ts.replace(tzinfo=timezone.utc) if last_ts.tzinfo is None else last_ts
        candidate = base + timedelta(days=1)
        for _ in range(14):  # search within 2 weeks
            if candidate.weekday() == pattern.typical_day_of_week:
                break
            candidate += timedelta(days=1)

        predicted_at = candidate.replace(
            hour=pattern.typical_hour,
            minute=0,
            second=0,
            microsecond=0,
        )
        early_check_at = predicted_at - timedelta(hours=1)

        next_episode = last_episode + 1
        next_season = last_season

        return EpisodePrediction(
            show_id=show_id,
            season=next_season,
            episode=next_episode,
            predicted_at=predicted_at,
            confidence=pattern.confidence,
            early_check_at=early_check_at,
        )

    def get_upcoming_releases(self, days_ahead: int = 7) -> List[EpisodePrediction]:
        """Return predicted releases within the next N days.

        Args:
            days_ahead: Number of days to look ahead.

        Returns:
            List of EpisodePredictions sorted by predicted_at ascending.
        """
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        upcoming: List[EpisodePrediction] = []

        for show_id, history in self._history.items():
            if not history:
                continue
            _, last_s, last_ep = history[-1]
            pred = self.predict_next(show_id, last_s, last_ep)
            if pred and pred.predicted_at.replace(tzinfo=timezone.utc) <= cutoff:
                upcoming.append(pred)

        upcoming.sort(key=lambda p: p.predicted_at)
        return upcoming

    def check_delayed(self, threshold_hours: float = 24.0) -> List[str]:
        """Return show IDs where the expected release is overdue.

        A show is considered delayed when the predicted release time has passed
        by more than threshold_hours and no new release has been recorded.

        Args:
            threshold_hours: Hours past the predicted time before marking delayed.

        Returns:
            List of show_id strings for delayed shows.
        """
        now = datetime.now(timezone.utc)
        delayed: List[str] = []

        for show_id, history in self._history.items():
            if not history:
                continue
            _, last_s, last_ep = history[-1]
            pred = self.predict_next(show_id, last_s, last_ep)
            if pred is None:
                continue
            pred_time = pred.predicted_at
            if pred_time.tzinfo is None:
                pred_time = pred_time.replace(tzinfo=timezone.utc)
            overdue_hours = (now - pred_time).total_seconds() / 3600.0
            if overdue_hours > threshold_hours:
                delayed.append(show_id)
                publish_event("media.release.delayed", {
                    "show_id": show_id,
                    "overdue_hours": round(overdue_hours, 1),
                })
                logger.warning(
                    "check_delayed: show_id=%s overdue by %.1fh", show_id, overdue_hours
                )

        return delayed

    def pre_warm_search(self, show_id: str, minutes_before: int = 60) -> bool:
        """Trigger an early Prowlarr search before the expected release.

        Calls POST /api/v1/search on the Prowlarr instance configured via the
        PROWLARR_URL environment variable. Silently skips if unavailable.

        Args:
            show_id: Show identifier to search for.
            minutes_before: Minutes ahead of predicted release to trigger.

        Returns:
            True if the search was successfully triggered.
        """
        prowlarr_url = os.environ.get("PROWLARR_URL", "")
        prowlarr_key = os.environ.get("PROWLARR_API_KEY", "")
        if not prowlarr_url or not _REQUESTS_AVAILABLE:
            logger.debug("pre_warm_search: PROWLARR_URL not set or requests unavailable")
            return False

        pattern = self._patterns.get(show_id)
        show_name = pattern.show_name if pattern else show_id

        try:
            payload = {"query": show_name, "categories": [5000, 5030, 5040]}
            resp = requests.post(
                f"{prowlarr_url.rstrip('/')}{PROWLARR_SEARCH_PATH}",
                json=payload,
                headers={"X-Api-Key": prowlarr_key},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            logger.info("pre_warm_search: triggered Prowlarr search for '%s'", show_name)
            return True
        except Exception as exc:
            logger.warning("pre_warm_search: %s", exc)
            return False

    def get_calendar_data(self) -> List[dict]:
        """Return upcoming releases in calendar format for dashboards.

        Returns:
            List of dicts: {date, show, episode (SxxEyy), confidence}.
        """
        upcoming = self.get_upcoming_releases(days_ahead=14)
        calendar: List[dict] = []
        for pred in upcoming:
            pattern = self._patterns.get(pred.show_id)
            show_name = pattern.show_name if pattern else pred.show_id
            calendar.append({
                "date": pred.predicted_at.date().isoformat(),
                "show": show_name,
                "episode": f"S{pred.season:02d}E{pred.episode:02d}",
                "confidence": round(pred.confidence, 3),
                "predicted_at": pred.predicted_at.isoformat(),
            })
        return calendar
