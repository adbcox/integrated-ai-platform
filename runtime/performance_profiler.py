"""
Performance profiler: capture execution timing metrics and performance analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union


class PerformanceProfiler:
    def __init__(self, session_id: str, job_id: str, task_id: Optional[str] = None, selected_profile: Optional[str] = None):
        self.session_id = session_id
        self.job_id = job_id
        self.task_id = task_id
        self.selected_profile = selected_profile
        self.timing_breakdown: Dict[str, float] = {}
        self.command_metrics: Dict[str, Any] = {}
        self.created_at = datetime.utcnow().isoformat()

    def record_stage_timing(self, stage: str, duration_seconds: float):
        self.timing_breakdown[stage] = round(duration_seconds, 3)

    def record_command_metrics(
        self,
        command: list,
        duration_seconds: float,
        exit_code: Optional[int] = None,
        stdout_length: int = 0,
        stderr_length: int = 0
    ):
        self.command_metrics = {
            "command": command,
            "command_duration_seconds": round(duration_seconds, 3),
            "exit_code": exit_code,
            "stdout_length_bytes": stdout_length,
            "stderr_length_bytes": stderr_length
        }

    def analyze_bottlenecks(self) -> Dict[str, Any]:
        if not self.timing_breakdown:
            return {}

        max_stage = max(self.timing_breakdown, key=self.timing_breakdown.get)
        max_duration = self.timing_breakdown[max_stage]
        total_duration = sum(self.timing_breakdown.values())

        if total_duration == 0:
            percentage = 0
        else:
            percentage = round((max_duration / total_duration) * 100, 1)

        return {
            "slowest_stage": max_stage,
            "slowest_stage_duration": max_duration,
            "percentage_of_total": percentage
        }

    def suggest_optimizations(self) -> list:
        suggestions = []
        bottleneck = self.analyze_bottlenecks()

        if not bottleneck:
            return suggestions

        slowest = bottleneck.get("slowest_stage")
        percentage = bottleneck.get("percentage_of_total", 0)

        if percentage > 50:
            if slowest == "command_execution":
                suggestions.append({
                    "suggestion": "Optimize command logic or consider parallel execution",
                    "potential_impact": f"Could reduce total execution time by up to {percentage}%"
                })
            elif slowest == "workspace_initialization":
                suggestions.append({
                    "suggestion": "Cache workspace setup or use pre-initialized templates",
                    "potential_impact": f"Could reduce total execution time by up to {percentage}%"
                })
            elif slowest == "artifact_emission":
                suggestions.append({
                    "suggestion": "Consider streaming artifacts or async emission",
                    "potential_impact": f"Could reduce total execution time by up to {percentage}%"
                })

        if self.timing_breakdown.get("profile_selection", 0) > 0.5:
            suggestions.append({
                "suggestion": "Profile selection is taking significant time; consider caching",
                "potential_impact": "Could reduce overhead"
            })

        return suggestions

    def build_profile(self) -> Dict[str, Any]:
        total_duration = sum(self.timing_breakdown.values())
        bottleneck = self.analyze_bottlenecks()

        profile = {
            "schema_version": "1.0",
            "profile_kind": "performance_profile",
            "session_id": self.session_id,
            "job_id": self.job_id,
            "task_id": self.task_id,
            "selected_profile": self.selected_profile,
            "timing_breakdown": {
                "total_duration_seconds": round(total_duration, 3),
                "stages": self.timing_breakdown
            },
            "command_metrics": self.command_metrics,
            "bottleneck_analysis": bottleneck,
            "optimization_suggestions": self.suggest_optimizations(),
            "created_at": self.created_at
        }

        return profile

    def emit_profile(self, output_path: Union[str, Path]) -> Dict[str, Any]:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        profile = self.build_profile()

        with open(output_path, "w") as f:
            json.dump(profile, f, indent=2, default=str)

        file_size = output_path.stat().st_size
        now = datetime.utcnow().isoformat()

        result = {
            "output_path": str(output_path),
            "size_bytes": file_size,
            "emission_timestamp": now,
            "status": "success"
        }

        return result
