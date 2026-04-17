from dataclasses import dataclass, field

@dataclass
class ExecutionTraceResult:
    result_id: str
    request_id: str = ""
    completed_trace_items: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
