from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from framework.compat import UTC


@dataclass(frozen=True)
class DispatchReport:
    timestamp: str
    queued_count: int
    dispatched_count: int
    completed_count: int
    failed_count: int
    success_rate: float


@dataclass
class DispatchReportGenerator:
    """Generates dispatch activity summaries and metrics."""

    job_records: list[dict[str, Any]] = field(default_factory=list)

    def add_job_record(self, job: dict[str, Any]) -> None:
        """Record a job for reporting."""
        self.job_records.append({
            "job_id": job.get("job_id"),
            "status": job.get("lifecycle"),
            "task_class": job.get("task_class"),
            "priority": job.get("priority"),
            "created_at": job.get("created_at_utc"),
            "completed_at": job.get("completed_at"),
        })

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive dispatch report."""
        timestamp = datetime.now(UTC).isoformat(timespec="seconds")

        status_counts = {}
        for record in self.job_records:
            status = record.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        queued_count = status_counts.get("queued", 0)
        dispatched_count = status_counts.get("dispatched", 0) + status_counts.get(
            "dispatching", 0
        )
        completed_count = status_counts.get("completed", 0)
        failed_count = status_counts.get("failed", 0)

        total_finished = completed_count + failed_count
        success_rate = (
            completed_count / total_finished if total_finished > 0 else 0.0
        )

        class_counts = {}
        for record in self.job_records:
            task_class = record.get("task_class", "unknown")
            class_counts[task_class] = class_counts.get(task_class, 0) + 1

        priority_counts = {}
        for record in self.job_records:
            priority = record.get("priority", "unknown")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        return {
            "timestamp": timestamp,
            "queued_count": queued_count,
            "dispatched_count": dispatched_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 3),
            "total_jobs": len(self.job_records),
            "by_class": class_counts,
            "by_priority": priority_counts,
            "by_status": status_counts,
        }

    def calculate_dispatch_latency(self) -> dict[str, Any]:
        """Calculate average time from creation to dispatch."""
        latencies = []
        for record in self.job_records:
            created = record.get("created_at")
            dispatched = record.get("completed_at")
            if created and dispatched:
                try:
                    created_dt = datetime.fromisoformat(created)
                    dispatched_dt = datetime.fromisoformat(dispatched)
                    latency = (dispatched_dt - created_dt).total_seconds()
                    latencies.append(latency)
                except (ValueError, TypeError):
                    pass

        if not latencies:
            return {"avg_latency_seconds": 0, "samples": 0}

        avg_latency = sum(latencies) / len(latencies)
        return {
            "avg_latency_seconds": round(avg_latency, 2),
            "min_latency_seconds": round(min(latencies), 2),
            "max_latency_seconds": round(max(latencies), 2),
            "samples": len(latencies),
        }

    def calculate_attempt_rates(self) -> dict[str, Any]:
        """Calculate average attempts per job by class."""
        class_attempts = {}
        for record in self.job_records:
            task_class = record.get("task_class", "unknown")
            if task_class not in class_attempts:
                class_attempts[task_class] = {"total_attempts": 0, "jobs": 0}
            class_attempts[task_class]["jobs"] += 1

        return {
            "by_class": {
                cls: {
                    "avg_attempts": round(
                        data["total_attempts"] / max(1, data["jobs"]), 2
                    ),
                    "job_count": data["jobs"],
                }
                for cls, data in class_attempts.items()
            },
        }

    def clear_records(self) -> None:
        """Clear all job records."""
        self.job_records.clear()
