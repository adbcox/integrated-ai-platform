from dataclasses import dataclass, field

@dataclass
class RequestQueueResult:
    result_id: str
    queue_id: str = ""
    processed_request_ids: list[str] = field(default_factory=list)
    result_state: str = "complete"
    notes: str = ""
