#!/usr/bin/env python3
"""DAG-based parallel execution engine with resource-aware auto-scaling.

Publishes events and emits metrics for executor task lifecycle.
Uses topological sort to identify layers of parallelizable tasks,
then executes each layer with ThreadPoolExecutor, auto-scaling
worker count based on CPU utilization.
"""

from __future__ import annotations

import logging
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    _PSUTIL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_WORKERS: int = 5
CPU_HIGH_THRESHOLD: float = 0.80
CPU_CHECK_INTERVAL: int = 5  # seconds between CPU checks during execution

# ---------------------------------------------------------------------------
# Structured logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lightweight event / metrics stubs (replaced by real sinks if wired)
# ---------------------------------------------------------------------------

try:
    from framework.event_system import publish_event as _publish_event
except Exception:
    def _publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        """Fallback no-op event publisher."""
        logger.debug("event %s: %s", name, payload)

try:
    from framework.metrics_collector import (
        counter as _counter,
        gauge as _gauge,
        histogram as _histogram,
    )
    _METRICS_AVAILABLE = True
except Exception:
    _METRICS_AVAILABLE = False

    def _counter(name: str, value: float = 1, labels: dict | None = None) -> None:  # type: ignore[misc]
        pass

    def _gauge(name: str, value: float, labels: dict | None = None) -> None:  # type: ignore[misc]
        pass

    def _histogram(name: str, value: float, labels: dict | None = None) -> None:  # type: ignore[misc]
        pass


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single unit of work in the DAG.

    Attributes:
        id: Unique identifier for this task.
        func: Callable to invoke.
        args: Positional arguments for *func*.
        kwargs: Keyword arguments for *func*.
        dependencies: IDs of tasks that must complete before this one.
        priority: Higher value = higher priority when scheduling.
        timeout_seconds: Per-task execution timeout.
    """

    id: str
    func: Callable[..., Any]
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    timeout_seconds: float = 300.0


@dataclass
class TaskResult:
    """Result of a single task execution.

    Attributes:
        task_id: ID of the task that produced this result.
        success: Whether the task completed without error.
        result: Return value of the task callable.
        error: String representation of any exception raised.
        start_time: Wall-clock time when execution began.
        end_time: Wall-clock time when execution finished.
        duration_seconds: Elapsed time in seconds.
    """

    task_id: str
    success: bool
    result: Any
    error: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float


@dataclass
class ExecutionPlan:
    """A topologically sorted execution plan.

    Attributes:
        tasks: All tasks registered in the plan.
        execution_order: Batches of task IDs that can run in parallel.
                         Each inner list is one layer; layers are sequential.
    """

    tasks: List[Task]
    execution_order: List[List[str]]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ParallelEngine:
    """DAG-based parallel task executor with CPU-aware auto-scaling.

    Example::

        engine = ParallelEngine(max_workers=4)
        engine.add_task(Task(id="a", func=my_fn, args=(1,)))
        engine.add_task(Task(id="b", func=other_fn, dependencies=["a"]))
        results = engine.execute()
    """

    def __init__(self, max_workers: int = MAX_WORKERS) -> None:
        """Initialise the engine.

        Args:
            max_workers: Maximum number of concurrent threads.
        """
        self._max_workers: int = max_workers
        self._tasks: Dict[str, Task] = {}
        self._results: Dict[str, TaskResult] = {}
        self._running: Dict[str, Future] = {}  # type: ignore[type-arg]
        self._cancelled: set[str] = set()
        self._last_cpu_check: float = 0.0
        self._current_workers: int = max_workers

        logger.debug(
            "ParallelEngine initialised with max_workers=%d cpu_threshold=%.2f",
            max_workers,
            CPU_HIGH_THRESHOLD,
        )

    # ------------------------------------------------------------------
    # Task registration
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Register a task for execution.

        Args:
            task: The task to add.

        Raises:
            ValueError: If a task with the same ID already exists.
        """
        if task.id in self._tasks:
            raise ValueError(f"Task with id '{task.id}' already registered.")
        self._tasks[task.id] = task
        logger.debug("Registered task id=%s priority=%d deps=%s", task.id, task.priority, task.dependencies)

    # ------------------------------------------------------------------
    # Plan construction
    # ------------------------------------------------------------------

    def build_plan(self) -> ExecutionPlan:
        """Topologically sort tasks into parallel layers.

        Returns:
            An ExecutionPlan with tasks grouped into layers.

        Raises:
            ValueError: If a dependency is missing or a cycle is detected.
        """
        tasks = self._tasks

        # Validate all dependencies exist
        for task in tasks.values():
            for dep in task.dependencies:
                if dep not in tasks:
                    raise ValueError(
                        f"Task '{task.id}' depends on '{dep}' which is not registered."
                    )

        # Kahn's algorithm for topological sort
        in_degree: Dict[str, int] = {tid: 0 for tid in tasks}
        dependents: Dict[str, List[str]] = {tid: [] for tid in tasks}

        for task in tasks.values():
            for dep in task.dependencies:
                in_degree[task.id] += 1
                dependents[dep].append(task.id)

        # BFS layer-by-layer
        current_layer = [tid for tid, deg in in_degree.items() if deg == 0]
        execution_order: List[List[str]] = []
        visited: set[str] = set()

        while current_layer:
            # Sort layer by descending priority for deterministic ordering
            current_layer.sort(key=lambda tid: -tasks[tid].priority)
            execution_order.append(current_layer)
            visited.update(current_layer)

            next_layer: List[str] = []
            for tid in current_layer:
                for dependent in dependents[tid]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_layer.append(dependent)
            current_layer = next_layer

        if len(visited) != len(tasks):
            # Find the cycle for a helpful error message
            remaining = set(tasks) - visited
            cycle_desc = self._describe_cycle(remaining, tasks)
            raise ValueError(f"Cycle detected among tasks: {cycle_desc}")

        plan = ExecutionPlan(tasks=list(tasks.values()), execution_order=execution_order)
        logger.info(
            "Built execution plan: %d tasks in %d layers",
            len(tasks),
            len(execution_order),
        )
        return plan

    def _describe_cycle(self, remaining: set[str], tasks: Dict[str, Task]) -> str:
        """Produce a human-readable description of a cycle.

        Args:
            remaining: Task IDs that were not visited during topological sort.
            tasks: Full task registry.

        Returns:
            A string describing the cycle.
        """
        # Walk one path to find a cycle
        visited_path: List[str] = []
        start = next(iter(remaining))
        current = start
        seen: set[str] = set()

        while current not in seen:
            seen.add(current)
            visited_path.append(current)
            # Follow first dep that is in remaining
            deps_in_cycle = [d for d in tasks[current].dependencies if d in remaining]
            if not deps_in_cycle:
                break
            current = deps_in_cycle[0]

        if current in visited_path:
            cycle_start = visited_path.index(current)
            cycle = visited_path[cycle_start:] + [current]
            return " → ".join(cycle)
        return str(remaining)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, plan: Optional[ExecutionPlan] = None) -> Dict[str, TaskResult]:
        """Execute a plan layer by layer, auto-scaling workers.

        Args:
            plan: Pre-built plan; if None, calls ``build_plan()`` first.

        Returns:
            Mapping of task_id → TaskResult for every task.
        """
        if plan is None:
            plan = self.build_plan()

        self._results = {}
        total_tasks = len(plan.tasks)
        logger.info("Starting execution of %d tasks across %d layers", total_tasks, len(plan.execution_order))

        _gauge("executor_tasks_pending", float(total_tasks))

        for layer_idx, layer in enumerate(plan.execution_order):
            active_layer = [tid for tid in layer if tid not in self._cancelled]
            if not active_layer:
                continue

            workers = self._scale_workers()
            logger.info("Layer %d: executing %d tasks with %d workers", layer_idx, len(active_layer), workers)

            with ThreadPoolExecutor(max_workers=workers) as pool:
                future_to_id: Dict[Future, str] = {}  # type: ignore[type-arg]
                for tid in active_layer:
                    task = self._tasks[tid]
                    fut = pool.submit(self.execute_single, task)
                    future_to_id[fut] = tid
                    self._running[tid] = fut

                for fut in as_completed(future_to_id):
                    tid = future_to_id[fut]
                    try:
                        result = fut.result(timeout=self._tasks[tid].timeout_seconds)
                        self._results[tid] = result
                    except Exception as exc:
                        # Wrap any outer exception (e.g. timeout from as_completed)
                        now = datetime.now(timezone.utc)
                        self._results[tid] = TaskResult(
                            task_id=tid,
                            success=False,
                            result=None,
                            error=str(exc),
                            start_time=now,
                            end_time=now,
                            duration_seconds=0.0,
                        )
                    finally:
                        self._running.pop(tid, None)

            _gauge("executor_tasks_pending", float(total_tasks - len(self._results)))

        logger.info(
            "Execution complete: %d succeeded, %d failed",
            sum(1 for r in self._results.values() if r.success),
            sum(1 for r in self._results.values() if not r.success),
        )
        return self._results

    def execute_single(self, task: Task) -> TaskResult:
        """Execute a single task and return its result.

        Args:
            task: The task to execute.

        Returns:
            A TaskResult capturing success/failure and timing.
        """
        start = datetime.now(timezone.utc)
        start_ts = time.monotonic()

        _publish_event("executor.task.started", {"task_id": task.id, "timestamp": start.isoformat()})
        logger.debug("Starting task id=%s", task.id)

        try:
            value = task.func(*task.args, **task.kwargs)
            end = datetime.now(timezone.utc)
            duration = time.monotonic() - start_ts

            result = TaskResult(
                task_id=task.id,
                success=True,
                result=value,
                error="",
                start_time=start,
                end_time=end,
                duration_seconds=duration,
            )
            _publish_event("executor.task.completed", {"task_id": task.id, "duration_seconds": duration})
            _counter("executor_tasks_completed")
            _histogram("executor_task_duration", duration)
            logger.debug("Task id=%s completed in %.3fs", task.id, duration)
            return result

        except Exception as exc:  # pylint: disable=broad-except
            end = datetime.now(timezone.utc)
            duration = time.monotonic() - start_ts
            err_msg = f"{type(exc).__name__}: {exc}"

            result = TaskResult(
                task_id=task.id,
                success=False,
                result=None,
                error=err_msg,
                start_time=start,
                end_time=end,
                duration_seconds=duration,
            )
            _publish_event("executor.task.failed", {"task_id": task.id, "error": err_msg})
            _histogram("executor_task_duration", duration)
            logger.warning("Task id=%s FAILED after %.3fs: %s", task.id, duration, err_msg)
            return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_ready_tasks(self) -> List[Task]:
        """Return tasks whose dependencies have all completed successfully.

        Returns:
            List of tasks ready to run.
        """
        completed_ok = {tid for tid, r in self._results.items() if r.success}
        ready: List[Task] = []
        for task in self._tasks.values():
            if task.id in self._results or task.id in self._running or task.id in self._cancelled:
                continue
            if all(dep in completed_ok for dep in task.dependencies):
                ready.append(task)
        return ready

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending or running task.

        Args:
            task_id: ID of the task to cancel.

        Returns:
            True if the task was found and cancelled, False otherwise.
        """
        if task_id not in self._tasks:
            return False
        self._cancelled.add(task_id)
        if task_id in self._running:
            self._running[task_id].cancel()
        logger.info("Task id=%s cancelled", task_id)
        return True

    def get_status(self) -> Dict[str, Any]:
        """Return counts of tasks by lifecycle state.

        Returns:
            Dict with keys: pending, running, completed, failed.
        """
        completed = sum(1 for r in self._results.values() if r.success)
        failed = sum(1 for r in self._results.values() if not r.success)
        running = len(self._running)
        total = len(self._tasks)
        pending = total - completed - failed - running - len(self._cancelled)
        return {
            "pending": max(0, pending),
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": len(self._cancelled),
            "total": total,
        }

    def _scale_workers(self) -> int:
        """Recommend a worker count based on current CPU utilisation.

        Returns:
            Number of workers to use for the next layer.
        """
        now = time.monotonic()
        if not _PSUTIL_AVAILABLE or (now - self._last_cpu_check) < CPU_CHECK_INTERVAL:
            return self._current_workers

        cpu_pct = psutil.cpu_percent(interval=0.1) / 100.0
        self._last_cpu_check = now

        if cpu_pct > CPU_HIGH_THRESHOLD:
            # Reduce workers proportionally to how far over the threshold we are
            reduction = max(1, int((cpu_pct - CPU_HIGH_THRESHOLD) / 0.1))
            recommended = max(1, self._current_workers - reduction)
        else:
            # Allow gradual scale-up
            recommended = min(self._max_workers, self._current_workers + 1)

        if recommended != self._current_workers:
            logger.info(
                "Auto-scale: cpu=%.1f%% workers %d → %d",
                cpu_pct * 100,
                self._current_workers,
                recommended,
            )
            self._current_workers = recommended

        return self._current_workers


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def make_task(
    func: Callable[..., Any],
    *args: Any,
    task_id: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    priority: int = 0,
    timeout_seconds: float = 300.0,
    **kwargs: Any,
) -> Task:
    """Convenience constructor for Task.

    Args:
        func: Callable to execute.
        *args: Positional arguments.
        task_id: Optional explicit ID; auto-generated if omitted.
        dependencies: Task IDs that must complete before this one.
        priority: Scheduling priority (higher = sooner).
        timeout_seconds: Per-task timeout.
        **kwargs: Keyword arguments for *func*.

    Returns:
        A configured Task instance.
    """
    return Task(
        id=task_id or str(uuid.uuid4()),
        func=func,
        args=args,
        kwargs=kwargs,
        dependencies=dependencies or [],
        priority=priority,
        timeout_seconds=timeout_seconds,
    )
