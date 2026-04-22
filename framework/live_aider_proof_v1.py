"""LiveAiderProofV1: truthful live-capable Aider dispatch proof surface."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.live_aider_dispatch_v1 import (
    LiveAiderDispatchV1,
    AiderDispatchRecordV1,
    DISPATCH_STATUS_DRY_RUN,
    DISPATCH_STATUS_BLOCKED,
    DISPATCH_STATUS_COMPLETED,
    DISPATCH_STATUS_FAILED,
)

PROOF_MODE_LIVE = "live"
PROOF_MODE_DRY_RUN_ONLY = "dry_run_only"
PROOF_MODE_BLOCKED = "blocked"


@dataclass
class AiderProofResultV1:
    live_dispatch_attempted: bool
    live_dispatch_succeeded: bool
    dispatch_mode: str
    failure_reason: Optional[str]
    dispatch_record: Optional[AiderDispatchRecordV1]
    proved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_dispatch_attempted": self.live_dispatch_attempted,
            "live_dispatch_succeeded": self.live_dispatch_succeeded,
            "dispatch_mode": self.dispatch_mode,
            "failure_reason": self.failure_reason,
            "dispatch_record": self.dispatch_record.to_dict() if self.dispatch_record else None,
            "proved_at": self.proved_at,
            "notes": self.notes,
        }


class LiveAiderProofV1:
    """
    Truthful live-capable proof surface for Aider dispatch.

    - Attempts live dispatch when `attempt_live=True` and environment supports it.
    - Falls back explicitly to dry_run_only when Aider is not installed.
    - Never claims "live" when only dry-run was executed.
    """

    def prove(
        self,
        package_id: str,
        allowed_files: List[str],
        message: str,
        attempt_live: bool = False,
        notes: Optional[List[str]] = None,
    ) -> AiderProofResultV1:
        dispatcher = LiveAiderDispatchV1()

        if not attempt_live:
            # Explicit dry-run mode — no live claim
            record = dispatcher.dispatch(
                package_id=package_id,
                allowed_files=allowed_files,
                message=message,
                dry_run=True,
                notes=notes,
            )
            return AiderProofResultV1(
                live_dispatch_attempted=False,
                live_dispatch_succeeded=False,
                dispatch_mode=PROOF_MODE_DRY_RUN_ONLY,
                failure_reason=None,
                dispatch_record=record,
                notes=(notes or []) + ["attempt_live=False; dry-run proof only"],
            )

        # Attempt live dispatch
        record = dispatcher.dispatch(
            package_id=package_id,
            allowed_files=allowed_files,
            message=message,
            dry_run=False,
            notes=notes,
        )

        if record.dispatch_status == DISPATCH_STATUS_COMPLETED:
            return AiderProofResultV1(
                live_dispatch_attempted=True,
                live_dispatch_succeeded=True,
                dispatch_mode=PROOF_MODE_LIVE,
                failure_reason=None,
                dispatch_record=record,
                notes=notes or [],
            )

        if record.dispatch_status == DISPATCH_STATUS_BLOCKED:
            # Aider not installed or no files — truthful fallback
            failure = next(
                (n for n in record.notes if "not found" in n or "unavailable" in n),
                "dispatch blocked",
            )
            return AiderProofResultV1(
                live_dispatch_attempted=True,
                live_dispatch_succeeded=False,
                dispatch_mode=PROOF_MODE_DRY_RUN_ONLY,
                failure_reason=failure,
                dispatch_record=record,
                notes=(notes or []) + [f"live dispatch blocked: {failure}"],
            )

        # Failed
        return AiderProofResultV1(
            live_dispatch_attempted=True,
            live_dispatch_succeeded=False,
            dispatch_mode=PROOF_MODE_BLOCKED,
            failure_reason=f"dispatch_status={record.dispatch_status}",
            dispatch_record=record,
            notes=notes or [],
        )
