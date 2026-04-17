from dataclasses import dataclass, field

@dataclass
class ExecutionSnapshot:
    snapshot_id: str
    request_id: str = ""
    captured_items: list[str] = field(default_factory=list)
    snapshot_state: str = "planned"
    notes: str = ""
