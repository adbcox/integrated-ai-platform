"""Inspection-gated adapter over the validation writer for the MVP coding loop."""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Optional

# Inspection gate
from framework.validation_artifact_writer import emit_validation_record, ValidationRecord, ValidationCheck

_sig = inspect.signature(emit_validation_record)
assert "record" in _sig.parameters, "emit_validation_record must accept 'record'"
assert "artifact_dir" in _sig.parameters, "emit_validation_record must accept 'artifact_dir'"
assert "dry_run" in _sig.parameters, "emit_validation_record must accept 'dry_run'"


def emit_loop_validation(
    *,
    emitter: str = "mvp_coding_loop",
    session_id: str,
    job_id: str,
    outcome: str,
    step_results: tuple = (),
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[str]:
    checks = tuple(
        ValidationCheck(
            check_name=f"step_{i}_{r.get('step', 'unknown')}",
            outcome="pass" if r.get("success") else "fail",
            detail=r.get("error"),
        )
        for i, r in enumerate(step_results)
    )
    record = ValidationRecord(
        emitter=emitter,
        validation_type="mvp_loop",
        outcome=outcome,
        checks=checks,
        session_id=session_id,
        job_id=job_id,
    )
    return emit_validation_record(record, artifact_dir=artifact_dir, dry_run=dry_run)


__all__ = ["emit_loop_validation"]
