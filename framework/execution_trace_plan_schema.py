from dataclasses import dataclass, field

@dataclass
class ExecutionTracePlan:
    plan_id: str
    request_id: str = ""
    trace_items: list[str] = field(default_factory=list)
    trace_state: str = "planned"
    notes: str = ""
