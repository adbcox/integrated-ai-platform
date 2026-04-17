from dataclasses import dataclass, field

@dataclass
class SessionPromptResult:
    result_id: str
    session_id: str = ""
    output_ids: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
