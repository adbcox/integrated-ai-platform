from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from framework.compat import UTC


@dataclass(frozen=True)
class QueueItem:
    job_id: str
    priority: str
    enqueued_at: str


@dataclass
class DispatchQueueManager:
    """Manages job queue ordering with FIFO and priority tier support."""

    queue: list[QueueItem] = field(default_factory=list)
    throttle_limits: dict[str, int] = field(default_factory=lambda: {
        "multi_file_orchestration": 2,
        "retrieval_orchestration": 3,
        "resumable_checkpointed": 2,
        "default": 5,
    })

    def enqueue(self, job_id: str, priority: str) -> dict[str, Any]:
        """Add job to queue with priority ordering."""
        if not job_id or not priority:
            return {"enqueued": False, "reason": "invalid_job_or_priority"}
        item = QueueItem(
            job_id=job_id,
            priority=priority,
            enqueued_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self.queue.append(item)
        return {
            "enqueued": True,
            "job_id": job_id,
            "queue_position": len(self.queue) - 1,
        }

    def peek(self) -> dict[str, Any]:
        """Return next job without removing."""
        if not self.queue:
            return {"job_id": None, "has_job": False}
        next_item = self._get_next_priority_item()
        return {
            "job_id": next_item.job_id if next_item else None,
            "has_job": next_item is not None,
            "priority": next_item.priority if next_item else None,
        }

    def pop(self) -> dict[str, Any]:
        """Remove and return next job."""
        if not self.queue:
            return {"job_id": None, "popped": False}
        next_item = self._get_next_priority_item()
        if next_item:
            self.queue.remove(next_item)
            return {"job_id": next_item.job_id, "popped": True}
        return {"job_id": None, "popped": False}

    def requeue(self, job_id: str, priority: str = None) -> dict[str, Any]:
        """Move job back to queue."""
        for item in self.queue:
            if item.job_id == job_id:
                return {"requeued": False, "reason": "already_queued"}
        if priority is None:
            priority = "p2"
        return self.enqueue(job_id, priority)

    def get_queue_size(self) -> int:
        """Return current queue size."""
        return len(self.queue)

    def get_throttle_limit(self, job_class: str) -> int:
        """Return throttle limit for job class."""
        return self.throttle_limits.get(job_class, self.throttle_limits.get("default", 5))

    def _get_next_priority_item(self) -> QueueItem | None:
        """Get next item by priority, then FIFO."""
        if not self.queue:
            return None
        priority_order = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
        sorted_queue = sorted(
            self.queue,
            key=lambda x: (priority_order.get(x.priority, 2), x.enqueued_at),
        )
        return sorted_queue[0] if sorted_queue else None
