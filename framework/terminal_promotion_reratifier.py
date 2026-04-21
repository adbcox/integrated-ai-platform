"""TerminalPromotionReratifier: final matrix closeout from Aider promotion artifact (TERMINAL-PROMOTION-COMPLETION-RERATIFIER-1)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TerminalPromotionDecision:
    terminal_decision: str  # "terminal_promotion_complete" | "terminal_promotion_partial"
    aider_decision: str
    resolved_count: int
    total_count: int
    unresolved_items: List[str]
    decided_at: str
    artifact_path: Optional[str]


class TerminalPromotionReratifier:
    """Decides terminal_promotion_complete or terminal_promotion_partial from refreshed Aider artifact."""

    def decide(
        self,
        *,
        aider_promotion_decision: dict,
        prior_resolved_count: int = 7,
        total_count: int = 8,
    ) -> TerminalPromotionDecision:
        aider_decision = aider_promotion_decision.get("decision", "aider_partial")
        unresolved_items: List[str] = []

        if aider_decision == "aider_done":
            resolved_count = prior_resolved_count + 1
        else:
            resolved_count = prior_resolved_count
            blocking_reason = aider_promotion_decision.get("blocking_reason") or "unknown"
            unresolved_items.append(f"aider_overall: {blocking_reason}")

        if resolved_count >= total_count and len(unresolved_items) == 0:
            terminal_decision = "terminal_promotion_complete"
        else:
            terminal_decision = "terminal_promotion_partial"

        return TerminalPromotionDecision(
            terminal_decision=terminal_decision,
            aider_decision=aider_decision,
            resolved_count=resolved_count,
            total_count=total_count,
            unresolved_items=unresolved_items,
            decided_at=_iso_now(),
            artifact_path=None,
        )


def emit_terminal_promotion_decision(
    decision: TerminalPromotionDecision,
    *,
    artifact_dir: Path = Path("artifacts") / "terminal_promotion_reratification",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "terminal_promotion_decision.json"
    out_path.write_text(
        json.dumps(
            {
                "terminal_decision": decision.terminal_decision,
                "aider_decision": decision.aider_decision,
                "resolved_count": decision.resolved_count,
                "total_count": decision.total_count,
                "unresolved_items": decision.unresolved_items,
                "decided_at": decision.decided_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    decision.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "TerminalPromotionDecision",
    "TerminalPromotionReratifier",
    "emit_terminal_promotion_decision",
]
