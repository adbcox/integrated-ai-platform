from dataclasses import dataclass, field

@dataclass
class SessionWindowPlan:
    plan_id: str
    session_id: str = ""
    window_items: list[str] = field(default_factory=list)
    window_state: str = "planned"
    notes: str = ""
