from dataclasses import dataclass, field

@dataclass
class OutputBundleResult:
    result_id: str
    bundle_id: str = ""
    materialized_paths: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
