from dataclasses import dataclass

@dataclass
class ExecutionCheckpoint:
    checkpoint_id: str
    request_id: str = ""
    stage_name: str = ""
    checkpoint_status: str = "pending"
    notes: str = ""
