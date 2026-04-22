#!/usr/bin/env python3
"""Run machine-readable QC classification against a bounded run artifact."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _update_pattern_store(pattern_store_path: Path, findings: list[dict[str, Any]]) -> None:
    """Update QC pattern store with findings from this run."""
    pattern_store = _load_yaml(pattern_store_path)

    if not pattern_store.get("failure_classes"):
        return

    # Update failure class counts based on findings
    for finding in findings:
        category = finding.get("category")
        if category == "safety":
            for cls in pattern_store.get("failure_classes", []):
                if cls.get("class_id") == "scope-violation":
                    cls["count"] = cls.get("count", 0) + 1
                    cls["last_seen"] = _iso_now()
        elif category == "correctness":
            for cls in pattern_store.get("failure_classes", []):
                if cls.get("class_id") == "validation-failed":
                    cls["count"] = cls.get("count", 0) + 1
                    cls["last_seen"] = _iso_now()

    # Initialize run_history if needed
    if not pattern_store.get("run_history"):
        pattern_store["run_history"] = []

    # Add run summary to history
    pattern_store["run_history"].append(
        {
            "timestamp": _iso_now(),
            "finding_count": len(findings),
            "categories": {f["category"] for f in findings},
        }
    )

    # Keep only last 10 run history entries
    pattern_store["run_history"] = pattern_store["run_history"][-10:]

    # Write back to file
    pattern_store_path.parent.mkdir(parents=True, exist_ok=True)
    pattern_store_path.write_text(yaml.dump(pattern_store, default_flow_style=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-artifact", default="artifacts/bounded_autonomy/runs/latest_run.json")
    parser.add_argument("--schema", default="governance/qc_finding_schema_rm_dev_002.v1.yaml")
    parser.add_argument("--template", default="governance/rm_dev_002_qc_result_template.v1.json")
    parser.add_argument("--out", default="artifacts/qc/latest_qc_result.json")
    parser.add_argument("--pattern-store", default="governance/qc_pattern_store.v1.yaml")
    args = parser.parse_args()

    run_path = REPO_ROOT / args.run_artifact
    schema_path = REPO_ROOT / args.schema
    template_path = REPO_ROOT / args.template
    out_path = REPO_ROOT / args.out
    pattern_store_path = REPO_ROOT / args.pattern_store

    run_payload = _load_json(run_path)
    schema = _load_yaml(schema_path)
    template = _load_json(template_path)

    findings: list[dict[str, Any]] = []

    scope_violations = (
        ((run_payload.get("planned_changes") or {}).get("scope_violations"))
        or []
    )
    if scope_violations:
        findings.append(
            {
                "finding_id": "F-SAFE-001",
                "category": "safety",
                "severity": "critical",
                "summary": "Scope violations detected in bounded run.",
                "evidence": "; ".join(scope_violations),
                "target_files": ((run_payload.get("planned_changes") or {}).get("planned_touched_files") or []),
                "bounded_fix_hint": "Restrict touched files to allowed_files and remove forbidden targets.",
                "disposition": "must-fix",
            }
        )

    validation = run_payload.get("validation_results") or {}
    if not bool(validation.get("all_passed")):
        failing_commands = [
            row.get("command")
            for row in (validation.get("command_results") or [])
            if not row.get("passed")
        ]
        findings.append(
            {
                "finding_id": "F-COR-001",
                "category": "correctness",
                "severity": "high",
                "summary": "One or more bounded-run validations failed.",
                "evidence": "; ".join(str(cmd) for cmd in failing_commands),
                "target_files": ((run_payload.get("planned_changes") or {}).get("planned_touched_files") or []),
                "bounded_fix_hint": "Fix failing command checks before promotion.",
                "disposition": "must-fix",
            }
        )

    touched_files = ((run_payload.get("planned_changes") or {}).get("planned_touched_files") or [])
    if len(touched_files) > 5:
        findings.append(
            {
                "finding_id": "F-STR-001",
                "category": "structural",
                "severity": "medium",
                "summary": "Run touches more files than expected bounded baseline.",
                "evidence": f"planned_touched_files={len(touched_files)}",
                "target_files": touched_files,
                "bounded_fix_hint": "Split into smaller bounded packets where possible.",
                "disposition": "review",
            }
        )

    findings.append(
        {
            "finding_id": "F-STY-001",
            "category": "style_noise",
            "severity": "low",
            "summary": "No style/noise specific blocker detected for this run.",
            "evidence": "informational baseline finding",
            "target_files": touched_files,
            "bounded_fix_hint": "Optional style cleanup only after correctness/safety gates.",
            "disposition": "info",
        }
    )

    category_counts = {key: 0 for key in (schema.get("finding_categories") or [])}
    for row in findings:
        cat = str(row.get("category"))
        category_counts[cat] = category_counts.get(cat, 0) + 1

    has_blocker = any(row.get("severity") in {"critical", "high"} for row in findings)

    result_payload = {
        "schema_version": 1,
        "schema_id": schema.get("schema_id"),
        "generated_at": _iso_now(),
        "run_id": ((run_payload.get("run_metadata") or {}).get("run_id") or "unknown"),
        "task_contract_ref": template.get("task_contract_ref"),
        "qc_model_profile": template.get("qc_model_profile"),
        "secondary_model_profile": template.get("secondary_model_profile"),
        "findings": findings,
        "category_counts": category_counts,
        "overall_disposition": "needs-fix" if has_blocker else "acceptable",
        "writeback_actions": [
            {
                "action_type": "pattern_capture",
                "target_surface": "artifacts/codex51/patterns/",
                "payload_ref": f"artifacts/codex51/patterns/{((run_payload.get('run_metadata') or {}).get('run_id') or 'run')}_qc_patterns.json",
                "rationale": "Capture recurrent QC issues for local-first prevention loops.",
            }
        ],
        "integration_refs": {
            "bounded_run_artifact": str(run_path.relative_to(REPO_ROOT)),
            "qc_schema": str(schema_path.relative_to(REPO_ROOT)),
            "verified_harvest": "governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml",
            "watchtower": "governance/oss_watchtower_candidates.v1.yaml",
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(f"artifact={out_path}")

    # Update pattern store with findings from this run
    _update_pattern_store(pattern_store_path, findings)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
