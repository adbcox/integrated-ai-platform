from dataclasses import dataclass

@dataclass
class ReviewRecord:
    review_id: str
    request_id: str = ""
    reviewer: str = ""
    review_status: str = "pending"
    notes: str = ""
