from dataclasses import dataclass, field

@dataclass
class ExecutionSnapshotResult:
    result_id: str
    request_id: str = ""
    result_items: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
