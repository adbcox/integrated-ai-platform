"""Platform-level Prometheus metrics for the integrated-AI-platform.

Registers and exposes the key execution metrics that matter for the
Codex 5.1 replacement gate:

  aider_tasks_total{model, outcome}          - task completion counts
  aider_task_duration_seconds{model}         - execution latency histogram
  executor_tasks_total{executor, outcome}    - executor dispatch counts
  pipeline_stage_duration_seconds{stage}     - per-stage RAG/planning latency
  rag_retrieval_hits_total{stage}            - retrieval hit counts
  active_tasks                               - current in-flight task gauge
  learning_events_total{task_class}          - learning hook event counts
  process_cpu_percent / process_memory_bytes - from MetricsRegistry builtins

All metrics live in the global MetricsRegistry singleton so they are
automatically included in the /metrics endpoint served by metrics_server.py.
"""
from __future__ import annotations

import time
from typing import Optional

from .metrics_system import Counter, Gauge, Histogram, MetricsRegistry


def _reg() -> MetricsRegistry:
    return MetricsRegistry.instance()


# ---------------------------------------------------------------------------
# Aider / executor task metrics
# ---------------------------------------------------------------------------

def record_aider_task(model: str, outcome: str, duration_seconds: float) -> None:
    """Call after each aider task completes.

    Args:
        model: e.g. 'qwen2.5-coder:14b', 'deepseek-coder-v2'
        outcome: 'success' | 'failure' | 'timeout' | 'skipped'
        duration_seconds: wall-clock execution time
    """
    reg = _reg()
    _inc_counter(reg, f"aider_tasks_total_{_safe(model)}_{outcome}")
    _observe_histogram(reg, f"aider_task_duration_seconds_{_safe(model)}", duration_seconds)
    # Generic aggregated versions
    _inc_counter(reg, "aider_tasks_total", {"model": model, "outcome": outcome})
    _observe_histogram(reg, "aider_task_duration_seconds", duration_seconds, {"model": _safe(model)})


def record_executor_task(executor: str, outcome: str) -> None:
    """Call when an executor (ClaudeCode, Aider, etc.) finishes a task.

    Args:
        executor: 'claude_code' | 'aider' | 'dry_run'
        outcome: 'success' | 'failure'
    """
    _inc_counter(_reg(), "executor_tasks_total", {"executor": executor, "outcome": outcome})


def record_pipeline_stage(stage: str, duration_seconds: float) -> None:
    """Record duration for a RAG/planning stage pass.

    Args:
        stage: 'rag1' | 'rag2' | 'rag3' | 'rag4' | 'rag6' | 'stage3' | ...
        duration_seconds: elapsed seconds
    """
    _observe_histogram(_reg(), "pipeline_stage_duration_seconds",
                       duration_seconds, {"stage": stage})


def record_rag_hit(stage: str, hit: bool = True) -> None:
    """Record a retrieval hit or miss for a RAG stage.

    Args:
        stage: RAG stage name
        hit: True if the right file was retrieved
    """
    outcome = "hit" if hit else "miss"
    _inc_counter(_reg(), "rag_retrieval_hits_total", {"stage": stage, "outcome": outcome})


def record_learning_event(task_class: str) -> None:
    """Increment learning event counter when a LearningEvent is emitted.

    Args:
        task_class: e.g. 'CodeModification', 'GuardClause', 'Assertion'
    """
    _inc_counter(_reg(), "learning_events_total", {"task_class": _safe(task_class)})


# ---------------------------------------------------------------------------
# Active task gauge
# ---------------------------------------------------------------------------

_active_gauge: Optional[Gauge] = None


def task_started() -> None:
    """Call when a task enters the execution queue."""
    global _active_gauge
    if _active_gauge is None:
        _active_gauge = _reg().register(Gauge("active_tasks"))  # type: ignore[assignment]
    _active_gauge.inc()


def task_finished() -> None:
    """Call when a task leaves the execution queue (success or failure)."""
    global _active_gauge
    if _active_gauge is None:
        _active_gauge = _reg().register(Gauge("active_tasks"))  # type: ignore[assignment]
    _active_gauge.dec()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(s: str) -> str:
    return s.replace(":", "_").replace(".", "_").replace("-", "_").replace("/", "_")


def _inc_counter(reg: MetricsRegistry, name: str, labels: Optional[dict] = None) -> None:
    try:
        c = reg.get(name)
    except KeyError:
        c = reg.register(Counter(name, labels))
    if isinstance(c, Counter):
        c.inc()


def _observe_histogram(
    reg: MetricsRegistry,
    name: str,
    value: float,
    labels: Optional[dict] = None,
) -> None:
    try:
        h = reg.get(name)
    except KeyError:
        h = reg.register(Histogram(name, labels=labels))
    if isinstance(h, Histogram):
        h.observe(value)
