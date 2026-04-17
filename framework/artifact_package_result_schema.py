from dataclasses import dataclass, field

@dataclass
class ArtifactPackageResult:
    result_id: str
    package_id: str = ""
    materialized_artifact_paths: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
