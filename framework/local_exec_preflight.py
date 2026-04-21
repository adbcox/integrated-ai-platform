"""LEDT-P3: Bounded preflight evaluator for local execution readiness."""
from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class PreflightCheck:
    check_id: str
    check_name: str
    passed: bool
    detail: str


@dataclass
class LocalExecPreflightReport:
    report_id: str
    packet_id: str
    aider_importable: bool
    code_executor_importable: bool
    file_scope_risk: str
    validation_commands_present: bool
    checks: List[PreflightCheck]
    overall_ready: bool
    preflight_at: str


def _scope_risk(count: int) -> str:
    if count <= 3:
        return "low"
    if count <= 7:
        return "medium"
    return "high"


class LocalExecPreflightEvaluator:
    """Checks local execution readiness for a bounded packet."""

    def evaluate(
        self,
        packet_id: str,
        file_scope_count: int,
        validation_commands: List[str],
    ) -> LocalExecPreflightReport:
        checks: List[PreflightCheck] = []

        aider_ok = importlib.util.find_spec("aider") is not None
        checks.append(PreflightCheck(
            check_id="C1", check_name="aider_importable",
            passed=aider_ok,
            detail="aider package found" if aider_ok else "aider not found on sys.path",
        ))

        executor_ok = importlib.util.find_spec("framework.code_executor") is not None
        checks.append(PreflightCheck(
            check_id="C2", check_name="code_executor_importable",
            passed=executor_ok,
            detail="framework.code_executor found" if executor_ok else "framework.code_executor not found",
        ))

        risk = _scope_risk(file_scope_count)
        risk_ok = risk in ("low", "medium")
        checks.append(PreflightCheck(
            check_id="C3", check_name="file_scope_risk",
            passed=risk_ok,
            detail=f"file_scope_count={file_scope_count} → risk={risk}",
        ))

        val_ok = len(validation_commands) >= 1
        checks.append(PreflightCheck(
            check_id="C4", check_name="validation_commands_present",
            passed=val_ok,
            detail=f"{len(validation_commands)} validation commands" if val_ok else "no validation commands",
        ))

        overall_ready = executor_ok and val_ok

        return LocalExecPreflightReport(
            report_id=f"PRE-{_ts()}-{packet_id[:16].replace(' ', '_')}",
            packet_id=packet_id,
            aider_importable=aider_ok,
            code_executor_importable=executor_ok,
            file_scope_risk=risk,
            validation_commands_present=val_ok,
            checks=checks,
            overall_ready=overall_ready,
            preflight_at=_iso_now(),
        )

    def emit(self, reports: List[LocalExecPreflightReport], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "preflight_report.json"
        ready_count = sum(1 for r in reports if r.overall_ready)
        out_path.write_text(
            json.dumps({
                "sample_count": len(reports),
                "ready_count": ready_count,
                "not_ready_count": len(reports) - ready_count,
                "sample_reports": [asdict(r) for r in reports],
                "reported_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["PreflightCheck", "LocalExecPreflightReport", "LocalExecPreflightEvaluator"]
