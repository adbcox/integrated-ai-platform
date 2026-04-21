#!/usr/bin/env python3
"""P2-01: Instantiate and verify all minimum substrate surfaces; emit check artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/minimum_substrate_check.json"


def _check_session_job_schema() -> dict:
    from framework.session_job_schema_v1 import SessionRecord, JobRecord
    s = SessionRecord(
        session_id="test-session-001",
        package_id="P2-01-MINIMUM-SUBSTRATE-IMPLEMENTATION-PACK-1",
        package_label="SUBSTRATE",
        objective="Verify minimum substrate coheres",
        allowed_files=["framework/session_job_schema_v1.py"],
        forbidden_files=["framework/__init__.py"],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root=str(REPO_ROOT),
        artifact_root="artifacts/substrate",
        escalation_status="NOT_ESCALATED",
    )
    j = JobRecord(
        job_id="test-job-001",
        package_id="P2-01-MINIMUM-SUBSTRATE-IMPLEMENTATION-PACK-1",
        package_label="SUBSTRATE",
        objective="Verify minimum substrate coheres",
        allowed_files=["framework/session_job_schema_v1.py"],
        forbidden_files=["framework/__init__.py"],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root=str(REPO_ROOT),
        artifact_root="artifacts/substrate",
        escalation_status="NOT_ESCALATED",
        session_id=s.session_id,
    )
    sd = s.to_dict()
    jd = j.to_dict()
    assert "session_id" in sd and "job_id" in jd
    return {"ok": True, "session_fields": list(sd.keys()), "job_fields": list(jd.keys())}


def _check_tool_registry() -> dict:
    from framework.tool_registry_v1 import ToolRegistryV1
    r = ToolRegistryV1()
    names = set(r.list_tool_names())
    required = {"read_file", "run_command", "run_tests", "publish_artifact"}
    assert names == required, f"registry mismatch: {names}"
    for name in required:
        c = r.get_contract(name)
        assert c is not None
        assert c.tool_name == name
        assert isinstance(c.action_fields, list)
        assert isinstance(c.observation_fields, list)
        assert isinstance(c.side_effecting, bool)
    return {"ok": True, "tools_registered": sorted(names)}


def _check_workspace_controller() -> dict:
    from framework.workspace_controller_v1 import WorkspaceDescriptorV1, WorkspaceControllerV1
    d = WorkspaceDescriptorV1(
        source_root=str(REPO_ROOT),
        scratch_root="/tmp/substrate_scratch",
        artifact_root="artifacts/substrate",
        source_read_only=True,
    )
    c = WorkspaceControllerV1(d)
    assert c.validate_layout() is True
    w = c.to_dict()
    assert w["layout_valid"] is True
    assert w["source_read_only"] is True
    # invalid layout: scratch == source
    d2 = WorkspaceDescriptorV1(
        source_root="same", scratch_root="same", artifact_root="artifacts", source_read_only=True
    )
    c2 = WorkspaceControllerV1(d2)
    assert c2.validate_layout() is False
    return {"ok": True, "layout_valid": True}


def _check_permission_model() -> dict:
    from framework.permission_decision_v1 import PermissionDecisionV1, Decision
    allow = PermissionDecisionV1(
        tool_name="read_file",
        target_scope="framework/session_job_schema_v1.py",
        decision=Decision.ALLOW,
        rationale="File is in allowed_files",
    )
    deny = PermissionDecisionV1(
        tool_name="run_command",
        target_scope="framework/__init__.py",
        decision=Decision.DENY,
        rationale="File is in forbidden_files",
    )
    ask = PermissionDecisionV1(
        tool_name="publish_artifact",
        target_scope="artifacts/substrate/",
        decision=Decision.ASK,
        rationale="Artifact root write requires confirmation",
    )
    assert allow.to_dict()["decision"] == "allow"
    assert deny.to_dict()["decision"] == "deny"
    assert ask.to_dict()["decision"] == "ask"
    assert Decision.ALLOW.value == "allow"
    assert Decision.DENY.value == "deny"
    return {"ok": True, "decisions_verified": ["allow", "deny", "ask"]}


def _check_artifact_bundle() -> dict:
    from framework.session_job_schema_v1 import SessionRecord, JobRecord
    from framework.artifact_bundle_v1 import ArtifactBundleV1
    s = SessionRecord(
        session_id="test-session-001",
        package_id="P2-01-MINIMUM-SUBSTRATE-IMPLEMENTATION-PACK-1",
        package_label="SUBSTRATE",
        objective="Verify minimum substrate coheres",
        allowed_files=[],
        forbidden_files=[],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root=str(REPO_ROOT),
        artifact_root="artifacts/substrate",
        escalation_status="NOT_ESCALATED",
        final_outcome="success",
    )
    j = JobRecord(
        job_id="test-job-001",
        package_id="P2-01-MINIMUM-SUBSTRATE-IMPLEMENTATION-PACK-1",
        package_label="SUBSTRATE",
        objective="Verify minimum substrate coheres",
        allowed_files=[],
        forbidden_files=[],
        selected_profile=None,
        selected_backend="substrate",
        workspace_root=str(REPO_ROOT),
        artifact_root="artifacts/substrate",
        escalation_status="NOT_ESCALATED",
        final_outcome="success",
        session_id=s.session_id,
        validations_run=["import_check", "runner", "seam_tests", "make_check"],
        validation_results={"import_check": "pass", "runner": "pass"},
        artifacts_produced=["artifacts/substrate/minimum_substrate_check.json"],
    )
    bundle = ArtifactBundleV1(
        session=s,
        job=j,
        tools_used=["read_file", "publish_artifact"],
        validations_run=j.validations_run,
        artifacts_produced=j.artifacts_produced,
        escalation_status="NOT_ESCALATED",
        final_outcome="success",
    )
    d = bundle.to_dict()
    assert "session" in d and "job" in d
    assert d["escalation_status"] == "NOT_ESCALATED"
    assert d["final_outcome"] == "success"
    return {"ok": True, "bundle_fields": list(d.keys())}


def main() -> None:
    print("P2-01: checking minimum substrate surfaces...")
    results: dict = {}
    all_ok = True

    checks = [
        ("session_job_schema", _check_session_job_schema),
        ("tool_registry", _check_tool_registry),
        ("workspace_controller", _check_workspace_controller),
        ("permission_model", _check_permission_model),
        ("artifact_bundle", _check_artifact_bundle),
    ]

    for name, fn in checks:
        try:
            r = fn()
            results[name] = r
            print(f"  [{name}]: OK")
        except Exception as exc:
            results[name] = {"ok": False, "error": str(exc)}
            print(f"  [{name}]: FAIL — {exc}", file=sys.stderr)
            all_ok = False

    if not all_ok:
        print("HARD STOP: substrate check failed", file=sys.stderr)
        sys.exit(1)

    component_summary = [
        {"module": "framework/session_job_schema_v1.py", "classes": ["SessionRecord", "JobRecord"]},
        {"module": "framework/tool_contracts_v1.py", "classes": ["ToolContractV1"], "instances": 4},
        {"module": "framework/tool_registry_v1.py", "classes": ["ToolRegistryV1"]},
        {"module": "framework/workspace_controller_v1.py", "classes": ["WorkspaceDescriptorV1", "WorkspaceControllerV1"]},
        {"module": "framework/permission_decision_v1.py", "classes": ["PermissionDecisionV1", "Decision"]},
        {"module": "framework/artifact_bundle_v1.py", "classes": ["ArtifactBundleV1"]},
    ]

    artifact = {
        "substrate_pack": "minimum_substrate_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_loaded": results["session_job_schema"]["ok"],
        "tool_registry_loaded": results["tool_registry"]["ok"],
        "workspace_contract_loaded": results["workspace_controller"]["ok"],
        "permission_model_loaded": results["permission_model"]["ok"],
        "artifact_bundle_loaded": results["artifact_bundle"]["ok"],
        "all_checks_passed": all_ok,
        "component_summary": component_summary,
        "check_details": results,
        "phase_linkage": "Phase 2 (minimum_substrate_implementation)",
        "authority_sources": [
            "governance/phase1_hardening_baseline.v1.yaml",
            "governance/workspace_contract.v1.yaml",
            "governance/local_run_validation_pack.v1.yaml",
            "ADR-0001", "ADR-0002", "ADR-0003", "ADR-0006",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P2-01: all substrate checks passed.")


if __name__ == "__main__":
    main()
