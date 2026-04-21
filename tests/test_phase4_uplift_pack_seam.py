"""Seam tests for P4-01-SELF-SUFFICIENCY-UPLIFT-AND-PHASE5-READINESS-PACK-1."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase4_uplift_pack_check.json"
PHASE4_BASELINE = REPO_ROOT / "governance/phase4_uplift_baseline.v1.yaml"
PHASE5_BASELINE = REPO_ROOT / "governance/phase5_readiness_baseline.v1.yaml"


# ─────────────────────────────────────────────────────────────────
# Import seam tests
# ─────────────────────────────────────────────────────────────────

def test_import_task_class_prompt_pack():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1, PromptPackEntryV1
    assert TaskClassPromptPackV1 is not None
    assert PromptPackEntryV1 is not None


def test_import_failure_memory():
    from framework.failure_memory_v1 import FailureMemoryV1, FailureRecordV1, FailureSummaryV1
    assert FailureMemoryV1 is not None
    assert FailureRecordV1 is not None
    assert FailureSummaryV1 is not None


def test_import_critique_injection():
    from framework.critique_injection_v1 import CritiqueInjectionV1, CritiqueResultV1
    assert CritiqueInjectionV1 is not None
    assert CritiqueResultV1 is not None


def test_import_routing_policy_uplift():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1, RoutingDecisionV1
    assert RoutingPolicyUpliftV1 is not None
    assert RoutingDecisionV1 is not None


def test_import_phase5_readiness():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1, Phase5ReadinessResultV1
    assert Phase5ReadinessEvaluatorV1 is not None
    assert Phase5ReadinessResultV1 is not None


# ─────────────────────────────────────────────────────────────────
# TaskClassPromptPackV1 tests
# ─────────────────────────────────────────────────────────────────

def test_prompt_pack_has_four_default_classes():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1
    pack = TaskClassPromptPackV1()
    classes = pack.list_classes()
    for tc in ("bug_fix", "narrow_feature", "reporting_helper", "test_addition"):
        assert tc in classes, f"Expected task class {tc!r} not found"


def test_prompt_pack_entry_fields():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1
    pack = TaskClassPromptPackV1()
    for tc in ("bug_fix", "narrow_feature", "reporting_helper", "test_addition"):
        entry = pack.get(tc)
        assert entry is not None, f"No entry for {tc}"
        assert entry.system_guidance, f"{tc}.system_guidance is empty"
        assert entry.execution_guidance, f"{tc}.execution_guidance is empty"
        assert entry.validation_guidance, f"{tc}.validation_guidance is empty"


def test_prompt_pack_to_dict():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1
    pack = TaskClassPromptPackV1()
    entry = pack.get("bug_fix")
    assert entry is not None
    d = entry.to_dict()
    assert set(d.keys()) >= {"task_class", "system_guidance", "execution_guidance", "validation_guidance"}


def test_prompt_pack_get_unknown_returns_none():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1
    pack = TaskClassPromptPackV1()
    assert pack.get("nonexistent_class") is None


def test_prompt_pack_register():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1, PromptPackEntryV1
    pack = TaskClassPromptPackV1()
    entry = PromptPackEntryV1(
        task_class="custom_task",
        system_guidance="sys",
        execution_guidance="exec",
        validation_guidance="val",
    )
    pack.register(entry)
    assert pack.get("custom_task") is entry


def test_prompt_pack_all_entries():
    from framework.task_class_prompt_pack_v1 import TaskClassPromptPackV1
    pack = TaskClassPromptPackV1()
    entries = pack.all_entries()
    assert len(entries) == 4
    for e in entries:
        assert e.task_class
        assert e.system_guidance


# ─────────────────────────────────────────────────────────────────
# FailureMemoryV1 tests
# ─────────────────────────────────────────────────────────────────

def test_failure_memory_record_and_retrieve():
    from framework.failure_memory_v1 import FailureMemoryV1
    mem = FailureMemoryV1()
    rec = mem.record(
        task_id="t001",
        task_class="bug_fix",
        failure_signature="assertion_failed",
        correction_hint="read_trace_first",
    )
    assert rec.task_id == "t001"
    assert rec.task_class == "bug_fix"
    assert rec.failure_signature == "assertion_failed"
    assert rec.correction_hint == "read_trace_first"
    assert rec.recorded_at


def test_failure_memory_get_by_class():
    from framework.failure_memory_v1 import FailureMemoryV1
    mem = FailureMemoryV1()
    mem.record("t1", "bug_fix", "sig1", "hint1")
    mem.record("t2", "test_addition", "sig2", "hint2")
    mem.record("t3", "bug_fix", "sig3", "hint3")
    bf = mem.get_by_task_class("bug_fix")
    assert len(bf) == 2
    assert all(r.task_class == "bug_fix" for r in bf)


def test_failure_memory_get_by_task_id():
    from framework.failure_memory_v1 import FailureMemoryV1
    mem = FailureMemoryV1()
    mem.record("t1", "bug_fix", "sig1", "hint1")
    mem.record("t1", "bug_fix", "sig2", "hint2")
    mem.record("t2", "narrow_feature", "sig3", "hint3")
    recs = mem.get_by_task_id("t1")
    assert len(recs) == 2


def test_failure_memory_summarize():
    from framework.failure_memory_v1 import FailureMemoryV1
    mem = FailureMemoryV1()
    for i in range(3):
        mem.record(f"t{i}", "bug_fix", "assertion_failed", "read_trace")
    mem.record("t3", "test_addition", "order_dep", "isolate_test")
    summary = mem.summarize()
    assert summary.total_failures == 4
    assert summary.by_task_class["bug_fix"] == 3
    assert summary.by_task_class["test_addition"] == 1
    assert "assertion_failed" in summary.most_common_signatures
    assert summary.top_correction_hints


def test_failure_memory_summarize_to_dict():
    from framework.failure_memory_v1 import FailureMemoryV1
    mem = FailureMemoryV1()
    mem.record("t1", "bug_fix", "sig", "hint")
    d = mem.summarize().to_dict()
    assert set(d.keys()) >= {"total_failures", "by_task_class", "most_common_signatures", "top_correction_hints"}


def test_failure_memory_append():
    from framework.failure_memory_v1 import FailureMemoryV1, FailureRecordV1
    mem = FailureMemoryV1()
    rec = FailureRecordV1(task_id="t1", task_class="bug_fix",
                          failure_signature="sig", correction_hint="hint")
    mem.append(rec)
    assert len(mem.all_records()) == 1


# ─────────────────────────────────────────────────────────────────
# CritiqueInjectionV1 tests
# ─────────────────────────────────────────────────────────────────

def test_critique_injection_returns_structured_result():
    from framework.critique_injection_v1 import CritiqueInjectionV1
    ci = CritiqueInjectionV1()
    result = ci.inject(
        task_class="bug_fix",
        prior_failures=[],
        current_objective="fix assertion in test_foo",
    )
    assert result.task_class == "bug_fix"
    assert result.current_objective == "fix assertion in test_foo"
    assert isinstance(result.critique_points, list)
    assert len(result.critique_points) > 0
    assert isinstance(result.retry_guidance, list)
    assert len(result.retry_guidance) > 0


def test_critique_injection_incorporates_prior_failures():
    from framework.critique_injection_v1 import CritiqueInjectionV1
    from framework.failure_memory_v1 import FailureRecordV1
    ci = CritiqueInjectionV1()
    prior = [
        FailureRecordV1(
            task_id="t1", task_class="bug_fix",
            failure_signature="unique_prior_sig",
            correction_hint="unique_prior_hint",
        )
    ]
    result = ci.inject("bug_fix", prior, "objective")
    combined = " ".join(result.critique_points + result.retry_guidance)
    assert "unique_prior_sig" in combined or "unique_prior_hint" in combined


def test_critique_injection_all_task_classes():
    from framework.critique_injection_v1 import CritiqueInjectionV1
    ci = CritiqueInjectionV1()
    for tc in ("bug_fix", "narrow_feature", "reporting_helper", "test_addition"):
        result = ci.inject(tc, [], f"objective for {tc}")
        assert result.critique_points
        assert result.retry_guidance


def test_critique_injection_to_dict():
    from framework.critique_injection_v1 import CritiqueInjectionV1
    ci = CritiqueInjectionV1()
    result = ci.inject("narrow_feature", [], "add a field")
    d = result.to_dict()
    assert set(d.keys()) >= {"task_class", "current_objective", "critique_points", "retry_guidance"}


# ─────────────────────────────────────────────────────────────────
# RoutingPolicyUpliftV1 tests
# ─────────────────────────────────────────────────────────────────

def test_routing_policy_returns_decision():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1
    router = RoutingPolicyUpliftV1()
    decision = router.decide("bug_fix", "medium")
    assert decision.task_class == "bug_fix"
    assert decision.difficulty == "medium"
    assert decision.selected_profile
    assert decision.retry_budget >= 1
    assert decision.retry_posture in ("conservative", "standard", "aggressive")
    assert decision.rationale


def test_routing_policy_all_task_classes():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1
    router = RoutingPolicyUpliftV1()
    for tc in ("bug_fix", "narrow_feature", "reporting_helper", "test_addition"):
        for diff in ("low", "medium", "high"):
            d = router.decide(tc, diff)
            assert d.selected_profile, f"no profile for {tc}/{diff}"
            assert d.retry_budget >= 1


def test_routing_policy_override_profile():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1
    router = RoutingPolicyUpliftV1()
    d = router.decide("bug_fix", "low", override_profile="remote_assist")
    assert d.selected_profile == "remote_assist"


def test_routing_policy_to_dict():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1
    router = RoutingPolicyUpliftV1()
    d = router.decide("test_addition", "medium").to_dict()
    assert set(d.keys()) >= {
        "task_class", "difficulty", "selected_profile",
        "retry_budget", "retry_posture", "rationale"
    }


def test_routing_policy_low_difficulty_conservative():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1
    router = RoutingPolicyUpliftV1()
    d = router.decide("bug_fix", "low")
    assert d.retry_posture == "conservative"
    assert d.retry_budget == 1


def test_routing_policy_high_difficulty_aggressive():
    from framework.routing_policy_uplift_v1 import RoutingPolicyUpliftV1
    router = RoutingPolicyUpliftV1()
    d = router.decide("bug_fix", "high")
    assert d.retry_posture == "aggressive"
    assert d.retry_budget >= 2


# ─────────────────────────────────────────────────────────────────
# Phase5ReadinessEvaluatorV1 tests
# ─────────────────────────────────────────────────────────────────

def test_readiness_evaluator_all_met():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=1.0,
        escalation_status_present=True,
        first_pass_successes=4,
        total_cases=4,
        retries_within_budget=True,
    )
    assert result.ready is True
    assert result.blocking_gaps == []
    assert len(result.dimension_results) == 5


def test_readiness_evaluator_blocking_on_low_pass_rate():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=True,
        validation_pass_rate=0.5,
        escalation_status_present=True,
        first_pass_successes=4,
        total_cases=4,
        retries_within_budget=True,
    )
    assert result.ready is False
    assert any("pass_rate" in gap for gap in result.blocking_gaps)


def test_readiness_evaluator_blocking_on_missing_artifact():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(
        artifact_complete=False,
        validation_pass_rate=1.0,
        escalation_status_present=True,
        first_pass_successes=4,
        total_cases=4,
        retries_within_budget=True,
    )
    assert result.ready is False
    assert any("artifact" in gap for gap in result.blocking_gaps)


def test_readiness_evaluator_evidence_summary_keys():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(True, 1.0, True, 4, 4, True)
    expected_dims = {
        "artifact_completeness", "validation_pass_rate", "escalation_accounting",
        "first_pass_success_signal", "retry_discipline_signal",
    }
    assert expected_dims == set(result.evidence_summary.keys())


def test_readiness_evaluator_to_dict():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(True, 1.0, True, 4, 4, True)
    d = result.to_dict()
    assert set(d.keys()) >= {"ready", "blocking_gaps", "evidence_summary", "dimension_results"}
    assert isinstance(d["dimension_results"], list)
    assert len(d["dimension_results"]) == 5


def test_readiness_evaluator_blocking_on_retry_budget_exceeded():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(True, 1.0, True, 4, 4, retries_within_budget=False)
    assert result.ready is False
    assert any("retry" in gap for gap in result.blocking_gaps)


def test_readiness_evaluator_blocking_on_missing_escalation():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(True, 1.0, False, 4, 4, True)
    assert result.ready is False
    assert any("escalation" in gap for gap in result.blocking_gaps)


def test_readiness_evaluator_first_pass_rate_below_threshold():
    from framework.phase5_readiness_v1 import Phase5ReadinessEvaluatorV1
    ev = Phase5ReadinessEvaluatorV1()
    result = ev.evaluate(True, 1.0, True, 1, 4, True)
    assert result.ready is False
    assert any("first-pass" in gap for gap in result.blocking_gaps)


# ─────────────────────────────────────────────────────────────────
# Baseline file content tests
# ─────────────────────────────────────────────────────────────────

def _load_yaml_keys(path: Path) -> dict:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        data: dict = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
            if m:
                data[m.group(1)] = True
        return data


def test_phase4_baseline_exists():
    assert PHASE4_BASELINE.exists(), f"Missing: {PHASE4_BASELINE}"


def test_phase4_baseline_phase_id():
    data = _load_yaml_keys(PHASE4_BASELINE)
    assert data.get("phase_id") == "phase_4"


def test_phase4_baseline_required_modules():
    data = _load_yaml_keys(PHASE4_BASELINE)
    rm = data.get("required_modules", {})
    assert isinstance(rm, dict), "required_modules must be a mapping"
    for name in (
        "task_class_prompt_pack_v1",
        "failure_memory_v1",
        "critique_injection_v1",
        "routing_policy_uplift_v1",
        "phase5_readiness_v1",
    ):
        assert name in rm, f"required_modules missing: {name}"


def test_phase4_baseline_required_capabilities():
    data = _load_yaml_keys(PHASE4_BASELINE)
    rc = data.get("required_capabilities", {})
    assert isinstance(rc, dict)
    for cap in (
        "task_class_prompting",
        "failure_memory",
        "critique_guidance",
        "routing_uplift",
        "readiness_evaluation",
    ):
        assert cap in rc, f"required_capabilities missing: {cap}"


def test_phase4_baseline_completion_requirements():
    data = _load_yaml_keys(PHASE4_BASELINE)
    cr = data.get("completion_requirements", {})
    assert isinstance(cr, dict)
    for req in (
        "uplift_cases_execute",
        "readiness_signal_emitted",
        "artifact_complete_outputs",
        "explicit_escalation_accounting",
    ):
        assert req in cr, f"completion_requirements missing: {req}"


def test_phase4_baseline_has_remaining_blockers():
    data = _load_yaml_keys(PHASE4_BASELINE)
    assert "remaining_blockers" in data


def test_phase4_baseline_has_completion_gate():
    data = _load_yaml_keys(PHASE4_BASELINE)
    assert "completion_gate" in data


def test_phase5_baseline_exists():
    assert PHASE5_BASELINE.exists(), f"Missing: {PHASE5_BASELINE}"


def test_phase5_baseline_phase_id():
    data = _load_yaml_keys(PHASE5_BASELINE)
    assert data.get("phase_id") == "phase_5"


def test_phase5_baseline_readiness_dimensions():
    data = _load_yaml_keys(PHASE5_BASELINE)
    rd = data.get("readiness_dimensions", {})
    assert isinstance(rd, dict)
    for dim in (
        "artifact_completeness",
        "validation_pass_rate",
        "escalation_accounting",
        "first_pass_success",
        "retry_discipline",
    ):
        assert dim in rd, f"readiness_dimensions missing: {dim}"


def test_phase5_baseline_evidence_requirements():
    data = _load_yaml_keys(PHASE5_BASELINE)
    assert "evidence_requirements" in data


def test_phase5_baseline_blocking_conditions():
    data = _load_yaml_keys(PHASE5_BASELINE)
    assert "blocking_conditions" in data


def test_phase5_baseline_promotion_readiness_gate():
    data = _load_yaml_keys(PHASE5_BASELINE)
    assert "promotion_readiness_gate" in data


# ─────────────────────────────────────────────────────────────────
# Artifact tests
# ─────────────────────────────────────────────────────────────────

def test_artifact_exists():
    assert ARTIFACT_PATH.exists(), f"artifact not found: {ARTIFACT_PATH}"


def test_artifact_parses():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_artifact_phase4_pack_field():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data.get("phase4_pack") == "self_sufficiency_uplift_v1"


def test_artifact_all_checks_passed():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data.get("all_checks_passed") is True


def test_artifact_uplift_cases_run():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data.get("uplift_cases_run", 0) >= 4


def test_artifact_readiness_evaluated():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data.get("readiness_evaluated") is True


def test_artifact_readiness_ready_present():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert "readiness_ready" in data
    assert isinstance(data["readiness_ready"], bool)


def test_artifact_blocking_gaps_present():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert "blocking_gaps" in data
    assert isinstance(data["blocking_gaps"], list)


def test_artifact_escalation_status():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert data.get("escalation_status") == "NOT_ESCALATED"


def test_artifact_component_summary():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    cs = data.get("component_summary", [])
    assert len(cs) >= 5
    modules = [c["module"] for c in cs]
    for expected in (
        "framework/task_class_prompt_pack_v1.py",
        "framework/failure_memory_v1.py",
        "framework/critique_injection_v1.py",
        "framework/routing_policy_uplift_v1.py",
        "framework/phase5_readiness_v1.py",
    ):
        assert any(expected in m for m in modules), f"component_summary missing: {expected}"


def test_artifact_required_fields_all_present():
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    required = [
        "phase4_pack", "generated_at", "required_modules_loaded",
        "uplift_cases_run", "uplift_pass_rate", "readiness_evaluated",
        "readiness_ready", "blocking_gaps", "all_checks_passed", "component_summary",
    ]
    for field in required:
        assert field in data, f"artifact missing required field: {field}"


# ─────────────────────────────────────────────────────────────────
# Runner script seam test
# ─────────────────────────────────────────────────────────────────

def test_runner_script_exists():
    runner = REPO_ROOT / "bin/run_phase4_uplift_pack_check.py"
    assert runner.exists()


def test_runner_script_is_python():
    runner = REPO_ROOT / "bin/run_phase4_uplift_pack_check.py"
    content = runner.read_text(encoding="utf-8")
    assert "def main" in content
    assert "phase4_pack" in content
