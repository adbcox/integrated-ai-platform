"""CMDB-AUTHORITY-PROOF-HARNESS-SEAM-1: five-criterion deterministic proof harness."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.cmdb_authority_boundary import (
    AuthorityDomain,
    CMDB_AUTHORITY,
    PROMOTION_AUTHORITY,
    validate_boundary_non_overlap,
)
from framework.cmdb_authority_contract import CmdbAuthorityContract
from framework.cmdb_read_model import CmdbReadModel, CmdbReadModelOutput
from framework.cmdb_integration_gate import evaluate_cmdb_gate, GATE_PASS, GATE_BLOCK

# Import-time assertions
assert "domain_name" in AuthorityDomain.__dataclass_fields__, \
    "INTERFACE MISMATCH: AuthorityDomain missing domain_name"
assert callable(evaluate_cmdb_gate), \
    "INTERFACE MISMATCH: evaluate_cmdb_gate not callable"
assert callable(CmdbReadModel), \
    "INTERFACE MISMATCH: CmdbReadModel not callable"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbProofCriterion:
    criterion_name: str
    passed: bool
    detail: str


@dataclass
class CmdbProofResult:
    criteria: List[CmdbProofCriterion]
    criteria_passed: int
    criteria_total: int
    proof_verdict: str  # "proven" | "partial" | "blocked"
    blocking_reasons: List[str]
    proven_at: str
    artifact_path: Optional[str]


class CmdbAuthorityProofHarness:
    """Evaluates five criteria for CMDB authoritative adoption."""

    def run(
        self,
        *,
        contract: CmdbAuthorityContract,
        read_model_output: CmdbReadModelOutput,
    ) -> CmdbProofResult:
        criteria: List[CmdbProofCriterion] = []
        blocking_reasons: List[str] = []

        # Criterion 1: source_readable
        total = read_model_output.total_entries
        readable = read_model_output.readable_count
        c1_passed = total > 0 and readable == total
        if not c1_passed:
            blocking_reasons.append(
                f"source_readable: {readable}/{total} entries readable"
            )
        criteria.append(CmdbProofCriterion(
            criterion_name="source_readable",
            passed=c1_passed,
            detail=f"readable={readable} total={total}",
        ))

        # Criterion 2: stable_typed_output
        stable = read_model_output.stable_count
        c2_passed = total > 0 and stable == total
        if not c2_passed:
            blocking_reasons.append(
                f"stable_typed_output: {stable}/{total} entries stable"
            )
        criteria.append(CmdbProofCriterion(
            criterion_name="stable_typed_output",
            passed=c2_passed,
            detail=f"stable={stable} total={total}",
        ))

        # Criterion 3: deterministic_gate
        try:
            gate_result = evaluate_cmdb_gate(requested_class="")
            c3_passed = gate_result.result in (GATE_PASS, GATE_BLOCK)
            c3_detail = f"gate_result={gate_result.result!r}"
        except Exception as exc:
            c3_passed = False
            c3_detail = f"evaluate_cmdb_gate raised: {exc}"
            blocking_reasons.append(f"deterministic_gate: {c3_detail}")
        if c3_passed is True and gate_result.result not in (GATE_PASS, GATE_BLOCK):
            c3_passed = False
        if not c3_passed and "deterministic_gate" not in " ".join(blocking_reasons):
            blocking_reasons.append(f"deterministic_gate: {c3_detail}")
        criteria.append(CmdbProofCriterion(
            criterion_name="deterministic_gate",
            passed=c3_passed,
            detail=c3_detail,
        ))

        # Criterion 4: authority_boundary_correct
        violations = validate_boundary_non_overlap()
        domain_ok = contract.authority_domain == CMDB_AUTHORITY.domain_name
        c4_passed = len(violations) == 0 and domain_ok
        c4_detail = f"overlap_violations={violations} domain_match={domain_ok}"
        if not c4_passed:
            blocking_reasons.append(f"authority_boundary_correct: {c4_detail}")
        criteria.append(CmdbProofCriterion(
            criterion_name="authority_boundary_correct",
            passed=c4_passed,
            detail=c4_detail,
        ))

        # Criterion 5: non_overlap_with_manifest
        promo_clean = "service_inventory" not in PROMOTION_AUTHORITY.owns
        cmdb_clean = "promotion_manifest" not in CMDB_AUTHORITY.owns
        c5_passed = promo_clean and cmdb_clean
        c5_detail = f"promotion_owns_service_inventory={not promo_clean} cmdb_owns_promotion_manifest={not cmdb_clean}"
        if not c5_passed:
            blocking_reasons.append(f"non_overlap_with_manifest: {c5_detail}")
        criteria.append(CmdbProofCriterion(
            criterion_name="non_overlap_with_manifest",
            passed=c5_passed,
            detail=c5_detail,
        ))

        criteria_passed = sum(1 for c in criteria if c.passed)
        criteria_total = len(criteria)

        if criteria_passed == criteria_total:
            proof_verdict = "proven"
        elif criteria_passed == 0:
            proof_verdict = "blocked"
        else:
            proof_verdict = "partial"

        return CmdbProofResult(
            criteria=criteria,
            criteria_passed=criteria_passed,
            criteria_total=criteria_total,
            proof_verdict=proof_verdict,
            blocking_reasons=blocking_reasons,
            proven_at=_iso_now(),
            artifact_path=None,
        )


def emit_cmdb_proof_result(
    result: CmdbProofResult,
    *,
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "proof_harness_result.json"
    out_path.write_text(
        json.dumps(
            {
                "proof_verdict": result.proof_verdict,
                "criteria_passed": result.criteria_passed,
                "criteria_total": result.criteria_total,
                "blocking_reasons": result.blocking_reasons,
                "proven_at": result.proven_at,
                "criteria": [
                    {
                        "criterion_name": c.criterion_name,
                        "passed": c.passed,
                        "detail": c.detail,
                    }
                    for c in result.criteria
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    result.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "CmdbProofCriterion",
    "CmdbProofResult",
    "CmdbAuthorityProofHarness",
    "emit_cmdb_proof_result",
]
