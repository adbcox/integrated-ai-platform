#!/usr/bin/env python3
"""Full execution tracing, step replay, state snapshots, and diff visualization.

Records every step of a task execution, captures file-system snapshots at
each step, computes unified diffs between snapshots, and exports traces as
JSON or Markdown. Provides ASCII timeline visualization and performance profiling.
"""

from __future__ import annotations

import difflib
import json
import logging
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TraceStep:
    """A single recorded step within an execution trace.

    Attributes:
        step_id: Unique identifier for this step.
        operation: Human-readable name of the operation.
        inputs: Key-value mapping of inputs provided to the operation.
        outputs: Key-value mapping of outputs produced by the operation.
        timestamp: ISO-format UTC timestamp when the step was recorded.
        duration_ms: Elapsed time in milliseconds.
        git_diff: Unified diff string captured at this step (may be empty).
    """

    step_id: str
    operation: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    timestamp: str
    duration_ms: float = 0.0
    git_diff: str = ""


@dataclass
class ExecutionTrace:
    """A complete execution trace covering a full task lifecycle.

    Attributes:
        trace_id: Unique identifier for this trace.
        task_description: Human-readable description of the task being traced.
        steps: Ordered list of recorded steps.
        start_time: ISO-format UTC timestamp of trace start.
        end_time: ISO-format UTC timestamp of trace completion.
        success: Whether the overall task succeeded.
    """

    trace_id: str
    task_description: str
    steps: List[TraceStep]
    start_time: str
    end_time: str
    success: bool


@dataclass
class StateSnapshot:
    """A point-in-time snapshot of file contents.

    Attributes:
        snapshot_id: Unique identifier for this snapshot.
        trace_id: ID of the parent trace.
        step_id: ID of the step that triggered this snapshot.
        files: Mapping of file path → file content at snapshot time.
        git_sha: Current HEAD git SHA when snapshot was taken.
        timestamp: ISO-format UTC timestamp.
    """

    snapshot_id: str
    trace_id: str
    step_id: str
    files: Dict[str, str]
    git_sha: str
    timestamp: str


# ---------------------------------------------------------------------------
# Tracer
# ---------------------------------------------------------------------------


class ExecutionTracer:
    """Records and replays execution traces for audit and debugging.

    Traces are persisted to ``artifacts/traces/{trace_id}.json``.
    Snapshots are stored in-memory during a session and embedded in trace exports.

    Example::

        tracer = ExecutionTracer(repo_root="/path/to/repo")
        tid = tracer.start_trace("Improve ExecutorFactory")
        sid = tracer.record_step(tid, "read_file", {"path": "a.py"}, {"lines": 42})
        tracer.take_snapshot(tid, sid, ["a.py"])
        tracer.finish_trace(tid, success=True)
    """

    def __init__(
        self,
        repo_root: str,
        traces_dir: str = "artifacts/traces",
    ) -> None:
        """Initialise the tracer.

        Args:
            repo_root: Absolute path to the repository root.
            traces_dir: Directory for persisted trace files.
        """
        self.repo_root = Path(repo_root)
        td = Path(traces_dir)
        self._traces_dir = td if td.is_absolute() else self.repo_root / td
        self._traces_dir.mkdir(parents=True, exist_ok=True)

        # In-memory stores (keyed by trace_id / snapshot_id)
        self._active_traces: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, StateSnapshot] = {}

        logger.debug("ExecutionTracer initialised traces_dir=%s", self._traces_dir)

    # ------------------------------------------------------------------
    # Trace lifecycle
    # ------------------------------------------------------------------

    def start_trace(self, task_description: str) -> str:
        """Begin a new execution trace.

        Args:
            task_description: Human-readable description of the task.

        Returns:
            New trace ID string.
        """
        trace_id = str(uuid.uuid4())
        self._active_traces[trace_id] = {
            "trace_id": trace_id,
            "task_description": task_description,
            "steps": [],
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": "",
            "success": False,
        }
        logger.info("Trace started id=%s task=%r", trace_id, task_description[:60])
        return trace_id

    def record_step(
        self,
        trace_id: str,
        operation: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        duration_ms: float = 0.0,
    ) -> str:
        """Append a step to an active trace.

        Args:
            trace_id: ID of the trace to append to.
            operation: Name of the operation being recorded.
            inputs: Input parameters for the operation.
            outputs: Output values from the operation.
            duration_ms: Elapsed time for this step in milliseconds.

        Returns:
            New step ID string.

        Raises:
            KeyError: If trace_id is not an active trace.
        """
        if trace_id not in self._active_traces:
            raise KeyError(f"No active trace with id '{trace_id}'")

        step_id = str(uuid.uuid4())
        step = TraceStep(
            step_id=step_id,
            operation=operation,
            inputs=inputs,
            outputs=outputs,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
        )
        self._active_traces[trace_id]["steps"].append(asdict(step))
        logger.debug("Step recorded trace=%s op=%s step=%s", trace_id[:8], operation, step_id[:8])
        return step_id

    def take_snapshot(
        self,
        trace_id: str,
        step_id: str,
        files: List[str],
    ) -> StateSnapshot:
        """Capture the current content of a list of files.

        Args:
            trace_id: ID of the parent trace.
            step_id: ID of the step triggering this snapshot.
            files: List of file paths to capture (relative or absolute).

        Returns:
            A ``StateSnapshot`` with current file contents and git SHA.
        """
        snapshot_id = str(uuid.uuid4())
        file_contents: Dict[str, str] = {}

        for fp in files:
            resolved = self._resolve(fp)
            if resolved.is_file():
                try:
                    file_contents[str(fp)] = resolved.read_text(encoding="utf-8", errors="replace")
                except OSError as exc:
                    file_contents[str(fp)] = f"<read error: {exc}>"
            else:
                file_contents[str(fp)] = "<file not found>"

        sha = self._current_sha()
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            trace_id=trace_id,
            step_id=step_id,
            files=file_contents,
            git_sha=sha,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._snapshots[snapshot_id] = snapshot
        logger.debug("Snapshot taken id=%s files=%d", snapshot_id[:8], len(file_contents))
        return snapshot

    def get_diff(
        self,
        before_snapshot: StateSnapshot,
        after_snapshot: StateSnapshot,
    ) -> Dict[str, str]:
        """Compute unified diffs between two snapshots.

        Args:
            before_snapshot: Snapshot taken before changes.
            after_snapshot: Snapshot taken after changes.

        Returns:
            Dict mapping file path → unified diff string.
            Only includes files that changed.
        """
        diffs: Dict[str, str] = {}
        all_files = set(before_snapshot.files) | set(after_snapshot.files)

        for fp in all_files:
            before_lines = before_snapshot.files.get(fp, "").splitlines(keepends=True)
            after_lines = after_snapshot.files.get(fp, "").splitlines(keepends=True)

            if before_lines == after_lines:
                continue

            diff_lines = list(
                difflib.unified_diff(
                    before_lines,
                    after_lines,
                    fromfile=f"before/{fp}",
                    tofile=f"after/{fp}",
                )
            )
            if diff_lines:
                diffs[fp] = "".join(diff_lines)

        return diffs

    def finish_trace(self, trace_id: str, success: bool) -> ExecutionTrace:
        """Complete an active trace and persist it to disk.

        Args:
            trace_id: ID of the trace to finish.
            success: Whether the task succeeded.

        Returns:
            The completed ``ExecutionTrace``.

        Raises:
            KeyError: If trace_id is not an active trace.
        """
        if trace_id not in self._active_traces:
            raise KeyError(f"No active trace with id '{trace_id}'")

        raw = self._active_traces.pop(trace_id)
        raw["end_time"] = datetime.now(timezone.utc).isoformat()
        raw["success"] = success

        steps = [TraceStep(**s) for s in raw["steps"]]
        trace = ExecutionTrace(
            trace_id=raw["trace_id"],
            task_description=raw["task_description"],
            steps=steps,
            start_time=raw["start_time"],
            end_time=raw["end_time"],
            success=success,
        )

        self._persist_trace(trace)
        logger.info("Trace finished id=%s success=%s steps=%d", trace_id[:8], success, len(steps))
        return trace

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def replay(
        self,
        trace_id: str,
        up_to_step: Optional[int] = None,
    ) -> List[TraceStep]:
        """Return steps from a saved trace for review or replay.

        Args:
            trace_id: ID of the trace to replay.
            up_to_step: If provided, return only steps 0..up_to_step (exclusive).

        Returns:
            List of ``TraceStep`` instances.
        """
        trace = self.get_trace(trace_id)
        if trace is None:
            logger.warning("Replay: trace %s not found", trace_id)
            return []
        steps = trace.steps
        if up_to_step is not None:
            steps = steps[:up_to_step]
        logger.debug("Replay trace=%s steps=%d", trace_id[:8], len(steps))
        return steps

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Load a persisted trace by ID.

        Args:
            trace_id: Trace identifier.

        Returns:
            ``ExecutionTrace`` if found, None otherwise.
        """
        # Check active first
        if trace_id in self._active_traces:
            raw = self._active_traces[trace_id]
            steps = [TraceStep(**s) for s in raw["steps"]]
            return ExecutionTrace(
                trace_id=raw["trace_id"],
                task_description=raw["task_description"],
                steps=steps,
                start_time=raw["start_time"],
                end_time=raw.get("end_time", ""),
                success=raw.get("success", False),
            )

        trace_file = self._traces_dir / f"{trace_id}.json"
        if not trace_file.is_file():
            return None

        try:
            data = json.loads(trace_file.read_text(encoding="utf-8"))
            steps = [TraceStep(**s) for s in data.get("steps", [])]
            return ExecutionTrace(
                trace_id=data["trace_id"],
                task_description=data["task_description"],
                steps=steps,
                start_time=data["start_time"],
                end_time=data["end_time"],
                success=data["success"],
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error("Failed to load trace %s: %s", trace_id, exc)
            return None

    def list_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List persisted traces, most recent first.

        Args:
            limit: Maximum number of traces to return.

        Returns:
            List of summary dicts with keys: id, task, success, duration, steps_count.
        """
        files = sorted(
            self._traces_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        summaries: List[Dict[str, Any]] = []
        for fp in files[:limit]:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                start = data.get("start_time", "")
                end = data.get("end_time", "")
                duration = self._iso_diff_seconds(start, end)
                summaries.append(
                    {
                        "id": data.get("trace_id", fp.stem),
                        "task": data.get("task_description", ""),
                        "success": data.get("success", False),
                        "duration_seconds": duration,
                        "steps_count": len(data.get("steps", [])),
                    }
                )
            except Exception:  # pylint: disable=broad-except
                pass

        return summaries

    # ------------------------------------------------------------------
    # Visualization and profiling
    # ------------------------------------------------------------------

    def visualize_timeline(self, trace_id: str) -> str:
        """Generate an ASCII timeline of steps with durations.

        Args:
            trace_id: Trace to visualize.

        Returns:
            Multi-line ASCII string representing the timeline.
        """
        trace = self.get_trace(trace_id)
        if trace is None:
            return f"[Trace {trace_id} not found]"

        lines: List[str] = [
            f"Trace: {trace_id[:8]}  Task: {trace.task_description[:60]}",
            f"Start: {trace.start_time}  Success: {trace.success}",
            "-" * 72,
        ]

        max_dur = max((s.duration_ms for s in trace.steps), default=1.0) or 1.0
        bar_width = 30

        for i, step in enumerate(trace.steps):
            bar_len = max(1, int((step.duration_ms / max_dur) * bar_width))
            bar = "#" * bar_len
            lines.append(
                f"  {i+1:>3}. {step.operation:<25} [{bar:<{bar_width}}] {step.duration_ms:7.1f}ms"
            )

        lines.append("-" * 72)
        total_ms = sum(s.duration_ms for s in trace.steps)
        lines.append(f"  Total: {total_ms:.1f}ms  Steps: {len(trace.steps)}")
        return "\n".join(lines)

    def profile_trace(self, trace_id: str) -> Dict[str, Any]:
        """Profile a trace to identify time-per-step and bottlenecks.

        Args:
            trace_id: Trace to profile.

        Returns:
            Dict with: time_per_step, slowest_steps, bottlenecks.
        """
        trace = self.get_trace(trace_id)
        if trace is None:
            return {"error": f"Trace {trace_id} not found"}

        time_per_step = {s.step_id: s.duration_ms for s in trace.steps}
        sorted_steps = sorted(trace.steps, key=lambda s: s.duration_ms, reverse=True)
        slowest = [
            {"step_id": s.step_id, "operation": s.operation, "duration_ms": s.duration_ms}
            for s in sorted_steps[:5]
        ]
        total_ms = sum(s.duration_ms for s in trace.steps)
        bottlenecks = [
            s["operation"]
            for s in slowest
            if total_ms > 0 and s["duration_ms"] / total_ms > 0.25
        ]

        return {
            "time_per_step": time_per_step,
            "slowest_steps": slowest,
            "bottlenecks": bottlenecks,
            "total_ms": total_ms,
            "step_count": len(trace.steps),
        }

    def export_trace(self, trace_id: str, format: str = "json") -> str:
        """Export a trace as JSON or Markdown.

        Args:
            trace_id: Trace to export.
            format: Either "json" or "markdown".

        Returns:
            Serialized trace string.
        """
        trace = self.get_trace(trace_id)
        if trace is None:
            return f"{{\"error\": \"Trace {trace_id} not found\"}}"

        if format == "json":
            return json.dumps(
                {
                    "trace_id": trace.trace_id,
                    "task_description": trace.task_description,
                    "start_time": trace.start_time,
                    "end_time": trace.end_time,
                    "success": trace.success,
                    "steps": [asdict(s) for s in trace.steps],
                },
                indent=2,
            )

        # Markdown format
        lines = [
            f"# Execution Trace: `{trace_id[:8]}`",
            f"",
            f"**Task**: {trace.task_description}",
            f"**Status**: {'SUCCESS' if trace.success else 'FAILED'}",
            f"**Start**: {trace.start_time}",
            f"**End**: {trace.end_time}",
            f"",
            f"## Steps ({len(trace.steps)})",
            "",
        ]
        for i, step in enumerate(trace.steps):
            lines.append(f"### Step {i+1}: `{step.operation}`")
            lines.append(f"- **Duration**: {step.duration_ms:.1f}ms")
            lines.append(f"- **Timestamp**: {step.timestamp}")
            if step.inputs:
                lines.append(f"- **Inputs**: `{json.dumps(step.inputs)[:120]}`")
            if step.outputs:
                lines.append(f"- **Outputs**: `{json.dumps(step.outputs)[:120]}`")
            if step.git_diff:
                lines.append(f"\n```diff\n{step.git_diff[:500]}\n```")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist_trace(self, trace: ExecutionTrace) -> None:
        """Write a finished trace to disk.

        Args:
            trace: The completed trace to save.
        """
        out_path = self._traces_dir / f"{trace.trace_id}.json"
        data = {
            "trace_id": trace.trace_id,
            "task_description": trace.task_description,
            "steps": [asdict(s) for s in trace.steps],
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "success": trace.success,
        }
        try:
            out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.debug("Trace persisted: %s", out_path)
        except OSError as exc:
            logger.error("Failed to persist trace %s: %s", trace.trace_id, exc)

    def _resolve(self, file_path: str) -> Path:
        """Resolve a file path relative to repo_root if not absolute.

        Args:
            file_path: Path string.

        Returns:
            Resolved ``Path``.
        """
        p = Path(file_path)
        return p if p.is_absolute() else self.repo_root / p

    def _current_sha(self) -> str:
        """Return current HEAD git SHA.

        Returns:
            SHA string, or empty string on failure.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=10,
            )
            return result.stdout.strip()
        except Exception:  # pylint: disable=broad-except
            return ""

    @staticmethod
    def _iso_diff_seconds(start: str, end: str) -> float:
        """Compute elapsed seconds between two ISO timestamps.

        Args:
            start: ISO datetime string.
            end: ISO datetime string.

        Returns:
            Elapsed seconds, or 0.0 on parse failure.
        """
        try:
            from datetime import datetime as _dt
            fmt = "%Y-%m-%dT%H:%M:%S.%f+00:00"
            # Handle both Z and +00:00 suffixes
            def parse_iso(s: str) -> _dt:
                for sfx, replacement in [("Z", "+00:00"), ("+00:00", "+00:00")]:
                    if s.endswith(sfx):
                        s = s[:-len(sfx)] + "+00:00"
                        break
                return _dt.fromisoformat(s)

            t_start = parse_iso(start)
            t_end = parse_iso(end)
            return (t_end - t_start).total_seconds()
        except Exception:  # pylint: disable=broad-except
            return 0.0
