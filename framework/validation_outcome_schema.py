from dataclasses import dataclass, field

@dataclass
class ValidationOutcome:
    outcome_id: str
    plan_id: str = ""
    passed_gates: list[str] = field(default_factory=list)
    failed_gates: list[str] = field(default_factory=list)
    status: str = "complete"
