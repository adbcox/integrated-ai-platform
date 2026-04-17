from dataclasses import dataclass, field

@dataclass
class ValidationPlanResult:
    result_id: str
    request_id: str = ""
    passed_items: list[str] = field(default_factory=list)
    failed_items: list[str] = field(default_factory=list)
    status: str = "complete"
