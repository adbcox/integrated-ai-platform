#!/usr/bin/env python3
"""P0-06: Validate autonomy scorecard YAML and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCORECARD_PATH = REPO_ROOT / "governance/autonomy_scorecard.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/autonomy_scorecard_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/execution_control_package.schema.json",
    REPO_ROOT / "docs/specs/definition_of_done.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

REQUIRED_SECTIONS = [
    "version",
    "metrics",
    "thresholds",
    "interpretations",
    "phase_progression_rules",
    "exceptions",
]

REQUIRED_METRICS = [
    "first_pass_success",
    "retry_count",
    "escalation_rate",
    "artifact_completeness",
    "validation_pass_rate",
    "promotion_readiness",
]

REQUIRED_METRIC_FIELDS = ["description", "unit", "measurement_scope"]

REQUIRED_THRESHOLD_FIELDS = ["target", "warning", "blocking"]

REQUIRED_INTERPRETATION_KEYS = ["good", "caution", "failing"]

REQUIRED_PROGRESSION_RULES = ["phase_1_complete", "phase_2_ready", "local_autonomy_gate"]

REQUIRED_EXCEPTION_KEYS = [
    "claude_escalation_not_counted_as_local_autonomy",
    "missing_artifact_bundle_blocks_positive_scoring",
]


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except ImportError:
        pass
    return _minimal_yaml_keys(path.read_text(encoding="utf-8")), None


def _minimal_yaml_keys(text: str) -> dict:
    import re
    keys: dict = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
        if m:
            keys[m.group(1)] = True
    return keys


def _verify_grounding() -> bool:
    all_ok = True
    for p in GROUNDING_INPUTS:
        ok = p.exists() and p.stat().st_size > 50
        print(f"  grounding [{'OK' if ok else 'FAIL'}]: {p.relative_to(REPO_ROOT)}")
        if not ok:
            all_ok = False
    return all_ok


def _check_content(sc: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # Metrics section
    metrics = sc.get("metrics", {})
    if not isinstance(metrics, dict):
        errors.append("metrics must be a mapping")
    else:
        for m in REQUIRED_METRICS:
            if m not in metrics:
                errors.append(f"metrics missing required metric: {m}")
            else:
                entry = metrics[m]
                if isinstance(entry, dict):
                    for f in REQUIRED_METRIC_FIELDS:
                        if f not in entry:
                            errors.append(f"metrics.{m} missing required field: {f}")

    # Thresholds section
    thresholds = sc.get("thresholds", {})
    if not isinstance(thresholds, dict):
        errors.append("thresholds must be a mapping")
    else:
        for m in REQUIRED_METRICS:
            if m not in thresholds:
                errors.append(f"thresholds missing metric: {m}")
            else:
                entry = thresholds[m]
                if isinstance(entry, dict):
                    for f in REQUIRED_THRESHOLD_FIELDS:
                        if f not in entry:
                            errors.append(f"thresholds.{m} missing field: {f}")

    # Interpretations section
    interps = sc.get("interpretations", {})
    if not isinstance(interps, dict):
        errors.append("interpretations must be a mapping")
    else:
        for k in REQUIRED_INTERPRETATION_KEYS:
            if k not in interps:
                errors.append(f"interpretations missing key: {k}")

    # Phase progression rules
    ppr = sc.get("phase_progression_rules", {})
    if not isinstance(ppr, dict):
        errors.append("phase_progression_rules must be a mapping")
    else:
        for r in REQUIRED_PROGRESSION_RULES:
            if r not in ppr:
                errors.append(f"phase_progression_rules missing rule: {r}")

    # Exceptions
    exc = sc.get("exceptions", {})
    if not isinstance(exc, dict):
        errors.append("exceptions must be a mapping")
    else:
        for k in REQUIRED_EXCEPTION_KEYS:
            if k not in exc:
                errors.append(f"exceptions missing key: {k}")

    return len(errors) == 0, errors


def main() -> None:
    print("P0-06: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading scorecard YAML...")
    sc, err = _load_yaml(SCORECARD_PATH)
    if sc is None:
        print(f"HARD STOP: scorecard load failed: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"  yaml loaded: {SCORECARD_PATH.relative_to(REPO_ROOT)}")

    print("Checking required sections...")
    missing = [s for s in REQUIRED_SECTIONS if s not in sc]
    if missing:
        print(f"HARD STOP: missing sections: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_sections_present: True ({len(REQUIRED_SECTIONS)} sections)")

    print("Checking required metrics, thresholds, and interpretations...")
    ok, content_errors = _check_content(sc)
    if not ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)
    print(f"  required_metrics_present: True ({len(REQUIRED_METRICS)} metrics)")
    print(f"  threshold_fields_present: True ({len(REQUIRED_THRESHOLD_FIELDS)} fields per metric)")

    artifact = {
        "artifact_id": "P0-06-AUTONOMY-SCORECARD-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scorecard_path": str(SCORECARD_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_metrics_checked": REQUIRED_METRICS,
        "required_metrics_present": True,
        "threshold_fields_checked": REQUIRED_THRESHOLD_FIELDS,
        "threshold_fields_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "ADR-0007",
            "ADR-0006",
            "ADR-0005",
            "ADR-0004",
            "ADR-0001",
            "governance/definition_of_done.v1.yaml",
            "governance/cmdb_lite_registry.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P0-06: all checks passed.")


if __name__ == "__main__":
    main()
