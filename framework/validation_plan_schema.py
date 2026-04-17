from dataclasses import dataclass, field

@dataclass
class ValidationPlan:
    plan_id: str
    request_id: str = ""
    gate_names: list[str] = field(default_factory=list)
    stop_on_failure: bool = True
    status: str = "planned"
