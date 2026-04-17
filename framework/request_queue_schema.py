from dataclasses import dataclass, field

@dataclass
class RequestQueue:
    queue_id: str
    request_ids: list[str] = field(default_factory=list)
    queue_state: str = "planned"
    selected_route: str = "ollama_local"
    notes: str = ""
