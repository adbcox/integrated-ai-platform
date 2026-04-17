from dataclasses import dataclass, field

@dataclass
class RequestBatchResult:
    result_id: str
    batch_id: str = ""
    completed_request_ids: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
