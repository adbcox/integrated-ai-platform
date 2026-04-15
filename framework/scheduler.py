"""Scheduler and queue control-plane for bounded parallel job dispatch."""

from __future__ import annotations

import queue
import threading
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .backend_profiles import BackendProfile
from .inference_adapter import InferenceAdapter
from .job_schema import Job, JobClass, JobLifecycle
from .learning_hooks import LearningHooks
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
    ) -> None:
        self.store = store
        self.learning = learning
        self.inference = inference
        self.backend_profile = backend_profile
        self._queue: "queue.Queue[Job]" = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_pool: WorkerPool | None = None
        self._reserved_contexts: set[str] = set()
        self._context_lock = threading.Lock()
        self._jobs_by_state: dict[str, list[str]] = defaultdict(list)

    def start(self) -> None:
        if self._worker_pool is not None:
            return
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
                )
            )
        self._worker_pool = WorkerPool(workers=workers, stop_event=self._stop_event)
        self._worker_pool.start()
        self.store.append_trace({
            "kind": "scheduler_start",
            "worker_count": worker_count,
            "backend_profile": self.backend_profile.name,
        })

    def stop(self) -> None:
        if self._worker_pool is None:
            return
        self._worker_pool.stop()
        self._worker_pool = None
        self.store.append_trace({"kind": "scheduler_stop"})

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
        self._queue.put(job)
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
        }

    def classify_job(self, job: Job) -> str:
        if job.task_class in {JobClass.MULTI_FILE_ORCHESTRATION, JobClass.RESUMABLE_CHECKPOINTED}:
            return "complex_orchestration"
        if job.task_class == JobClass.RETRIEVAL_ORCHESTRATION:
            return "retrieval"
        if job.task_class == JobClass.SAFE_CONTRACTS:
            return "safe_contract"
        return "general"

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
