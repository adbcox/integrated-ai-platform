from dataclasses import dataclass, field

@dataclass
class SessionWindowAudit:
    audit_id: str
    session_id: str = ""
    audited_window_items: list[str] = field(default_factory=list)
    audit_state: str = "complete"
    notes: str = ""
