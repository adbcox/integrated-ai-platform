from dataclasses import dataclass, field

@dataclass
class ArtifactPackage:
    package_id: str
    request_id: str = ""
    artifact_paths: list[str] = field(default_factory=list)
    package_state: str = "planned"
    notes: str = ""
