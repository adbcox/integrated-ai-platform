"""Pub/sub event bus with topic routing, persistence, and dead-letter queue.

Topics follow the convention: "domain.entity.action"
Examples: "media.download.started", "training.epoch.complete", "executor.task.failed"
"""
from __future__ import annotations

import fnmatch
import json
import logging
import os
import re
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event dataclass
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """Immutable event envelope published to the bus.

    Attributes:
        id: Unique UUID4 string for this event instance.
        topic: Dot-separated topic string, e.g. "training.epoch.complete".
        payload: Arbitrary JSON-serialisable dict.
        timestamp: Unix epoch float at creation time.
        source: Logical name of the producing component.
        correlation_id: Optional grouping ID to trace related events.
    """

    topic: str
    payload: dict[str, Any]
    source: str = ""
    correlation_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Subscription record
# ---------------------------------------------------------------------------

@dataclass
class _Subscription:
    id: str
    pattern: str
    regex: re.Pattern
    handler: Callable[[Event], None]
    predicate: Optional[Callable[[Event], bool]]


# ---------------------------------------------------------------------------
# Event persistence
# ---------------------------------------------------------------------------

_EVENTS_DIR = Path("artifacts/events")
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
_MAX_ROTATED_FILES = 5


class EventPersistence:
    """Append-only JSONL log for events with rotation.

    Rotates when the active file exceeds 10 MB; keeps the last 5 rotated
    files.
    """

    def __init__(self, base_dir: Path = _EVENTS_DIR) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._active_path = self._base_dir / "events.jsonl"
        self._lock = threading.Lock()

    def append(self, event: Event) -> None:
        """Persist one event, rotating the file if necessary.

        Args:
            event: The event to persist.
        """
        line = json.dumps(asdict(event), default=str) + "\n"
        with self._lock:
            self._rotate_if_needed()
            try:
                with self._active_path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
            except OSError as exc:
                logger.warning("EventPersistence: could not write event: %s", exc)

    def _rotate_if_needed(self) -> None:
        if not self._active_path.exists():
            return
        if self._active_path.stat().st_size < _MAX_FILE_BYTES:
            return
        ts = int(time.time())
        rotated = self._base_dir / f"events.{ts}.jsonl"
        try:
            self._active_path.rename(rotated)
        except OSError as exc:
            logger.warning("EventPersistence: rotation failed: %s", exc)
            return
        self._prune_old_files()

    def _prune_old_files(self) -> None:
        rotated = sorted(self._base_dir.glob("events.*.jsonl"))
        while len(rotated) > _MAX_ROTATED_FILES:
            try:
                rotated.pop(0).unlink()
            except OSError:
                pass

    def read_events(self, pattern: str = "*", limit: int = 100) -> list[Event]:
        """Read persisted events matching a topic pattern.

        Args:
            pattern: Glob-style topic pattern, e.g. "training.*".
            limit: Maximum number of events to return (most recent).

        Returns:
            List of matching Event objects, most recent last.
        """
        results: list[Event] = []
        paths = [self._active_path] if self._active_path.exists() else []
        paths += sorted(self._base_dir.glob("events.*.jsonl"))
        for path in paths:
            try:
                with path.open("r", encoding="utf-8") as fh:
                    for raw in fh:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            d = json.loads(raw)
                            evt = Event(**d)
                            if fnmatch.fnmatch(evt.topic, pattern):
                                results.append(evt)
                        except (json.JSONDecodeError, TypeError):
                            pass
            except OSError:
                pass
        return results[-limit:]


# ---------------------------------------------------------------------------
# Dead-letter queue
# ---------------------------------------------------------------------------

_BACKOFF_SECONDS = [1.0, 4.0, 16.0]


class DeadLetterQueue:
    """Stores and retries failed event deliveries with exponential backoff.

    Failed entries are written to artifacts/events/dlq.jsonl.
    """

    def __init__(self, base_dir: Path = _EVENTS_DIR) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._dlq_path = self._base_dir / "dlq.jsonl"
        self._lock = threading.Lock()

    def enqueue(self, event: Event, handler_id: str, error: str) -> None:
        """Record a failed delivery for later retry.

        Args:
            event: The event that failed delivery.
            handler_id: Subscription ID of the failing handler.
            error: Human-readable description of the failure.
        """
        entry = {
            "event": asdict(event),
            "handler_id": handler_id,
            "error": error,
            "attempts": 1,
            "next_retry_at": time.time() + _BACKOFF_SECONDS[0],
            "enqueued_at": time.time(),
        }
        line = json.dumps(entry, default=str) + "\n"
        with self._lock:
            try:
                with self._dlq_path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
            except OSError as exc:
                logger.warning("DLQ: could not write entry: %s", exc)

    def retry_due(
        self,
        handler_lookup: Callable[[str], Optional[Callable[[Event], None]]],
    ) -> None:
        """Attempt redelivery of due entries.

        Args:
            handler_lookup: Function that maps subscription_id → handler or None.
        """
        if not self._dlq_path.exists():
            return
        now = time.time()
        remaining: list[dict] = []
        with self._lock:
            try:
                with self._dlq_path.open("r", encoding="utf-8") as fh:
                    lines = fh.readlines()
            except OSError:
                return

        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if entry.get("next_retry_at", 0) > now:
                remaining.append(entry)
                continue
            attempts: int = entry.get("attempts", 1)
            handler = handler_lookup(entry.get("handler_id", ""))
            if handler is None or attempts >= len(_BACKOFF_SECONDS) + 1:
                logger.warning(
                    "DLQ: dropping event %s for handler %s after %d attempts",
                    entry["event"].get("id"),
                    entry.get("handler_id"),
                    attempts,
                )
                continue
            try:
                evt = Event(**entry["event"])
                handler(evt)
                logger.debug("DLQ: redelivered event %s", evt.id)
            except Exception as exc:
                entry["attempts"] = attempts + 1
                backoff_idx = min(attempts, len(_BACKOFF_SECONDS) - 1)
                entry["next_retry_at"] = now + _BACKOFF_SECONDS[backoff_idx]
                entry["error"] = str(exc)
                remaining.append(entry)

        with self._lock:
            try:
                with self._dlq_path.open("w", encoding="utf-8") as fh:
                    for e in remaining:
                        fh.write(json.dumps(e, default=str) + "\n")
            except OSError as exc:
                logger.warning("DLQ: could not rewrite file: %s", exc)


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------

class EventBus:
    """Thread-safe singleton pub/sub event bus.

    Handlers are called concurrently in a ThreadPoolExecutor.  Failed handlers
    are routed to the DeadLetterQueue and retried up to three times.
    """

    _instance: Optional[EventBus] = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._subscriptions: dict[str, _Subscription] = {}
        self._sub_lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="eventbus")
        self._persistence = EventPersistence()
        self._dlq = DeadLetterQueue()
        self._dlq_timer: Optional[threading.Timer] = None
        self._start_dlq_loop()

    # -- Singleton ------------------------------------------------------------

    @classmethod
    def instance(cls) -> EventBus:
        """Return (creating if necessary) the process-wide EventBus singleton.

        Returns:
            The singleton EventBus.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # -- Subscription ---------------------------------------------------------

    def subscribe(
        self,
        topic_pattern: str,
        handler: Callable[[Event], None],
        predicate: Optional[Callable[[Event], bool]] = None,
    ) -> str:
        """Register a handler for events matching *topic_pattern*.

        Args:
            topic_pattern: Glob-style pattern; wildcards ``*`` and ``?``
                supported.  Example: ``"media.*"``, ``"*.error"``.
            handler: Callable invoked with the matching Event.
            predicate: Optional extra filter; called before the handler.

        Returns:
            Opaque subscription ID string for later unsubscribing.
        """
        subscription_id = str(uuid.uuid4())
        regex = re.compile(fnmatch.translate(topic_pattern))
        sub = _Subscription(
            id=subscription_id,
            pattern=topic_pattern,
            regex=regex,
            handler=handler,
            predicate=predicate,
        )
        with self._sub_lock:
            self._subscriptions[subscription_id] = sub
        logger.debug("EventBus: subscribed %s to pattern '%s'", subscription_id, topic_pattern)
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription by ID.

        Args:
            subscription_id: The ID returned by :meth:`subscribe`.
        """
        with self._sub_lock:
            self._subscriptions.pop(subscription_id, None)
        logger.debug("EventBus: unsubscribed %s", subscription_id)

    # -- Publishing -----------------------------------------------------------

    def publish(
        self,
        topic: str,
        payload: dict[str, Any],
        source: str = "",
        correlation_id: str = "",
    ) -> str:
        """Publish an event and dispatch it to matching subscribers.

        Args:
            topic: Dot-separated topic string.
            payload: Arbitrary JSON-serialisable dict.
            source: Logical name of the emitting component.
            correlation_id: Optional grouping identifier.

        Returns:
            The generated event ID.
        """
        event = Event(
            topic=topic,
            payload=payload,
            source=source,
            correlation_id=correlation_id,
        )
        self._persistence.append(event)
        with self._sub_lock:
            matching = [
                sub for sub in self._subscriptions.values()
                if sub.regex.match(topic)
            ]
        for sub in matching:
            self._executor.submit(self._dispatch, event, sub)
        logger.debug("EventBus: published %s to %d subscribers", topic, len(matching))
        return event.id

    def _dispatch(self, event: Event, sub: _Subscription) -> None:
        if sub.predicate is not None:
            try:
                if not sub.predicate(event):
                    return
            except Exception as exc:
                logger.warning("EventBus: predicate error for %s: %s", sub.id, exc)
                return
        try:
            sub.handler(event)
        except Exception as exc:
            logger.warning(
                "EventBus: handler %s raised for topic '%s': %s",
                sub.id,
                event.topic,
                exc,
            )
            self._dlq.enqueue(event, sub.id, str(exc))

    # -- History --------------------------------------------------------------

    def get_event_history(
        self,
        topic_pattern: str,
        limit: int = 100,
    ) -> list[Event]:
        """Retrieve persisted events matching *topic_pattern*.

        Args:
            topic_pattern: Glob-style topic pattern.
            limit: Maximum number of events to return.

        Returns:
            List of Event objects, most recent last.
        """
        return self._persistence.read_events(topic_pattern, limit)

    # -- DLQ loop -------------------------------------------------------------

    def _start_dlq_loop(self) -> None:
        self._dlq_timer = threading.Timer(30.0, self._dlq_tick)
        self._dlq_timer.daemon = True
        self._dlq_timer.start()

    def _dlq_tick(self) -> None:
        try:
            with self._sub_lock:
                lookup = dict(self._subscriptions)

            def handler_lookup(sid: str) -> Optional[Callable[[Event], None]]:
                sub = lookup.get(sid)
                return sub.handler if sub else None

            self._dlq.retry_due(handler_lookup)
        except Exception as exc:
            logger.warning("EventBus: DLQ tick error: %s", exc)
        finally:
            self._start_dlq_loop()

    def shutdown(self) -> None:
        """Gracefully shut down the bus (cancel timers, drain executor)."""
        if self._dlq_timer:
            self._dlq_timer.cancel()
        self._executor.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def publish(
    topic: str,
    payload: dict[str, Any],
    source: str = "",
    correlation_id: str = "",
) -> str:
    """Publish an event to the global EventBus.

    Args:
        topic: Dot-separated topic string.
        payload: JSON-serialisable dict.
        source: Logical emitter name.
        correlation_id: Optional grouping ID.

    Returns:
        Generated event ID.
    """
    return EventBus.instance().publish(topic, payload, source, correlation_id)


def subscribe(
    topic_pattern: str,
    handler: Callable[[Event], None],
    predicate: Optional[Callable[[Event], bool]] = None,
) -> str:
    """Subscribe to the global EventBus.

    Args:
        topic_pattern: Glob-style pattern.
        handler: Callable invoked on matching events.
        predicate: Optional extra filter.

    Returns:
        Subscription ID.
    """
    return EventBus.instance().subscribe(topic_pattern, handler, predicate)


def unsubscribe(subscription_id: str) -> None:
    """Unsubscribe from the global EventBus.

    Args:
        subscription_id: ID returned by :func:`subscribe`.
    """
    EventBus.instance().unsubscribe(subscription_id)


def get_event_history(topic_pattern: str, limit: int = 100) -> list[Event]:
    """Retrieve event history from the global EventBus.

    Args:
        topic_pattern: Glob-style topic pattern.
        limit: Maximum number of events returned.

    Returns:
        List of Event objects.
    """
    return EventBus.instance().get_event_history(topic_pattern, limit)
