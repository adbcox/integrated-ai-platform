"""Codex defer seam for LAEC1.

Primary defer path: if no env-backed availability is present,
emit a machine-readable defer artifact. No Codex execution code.
No SDK imports. No subprocess.

CODEX_AVAILABLE is evaluated at import time via env inspection only.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CODEX_AVAILABLE: bool = bool(
    os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
)

CODEX_DECISION_AVAILABLE = "codex_available"
CODEX_DECISION_DEFERRED = "codex_deferred"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "codex_defer"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CodexDeferArtifact:
    campaign_id: str
    decision: str
    codex_available: bool
    defer_reason: str
    next_steps: str
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "campaign_id": self.campaign_id,
            "decision": self.decision,
            "codex_available": self.codex_available,
            "defer_reason": self.defer_reason,
            "next_steps": self.next_steps,
            "generated_at": self.generated_at,
            "artifact_path": self.artifact_path,
        }


def emit_codex_defer(
    *,
    campaign_id: str = "LOCAL-AUTONOMY-EXPANSION-CLOSEOUT-CAMPAIGN-1",
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> CodexDeferArtifact:
    if CODEX_AVAILABLE:
        decision = CODEX_DECISION_AVAILABLE
        defer_reason = ""
        next_steps = "Codex adapter available; execution requires explicit campaign authorization."
    else:
        decision = CODEX_DECISION_DEFERRED
        defer_reason = (
            "Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY found in environment. "
            "Codex execution deferred."
        )
        next_steps = (
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY and re-run with explicit campaign authorization."
        )

    artifact = CodexDeferArtifact(
        campaign_id=campaign_id,
        decision=decision,
        codex_available=CODEX_AVAILABLE,
        defer_reason=defer_reason,
        next_steps=next_steps,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "codex_defer_record.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "CODEX_AVAILABLE",
    "CODEX_DECISION_AVAILABLE",
    "CODEX_DECISION_DEFERRED",
    "CodexDeferArtifact",
    "emit_codex_defer",
]
