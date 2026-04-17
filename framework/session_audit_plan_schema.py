from dataclasses import dataclass, field

@dataclass
class SessionAuditPlan:
    plan_id: str
    session_id: str = ""
    audit_items: list[str] = field(default_factory=list)
    audit_state: str = "planned"
    notes: str = ""
