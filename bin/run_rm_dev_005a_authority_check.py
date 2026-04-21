#!/usr/bin/env python3
"""RM-DEV-005A file-specific authority closure validator."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = REPO_ROOT / "governance" / "authority_adr_0023_rm_dev_005a_adapter_boundary.md"
OSS_PATH = REPO_ROOT / "governance" / "oss_intake_registry.v1.yaml"
STATE_PATH = REPO_ROOT / "governance" / "rm_dev_005a_authority_state.v1.yaml"
SELF_PATH = REPO_ROOT / "bin" / "run_rm_dev_005a_authority_check.py"
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "governance" / "rm_dev_005a_authority_validation.json"

EXPECTED_PACKET_FILES = {
    "governance/authority_adr_0023_rm_dev_005a_adapter_boundary.md",
    "governance/oss_intake_registry.v1.yaml",
    "governance/rm_dev_005a_authority_state.v1.yaml",
    "bin/run_rm_dev_005a_authority_check.py",
    "artifacts/governance/rm_dev_005a_authority_validation.json",
}

REQUIRED_COMPONENTS = {
    "aider_repomap",
    "mcp",
    "openhands_workspace_reference",
    "qdrant",
    "swe_bench",
    "gvisor",
    "vllm",
}

REQUIRED_OSS_FIELDS = {
    "name",
    "source",
    "license",
    "wrapper_boundary",
    "removal_or_rollback_strategy",
}

ADR_REQUIRED_SNIPPETS = {
    "adapter_only": "controlled adapter / transport target only",
    "not_backbone": "architecture backbone",
    "not_policy_authority": "policy authority",
    "not_artifact_authority": "artifact authority",
    "not_state_authority": "state authority",
    "no_permanent_core_runtime_coupling": "permanent direct coupling between aider and core runtime",
    "no_permanent_ollama_coupling": "permanent direct coupling between aider and ollama as architecture",
    "behind_repo_owned_surfaces": "repo-owned runtime, gateway, and authority surfaces",
    "decision_final": "final for rm-dev-005a",
    "prohibited_patterns_section": "prohibited patterns (explicitly blocked)",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _check(label: str, passed: bool, detail: str, results: list[dict[str, Any]], failures: list[str]) -> None:
    results.append({"check": label, "passed": passed, "detail": detail})
    if not passed:
        failures.append(f"{label}: {detail}")


def main() -> int:
    failures: list[str] = []
    validated_files = {
        "adr": "governance/authority_adr_0023_rm_dev_005a_adapter_boundary.md",
        "oss_registry": "governance/oss_intake_registry.v1.yaml",
        "authority_state": "governance/rm_dev_005a_authority_state.v1.yaml",
        "validator": "bin/run_rm_dev_005a_authority_check.py",
        "artifact_output": "artifacts/governance/rm_dev_005a_authority_validation.json",
    }

    file_existence = {
        name: (REPO_ROOT / rel).exists()
        for name, rel in validated_files.items()
        if name != "artifact_output"
    }
    for name, exists in file_existence.items():
        if not exists:
            failures.append(f"missing required file: {validated_files[name]}")

    adr_checks: list[dict[str, Any]] = []
    oss_checks: list[dict[str, Any]] = []
    state_checks: list[dict[str, Any]] = []
    cross_checks: list[dict[str, Any]] = []
    packet_scope_checks: list[dict[str, Any]] = []

    if not failures:
        adr_text = ADR_PATH.read_text(encoding="utf-8").lower()
        oss = _load_yaml(OSS_PATH)
        state = _load_yaml(STATE_PATH)

        for key, snippet in ADR_REQUIRED_SNIPPETS.items():
            _check(
                f"adr_{key}",
                snippet in adr_text,
                f"requires phrase: {snippet}",
                adr_checks,
                failures,
            )

        _check(
            "oss_package_id",
            oss.get("package_id") == "RM-DEV-005A",
            f"package_id={oss.get('package_id')!r}",
            oss_checks,
            failures,
        )

        components = oss.get("components") or []
        component_ids = {component.get("component_id") for component in components}
        _check(
            "oss_required_components",
            REQUIRED_COMPONENTS.issubset(component_ids),
            f"present={sorted(str(c) for c in component_ids)}",
            oss_checks,
            failures,
        )

        missing_fields_by_component: dict[str, list[str]] = {}
        for component in components:
            component_id = component.get("component_id")
            if component_id not in REQUIRED_COMPONENTS:
                continue

            missing = [field for field in REQUIRED_OSS_FIELDS if not component.get(field)]
            has_version_pin = bool(component.get("version_pin"))
            has_version_placeholder = bool(component.get("version_pin_placeholder"))
            if not (has_version_pin or has_version_placeholder):
                missing.append("version_pin_or_version_pin_placeholder")
            has_status = bool(component.get("status") or component.get("intake_state"))
            if not has_status:
                missing.append("status_or_intake_state")

            if missing:
                missing_fields_by_component[str(component_id)] = missing

        _check(
            "oss_required_fields_per_component",
            not missing_fields_by_component,
            f"missing_fields={missing_fields_by_component}",
            oss_checks,
            failures,
        )

        _check(
            "state_package_id",
            state.get("package_id") == "RM-DEV-005A",
            f"package_id={state.get('package_id')!r}",
            state_checks,
            failures,
        )
        _check(
            "state_authority_decision_state",
            bool(state.get("authority_decision_state")),
            f"authority_decision_state={state.get('authority_decision_state')!r}",
            state_checks,
            failures,
        )
        _check(
            "state_repo_visible_closure_complete",
            state.get("repo_visible_authority_closure_state") == "complete",
            f"repo_visible_authority_closure_state={state.get('repo_visible_authority_closure_state')!r}",
            state_checks,
            failures,
        )

        aider_status = ((state.get("adapter_status") or {}).get("aider") or {})
        _check(
            "state_aider_adapter_status",
            aider_status.get("status") == "controlled_adapter_transport_target",
            f"aider.status={aider_status.get('status')!r}",
            state_checks,
            failures,
        )
        _check(
            "state_aider_not_backbone",
            aider_status.get("backbone_allowed") is False,
            f"backbone_allowed={aider_status.get('backbone_allowed')!r}",
            state_checks,
            failures,
        )
        _check(
            "state_aider_not_permanent_ollama_coupling",
            aider_status.get("permanent_direct_aider_to_ollama_coupling_allowed") is False,
            f"permanent_direct_aider_to_ollama_coupling_allowed={aider_status.get('permanent_direct_aider_to_ollama_coupling_allowed')!r}",
            state_checks,
            failures,
        )

        blocked_patterns = ((state.get("blocked_pattern_policy_state") or {}).get("blocked_patterns") or [])
        _check(
            "state_blocked_pattern_policy_active",
            (state.get("blocked_pattern_policy_state") or {}).get("state") == "active_enforced",
            f"blocked_pattern_policy_state={state.get('blocked_pattern_policy_state')!r}",
            state_checks,
            failures,
        )
        _check(
            "state_has_blocked_patterns",
            len(blocked_patterns) >= 5,
            f"blocked_patterns={blocked_patterns}",
            state_checks,
            failures,
        )

        linkage = state.get("authority_linkage") or {}
        _check(
            "state_links_adr_0023",
            linkage.get("adr_0023") == validated_files["adr"],
            f"adr_0023={linkage.get('adr_0023')!r}",
            state_checks,
            failures,
        )
        _check(
            "state_links_oss_registry",
            linkage.get("oss_registry") == validated_files["oss_registry"],
            f"oss_registry={linkage.get('oss_registry')!r}",
            state_checks,
            failures,
        )

        _check(
            "cross_adr_and_state_agree_on_adapter_only",
            ("controlled adapter / transport target only" in adr_text) and (aider_status.get("status") == "controlled_adapter_transport_target"),
            "ADR adapter-only statement must match authority_state adapter status",
            cross_checks,
            failures,
        )
        _check(
            "cross_state_and_registry_linked",
            (state.get("oss_intake_status") or {}).get("registry_path") == validated_files["oss_registry"],
            f"state.oss_intake_status.registry_path={(state.get('oss_intake_status') or {}).get('registry_path')!r}",
            cross_checks,
            failures,
        )
        _check(
            "cross_adr_and_state_prohibited_pattern_alignment",
            "permanent_direct_aider_to_ollama_coupling" in blocked_patterns
            and "permanent direct coupling between aider and ollama as architecture" in adr_text,
            "ADR prohibited coupling statement must align with blocked pattern policy state",
            cross_checks,
            failures,
        )

        _check(
            "packet_scope_expected_files_constant",
            EXPECTED_PACKET_FILES == set(validated_files.values()),
            f"expected={sorted(EXPECTED_PACKET_FILES)} validated={sorted(validated_files.values())}",
            packet_scope_checks,
            failures,
        )
        _check(
            "packet_scope_no_extra_validated_inputs",
            set(validated_files.values()) - {"artifacts/governance/rm_dev_005a_authority_validation.json"}
            == {
                "governance/authority_adr_0023_rm_dev_005a_adapter_boundary.md",
                "governance/oss_intake_registry.v1.yaml",
                "governance/rm_dev_005a_authority_state.v1.yaml",
                "bin/run_rm_dev_005a_authority_check.py",
            },
            "validator checks only RM-DEV-005A packet files",
            packet_scope_checks,
            failures,
        )

    gate_results = {
        "aider_adapter_gate": not any(check for check in failures if "adr_" in check or "state_aider_" in check),
        "oss_intake_gate": not any(check for check in failures if check.startswith("oss_") or "version_pin" in check),
        "repo_visible_authority_gate": not any(
            check for check in failures if check.startswith("state_") or check.startswith("cross_")
        ),
    }
    gate_results["validation_gate"] = len(failures) == 0

    overall_result = "pass" if all(gate_results.values()) else "fail"

    payload = {
        "schema_version": 1,
        "package_id": "RM-DEV-005A",
        "generated_at": _iso_now(),
        "validated_files": validated_files,
        "file_existence": file_existence,
        "per_file_checks": {
            "adr": adr_checks,
            "oss_registry": oss_checks,
            "authority_state": state_checks,
            "cross_file_consistency": cross_checks,
            "packet_scope": packet_scope_checks,
        },
        "prohibited_pattern_checks": {
            "adr_prohibited_patterns_explicit": any(c["check"] == "adr_prohibited_patterns_section" and c["passed"] for c in adr_checks),
            "authority_state_blocked_patterns_explicit": any(c["check"] == "state_has_blocked_patterns" and c["passed"] for c in state_checks),
        },
        "gate_results": gate_results,
        "overall_result": overall_result,
        "failure_reasons": failures,
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"artifact={ARTIFACT_PATH}")
    return 0 if overall_result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
