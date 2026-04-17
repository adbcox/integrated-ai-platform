from dataclasses import dataclass, field

@dataclass
class ValidationSessionRecord:
    record_id: str
    session_id: str = ""
    gate_ids: list[str] = field(default_factory=list)
    validation_state: str = "planned"
    notes: str = ""
