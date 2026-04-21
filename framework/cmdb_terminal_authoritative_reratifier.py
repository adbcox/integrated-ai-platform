"""CMDB-TERMINAL-AUTHORITATIVE-RERATIFIER-SEAM-1: terminal matrix reratification from CMDB decision."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CmdbTerminalDecision:
    terminal_decision: str  # "terminal_matrix_updated" | "terminal_matrix_unchanged"
    cmdb_decision: str
    cmdb_row_status: str  # "cmdb_done" | "cmdb_deferred"
    prior_terminal_decision: str
    matrix_impact: str
    decided_at: str
    artifact_path: Optional[str]


class CmdbTerminalAuthoritativeReratifier:
    """Decides whether the terminal matrix is updated based on CMDB promotion decision."""

    def reratify(
        self,
        *,
        cmdb_promotion_decision: dict,
        prior_terminal_decision: dict,
        prior_cmdb_row_status: str = "cmdb_deferred",
    ) -> CmdbTerminalDecision:
        cmdb_decision = cmdb_promotion_decision.get("decision", "cmdb_deferred")
        cmdb_row_status = cmdb_decision
        prior_td = prior_terminal_decision.get("terminal_decision", "terminal_promotion_complete")

        if cmdb_row_status == "cmdb_done" and prior_cmdb_row_status == "cmdb_deferred":
            terminal_decision = "terminal_matrix_updated"
            matrix_impact = (
                "CMDB row closed as cmdb_done; terminal matrix updated — "
                "CMDB authoritative adoption row moves from deferred to done."
            )
        elif cmdb_row_status == "cmdb_done" and prior_cmdb_row_status == "cmdb_done":
            terminal_decision = "terminal_matrix_unchanged"
            matrix_impact = "CMDB already done; no change to terminal matrix."
        else:
            terminal_decision = "terminal_matrix_unchanged"
            matrix_impact = (
                f"CMDB row remains {cmdb_row_status!r}; terminal matrix impact: none."
            )

        return CmdbTerminalDecision(
            terminal_decision=terminal_decision,
            cmdb_decision=cmdb_decision,
            cmdb_row_status=cmdb_row_status,
            prior_terminal_decision=prior_td,
            matrix_impact=matrix_impact,
            decided_at=_iso_now(),
            artifact_path=None,
        )


def emit_cmdb_terminal_decision(
    decision: CmdbTerminalDecision,
    *,
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "cmdb_terminal_decision.json"
    out_path.write_text(
        json.dumps(
            {
                "terminal_decision": decision.terminal_decision,
                "cmdb_decision": decision.cmdb_decision,
                "cmdb_row_status": decision.cmdb_row_status,
                "prior_terminal_decision": decision.prior_terminal_decision,
                "matrix_impact": decision.matrix_impact,
                "decided_at": decision.decided_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    decision.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "CmdbTerminalDecision",
    "CmdbTerminalAuthoritativeReratifier",
    "emit_cmdb_terminal_decision",
]
