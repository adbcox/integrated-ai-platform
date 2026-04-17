from dataclasses import dataclass, field

@dataclass
class ValidationSummary:
    summary_id: str
    request_id: str = ""
    passed_gates: list[str] = field(default_factory=list)
    failed_gates: list[str] = field(default_factory=list)
    status: str = "complete"
