from dataclasses import dataclass, field

@dataclass
class OutputBundleAudit:
    audit_id: str
    bundle_id: str = ""
    audited_paths: list[str] = field(default_factory=list)
    audit_state: str = "complete"
    notes: str = ""
