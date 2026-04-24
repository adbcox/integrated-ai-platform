from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.learning import LearningDomain


class ExecutorType(Enum):
    LOCAL_AIDER = "local_aider"
    CLAUDE_CHAT = "claude_chat"
    CLAUDE_CODE = "claude_code"


@dataclass
class TaskRoute:
    executor: ExecutorType
    model: str
    confidence: float
    reasoning: str


class TaskRouter:
    """Routes tasks to optimal executor based on classification and learning."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        try:
            self.learning = LearningDomain(self.repo_root)
        except Exception:
            self.learning = None

    def _infer_task_type(self, description: str, files: Optional[List[str]] = None) -> str:
        """Infer task type from description and context."""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["search", "find", "latest", "current", "what is"]):
            return "research"
        if any(kw in desc_lower for kw in ["architecture", "design", "plan", "strategy"]):
            return "architecture"
        if files:
            return "coding"

        return "general"

    def classify(self, description: str, files: Optional[List[str]] = None) -> TaskRoute:
        """Classify and route task using learning or keyword-based fallback."""
        task_type = self._infer_task_type(description, files)
        desc_lower = description.lower()

        # Try learning-based recommendation first
        if self.learning and task_type == "coding" and files:
            # Check if we have execution history for this task type
            task_types = self.learning.get_all_task_types()
            if "coding" in task_types:
                # Try LOCAL_AIDER first (most cost-effective)
                rec = self.learning.recommend_model("coding", "LOCAL_AIDER")
                if rec.confidence >= 0.6:
                    return TaskRoute(
                        ExecutorType.LOCAL_AIDER,
                        rec.model,
                        rec.confidence,
                        f"Learning-tuned: {rec.reason}",
                    )

                # Check if escalation is recommended
                should_escalate, escalation_reason = self.learning.should_escalate(
                    "coding"
                )
                if should_escalate:
                    rec = self.learning.recommend_model("coding", "CLAUDE_CODE")
                    return TaskRoute(
                        ExecutorType.CLAUDE_CODE,
                        rec.model,
                        rec.confidence,
                        f"Escalated: {escalation_reason}",
                    )

        # Keyword-based fallback routing
        # Research/current info
        if any(
            kw in desc_lower for kw in ["search", "find", "latest", "current", "what is"]
        ):
            return TaskRoute(
                ExecutorType.CLAUDE_CHAT, "sonnet-4", 0.9, "Requires web search"
            )

        # Architecture/design
        if any(
            kw in desc_lower for kw in ["architecture", "design", "plan", "strategy"]
        ):
            return TaskRoute(
                ExecutorType.CLAUDE_CODE, "sonnet-4", 0.85, "Architectural work"
            )

        # Coding tasks
        if files:
            if len(files) <= 2 and len(description) < 100:
                return TaskRoute(
                    ExecutorType.LOCAL_AIDER,
                    "qwen2.5-coder:7b",
                    0.95,
                    "Simple coding",
                )
            elif len(files) <= 5:
                return TaskRoute(
                    ExecutorType.LOCAL_AIDER,
                    "qwen2.5-coder:14b",
                    0.9,
                    "Medium coding",
                )
            else:
                return TaskRoute(
                    ExecutorType.CLAUDE_CODE, "sonnet-4", 0.7, ">5 files - needs planning"
                )

        # Default
        return TaskRoute(
            ExecutorType.CLAUDE_CHAT, "sonnet-4", 0.6, "Ambiguous"
        )
