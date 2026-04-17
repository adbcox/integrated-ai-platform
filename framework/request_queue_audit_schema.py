from dataclasses import dataclass, field

@dataclass
class RequestQueueAudit:
    audit_id: str
    queue_id: str = ""
    audited_request_ids: list[str] = field(default_factory=list)
    audit_state: str = "complete"
    notes: str = ""
