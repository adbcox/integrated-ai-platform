from dataclasses import dataclass, field

@dataclass
class ExecutionEnvelope:
    envelope_id: str
    request_id: str = ""
    selected_route: str = "ollama_local"
    target_files: list[str] = field(default_factory=list)
    status: str = "planned"
