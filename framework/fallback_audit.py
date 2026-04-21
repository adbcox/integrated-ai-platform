"""LEDT-P9: Fallback audit classifying justified, avoidable, and invalid fallback usage."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.local_run_receipt import LocalRunReceipt
from framework.fallback_justification import FallbackJustificationRecord

assert "fallback_used" in LocalRunReceipt.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalRunReceipt.fallback_used"
assert "fallback_justification_id" in LocalRunReceipt.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalRunReceipt.fallback_justification_id"
assert "avoidable_in_future" in FallbackJustificationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: FallbackJustificationRecord.avoidable_in_future"
assert "justification_class" in FallbackJustificationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: FallbackJustificationRecord.justification_class"
assert "evidence" in FallbackJustificationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: FallbackJustificationRecord.evidence"

AUDIT_CLASSES = frozenset({"justified", "avoidable", "invalid"})


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class FallbackAuditEntry:
    receipt_id: str
    packet_id: str
    fallback_used: bool
    audit_class: Optional[str]
    audit_rationale: str


@dataclass
class FallbackAuditorReport:
    audit_id: str
    total_receipts: int
    fallback_used_count: int
    justified_count: int
    avoidable_count: int
    invalid_count: int
    entries: List[FallbackAuditEntry]
    audited_at: str
    artifact_path: Optional[str] = None


def _classify(just: FallbackJustificationRecord) -> str:
    if just.avoidable_in_future:
        return "avoidable"
    if (just.justification_class == "manual_override"
            and len((just.evidence or "").strip()) < 20):
        return "invalid"
    return "justified"


class FallbackAuditor:
    """Classifies fallback events from run receipts and justification records."""

    def audit(
        self,
        receipts: List[LocalRunReceipt],
        justifications: Dict[str, FallbackJustificationRecord],
    ) -> FallbackAuditorReport:
        entries: List[FallbackAuditEntry] = []
        justified = avoidable = invalid = 0

        for r in receipts:
            if not r.fallback_used:
                entries.append(FallbackAuditEntry(
                    receipt_id=r.receipt_id,
                    packet_id=r.packet_id,
                    fallback_used=False,
                    audit_class=None,
                    audit_rationale="no fallback used",
                ))
                continue

            just = justifications.get(r.fallback_justification_id) if r.fallback_justification_id else None
            if just is None:
                audit_class = "invalid"
                rationale = "fallback_used=True but no justification record found"
                invalid += 1
            else:
                audit_class = _classify(just)
                rationale = (
                    f"class={just.justification_class} avoidable={just.avoidable_in_future} "
                    f"evidence_len={len(just.evidence or '')}"
                )
                if audit_class == "avoidable":
                    avoidable += 1
                elif audit_class == "invalid":
                    invalid += 1
                else:
                    justified += 1

            entries.append(FallbackAuditEntry(
                receipt_id=r.receipt_id,
                packet_id=r.packet_id,
                fallback_used=True,
                audit_class=audit_class,
                audit_rationale=rationale,
            ))

        return FallbackAuditorReport(
            audit_id=f"AUDIT-{_ts()}",
            total_receipts=len(receipts),
            fallback_used_count=sum(1 for r in receipts if r.fallback_used),
            justified_count=justified,
            avoidable_count=avoidable,
            invalid_count=invalid,
            entries=entries,
            audited_at=_iso_now(),
        )

    def emit(self, report: FallbackAuditorReport, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "fallback_audit.json"
        out_path.write_text(
            json.dumps({
                "audit_id": report.audit_id,
                "total_receipts": report.total_receipts,
                "fallback_used_count": report.fallback_used_count,
                "justified_count": report.justified_count,
                "avoidable_count": report.avoidable_count,
                "invalid_count": report.invalid_count,
                "entries": [asdict(e) for e in report.entries],
                "audited_at": report.audited_at,
            }, indent=2),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["FallbackAuditEntry", "FallbackAuditorReport", "FallbackAuditor"]
