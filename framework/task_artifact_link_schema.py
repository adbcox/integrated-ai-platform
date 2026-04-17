from dataclasses import dataclass, field

@dataclass
class TaskArtifactLink:
    task_id: str
    session_id: str = ""
    artifact_name: str = ""
    artifact_path: str = ""
    link_type: str = ""
    tags: list[str] = field(default_factory=list)
