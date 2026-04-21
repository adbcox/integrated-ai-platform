"""PromotionBaselineInspector — LAPC1 P1.

Inspects all eight expansion surfaces and emits PromotionBaselineReport
with per-candidate current_state, evidence_present, evidence_missing, blocker_class.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Inspection gate — bind confirmed surface names before use
from framework.aider_runtime_adapter import AiderRuntimeAdapter as _AiderRuntimeAdapter
from framework.codex_defer_adapter import CODEX_AVAILABLE as _CODEX_AVAILABLE
from framework.cmdb_authority_pilot import CmdbAuthorityPilot as _CmdbAuthorityPilot
from framework.cmdb_integration_gate import CmdbIntegrationGate as _CmdbIntegrationGate
from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST as _FIRST_WAVE_MANIFEST
from framework.domain_branch_second_wave import SECOND_WAVE_MANIFEST as _SECOND_WAVE_MANIFEST

assert hasattr(_AiderRuntimeAdapter, "run"), "INTERFACE MISMATCH: AiderRuntimeAdapter.run"
assert hasattr(_CmdbAuthorityPilot, "read_authority"), "INTERFACE MISMATCH: CmdbAuthorityPilot.read_authority"
assert hasattr(_CmdbIntegrationGate, "evaluate"), "INTERFACE MISMATCH: CmdbIntegrationGate.evaluate"
assert _FIRST_WAVE_MANIFEST.branch_count == 3, "INTERFACE MISMATCH: FIRST_WAVE_MANIFEST.branch_count"
assert _SECOND_WAVE_MANIFEST.branch_count == 2, "INTERFACE MISMATCH: SECOND_WAVE_MANIFEST.branch_count"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "promotion_baseline"

BLOCKER_CLASS_HARD = "hard"
BLOCKER_CLASS_SOFT = "soft"
BLOCKER_CLASS_NONE = "none"

CURRENT_STATE_PARTIAL = "partial"
CURRENT_STATE_DEFERRED = "deferred"
CURRENT_STATE_SEED_COMPLETE = "seed_complete"
CURRENT_STATE_DONE = "done"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class PromotionCandidate:
    name: str
    current_state: str
    promotion_target: str
    evidence_present: list
    evidence_missing: list
    blocker_class: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current_state": self.current_state,
            "promotion_target": self.promotion_target,
            "evidence_present": list(self.evidence_present),
            "evidence_missing": list(self.evidence_missing),
            "blocker_class": self.blocker_class,
        }


@dataclass
class PromotionBaselineReport:
    candidates: list
    total_candidates: int
    hard_blocked_count: int
    soft_blocked_count: int
    unblocked_count: int
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "total_candidates": self.total_candidates,
            "hard_blocked_count": self.hard_blocked_count,
            "soft_blocked_count": self.soft_blocked_count,
            "unblocked_count": self.unblocked_count,
            "generated_at": self.generated_at,
            "candidates": [c.to_dict() for c in self.candidates],
        }


def _build_candidates() -> list:
    domain_evidence_present = [
        "DomainBranchPolicy validates",
        "Runner delegates to TaskRepetitionHarness dry-run",
    ]
    domain_evidence_missing = ["real product task execution"]

    return [
        PromotionCandidate(
            name="aider",
            current_state=CURRENT_STATE_PARTIAL,
            promotion_target="aider_done",
            evidence_present=[
                "AiderRuntimeAdapter importable",
                "dry_run evidence at adapter_partial",
            ],
            evidence_missing=[
                "live binary execution via runtime",
                "aider in KNOWN_FRAMEWORK_COMMANDS",
            ],
            blocker_class=BLOCKER_CLASS_HARD,
        ),
        PromotionCandidate(
            name="codex",
            current_state=CURRENT_STATE_DEFERRED,
            promotion_target="codex_done_or_long_term_deferred",
            evidence_present=[
                "CodexDeferArtifact importable",
                "CODEX_AVAILABLE evaluated",
            ],
            evidence_missing=["ANTHROPIC_API_KEY or OPENAI_API_KEY in env"],
            blocker_class=BLOCKER_CLASS_SOFT,
        ),
        PromotionCandidate(
            name="cmdb",
            current_state=CURRENT_STATE_SEED_COMPLETE,
            promotion_target="cmdb_done",
            evidence_present=[
                "CmdbAuthorityPilot reads governance files",
                "CmdbIntegrationGate evaluates",
            ],
            evidence_missing=["formal proof criteria evaluated"],
            blocker_class=BLOCKER_CLASS_NONE,
        ),
        PromotionCandidate(
            name="media_control",
            current_state=CURRENT_STATE_SEED_COMPLETE,
            promotion_target="done_or_scaffold_complete_product_deferred",
            evidence_present=domain_evidence_present,
            evidence_missing=domain_evidence_missing,
            blocker_class=BLOCKER_CLASS_SOFT,
        ),
        PromotionCandidate(
            name="media_lab",
            current_state=CURRENT_STATE_SEED_COMPLETE,
            promotion_target="done_or_scaffold_complete_product_deferred",
            evidence_present=domain_evidence_present,
            evidence_missing=domain_evidence_missing,
            blocker_class=BLOCKER_CLASS_SOFT,
        ),
        PromotionCandidate(
            name="meeting_intelligence",
            current_state=CURRENT_STATE_SEED_COMPLETE,
            promotion_target="done_or_scaffold_complete_product_deferred",
            evidence_present=domain_evidence_present,
            evidence_missing=domain_evidence_missing,
            blocker_class=BLOCKER_CLASS_SOFT,
        ),
        PromotionCandidate(
            name="athlete_analytics",
            current_state=CURRENT_STATE_SEED_COMPLETE,
            promotion_target="done_or_scaffold_complete_product_deferred",
            evidence_present=domain_evidence_present,
            evidence_missing=domain_evidence_missing,
            blocker_class=BLOCKER_CLASS_SOFT,
        ),
        PromotionCandidate(
            name="office_automation",
            current_state=CURRENT_STATE_SEED_COMPLETE,
            promotion_target="done_or_scaffold_complete_product_deferred",
            evidence_present=domain_evidence_present,
            evidence_missing=domain_evidence_missing,
            blocker_class=BLOCKER_CLASS_SOFT,
        ),
    ]


def inspect_promotion_baseline(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> PromotionBaselineReport:
    candidates = _build_candidates()

    hard_blocked = sum(1 for c in candidates if c.blocker_class == BLOCKER_CLASS_HARD)
    soft_blocked = sum(1 for c in candidates if c.blocker_class == BLOCKER_CLASS_SOFT)
    unblocked = sum(1 for c in candidates if c.blocker_class == BLOCKER_CLASS_NONE)

    report = PromotionBaselineReport(
        candidates=candidates,
        total_candidates=len(candidates),
        hard_blocked_count=hard_blocked,
        soft_blocked_count=soft_blocked,
        unblocked_count=unblocked,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_promotion_baseline.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "BLOCKER_CLASS_HARD",
    "BLOCKER_CLASS_SOFT",
    "BLOCKER_CLASS_NONE",
    "CURRENT_STATE_PARTIAL",
    "CURRENT_STATE_DEFERRED",
    "CURRENT_STATE_SEED_COMPLETE",
    "CURRENT_STATE_DONE",
    "PromotionCandidate",
    "PromotionBaselineReport",
    "inspect_promotion_baseline",
]
