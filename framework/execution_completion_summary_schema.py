from dataclasses import dataclass, field

@dataclass
class ExecutionCompletionSummary:
    summary_id: str
    request_id: str = ""
    completed_items: list[str] = field(default_factory=list)
    remaining_items: list[str] = field(default_factory=list)
    status: str = "complete"
