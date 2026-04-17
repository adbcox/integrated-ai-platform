from dataclasses import dataclass

@dataclass
class ExecutionAttempt:
    attempt_id: str
    request_id: str = ""
    selected_route: str = "ollama_local"
    attempt_status: str = "planned"
    notes: str = ""
