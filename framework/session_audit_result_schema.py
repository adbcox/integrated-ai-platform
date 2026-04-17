from dataclasses import dataclass, field

@dataclass
class SessionAuditResult:
    result_id: str
    session_id: str = ""
    completed_audit_items: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
