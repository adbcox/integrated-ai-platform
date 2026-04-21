from dataclasses import dataclass, asdict
import json

@dataclass(frozen=True)
class LocalRunBaselineReceipt:
    package_id: str
    executor: str
    route: str
    validations_run: list[str]
    validation_passed: bool
    changed_files: list[str]
    artifact_paths: list[str]
    result: str
    recorded_at: str

@dataclass
class LocalRunBaselineReceiptWriter:
    def write(self, receipt: LocalRunBaselineReceipt, output_path: str) -> None:
        with open(output_path, 'w') as f:
            json.dump(asdict(receipt), f, indent=2)
