"""domains/quality_analyzer.py — Release quality analysis, scoring, and profile generation.

Analyzes release metadata to produce quality scores, learns user preferences from
Plex watch history, recommends upgrades, and generates Sonarr/Radarr quality profiles.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional integrations
# ---------------------------------------------------------------------------
try:
    from framework.event_bus import publish_event  # type: ignore
except ImportError:
    def publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        logger.debug("event_bus unavailable — skipped event: %s", name)

try:
    from framework.metrics import get_gauge, get_counter  # type: ignore
    _quality_gauge = get_gauge("media_quality_score", "Current quality score for a release")
    _upgrade_counter = get_counter("media_upgrades_recommended", "Number of upgrade recommendations issued")
except Exception:
    class _Noop:  # type: ignore[misc]
        def set(self, *a, **kw) -> None: ...
        def inc(self, *a, **kw) -> None: ...
        def labels(self, **kw) -> "_Noop": return self
    _quality_gauge = _Noop()       # type: ignore[assignment]
    _upgrade_counter = _Noop()     # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RESOLUTION_SCORES: Dict[str, float] = {
    "4k": 10.0,
    "2160p": 10.0,
    "1080p": 8.0,
    "720p": 6.0,
    "480p": 3.0,
    "sd": 2.0,
}
HDR_BONUS: float = 1.0
CODEC_ADJUSTMENTS: Dict[str, float] = {
    "h265": 1.0,
    "hevc": 1.0,
    "h264": 0.0,
    "avc": 0.0,
    "xvid": -2.0,
    "divx": -2.0,
    "mpeg2": -2.0,
}
AUDIO_CODEC_SCORES: Dict[str, float] = {
    "truehd": 10.0,
    "dts-hd": 10.0,
    "dts-hd ma": 10.0,
    "dts": 8.0,
    "ac3": 6.0,
    "dd": 6.0,
    "eac3": 7.0,
    "aac": 5.0,
    "mp3": 3.0,
}
CHANNEL_ADJUSTMENTS: Dict[str, float] = {
    "7.1": 1.0,
    "5.1": 0.0,
    "2.0": -1.0,
    "stereo": -1.0,
    "mono": -2.0,
}
VIDEO_WEIGHT: float = 0.6
AUDIO_WEIGHT: float = 0.4
SIZE_PENALTY_EXPONENT: float = 0.1
DEFAULT_UPGRADE_THRESHOLD: float = 6.0
MIN_FILE_SIZE_GB: float = 0.01  # avoid division by near-zero


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class QualityScore:
    """Composite quality score for a single release.

    Attributes:
        video_score: Raw video quality score (0–11).
        audio_score: Raw audio quality score (0–11).
        file_size_gb: File size in gigabytes.
        overall_score: Weighted, size-penalised composite score.
        upgrade_recommended: True if overall_score is below the upgrade threshold.
    """

    video_score: float
    audio_score: float
    file_size_gb: float
    overall_score: float
    upgrade_recommended: bool


# ---------------------------------------------------------------------------
# Analyser
# ---------------------------------------------------------------------------
class QualityAnalyzer:
    """Analyse release quality, track history, and generate quality profiles.

    Example::

        analyzer = QualityAnalyzer()
        metadata = {
            "codec": "h265",
            "bitrate_kbps": 8000,
            "resolution": "1080p",
            "hdr": False,
            "audio_codec": "dts",
            "audio_channels": "5.1",
            "file_size_bytes": 8_000_000_000,
        }
        score = analyzer.analyze_release(metadata)
        print(score.overall_score)
    """

    def __init__(self) -> None:
        self.score_history: Dict[str, List[QualityScore]] = {}
        self._upgrade_threshold: float = DEFAULT_UPGRADE_THRESHOLD
        self._preference_data: Dict[str, float] = {}
        logger.info("QualityAnalyzer initialised (default threshold=%.1f)", self._upgrade_threshold)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _video_score(self, metadata: dict) -> float:
        """Compute raw video quality score from resolution, HDR, and codec.

        Args:
            metadata: Release metadata dictionary.

        Returns:
            Video quality score (float).
        """
        resolution = str(metadata.get("resolution", "")).lower().strip()
        score = RESOLUTION_SCORES.get(resolution, 4.0)

        if metadata.get("hdr", False):
            score += HDR_BONUS

        codec = str(metadata.get("codec", "")).lower().strip()
        score += CODEC_ADJUSTMENTS.get(codec, 0.0)

        return max(0.0, score)

    def _audio_score(self, metadata: dict) -> float:
        """Compute raw audio quality score from codec and channel layout.

        Args:
            metadata: Release metadata dictionary.

        Returns:
            Audio quality score (float).
        """
        codec = str(metadata.get("audio_codec", "")).lower().strip()
        score = AUDIO_CODEC_SCORES.get(codec, 4.0)

        channels = str(metadata.get("audio_channels", "2.0")).strip()
        score += CHANNEL_ADJUSTMENTS.get(channels, 0.0)

        return max(0.0, score)

    def analyze_release(self, metadata: dict) -> QualityScore:
        """Score a single release from its metadata.

        Args:
            metadata: Dictionary with keys: codec, bitrate_kbps, resolution,
                hdr, audio_codec, audio_channels, file_size_bytes.

        Returns:
            QualityScore with video/audio breakdown and an overall score.
        """
        file_size_bytes = float(metadata.get("file_size_bytes", 1_000_000_000))
        file_size_gb = max(MIN_FILE_SIZE_GB, file_size_bytes / 1_073_741_824)

        v_score = self._video_score(metadata)
        a_score = self._audio_score(metadata)

        weighted = v_score * VIDEO_WEIGHT + a_score * AUDIO_WEIGHT
        overall = weighted / (file_size_gb ** SIZE_PENALTY_EXPONENT)
        upgrade_recommended = overall < self._upgrade_threshold

        qs = QualityScore(
            video_score=round(v_score, 3),
            audio_score=round(a_score, 3),
            file_size_gb=round(file_size_gb, 3),
            overall_score=round(overall, 3),
            upgrade_recommended=upgrade_recommended,
        )

        logger.debug(
            "analyze_release: video=%.2f audio=%.2f size=%.2fGB overall=%.2f",
            v_score, a_score, file_size_gb, overall,
        )

        _quality_gauge.labels(resolution=metadata.get("resolution", "unknown")).set(overall)  # type: ignore[attr-defined]

        publish_event("media.quality.analyzed", {
            "video_score": qs.video_score,
            "audio_score": qs.audio_score,
            "overall_score": qs.overall_score,
            "upgrade_recommended": qs.upgrade_recommended,
        })

        if upgrade_recommended:
            _upgrade_counter.inc()  # type: ignore[attr-defined]
            publish_event("media.quality.upgrade_recommended", {
                "overall_score": qs.overall_score,
                "threshold": self._upgrade_threshold,
            })

        return qs

    # ------------------------------------------------------------------
    # History & learning
    # ------------------------------------------------------------------

    def record_score(self, item_id: str, score: QualityScore) -> None:
        """Store a QualityScore in score_history for the given item.

        Args:
            item_id: Unique identifier for the show or movie.
            score: QualityScore to record.
        """
        self.score_history.setdefault(item_id, []).append(score)

    def learn_preferences(self, plex_watch_history: List[dict]) -> dict:
        """Derive codec/quality preferences from Plex watch history.

        Aggregates played items by genre and records which codecs/resolutions
        were most commonly viewed, producing a preference weight per genre.

        Args:
            plex_watch_history: List of dicts with keys: genre (list[str]),
                codec, resolution, rating.

        Returns:
            Dict mapping genre → {codec: weight, resolution: weight}.
        """
        genre_stats: Dict[str, Dict[str, Dict[str, float]]] = {}

        for entry in plex_watch_history:
            genres: List[str] = entry.get("genre", ["unknown"])
            codec = str(entry.get("codec", "unknown")).lower()
            resolution = str(entry.get("resolution", "unknown")).lower()

            for genre in genres:
                g = genre_stats.setdefault(genre, {"codecs": {}, "resolutions": {}})
                g["codecs"][codec] = g["codecs"].get(codec, 0) + 1
                g["resolutions"][resolution] = g["resolutions"].get(resolution, 0) + 1

        preferences: Dict[str, dict] = {}
        for genre, stats in genre_stats.items():
            total_codec = sum(stats["codecs"].values()) or 1
            total_res = sum(stats["resolutions"].values()) or 1
            preferences[genre] = {
                "preferred_codec": max(stats["codecs"], key=stats["codecs"].get),  # type: ignore[arg-type]
                "preferred_resolution": max(stats["resolutions"], key=stats["resolutions"].get),  # type: ignore[arg-type]
                "codec_weights": {k: v / total_codec for k, v in stats["codecs"].items()},
                "resolution_weights": {k: v / total_res for k, v in stats["resolutions"].items()},
            }

        self._preference_data = {genre: p["preferred_codec"] for genre, p in preferences.items()}
        logger.info("learn_preferences: processed %d history entries, %d genres", len(plex_watch_history), len(preferences))
        return preferences

    def get_upgrade_threshold(self) -> float:
        """Return the current upgrade recommendation threshold.

        Returns:
            Threshold float (default 6.0, may be adjusted by learn_preferences).
        """
        return self._upgrade_threshold

    def recommend_upgrades(self, library: List[dict]) -> List[dict]:
        """Identify library items whose quality scores fall below the threshold.

        Args:
            library: List of dicts with keys matching analyze_release() metadata,
                plus an optional 'id' and 'title' key.

        Returns:
            List of dicts with 'id', 'title', 'overall_score', and 'metadata'.
        """
        recommendations: List[dict] = []
        threshold = self.get_upgrade_threshold()

        for item in library:
            score = self.analyze_release(item)
            if score.overall_score < threshold:
                recommendations.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "overall_score": score.overall_score,
                    "upgrade_recommended": True,
                    "metadata": item,
                })

        logger.info("recommend_upgrades: %d/%d items below threshold %.1f",
                    len(recommendations), len(library), threshold)
        return recommendations

    # ------------------------------------------------------------------
    # Profile generation
    # ------------------------------------------------------------------

    def _base_profile(self, prefs: dict, arr_type: str) -> dict:
        """Build a common quality profile dict from learned preferences.

        Args:
            prefs: Preference dict from learn_preferences().
            arr_type: 'sonarr' or 'radarr'.

        Returns:
            Partial profile dict.
        """
        preferred_resolutions = set()
        preferred_codecs = set()
        for genre_prefs in prefs.values():
            if isinstance(genre_prefs, dict):
                preferred_resolutions.add(genre_prefs.get("preferred_resolution", "1080p"))
                preferred_codecs.add(genre_prefs.get("preferred_codec", "h265"))

        resolution_cutoff = "1080p" if "4k" not in preferred_resolutions and "2160p" not in preferred_resolutions else "2160p"
        return {
            "name": f"AI-Generated {arr_type.capitalize()} Profile",
            "upgradeAllowed": True,
            "cutoff": resolution_cutoff,
            "minFormatScore": int(self._upgrade_threshold * 10),
            "cutoffFormatScore": 0,
            "preferredCodecs": list(preferred_codecs),
        }

    def to_sonarr_profile(self, prefs: dict) -> dict:
        """Generate a Sonarr API quality profile payload from preferences.

        Args:
            prefs: Preference dict from learn_preferences().

        Returns:
            Sonarr-compatible quality profile dict for POST /api/v3/qualityprofile.
        """
        profile = self._base_profile(prefs, "sonarr")
        profile["items"] = [
            {"quality": {"id": 3, "name": "WEBDL-1080p"}, "allowed": True},
            {"quality": {"id": 4, "name": "Bluray-1080p"}, "allowed": True},
            {"quality": {"id": 6, "name": "WEBDL-720p"}, "allowed": True},
            {"quality": {"id": 7, "name": "Bluray-720p"}, "allowed": True},
        ]
        logger.debug("to_sonarr_profile: generated profile '%s'", profile["name"])
        return profile

    def to_radarr_profile(self, prefs: dict) -> dict:
        """Generate a Radarr API quality profile payload from preferences.

        Args:
            prefs: Preference dict from learn_preferences().

        Returns:
            Radarr-compatible quality profile dict for POST /api/v3/qualityprofile.
        """
        profile = self._base_profile(prefs, "radarr")
        profile["items"] = [
            {"quality": {"id": 2, "name": "WEBDL-2160p"}, "allowed": True},
            {"quality": {"id": 3, "name": "Bluray-2160p"}, "allowed": True},
            {"quality": {"id": 4, "name": "WEBDL-1080p"}, "allowed": True},
            {"quality": {"id": 5, "name": "Bluray-1080p"}, "allowed": True},
        ]
        logger.debug("to_radarr_profile: generated profile '%s'", profile["name"])
        return profile
