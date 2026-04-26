"""domains/source_ranker.py — Torrent/usenet source reliability ranking.

Tracks each source's historical success rate, download speed, and quality
score using exponential moving averages. Produces ordered fallback chains and
disables consistently poor sources automatically.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional integrations
# ---------------------------------------------------------------------------
try:
    from framework.event_bus import publish_event  # type: ignore
except ImportError:
    def publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        logger.debug("event_bus unavailable — skipped event: %s", name)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMA_ALPHA: float = 0.1                       # Exponential moving average smoothing factor
DEFAULT_SUCCESS_RATE: float = 1.0            # Optimistic start for new sources
DEFAULT_SPEED_MBPS: float = 10.0
DEFAULT_QUALITY_SCORE: float = 7.0
COMPOSITE_WEIGHT_SUCCESS: float = 0.4
COMPOSITE_WEIGHT_SPEED: float = 0.3
COMPOSITE_WEIGHT_QUALITY: float = 0.3
POOR_SOURCE_THRESHOLD: float = 0.7          # Disable sources below this composite score
HISTORY_MAXLEN: int = 100                    # Per-source history entries
ARTIFACTS_DIR: str = "artifacts"
HEALTH_FILE: str = os.path.join(ARTIFACTS_DIR, "source_health.json")
SPEED_NORMALISATION_CAP: float = 100.0      # Mbps — cap for normalisation


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class SourceHealth:
    """Running health statistics for a single download source.

    Attributes:
        name: Human-readable source name.
        url: Base URL or endpoint.
        success_rate: EMA of download success (0–1).
        avg_speed_mbps: EMA of download speed in Mbps.
        avg_quality_score: EMA of quality scores received (0–10).
        uptime_pct: Percentage of checks that returned a successful response.
        last_checked: ISO-8601 timestamp of last health update.
        enabled: Whether this source is active.
    """

    name: str
    url: str
    success_rate: float = DEFAULT_SUCCESS_RATE
    avg_speed_mbps: float = DEFAULT_SPEED_MBPS
    avg_quality_score: float = DEFAULT_QUALITY_SCORE
    uptime_pct: float = 100.0
    last_checked: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    enabled: bool = True
    type: str = "torrent"  # "torrent" | "usenet"

    def composite_score(self) -> float:
        """Compute the composite ranking score for this source.

        Returns:
            Weighted sum of success_rate, normalised speed, and quality.
        """
        speed_norm = min(self.avg_speed_mbps / SPEED_NORMALISATION_CAP, 1.0)
        quality_norm = self.avg_quality_score / 10.0
        return (
            self.success_rate * COMPOSITE_WEIGHT_SUCCESS
            + speed_norm * COMPOSITE_WEIGHT_SPEED
            + quality_norm * COMPOSITE_WEIGHT_QUALITY
        )


@dataclass
class RankedResult:
    """A search result annotated with source ranking metadata.

    Attributes:
        result_dict: Original result payload from the source.
        source_name: Name of the source that produced the result.
        rank_score: Composite rank score for sorting.
        estimated_quality: Estimated quality score for this specific result.
    """

    result_dict: dict
    source_name: str
    rank_score: float
    estimated_quality: float


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------
class SourceRanker:
    """Aggregate, track, and rank download sources by composite health score.

    Example::

        ranker = SourceRanker()
        ranker.register_source("NZBGeek", "https://api.nzbgeek.info", type="usenet")
        ranker.record_result("NZBGeek", success=True, speed_mbps=25.0, quality_score=8.5)
        print(ranker.rank_sources())
    """

    def __init__(self, config_path: str = "config/sources.yaml") -> None:
        """Initialise the ranker and load persisted health data.

        Args:
            config_path: Optional YAML config for pre-configured sources.
        """
        self._sources: Dict[str, SourceHealth] = {}
        self._source_history: Dict[str, Deque[Tuple[float, bool, Optional[float], Optional[float]]]] = {}
        self._uptime_checks: Dict[str, List[bool]] = {}
        self._load_health()
        logger.info("SourceRanker initialised with %d sources", len(self._sources))

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_health(self) -> None:
        """Load persisted source health from artifacts/source_health.json."""
        if not os.path.exists(HEALTH_FILE):
            return
        try:
            with open(HEALTH_FILE, "r") as fh:
                data = json.load(fh)
            for name, attrs in data.items():
                self._sources[name] = SourceHealth(**attrs)
                self._source_history[name] = deque(maxlen=HISTORY_MAXLEN)
                self._uptime_checks[name] = []
            logger.info("_load_health: loaded %d sources from %s", len(self._sources), HEALTH_FILE)
        except Exception as exc:
            logger.warning("_load_health: could not load %s — %s", HEALTH_FILE, exc)

    def _save_health(self) -> None:
        """Persist current source health to artifacts/source_health.json."""
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            data = {name: asdict(health) for name, health in self._sources.items()}
            with open(HEALTH_FILE, "w") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:
            logger.warning("_save_health: %s", exc)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_source(self, name: str, url: str, type: str = "torrent") -> None:
        """Register a new download source.

        If the source already exists (loaded from persistence), this is a no-op.

        Args:
            name: Unique source name.
            url: Base URL for the source.
            type: 'torrent' or 'usenet'.
        """
        if name in self._sources:
            logger.debug("register_source: '%s' already registered", name)
            return
        self._sources[name] = SourceHealth(name=name, url=url, type=type)
        self._source_history[name] = deque(maxlen=HISTORY_MAXLEN)
        self._uptime_checks[name] = []
        logger.info("register_source: registered '%s' (%s)", name, type)
        self._save_health()

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_result(
        self,
        source_name: str,
        success: bool,
        speed_mbps: Optional[float] = None,
        quality_score: Optional[float] = None,
    ) -> None:
        """Update a source's health stats with a new observation.

        Uses exponential moving average (alpha=0.1) to update running averages.
        The source is auto-registered with defaults if not yet known.

        Args:
            source_name: Name of the source.
            success: Whether the download completed successfully.
            speed_mbps: Measured download speed in Mbps (optional).
            quality_score: Quality score for the downloaded content (optional).
        """
        if source_name not in self._sources:
            self.register_source(source_name, url="unknown")

        health = self._sources[source_name]
        alpha = EMA_ALPHA

        # EMA update for success rate
        health.success_rate = (1 - alpha) * health.success_rate + alpha * (1.0 if success else 0.0)

        if speed_mbps is not None:
            health.avg_speed_mbps = (1 - alpha) * health.avg_speed_mbps + alpha * speed_mbps

        if quality_score is not None:
            health.avg_quality_score = (1 - alpha) * health.avg_quality_score + alpha * quality_score

        # Track uptime
        self._uptime_checks.setdefault(source_name, []).append(success)
        checks = self._uptime_checks[source_name]
        health.uptime_pct = (sum(checks) / len(checks)) * 100.0 if checks else 100.0
        health.last_checked = datetime.utcnow().isoformat()

        # Store raw history
        self._source_history[source_name].append(
            (time.time(), success, speed_mbps, quality_score)
        )

        publish_event("source.health.updated", {
            "source": source_name,
            "success_rate": round(health.success_rate, 3),
            "composite": round(health.composite_score(), 3),
        })

        self._save_health()
        logger.debug(
            "record_result: %s success=%s speed=%s quality=%s → composite=%.3f",
            source_name, success, speed_mbps, quality_score, health.composite_score(),
        )

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def rank_sources(self) -> List[SourceHealth]:
        """Return enabled sources sorted by composite score (highest first).

        Returns:
            Sorted list of SourceHealth objects.
        """
        enabled = [h for h in self._sources.values() if h.enabled]
        return sorted(enabled, key=lambda h: h.composite_score(), reverse=True)

    def rank_results(self, results: List[dict], source_name: str) -> List[RankedResult]:
        """Annotate a list of raw results with the source's rank score.

        Args:
            results: Raw result dicts from the source (e.g. Prowlarr hits).
            source_name: Name of the source that produced these results.

        Returns:
            List of RankedResult objects preserving the original order.
        """
        health = self._sources.get(source_name)
        rank_score = health.composite_score() if health else 0.5
        est_quality = health.avg_quality_score if health else DEFAULT_QUALITY_SCORE

        return [
            RankedResult(
                result_dict=r,
                source_name=source_name,
                rank_score=rank_score,
                estimated_quality=est_quality,
            )
            for r in results
        ]

    def get_fallback_chain(self, primary_source: str) -> List[str]:
        """Return an ordered list of fallback source names excluding the primary.

        Args:
            primary_source: Name of the primary (failed) source.

        Returns:
            List of source names ordered by composite score descending.
        """
        ranked = self.rank_sources()
        return [h.name for h in ranked if h.name != primary_source]

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    def disable_poor_sources(self, threshold: float = POOR_SOURCE_THRESHOLD) -> None:
        """Disable sources whose composite score falls below the threshold.

        Args:
            threshold: Minimum composite score to remain enabled.
        """
        for health in self._sources.values():
            if health.enabled and health.composite_score() < threshold:
                health.enabled = False
                publish_event("source.disabled", {
                    "source": health.name,
                    "composite": round(health.composite_score(), 3),
                    "threshold": threshold,
                })
                logger.warning(
                    "disable_poor_sources: disabled '%s' (composite=%.3f < %.3f)",
                    health.name, health.composite_score(), threshold,
                )
        self._save_health()

    def health_report(self) -> dict:
        """Return a full health summary for all registered sources.

        Returns:
            Dict mapping source name → health attributes and composite score.
        """
        report: Dict[str, dict] = {}
        for name, health in self._sources.items():
            d = asdict(health)
            d["composite_score"] = round(health.composite_score(), 4)
            d["history_entries"] = len(self._source_history.get(name, []))
            report[name] = d
        return report
