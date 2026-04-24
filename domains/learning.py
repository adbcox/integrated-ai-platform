#!/usr/bin/env python3
"""Learning domain: track execution metrics and auto-tune model selection."""

import sys
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, timedelta
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ExecutionRecord:
    """Record of a single task execution."""
    timestamp: str
    task_type: str  # 'coding', 'research', 'architecture', etc.
    description: str
    model: str
    executor: str  # 'LOCAL_AIDER', 'CLAUDE_CHAT', 'CLAUDE_CODE'
    success: bool
    duration_seconds: float
    error_type: Optional[str] = None  # e.g., 'timeout', 'syntax_error', 'llm_failure'
    tokens_used: int = 0
    exit_code: int = 0


@dataclass
class ModelRecommendation:
    """Recommendation for which model to use."""
    model: str
    executor: str
    confidence: float
    reason: str
    success_rate: float
    sample_count: int


class LearningDomain:
    """Track execution metrics and recommend model selection."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        self.db_path = self.repo_root / "artifacts" / "execution_metrics.jsonl"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: List[ExecutionRecord] = self._load_records()

    def _load_records(self) -> List[ExecutionRecord]:
        """Load execution records from disk."""
        records = []
        if self.db_path.exists():
            with open(self.db_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            records.append(ExecutionRecord(**data))
                        except (json.JSONDecodeError, TypeError):
                            continue
        return records

    def record_execution(
        self,
        task_type: str,
        description: str,
        model: str,
        executor: str,
        success: bool,
        duration_seconds: float,
        error_type: Optional[str] = None,
        tokens_used: int = 0,
        exit_code: int = 0,
    ) -> None:
        """Record a task execution."""
        record = ExecutionRecord(
            timestamp=datetime.utcnow().isoformat(),
            task_type=task_type,
            description=description,
            model=model,
            executor=executor,
            success=success,
            error_type=error_type,
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            exit_code=exit_code,
        )

        self.records.append(record)

        # Append to file
        with open(self.db_path, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def get_success_rate(
        self, task_type: str, model: Optional[str] = None
    ) -> float:
        """Get success rate for a task type (optionally filtered by model)."""
        filtered = [
            r
            for r in self.records
            if r.task_type == task_type and (model is None or r.model == model)
        ]

        if not filtered:
            return 0.0

        successes = sum(1 for r in filtered if r.success)
        return successes / len(filtered)

    def get_failure_patterns(
        self, task_type: str, limit: int = 5
    ) -> Dict[str, int]:
        """Get most common failure patterns for a task type."""
        failures = [
            r
            for r in self.records
            if r.task_type == task_type and not r.success and r.error_type
        ]

        error_counts: Dict[str, int] = {}
        for record in failures:
            error_counts[record.error_type] = (
                error_counts.get(record.error_type, 0) + 1
            )

        return dict(
            sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        )

    def get_average_time(self, task_type: str) -> float:
        """Get average execution time for a task type."""
        filtered = [r for r in self.records if r.task_type == task_type]

        if not filtered:
            return 0.0

        return statistics.mean(r.duration_seconds for r in filtered)

    def recommend_model(
        self, task_type: str, executor: str
    ) -> ModelRecommendation:
        """Recommend best model for a task type + executor.

        Returns: ModelRecommendation with model, executor, confidence, reason
        """
        # Get all models used for this task type + executor
        relevant = [
            r
            for r in self.records
            if r.task_type == task_type and r.executor == executor
        ]

        if not relevant:
            # Default recommendation based on executor
            defaults = {
                "LOCAL_AIDER": ("qwen2.5-coder:14b", "No history"),
                "CLAUDE_CHAT": ("claude-3.5-sonnet", "No history"),
                "CLAUDE_CODE": ("claude-opus", "No history"),
            }
            model, reason = defaults.get(executor, ("unknown", "No history"))
            return ModelRecommendation(
                model=model,
                executor=executor,
                confidence=0.5,
                reason=reason,
                success_rate=0.0,
                sample_count=0,
            )

        # Find model with highest success rate
        model_stats: Dict[str, Tuple[float, int]] = {}
        for model in set(r.model for r in relevant):
            success_rate = self.get_success_rate(task_type, model)
            count = sum(1 for r in relevant if r.model == model)
            model_stats[model] = (success_rate, count)

        # Rank by success rate, then by frequency (more data = higher confidence)
        best_model_name = max(
            model_stats.keys(),
            key=lambda m: (model_stats[m][0], model_stats[m][1]),
        )

        success_rate, count = model_stats[best_model_name]
        # Confidence based on success rate and sample size
        confidence = success_rate * min(count / 10, 1.0)

        return ModelRecommendation(
            model=best_model_name,
            executor=executor,
            confidence=confidence,
            reason=f"Best performer: {success_rate:.0%} on {count} tasks",
            success_rate=success_rate,
            sample_count=count,
        )

    def should_escalate(self, task_type: str) -> Tuple[bool, str]:
        """Determine if a task type should be escalated to higher-tier executor.

        Returns: (should_escalate, reason)
        """
        # Get recent records for this task type
        recent = [r for r in self.records if r.task_type == task_type]

        if len(recent) < 3:
            return False, "Insufficient data"

        # Check success rate (last 20 attempts)
        recent_20 = recent[-20:]
        success_rate = sum(1 for r in recent_20 if r.success) / len(recent_20)

        if success_rate < 0.5:
            return True, f"Low success rate: {success_rate:.0%} on last 20 attempts"

        # Check for repeated error patterns
        error_patterns = self.get_failure_patterns(task_type)
        if error_patterns:
            top_error, count = list(error_patterns.items())[0]
            if count >= 3 and success_rate < 0.7:
                return (
                    True,
                    f"Repeated {top_error} errors ({count}x) with {success_rate:.0%} success rate",
                )

        return False, "Performing well"

    def get_model_comparison(self, task_type: str) -> Dict[str, Dict]:
        """Compare performance of models for a task type."""
        relevant = [r for r in self.records if r.task_type == task_type]

        if not relevant:
            return {}

        comparison = {}
        for model in set(r.model for r in relevant):
            model_records = [r for r in relevant if r.model == model]
            success_rate = sum(1 for r in model_records if r.success) / len(
                model_records
            )
            avg_time = statistics.mean(r.duration_seconds for r in model_records)

            comparison[model] = {
                "success_rate": success_rate,
                "average_time_seconds": avg_time,
                "sample_count": len(model_records),
                "failures": sum(1 for r in model_records if not r.success),
            }

        return comparison

    def get_metrics_summary(self, task_type: Optional[str] = None) -> Dict:
        """Get performance summary."""
        if task_type:
            filtered = [r for r in self.records if r.task_type == task_type]
            label = task_type
        else:
            filtered = self.records
            label = "all"

        if not filtered:
            return {"total_executions": 0}

        success_rate = sum(1 for r in filtered if r.success) / len(filtered)
        avg_time = statistics.mean(r.duration_seconds for r in filtered)

        models_used = set(r.model for r in filtered)
        executors_used = set(r.executor for r in filtered)

        return {
            "task_type": label,
            "total_executions": len(filtered),
            "success_rate": success_rate,
            "average_time_seconds": avg_time,
            "models_used": list(models_used),
            "executors_used": list(executors_used),
            "failure_patterns": (
                self.get_failure_patterns(task_type) if task_type else {}
            ),
        }

    def get_all_task_types(self) -> List[str]:
        """Get all task types in history."""
        return sorted(set(r.task_type for r in self.records))

    def get_escalation_report(self) -> List[Tuple[str, bool, str]]:
        """Get escalation recommendations for all task types.

        Returns: [(task_type, should_escalate, reason), ...]
        """
        report = []
        for task_type in self.get_all_task_types():
            should_escalate, reason = self.should_escalate(task_type)
            report.append((task_type, should_escalate, reason))

        # Sort by escalation needed first
        return sorted(report, key=lambda x: not x[1])

    def recent_failures(self, limit: int = 10) -> List[ExecutionRecord]:
        """Get recent failures for analysis."""
        failures = [r for r in self.records if not r.success]
        return failures[-limit:]

    def prune_old_records(self, days: int = 90) -> int:
        """Remove records older than N days, return count removed."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        old_records = [
            r
            for r in self.records
            if datetime.fromisoformat(r.timestamp) < cutoff
        ]

        if not old_records:
            return 0

        # Rewrite file without old records
        new_records = [
            r
            for r in self.records
            if datetime.fromisoformat(r.timestamp) >= cutoff
        ]

        with open(self.db_path, "w") as f:
            for record in new_records:
                f.write(json.dumps(asdict(record)) + "\n")

        self.records = new_records
        return len(old_records)
