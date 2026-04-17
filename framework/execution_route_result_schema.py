from dataclasses import dataclass

@dataclass
class ExecutionRouteResult:
    result_id: str
    request_id: str = ""
    selected_route: str = "ollama_local"
    result_reason: str = ""
    status: str = "complete"
