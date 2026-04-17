from dataclasses import dataclass, field

@dataclass
class ExecutionRouteAudit:
    audit_id: str
    request_id: str = ""
    audited_routes: list[str] = field(default_factory=list)
    audit_state: str = "complete"
    notes: str = ""
