"""Seam tests for P0-06-AUTONOMY-SCORECARD-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_autonomy_scorecard_check as chk

SCORECARD_PATH = REPO_ROOT / "governance/autonomy_scorecard.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/autonomy_scorecard.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/execution_control_package.schema.json",
    REPO_ROOT / "docs/specs/definition_of_done.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_SECTIONS = [
    "version", "metrics", "thresholds", "interpretations",
    "phase_progression_rules", "exceptions",
]

_REQUIRED_METRICS = [
    "first_pass_success", "retry_count", "escalation_rate",
    "artifact_completeness", "validation_pass_rate", "promotion_readiness",
]

_REQUIRED_METRIC_FIELDS = ["description", "unit", "measurement_scope"]
_REQUIRED_THRESHOLD_FIELDS = ["target", "warning", "blocking"]
_REQUIRED_INTERPRETATION_KEYS = ["good", "caution", "failing"]
_REQUIRED_PROGRESSION_RULES = ["phase_1_complete", "phase_2_ready", "local_autonomy_gate"]
_REQUIRED_EXCEPTION_KEYS = [
    "claude_escalation_not_counted_as_local_autonomy",
    "missing_artifact_bundle_blocks_positive_scoring",
]


def _load() -> dict:
    sc, _ = chk._load_yaml(SCORECARD_PATH)
    return sc


def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_content)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_scorecard_file_exists():
    assert SCORECARD_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_scorecard_loads():
    sc = _load()
    assert isinstance(sc, dict)
    assert len(sc) > 0


def test_version_present():
    sc = _load()
    assert "version" in sc
    assert sc["version"]


def test_required_sections_present():
    sc = _load()
    for section in _REQUIRED_SECTIONS:
        assert section in sc, f"missing section: {section}"


def test_metrics_has_all_required():
    sc = _load()
    metrics = sc["metrics"]
    assert isinstance(metrics, dict)
    for m in _REQUIRED_METRICS:
        assert m in metrics, f"metrics missing: {m}"


def test_each_metric_has_required_fields():
    sc = _load()
    for m, entry in sc["metrics"].items():
        if not isinstance(entry, dict):
            continue
        for f in _REQUIRED_METRIC_FIELDS:
            assert f in entry, f"metrics.{m} missing field: {f}"


def test_thresholds_has_all_metrics():
    sc = _load()
    thresholds = sc["thresholds"]
    assert isinstance(thresholds, dict)
    for m in _REQUIRED_METRICS:
        assert m in thresholds, f"thresholds missing metric: {m}"


def test_each_threshold_has_required_fields():
    sc = _load()
    for m, entry in sc["thresholds"].items():
        if not isinstance(entry, dict):
            continue
        for f in _REQUIRED_THRESHOLD_FIELDS:
            assert f in entry, f"thresholds.{m} missing field: {f}"


def test_interpretations_has_required_keys():
    sc = _load()
    interps = sc["interpretations"]
    assert isinstance(interps, dict)
    for k in _REQUIRED_INTERPRETATION_KEYS:
        assert k in interps, f"interpretations missing key: {k}"


def test_phase_progression_rules_present():
    sc = _load()
    ppr = sc["phase_progression_rules"]
    assert isinstance(ppr, dict)
    for r in _REQUIRED_PROGRESSION_RULES:
        assert r in ppr, f"phase_progression_rules missing: {r}"


def test_exceptions_has_required_keys():
    sc = _load()
    exc = sc["exceptions"]
    assert isinstance(exc, dict)
    for k in _REQUIRED_EXCEPTION_KEYS:
        assert k in exc, f"exceptions missing key: {k}"


def test_content_check_passes():
    sc = _load()
    ok, errors = chk._check_content(sc)
    assert ok, f"content check failed: {errors}"


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose",
        "## Why Autonomy Scoring Matters",
        "## Required Metrics",
        "## Thresholds",
        "## Interpretations",
        "## Phase Progression Rules",
        "## Exceptions",
        "## Relationship to ADRs",
        "## Relationship to Definition of Done",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_covers_all_metrics():
    text = SPEC_PATH.read_text()
    for m in _REQUIRED_METRICS:
        assert f"`{m}`" in text, f"spec does not document metric: {m}"


def test_spec_references_scorecard_yaml():
    text = SPEC_PATH.read_text()
    assert "autonomy_scorecard.v1.yaml" in text


def test_emit_artifact(tmp_path):
    sc = _load()
    ok, _ = chk._check_content(sc)
    artifact = {
        "artifact_id": "P0-06-AUTONOMY-SCORECARD-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "scorecard_path": str(SCORECARD_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_metrics_checked": _REQUIRED_METRICS,
        "required_metrics_present": ok,
        "threshold_fields_checked": _REQUIRED_THRESHOLD_FIELDS,
        "threshold_fields_present": True,
        "phase_linkage": "Phase 0",
        "authority_sources": ["ADR-0007", "ADR-0006"],
    }
    out = tmp_path / "autonomy_scorecard_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P0-06-AUTONOMY-SCORECARD-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_metrics_present"] is True
    assert loaded["threshold_fields_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_autonomy_scorecard_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/autonomy_scorecard_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P0-06-AUTONOMY-SCORECARD-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_metrics_present"] is True
    assert data["threshold_fields_present"] is True
