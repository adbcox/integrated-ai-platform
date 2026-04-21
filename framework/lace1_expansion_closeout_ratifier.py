"""LACE1-P15-EXPANSION-CLOSEOUT-RATIFIER-SEAM-1: ratify LACE1 campaign closeout."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.autonomy_uplift_ratifier import (
    UpliftRatificationRecord,
    VERDICT_SUBSTRATE_UPLIFT_CONFIRMED,
    VERDICT_PARTIAL_SUBSTRATE_UPLIFT,
    VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED,
)
from framework.grouped_package_expansion_selector import GroupedPackageSelectionRecord

assert "verdict" in UpliftRatificationRecord.__dataclass_fields__, "INTERFACE MISMATCH: UpliftRatificationRecord.verdict"
assert "selected_package_id" in GroupedPackageSelectionRecord.__dataclass_fields__, "INTERFACE MISMATCH: GroupedPackageSelectionRecord.selected_package_id"

CAMPAIGN_VERDICT_COMPLETE = "lace1_campaign_complete"
CAMPAIGN_VERDICT_PARTIAL = "lace1_campaign_partial"

_PACKETS_EXPECTED = 15

_KNOWN_LIMITATIONS = [
    "Benchmark is fully synthetic: pass_rate=1.0 reflects task construction correctness, NOT real LLM coding capability.",
    "No real file modifications were made during P10 benchmark execution; all edits are in-memory string replacements.",
    "Retrieval enrichment substrate (P14) is not yet wired into the live stage_rag4 pipeline; it is a standalone module.",
    "Failure pattern mining (P11) found no real failures because the benchmark has no LLM or execution errors by design.",
    "The RM-GOV-003 grouped package scoring used static item_ids; production scoring would query live YAML state.",
    "LocalAutonomyTask acceptance_grep validation is compile-only; grep matching correctness was not tested at the integration level.",
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class Lace1CloseoutRecord:
    closeout_id: str
    campaign_id: str
    campaign_verdict: str
    packets_completed: int
    packets_expected: int
    uplift_verdict: str
    selected_expansion_package: str
    known_limitations: List[str]
    closed_at: str
    artifact_path: Optional[str] = None


class Lace1ExpansionCloseoutRatifier:
    """Ratify the LACE1 expansion campaign closeout."""

    def ratify(
        self,
        uplift_record: UpliftRatificationRecord,
        selection_record: GroupedPackageSelectionRecord,
        *,
        packets_completed: int = _PACKETS_EXPECTED,
    ) -> Lace1CloseoutRecord:
        if (
            uplift_record.verdict == VERDICT_SUBSTRATE_UPLIFT_CONFIRMED
            and packets_completed >= _PACKETS_EXPECTED
        ):
            campaign_verdict = CAMPAIGN_VERDICT_COMPLETE
        else:
            campaign_verdict = CAMPAIGN_VERDICT_PARTIAL

        return Lace1CloseoutRecord(
            closeout_id=f"LACE1-CLOSE-{_ts()}",
            campaign_id="LACE1",
            campaign_verdict=campaign_verdict,
            packets_completed=packets_completed,
            packets_expected=_PACKETS_EXPECTED,
            uplift_verdict=uplift_record.verdict,
            selected_expansion_package=selection_record.selected_package_id,
            known_limitations=list(_KNOWN_LIMITATIONS),
            closed_at=_iso_now(),
        )

    def emit(self, record: Lace1CloseoutRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "LACE1_closeout.json"
        payload = {
            "closeout_id": record.closeout_id,
            "campaign_id": record.campaign_id,
            "campaign_verdict": record.campaign_verdict,
            "packets_completed": record.packets_completed,
            "packets_expected": record.packets_expected,
            "uplift_verdict": record.uplift_verdict,
            "selected_expansion_package": record.selected_expansion_package,
            "known_limitations": record.known_limitations,
            "closed_at": record.closed_at,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = [
    "Lace1CloseoutRecord",
    "Lace1ExpansionCloseoutRatifier",
    "CAMPAIGN_VERDICT_COMPLETE",
    "CAMPAIGN_VERDICT_PARTIAL",
]
