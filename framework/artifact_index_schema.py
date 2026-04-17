from dataclasses import dataclass, field

@dataclass
class ArtifactIndex:
    index_id: str
    artifact_names: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    request_id: str = ""
    status: str = "planned"
