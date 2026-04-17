from dataclasses import dataclass, field

@dataclass
class GateAudit:
    audit_id: str
    request_id: str = ""
    gate_names: list[str] = field(default_factory=list)
    failed_gate_names: list[str] = field(default_factory=list)
    status: str = "complete"
