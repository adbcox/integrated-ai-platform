from dataclasses import dataclass, field

@dataclass
class RunRequest:
    request_id: str
    session_id: str = ""
    task_id: str = ""
    requested_files: list[str] = field(default_factory=list)
    model_route: str = "ollama_local"
    status: str = "planned"
