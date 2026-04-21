"""CodexPromotionRatifier — LAPC1 P6.

Derives codex_done or codex_long_term_deferred from CodexAvailabilityReport.
No SDK imports, no network calls.
Inspection gate confirmed:
  CodexAvailabilityReport fields: checks, overall_result, codex_available,
                                   policy_allows_execution, blocking_reason,
                                   generated_at, artifact_path
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.codex_availability_gate import (
    CodexAvailabilityReport as _CodexAvailabilityReport,
    CODEX_GATE_PASS as _CODEX_GATE_PASS,
)

assert "codex_available" in _CodexAvailabilityReport.__dataclass_fields__, "INTERFACE MISMATCH: CodexAvailabilityReport.codex_available"
assert "overall_result" in _CodexAvailabilityReport.__dataclass_fields__, "INTERFACE MISMATCH: CodexAvailabilityReport.overall_result"
assert "policy_allows_execution" in _CodexAvailabilityReport.__dataclass_fields__, "INTERFACE MISMATCH: CodexAvailabilityReport.policy_allows_execution"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "codex_promotion"

CODEX_PROMOTION_DONE = "codex_done"
CODEX_LONG_TERM_DEFERRED = "codex_long_term_deferred"

_NEXT_REVIEW_TRIGGER = (
    "Set ANTHROPIC_API_KEY or OPENAI_API_KEY and run evaluate_codex_availability() "
    "to confirm availability, then request explicit authorization for live Codex proof runs."
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CodexPromotionArtifact:
    decision: str
    rationale: str
    availability_result: str
    codex_available: bool
    defer_reason: str
    next_review_trigger: str
    ratified_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "decision": self.decision,
            "rationale": self.rationale,
            "availability_result": self.availability_result,
            "codex_available": self.codex_available,
            "defer_reason": self.defer_reason,
            "next_review_trigger": self.next_review_trigger,
            "ratified_at": self.ratified_at,
        }


def ratify_codex_promotion(
    availability_report: Optional[_CodexAvailabilityReport] = None,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> CodexPromotionArtifact:
    if availability_report is not None:
        availability_result = availability_report.overall_result
        codex_available = availability_report.codex_available
        policy_allows = availability_report.policy_allows_execution
        blocking_reason = availability_report.blocking_reason
    else:
        availability_result = "not_evaluated"
        codex_available = False
        policy_allows = False
        blocking_reason = "availability not evaluated"

    # codex_done requires: available AND policy allows AND explicit authorization
    # In LAPC1 campaign scope: no explicit authorization for live runs is granted.
    # So even if env key were present, we still defer in this campaign.
    done = False  # No live proof authorization in LAPC1 scope

    if done:
        decision = CODEX_PROMOTION_DONE
        rationale = "Codex available and live proof authorized and succeeded."
        defer_reason = ""
    else:
        decision = CODEX_LONG_TERM_DEFERRED
        if not codex_available:
            defer_reason = (
                "No ANTHROPIC_API_KEY or OPENAI_API_KEY in environment. "
                "Codex execution requires explicit API key and authorization."
            )
        else:
            defer_reason = (
                "No explicit authorization for live Codex proof runs in LAPC1 campaign scope. "
                "API key present but live execution not authorized for this campaign."
            )
        rationale = (
            f"Codex long-term deferred. availability_result={availability_result!r}. "
            f"Reason: {defer_reason}"
        )

    artifact = CodexPromotionArtifact(
        decision=decision,
        rationale=rationale,
        availability_result=availability_result,
        codex_available=codex_available,
        defer_reason=defer_reason,
        next_review_trigger=_NEXT_REVIEW_TRIGGER,
        ratified_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_codex_promotion.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "CODEX_PROMOTION_DONE",
    "CODEX_LONG_TERM_DEFERRED",
    "CodexPromotionArtifact",
    "ratify_codex_promotion",
]
