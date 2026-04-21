"""UnifiedValidationArtifactV1: bundle validation evidence from a single package run."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class UnifiedValidationArtifactV1:
    package_id: str
    package_label: str
    validations_run: List[str]
    validation_results: Dict[str, bool]
    artifacts_produced: List[str]
    escalation_status: str
    final_outcome: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Derived helpers
    # ------------------------------------------------------------------ #

    @property
    def all_passed(self) -> bool:
        return all(self.validation_results.values()) if self.validation_results else False

    @property
    def pass_count(self) -> int:
        return sum(1 for v in self.validation_results.values() if v)

    @property
    def total_count(self) -> int:
        return len(self.validation_results)

    @property
    def pass_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.pass_count / self.total_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "package_label": self.package_label,
            "validations_run": self.validations_run,
            "validation_results": self.validation_results,
            "artifacts_produced": self.artifacts_produced,
            "escalation_status": self.escalation_status,
            "final_outcome": self.final_outcome,
            "generated_at": self.generated_at,
            "all_passed": self.all_passed,
            "pass_rate": self.pass_rate,
            "notes": self.notes,
        }

    # ------------------------------------------------------------------ #
    # Factory
    # ------------------------------------------------------------------ #

    @classmethod
    def build(
        cls,
        package_id: str,
        package_label: str,
        validation_results: Dict[str, bool],
        artifacts_produced: Optional[List[str]] = None,
        escalation_status: str = "NOT_ESCALATED",
        notes: Optional[List[str]] = None,
    ) -> "UnifiedValidationArtifactV1":
        all_ok = all(validation_results.values()) if validation_results else False
        final_outcome = "PASS" if all_ok else "FAIL"
        return cls(
            package_id=package_id,
            package_label=package_label,
            validations_run=list(validation_results.keys()),
            validation_results=validation_results,
            artifacts_produced=artifacts_produced or [],
            escalation_status=escalation_status,
            final_outcome=final_outcome,
            notes=notes or [],
        )
