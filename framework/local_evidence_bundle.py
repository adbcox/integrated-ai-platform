from dataclasses import dataclass, asdict
import json
from datetime import datetime, timezone

@dataclass(frozen=True)
class LocalEvidenceBundle:
    package_id: str
    executor: str
    route: str
    baseline_receipt_path: str
    summary_path: str
    report_index_path: str
    validation_count: int
    artifact_count: int
    final_result: str
    bundle_generated_at: str

class LocalEvidenceBundleBuilder:
    @staticmethod
    def from_files(baseline_path, summary_path, index_path):
        with open(baseline_path, 'r') as f:
            baseline_dict = json.load(f)
        with open(summary_path, 'r') as f:
            summary_dict = json.load(f)
        with open(index_path, 'r') as f:
            index_dict = json.load(f)

        return LocalEvidenceBundle(
            package_id=baseline_dict['package_id'],
            executor=baseline_dict['executor'],
            route=baseline_dict['route'],
            baseline_receipt_path=baseline_path,
            summary_path=summary_path,
            report_index_path=index_path,
            validation_count=summary_dict['validation_count'],
            artifact_count=summary_dict['artifact_count'],
            final_result=summary_dict['result'],
            bundle_generated_at=datetime.now(timezone.utc).isoformat(),
        )
