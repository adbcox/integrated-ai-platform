from dataclasses import dataclass, field

@dataclass
class ValidationGateAuditResult:
    result_id: str
    request_id: str = ""
    passed_gate_ids: list[str] = field(default_factory=list)
    failed_gate_ids: list[str] = field(default_factory=list)
    status: str = "complete"
