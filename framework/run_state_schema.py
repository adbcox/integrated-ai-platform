from dataclasses import dataclass

@dataclass
class RunState:
    state_id: str
    request_id: str = ""
    current_stage: str = ""
    state_status: str = "planned"
    notes: str = ""
