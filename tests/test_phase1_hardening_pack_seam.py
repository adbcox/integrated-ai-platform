"""Seam tests for P1-06-PHASE1-HARDENING-CLOSEOUT-PACK-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_phase1_hardening_pack_check as chk

ARTIFACT_ROOT_PATH = REPO_ROOT / "governance/artifact_root_contract.v1.yaml"
TELEMETRY_PATH = REPO_ROOT / "governance/telemetry_normalization_contract.v1.yaml"
VALIDATION_PACK_PATH = REPO_ROOT / "governance/local_run_validation_pack.v1.yaml"
BASELINE_PATH = REPO_ROOT / "governance/phase1_hardening_baseline.v1.yaml"

ARTIFACT_ROOT_SPEC = REPO_ROOT / "docs/specs/artifact_root_contract.md"
TELEMETRY_SPEC = REPO_ROOT / "docs/specs/telemetry_normalization_contract.md"
VALIDATION_PACK_SPEC = REPO_ROOT / "docs/specs/local_run_validation_pack.md"
BASELINE_SPEC = REPO_ROOT / "docs/specs/phase1_hardening_baseline.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/workspace_contract.v1.yaml",
    REPO_ROOT / "governance/inference_gateway_contract.v1.yaml",
    REPO_ROOT / "governance/wrapped_command_contract.v1.yaml",
    REPO_ROOT / "governance/model_profiles.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "governance/autonomy_scorecard.v1.yaml",
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "docs/specs/workspace_contract.md",
    REPO_ROOT / "docs/specs/inference_gateway_contract.md",
    REPO_ROOT / "docs/specs/wrapped_command_contract.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_BASELINE_CONTRACTS = [
    "model_profiles",
    "inference_gateway_contract",
    "workspace_contract",
    "wrapped_command_contract",
    "artifact_root_contract",
    "telemetry_normalization_contract",
    "local_run_validation_pack",
]


def _load(path: Path) -> dict:
    c, _ = chk._load_yaml(path)
    return c


# ── Module / grounding ────────────────────────────────────────────────────────

def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_contract)
    assert callable(chk._check_baseline)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


# ── All 4 contract files exist ────────────────────────────────────────────────

def test_artifact_root_contract_exists():
    assert ARTIFACT_ROOT_PATH.exists()


def test_telemetry_contract_exists():
    assert TELEMETRY_PATH.exists()


def test_validation_pack_exists():
    assert VALIDATION_PACK_PATH.exists()


def test_baseline_exists():
    assert BASELINE_PATH.exists()


# ── All 4 spec files exist ────────────────────────────────────────────────────

def test_artifact_root_spec_exists():
    assert ARTIFACT_ROOT_SPEC.exists()


def test_telemetry_spec_exists():
    assert TELEMETRY_SPEC.exists()


def test_validation_pack_spec_exists():
    assert VALIDATION_PACK_SPEC.exists()


def test_baseline_spec_exists():
    assert BASELINE_SPEC.exists()


# ── Contract YAML loads ───────────────────────────────────────────────────────

def test_artifact_root_loads():
    c = _load(ARTIFACT_ROOT_PATH)
    assert isinstance(c, dict) and len(c) > 0


def test_telemetry_loads():
    c = _load(TELEMETRY_PATH)
    assert isinstance(c, dict) and len(c) > 0


def test_validation_pack_loads():
    c = _load(VALIDATION_PACK_PATH)
    assert isinstance(c, dict) and len(c) > 0


def test_baseline_loads():
    c = _load(BASELINE_PATH)
    assert isinstance(c, dict) and len(c) > 0


# ── artifact_root_contract sections ──────────────────────────────────────────

def test_artifact_root_required_sections():
    c = _load(ARTIFACT_ROOT_PATH)
    for s in ["version", "artifact_root", "separation_rules", "write_policy",
               "retention_policy", "artifact_bundle_rules", "exceptions"]:
        assert s in c, f"artifact_root_contract missing section: {s}"


def test_artifact_root_repo_relative_writes_forbidden():
    c = _load(ARTIFACT_ROOT_PATH)
    rrw = chk._bool_or_value(c["separation_rules"]["repo_relative_writes_forbidden"])
    assert rrw is True


def test_artifact_root_arbitrary_writes_forbidden():
    c = _load(ARTIFACT_ROOT_PATH)
    arw = chk._bool_or_value(c["separation_rules"]["arbitrary_repo_writes_forbidden"])
    assert arw is True


def test_artifact_root_scratch_cannot_be_artifact():
    c = _load(ARTIFACT_ROOT_PATH)
    sca = chk._bool_or_value(c["separation_rules"]["scratch_cannot_be_artifact"])
    assert sca is True


def test_artifact_root_canonical_paths_present():
    c = _load(ARTIFACT_ROOT_PATH)
    cp = c["artifact_root"]["canonical_paths"]
    assert isinstance(cp, dict)
    assert "governance_artifacts" in cp
    assert "artifacts" in cp["governance_artifacts"] or "governance" in cp["governance_artifacts"]


def test_artifact_root_exceptions_non_empty():
    c = _load(ARTIFACT_ROOT_PATH)
    assert isinstance(c["exceptions"], dict) and len(c["exceptions"]) > 0


# ── telemetry_normalization_contract sections ─────────────────────────────────

def test_telemetry_required_sections():
    c = _load(TELEMETRY_PATH)
    for s in ["version", "telemetry_identity", "required_fields", "normalized_units",
               "event_shapes", "scoring_linkage", "exceptions"]:
        assert s in c, f"telemetry_normalization_contract missing section: {s}"


def test_telemetry_required_fields_present():
    c = _load(TELEMETRY_PATH)
    rf = c["required_fields"]
    for f in chk.REQUIRED_TELEMETRY_FIELDS:
        assert f in rf, f"telemetry required_fields missing: {f}"


def test_telemetry_escalation_status_required():
    c = _load(TELEMETRY_PATH)
    es = c["required_fields"]["escalation_status"]
    assert isinstance(es, dict)
    allowed = es.get("allowed_values", [])
    assert "NOT_ESCALATED" in allowed
    assert "ESCALATED" in allowed


def test_telemetry_scoring_linkage_references_scorecard():
    c = _load(TELEMETRY_PATH)
    sl = c["scoring_linkage"]
    assert isinstance(sl, dict) and len(sl) > 0
    auth = str(sl.get("authority", ""))
    assert "autonomy_scorecard" in auth


def test_telemetry_claude_rescue_exception_present():
    c = _load(TELEMETRY_PATH)
    exc = c["exceptions"]
    assert "claude_rescue_counts_as_escalation" in exc or "claude_rescue_not_local_autonomy" in str(exc)


def test_telemetry_event_shapes_has_package_end():
    c = _load(TELEMETRY_PATH)
    es = c["event_shapes"]
    assert "package_end_event" in es


# ── local_run_validation_pack sections ────────────────────────────────────────

def test_validation_pack_required_sections():
    c = _load(VALIDATION_PACK_PATH)
    for s in ["version", "validation_sequence", "required_checks", "artifact_requirements",
               "failure_handling", "package_class_rules", "exceptions"]:
        assert s in c, f"local_run_validation_pack missing section: {s}"


def test_validation_pack_sequence_includes_required_steps():
    c = _load(VALIDATION_PACK_PATH)
    vs = c["validation_sequence"]
    steps = vs.get("steps", [])
    step_names = [s.get("name") for s in steps if isinstance(s, dict)]
    for req in chk.REQUIRED_VALIDATION_STEPS:
        assert req in step_names, f"validation_sequence missing step: {req}"


def test_validation_pack_failure_handling_keys():
    c = _load(VALIDATION_PACK_PATH)
    fh = c["failure_handling"]
    for k in chk.REQUIRED_FAILURE_HANDLING_KEYS:
        assert k in fh, f"failure_handling missing: {k}"


def test_validation_pack_stop_on_failed_gate_is_true():
    c = _load(VALIDATION_PACK_PATH)
    sofg = chk._bool_or_value(c["failure_handling"]["stop_on_failed_gate"])
    assert sofg is True


def test_validation_pack_no_accept_without_validation_is_true():
    c = _load(VALIDATION_PACK_PATH)
    nawv = chk._bool_or_value(c["failure_handling"]["no_accept_without_validation"])
    assert nawv is True


def test_validation_pack_package_class_rules_present():
    c = _load(VALIDATION_PACK_PATH)
    pc = c["package_class_rules"]
    for k in chk.REQUIRED_PACKAGE_CLASS_KEYS:
        assert k in pc, f"package_class_rules missing: {k}"


def test_validation_pack_make_check_in_sequence():
    c = _load(VALIDATION_PACK_PATH)
    steps = c["validation_sequence"].get("steps", [])
    step_names = [s.get("name") for s in steps if isinstance(s, dict)]
    assert "make_check" in step_names


# ── phase1_hardening_baseline sections ───────────────────────────────────────

def test_baseline_required_sections():
    c = _load(BASELINE_PATH)
    for s in ["version", "phase_id", "objective", "required_contracts",
               "completion_requirements", "blockers", "notes"]:
        assert s in c, f"phase1_hardening_baseline missing section: {s}"


def test_baseline_phase_id_is_phase_1():
    c = _load(BASELINE_PATH)
    assert c["phase_id"] == "phase_1"


def test_baseline_required_contracts_complete():
    c = _load(BASELINE_PATH)
    rc = c["required_contracts"]
    for name in _REQUIRED_BASELINE_CONTRACTS:
        assert name in rc, f"baseline required_contracts missing: {name}"


def test_baseline_completion_requirements_present():
    c = _load(BASELINE_PATH)
    cr = c["completion_requirements"]
    for req in ["reproducible_local_runs", "complete_artifacts",
                "no_manual_environment_repair", "explicit_escalation_accounting"]:
        assert req in cr, f"completion_requirements missing: {req}"


def test_baseline_blockers_key_exists():
    c = _load(BASELINE_PATH)
    assert "blockers" in c
    # blockers may be empty; key must exist
    b = c["blockers"]
    assert isinstance(b, dict)


def test_baseline_each_required_contract_has_path():
    c = _load(BASELINE_PATH)
    rc = c["required_contracts"]
    for name in _REQUIRED_BASELINE_CONTRACTS:
        entry = rc[name]
        assert isinstance(entry, dict), f"required_contracts.{name} must be a mapping"
        assert "contract_path" in entry, f"required_contracts.{name} missing contract_path"


# ── Spec content ──────────────────────────────────────────────────────────────

def test_artifact_root_spec_sections():
    text = ARTIFACT_ROOT_SPEC.read_text()
    for heading in (
        "## Purpose",
        "## The Arbitrary-Write Prohibition",
        "## Artifact Root Paths",
        "## Separation Rules",
        "## Write Policy",
        "## Retention Policy",
        "## Artifact Bundle Rules",
        "## Exceptions",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"artifact_root spec missing: {heading}"


def test_telemetry_spec_sections():
    text = TELEMETRY_SPEC.read_text()
    for heading in (
        "## Purpose",
        "## The Completeness Requirement",
        "## Required Fields",
        "## Normalized Units",
        "## Event Shapes",
        "## Scoring Linkage",
        "## Exceptions",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"telemetry spec missing: {heading}"


def test_validation_pack_spec_sections():
    text = VALIDATION_PACK_SPEC.read_text()
    for heading in (
        "## Purpose",
        "## The No-Skip Rule",
        "## Validation Sequence",
        "## Required Checks per Step",
        "## Artifact Requirements",
        "## Failure Handling",
        "## Package Class Rules",
        "## Exceptions",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"validation_pack spec missing: {heading}"


def test_baseline_spec_sections():
    text = BASELINE_SPEC.read_text()
    for heading in (
        "## Purpose",
        "## Phase Identity",
        "## Objective",
        "## Required Contracts",
        "## Completion Requirements",
        "## Blockers",
        "## Notes",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"baseline spec missing: {heading}"


def test_specs_reference_yaml_files():
    assert "artifact_root_contract.v1.yaml" in ARTIFACT_ROOT_SPEC.read_text()
    assert "telemetry_normalization_contract.v1.yaml" in TELEMETRY_SPEC.read_text()
    assert "local_run_validation_pack.v1.yaml" in VALIDATION_PACK_SPEC.read_text()
    assert "phase1_hardening_baseline.v1.yaml" in BASELINE_SPEC.read_text()


# ── Artifact emission ─────────────────────────────────────────────────────────

def test_emit_artifact(tmp_path):
    artifact = {
        "artifact_id": "P1-06-PHASE1-HARDENING-PACK-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "contracts_checked": list(chk.CONTRACTS.keys()),
        "contracts_loaded": True,
        "contract_section_summary": [],
        "baseline_links_checked": chk.REQUIRED_BASELINE_CONTRACTS,
        "baseline_links_present": True,
        "phase_linkage": "Phase 1",
        "authority_sources": ["ADR-0003", "ADR-0006", "ADR-0007"],
    }
    out = tmp_path / "phase1_hardening_pack_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P1-06-PHASE1-HARDENING-PACK-VALIDATION-1"
    assert loaded["contracts_loaded"] is True
    assert loaded["baseline_links_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_phase1_hardening_pack_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/phase1_hardening_pack_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P1-06-PHASE1-HARDENING-PACK-VALIDATION-1"
    assert data["contracts_loaded"] is True
    assert data["baseline_links_present"] is True
    assert len(data["contracts_checked"]) == 4
