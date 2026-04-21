from dataclasses import dataclass, asdict
import json
from datetime import datetime, timezone

@dataclass(frozen=True)
class LocalLiveProofChain:
    package_id: str
    executor: str
    route: str
    evidence_inputs_seen: list[str]
    validation_count: int
    artifact_count: int
    final_result: str
    live_execution_signal: bool
    proof_generated_at: str

class LocalLiveProofChainBuilder:
    @staticmethod
    def from_files(baseline_path, summary_path, index_path, bundle_path):
        evidence_inputs_seen = []
        data = {}

        if baseline_path.exists():
            with open(baseline_path, 'r') as f:
                baseline_dict = json.load(f)
                evidence_inputs_seen.append("baseline_receipt")
                data.update({
                    "package_id": baseline_dict['package_id'],
                    "executor": baseline_dict['executor'],
                    "route": baseline_dict['route'],
                    "validation_count": len(baseline_dict.get('validations_run', [])),
                    "artifact_count": len(baseline_dict.get('artifact_paths', [])),
                    "final_result": baseline_dict['result']
                })
        else:
            raise FileNotFoundError(f"Baseline receipt not found at {baseline_path}")

        if summary_path.exists():
            with open(summary_path, 'r') as f:
                summary_dict = json.load(f)
                evidence_inputs_seen.append("summary")
                data["validation_count"] += summary_dict.get('validation_count', 0)
                data["artifact_count"] += summary_dict.get('artifact_count', 0)

        if index_path.exists():
            with open(index_path, 'r') as f:
                index_dict = json.load(f)
                evidence_inputs_seen.append("index")

        if bundle_path.exists():
            with open(bundle_path, 'r') as f:
                bundle_dict = json.load(f)
                evidence_inputs_seen.append("bundle")

        return LocalLiveProofChain(
            package_id=data.get('package_id', ""),
            executor=data.get('executor', ""),
            route=data.get('route', ""),
            evidence_inputs_seen=evidence_inputs_seen,
            validation_count=data.get('validation_count', 0),
            artifact_count=data.get('artifact_count', 0),
            final_result=data.get('final_result', ""),
            live_execution_signal=True,
            proof_generated_at=datetime.now(timezone.utc).isoformat()
        )
