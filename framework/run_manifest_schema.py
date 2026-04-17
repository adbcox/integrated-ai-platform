from dataclasses import dataclass, field

@dataclass
class RunManifest:
    manifest_id: str
    request_ids: list[str] = field(default_factory=list)
    target_files: list[str] = field(default_factory=list)
    selected_route: str = "ollama_local"
    status: str = "planned"
