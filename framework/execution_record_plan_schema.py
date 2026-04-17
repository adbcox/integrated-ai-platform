from dataclasses import dataclass, field

@dataclass
class ExecutionRecordPlan:
    plan_id: str
    request_id: str = ""
    record_items: list[str] = field(default_factory=list)
    plan_state: str = "planned"
    notes: str = ""
