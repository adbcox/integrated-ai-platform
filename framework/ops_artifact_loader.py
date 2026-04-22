#!/usr/bin/env python3
"""OPS artifact loader: discovers and reads execution trace, failure record, and performance profile artifacts."""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class OpsArtifactLoader:
    """Loads and provides access to OPS artifacts from runtime executions."""

    def __init__(self, artifacts_root: Path = None):
        if artifacts_root is None:
            artifacts_root = Path(__file__).parent.parent / "artifacts"
        self.artifacts_root = artifacts_root
        self.runtime_runs_dir = artifacts_root / "runtime_runs"

    def discover_executions(self) -> List[Dict[str, Any]]:
        """Discover all execution runs and their associated artifacts."""
        executions = []
        if not self.runtime_runs_dir.exists():
            return executions

        for workspace_dir in self.runtime_runs_dir.iterdir():
            if not workspace_dir.is_dir():
                continue
            artifacts_dir = workspace_dir / "artifacts"
            if not artifacts_dir.exists():
                continue

            execution_info = {
                "workspace_id": workspace_dir.name,
                "artifacts_dir": str(artifacts_dir),
                "execution_trace": None,
                "failure_record": None,
                "performance_profile": None,
            }

            # Find artifacts
            for artifact_file in artifacts_dir.iterdir():
                if artifact_file.suffix != ".json":
                    continue

                if "execution_trace" in artifact_file.name:
                    execution_info["execution_trace"] = self._load_json(artifact_file)
                elif "failure_record" in artifact_file.name:
                    execution_info["failure_record"] = self._load_json(artifact_file)
                elif "performance_profile" in artifact_file.name:
                    execution_info["performance_profile"] = self._load_json(artifact_file)

            # Only include if has at least one OPS artifact
            if any(
                [
                    execution_info["execution_trace"],
                    execution_info["failure_record"],
                    execution_info["performance_profile"],
                ]
            ):
                executions.append(execution_info)

        return sorted(
            executions, key=lambda x: x.get("artifacts_dir", ""), reverse=True
        )

    def get_latest_execution(self) -> Optional[Dict[str, Any]]:
        """Get the most recent execution with OPS artifacts."""
        executions = self.discover_executions()
        return executions[0] if executions else None

    def get_execution_summary(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary statistics for an execution."""
        trace = execution.get("execution_trace", {})
        failure = execution.get("failure_record", {})
        profile = execution.get("performance_profile", {})

        session_id = trace.get("session_id", "unknown")
        job_id = trace.get("job_id", "unknown")

        # Extract stage summary from trace
        stages = {}
        if trace.get("trace_events"):
            for event in trace["trace_events"]:
                stage = event.get("stage", "unknown")
                event_type = event.get("event_type", "")
                duration = event.get("duration_seconds", 0)

                if stage not in stages:
                    stages[stage] = {
                        "duration_seconds": 0,
                        "event_count": 0,
                        "status": "unknown",
                    }

                if "complete" in event_type:
                    stages[stage]["status"] = "complete"
                elif "failed" in event_type:
                    stages[stage]["status"] = "failed"

                if duration > 0:
                    stages[stage]["duration_seconds"] += duration
                stages[stage]["event_count"] += 1

        return {
            "session_id": session_id,
            "job_id": job_id,
            "objective": trace.get("objective", "N/A"),
            "total_duration_seconds": trace.get("total_duration_seconds", 0),
            "stages": stages,
            "stage_count": len(stages),
            "has_failure": bool(failure),
            "failure_type": failure.get("failure_type", None),
            "has_profile": bool(profile),
            "slowest_stage": profile.get("bottleneck_analysis", {}).get("slowest_stage"),
            "bottleneck_percentage": profile.get("bottleneck_analysis", {}).get(
                "percentage_of_total"
            ),
            "created_at": trace.get("created_at", "N/A"),
        }

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """Safely load JSON file."""
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    def get_trace_events_display(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format trace events for UI display."""
        events = []
        if not trace.get("trace_events"):
            return events

        for event in trace["trace_events"]:
            display_event = {
                "event_type": event.get("event_type", ""),
                "stage": event.get("stage", ""),
                "timestamp": event.get("timestamp", ""),
                "duration_ms": int(event.get("duration_seconds", 0) * 1000),
                "details": event.get("details", {}),
            }
            events.append(display_event)

        return events

    def get_failure_details(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """Format failure record for UI display."""
        if not failure:
            return {}

        return {
            "failure_type": failure.get("failure_type", "unknown"),
            "root_cause": failure.get("root_cause", ""),
            "stage_failed": failure.get("stage_failed", ""),
            "command": failure.get("command_executed", []),
            "exit_code": failure.get("exit_code", None),
            "error_message": failure.get("error_message", ""),
            "recovery_suggestions": failure.get("recovery_suggestions", []),
            "timestamp": failure.get("timestamp", ""),
        }

    def get_performance_details(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Format performance profile for UI display."""
        if not profile:
            return {}

        timing = profile.get("timing_breakdown", {})
        bottleneck = profile.get("bottleneck_analysis", {})
        command_metrics = profile.get("command_metrics", {})

        return {
            "selected_profile": profile.get("selected_profile", ""),
            "total_duration_ms": int(timing.get("total_duration_seconds", 0) * 1000),
            "stages": {
                name: int(duration * 1000)
                for name, duration in timing.get("stages", {}).items()
            },
            "command_duration_ms": int(command_metrics.get("command_duration_seconds", 0) * 1000),
            "slowest_stage": bottleneck.get("slowest_stage", ""),
            "bottleneck_percentage": bottleneck.get("percentage_of_total", 0),
            "optimization_suggestions": profile.get("optimization_suggestions", []),
            "stdout_bytes": command_metrics.get("stdout_length_bytes", 0),
            "stderr_bytes": command_metrics.get("stderr_length_bytes", 0),
        }
