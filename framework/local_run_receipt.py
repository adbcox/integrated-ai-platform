"""LEDT-P7: Typed local run receipt capturing route, validations, and fallback status."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


VALID_ROUTES = frozenset({"local_execute", "claude_fallback", "hard_stop"})
VALID_EXECUTORS = frozenset({"aider", "claude", "dry_run", "none"})
VALID_RESULTS = frozenset({"success", "failure", "partial"})


@dataclass
class LocalRunReceipt:
    receipt_id: str
    packet_id: str
    route_chosen: str
    executor_used: str
    validations_run: List[str]
    validation_passed: bool
    fallback_used: bool
    fallback_justification_id: Optional[str]
    result: str
    elapsed_seconds: Optional[float]
    recorded_at: str


class LocalRunReceiptWriter:
    """Emits a typed receipt per local execution attempt."""

    def write(
        self,
        packet_id: str,
        route_chosen: str,
        executor_used: str,
        validations_run: List[str],
        validation_passed: bool,
        fallback_used: bool,
        result: str,
        elapsed_seconds: Optional[float] = None,
        fallback_justification_id: Optional[str] = None,
    ) -> LocalRunReceipt:
        if fallback_used and fallback_justification_id is None:
            raise ValueError(
                "fallback_justification_id is required when fallback_used=True"
            )
        return LocalRunReceipt(
            receipt_id=f"RCPT-{_ts()}-{packet_id[:16].replace(' ', '_')}",
            packet_id=packet_id,
            route_chosen=route_chosen,
            executor_used=executor_used,
            validations_run=validations_run,
            validation_passed=validation_passed,
            fallback_used=fallback_used,
            fallback_justification_id=fallback_justification_id,
            result=result,
            elapsed_seconds=elapsed_seconds,
            recorded_at=_iso_now(),
        )

    def emit(self, receipts: List[LocalRunReceipt], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "local_run_receipt_proof.json"
        local_count = sum(1 for r in receipts if r.route_chosen == "local_execute")
        fallback_count = sum(1 for r in receipts if r.route_chosen == "claude_fallback")
        fallback_used_count = sum(1 for r in receipts if r.fallback_used)
        val_passed_count = sum(1 for r in receipts if r.validation_passed)
        out_path.write_text(
            json.dumps({
                "sample_count": len(receipts),
                "local_execute_count": local_count,
                "claude_fallback_count": fallback_count,
                "fallback_used_count": fallback_used_count,
                "validation_passed_count": val_passed_count,
                "receipts": [asdict(r) for r in receipts],
                "proved_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["LocalRunReceipt", "LocalRunReceiptWriter"]
