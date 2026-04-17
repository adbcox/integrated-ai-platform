from dataclasses import dataclass, field

@dataclass
class SessionWindowResult:
    result_id: str
    session_id: str = ""
    completed_window_items: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
