"""TerminalPromotionRatifier — LAPC1 P12.

Aggregates all five promotion artifacts into a single terminal campaign record.
terminal_promotion_complete only if all 8 items resolve to expected terminal states.
terminal_promotion_partial otherwise (expected honest result for this campaign).

Inspection gate confirmed all upstream artifact types have __dataclass_fields__.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.aider_promotion_ratifier import AiderPromotionArtifact as _AiderPromotionArtifact
from framework.codex_promotion_ratifier import CodexPromotionArtifact as _CodexPromotionArtifact
from framework.cmdb_promotion_ratifier import CmdbPromotionArtifact as _CmdbPromotionArtifact
from framework.domain_branch_first_wave_ratifier import FirstWavePromotionArtifact as _FirstWavePromotionArtifact
from framework.domain_branch_second_wave_ratifier import SecondWavePromotionArtifact as _SecondWavePromotionArtifact

assert hasattr(_AiderPromotionArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: AiderPromotionArtifact"
assert hasattr(_CodexPromotionArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: CodexPromotionArtifact"
assert hasattr(_CmdbPromotionArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: CmdbPromotionArtifact"
assert hasattr(_FirstWavePromotionArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: FirstWavePromotionArtifact"
assert hasattr(_SecondWavePromotionArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: SecondWavePromotionArtifact"
assert "decision" in _AiderPromotionArtifact.__dataclass_fields__, "INTERFACE MISMATCH: AiderPromotionArtifact.decision"
assert "decision" in _CodexPromotionArtifact.__dataclass_fields__, "INTERFACE MISMATCH: CodexPromotionArtifact.decision"
assert "decision" in _CmdbPromotionArtifact.__dataclass_fields__, "INTERFACE MISMATCH: CmdbPromotionArtifact.decision"
assert "records" in _FirstWavePromotionArtifact.__dataclass_fields__, "INTERFACE MISMATCH: FirstWavePromotionArtifact.records"
assert "records" in _SecondWavePromotionArtifact.__dataclass_fields__, "INTERFACE MISMATCH: SecondWavePromotionArtifact.records"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "terminal_promotion"

TERMINAL_PROMOTION_COMPLETE = "terminal_promotion_complete"
TERMINAL_PROMOTION_PARTIAL = "terminal_promotion_partial"

_EXPECTED_RESOLUTIONS = {
    "aider_overall": "aider_done",
    "codex_overall": "codex_long_term_deferred",
    "cmdb_overall": "cmdb_done",
    "media_control": "scaffold_complete_product_deferred",
    "media_lab": "scaffold_complete_product_deferred",
    "meeting_intelligence": "scaffold_complete_product_deferred",
    "athlete_analytics": "scaffold_complete_product_deferred",
    "office_automation": "scaffold_complete_product_deferred",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TerminalPromotionRecord:
    item_key: str
    expected_resolution: str
    actual_resolution: str
    resolved: bool
    notes: str

    def to_dict(self) -> dict:
        return {
            "item_key": self.item_key,
            "expected_resolution": self.expected_resolution,
            "actual_resolution": self.actual_resolution,
            "resolved": self.resolved,
            "notes": self.notes,
        }


@dataclass
class TerminalPromotionArtifact:
    campaign_id: str
    decision: str
    records: list
    all_resolved: bool
    resolved_count: int
    total_count: int
    unresolved_items: list
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "campaign_id": self.campaign_id,
            "decision": self.decision,
            "all_resolved": self.all_resolved,
            "resolved_count": self.resolved_count,
            "total_count": self.total_count,
            "unresolved_items": list(self.unresolved_items),
            "generated_at": self.generated_at,
            "records": [r.to_dict() for r in self.records],
        }


def _find_branch_verdict(wave_artifact, branch_name: str) -> str:
    if wave_artifact is None:
        return "not_provided"
    for rec in wave_artifact.records:
        if rec.branch_name == branch_name:
            return rec.verdict
    return "not_found"


def ratify_terminal_promotion(
    *,
    aider_artifact: Optional[_AiderPromotionArtifact] = None,
    codex_artifact: Optional[_CodexPromotionArtifact] = None,
    cmdb_artifact: Optional[_CmdbPromotionArtifact] = None,
    first_wave_artifact: Optional[_FirstWavePromotionArtifact] = None,
    second_wave_artifact: Optional[_SecondWavePromotionArtifact] = None,
    campaign_id: str = "LOCAL-AUTONOMY-PROMOTION-CAMPAIGN-1",
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> TerminalPromotionArtifact:
    records = []

    # aider_overall
    aider_actual = aider_artifact.decision if aider_artifact is not None else "not_provided"
    aider_expected = _EXPECTED_RESOLUTIONS["aider_overall"]
    aider_resolved = (aider_actual == aider_expected)
    records.append(TerminalPromotionRecord(
        item_key="aider_overall",
        expected_resolution=aider_expected,
        actual_resolution=aider_actual,
        resolved=aider_resolved,
        notes=(
            "aider_partial is the expected outcome; live binary not registered in "
            "KNOWN_FRAMEWORK_COMMANDS. Upgrade path: register command, rerun proof."
            if not aider_resolved else "aider_done confirmed."
        ),
    ))

    # codex_overall
    codex_actual = codex_artifact.decision if codex_artifact is not None else "not_provided"
    codex_expected = _EXPECTED_RESOLUTIONS["codex_overall"]
    records.append(TerminalPromotionRecord(
        item_key="codex_overall",
        expected_resolution=codex_expected,
        actual_resolution=codex_actual,
        resolved=(codex_actual == codex_expected),
        notes="Codex deferred: no API key in environment." if codex_actual != codex_expected else "codex_long_term_deferred confirmed.",
    ))

    # cmdb_overall
    cmdb_actual = cmdb_artifact.decision if cmdb_artifact is not None else "not_provided"
    cmdb_expected = _EXPECTED_RESOLUTIONS["cmdb_overall"]
    records.append(TerminalPromotionRecord(
        item_key="cmdb_overall",
        expected_resolution=cmdb_expected,
        actual_resolution=cmdb_actual,
        resolved=(cmdb_actual == cmdb_expected),
        notes="All 5 CMDB criteria passed." if cmdb_actual == cmdb_expected else f"CMDB not done: {cmdb_actual!r}.",
    ))

    # Domain branches
    for key in ("media_control", "media_lab", "meeting_intelligence"):
        actual = _find_branch_verdict(first_wave_artifact, key)
        expected = _EXPECTED_RESOLUTIONS[key]
        records.append(TerminalPromotionRecord(
            item_key=key,
            expected_resolution=expected,
            actual_resolution=actual,
            resolved=(actual == expected),
            notes=f"First-wave branch {key}: {actual}.",
        ))

    for key in ("athlete_analytics", "office_automation"):
        actual = _find_branch_verdict(second_wave_artifact, key)
        expected = _EXPECTED_RESOLUTIONS[key]
        records.append(TerminalPromotionRecord(
            item_key=key,
            expected_resolution=expected,
            actual_resolution=actual,
            resolved=(actual == expected),
            notes=f"Second-wave branch {key}: {actual}.",
        ))

    all_resolved = all(r.resolved for r in records)
    resolved_count = sum(1 for r in records if r.resolved)
    total_count = len(records)
    unresolved_items = [r.item_key for r in records if not r.resolved]
    decision = TERMINAL_PROMOTION_COMPLETE if all_resolved else TERMINAL_PROMOTION_PARTIAL

    artifact = TerminalPromotionArtifact(
        campaign_id=campaign_id,
        decision=decision,
        records=records,
        all_resolved=all_resolved,
        resolved_count=resolved_count,
        total_count=total_count,
        unresolved_items=unresolved_items,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_terminal_promotion.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "TERMINAL_PROMOTION_COMPLETE",
    "TERMINAL_PROMOTION_PARTIAL",
    "TerminalPromotionRecord",
    "TerminalPromotionArtifact",
    "ratify_terminal_promotion",
]
