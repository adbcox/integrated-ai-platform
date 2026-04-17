from dataclasses import dataclass, field

@dataclass
class ArtifactManifest:
    manifest_id: str
    request_id: str = ""
    artifact_paths: list[str] = field(default_factory=list)
    manifest_status: str = "planned"
    notes: str = ""
