"""Scheduler and queue control-plane for bounded parallel job dispatch."""

from __future__ import annotations

import queue
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .backend_profiles import BackendProfile
from .compat import UTC
from .inference_adapter import InferenceAdapter
from .job_schema import Job, JobClass, JobLifecycle, JobPriority
from .learning_hooks import LearningHooks
from .queue_types import QueueEnvelope
from .state_store import StateStore
from .worker_runtime import WorkerPool, WorkerRuntime

class Scheduler:
    """Bounded scheduler that accepts, queues, and dispatches jobs to workers."""

    def __init__(
        self,
        *,
        store: StateStore,
        learning: LearningHooks,
        inference: InferenceAdapter,
        backend_profile: BackendProfile,
        replay_pending_on_start: bool = False,
        replay_attempt_limit: int = 2,
    ) -> None:
        self.store = store
        self.learning = learning
        self.inference = inference
        self.backend_profile = backend_profile
        self.replay_pending_on_start = bool(replay_pending_on_start)
        self.replay_attempt_limit = max(1, int(replay_attempt_limit))
        self._queue: "queue.PriorityQueue[QueueEnvelope]" = queue.PriorityQueue()
        self._stop_event = threading.Event()
        self._worker_pool: WorkerPool | None = None
        self._reserved_contexts: set[str] = set()
        self._context_lock = threading.Lock()
        self._jobs_by_state: dict[str, list[str]] = defaultdict(list)
        self._sequence = 0

    def start(self) -> None:
        if self._worker_pool is not None:
            return
        class_semaphores: dict[str, threading.BoundedSemaphore] = {}
        for task_class, max_active in self.backend_profile.max_active_jobs_by_task_class.items():
            if int(max_active) > 0:
                class_semaphores[str(task_class)] = threading.BoundedSemaphore(value=int(max_active))
        workers: list[WorkerRuntime] = []
        worker_count = max(1, self.backend_profile.max_worker_concurrency)
        for idx in range(worker_count):
            workers.append(
                WorkerRuntime(
                    worker_id=f"w{idx + 1}",
                    queue_ref=self._queue,
                    inference=self.inference,
                    store=self.store,
                    learning=self.learning,
                    stop_event=self._stop_event,
                    context_release_callback=self._release_execution_context,
                    dequeue_callback=self._on_job_dequeued,
                    class_semaphores=class_semaphores,
                )
            )
        self._worker_pool = WorkerPool(workers=workers, stop_event=self._stop_event)
        self._worker_pool.start()
        replayed = self._requeue_replayable_jobs() if self.replay_pending_on_start else 0
        self.store.append_trace({
            "kind": "scheduler_start",
            "worker_count": worker_count,
            "backend_profile": self.backend_profile.name,
            "replayed_jobs": replayed,
            "class_limits": {
                key: int(limit)
                for key, limit in self.backend_profile.max_active_jobs_by_task_class.items()
                if int(limit) > 0
            },
        })
        self._persist_queue_snapshot()

    def stop(self) -> None:
        if self._worker_pool is None:
            return
        self._worker_pool.stop()
        self._worker_pool = None
        self.store.append_trace({"kind": "scheduler_stop"})
        self._persist_queue_snapshot()

    def submit(self, job: Job) -> Job:
        context_id = self._reserve_execution_context(job)
        classification = self.classify_job(job)
        job.execution_context_id = context_id
        job.set_lifecycle(JobLifecycle.QUEUED, reason="accepted_by_scheduler")
        self.store.save_job(job)
        self.store.append_queue_event(
            {
                "kind": "job_queued",
                "job_id": job.job_id,
                "task_class": job.task_class.value,
                "classification": classification,
                "priority": job.priority.value,
                "context_id": context_id,
            }
        )
        self._jobs_by_state[job.lifecycle.value].append(job.job_id)
        self._enqueue_job(job)
        self._persist_queue_snapshot()
        return job

    def wait_for_idle(self, *, timeout_seconds: float | None = None) -> bool:
        """Wait until queued jobs are processed."""

        started = datetime.now(UTC)
        while True:
            if self._queue.unfinished_tasks == 0:
                return True
            if timeout_seconds is not None:
                elapsed = (datetime.now(UTC) - started).total_seconds()
                if elapsed >= timeout_seconds:
                    return False
            threading.Event().wait(0.1)

    def status_snapshot(self) -> dict[str, Any]:
        return {
            "backend_profile": self.backend_profile.name,
            "queued_jobs": self._queue.qsize(),
            "reserved_contexts": sorted(self._reserved_contexts),
            "jobs_by_state": {key: list(value) for key, value in self._jobs_by_state.items()},
            "class_limits": {
                key: int(limit)
                for key, limit in self.backend_profile.max_active_jobs_by_task_class.items()
                if int(limit) > 0
            },
            "replay_attempt_limit": self.replay_attempt_limit,
        }

    def classify_job(self, job: Job) -> str:
        if job.task_class in {JobClass.MULTI_FILE_ORCHESTRATION, JobClass.RESUMABLE_CHECKPOINTED}:
            return "complex_orchestration"
        if job.task_class == JobClass.RETRIEVAL_ORCHESTRATION:
            return "retrieval"
        if job.task_class == JobClass.SAFE_CONTRACTS:
            return "safe_contract"
        return "general"

    def _priority_rank(self, priority: JobPriority) -> int:
        order = {
            JobPriority.P0: 0,
            JobPriority.P1: 1,
            JobPriority.P2: 2,
            JobPriority.P3: 3,
        }
        return order.get(priority, 9)

    def _enqueue_job(self, job: Job) -> None:
        envelope = QueueEnvelope(
            priority_rank=self._priority_rank(job.priority),
            sequence=self._sequence,
            job=job,
        )
        self._sequence += 1
        self._queue.put(envelope)

    def _requeue_replayable_jobs(self) -> int:
        replayable_states = {
            JobLifecycle.ACCEPTED,
            JobLifecycle.QUEUED,
            JobLifecycle.DISPATCHED,
            JobLifecycle.RUNNING,
            JobLifecycle.RETRY_WAITING,
        }
        queued = 0
        for job in self.store.list_jobs():
            if job.lifecycle not in replayable_states:
                continue
            replay_attempts = int(job.metadata.get("scheduler_replay_attempts") or 0)
            if replay_attempts >= self.replay_attempt_limit:
                job.set_lifecycle(JobLifecycle.FAILED, reason="scheduler_replay_attempt_limit_exhausted")
                self.store.save_job(job)
                result_payload = {
                    "job_id": job.job_id,
                    "status": "failed",
                    "status_reason": job.status_reason,
                    "attempts_used": int(job.attempts_used or 0),
                    "return_code": -1,
                    "output": "",
                    "error": "scheduler_replay_attempt_limit_exhausted",
                    "validation": {"passed": False, "checks": []},
                }
                self.store.save_result(job.job_id, result_payload)
                self.store.save_dead_letter_record(
                    job=job,
                    result_payload=result_payload,
                    reason="scheduler_replay_attempt_limit_exhausted",
                )
                self.store.append_queue_event(
                    {
                        "kind": "job_dead_lettered_on_replay",
                        "job_id": job.job_id,
                        "task_class": job.task_class.value,
                        "priority": job.priority.value,
                        "replay_attempts": replay_attempts,
                    }
                )
                continue
            if job.lifecycle is not JobLifecycle.QUEUED:
                job.set_lifecycle(JobLifecycle.QUEUED, reason="scheduler_replay")
            job.metadata["scheduler_replay_attempts"] = replay_attempts + 1
            self.store.save_job(job)
            self._enqueue_job(job)
            queued += 1
            self.store.append_queue_event(
                {
                    "kind": "job_replayed",
                    "job_id": job.job_id,
                    "task_class": job.task_class.value,
                    "priority": job.priority.value,
                    "context_id": job.execution_context_id,
                    "replay_attempts": int(job.metadata.get("scheduler_replay_attempts") or 0),
                }
            )
        self._persist_queue_snapshot()
        return queued

    def _reserve_execution_context(self, job: Job) -> str:
        context_hint = str(job.metadata.get("context_hint") or Path(job.target.worktree_target).name or "default")
        candidate = f"{context_hint}:{job.target.worktree_target}"
        with self._context_lock:
            if candidate not in self._reserved_contexts:
                self._reserved_contexts.add(candidate)
                self.store.append_trace({
                    "kind": "context_reserved",
                    "job_id": job.job_id,
                    "context_id": candidate,
                })
                return candidate

            suffix = 1
            while True:
                derived = f"{candidate}#{suffix}"
                if derived not in self._reserved_contexts:
                    self._reserved_contexts.add(derived)
                    self.store.append_trace({
                        "kind": "context_reserved",
                        "job_id": job.job_id,
                        "context_id": derived,
                    })
                    return derived
                suffix += 1

    def _release_execution_context(self, job: Job) -> None:
        context_id = str(job.execution_context_id or "")
        if not context_id:
            return
        with self._context_lock:
            self._reserved_contexts.discard(context_id)
        self.store.append_trace({
            "kind": "context_released",
            "job_id": job.job_id,
            "context_id": context_id,
            "final_lifecycle": job.lifecycle.value,
        })
        self._persist_queue_snapshot()

    def _on_job_dequeued(self, job: Job) -> None:
        self.store.append_queue_event(
            {
                "kind": "job_dequeued",
                "job_id": job.job_id,
                "task_class": job.task_class.value,
                "priority": job.priority.value,
                "lifecycle": job.lifecycle.value,
            }
        )
        self._persist_queue_snapshot()

    def _persist_queue_snapshot(self) -> None:
        with self._queue.mutex:
            queued = [
                {
                    "job_id": env.job.job_id,
                    "task_class": env.job.task_class.value,
                    "priority": env.job.priority.value,
                    "priority_rank": int(env.priority_rank),
                    "sequence": int(env.sequence),
                    "lifecycle": env.job.lifecycle.value,
                }
                for env in list(self._queue.queue)
            ]
        self.store.save_queue_snapshot(
            {
                "kind": "scheduler_queue_snapshot",
                "backend_profile": self.backend_profile.name,
                "queued_jobs": queued,
                "reserved_contexts": sorted(self._reserved_contexts),
            }
        )
