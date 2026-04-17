from dataclasses import dataclass

@dataclass
class CompletionRecord:
    record_id: str
    request_id: str = ""
    completion_state: str = "planned"
    completion_reason: str = ""
    status: str = "complete"
