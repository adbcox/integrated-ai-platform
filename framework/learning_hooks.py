"""Learning integration hooks for framework job outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .job_schema import Job
from .state_store import StateStore


@dataclass(frozen=True)
class LearningEvent:
    job_id: str
    task_class: str
    outcome: str
    attempts_used: int
    prevention_candidate: str
    reuse_candidate: str
    lesson: str
    artifact_result_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningHooks:
    """Small integration layer feeding learning artifacts from execution outcomes."""

    def __init__(self, store: StateStore, learning_latest_path: Path) -> None:
        self.store = store
        self.learning_latest_path = learning_latest_path.resolve()

    def _lesson_from_outcome(self, job: Job, result: dict[str, Any]) -> str:
        status = str(result.get("status") or "unknown")
        validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
        if status == "completed" and bool(validation.get("passed", False)):
            return "First-attempt or bounded retry succeeded with required validations."
        if status == "failed" and job.attempts_used >= job.retry_policy.retry_budget:
            return "Retry budget exhausted; convert signature into prevention candidate."
        return "Outcome requires follow-up analysis for class-level priors."

    def _prevention_candidate(self, job: Job, result: dict[str, Any]) -> str:
        if str(result.get("status") or "") == "failed":
            reason = str(result.get("error") or result.get("status_reason") or "execution_failure")
            return f"prevent:{job.task_class.value}:{reason}"
        return ""

    def _reuse_candidate(self, job: Job, result: dict[str, Any]) -> str:
        if str(result.get("status") or "") == "completed":
            outputs = result.get("requested_outputs") if isinstance(result.get("requested_outputs"), list) else []
            if outputs:
                return f"reuse:{job.task_class.value}:{outputs[0]}"
            return f"reuse:{job.task_class.value}:bounded_success"
        return ""

    def emit(self, *, job: Job, result: dict[str, Any], result_path: Path) -> LearningEvent:
        event = LearningEvent(
            job_id=job.job_id,
            task_class=job.task_class.value,
            outcome=str(result.get("status") or "unknown"),
            attempts_used=job.attempts_used,
            prevention_candidate=self._prevention_candidate(job, result),
            reuse_candidate=self._reuse_candidate(job, result),
            lesson=self._lesson_from_outcome(job, result),
            artifact_result_path=str(result_path),
        )
        self.store.append_learning_event(event.to_dict())
        self._write_latest_snapshot(job=job, event=event)
        return event

    def _write_latest_snapshot(self, *, job: Job, event: LearningEvent) -> None:
        payload = {
            "schema_version": "framework_learning_v1",
            "generated_from": "framework.worker_runtime",
            "active": True,
            "weak_classes": [job.task_class.value] if event.outcome != "completed" else [],
            "replay_queue": [
                {
                    "job_id": job.job_id,
                    "task_class": job.task_class.value,
                    "reason": event.lesson,
                }
            ],
            "framework_latest_event": event.to_dict(),
        }
        self.learning_latest_path.parent.mkdir(parents=True, exist_ok=True)
        self.learning_latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
