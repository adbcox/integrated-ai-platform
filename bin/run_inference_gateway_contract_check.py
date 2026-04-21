#!/usr/bin/env python3
"""P1-02: Validate inference gateway contract YAML and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CONTRACT_PATH = REPO_ROOT / "governance/inference_gateway_contract.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/inference_gateway_contract_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/model_profiles.v1.yaml",
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/model_profiles.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

REQUIRED_SECTIONS = [
    "version",
    "gateway_api",
    "profile_resolution",
    "backend_routing",
    "timeout_retry_policy",
    "telemetry_contract",
    "exceptions",
]

REQUIRED_GATEWAY_API_KEYS = [
    "request_fields",
    "response_fields",
    "supported_backends",
    "default_backend",
]

REQUIRED_PROFILE_RESOLUTION_KEYS = [
    "input_profile_id",
    "resolution_order",
    "fallback_behavior",
]

REQUIRED_BACKEND_ROUTING_KEYS = [
    "ollama_default_rule",
    "allowed_backends",
    "direct_backend_calls_forbidden",
]

REQUIRED_TIMEOUT_RETRY_KEYS = [
    "timeout_seconds",
    "retry_budget",
    "failure_class_handling",
]

REQUIRED_TELEMETRY_FIELDS = [
    "session_id",
    "package_id",
    "selected_profile",
    "selected_backend",
    "prompt_hash",
    "response_hash",
    "token_counts",
    "latency_ms",
    "finish_reason",
    "retry_count",
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


def _check_subsection(parent_name: str, parent: dict, required_keys: list[str], errors: list[str]) -> None:
    if not isinstance(parent, dict):
        errors.append(f"{parent_name} must be a mapping")
        return
    for k in required_keys:
        if k not in parent:
            errors.append(f"{parent_name} missing required key: {k}")


def _check_content(contract: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # gateway_api
    ga = contract.get("gateway_api", {})
    _check_subsection("gateway_api", ga, REQUIRED_GATEWAY_API_KEYS, errors)
    if isinstance(ga, dict):
        if ga.get("default_backend") != "ollama":
            errors.append(f"gateway_api.default_backend must be 'ollama', got {ga.get('default_backend')!r}")
        backends = ga.get("supported_backends", [])
        if "ollama" not in (backends if isinstance(backends, list) else []):
            errors.append("gateway_api.supported_backends must include 'ollama'")

    # profile_resolution
    pr = contract.get("profile_resolution", {})
    _check_subsection("profile_resolution", pr, REQUIRED_PROFILE_RESOLUTION_KEYS, errors)

    # backend_routing
    br = contract.get("backend_routing", {})
    _check_subsection("backend_routing", br, REQUIRED_BACKEND_ROUTING_KEYS, errors)
    if isinstance(br, dict):
        backends = br.get("allowed_backends", [])
        if "ollama" not in (backends if isinstance(backends, list) else []):
            errors.append("backend_routing.allowed_backends must include 'ollama'")
        dcf = br.get("direct_backend_calls_forbidden", {})
        # Can be bool True or a dict with value: true
        forbidden_val = dcf if isinstance(dcf, bool) else (dcf.get("value") if isinstance(dcf, dict) else None)
        if forbidden_val is not True:
            errors.append("backend_routing.direct_backend_calls_forbidden must be true")

    # timeout_retry_policy
    trp = contract.get("timeout_retry_policy", {})
    _check_subsection("timeout_retry_policy", trp, REQUIRED_TIMEOUT_RETRY_KEYS, errors)

    # telemetry_contract
    tc = contract.get("telemetry_contract", {})
    if not isinstance(tc, dict):
        errors.append("telemetry_contract must be a mapping")
    else:
        fields = tc.get("fields", {})
        if not isinstance(fields, dict):
            errors.append("telemetry_contract.fields must be a mapping")
        else:
            for f in REQUIRED_TELEMETRY_FIELDS:
                if f not in fields:
                    errors.append(f"telemetry_contract.fields missing required field: {f}")

    # exceptions: must include claude escalation-only rule
    exc = contract.get("exceptions", {})
    if not isinstance(exc, dict):
        errors.append("exceptions must be a mapping")
    else:
        if "claude_is_escalation_only_not_routine_backend" not in exc:
            errors.append("exceptions missing required key: claude_is_escalation_only_not_routine_backend")

    # profile_resolution must reference model_profiles authority
    if isinstance(pr, dict):
        auth = pr.get("authority", "")
        if "model_profiles" not in str(auth):
            errors.append("profile_resolution.authority must reference model_profiles authority surface")

    return len(errors) == 0, errors


def main() -> None:
    print("P1-02: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading inference gateway contract YAML...")
    contract, err = _load_yaml(CONTRACT_PATH)
    if contract is None:
        print(f"HARD STOP: contract load failed: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"  yaml loaded: {CONTRACT_PATH.relative_to(REPO_ROOT)}")

    print("Checking required sections...")
    missing = [s for s in REQUIRED_SECTIONS if s not in contract]
    if missing:
        print(f"HARD STOP: missing sections: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_sections_present: True ({len(REQUIRED_SECTIONS)} sections)")

    print("Checking routing and telemetry fields...")
    ok, content_errors = _check_content(contract)
    if not ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)
    print(f"  routing_fields_present: True")
    print(f"  telemetry_fields_present: True ({len(REQUIRED_TELEMETRY_FIELDS)} fields)")

    routing_fields = (
        REQUIRED_GATEWAY_API_KEYS
        + REQUIRED_PROFILE_RESOLUTION_KEYS
        + REQUIRED_BACKEND_ROUTING_KEYS
        + REQUIRED_TIMEOUT_RETRY_KEYS
    )

    artifact = {
        "artifact_id": "P1-02-INFERENCE-GATEWAY-CONTRACT-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": REQUIRED_SECTIONS,
        "required_sections_present": True,
        "routing_fields_checked": routing_fields,
        "routing_fields_present": True,
        "telemetry_fields_checked": REQUIRED_TELEMETRY_FIELDS,
        "telemetry_fields_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "ADR-0004",
            "ADR-0001",
            "governance/model_profiles.v1.yaml",
            "governance/definition_of_done.v1.yaml",
            "governance/autonomy_scorecard.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P1-02: all checks passed.")


if __name__ == "__main__":
    main()
