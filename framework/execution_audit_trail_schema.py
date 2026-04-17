from dataclasses import dataclass, field

@dataclass
class ExecutionAuditTrail:
    trail_id: str
    request_id: str = ""
    events: list[str] = field(default_factory=list)
    selected_route: str = "ollama_local"
    status: str = "complete"
