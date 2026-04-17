from dataclasses import dataclass

@dataclass
class RetryPolicy:
    policy_id: str
    max_attempts: int = 1
    retry_on_validation_failure: bool = False
    retry_on_execution_failure: bool = False
    status: str = "active"
