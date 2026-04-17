from dataclasses import dataclass, field

@dataclass
class FailureRecord:
    failure_id: str
    request_id: str = ""
    failure_type: str = ""
    affected_files: list[str] = field(default_factory=list)
    notes: str = ""
