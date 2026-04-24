# Unified task executor that routes tasks intelligently
# Uses TaskRouter to classify and delegate to optimal backend

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from domains.router import TaskRouter, ExecutorType
from domains.coding import CodingDomain


@dataclass
class ExecutionResult:
    """Result of task execution."""
    success: bool
    executor_used: ExecutorType
    output: str
    commit_hash: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class UnifiedExecutor:
    """
    Unified executor that routes tasks to appropriate backend.

    Routes based on:
    - Simple edits → Local Aider 7B (fast, low-resource)
    - Bounded tasks → Local Aider 14B/32B (balanced)
    - Research/Architecture → Claude API (when available)
    - Complex → Orchestrator (multi-stage decomposition)
    """

    def __init__(self, framework_runtime=None):
        """
        Initialize unified executor.

        Args:
            framework_runtime: Optional framework runtime for job scheduler integration
        """
        self.router = TaskRouter()
        self.coding = CodingDomain(framework_runtime=framework_runtime)
        self.runtime = framework_runtime

    def execute(
        self,
        description: str,
        files: Optional[List[str]] = None,
        priority: int = 5,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """
        Execute task, routing to optimal executor.

        Args:
            description: Task description
            files: Target files
            priority: 1-10 (10=highest)
            timeout_seconds: Max execution time for local tasks

        Returns:
            ExecutionResult with success status and output
        """
        files = files or []

        # Classify task
        decision = self.router.classify_task(description, files)

        # Route to executor
        if self.router.should_delegate_to_api(decision):
            return self._execute_via_api(description, files, decision)
        else:
            return self._execute_local(description, files, decision, timeout_seconds)

    def _execute_local(
        self,
        description: str,
        files: List[str],
        decision,
        timeout_seconds: int,
    ) -> ExecutionResult:
        """Execute locally via Aider."""
        try:
            model = self.router.get_local_model(decision)
            result = self.coding.execute_task(
                task_description=description,
                files=files,
                model=model,
                timeout_seconds=timeout_seconds,
            )

            return ExecutionResult(
                success=result.get("success", False),
                executor_used=decision.executor,
                output=result.get("output", ""),
                commit_hash=result.get("commit_hash"),
                error=result.get("error"),
                metadata={
                    "category": decision.category.value,
                    "confidence": decision.confidence,
                    "model": model,
                },
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                executor_used=decision.executor,
                output="",
                error=str(e),
                metadata={"error_type": type(e).__name__},
            )

    def _execute_via_api(
        self,
        description: str,
        files: List[str],
        decision,
    ) -> ExecutionResult:
        """Execute via Claude API (placeholder for remote integration)."""
        # TODO: Integrate with Claude API when available
        # For now, this is a placeholder that indicates what would happen

        message = (
            f"Task routed to Claude API ({decision.executor.value}):\n"
            f"- Category: {decision.category.value}\n"
            f"- Description: {description}\n"
            f"- Files: {len(files)}"
        )

        if decision.subtasks:
            message += f"\n- Subtasks: {len(decision.subtasks)}"
            for i, subtask in enumerate(decision.subtasks[:3], 1):
                message += f"\n  {i}. {subtask[:60]}"

        return ExecutionResult(
            success=False,  # Not implemented yet
            executor_used=decision.executor,
            output="",
            error="Claude API execution not yet implemented - task would be delegated",
            metadata={
                "category": decision.category.value,
                "confidence": decision.confidence,
                "would_delegate": True,
                "message": message,
            },
        )

    def submit_job(
        self,
        description: str,
        files: Optional[List[str]] = None,
        priority: int = 5,
    ) -> Optional[str]:
        """
        Submit task via framework scheduler.

        Returns:
            job_id if submitted to scheduler, None if not applicable
        """
        files = files or []

        decision = self.router.classify_task(description, files)

        # Only submit local tasks to framework scheduler
        if self.router.should_delegate_to_api(decision):
            return None

        if not self.runtime:
            raise RuntimeError("Framework runtime required for job submission")

        return self.coding.submit_job(
            task_description=description,
            files=files,
            priority=priority,
        )

    def get_routing_info(
        self,
        description: str,
        files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get routing decision without executing."""
        files = files or []
        decision = self.router.classify_task(description, files)

        return {
            "category": decision.category.value,
            "executor": decision.executor.value,
            "confidence": decision.confidence,
            "will_delegate": self.router.should_delegate_to_api(decision),
            "files_count": decision.files_count,
            "description_len": decision.description_len,
            "reasoning": decision.reasoning,
            "subtasks": decision.subtasks,
        }
