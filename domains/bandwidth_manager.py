"""domains/bandwidth_manager.py — Network bandwidth monitoring, scheduling, and throttling.

Tracks real-time network utilisation, enforces business-hours throttle windows,
and prioritises download tasks so high-value content always goes first.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------
try:
    import psutil  # type: ignore
    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    _PSUTIL_AVAILABLE = False
    logger.warning("psutil not available — network stats will return zeros")

try:
    import yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    _YAML_AVAILABLE = False

try:
    from framework.event_bus import publish_event  # type: ignore
except ImportError:
    def publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        logger.debug("event_bus unavailable — skipped event: %s", name)

try:
    from framework.metrics import get_gauge  # type: ignore
    _upload_gauge = get_gauge("network_upload_mbps", "Current upload speed in Mbps")
    _download_gauge = get_gauge("network_download_mbps", "Current download speed in Mbps")
except Exception:
    class _Noop:  # type: ignore[misc]
        def set(self, *a, **kw) -> None: ...
    _upload_gauge = _Noop()    # type: ignore[assignment]
    _download_gauge = _Noop()  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BUSINESS_HOURS_START: int = 9
BUSINESS_HOURS_END: int = 18
THROTTLE_MBPS: float = 10.0
FULL_SPEED_MBPS: float = 100.0
CPU_THROTTLE_THRESHOLD: float = 80.0    # percent
NETWORK_CAPACITY_THRESHOLD: float = 90.0  # percent of FULL_SPEED_MBPS
SAMPLE_INTERVAL_SECONDS: int = 60
STATS_DEQUE_MAXLEN: int = 1440          # 24 hours × 60 samples/hour
TASK_PRIORITY_ORDER: List[str] = ["new_episode", "catalog", "backfill"]
BYTES_PER_MEGABIT: float = 125_000.0   # 1 Mbps = 125,000 bytes/s


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class BandwidthWindow:
    """A time window with a bandwidth cap.

    Attributes:
        start_hour: Inclusive start hour (0–23).
        end_hour: Exclusive end hour (0–23).
        max_mbps: Maximum allowed throughput in Mbps.
        priority: Lower number = higher priority when windows overlap.
    """

    start_hour: int
    end_hour: int
    max_mbps: float
    priority: int = 0


@dataclass
class NetworkStats:
    """Point-in-time network I/O measurements.

    Attributes:
        upload_mbps: Upload speed in Mbps.
        download_mbps: Download speed in Mbps.
        latency_ms: Round-trip latency in milliseconds (0 if unavailable).
        timestamp: Unix timestamp when stats were collected.
    """

    upload_mbps: float
    download_mbps: float
    latency_ms: float
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------
class BandwidthManager:
    """Monitor network utilisation and apply dynamic throttle policies.

    Example::

        manager = BandwidthManager()
        manager.add_window(BandwidthWindow(9, 18, THROTTLE_MBPS, priority=0))
        print(manager.get_current_limit())
        print(manager.get_throttle_params())
    """

    def __init__(self, config_path: str = "config/bandwidth.yaml") -> None:
        """Initialise the manager, optionally loading window definitions from YAML.

        Args:
            config_path: Path to a YAML file defining BandwidthWindow entries.
        """
        self._windows: List[BandwidthWindow] = []
        self._stats_history: Deque[NetworkStats] = deque(maxlen=STATS_DEQUE_MAXLEN)
        self._throttled: bool = False
        self._lock = threading.Lock()

        # Track previous counters for delta calculation
        self._prev_bytes_sent: int = 0
        self._prev_bytes_recv: int = 0
        self._prev_sample_time: float = time.time()

        self._load_config(config_path)
        self._collector_thread: Optional[threading.Thread] = None
        self._start_collector()
        logger.info("BandwidthManager initialised (config=%s, psutil=%s)", config_path, _PSUTIL_AVAILABLE)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _load_config(self, config_path: str) -> None:
        """Load BandwidthWindow definitions from a YAML config file.

        Args:
            config_path: Path to YAML file. Silently ignored if missing.
        """
        if not _YAML_AVAILABLE:
            return
        try:
            import os
            if not os.path.exists(config_path):
                return
            with open(config_path, "r") as fh:
                data = yaml.safe_load(fh) or {}
            for entry in data.get("windows", []):
                w = BandwidthWindow(
                    start_hour=int(entry["start_hour"]),
                    end_hour=int(entry["end_hour"]),
                    max_mbps=float(entry["max_mbps"]),
                    priority=int(entry.get("priority", 0)),
                )
                self._windows.append(w)
            logger.info("_load_config: loaded %d windows from %s", len(self._windows), config_path)
        except Exception as exc:
            logger.warning("_load_config: could not load %s — %s", config_path, exc)

    def add_window(self, window: BandwidthWindow) -> None:
        """Register a bandwidth-limit window.

        Args:
            window: BandwidthWindow to add.
        """
        with self._lock:
            self._windows.append(window)
        logger.info("add_window: %02d:00–%02d:00 @ %.1f Mbps (priority=%d)",
                    window.start_hour, window.end_hour, window.max_mbps, window.priority)

    # ------------------------------------------------------------------
    # Limit queries
    # ------------------------------------------------------------------

    def get_current_limit(self) -> float:
        """Return the active Mbps cap for the current time of day.

        Finds all matching windows, picks the one with the lowest priority number.
        Falls back to THROTTLE_MBPS if in business hours, else FULL_SPEED_MBPS.

        Returns:
            Maximum allowed throughput in Mbps.
        """
        now_hour = datetime.now().hour
        with self._lock:
            matching = [
                w for w in self._windows
                if w.start_hour <= now_hour < w.end_hour
            ]
        if matching:
            best = min(matching, key=lambda w: w.priority)
            return best.max_mbps
        return THROTTLE_MBPS if self.is_business_hours() else FULL_SPEED_MBPS

    def is_business_hours(self) -> bool:
        """Return True if the current time falls within business hours.

        Returns:
            True between BUSINESS_HOURS_START and BUSINESS_HOURS_END.
        """
        hour = datetime.now().hour
        return BUSINESS_HOURS_START <= hour < BUSINESS_HOURS_END

    # ------------------------------------------------------------------
    # Stats collection
    # ------------------------------------------------------------------

    def get_network_stats(self) -> NetworkStats:
        """Sample current network I/O and return a NetworkStats snapshot.

        Uses psutil.net_io_counters() with a delta against the previous sample
        to compute current throughput. Returns zeros when psutil is unavailable.

        Returns:
            NetworkStats with upload_mbps, download_mbps, latency_ms, timestamp.
        """
        if not _PSUTIL_AVAILABLE:
            return NetworkStats(upload_mbps=0.0, download_mbps=0.0, latency_ms=0.0)

        try:
            counters = psutil.net_io_counters()
            now = time.time()
            with self._lock:
                elapsed = now - self._prev_sample_time
                if elapsed <= 0:
                    elapsed = 1.0
                bytes_sent_delta = max(0, counters.bytes_sent - self._prev_bytes_sent)
                bytes_recv_delta = max(0, counters.bytes_recv - self._prev_bytes_recv)
                self._prev_bytes_sent = counters.bytes_sent
                self._prev_bytes_recv = counters.bytes_recv
                self._prev_sample_time = now

            upload_mbps = (bytes_sent_delta / elapsed) / BYTES_PER_MEGABIT
            download_mbps = (bytes_recv_delta / elapsed) / BYTES_PER_MEGABIT

            _upload_gauge.set(upload_mbps)    # type: ignore[attr-defined]
            _download_gauge.set(download_mbps)  # type: ignore[attr-defined]

            return NetworkStats(
                upload_mbps=round(upload_mbps, 3),
                download_mbps=round(download_mbps, 3),
                latency_ms=0.0,
                timestamp=now,
            )
        except Exception as exc:
            logger.warning("get_network_stats error: %s", exc)
            return NetworkStats(upload_mbps=0.0, download_mbps=0.0, latency_ms=0.0)

    # ------------------------------------------------------------------
    # Throttle decision
    # ------------------------------------------------------------------

    def should_throttle(self) -> bool:
        """Decide whether downloads should be throttled right now.

        Returns True when any of the following conditions is met:
        - Current time is within business hours.
        - CPU usage exceeds CPU_THROTTLE_THRESHOLD.
        - Network download is above NETWORK_CAPACITY_THRESHOLD % of FULL_SPEED_MBPS.

        Returns:
            True if throttle should be applied.
        """
        if self.is_business_hours():
            return True

        if _PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                if cpu > CPU_THROTTLE_THRESHOLD:
                    return True
            except Exception:
                pass

        if self._stats_history:
            last = self._stats_history[-1]
            capacity_pct = (last.download_mbps / FULL_SPEED_MBPS) * 100.0
            if capacity_pct > NETWORK_CAPACITY_THRESHOLD:
                return True

        return False

    def get_throttle_params(self) -> dict:
        """Return rclone-compatible throttle parameters for the current limit.

        Returns:
            Dict with 'bwlimit' key as a string like '10M' or '0' for unlimited.
        """
        limit = self.get_current_limit()
        if limit >= FULL_SPEED_MBPS:
            return {"bwlimit": "0"}
        return {"bwlimit": f"{int(limit)}M"}

    # ------------------------------------------------------------------
    # Task prioritisation
    # ------------------------------------------------------------------

    def prioritize(self, tasks: List[dict]) -> List[dict]:
        """Sort download tasks by type priority, then by added_at (newest first).

        Priority order: new_episode > catalog > backfill (unknown types go last).

        Args:
            tasks: List of task dicts with keys: type, size_gb, added_at.

        Returns:
            Sorted list of tasks.
        """
        def _sort_key(task: dict):
            task_type = task.get("type", "unknown")
            try:
                type_rank = TASK_PRIORITY_ORDER.index(task_type)
            except ValueError:
                type_rank = len(TASK_PRIORITY_ORDER)
            added_at = task.get("added_at", "")
            return (type_rank, added_at)

        return sorted(tasks, key=_sort_key)

    # ------------------------------------------------------------------
    # Dashboard data
    # ------------------------------------------------------------------

    def get_usage_graph_data(self, hours: int = 24) -> List[dict]:
        """Return time-series network usage data for dashboard charts.

        Args:
            hours: Number of hours of history to return (max limited by deque).

        Returns:
            List of dicts with keys: timestamp, upload_mbps, download_mbps.
        """
        max_samples = min(hours * 60, len(self._stats_history))
        recent = list(self._stats_history)[-max_samples:]
        return [
            {
                "timestamp": s.timestamp,
                "upload_mbps": s.upload_mbps,
                "download_mbps": s.download_mbps,
                "latency_ms": s.latency_ms,
            }
            for s in recent
        ]

    # ------------------------------------------------------------------
    # Background collector
    # ------------------------------------------------------------------

    def _collect_loop(self) -> None:
        """Background thread: sample network stats every SAMPLE_INTERVAL_SECONDS seconds."""
        logger.debug("_collect_loop: started")
        was_throttled = False
        while True:
            try:
                stats = self.get_network_stats()
                with self._lock:
                    self._stats_history.append(stats)

                now_throttled = self.should_throttle()
                if now_throttled and not was_throttled:
                    publish_event("bandwidth.throttle.enabled", {
                        "limit_mbps": self.get_current_limit(),
                        "params": self.get_throttle_params(),
                    })
                    logger.info("Throttle ENABLED — %.1f Mbps", self.get_current_limit())
                elif not now_throttled and was_throttled:
                    publish_event("bandwidth.throttle.disabled", {
                        "limit_mbps": FULL_SPEED_MBPS,
                    })
                    logger.info("Throttle DISABLED — full speed %.1f Mbps", FULL_SPEED_MBPS)
                was_throttled = now_throttled
            except Exception as exc:
                logger.warning("_collect_loop error: %s", exc)
            time.sleep(SAMPLE_INTERVAL_SECONDS)

    def _start_collector(self) -> None:
        """Start the background stats-collection daemon thread."""
        self._collector_thread = threading.Thread(
            target=self._collect_loop,
            name="bandwidth-collector",
            daemon=True,
        )
        self._collector_thread.start()
        logger.debug("_start_collector: daemon thread started")
