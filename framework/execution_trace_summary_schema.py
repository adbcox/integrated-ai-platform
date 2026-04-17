from dataclasses import dataclass, field

@dataclass
class ExecutionTraceSummary:
    summary_id: str
    request_id: str = ""
    included_trace_items: list[str] = field(default_factory=list)
    omitted_trace_items: list[str] = field(default_factory=list)
    status: str = "complete"
