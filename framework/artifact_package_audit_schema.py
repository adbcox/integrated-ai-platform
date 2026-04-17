from dataclasses import dataclass, field

@dataclass
class ArtifactPackageAudit:
    audit_id: str
    package_id: str = ""
    audited_artifact_paths: list[str] = field(default_factory=list)
    audit_state: str = "complete"
    notes: str = ""
