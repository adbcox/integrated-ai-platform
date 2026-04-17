from dataclasses import dataclass, field

@dataclass
class OutputBundle:
    bundle_id: str
    request_id: str = ""
    output_paths: list[str] = field(default_factory=list)
    bundle_state: str = "planned"
    notes: str = ""
