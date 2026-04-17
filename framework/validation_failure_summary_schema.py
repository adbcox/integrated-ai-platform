from dataclasses import dataclass, field

@dataclass
class ValidationFailureSummary:
    summary_id: str
    request_id: str = ""
    failure_items: list[str] = field(default_factory=list)
    summary_state: str = "complete"
    notes: str = ""
