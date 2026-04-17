from dataclasses import dataclass

@dataclass
class ExecutionDecision:
    decision_id: str
    request_id: str = ""
    selected_route: str = "ollama_local"
    decision_reason: str = ""
    status: str = "planned"
