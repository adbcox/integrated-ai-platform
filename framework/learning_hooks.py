"""Learning integration hooks for framework job outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .job_schema import Job
from .state_store import StateStore


@dataclass(frozen=True)
class LearningEvent:
    job_id: str
    task_class: str
    task_template: str
    outcome: str
    attempts_used: int
    prevention_candidate: str
    prevention_recurrence_count: int
    reuse_candidate: str
    lesson: str
    artifact_result_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningHooks:
    """Small integration layer feeding learning artifacts from execution outcomes."""

    def __init__(
        self,
        store: StateStore,
        learning_latest_path: Path,
        code_library_path: Path | None = None,
        trusted_patterns_path: Path | None = None,
        manager_bridge_path: Path | None = None,
    ) -> None:
        self.store = store
        self.learning_latest_path = learning_latest_path.resolve()
        self.code_library_path = (
            code_library_path.resolve()
            if code_library_path is not None
            else self.learning_latest_path.parent / "code_library" / "latest.json"
        )
        self.trusted_patterns_path = (
            trusted_patterns_path.resolve()
            if trusted_patterns_path is not None
            else self.learning_latest_path.parent.parent / "trusted_patterns" / "latest.json"
        )
        self.manager_bridge_path = (
            manager_bridge_path.resolve()
            if manager_bridge_path is not None
            else self.learning_latest_path.parent.parent / "bridge" / "latest_manager_learning_bridge.json"
        )

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _build_execution_priors(self, task_class: str) -> dict[str, Any]:
        library = self._load_json(self.code_library_path)
        trusted = self._load_json(self.trusted_patterns_path)

        top_promotions = []
        for row in (library.get("promotion_candidates") or []):
            if not isinstance(row, dict):
                continue
            top_promotions.append(
                {
                    "source_key": str(row.get("source_key") or ""),
                    "target_key": str(row.get("target_key") or ""),
                    "reuse_confidence": float(row.get("reuse_confidence") or 0.0),
                }
            )
            if len(top_promotions) >= 5:
                break

        trusted_task_tokens = [task_class]
        best_practices: list[dict[str, Any]] = []
        for row in (trusted.get("best_practice_priors") or []):
            if not isinstance(row, dict):
                continue
            applies_to = [str(x).lower() for x in (row.get("applies_to") or []) if str(x)]
            if applies_to and not any(tok in applies_to for tok in trusted_task_tokens):
                continue
            best_practices.append(
                {
                    "title": str(row.get("title") or ""),
                    "recommendation": str(row.get("recommendation") or ""),
                    "source": str(row.get("source") or ""),
                }
            )
            if len(best_practices) >= 5:
                break

        return {
            "code_library_summary": library.get("summary") if isinstance(library.get("summary"), dict) else {},
            "top_promotion_candidates": top_promotions,
            "trusted_best_practices": best_practices,
        }

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

    def _prevention_recurrence_count(self, candidate: str) -> int:
        if not candidate:
            return 0
        count = 0
        for row in self.store.read_learning_events():
            if str(row.get("prevention_candidate") or "") == candidate:
                count += 1
        return count + 1

    def _reuse_candidate(self, job: Job, result: dict[str, Any]) -> str:
        if str(result.get("status") or "") == "completed":
            outputs = result.get("requested_outputs") if isinstance(result.get("requested_outputs"), list) else []
            if outputs:
                return f"reuse:{job.task_class.value}:{outputs[0]}"
            return f"reuse:{job.task_class.value}:bounded_success"
        return ""

    def emit(self, *, job: Job, result: dict[str, Any], result_path: Path) -> LearningEvent:
        prevention_candidate = self._prevention_candidate(job, result)
        event = LearningEvent(
            job_id=job.job_id,
            task_class=job.task_class.value,
            task_template=str(job.metadata.get("task_template") or ""),
            outcome=str(result.get("status") or "unknown"),
            attempts_used=job.attempts_used,
            prevention_candidate=prevention_candidate,
            prevention_recurrence_count=self._prevention_recurrence_count(prevention_candidate),
            reuse_candidate=self._reuse_candidate(job, result),
            lesson=self._lesson_from_outcome(job, result),
            artifact_result_path=str(result_path),
        )
        self.store.append_learning_event(event.to_dict())
        self._write_latest_snapshot(job=job, event=event)
        return event

    def _write_latest_snapshot(self, *, job: Job, event: LearningEvent) -> None:
        prevention_priority = "elevated" if event.prevention_recurrence_count >= 3 else "normal"
        execution_priors = self._build_execution_priors(job.task_class.value)
        payload = {
            "schema_version": "framework_learning_v1",
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
            "framework_prevention_candidates": [
                {
                    "candidate": event.prevention_candidate,
                    "recurrence_count": event.prevention_recurrence_count,
                    "priority": prevention_priority,
                }
            ]
            if event.prevention_candidate
            else [],
            "framework_execution_priors": execution_priors,
        }
        self.learning_latest_path.parent.mkdir(parents=True, exist_ok=True)
        self.learning_latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_manager_bridge_snapshot(job=job, event=event, execution_priors=execution_priors)

    def _write_manager_bridge_snapshot(
        self,
        *,
        job: Job,
        event: LearningEvent,
        execution_priors: dict[str, Any],
    ) -> None:
        payload = {
            "schema_version": "framework_manager_bridge_v1",
            "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generated_from": "framework.learning_hooks",
            "active": True,
            "source_learning_latest_path": str(self.learning_latest_path),
            "weak_classes": [job.task_class.value] if event.outcome != "completed" else [],
            "replay_queue": [
                {
                    "task_id": event.job_id,
                    "task_class": job.task_class.value,
                    "reason": event.lesson,
                    "source_plan_id": event.job_id,
                }
            ],
            "framework_execution_priors": execution_priors,
        }
        self.manager_bridge_path.parent.mkdir(parents=True, exist_ok=True)
        self.manager_bridge_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
