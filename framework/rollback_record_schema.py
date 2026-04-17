from dataclasses import dataclass, field

@dataclass
class RollbackRecord:
    rollback_id: str
    request_id: str = ""
    affected_files: list[str] = field(default_factory=list)
    rollback_reason: str = ""
    rollback_status: str = "not_needed"
