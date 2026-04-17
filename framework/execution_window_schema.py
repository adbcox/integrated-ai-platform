from dataclasses import dataclass

@dataclass
class ExecutionWindow:
    window_id: str
    request_id: str = ""
    window_status: str = "planned"
    start_marker: str = ""
    end_marker: str = ""
