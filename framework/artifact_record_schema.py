from dataclasses import dataclass, field

@dataclass
class ArtifactRecord:
    artifact_name: str
    artifact_path: str = ""
    artifact_type: str = ""
    created_by_session: str = ""
    tags: list[str] = field(default_factory=list)
