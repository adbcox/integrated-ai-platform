from dataclasses import dataclass

@dataclass
class ApprovalRecord:
    approval_id: str
    request_id: str = ""
    approved_by: str = ""
    approval_status: str = "pending"
    notes: str = ""
