from dataclasses import dataclass, field

@dataclass
class RequestBatch:
    batch_id: str
    request_ids: list[str] = field(default_factory=list)
    batch_route: str = "ollama_local"
    batch_state: str = "planned"
    notes: str = ""
