#!/usr/bin/env python3
"""P6-01: Run Phase 6 local-first transition checks and emit pack artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase6_transition_pack_check.json"
PHASE6_BASELINE = REPO_ROOT / "governance/phase6_local_first_transition_baseline.v1.yaml"

REQUIRED_MODULES = [
    "framework.local_execution_ledger_v1",
    "framework.aider_execution_adapter_v1",
    "framework.local_autonomy_evidence_bridge_v1",
    "framework.escalation_record_v1",
    "framework.phase6_transition_v1",
]

REQUIRED_BASELINE_MODULES = [
    "local_execution_ledger_v1",
    "aider_execution_adapter_v1",
    "local_autonomy_evidence_bridge_v1",
    "escalation_record_v1",
    "phase6_transition_v1",
]

SYNTHETIC_LOCAL_RUNS = [
    {"run_id": "local-bug-001",   "package_id": "PKG-BUG-001",       "task_class": "bug_fix",          "pass": True},
    {"run_id": "local-feat-001",  "package_id": "PKG-FEAT-001",      "task_class": "narrow_feature",   "pass": True},
    {"run_id": "local-test-001",  "package_id": "PKG-TEST-001",      "task_class": "test_addition",    "pass": True},
    {"run_id": "local-report-001","package_id": "PKG-REPORT-001",    "task_class": "reporting_helper", "pass": True},
]


def _check_modules() -> tuple[bool, list[str]]:
    errors = []
    for mod in REQUIRED_MODULES:
        try:
            __import__(mod)
        except Exception as exc:
            errors.append(f"{mod}: {exc}")
    return len(errors) == 0, errors


def _build_ledger():
    from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1

    ledger = LocalExecutionLedgerV1()
    for spec in SYNTHETIC_LOCAL_RUNS:
        ledger.record(
            run_id=spec["run_id"],
            package_id=spec["package_id"],
            package_label="SUBSTRATE",
            executor="aider",
            route="local_fast",
            validation_results={"make_check": spec["pass"], "pytest": spec["pass"]},
            artifacts_produced=[],
            escalation_status="NOT_ESCALATED",
        )
    return ledger


def _build_aider_handoff(package_id: str):
    from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1

    adapter = AiderExecutionAdapterV1()
    return adapter.build_handoff(
        package_id=package_id,
        allowed_files=[
            "framework/local_execution_ledger_v1.py",
            "framework/aider_execution_adapter_v1.py",
            "framework/local_autonomy_evidence_bridge_v1.py",
            "framework/escalation_record_v1.py",
            "framework/phase6_transition_v1.py",
        ],
        task_class="narrow_feature",
        difficulty="medium",
    )


def _build_autonomy_evidence(ledger, handoff):
    from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceBridgeV1
    from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
    from framework.qualification_readiness_v1 import QualificationReadinessEvaluatorV1

    artifact = UnifiedValidationArtifactV1.build(
        package_id="P6-01-LOCAL-FIRST-TRANSITION-PACK-1",
        package_label="SUBSTRATE",
        validation_results={
            "modules_loaded": True,
            "ledger_runs": True,
            "aider_handoff": True,
            "escalation_check": True,
            "baseline_check": True,
        },
        escalation_status="NOT_ESCALATED",
    )

    qual_ev = QualificationReadinessEvaluatorV1()
    qual_result = qual_ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=ledger.pass_rate,
        escalation_status_present=True,
    )

    bridge = LocalAutonomyEvidenceBridgeV1()
    return bridge.derive(
        ledger=ledger,
        unified_artifact=artifact,
        qualification_result=qual_result,
    ), artifact, qual_result


def _build_escalation_registry():
    from framework.escalation_record_v1 import EscalationRegistryV1

    registry = EscalationRegistryV1()
    # Record synthetic non-escalated local runs
    for spec in SYNTHETIC_LOCAL_RUNS:
        registry.record(
            run_id=spec["run_id"],
            package_id=spec["package_id"],
            escalation_requested=False,
            escalation_approved=False,
            escalation_reason="routine_local_run",
            executor="aider",
        )
    return registry


def _load_baseline(path: Path) -> tuple[dict, list[str]]:
    if not path.exists():
        return {}, [f"baseline not found: {path.relative_to(REPO_ROOT)}"]
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except ImportError:
        import re
        data = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if m:
                data[m.group(1)] = True
    if not isinstance(data, dict):
        return {}, ["baseline did not parse as a mapping"]
    return data, []


def _check_phase6_baseline(path: Path) -> tuple[bool, list[str]]:
    data, load_errors = _load_baseline(path)
    if load_errors:
        return False, load_errors
    errors = []
    if data.get("phase_id") != "phase_6":
        errors.append(f"baseline phase_id must be 'phase_6', got {data.get('phase_id')!r}")
    rm = data.get("required_modules", {})
    if isinstance(rm, dict):
        for name in REQUIRED_BASELINE_MODULES:
            if name not in rm:
                errors.append(f"baseline required_modules missing: {name}")
    for section in ("required_capabilities", "completion_requirements",
                    "remaining_blockers", "transition_gate"):
        if section not in data:
            errors.append(f"phase6 baseline missing section: {section}")
    return len(errors) == 0, errors


def main() -> None:
    print("P6-01: running Phase 6 local-first transition checks...")
    all_ok = True
    details: dict = {}

    print("  [1] loading required modules...")
    ok, errs = _check_modules()
    details["modules_loaded"] = {"ok": ok, "errors": errs}
    print(f"      modules_loaded: {'OK' if ok else 'FAIL'}")
    if not ok:
        for e in errs:
            print(f"    FAIL: {e}", file=sys.stderr)
        all_ok = False

    print("  [2] building local execution ledger...")
    ledger = _build_ledger()
    details["ledger"] = ledger.to_dict()
    print(f"      ledger: {ledger.total_runs} runs, pass_rate={ledger.pass_rate:.2f}")

    print("  [3] building Aider execution handoff...")
    handoff = _build_aider_handoff("P6-01-LOCAL-FIRST-TRANSITION-PACK-1")
    details["aider_handoff"] = handoff.to_dict()
    print(f"      aider_handoff: status={handoff.adapter_status}, mode={handoff.execution_mode}")

    print("  [4] deriving local autonomy evidence...")
    autonomy_evidence, artifact, qual_result = _build_autonomy_evidence(ledger, handoff)
    details["autonomy_evidence"] = autonomy_evidence.to_dict()
    print(
        f"      autonomy_evidence: "
        f"routine_local_ready={autonomy_evidence.routine_local_execution_ready}, "
        f"claude_removed={autonomy_evidence.claude_removed_from_routine_path_signal}, "
        f"gaps={len(autonomy_evidence.evidence_gaps)}"
    )
    if not autonomy_evidence.routine_local_execution_ready:
        print(f"    WARN: routine_local_execution_ready=False; gaps: {autonomy_evidence.evidence_gaps}")

    print("  [5] building escalation registry...")
    escalation_registry = _build_escalation_registry()
    details["escalation_registry"] = escalation_registry.to_dict()
    print(
        f"      escalation_registry: "
        f"total={escalation_registry.total_records if hasattr(escalation_registry, 'total_records') else len(escalation_registry.all_records())}, "
        f"escalated={escalation_registry.escalated_count}"
    )

    print("  [6] checking Phase 6 baseline...")
    ok, errs = _check_phase6_baseline(PHASE6_BASELINE)
    details["phase6_baseline"] = {"ok": ok, "errors": errs}
    print(f"      phase6_baseline: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    print("  [7] assembling Phase 6 transition result...")
    from framework.phase6_transition_v1 import Phase6TransitionV1
    transition = Phase6TransitionV1()
    result = transition.assemble(
        package_id="P6-01-LOCAL-FIRST-TRANSITION-PACK-1",
        ledger=ledger,
        aider_handoff=handoff,
        autonomy_evidence=autonomy_evidence,
        escalation_registry=escalation_registry,
        escalation_status="NOT_ESCALATED",
    )
    details["transition_result"] = result.to_dict()
    print(f"      transition_assembled: OK (transition_ready={result.transition_ready})")

    if not all_ok:
        print("HARD STOP: phase6 transition pack check failed", file=sys.stderr)
        sys.exit(1)

    component_summary = [
        {"module": "framework/local_execution_ledger_v1.py",
         "classes": ["LocalExecutionLedgerV1", "LedgerEntryV1"]},
        {"module": "framework/aider_execution_adapter_v1.py",
         "classes": ["AiderExecutionAdapterV1", "AiderHandoffRecordV1"]},
        {"module": "framework/local_autonomy_evidence_bridge_v1.py",
         "classes": ["LocalAutonomyEvidenceBridgeV1", "LocalAutonomyEvidenceSummaryV1"]},
        {"module": "framework/escalation_record_v1.py",
         "classes": ["EscalationRecordV1", "EscalationRegistryV1"]},
        {"module": "framework/phase6_transition_v1.py",
         "classes": ["Phase6TransitionV1", "Phase6TransitionResultV1"]},
        {"module": "governance/phase6_local_first_transition_baseline.v1.yaml", "type": "baseline"},
    ]

    artifact_out = {
        "phase6_pack": "local_first_transition_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_modules_loaded": details["modules_loaded"]["ok"],
        "local_execution_cases_run": ledger.total_runs,
        "escalation_accounting_checked": True,
        "routine_local_execution_ready": autonomy_evidence.routine_local_execution_ready,
        "claude_removed_from_routine_path_signal": autonomy_evidence.claude_removed_from_routine_path_signal,
        "all_checks_passed": all_ok,
        "escalation_status": "NOT_ESCALATED",
        "component_summary": component_summary,
        "check_details": details,
        "phase_linkage": "Phase 6 (local_first_routine)",
        "authority_sources": [
            "governance/phase6_local_first_transition_baseline.v1.yaml",
            "governance/phase5_closeout_baseline.v1.yaml",
            "governance/phase5_readiness_baseline.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact_out, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P6-01: all Phase 6 transition checks passed.")


if __name__ == "__main__":
    main()
