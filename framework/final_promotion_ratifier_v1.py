"""FinalPromotionRatifierV1: final Phase 7 promotion gate ratification from evidence chain."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Evidence input paths ──────────────────────────────────────────────────────

_EVIDENCE_PATHS = {
    "promotion_pack":    Path("artifacts/substrate/phase7_promotion_pack_check.json"),
    "live_evidence":     Path("artifacts/substrate/phase7_live_evidence_pack_check.json"),
    "live_proof_chain":  Path("artifacts/local_runs/local_live_proof_chain.json"),
}


@dataclass
class FinalRatificationResultV1:
    phase7_final_ratified: bool
    promotion_gate_cleared: bool
    remaining_blockers: List[str]
    live_evidence_seen: bool
    final_summary: Dict[str, Any]
    ratified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase7_final_ratified": self.phase7_final_ratified,
            "promotion_gate_cleared": self.promotion_gate_cleared,
            "remaining_blockers": self.remaining_blockers,
            "live_evidence_seen": self.live_evidence_seen,
            "final_summary": self.final_summary,
            "ratified_at": self.ratified_at,
        }


class FinalPromotionRatifierV1:
    """
    Consume the Phase 7 evidence chain and emit a final ratification decision.

    Truthfulness rules:
    - If live proof chain is present and live_dispatch_succeeded = True: gate cleared.
    - If live evidence exists but dispatch was dry_run_only: partial credit; gate blocked
      on live dispatch gap only.
    - If evidence files are absent: gate blocked explicitly.
    - Never claims phase7_final_ratified = True when gate blockers remain.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self._root = repo_root or Path(".")

    def _load_json(self, rel_path: Path) -> tuple[Optional[dict], Optional[str]]:
        full = self._root / rel_path
        if not full.exists():
            return None, f"file not found: {rel_path}"
        try:
            return json.loads(full.read_text(encoding="utf-8")), None
        except Exception as exc:
            return None, f"parse error in {rel_path}: {exc}"

    def ratify(self) -> FinalRatificationResultV1:
        blockers: List[str] = []
        evidence_loaded: Dict[str, Any] = {}
        load_errors: List[str] = []

        # ── Load evidence inputs ──────────────────────────────────────────────
        for key, rel_path in _EVIDENCE_PATHS.items():
            data, err = self._load_json(rel_path)
            if err:
                load_errors.append(err)
                evidence_loaded[key] = None
            else:
                evidence_loaded[key] = data

        promotion_pack = evidence_loaded.get("promotion_pack")
        live_evidence  = evidence_loaded.get("live_evidence")
        live_proof     = evidence_loaded.get("live_proof_chain")

        # ── Assess live evidence ──────────────────────────────────────────────
        live_evidence_seen = live_evidence is not None

        # Phase 7 promotion pack must exist and be passing
        if promotion_pack is None:
            blockers.append("promotion_pack: phase7_promotion_pack_check.json not found")
        else:
            if not promotion_pack.get("all_checks_passed", False):
                blockers.append("promotion_pack: all_checks_passed is False")
            if not promotion_pack.get("promotion_ready", False):
                blockers.append(
                    f"promotion_pack: promotion_ready is False; "
                    f"blockers={promotion_pack.get('promotion_blockers', [])}"
                )

        # Live evidence pack must exist
        if live_evidence is None:
            blockers.append("live_evidence: phase7_live_evidence_pack_check.json not found")
        else:
            if not live_evidence.get("all_checks_passed", False):
                blockers.append("live_evidence: all_checks_passed is False")
            if not live_evidence.get("telemetry_complete", False):
                blockers.append("live_evidence: telemetry_complete is False")
            if not live_evidence.get("local_autonomy_progress_preserved", True):
                blockers.append("live_evidence: local_autonomy_progress_preserved is False")
            # Live dispatch gap — truthful disclosure
            if not live_evidence.get("live_dispatch_succeeded", False):
                mode = live_evidence.get("dispatch_mode", "unknown")
                blockers.append(
                    f"live_evidence: live_dispatch_succeeded=False "
                    f"(dispatch_mode={mode!r}); "
                    "live Aider execution required to clear this blocker"
                )

        # Live proof chain — optional supporting evidence only.
        # It must not override a failed current live evidence run.
        live_proof_notes: List[str] = []
        if live_proof is None:
            live_proof_notes.append(
                "live_proof_chain: artifacts/local_runs/local_live_proof_chain.json "
                "not found; no additional live execution evidence available"
            )
        else:
            live_evidence_seen = True
            if live_proof.get("live_dispatch_succeeded", False):
                if live_evidence is None:
                    live_proof_notes.append(
                        "live_proof_chain: live_dispatch_succeeded=True used because "
                        "current live evidence artifact is missing"
                    )
                else:
                    live_proof_notes.append(
                        "live_proof_chain: live_dispatch_succeeded=True present, but "
                        "current live evidence controls gate truth"
                    )

        promotion_gate_cleared = len(blockers) == 0
        # phase7_final_ratified is True only when gate is fully cleared
        phase7_final_ratified = promotion_gate_cleared

        final_summary: Dict[str, Any] = {
            "evidence_inputs_loaded": {
                k: (v is not None) for k, v in evidence_loaded.items()
            },
            "load_errors": load_errors,
            "promotion_pack_all_checks_passed": (
                promotion_pack.get("all_checks_passed") if promotion_pack else None
            ),
            "live_evidence_telemetry_complete": (
                live_evidence.get("telemetry_complete") if live_evidence else None
            ),
            "live_dispatch_succeeded": (
                live_evidence.get("live_dispatch_succeeded") if live_evidence else None
            ),
            "dispatch_mode": (
                live_evidence.get("dispatch_mode") if live_evidence else None
            ),
            "live_proof_chain_present": live_proof is not None,
            "live_proof_notes": live_proof_notes,
            "total_blockers": len(blockers),
        }

        return FinalRatificationResultV1(
            phase7_final_ratified=phase7_final_ratified,
            promotion_gate_cleared=promotion_gate_cleared,
            remaining_blockers=blockers,
            live_evidence_seen=live_evidence_seen,
            final_summary=final_summary,
        )
