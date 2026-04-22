"""
Execution tracer: capture structured execution traces with stage transitions and events.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


class ExecutionTracer:
    def __init__(self, session_id: str, job_id: str, objective: Optional[str] = None):
        self.session_id = session_id
        self.job_id = job_id
        self.objective = objective
        self.trace_events: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()

    def record_stage_start(self, stage: str, details: Optional[Dict[str, Any]] = None):
        event = {
            "event_type": "stage_start",
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": 0,
            "details": details or {}
        }
        self.trace_events.append(event)

    def record_stage_complete(self, stage: str, duration_seconds: float, details: Optional[Dict[str, Any]] = None):
        event = {
            "event_type": "stage_complete",
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "details": details or {}
        }
        self.trace_events.append(event)

    def record_stage_error(self, stage: str, error_message: str, duration_seconds: float):
        event = {
            "event_type": "stage_error",
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "error": error_message
        }
        self.trace_events.append(event)

    def record_command_started(self, command: List[str]):
        event = {
            "event_type": "command_started",
            "stage": "command_execution",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": 0,
            "details": {"command": command}
        }
        self.trace_events.append(event)

    def record_command_completed(self, command: List[str], duration_seconds: float, exit_code: int):
        event = {
            "event_type": "command_completed",
            "stage": "command_execution",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "details": {
                "command": command,
                "exit_code": exit_code
            }
        }
        self.trace_events.append(event)

    def record_profile_selected(self, profile_name: str, backend: str, model: str):
        event = {
            "event_type": "profile_selected",
            "stage": "profile_selection",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": 0,
            "details": {
                "profile": profile_name,
                "backend": backend,
                "model": model
            }
        }
        self.trace_events.append(event)

    def record_artifact_emitted(self, artifact_path: str, size_bytes: int):
        event = {
            "event_type": "artifact_emitted",
            "stage": "artifact_emission",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": 0,
            "details": {
                "artifact_path": artifact_path,
                "size_bytes": size_bytes
            }
        }
        self.trace_events.append(event)

    def build_trace(self) -> Dict[str, Any]:
        total_duration = (datetime.utcnow() - self.start_time).total_seconds()
        trace = {
            "schema_version": "1.0",
            "trace_kind": "execution_trace",
            "session_id": self.session_id,
            "job_id": self.job_id,
            "objective": self.objective,
            "trace_events": self.trace_events,
            "total_duration_seconds": round(total_duration, 3),
            "created_at": self.start_time.isoformat()
        }
        return trace

    def emit_trace(self, output_path: Union[str, Path]) -> Dict[str, Any]:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        trace = self.build_trace()

        with open(output_path, "w") as f:
            json.dump(trace, f, indent=2, default=str)

        file_size = output_path.stat().st_size
        now = datetime.utcnow().isoformat()

        result = {
            "output_path": str(output_path),
            "size_bytes": file_size,
            "emission_timestamp": now,
            "status": "success"
        }
        return result
