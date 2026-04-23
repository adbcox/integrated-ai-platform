from dataclasses import dataclass, field

@dataclass
class ExecutionSession:
    session_id: str
    baseline_commit: str = ""
    task_id: str = ""
    task_category: str = ""
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    model_route: str = "ollama_local"
    status: str = "planned"
