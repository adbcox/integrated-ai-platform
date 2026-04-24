from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


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
    """Routes tasks to optimal executor based on classification."""

    def classify(self, description: str, files: Optional[List[str]] = None) -> TaskRoute:
        """Classify and route task."""
        desc_lower = description.lower()

        # Research/current info
        if any(kw in desc_lower for kw in ['search', 'find', 'latest', 'current', 'what is']):
            return TaskRoute(ExecutorType.CLAUDE_CHAT, "sonnet-4", 0.9, "Requires web search")

        # Architecture/design
        if any(kw in desc_lower for kw in ['architecture', 'design', 'plan', 'strategy']):
            return TaskRoute(ExecutorType.CLAUDE_CODE, "sonnet-4", 0.85, "Architectural work")

        # Coding tasks
        if files:
            if len(files) <= 2 and len(description) < 100:
                return TaskRoute(ExecutorType.LOCAL_AIDER, "qwen2.5-coder:7b", 0.95, "Simple coding")
            elif len(files) <= 5:
                return TaskRoute(ExecutorType.LOCAL_AIDER, "qwen2.5-coder:14b", 0.9, "Medium coding")
            else:
                return TaskRoute(ExecutorType.CLAUDE_CODE, "sonnet-4", 0.7, ">5 files - needs planning")

        # Default
        return TaskRoute(ExecutorType.CLAUDE_CHAT, "sonnet-4", 0.6, "Ambiguous")
