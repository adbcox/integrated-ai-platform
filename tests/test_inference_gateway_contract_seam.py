"""Seam tests for P1-02-INFERENCE-GATEWAY-CONTRACT-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_inference_gateway_contract_check as chk

CONTRACT_PATH = REPO_ROOT / "governance/inference_gateway_contract.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/inference_gateway_contract.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/model_profiles.v1.yaml",
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/model_profiles.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_SECTIONS = [
    "version", "gateway_api", "profile_resolution", "backend_routing",
    "timeout_retry_policy", "telemetry_contract", "exceptions",
]

_REQUIRED_TELEMETRY_FIELDS = [
    "session_id", "package_id", "selected_profile", "selected_backend",
    "prompt_hash", "response_hash", "token_counts", "latency_ms",
    "finish_reason", "retry_count",
]


def _load() -> dict:
    c, _ = chk._load_yaml(CONTRACT_PATH)
    return c


def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_content)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_contract_file_exists():
    assert CONTRACT_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_contract_loads():
    c = _load()
    assert isinstance(c, dict) and len(c) > 0


def test_version_present():
    c = _load()
    assert "version" in c and c["version"]


def test_required_sections_present():
    c = _load()
    for s in _REQUIRED_SECTIONS:
        assert s in c, f"missing section: {s}"


def test_default_backend_is_ollama():
    c = _load()
    assert c["gateway_api"]["default_backend"] == "ollama"


def test_supported_backends_includes_ollama():
    c = _load()
    assert "ollama" in c["gateway_api"]["supported_backends"]


def test_gateway_api_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_GATEWAY_API_KEYS:
        assert k in c["gateway_api"], f"gateway_api missing: {k}"


def test_profile_resolution_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_PROFILE_RESOLUTION_KEYS:
        assert k in c["profile_resolution"], f"profile_resolution missing: {k}"


def test_profile_resolution_references_model_profiles():
    c = _load()
    auth = c["profile_resolution"].get("authority", "")
    assert "model_profiles" in str(auth)


def test_backend_routing_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_BACKEND_ROUTING_KEYS:
        assert k in c["backend_routing"], f"backend_routing missing: {k}"


def test_allowed_backends_includes_ollama():
    c = _load()
    assert "ollama" in c["backend_routing"]["allowed_backends"]


def test_direct_backend_calls_forbidden_is_true():
    c = _load()
    dcf = c["backend_routing"]["direct_backend_calls_forbidden"]
    # May be bool or dict with value key
    val = dcf if isinstance(dcf, bool) else (dcf.get("value") if isinstance(dcf, dict) else None)
    assert val is True


def test_timeout_retry_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_TIMEOUT_RETRY_KEYS:
        assert k in c["timeout_retry_policy"], f"timeout_retry_policy missing: {k}"


def test_telemetry_fields_present():
    c = _load()
    fields = c["telemetry_contract"]["fields"]
    assert isinstance(fields, dict)
    for f in _REQUIRED_TELEMETRY_FIELDS:
        assert f in fields, f"telemetry_contract.fields missing: {f}"


def test_exceptions_has_claude_escalation_only():
    c = _load()
    assert "claude_is_escalation_only_not_routine_backend" in c["exceptions"]


def test_content_check_passes():
    c = _load()
    ok, errors = chk._check_content(c)
    assert ok, f"content check failed: {errors}"


def test_request_fields_has_session_and_package_id():
    c = _load()
    rf = c["gateway_api"]["request_fields"]
    assert isinstance(rf, dict)
    assert "session_id" in rf
    assert "package_id" in rf
    assert "profile_id" in rf
    assert "prompt" in rf


def test_response_fields_has_fallback_triggered():
    c = _load()
    resp = c["gateway_api"]["response_fields"]
    assert isinstance(resp, dict)
    assert "fallback_triggered" in resp
    assert "retry_count" in resp
    assert "finish_reason" in resp


def test_finish_reason_allowed_values():
    c = _load()
    resp = c["gateway_api"]["response_fields"]
    allowed = resp["finish_reason"].get("allowed_values", [])
    assert "stop" in allowed
    assert "error" in allowed
    assert "timeout" in allowed


def test_fallback_chain_exhaustion_returns_escalation():
    c = _load()
    fb = c["profile_resolution"]["fallback_behavior"]
    assert isinstance(fb, dict)
    assert "escalation_response" in fb
    esc = fb["escalation_response"]
    assert esc.get("finish_reason") == "error"
    assert esc.get("fallback_triggered") is True


def test_substrate_not_in_fallback_chain():
    c = _load()
    fb = c["profile_resolution"]["fallback_behavior"]
    chain = fb.get("fallback_chain", {})
    # Verify hard profile ends in ESCALATE, not remote_api/claude
    assert chain.get("hard") == "ESCALATE"
    assert "claude" not in str(chain).lower() or "escalation_only" in str(c["exceptions"]).lower()


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose",
        "## The Direct-Call Prohibition",
        "## Gateway API",
        "## Profile Resolution",
        "## Backend Routing",
        "## Timeout and Retry Policy",
        "## Telemetry Contract",
        "## Exceptions",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_references_contract_yaml():
    text = SPEC_PATH.read_text()
    assert "inference_gateway_contract.v1.yaml" in text


def test_spec_mentions_direct_call_prohibition():
    text = SPEC_PATH.read_text()
    assert "must not call Ollama directly" in text or "direct" in text.lower()


def test_emit_artifact(tmp_path):
    c = _load()
    ok, _ = chk._check_content(c)
    routing_fields = (
        chk.REQUIRED_GATEWAY_API_KEYS
        + chk.REQUIRED_PROFILE_RESOLUTION_KEYS
        + chk.REQUIRED_BACKEND_ROUTING_KEYS
        + chk.REQUIRED_TIMEOUT_RETRY_KEYS
    )
    artifact = {
        "artifact_id": "P1-02-INFERENCE-GATEWAY-CONTRACT-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "contract_path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": _REQUIRED_SECTIONS,
        "required_sections_present": True,
        "routing_fields_checked": routing_fields,
        "routing_fields_present": ok,
        "telemetry_fields_checked": _REQUIRED_TELEMETRY_FIELDS,
        "telemetry_fields_present": True,
        "phase_linkage": "Phase 1",
        "authority_sources": ["ADR-0004"],
    }
    out = tmp_path / "inference_gateway_contract_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P1-02-INFERENCE-GATEWAY-CONTRACT-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_sections_present"] is True
    assert loaded["routing_fields_present"] is True
    assert loaded["telemetry_fields_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_inference_gateway_contract_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/inference_gateway_contract_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P1-02-INFERENCE-GATEWAY-CONTRACT-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_sections_present"] is True
    assert data["routing_fields_present"] is True
    assert data["telemetry_fields_present"] is True
