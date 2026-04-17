from dataclasses import dataclass, field

@dataclass
class ExecutionSummary:
    summary_id: str
    request_id: str = ""
    outcome_class: str = ""
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    status: str = "complete"
