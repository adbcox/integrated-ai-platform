from dataclasses import dataclass, field

@dataclass
class ReviewSummary:
    summary_id: str
    request_id: str = ""
    reviewers: list[str] = field(default_factory=list)
    decision: str = ""
    status: str = "complete"
