from dataclasses import dataclass, asdict
import json
from datetime import datetime, timezone

@dataclass(frozen=True)
class LocalRunReceiptSummary:
    package_id: str
    executor: str
    route: str
    validation_count: int
    artifact_count: int
    result: str
    summary_generated_at: str

class LocalRunReceiptSummaryBuilder:
    @staticmethod
    def from_dict(receipt_dict):
        return LocalRunReceiptSummary(
            package_id=receipt_dict['package_id'],
            executor=receipt_dict['executor'],
            route=receipt_dict['route'],
            validation_count=len(receipt_dict['validations_run']),
            artifact_count=len(receipt_dict['artifact_paths']),
            result=receipt_dict['result'],
            summary_generated_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def from_file(file_path):
        with open(file_path, 'r') as f:
            receipt_dict = json.load(f)
        return LocalRunReceiptSummaryBuilder.from_dict(receipt_dict)
