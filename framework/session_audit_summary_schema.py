from dataclasses import dataclass, field

@dataclass
class SessionAuditSummary:
    summary_id: str
    session_id: str = ""
    passed_items: list[str] = field(default_factory=list)
    failed_items: list[str] = field(default_factory=list)
    status: str = "complete"
