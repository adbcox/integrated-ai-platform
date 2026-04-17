from dataclasses import dataclass, field

@dataclass
class PromptResult:
    result_id: str
    request_id: str = ""
    output_sections: list[str] = field(default_factory=list)
    result_status: str = "complete"
    notes: str = ""
