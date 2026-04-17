from dataclasses import dataclass, field

@dataclass
class ExecutionRecordSummary:
    summary_id: str
    request_id: str = ""
    included_items: list[str] = field(default_factory=list)
    omitted_items: list[str] = field(default_factory=list)
    status: str = "complete"
