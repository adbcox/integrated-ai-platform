from dataclasses import dataclass, field

@dataclass
class ExecutionReport:
    report_id: str
    request_id: str = ""
    outcome_class: str = ""
    validations_run: list[str] = field(default_factory=list)
    summary: str = ""
    status: str = "complete"
