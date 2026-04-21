#!/usr/bin/env python3
"""P4-01: Run Phase 4 self-sufficiency uplift checks and emit pack artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase4_uplift_pack_check.json"
PHASE4_BASELINE = REPO_ROOT / "governance/phase4_uplift_baseline.v1.yaml"
PHASE5_BASELINE = REPO_ROOT / "governance/phase5_readiness_baseline.v1.yaml"

REQUIRED_MODULES = [
    "framework.task_class_prompt_pack_v1",
    "framework.failure_memory_v1",
    "framework.critique_injection_v1",
    "framework.routing_policy_uplift_v1",
    "framework.phase5_readiness_v1",
]

REQUIRED_PHASE4_MODULES = [
    "task_class_prompt_pack_v1",
    "failure_memory_v1",
    "critique_injection_v1",
    "routing_policy_uplift_v1",
    "phase5_readiness_v1",
]

TASK_CLASSES = ["bug_fix", "narrow_feature", "reporting_helper", "test_addition"]


def _check_modules() -> tuple[bool, list[str]]:
    errors = []
    for mod in REQUIRED_MODULES:
        try:
            __import__(mod)
        except Exception as exc:
            errors.append(f"{mod}: {exc}")
    return len(errors) == 0, errors


def _run_uplift_cases() -> tuple[bool, list[dict], int, int]:
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1
    from framework.failure_memory_v1 import FailureMemoryV1
    from framework.critique_injection_v1 import CritiqueInjectionV1
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1

    pack = TaskClassPromptPackV1()
    memory = FailureMemoryV1()
    critique = CritiqueInjectionV1()
    router = RoutingPolicyUpliftV1()

    cases = []
    passed = 0

    for tc in TASK_CLASSES:
        ok = True
        errors = []

        # 1. Prompt pack
        entry = pack.get(tc)
        if entry is None:
            ok = False
            errors.append(f"no prompt entry for {tc}")
        else:
            for fld in ("system_guidance", "execution_guidance", "validation_guidance"):
                if not getattr(entry, fld, ""):
                    ok = False
                    errors.append(f"{tc}.{fld} is empty")

        # 2. Record a synthetic failure and summarize
        rec = memory.record(
            task_id=f"uplift-{tc}-001",
            task_class=tc,
            failure_signature=f"synthetic_{tc}_failure",
            correction_hint=f"check_{tc}_guidance",
        )
        summary = memory.summarize()
        if summary.total_failures < 1:
            ok = False
            errors.append(f"failure summary total_failures < 1 after recording {tc}")

        # 3. Critique injection
        result = critique.inject(
            task_class=tc,
            prior_failures=[rec],
            current_objective=f"synthetic {tc} task",
        )
        if not result.critique_points:
            ok = False
            errors.append(f"critique_points empty for {tc}")
        if not result.retry_guidance:
            ok = False
            errors.append(f"retry_guidance empty for {tc}")

        # 4. Routing decision
        decision = router.decide(task_class=tc, difficulty="medium")
        if not decision.selected_profile:
            ok = False
            errors.append(f"routing decision missing selected_profile for {tc}")
        if decision.retry_budget < 1:
            ok = False
            errors.append(f"routing retry_budget < 1 for {tc}")

        if ok:
            passed += 1

        cases.append({
            "task_class": tc,
            "passed": ok,
            "errors": errors,
            "prompt_entry": entry.to_dict() if entry else None,
            "routing": decision.to_dict(),
            "critique_points": result.critique_points,
        })

    all_ok = passed == len(TASK_CLASSES)
    return all_ok, cases, len(TASK_CLASSES), passed


def _evaluate_readiness(cases_run: int, passed: int) -> tuple[bool, dict]:
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1

    evaluator = Phase5ReadinessEvaluatorV1()
    pass_rate = passed / cases_run if cases_run > 0 else 0.0

    result = evaluator.evaluate(
        artifact_complete=True,
        validation_pass_rate=pass_rate,
        escalation_status_present=True,
        first_pass_successes=passed,
        total_cases=cases_run,
        retries_within_budget=True,
    )
    return result.ready, result.to_dict()


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


def _check_phase4_baseline(path: Path) -> tuple[bool, list[str]]:
    data, load_errors = _load_baseline(path)
    if load_errors:
        return False, load_errors
    errors = []
    if data.get("phase_id") != "phase_4":
        errors.append(f"baseline phase_id must be 'phase_4', got {data.get('phase_id')!r}")
    rm = data.get("required_modules", {})
    if isinstance(rm, dict):
        for name in REQUIRED_PHASE4_MODULES:
            if name not in rm:
                errors.append(f"baseline required_modules missing: {name}")
    return len(errors) == 0, errors


def _check_phase5_baseline(path: Path) -> tuple[bool, list[str]]:
    data, load_errors = _load_baseline(path)
    if load_errors:
        return False, load_errors
    errors = []
    if data.get("phase_id") != "phase_5":
        errors.append(f"baseline phase_id must be 'phase_5', got {data.get('phase_id')!r}")
    for section in ("readiness_dimensions", "evidence_requirements",
                    "blocking_conditions", "promotion_readiness_gate"):
        if section not in data:
            errors.append(f"phase5 baseline missing section: {section}")
    return len(errors) == 0, errors


def main() -> None:
    print("P4-01: running Phase 4 self-sufficiency uplift checks...")
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

    print("  [2] running uplift cases (4 task classes)...")
    ok, cases, cases_run, cases_passed = _run_uplift_cases()
    uplift_pass_rate = cases_passed / cases_run if cases_run > 0 else 0.0
    details["uplift_cases"] = {"ok": ok, "cases": cases}
    print(
        f"      uplift_cases: {'OK' if ok else 'FAIL'} "
        f"({cases_passed}/{cases_run} passed, pass_rate={uplift_pass_rate:.2f})"
    )
    if not ok:
        all_ok = False

    print("  [3] evaluating Phase 5 readiness...")
    readiness_ready, readiness_detail = _evaluate_readiness(cases_run, cases_passed)
    details["readiness"] = readiness_detail
    blocking_gaps = readiness_detail.get("blocking_gaps", [])
    print(
        f"      readiness: ready={readiness_ready}, "
        f"blocking_gaps={len(blocking_gaps)}"
    )

    print("  [4] checking phase4 baseline...")
    ok, errs = _check_phase4_baseline(PHASE4_BASELINE)
    details["phase4_baseline"] = {"ok": ok, "errors": errs}
    print(f"      phase4_baseline: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    print("  [5] checking phase5 readiness baseline...")
    ok, errs = _check_phase5_baseline(PHASE5_BASELINE)
    details["phase5_baseline"] = {"ok": ok, "errors": errs}
    print(f"      phase5_baseline: {'OK' if ok else 'FAIL'}")
    if not ok:
        all_ok = False

    if not all_ok:
        print("HARD STOP: phase4 uplift pack check failed", file=sys.stderr)
        sys.exit(1)

    component_summary = [
        {"module": "framework/task_class_prompt_pack_v1.py",
         "classes": ["TaskClassPromptPackV1", "PromptPackEntryV1"]},
        {"module": "framework/failure_memory_v1.py",
         "classes": ["FailureMemoryV1", "FailureRecordV1", "FailureSummaryV1"]},
        {"module": "framework/critique_injection_v1.py",
         "classes": ["CritiqueInjectionV1", "CritiqueResultV1"]},
        {"module": "framework/routing_policy_uplift_v1.py",
         "classes": ["RoutingPolicyUpliftV1", "RoutingDecisionV1"]},
        {"module": "framework/phase5_readiness_v1.py",
         "classes": ["Phase5ReadinessEvaluatorV1", "Phase5ReadinessResultV1"]},
        {"module": "governance/phase4_uplift_baseline.v1.yaml", "type": "baseline"},
        {"module": "governance/phase5_readiness_baseline.v1.yaml", "type": "baseline"},
    ]

    artifact = {
        "phase4_pack": "self_sufficiency_uplift_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_modules_loaded": details["modules_loaded"]["ok"],
        "uplift_cases_run": cases_run,
        "uplift_pass_rate": uplift_pass_rate,
        "readiness_evaluated": True,
        "readiness_ready": readiness_ready,
        "blocking_gaps": blocking_gaps,
        "all_checks_passed": all_ok,
        "escalation_status": "NOT_ESCALATED",
        "component_summary": component_summary,
        "check_details": details,
        "phase_linkage": "Phase 4 (self_sufficiency_uplift)",
        "authority_sources": [
            "governance/phase4_uplift_baseline.v1.yaml",
            "governance/phase5_readiness_baseline.v1.yaml",
            "governance/phase3_mvp_baseline.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P4-01: all Phase 4 uplift checks passed.")


if __name__ == "__main__":
    main()
