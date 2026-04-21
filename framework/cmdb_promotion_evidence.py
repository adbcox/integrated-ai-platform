"""CmdbPromotionEvidence — LAPC1 P7.

Evaluates five local CMDB proof criteria against live governance state.
No governance writes. Local governance files only.
Inspection gate confirmed:
  CmdbAuthorityRecord fields include: current_phase, contract_version, phases_count, next_package_class
  evaluate_cmdb_gate() with no class -> gate_pass
  evaluate_cmdb_gate('invalid_xyz') -> gate_block
  evaluate_cmdb_gate('capability_session') -> gate_pass
  CmdbGateDecision fields: result, allowed_class, current_phase, reason, evaluated_at
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from framework.cmdb_authority_pilot import CmdbAuthorityPilot as _CmdbAuthorityPilot, CmdbAuthorityRecord as _CmdbAuthorityRecord
from framework.cmdb_integration_gate import evaluate_cmdb_gate as _evaluate_cmdb_gate, CmdbGateDecision as _CmdbGateDecision, GATE_PASS as _GATE_PASS, GATE_BLOCK as _GATE_BLOCK

assert "current_phase" in _CmdbAuthorityRecord.__dataclass_fields__, "INTERFACE MISMATCH: CmdbAuthorityRecord.current_phase"
assert "contract_version" in _CmdbAuthorityRecord.__dataclass_fields__, "INTERFACE MISMATCH: CmdbAuthorityRecord.contract_version"
assert "phases_count" in _CmdbAuthorityRecord.__dataclass_fields__, "INTERFACE MISMATCH: CmdbAuthorityRecord.phases_count"
assert "next_package_class" in _CmdbAuthorityRecord.__dataclass_fields__, "INTERFACE MISMATCH: CmdbAuthorityRecord.next_package_class"
assert "result" in _CmdbGateDecision.__dataclass_fields__, "INTERFACE MISMATCH: CmdbGateDecision.result"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "cmdb_promotion_evidence"

CMDB_PROOF_SUFFICIENT = "cmdb_proof_sufficient"
CMDB_PROOF_INSUFFICIENT = "cmdb_proof_insufficient"

CMDB_PROOF_CRITERIA = (
    "current_phase_json_readable",
    "authority_record_non_default",
    "gate_evaluates_no_class",
    "gate_blocks_invalid_class",
    "gate_passes_permitted_class",
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbProofCriterionResult:
    criterion: str
    passed: bool
    observed: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "criterion": self.criterion,
            "passed": self.passed,
            "observed": self.observed,
            "detail": self.detail,
        }


@dataclass
class CmdbEvidenceReport:
    criterion_results: list
    overall_result: str
    criteria_passed: int
    criteria_total: int
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "overall_result": self.overall_result,
            "criteria_passed": self.criteria_passed,
            "criteria_total": self.criteria_total,
            "generated_at": self.generated_at,
            "criterion_results": [r.to_dict() for r in self.criterion_results],
        }


def evaluate_cmdb_promotion_evidence(
    *,
    governance_dir: Optional[Path] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> CmdbEvidenceReport:
    kwargs = {}
    if governance_dir is not None:
        kwargs["governance_dir"] = Path(governance_dir)

    results = []

    # Criterion 1: current_phase_json_readable
    try:
        pilot = _CmdbAuthorityPilot(**kwargs) if kwargs else _CmdbAuthorityPilot()
        record = pilot.read_authority()
        readable = True
        observed_phase = str(record.current_phase)
    except Exception as exc:
        readable = False
        observed_phase = f"exception: {exc}"
    results.append(CmdbProofCriterionResult(
        criterion="current_phase_json_readable",
        passed=readable,
        observed=observed_phase,
        detail="governance/current_phase.json must be readable and parseable",
    ))

    # Criterion 2: authority_record_non_default
    if readable:
        non_default = (
            record.current_phase != ""
            and record.contract_version not in ("", "unknown")
            and record.phases_count > 0
        )
        observed_rec = f"phase={record.current_phase} version={record.contract_version} phases={record.phases_count}"
    else:
        non_default = False
        observed_rec = "unreadable"
    results.append(CmdbProofCriterionResult(
        criterion="authority_record_non_default",
        passed=non_default,
        observed=observed_rec,
        detail="Authority record must have non-empty phase, version, and phases_count > 0",
    ))

    # Criterion 3: gate_evaluates_no_class
    try:
        d1 = _evaluate_cmdb_gate()
        gate_no_class_pass = (d1.result == _GATE_PASS)
        observed_gate1 = d1.result
    except Exception as exc:
        gate_no_class_pass = False
        observed_gate1 = f"exception: {exc}"
    results.append(CmdbProofCriterionResult(
        criterion="gate_evaluates_no_class",
        passed=gate_no_class_pass,
        observed=observed_gate1,
        detail="evaluate_cmdb_gate() with no class must return gate_pass",
    ))

    # Criterion 4: gate_blocks_invalid_class
    try:
        d2 = _evaluate_cmdb_gate(requested_class="invalid_xyz_not_a_real_class")
        gate_blocks = (d2.result == _GATE_BLOCK)
        observed_gate2 = d2.result
    except Exception as exc:
        gate_blocks = False
        observed_gate2 = f"exception: {exc}"
    results.append(CmdbProofCriterionResult(
        criterion="gate_blocks_invalid_class",
        passed=gate_blocks,
        observed=observed_gate2,
        detail="evaluate_cmdb_gate('invalid_xyz') must return gate_block",
    ))

    # Criterion 5: gate_passes_permitted_class
    permitted_class = record.next_package_class if readable else "capability_session"
    try:
        d3 = _evaluate_cmdb_gate(requested_class=permitted_class)
        gate_permits = (d3.result == _GATE_PASS)
        observed_gate3 = f"{d3.result} for class={permitted_class!r}"
    except Exception as exc:
        gate_permits = False
        observed_gate3 = f"exception: {exc}"
    results.append(CmdbProofCriterionResult(
        criterion="gate_passes_permitted_class",
        passed=gate_permits,
        observed=observed_gate3,
        detail=f"evaluate_cmdb_gate(next_package_class={permitted_class!r}) must return gate_pass",
    ))

    criteria_passed = sum(1 for r in results if r.passed)
    overall_result = CMDB_PROOF_SUFFICIENT if criteria_passed == 5 else CMDB_PROOF_INSUFFICIENT

    report = CmdbEvidenceReport(
        criterion_results=results,
        overall_result=overall_result,
        criteria_passed=criteria_passed,
        criteria_total=5,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_cmdb_promotion_evidence.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "CMDB_PROOF_SUFFICIENT",
    "CMDB_PROOF_INSUFFICIENT",
    "CMDB_PROOF_CRITERIA",
    "CmdbProofCriterionResult",
    "CmdbEvidenceReport",
    "evaluate_cmdb_promotion_evidence",
]
