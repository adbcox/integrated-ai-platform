from dataclasses import dataclass, field

@dataclass
class ArtifactLinkIndex:
    index_id: str
    request_id: str = ""
    artifact_ids: list[str] = field(default_factory=list)
    linked_paths: list[str] = field(default_factory=list)
    status: str = "planned"
